"""Tests for ER benchmarking resilience, statistics, and retry workflows."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from entity_resolution.benchmarking.common.models import (
    ERFlakinessAnalysis,
    ERIterationMetrics,
    RunStatus,
    compute_mean_std,
)
from entity_resolution.benchmarking.common.resilience import (
    resolve_run_directory,
)
from entity_resolution.benchmarking.models import BenchmarkConfig
from entity_resolution.benchmarking.runner import (
    _aggregate_dataset_metrics,
    retry_benchmark_run,
    run_entity_resolution_benchmark,
)
from entity_resolution.dataset_loader import (
    DatasetMetadata,
    GroundTruthRef,
    GroundTruthType,
    LoadedDataset,
    TableRef,
)
from entity_resolution.models import (
    ColumnMatchConfig,
    EntityResolutionResult,
    ERPipelineConfiguration,
    SimilarityAlgorithm,
)
from shared.agents import ExecutionMetadata
from shared.profiling.engine import DataProfiler

# ---------------------------------------------------------------------------
# Unit tests: compute_mean_std and flakiness
# ---------------------------------------------------------------------------


def test_compute_mean_std_empty_and_values():
    """Verify compute_mean_std handles empty, single, and multiple inputs."""
    empty_stats = compute_mean_std([])
    assert empty_stats.mean == 0.0
    assert empty_stats.std == 0.0
    assert empty_stats.min == 0.0
    assert empty_stats.max == 0.0

    single_stats = compute_mean_std([0.85])
    assert single_stats.mean == 0.85
    assert single_stats.std == 0.0
    assert single_stats.min == 0.85
    assert single_stats.max == 0.85

    multi_stats = compute_mean_std([0.80, 0.90, 1.00])
    assert multi_stats.mean == 0.90
    assert multi_stats.std == 0.10
    assert multi_stats.min == 0.80
    assert multi_stats.max == 1.00


def test_flakiness_analysis_aggregation():
    """Verify flakiness analysis correctly groups consistent and flaky pairs."""
    pair1 = ("a1", "b1")
    pair2 = ("a2", "b2")
    pair3 = ("a3", "b3")

    # 3 successful iterations
    it1 = ERIterationMetrics(
        iteration_index=1,
        status=RunStatus.SUCCESS,
        precision=1.0,
        recall=1.0,
        f1=1.0,
    )
    it2 = ERIterationMetrics(
        iteration_index=2,
        status=RunStatus.SUCCESS,
        precision=1.0,
        recall=1.0,
        f1=1.0,
    )
    it3 = ERIterationMetrics(
        iteration_index=3,
        status=RunStatus.SUCCESS,
        precision=0.5,
        recall=0.5,
        f1=0.5,
    )

    pair_sets = [
        {pair1, pair2},  # iter 1
        {pair1, pair2},  # iter 2
        {pair1, pair3},  # iter 3
    ]

    metrics = _aggregate_dataset_metrics(
        dataset_name="test_flakiness",
        domain="e-commerce",
        num_rows_a=10,
        num_rows_b=10,
        ground_truth_count=2,
        iterations=[it1, it2, it3],
        match_pairs_list=pair_sets,
    )

    assert metrics.flakiness_analysis is not None
    fa = metrics.flakiness_analysis
    assert isinstance(fa, ERFlakinessAnalysis)
    # pair1 appeared in all 3 runs
    assert ("a1", "b1") in fa.consistent_matches
    # pair2 appeared in 2 of 3 runs (66.67%)
    assert "(a2, b2)" in fa.flaky_matches
    assert fa.flaky_matches["(a2, b2)"] == pytest.approx(0.6667, abs=1e-3)
    # pair3 appeared in 1 of 3 runs (33.33%)
    assert "(a3, b3)" in fa.flaky_matches
    assert fa.flaky_matches["(a3, b3)"] == pytest.approx(0.3333, abs=1e-3)
    # Stability ratio: 1 consistent out of 3 unique pairs
    assert fa.stability_ratio == pytest.approx(1 / 3, abs=1e-3)


# ---------------------------------------------------------------------------
# Resilience & retry end-to-end integration test
# ---------------------------------------------------------------------------


def _make_dummy_loaded_dataset() -> LoadedDataset:
    """Creates a minimal in-memory LoadedDataset."""
    df_a = pd.DataFrame(
        {"title": ["Laptop Pro", "Smartphone X"]}, index=["a1", "a2"]
    )
    df_b = pd.DataFrame(
        {"title": ["Laptop Pro", "Smartphone 10"]}, index=["b1", "b2"]
    )
    metadata = DatasetMetadata(
        name="dummy_ds",
        domain="electronics",
        ground_truth_type=GroundTruthType.EXHAUSTIVE,
        table_a=TableRef(file="a.csv", id_column="id"),
        table_b=TableRef(file="b.csv", id_column="id"),
        ground_truth=GroundTruthRef(
            file="gt.csv", column_a="id_a", column_b="id_b"
        ),
    )
    return LoadedDataset(
        metadata=metadata,
        table_a=df_a,
        table_b=df_b,
        ground_truth={("a1", "b1"), ("a2", "b2")},
        candidates=None,
    )


def _make_dummy_result(
    df_a: pd.DataFrame, df_b: pd.DataFrame
) -> EntityResolutionResult:
    """Creates a mock EntityResolutionResult."""
    profile_a = DataProfiler.profile_dataframe(df_a, "dummy_a")
    profile_b = DataProfiler.profile_dataframe(df_b, "dummy_b")
    config = ERPipelineConfiguration(
        sorting_keys=["title"],
        window_size=3,
        matching_columns={
            "title": ColumnMatchConfig(algorithm=SimilarityAlgorithm.JAROWINKLER)
        },
        reasoning="Test reasoning",
    )
    meta = ExecutionMetadata(
        model_name="mock-model",
        provider="mock",
        execution_time_seconds=0.15,
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
    )
    candidate_pairs = pd.MultiIndex.from_tuples([("a1", "b1"), ("a2", "b2")])
    matches_df = pd.DataFrame(
        {"title": [1.0], "aggregate_score": [0.95]},
        index=pd.MultiIndex.from_tuples(
            [("a1", "b1")], names=["left_id", "right_id"]
        ),
    )
    return EntityResolutionResult(
        config=config,
        er_config_metadata=meta,
        profile_a=profile_a,
        profile_b=profile_b,
        df_a_clean=df_a,
        df_b_clean=df_b,
        candidate_pairs=candidate_pairs,
        matches=matches_df,
        uncertain=pd.DataFrame(),
        non_matches=pd.DataFrame(),
    )


@pytest.mark.asyncio
async def test_benchmark_resilience_and_retry_flow(tmp_path: Path):
    """Verifies failure tolerance, artifact generation, no HTML, and targeted retry."""
    dummy_ds = _make_dummy_loaded_dataset()
    mock_result = _make_dummy_result(dummy_ds.table_a, dummy_ds.table_b)

    call_count = 0

    async def mock_run_er(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        # Fail on iteration 2
        if call_count == 2:
            raise RuntimeError("Simulated transient API rate limit error")
        return mock_result

    with (
        patch(
            "entity_resolution.benchmarking.runner.discover_and_load",
            return_value=[dummy_ds],
        ),
        patch(
            "entity_resolution.benchmarking.runner.run_entity_resolution",
            side_effect=mock_run_er,
        ),
    ):
        bench_conf = BenchmarkConfig(
            models=["mock_model"],
            iterations=3,
            datasets=["dummy_ds"],
            save_dataset_outputs=True,
            output_dir=tmp_path,
        )

        # 1. Run initial benchmark with 1 failure out of 3 iterations
        summary = await run_entity_resolution_benchmark(
            bench_conf, output_dir=tmp_path
        )

        assert call_count == 3
        assert summary.failed_iterations_count == 1
        assert summary.total_iterations_count == 3

        run_dir = tmp_path / summary.run_id
        assert run_dir.exists()

        # 2. Check root artifacts exist and NO HTML files were created
        assert (run_dir / "summary.json").exists()
        assert (run_dir / "summary.md").exists()
        assert (run_dir / "summary.csv").exists()

        html_files = list(run_dir.rglob("*.html"))
        assert len(html_files) == 0, f"Found unexpected HTML files: {html_files}"

        # 3. Check failure forensic section in summary.md
        summary_md_text = (run_dir / "summary.md").read_text(encoding="utf-8")
        assert "Failed Runs & Remediation" in summary_md_text
        assert "--retry" in summary_md_text

        # 4. Check nested dataset artifacts
        ds_dir = run_dir / "datasets" / "dummy_ds" / "mock_model"
        assert (ds_dir / "metrics.json").exists()
        assert (ds_dir / "report.md").exists()
        assert (ds_dir / "traces.jsonl").exists()
        assert (ds_dir / "matches.csv").exists()

        # Check metrics.json contents
        metrics_data = json.loads(
            (ds_dir / "metrics.json").read_text(encoding="utf-8")
        )
        assert len(metrics_data["iterations"]) == 3
        assert metrics_data["iterations"][0]["status"] == "SUCCESS"
        assert metrics_data["iterations"][1]["status"] == "FAILED"
        assert (
            "Simulated transient API rate limit error"
            in metrics_data["iterations"][1]["error_message"]
        )
        assert metrics_data["iterations"][2]["status"] == "SUCCESS"

        # 5. Execute targeted --retry
        # On retry, the mock runner will succeed
        retry_call_count = 0

        async def mock_retry_run_er(*args, **kwargs):
            nonlocal retry_call_count
            retry_call_count += 1
            return mock_result

        with patch(
            "entity_resolution.benchmarking.runner.run_entity_resolution",
            side_effect=mock_retry_run_er,
        ):
            retry_summary = await retry_benchmark_run(
                run_target=summary.run_id,
                output_dir=tmp_path,
            )

            # CRITICAL: Verify ONLY the 1 failed iteration was executed!
            assert retry_call_count == 1
            assert retry_summary.failed_iterations_count == 0
            assert retry_summary.total_iterations_count == 3

            # Check metrics.json was updated in-place
            updated_metrics = json.loads(
                (ds_dir / "metrics.json").read_text(encoding="utf-8")
            )
            for it in updated_metrics["iterations"]:
                assert it["status"] == "SUCCESS"

            # Check summary.md no longer has failure section
            updated_md = (run_dir / "summary.md").read_text(encoding="utf-8")
            assert "Failed Runs & Remediation" not in updated_md

            # Check still no HTML files
            assert len(list(run_dir.rglob("*.html"))) == 0


def test_resolve_run_directory_utility(tmp_path: Path):
    """Verify resolve_run_directory handles 'latest', IDs, and nonexistent paths."""
    run1 = tmp_path / "run_20260101_100000"
    run2 = tmp_path / "run_20260102_100000"
    run1.mkdir()
    run2.mkdir()

    # Test 'latest'
    latest = resolve_run_directory("latest", tmp_path)
    assert latest.name == "run_20260102_100000"

    # Test direct run ID
    resolved = resolve_run_directory("run_20260101_100000", tmp_path)
    assert resolved.name == "run_20260101_100000"

    # Test missing directory
    with pytest.raises(FileNotFoundError):
        resolve_run_directory("nonexistent_run", tmp_path)
