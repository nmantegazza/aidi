"""Tests for ER matching benchmarking harness, resilience, and retry workflows."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from entity_resolution.benchmarking.common.models import (
    RunStatus,
    TokenUsage,
)
from entity_resolution.benchmarking.matching_models import (
    MatchingIterationMetrics,
)
from entity_resolution.benchmarking.matching_runner import (
    _aggregate_matching_metrics,
    retry_matching_benchmark_run,
    run_matching_benchmark,
)
from entity_resolution.dataset_loader import (
    DatasetMetadata,
    GroundTruthRef,
    GroundTruthType,
    LoadedDataset,
    TableRef,
)
from entity_resolution.matching_strategies import (
    MatchingStrategyResult,
    WeightedScoreMatchingStrategy,
)
from shared.agents import ExecutionMetadata


def _make_dummy_matching_dataset() -> LoadedDataset:
    """Creates a minimal in-memory LoadedDataset with candidates for matching tests."""
    df_a = pd.DataFrame(
        {"title": ["Laptop Pro", "Smartphone X"]}, index=["a1", "a2"]
    )
    df_b = pd.DataFrame(
        {"title": ["Laptop Pro", "Smartphone 10"]}, index=["b1", "b2"]
    )
    metadata = DatasetMetadata(
        name="dummy_match_ds",
        domain="electronics",
        ground_truth_type=GroundTruthType.EXHAUSTIVE,
        table_a=TableRef(file="a.csv", id_column="id"),
        table_b=TableRef(file="b.csv", id_column="id"),
        ground_truth=GroundTruthRef(
            file="gt.csv", column_a="id_a", column_b="id_b"
        ),
    )
    cand_index = pd.MultiIndex.from_tuples(
        [("a1", "b1"), ("a2", "b2"), ("a1", "b2")],
        names=["left_id", "right_id"],
    )
    return LoadedDataset(
        metadata=metadata,
        table_a=df_a,
        table_b=df_b,
        ground_truth={("a1", "b1"), ("a2", "b2")},
        candidates=cand_index,
    )


def test_matching_aggregation_and_flakiness():
    """Verifies matching metric aggregation and stochastic flakiness analysis."""
    it1 = MatchingIterationMetrics(
        iteration_index=1,
        status=RunStatus.SUCCESS,
        precision=1.0,
        recall=1.0,
        f1=1.0,
        tp=2,
        fp=0,
        fn=0,
        execution_time_sec=1.5,
        peak_memory_mb=70.0,
        token_usage=TokenUsage(prompt_tokens=100, total_tokens=150),
    )
    it2 = MatchingIterationMetrics(
        iteration_index=2,
        status=RunStatus.SUCCESS,
        precision=0.5,
        recall=0.5,
        f1=0.5,
        tp=1,
        fp=1,
        fn=1,
        execution_time_sec=1.1,
        peak_memory_mb=75.0,
        token_usage=TokenUsage(prompt_tokens=100, total_tokens=150),
    )
    it3 = MatchingIterationMetrics(
        iteration_index=3,
        status=RunStatus.FAILED,
        error_message="Simulation failure",
    )

    pred_sets = [
        {("a1", "b1"), ("a2", "b2")},  # it1
        {("a1", "b1"), ("a1", "b2")},  # it2
    ]

    dm = _aggregate_matching_metrics(
        dataset_name="dummy_match_ds",
        domain="tech",
        strategy_name="Weighted Score",
        model_name="mock-model",
        iterations=[it1, it2, it3],
        predicted_sets=pred_sets,
    )

    assert dm.successful_iterations_count == 2
    assert dm.failed_iterations_count == 1
    assert round(dm.mean_f1, 2) == 0.75
    assert dm.mean_execution_time == 1.3
    assert dm.flakiness_analysis is not None
    assert dm.flakiness_analysis.consistent_matches_count == 1  # ("a1", "b1") in both
    assert dm.flakiness_analysis.flaky_matches_count == 2  # ("a2", "b2") and ("a1", "b2")
    assert round(dm.flakiness_analysis.stability_ratio, 2) == 0.33


@pytest.mark.asyncio
async def test_matching_resilience_and_retry_flow(tmp_path: Path):
    """Verifies matching failure tolerance, artifact generation, no HTML, and retry."""
    dummy_ds = _make_dummy_matching_dataset()
    mock_strategy = MagicMock(spec=WeightedScoreMatchingStrategy)
    mock_strategy.name = "Weighted Score"

    matched_pairs = pd.MultiIndex.from_tuples(
        [("a1", "b1"), ("a2", "b2")], names=["left_id", "right_id"]
    )
    features_df = pd.DataFrame(
        {
            "title_sim": [1.0, 0.9, 0.1],
            "prediction": ["match", "match", "non_match"],
        },
        index=dummy_ds.candidates,
    )

    mock_result = MatchingStrategyResult(
        classified_pairs=matched_pairs,
        execution_time_sec=0.35,
        peak_memory_mb=55.0,
        peak_cpu_percent=12.0,
        features_df=features_df,
    )
    mock_strategy.execute.return_value = mock_result

    mock_llm_meta = ExecutionMetadata(
        model_name="mock-llm",
        provider="mock",
        execution_time_seconds=0.12,
        prompt_tokens=60,
        completion_tokens=30,
        total_tokens=90,
    )

    call_count = 0

    async def mock_get_config(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise RuntimeError("Simulated transient LLM configuration failure")
        return mock_strategy, mock_llm_meta

    with (
        patch(
            "entity_resolution.benchmarking.matching_runner.discover_and_load",
            return_value=[dummy_ds],
        ),
        patch(
            "entity_resolution.benchmarking.matching_runner.LLMMatchingConfigGenerator.get_configuration",
            side_effect=mock_get_config,
        ),
    ):
        # 1. Run initial benchmark with 3 iterations (iter 2 will fail)
        summary = await run_matching_benchmark(
            data_dir=str(tmp_path),
            strategies=["weighted"],
            models=["mock-llm"],
            iterations=3,
            output_dir=tmp_path,
        )

        assert call_count == 3
        assert summary.failed_iterations_count == 1
        assert summary.total_iterations_count == 3

        run_dir = tmp_path / summary.run_id
        assert run_dir.exists()

        # Check required files exist
        assert (run_dir / "summary.json").exists()
        assert (run_dir / "summary.md").exists()
        assert (run_dir / "summary.csv").exists()

        strat_dir = (
            run_dir
            / "datasets"
            / "dummy_match_ds"
            / "mock-llm"
            / "ternary"
            / "weighted"
        )
        assert (strat_dir / "metrics.json").exists()
        assert (strat_dir / "report.md").exists()
        assert (strat_dir / "traces.jsonl").exists()
        assert (strat_dir / "iteration_1" / "matches.csv").exists()
        assert (strat_dir / "iteration_1" / "non_matches.csv").exists()

        # Assert no HTML files exist anywhere in output tree
        html_files = list(run_dir.rglob("*.html"))
        assert len(html_files) == 0, f"Found unexpected HTML files: {html_files}"

        # 2. In-place retry of failed run
        call_count = 0
        retry_summary = await retry_matching_benchmark_run(
            run_target=summary.run_id,
            output_dir=tmp_path,
        )

        assert call_count == 1  # only failed iteration 2 re-executed
        assert retry_summary.failed_iterations_count == 0

        # Verify metrics.json updated
        updated_metrics = json.loads(
            (strat_dir / "metrics.json").read_text(encoding="utf-8")
        )
        assert all(it["status"] == "SUCCESS" for it in updated_metrics["iterations"])


@pytest.mark.asyncio
async def test_matching_strategies_all_flag_expansion(tmp_path: Path):
    """Verifies --strategies all expands to both weighted and ecm strategies."""
    dummy_ds = _make_dummy_matching_dataset()
    mock_strategy = MagicMock(spec=WeightedScoreMatchingStrategy)
    mock_strategy.name = "Mock Strategy"

    cand_index = dummy_ds.candidates
    mock_result = MatchingStrategyResult(
        classified_pairs=cand_index,
        execution_time_sec=0.1,
        peak_memory_mb=10.0,
    )
    mock_strategy.execute.return_value = mock_result
    mock_llm_meta = ExecutionMetadata(
        model_name="mock-llm",
        provider="mock",
        execution_time_seconds=0.1,
        prompt_tokens=10,
        completion_tokens=5,
        total_tokens=15,
    )

    with (
        patch(
            "entity_resolution.benchmarking.matching_runner.discover_and_load",
            return_value=[dummy_ds],
        ),
        patch(
            "entity_resolution.benchmarking.matching_runner.LLMMatchingConfigGenerator.get_configuration",
            return_value=(mock_strategy, mock_llm_meta),
        ),
    ):
        summary = await run_matching_benchmark(
            data_dir=str(tmp_path),
            strategies=["all"],
            iterations=1,
            output_dir=tmp_path,
        )

        assert set(summary.strategies) == {
            "weighted",
            "dynamic_weighted",
            "kmeans",
        }
        assert summary.total_iterations_count == 3
        assert summary.failed_iterations_count == 0


@pytest.mark.asyncio
async def test_matching_report_embeds_llm_interaction(tmp_path: Path):
    """Verifies that actual LLM input and output are embedded in report.md."""
    dummy_ds = _make_dummy_matching_dataset()
    mock_strategy = MagicMock(spec=WeightedScoreMatchingStrategy)
    mock_strategy.name = "Weighted Score"
    mock_strategy.config = MagicMock()
    mock_strategy.config.model_dump.return_value = {
        "matching_columns": {
            "title": {"algorithm": "jarowinkler", "weight": 0.8}
        }
    }

    cand_index = dummy_ds.candidates
    mock_result = MatchingStrategyResult(
        classified_pairs=cand_index,
        execution_time_sec=0.2,
        peak_memory_mb=12.0,
    )
    mock_strategy.execute.return_value = mock_result

    log_file = tmp_path / "mock_llm_call.json"
    log_file.write_text(
        json.dumps({
            "system_prompt": "You are an expert Data Steward configuring ER matching.",
            "user_prompt": "### 1. Dataset Comparison Summary\nProfile info here.",
            "response": {
                "matching_columns": {
                    "title": {"algorithm": "jarowinkler", "weight": 0.8}
                }
            },
        }),
        encoding="utf-8",
    )

    mock_llm_meta = ExecutionMetadata(
        model_name="deepseek-v4-flash",
        provider="deepseek",
        execution_time_seconds=1.25,
        prompt_tokens=500,
        completion_tokens=150,
        total_tokens=650,
        prompt_template="You are an expert Data Steward configuring ER matching.",
        user_prompt="### 1. Dataset Comparison Summary\nProfile info here.",
        raw_response={
            "matching_columns": {
                "title": {"algorithm": "jarowinkler", "weight": 0.8}
            }
        },
        log_file_path=str(log_file),
    )

    with (
        patch(
            "entity_resolution.benchmarking.matching_runner.discover_and_load",
            return_value=[dummy_ds],
        ),
        patch(
            "entity_resolution.benchmarking.matching_runner.LLMMatchingConfigGenerator.get_configuration",
            return_value=(mock_strategy, mock_llm_meta),
        ),
    ):
        summary = await run_matching_benchmark(
            data_dir=str(tmp_path),
            strategies=["weighted"],
            models=["deepseek-v4-flash"],
            iterations=1,
            output_dir=tmp_path,
        )

        strat_dir = (
            tmp_path
            / summary.run_id
            / "datasets"
            / "dummy_match_ds"
            / "deepseek-v4-flash"
            / "ternary"
            / "weighted"
        )
        assert strat_dir.exists()

        # 1. Verify report.md contains embedded LLM inputs and outputs
        report_file = strat_dir / "report.md"
        assert report_file.exists()
        report_md = report_file.read_text(encoding="utf-8")

        assert "## LLM Strategy Configuration & Prompts" in report_md
        assert "- **Model**: `deepseek-v4-flash`" in report_md
        assert "- **Provider**: `deepseek`" in report_md
        assert "- **Latency**: `1.25s`" in report_md
        assert f"- **Log File**: `{log_file}`" in report_md
        assert "### LLM Output (Generated Strategy Configuration)" in report_md
        assert '"algorithm": "jarowinkler"' in report_md
        assert "### LLM Input Prompts" in report_md
        assert "<summary><b>System Prompt</b> (click to expand)</summary>" in report_md
        assert "You are an expert Data Steward" in report_md
        assert (
            "<summary><b>User Prompt (Comparative Profile & Exemplars)</b> "
            "(click to expand)</summary>"
            in report_md
        )
        assert "### 1. Dataset Comparison Summary" in report_md

        # 2. Verify llm_call.json was copied to strat_dir
        assert (strat_dir / "llm_call.json").exists()

        # 3. Verify metrics.json has llm_interaction
        metrics_data = json.loads(
            (strat_dir / "metrics.json").read_text(encoding="utf-8")
        )
        assert "llm_interaction" in metrics_data
        assert (
            metrics_data["llm_interaction"]["model_name"]
            == "deepseek-v4-flash"
        )
        assert (
            metrics_data["llm_interaction"]["system_prompt"]
            == "You are an expert Data Steward configuring ER matching."
        )
        assert metrics_data["llm_interaction"]["response"] == {
            "matching_columns": {
                "title": {"algorithm": "jarowinkler", "weight": 0.8}
            }
        }


def test_export_matching_buckets_capping_and_fn_preservation(tmp_path: Path):
    """Tests that _export_matching_buckets respects max_rows and preserves 100% of False Negatives."""
    from entity_resolution.benchmarking.matching_runner import _export_matching_buckets

    df_a = pd.DataFrame({"name": ["a1", "a2", "a3", "a4", "a5", "a6"]}, index=["1", "2", "3", "4", "5", "6"])
    df_b = pd.DataFrame({"name": ["b1", "b2", "b3", "b4", "b5", "b6"]}, index=["1", "2", "3", "4", "5", "6"])

    # 6 pairs total
    idx = pd.MultiIndex.from_tuples(
        [("1", "1"), ("2", "2"), ("3", "3"), ("4", "4"), ("5", "5"), ("6", "6")],
        names=["id_a", "id_b"],
    )
    features_df = pd.DataFrame({
        "prediction": ["non_match"] * 6,
        "final_score": [0.1, 0.9, 0.4, 0.3, 0.85, 0.2],
    }, index=idx)

    # Pairs ("3", "3") and ("6", "6") are ground truth matches (so they are False Negatives in non_matches!)
    gt_set = {("3", "3"), ("6", "6")}

    out_dir = tmp_path / "buckets"
    # Cap to 3 rows
    _export_matching_buckets(
        strat_dir=out_dir,
        clean_df_a=df_a,
        clean_df_b=df_b,
        features_df=features_df,
        gt_set=gt_set,
        iteration_index=1,
        max_rows=3,
    )

    non_matches_path = out_dir / "iteration_1" / "non_matches.csv"
    assert non_matches_path.exists()
    df_res = pd.read_csv(non_matches_path, dtype=str)

    # Row count should be exactly 3
    assert len(df_res) == 3

    # Both False Negatives must be present
    res_pairs = set(zip(df_res["id_a"], df_res["id_b"]))
    assert ("3", "3") in res_pairs
    assert ("6", "6") in res_pairs

    # The 3rd row must be the hardest True Negative (final_score = 0.9, pair ("2", "2"))
    assert ("2", "2") in res_pairs


@pytest.mark.asyncio
async def test_matching_config_generator_caches_only_first_response_on_force_llm(tmp_path: Path):
    """Tests that on force_llm=True, cache is bypassed each time but only the first response is cached."""
    from entity_resolution.benchmarking.matching_config_generator import (
        LLMMatchingConfigGenerator,
    )
    from entity_resolution.matching_strategies import DynamicWeightedMatchingStrategy
    from entity_resolution.matching_strategies.implementations import (
        WeightedScoreMatchingConfig,
    )
    from entity_resolution.models import ColumnMatchConfig, SimilarityAlgorithm
    from shared.profiling.engine import DataProfiler
    from shared.schema_models import TableField, TableResource, TableSchema

    cache_file = tmp_path / "matching_cache.json"
    gen = LLMMatchingConfigGenerator(cache_path=cache_file)

    df_dummy = pd.DataFrame({"col1": ["val1", "val2"]})
    p_a = DataProfiler.profile_dataframe(df_dummy, "a")
    p_b = DataProfiler.profile_dataframe(df_dummy, "b")
    res = TableResource(name="test_ds", schema=TableSchema(fields=[TableField(name="col1", type="string")]))

    config_1 = WeightedScoreMatchingConfig(
        reasoning="first run",
        matching_columns={"col1": ColumnMatchConfig(algorithm=SimilarityAlgorithm.EXACT, weight=1.0)},
    )
    config_2 = WeightedScoreMatchingConfig(
        reasoning="second run",
        matching_columns={"col1": ColumnMatchConfig(algorithm=SimilarityAlgorithm.JAROWINKLER, weight=0.7)},
    )

    call_num = 0
    async def mock_identify(*args, **kwargs):
        nonlocal call_num
        call_num += 1
        cfg = config_1 if call_num == 1 else config_2
        return cfg, None

    from unittest.mock import patch

    with patch(
        "entity_resolution.benchmarking.matching_config_generator.identify_indexing_config_via_llm",
        side_effect=mock_identify,
    ):
        # Call 1 with force_llm=True
        strat_1, _ = await gen.get_configuration(
            dataset_name="test_ds",
            profile_a=p_a,
            profile_b=p_b,
            table_resource=res,
            strategy_cls=DynamicWeightedMatchingStrategy,
            force_llm=True,
            model_name="mock-model",
        )
        assert strat_1.config.reasoning == "first run"
        assert call_num == 1

        # Verify cache file contains config_1
        cache_data = json.loads(cache_file.read_text(encoding="utf-8"))
        cache_key = "test_ds::DynamicWeightedMatchingStrategy::mock-model"
        assert cache_data[cache_key]["config_data"]["reasoning"] == "first run"

        # Call 2 with force_llm=True (should call LLM fresh, returning config_2, but NOT overwrite cache)
        strat_2, _ = await gen.get_configuration(
            dataset_name="test_ds",
            profile_a=p_a,
            profile_b=p_b,
            table_resource=res,
            strategy_cls=DynamicWeightedMatchingStrategy,
            force_llm=True,
            model_name="mock-model",
        )
        assert strat_2.config.reasoning == "second run"
        assert call_num == 2

        # Cache file must STILL retain config_1 (only first response is cached)
        cache_data_after = json.loads(cache_file.read_text(encoding="utf-8"))
        assert cache_data_after[cache_key]["config_data"]["reasoning"] == "first run"

        # Call 3 with force_llm=False (should load the cached first response)
        strat_3, _ = await gen.get_configuration(
            dataset_name="test_ds",
            profile_a=p_a,
            profile_b=p_b,
            table_resource=res,
            strategy_cls=DynamicWeightedMatchingStrategy,
            force_llm=False,
            model_name="mock-model",
        )
        assert strat_3.config.reasoning == "first run"
        assert call_num == 2  # No extra LLM call


