"""Tests for Data Fusion Benchmarking components and multi-iteration execution."""

import json
from pathlib import Path

import pandas as pd

from data_fusion.benchmarking.evaluation import DataFusionEvaluator
from data_fusion.benchmarking.loader import BenchmarkDataLoader
from data_fusion.benchmarking.models import (
    BenchmarkRunSummary,
    FusionDatasetAggregatedMetrics,
    FusionIterationMetrics,
    MetricsPayload,
    RunStatus,
)
from data_fusion.benchmarking.normalization import normalize_string
from data_fusion.benchmarking.runner import (
    retry_data_fusion_benchmark_run,
    run_data_fusion_benchmark,
)


def test_normalize_string_basic():
    """Tests normal text cleaning, NFKD decomposition, and honorific stripping."""
    res = normalize_string("Dr. John Smith, Ph.D.")
    assert res == {"john", "smith", "ph", "d"}

    res_honorific = normalize_string("Prof. Erich Gamma")
    assert res_honorific == {"erich", "gamma"}


def test_normalize_string_word_order():
    """Tests that word order differences yield identical token sets."""
    set1 = normalize_string("Gamma, Erich")
    set2 = normalize_string("Erich Gamma")
    assert set1 == set2


def test_normalize_string_empty():
    """Tests handling of empty, None, and NaN inputs."""
    assert normalize_string("") == set()
    assert normalize_string(None) == set()
    assert normalize_string("NaN") == set()


def test_evaluator_metrics():
    """Tests Absolute and Reachable metric calculations."""
    evaluator = DataFusionEvaluator()

    df_a = pd.DataFrame({
        "id": ["1", "2"],
        "author": ["Erich Gamma", "Timothy O'Leary"],
    })
    df_b = pd.DataFrame({
        "id": ["1", "2"],
        "author": ["Richard Helm", "Linda O'Leary"],
    })
    df_gt = pd.DataFrame({
        "id": ["1", "2"],
        "author": [
            "Erich Gamma; Richard Helm",
            "Timothy O'Leary; Linda O'Leary",
        ],
    })
    df_pred = pd.DataFrame({
        "id": ["1", "2"],
        "author": ["Erich Gamma", "Timothy O'Leary; Linda O'Leary"],
    })

    abs_m, reach_m = evaluator.evaluate_predictions(
        df_pred=df_pred,
        df_gt=df_gt,
        df_a=df_a,
        df_b=df_b,
        entity_id_col="id",
        attributes=["author"],
    )

    assert isinstance(abs_m, MetricsPayload)
    assert isinstance(reach_m, MetricsPayload)
    assert abs_m.precision == 1.0
    assert abs_m.recall < 1.0  # Missed Richard Helm for record 1
    assert reach_m.precision == 1.0


def test_loader(tmp_path: Path):
    """Tests BenchmarkDataLoader with synthetic dataset files."""
    dataset_dir = tmp_path / "processed" / "test_ds"
    dataset_dir.mkdir(parents=True)

    meta = {
        "dataset_id": "test_ds",
        "entity_id_column": "id",
        "attributes": ["title"],
    }
    with open(dataset_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f)

    pd.DataFrame({"id": ["1"], "title": ["A"]}).to_csv(
        dataset_dir / "source_a.csv", index=False
    )
    pd.DataFrame({"id": ["1"], "title": ["B"]}).to_csv(
        dataset_dir / "source_b.csv", index=False
    )
    pd.DataFrame({"id": ["1"], "title": ["A"]}).to_csv(
        dataset_dir / "ground_truth.csv", index=False
    )

    loader = BenchmarkDataLoader(base_dir=str(tmp_path / "processed"))
    df_a, df_b, df_gt, metadata = loader.load_dataset("test_ds")

    assert len(df_a) == 1
    assert len(df_b) == 1
    assert len(df_gt) == 1
    assert metadata["dataset_id"] == "test_ds"


def test_extract_disagreements():
    """Tests extract_disagreements on value mismatches."""
    evaluator = DataFusionEvaluator()
    df_a = pd.DataFrame(
        {"id": ["1", "2"], "title": ["Clean Code", "Design Patterns"]}
    )
    df_b = pd.DataFrame(
        {"id": ["1", "2"], "title": ["Clean Code Book", "Gang of Four"]}
    )
    df_gt = pd.DataFrame({
        "id": ["1", "2"],
        "title": ["Clean Code", "Design Patterns Elements"],
    })
    df_pred = pd.DataFrame(
        {"id": ["1", "2"], "title": ["Clean Code", "Gang of Four"]}
    )

    disagreements = evaluator.extract_disagreements(
        df_pred=df_pred,
        df_gt=df_gt,
        df_a=df_a,
        df_b=df_b,
        entity_id_col="id",
        attributes=["title"],
        audit_log={"title": "trust_source"},
    )

    assert len(disagreements) == 1
    row = disagreements.iloc[0]
    assert row["id"] == "2"
    assert row["attribute"] == "title"
    assert row["strategy"] == "trust_source"
    assert row["predicted"] == "Gang of Four"
    assert row["ground_truth"] == "Design Patterns Elements"


def test_multi_iteration_execution_and_metrics_aggregation(tmp_path: Path):
    """Tests multi-iteration execution, directory structure, metrics.json, and summaries."""
    # Create mock dataset
    data_dir = tmp_path / "processed" / "mock_books"
    data_dir.mkdir(parents=True)
    meta = {
        "dataset_id": "mock_books",
        "entity_id_column": "id",
        "attributes": ["title"],
    }
    (data_dir / "metadata.json").write_text(
        json.dumps(meta), encoding="utf-8"
    )

    pd.DataFrame({"id": ["1", "2"], "title": ["Title 1", "Title 2"]}).to_csv(
        data_dir / "source_a.csv", index=False
    )
    pd.DataFrame({"id": ["1", "2"], "title": ["Title 1", "Alt 2"]}).to_csv(
        data_dir / "source_b.csv", index=False
    )
    pd.DataFrame({"id": ["1", "2"], "title": ["Title 1", "Title 2"]}).to_csv(
        data_dir / "ground_truth.csv", index=False
    )

    from unittest.mock import patch

    with patch(
        "data_fusion.benchmarking.runner.BenchmarkDataLoader",
        return_value=BenchmarkDataLoader(base_dir=str(tmp_path / "processed")),
    ):
        summary = run_data_fusion_benchmark(
            datasets=["mock_books"],
            baselines=["trust_a"],
            iterations=2,
            output_dir=tmp_path / "df_benchmarks",
        )

        assert isinstance(summary, BenchmarkRunSummary)
        assert summary.iterations == 2
        assert "mock_books" in summary.datasets

        run_dir = tmp_path / "df_benchmarks" / summary.run_id
        assert run_dir.exists()
        assert (run_dir / "summary.json").exists()
        assert (run_dir / "summary.csv").exists()
        assert (run_dir / "summary.md").exists()
        # Ensure clean break: no legacy report.json or flat dataset_model.json
        assert not (run_dir / "report.json").exists()
        assert not (run_dir / "datasets" / "mock_books_trust_a.json").exists()

        # Check iteration folders
        ds_model_dir = run_dir / "datasets" / "mock_books" / "trust_a"
        assert (ds_model_dir / "iterations" / "iter_1" / "fused.csv").exists()
        assert (ds_model_dir / "iterations" / "iter_2" / "fused.csv").exists()

        # Check metrics.json
        metrics_file = ds_model_dir / "metrics.json"
        assert metrics_file.exists()
        dm = FusionDatasetAggregatedMetrics.model_validate_json(
            metrics_file.read_text(encoding="utf-8")
        )
        assert dm.dataset_id == "mock_books"
        assert dm.model_name == "trust_a"
        assert len(dm.iterations) == 2
        assert dm.mean_abs_f1 == 1.0
        assert dm.std_abs_f1 == 0.0


def test_data_fusion_retry_run(tmp_path: Path):
    """Tests in-place failure recovery for Data Fusion benchmarking."""
    run_dir = tmp_path / "run_20260916_120000"
    model_ds_dir = run_dir / "datasets" / "mock_books" / "trust_a"
    iter_1_dir = model_ds_dir / "iterations" / "iter_1"
    iter_2_dir = model_ds_dir / "iterations" / "iter_2"
    iter_1_dir.mkdir(parents=True)
    iter_2_dir.mkdir(parents=True)

    # Iteration 1 is success, Iteration 2 is failed
    it1 = FusionIterationMetrics(
        iteration_index=1,
        status=RunStatus.SUCCESS,
        absolute_metrics=MetricsPayload(precision=1.0, recall=1.0, f1=1.0),
        reachable_metrics=MetricsPayload(precision=1.0, recall=1.0, f1=1.0),
        latency_seconds=0.1,
    )
    it2 = FusionIterationMetrics(
        iteration_index=2,
        status=RunStatus.FAILED,
        error_message="Simulated connection timeout",
    )
    dm = FusionDatasetAggregatedMetrics(
        dataset_id="mock_books",
        model_name="trust_a",
        status=RunStatus.PARTIAL,
        iterations=[it1, it2],
    )
    (model_ds_dir / "metrics.json").write_text(
        dm.model_dump_json(indent=2), encoding="utf-8"
    )

    # Mock dataset
    data_dir = tmp_path / "processed" / "mock_books"
    data_dir.mkdir(parents=True)
    meta = {
        "dataset_id": "mock_books",
        "entity_id_column": "id",
        "attributes": ["title"],
    }
    (data_dir / "metadata.json").write_text(
        json.dumps(meta), encoding="utf-8"
    )

    pd.DataFrame({"id": ["1"], "title": ["Book 1"]}).to_csv(
        data_dir / "source_a.csv", index=False
    )
    pd.DataFrame({"id": ["1"], "title": ["Book 1"]}).to_csv(
        data_dir / "source_b.csv", index=False
    )
    pd.DataFrame({"id": ["1"], "title": ["Book 1"]}).to_csv(
        data_dir / "ground_truth.csv", index=False
    )

    from unittest.mock import patch

    with patch(
        "data_fusion.benchmarking.runner.BenchmarkDataLoader",
        return_value=BenchmarkDataLoader(base_dir=str(tmp_path / "processed")),
    ):
        retry_summary = retry_data_fusion_benchmark_run(
            run_target=run_dir,
            output_dir=tmp_path,
        )

        assert retry_summary.failed_iterations_count == 0
        updated_dm = FusionDatasetAggregatedMetrics.model_validate_json(
            (model_ds_dir / "metrics.json").read_text(encoding="utf-8")
        )
        assert updated_dm.status == RunStatus.SUCCESS
        assert all(it.status == RunStatus.SUCCESS for it in updated_dm.iterations)
        assert (iter_2_dir / "fused.csv").exists()
