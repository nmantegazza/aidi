"""
Unit tests for scoring and classification benchmarking framework.
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest
from pydantic import BaseModel

from entity_resolution.benchmarking.matching_evaluation import (
    MatchingMetricsEvaluator,
)
from entity_resolution.benchmarking.matching_runner import (
    retry_matching_benchmark_run,
    run_matching_benchmark,
)
from entity_resolution.dataset_loader import load_dataset
from entity_resolution.matching_strategies import (
    BaseMatchingStrategy,
    WeightedScoreMatchingConfig,
    WeightedScoreMatchingStrategy,
)
from entity_resolution.models import ColumnMatchConfig, SimilarityAlgorithm
from shared.agents import ExecutionMetadata


def test_matching_strategy_result_telemetry():
    """Verify execution telemetry tracking in BaseMatchingStrategy."""

    class DummyConfig(BaseModel):
        pass

    class DummyStrategy(BaseMatchingStrategy):
        config_schema = DummyConfig

        @classmethod
        def from_llm_config(cls, config: BaseModel) -> "DummyStrategy":
            return cls()

        def _perform_matching(
            self,
            df_a: pd.DataFrame,
            df_b: pd.DataFrame,
            candidate_pairs: pd.MultiIndex,
        ) -> pd.MultiIndex:
            return candidate_pairs

    strategy = DummyStrategy()
    df_a = pd.DataFrame({"name": ["Alice", "Bob"]}, index=["a1", "a2"])
    df_b = pd.DataFrame({"name": ["Alice", "Charlie"]}, index=["b1", "b2"])
    pairs = pd.MultiIndex.from_tuples([("a1", "b1"), ("a2", "b2")])

    res = strategy.execute(df_a, df_b, pairs)
    assert len(res.classified_pairs) == 2
    assert res.execution_time_sec >= 0.0
    assert res.peak_memory_mb >= 0.0


def test_weighted_score_matching_strategy():
    """Verify WeightedScoreMatchingStrategy produces expected match index."""
    df_a = pd.DataFrame({"name": ["Alice", "Bob"]}, index=["a1", "a2"])
    df_b = pd.DataFrame({"name": ["Alice", "Bob"]}, index=["b1", "b2"])
    pairs = pd.MultiIndex.from_tuples([("a1", "b1"), ("a1", "b2"), ("a2", "b2")])

    config = WeightedScoreMatchingConfig(
        reasoning="Test reasoning for weighted score benchmark.",
        matching_columns={
            "name": ColumnMatchConfig(
                algorithm=SimilarityAlgorithm.JAROWINKLER, weight=1.0
            )
        },
    )
    strategy = WeightedScoreMatchingStrategy(config=config)
    res = strategy.execute(df_a, df_b, pairs)

    assert ("a1", "b1") in res.classified_pairs
    assert ("a2", "b2") in res.classified_pairs
    assert ("a1", "b2") not in res.classified_pairs


def test_matching_metrics_evaluator():
    """Verify evaluation metric calculations."""
    evaluator = MatchingMetricsEvaluator()
    classified = pd.MultiIndex.from_tuples([("a1", "b1"), ("a1", "b2")])
    gt = {("a1", "b1")}

    metrics = evaluator.evaluate(classified, gt)
    assert round(metrics["precision"], 2) == 0.5
    assert round(metrics["recall"], 2) == 1.0
    assert round(metrics["f1"], 2) == 0.67
    assert metrics["potential_recall"] is None
    assert metrics["uncertain_count"] == 0


def test_matching_metrics_evaluator_triage():
    """Verify triage metric calculations with uncertain bucket."""
    evaluator = MatchingMetricsEvaluator()
    # A1 (classified matches): 1 TP ("a1", "b1"), 1 FP ("a5", "b5")
    classified = pd.MultiIndex.from_tuples([("a1", "b1"), ("a5", "b5")])
    # A2 (uncertain): 1 match in GT ("a2", "b2"), 1 non-match ("a3", "b3")
    uncertain = pd.MultiIndex.from_tuples([("a2", "b2"), ("a3", "b3")])
    # GT: 3 true matches total ("a1", "b1"), ("a2", "b2"), ("a4", "b4")
    gt = {("a1", "b1"), ("a2", "b2"), ("a4", "b4")}
    total_candidates = 10

    metrics = evaluator.evaluate(
        classified_pairs=classified,
        ground_truth=gt,
        uncertain_pairs=uncertain,
        total_candidates=total_candidates,
    )

    # Direct metrics
    assert metrics["tp"] == 1
    assert metrics["fp"] == 1
    assert metrics["fn"] == 2  # ("a2", "b2") and ("a4", "b4") treated as FN directly
    assert metrics["precision"] == 0.5  # 1 / 2
    assert metrics["recall"] == pytest.approx(1 / 3, abs=1e-3)
    # Triage metrics:
    # (A1 U A2) cap GT = {("a1", "b1"), ("a2", "b2")} -> size 2
    # Potential Recall: 2 / 3
    assert metrics["potential_recall"] == pytest.approx(2 / 3, abs=1e-3)
    # Potential F1: 2 * P * R_pot / (P + R_pot) = 2 * 0.5 * (2/3) / (0.5 + 2/3) = (2/3) / (7/6) = 4/7
    assert metrics["potential_f1"] == pytest.approx(4 / 7, abs=1e-3)
    # Unrecoverable loss: 1.0 - 2/3 = 1/3
    assert metrics["unrecoverable_loss"] == pytest.approx(1 / 3, abs=1e-3)
    # LLM workload: |A2| / total_candidates = 2 / 10 = 0.2
    assert metrics["llm_workload_ratio"] == 0.2
    # Uncertain purity: |A2 cap GT| / |A2| = 1 / 2 = 0.5
    assert metrics["uncertain_purity"] == 0.5
    assert metrics["uncertain_count"] == 2


def test_dataset_loader_load_candidates():
    """Verify candidate loading from CSV file."""
    import json
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        df_a = pd.DataFrame({"id": ["a1", "a2"], "name": ["Alice", "Bob"]})
        df_b = pd.DataFrame({"id": ["b1", "b2"], "name": ["Alice", "Bob"]})
        gt = pd.DataFrame({"id_a": ["a1"], "id_b": ["b1"], "label": [1]})
        candidates = pd.DataFrame({"id_a": ["a1", "a2"], "id_b": ["b1", "b2"]})

        df_a.to_csv(tmp_path / "table_a.csv", index=False)
        df_b.to_csv(tmp_path / "table_b.csv", index=False)
        gt.to_csv(tmp_path / "matches.csv", index=False)

        metadata_no_cand = {
            "name": "test_ds",
            "domain": "e-commerce",
            "ground_truth_type": "exhaustive",
            "table_a": {"file": "table_a.csv", "id_column": "id"},
            "table_b": {"file": "table_b.csv", "id_column": "id"},
            "ground_truth": {
                "file": "matches.csv",
                "column_a": "id_a",
                "column_b": "id_b",
                "label_column": "label",
            },
            "candidates": None,
        }
        with open(tmp_path / "metadata.json", "w") as f:
            json.dump(metadata_no_cand, f)

        dataset = load_dataset(str(tmp_path))
        assert dataset.candidates is None

        candidates.to_csv(tmp_path / "candidates.csv", index=False)
        metadata_with_cand = metadata_no_cand.copy()
        metadata_with_cand["candidates"] = {
            "file": "candidates.csv",
            "column_a": "id_a",
            "column_b": "id_b",
        }
        with open(tmp_path / "metadata.json", "w") as f:
            json.dump(metadata_with_cand, f)

        loaded_cand = load_dataset(str(tmp_path)).candidates
        assert loaded_cand is not None
        assert len(loaded_cand) == 2


@pytest.mark.asyncio
@patch(
    "entity_resolution.benchmarking.matching_config_generator."
    "identify_indexing_config_via_llm"
)
async def test_run_matching_benchmark_runner(mock_llm):
    """Verify run_matching_benchmark execution on temporary dataset."""
    import json
    mock_config = WeightedScoreMatchingConfig(
        reasoning="Mock reasoning for benchmark runner test.",
        matching_columns={
            "name": ColumnMatchConfig(
                algorithm=SimilarityAlgorithm.JAROWINKLER, weight=1.0
            )
        },
    )
    mock_metadata = ExecutionMetadata(
        model_name="test-model",
        provider="google",
        execution_time_seconds=1.0,
        total_tokens=100,
        prompt_tokens=50,
        completion_tokens=50,
    )
    mock_llm.side_effect = AsyncMock(return_value=(mock_config, mock_metadata))

    with tempfile.TemporaryDirectory() as tmpdir:
        root_path = Path(tmpdir)
        ds_path = root_path / "amazon-walmart"
        ds_path.mkdir(parents=True)

        df_a = pd.DataFrame({"id": ["a1"], "name": ["Widget"]})
        df_b = pd.DataFrame({"id": ["b1"], "name": ["Widget"]})
        gt = pd.DataFrame({"id_a": ["a1"], "id_b": ["b1"], "label": [1]})
        candidates = pd.DataFrame({"id_a": ["a1"], "id_b": ["b1"]})

        df_a.to_csv(ds_path / "amazon_standardized.csv", index=False)
        df_b.to_csv(ds_path / "walmart_standardized.csv", index=False)
        gt.to_csv(ds_path / "matches_walmart_amazon.csv", index=False)
        candidates.to_csv(ds_path / "candidates.csv", index=False)

        metadata = {
            "name": "amazon-walmart",
            "domain": "e-commerce",
            "ground_truth_type": "exhaustive",
            "table_a": {
                "file": "amazon_standardized.csv",
                "id_column": "id"
            },
            "table_b": {
                "file": "walmart_standardized.csv",
                "id_column": "id"
            },
            "ground_truth": {
                "file": "matches_walmart_amazon.csv",
                "column_a": "id_a",
                "column_b": "id_b",
                "label_column": "label"
            },
            "candidates": {
                "file": "candidates.csv",
                "column_a": "id_a",
                "column_b": "id_b",
            },
        }
        (ds_path / "metadata.json").write_text(
            json.dumps(metadata), encoding="utf-8"
        )

        out_file = root_path / "results.json"
        summary = await run_matching_benchmark(
            data_dir=str(root_path),
            output=str(out_file),
            strategy="weighted",
            force_llm=True,
        )

        assert summary.total_iterations_count == 1
        assert summary.failed_iterations_count == 0
        assert summary.strategies == ["weighted"]
        assert out_file.exists()


@pytest.mark.asyncio
@patch(
    "entity_resolution.benchmarking.matching_config_generator."
    "identify_indexing_config_via_llm"
)
async def test_run_matching_benchmark_dual_perspective_mode(mock_llm):
    """Verify dual-perspective benchmark execution (--classification-mode both)."""
    import json
    mock_config = WeightedScoreMatchingConfig(
        reasoning="Mock reasoning for dual perspective benchmark test.",
        matching_columns={
            "name": ColumnMatchConfig(
                algorithm=SimilarityAlgorithm.JAROWINKLER, weight=1.0
            )
        },
    )
    mock_metadata = ExecutionMetadata(
        model_name="mock-model",
        provider="google",
        execution_time_seconds=0.5,
        total_tokens=80,
        prompt_tokens=40,
        completion_tokens=40,
    )
    mock_llm.side_effect = AsyncMock(return_value=(mock_config, mock_metadata))

    with tempfile.TemporaryDirectory() as tmpdir:
        root_path = Path(tmpdir)
        ds_path = root_path / "ds_test"
        ds_path.mkdir(parents=True)

        df_a = pd.DataFrame({
            "id": ["a1", "a2", "a3"],
            "name": ["Widget Pro", "Gadget Plus", "Alpha Noise"],
        })
        df_b = pd.DataFrame({
            "id": ["b1", "b2", "b3"],
            "name": ["Widget Pro", "Gadget Plus Mini", "Beta Noise"],
        })
        gt = pd.DataFrame({
            "id_a": ["a1", "a2"],
            "id_b": ["b1", "b2"],
            "label": [1, 1],
        })
        candidates = pd.DataFrame({
            "id_a": ["a1", "a2", "a3"],
            "id_b": ["b1", "b2", "b3"],
        })

        df_a.to_csv(ds_path / "table_a.csv", index=False)
        df_b.to_csv(ds_path / "table_b.csv", index=False)
        gt.to_csv(ds_path / "matches.csv", index=False)
        candidates.to_csv(ds_path / "candidates.csv", index=False)

        metadata = {
            "name": "ds_test",
            "domain": "e-commerce",
            "ground_truth_type": "exhaustive",
            "table_a": {"file": "table_a.csv", "id_column": "id"},
            "table_b": {"file": "table_b.csv", "id_column": "id"},
            "ground_truth": {
                "file": "matches.csv",
                "column_a": "id_a",
                "column_b": "id_b",
                "label_column": "label",
            },
            "candidates": {
                "file": "candidates.csv",
                "column_a": "id_a",
                "column_b": "id_b",
            },
        }
        (ds_path / "metadata.json").write_text(
            json.dumps(metadata), encoding="utf-8"
        )

        run_dir = root_path / "test_run"
        summary = await run_matching_benchmark(
            data_dir=str(root_path),
            output_dir=run_dir,
            strategy="weighted",
            models=["mock-model"],
            classification_mode="both",
            iterations=1,
            force_llm=True,
        )

        assert summary.total_iterations_count == 2  # binary + ternary
        assert summary.failed_iterations_count == 0
        # Zero token overhead: LLM should only be called once, reused for ternary pass
        assert mock_llm.call_count == 1

        # Check directory structure
        datasets_base = run_dir / summary.run_id / "datasets" / "ds_test" / "mock-model"
        bin_dir = datasets_base / "binary" / "weighted"
        ter_dir = datasets_base / "ternary" / "weighted"

        assert bin_dir.exists()
        assert (bin_dir / "metrics.json").exists()
        assert (bin_dir / "traces.json").exists()
        assert (bin_dir / "traces.jsonl").exists()
        assert (bin_dir / "report.md").exists()
        assert (bin_dir / "iteration_1" / "matches.csv").exists()
        assert (bin_dir / "iteration_1" / "non_matches.csv").exists()

        assert ter_dir.exists()
        assert (ter_dir / "metrics.json").exists()
        assert (ter_dir / "traces.json").exists()
        assert (ter_dir / "traces.jsonl").exists()
        assert (ter_dir / "report.md").exists()
        assert (ter_dir / "iteration_1" / "matches.csv").exists()

        # Check comparison summary
        comp_summary = run_dir / summary.run_id / "comparison_summary.md"
        assert comp_summary.exists()
        comp_text = comp_summary.read_text(encoding="utf-8")
        assert "Dual-Perspective ER Matching Benchmarking Comparison Summary" in comp_text
        assert "ds_test" in comp_text

        # Check matrix keying
        matrix_ds = summary.matrix["ds_test"]["mock-model"]
        assert "weighted_binary" in matrix_ds
        assert "weighted_ternary" in matrix_ds


@pytest.mark.asyncio
@patch(
    "entity_resolution.benchmarking.matching_config_generator."
    "identify_indexing_config_via_llm"
)
async def test_retry_matching_benchmark_combinatorial(mock_llm):
    """Verify in-place retry resolution for combinatorial run directories."""
    import json
    mock_config = WeightedScoreMatchingConfig(
        reasoning="Mock reasoning for retry test.",
        matching_columns={
            "name": ColumnMatchConfig(
                algorithm=SimilarityAlgorithm.JAROWINKLER, weight=1.0
            )
        },
    )
    mock_metadata = ExecutionMetadata(
        model_name="mock-model",
        provider="google",
        execution_time_seconds=0.5,
        total_tokens=50,
        prompt_tokens=25,
        completion_tokens=25,
    )
    mock_llm.side_effect = AsyncMock(return_value=(mock_config, mock_metadata))

    with tempfile.TemporaryDirectory() as tmpdir:
        root_path = Path(tmpdir)
        ds_path = root_path / "ds_retry"
        ds_path.mkdir(parents=True)

        df_a = pd.DataFrame({"id": ["a1", "a2"], "name": ["Alpha", "Beta"]})
        df_b = pd.DataFrame({"id": ["b1", "b2"], "name": ["Alpha", "Beta"]})
        gt = pd.DataFrame({"id_a": ["a1"], "id_b": ["b1"], "label": [1]})
        candidates = pd.DataFrame({"id_a": ["a1", "a2"], "id_b": ["b1", "b2"]})

        df_a.to_csv(ds_path / "table_a.csv", index=False)
        df_b.to_csv(ds_path / "table_b.csv", index=False)
        gt.to_csv(ds_path / "matches.csv", index=False)
        candidates.to_csv(ds_path / "candidates.csv", index=False)

        metadata = {
            "name": "ds_retry",
            "domain": "e-commerce",
            "ground_truth_type": "exhaustive",
            "table_a": {"file": "table_a.csv", "id_column": "id"},
            "table_b": {"file": "table_b.csv", "id_column": "id"},
            "ground_truth": {
                "file": "matches.csv",
                "column_a": "id_a",
                "column_b": "id_b",
                "label_column": "label",
            },
            "candidates": {
                "file": "candidates.csv",
                "column_a": "id_a",
                "column_b": "id_b",
            },
        }
        (ds_path / "metadata.json").write_text(
            json.dumps(metadata), encoding="utf-8"
        )

        run_dir = root_path / "test_retry_run"
        summary = await run_matching_benchmark(
            data_dir=str(root_path),
            output_dir=run_dir,
            strategy="weighted",
            models=["mock-model"],
            classification_mode="binary",
            iterations=1,
            force_llm=True,
        )

        full_run_dir = run_dir / summary.run_id
        # Now simulate retry (0 failed iterations should exit cleanly)
        retry_summary = await retry_matching_benchmark_run(
            run_target=full_run_dir,
            output_dir=run_dir,
        )
        assert retry_summary.run_id == summary.run_id
        assert retry_summary.failed_iterations_count == 0


@pytest.mark.asyncio
@patch(
    "entity_resolution.benchmarking.matching_config_generator."
    "identify_indexing_config_via_llm"
)
async def test_run_matching_benchmark_multi_model_multi_strategy(mock_llm):
    """Verify execution with multiple models, multiple strategies, and multi-iterations."""
    import json
    from entity_resolution.models import KMeansColumnConfig, KMeansMatchingConfig

    async def mock_get_config(*args, **kwargs):
        config_schema = kwargs.get("config_schema")
        model_name = kwargs.get("model_name", "mock-model")
        mock_metadata = ExecutionMetadata(
            model_name=model_name,
            provider="google",
            execution_time_seconds=0.2,
            total_tokens=60,
            prompt_tokens=30,
            completion_tokens=30,
        )
        if config_schema == KMeansMatchingConfig:
            cfg = KMeansMatchingConfig(
                reasoning="KMeans multi-model test.",
                matching_columns={
                    "name": KMeansColumnConfig(
                        algorithm=SimilarityAlgorithm.JAROWINKLER
                    )
                },
            )
        else:
            cfg = WeightedScoreMatchingConfig(
                reasoning="Weighted multi-model test.",
                matching_columns={
                    "name": ColumnMatchConfig(
                        algorithm=SimilarityAlgorithm.JAROWINKLER, weight=1.0
                    )
                },
            )
        return cfg, mock_metadata

    mock_llm.side_effect = mock_get_config

    with tempfile.TemporaryDirectory() as tmpdir:
        root_path = Path(tmpdir)
        ds_path = root_path / "ds_multi"
        ds_path.mkdir(parents=True)

        df_a = pd.DataFrame({
            "id": ["a1", "a2", "a3", "a4"],
            "name": ["Alpha Pro", "Beta Max", "Gamma Ultra", "Delta Prime"],
        })
        df_b = pd.DataFrame({
            "id": ["b1", "b2", "b3", "b4"],
            "name": ["Alpha Pro", "Beta Max", "Gamma Ultra", "Delta Noise"],
        })
        gt = pd.DataFrame({
            "id_a": ["a1", "a2", "a3"],
            "id_b": ["b1", "b2", "b3"],
            "label": [1, 1, 1],
        })
        candidates = pd.DataFrame({
            "id_a": ["a1", "a2", "a3", "a4"],
            "id_b": ["b1", "b2", "b3", "b4"],
        })

        df_a.to_csv(ds_path / "table_a.csv", index=False)
        df_b.to_csv(ds_path / "table_b.csv", index=False)
        gt.to_csv(ds_path / "matches.csv", index=False)
        candidates.to_csv(ds_path / "candidates.csv", index=False)

        metadata = {
            "name": "ds_multi",
            "domain": "e-commerce",
            "ground_truth_type": "exhaustive",
            "table_a": {"file": "table_a.csv", "id_column": "id"},
            "table_b": {"file": "table_b.csv", "id_column": "id"},
            "ground_truth": {
                "file": "matches.csv",
                "column_a": "id_a",
                "column_b": "id_b",
                "label_column": "label",
            },
            "candidates": {
                "file": "candidates.csv",
                "column_a": "id_a",
                "column_b": "id_b",
            },
        }
        (ds_path / "metadata.json").write_text(
            json.dumps(metadata), encoding="utf-8"
        )

        run_dir = root_path / "test_multi_run"
        summary = await run_matching_benchmark(
            data_dir=str(root_path),
            output_dir=run_dir,
            strategies=["weighted", "kmeans"],
            models=["mock-model-1", "mock-model-2"],
            classification_mode="ternary",
            iterations=2,
            force_llm=True,
        )

        # 1 dataset * 2 models * 2 strategies * 2 iterations = 8 total iterations
        assert summary.total_iterations_count == 8
        assert summary.failed_iterations_count == 0
        assert set(summary.models) == {"mock-model-1", "mock-model-2"}
        assert set(summary.strategies) == {"weighted", "kmeans"}

        # Check 3-level matrix
        assert "ds_multi" in summary.matrix
        assert "mock-model-1" in summary.matrix["ds_multi"]
        assert "mock-model-2" in summary.matrix["ds_multi"]
        assert "weighted" in summary.matrix["ds_multi"]["mock-model-1"]
        assert "kmeans" in summary.matrix["ds_multi"]["mock-model-1"]
        assert "weighted" in summary.matrix["ds_multi"]["mock-model-2"]
        assert "kmeans" in summary.matrix["ds_multi"]["mock-model-2"]

        # Check summary.md and summary.csv
        out_run_dir = run_dir / summary.run_id
        summary_md_text = (out_run_dir / "summary.md").read_text(encoding="utf-8")
        assert "mock-model-1" in summary_md_text
        assert "mock-model-2" in summary_md_text

        summary_csv_text = (out_run_dir / "summary.csv").read_text(encoding="utf-8")
        assert "mock-model-1" in summary_csv_text
        assert "mock-model-2" in summary_csv_text



