"""Tests for ER indexing benchmarking harness, resilience, and retry workflows."""

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
from entity_resolution.benchmarking.index_models import (
    IndexIterationMetrics,
)
from entity_resolution.benchmarking.index_runner import (
    _aggregate_index_metrics,
    retry_indexing_benchmark_run,
    run_indexing_benchmark,
)
from entity_resolution.dataset_loader import (
    DatasetMetadata,
    GroundTruthRef,
    GroundTruthType,
    LoadedDataset,
    TableRef,
)
from entity_resolution.indexing_strategies import (
    SortedNeighborhoodStrategy,
    StrategyResult,
)
from shared.agents import ExecutionMetadata


def _make_dummy_indexing_dataset() -> LoadedDataset:
    """Creates a minimal in-memory LoadedDataset for indexing tests."""
    df_a = pd.DataFrame(
        {"title": ["Laptop Pro", "Smartphone X"]}, index=["a1", "a2"]
    )
    df_b = pd.DataFrame(
        {"title": ["Laptop Pro", "Smartphone 10"]}, index=["b1", "b2"]
    )
    metadata = DatasetMetadata(
        name="dummy_index_ds",
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


def test_indexing_compute_mean_std_and_aggregation():
    """Verifies stats computation across indexing metric iterations."""
    it1 = IndexIterationMetrics(
        iteration_index=1,
        status=RunStatus.SUCCESS,
        recall=1.0,
        precision=0.5,
        reduction_ratio=0.75,
        indexing_time_sec=1.2,
        peak_memory_mb=50.0,
        token_usage=TokenUsage(prompt_tokens=100, total_tokens=150),
    )
    it2 = IndexIterationMetrics(
        iteration_index=2,
        status=RunStatus.SUCCESS,
        recall=0.8,
        precision=0.4,
        reduction_ratio=0.85,
        indexing_time_sec=0.8,
        peak_memory_mb=60.0,
        token_usage=TokenUsage(prompt_tokens=100, total_tokens=150),
    )
    it3 = IndexIterationMetrics(
        iteration_index=3,
        status=RunStatus.FAILED,
        error_message="Simulation failure",
    )

    dm = _aggregate_index_metrics(
        dataset_name="test_ds",
        domain="tech",
        strategy_name="Sorted Neighborhood",
        model_name="mock-model",
        iterations=[it1, it2, it3],
    )

    assert dm.successful_iterations_count == 2
    assert dm.failed_iterations_count == 1
    assert round(dm.mean_recall, 2) == 0.90
    assert dm.mean_indexing_time == 1.0
    assert dm.mean_memory_mb == 55.0
    assert dm.prompt_tokens == 200
    assert dm.total_tokens == 300


@pytest.mark.asyncio
async def test_indexing_resilience_and_retry_flow(tmp_path: Path):
    """Verifies indexing failure tolerance, artifact generation, no HTML, and retry."""
    dummy_ds = _make_dummy_indexing_dataset()
    mock_strategy = MagicMock(spec=SortedNeighborhoodStrategy)
    mock_strategy.name = "Sorted Neighborhood"
    mock_strategy.sorting_keys = ["title"]
    mock_strategy.window_size = 3

    cand_index = pd.MultiIndex.from_tuples([("a1", "b1"), ("a2", "b2")])
    mock_result = StrategyResult(
        candidate_pairs=cand_index,
        indexing_time_sec=0.25,
        peak_memory_mb=42.0,
        peak_cpu_percent=10.0,
    )
    mock_strategy.execute.return_value = mock_result

    mock_llm_meta = ExecutionMetadata(
        model_name="mock-llm",
        provider="mock",
        execution_time_seconds=0.1,
        prompt_tokens=50,
        completion_tokens=25,
        total_tokens=75,
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
            "entity_resolution.benchmarking.index_runner.discover_and_load",
            return_value=[dummy_ds],
        ),
        patch(
            "entity_resolution.benchmarking.index_runner.LLMIndexConfigGenerator.get_configuration",
            side_effect=mock_get_config,
        ),
    ):
        # 1. Run initial benchmark with 3 iterations (iter 2 will fail)
        summary = await run_indexing_benchmark(
            datasets=["dummy_index_ds"],
            strategies=["sn"],
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
            / "dummy_index_ds"
            / "gemini-3.8-flash"
            / "sorted_neighborhood"
        )
        assert (strat_dir / "metrics.json").exists()
        assert (strat_dir / "report.md").exists()
        assert (strat_dir / "traces.jsonl").exists()

        # Assert no HTML files exist anywhere in output tree
        html_files = list(run_dir.rglob("*.html"))
        assert len(html_files) == 0, f"Found unexpected HTML files: {html_files}"

        # 2. In-place retry of failed run
        # Reset call_count; retry should re-execute only failed iteration 2
        call_count = 0
        retry_summary = await retry_indexing_benchmark_run(
            run_target=summary.run_id,
            output_dir=tmp_path,
        )

        assert call_count == 1  # only 1 failed iteration re-executed
        assert retry_summary.failed_iterations_count == 0

        # Verify metrics.json updated
        updated_metrics = json.loads(
            (strat_dir / "metrics.json").read_text(encoding="utf-8")
        )
        assert all(it["status"] == "SUCCESS" for it in updated_metrics["iterations"])
