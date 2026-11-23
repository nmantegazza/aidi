"""Tests for shared benchmarking toolkit (models, layout, stats, reporting, resilience)."""

import json
from pathlib import Path

import pytest
from pydantic import BaseModel

from shared.benchmarking import (
    BenchmarkReportWriter,
    BenchmarkStatsEngine,
    FailedIterationDescriptor,
    RunLayoutManager,
    RunResilienceHelper,
    compute_mean_std,
)


class DummySummary(BaseModel):
    name: str
    count: int


def test_layout_manager_slug_sanitization():
    assert RunLayoutManager.sanitize_slug("gemini-2.0-flash:exp") == "gemini-2.0-flash_exp"
    assert RunLayoutManager.sanitize_slug("openai/gpt-4o") == "openai_gpt-4o"
    assert RunLayoutManager.sanitize_slug("  some / messy : name  ") == "some_messy_name"


def test_layout_manager_paths(tmp_path: Path):
    run_dir = RunLayoutManager.get_run_dir(tmp_path)
    assert run_dir.parent == tmp_path
    assert run_dir.name.startswith("run_")

    ds_model_dir = RunLayoutManager.get_dataset_model_dir(
        run_dir, "books", "gemini-2.0-flash"
    )
    assert ds_model_dir == run_dir / "datasets" / "books" / "gemini-2.0-flash"

    ds_model_strat_dir = RunLayoutManager.get_dataset_model_dir(
        run_dir, "books", "gemini-2.0-flash", strategy="tfidf"
    )
    assert ds_model_strat_dir == run_dir / "datasets" / "books" / "gemini-2.0-flash" / "tfidf"

    iter_dir = RunLayoutManager.get_iteration_dir(ds_model_strat_dir, 1)
    assert iter_dir == ds_model_strat_dir / "iterations" / "iter_1"


def test_stats_engine_compute_mean_std():
    # Empty
    empty_res = compute_mean_std([])
    assert empty_res.mean == 0.0
    assert empty_res.std == 0.0

    # Single
    single_res = BenchmarkStatsEngine.compute_mean_std([0.85])
    assert single_res.mean == 0.85
    assert single_res.std == 0.0
    assert single_res.min == 0.85
    assert single_res.max == 0.85

    # Multiple
    multi_res = BenchmarkStatsEngine.compute_mean_std([0.8, 0.9, 1.0])
    assert multi_res.mean == 0.9
    assert round(multi_res.std, 4) == 0.1
    assert multi_res.min == 0.8
    assert multi_res.max == 1.0
    assert multi_res.min_val == 0.8
    assert multi_res.max_val == 1.0


def test_stats_engine_consensus_and_flakiness():
    # Scalar sequence consensus
    assert BenchmarkStatsEngine.compute_consensus_ratio(["a", "a", "a"]) == 1.0
    assert BenchmarkStatsEngine.compute_consensus_ratio(["a", "a", "b"]) == pytest.approx(0.666667, 1e-4)

    # Collection sequence consensus
    set_consensus = BenchmarkStatsEngine.compute_consensus_ratio([
        {"p1", "p2"},
        {"p1", "p2", "p3"},
    ])
    assert set_consensus == pytest.approx(2 / 3, 1e-4)

    # Flakiness
    flakiness = BenchmarkStatsEngine.compute_jaccard_flakiness([
        {"match_1", "match_2"},
        {"match_1", "match_3"},
    ])
    assert "match_1" in flakiness["consistent_items"]
    assert "match_2" in flakiness["flaky_items"]
    assert "match_3" in flakiness["flaky_items"]
    assert flakiness["flaky_items"]["match_2"] == 0.5
    assert flakiness["stability_ratio"] == pytest.approx(1 / 3, 1e-4)


def test_reporting_checkpoint_summaries(tmp_path: Path):
    run_dir = tmp_path / "run_test"
    summary_model = DummySummary(name="test_run", count=42)
    summary_rows = [{"dataset": "ds1", "f1": 0.95}, {"dataset": "ds2", "f1": 0.88}]
    md_content = "# Test Summary\n\nAll passed."

    BenchmarkReportWriter.checkpoint_summaries(
        run_dir=run_dir,
        summary_data=summary_model,
        summary_rows=summary_rows,
        markdown_content=md_content,
    )

    assert (run_dir / "summary.json").exists()
    assert (run_dir / "summary.csv").exists()
    assert (run_dir / "summary.md").exists()

    data = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    assert data["name"] == "test_run"
    assert data["count"] == 42

    csv_text = (run_dir / "summary.csv").read_text(encoding="utf-8")
    assert "dataset,f1" in csv_text
    assert "ds1,0.95" in csv_text

    md_text = (run_dir / "summary.md").read_text(encoding="utf-8")
    assert "# Test Summary" in md_text


def test_resilience_resolve_and_find_failed(tmp_path: Path):
    base_dir = tmp_path / "benchmarks"
    run_dir1 = base_dir / "run_20260916_100000"
    run_dir2 = base_dir / "run_20260916_110000"
    run_dir1.mkdir(parents=True)
    run_dir2.mkdir(parents=True)

    # Resolve latest
    latest = RunResilienceHelper.resolve_run_dir("latest", base_dir)
    assert latest == run_dir2.resolve()

    # Resolve by name without prefix
    resolved = RunResilienceHelper.resolve_run_dir("20260916_100000", base_dir)
    assert resolved == run_dir1.resolve()

    # Populate a failed iteration in run_dir2
    ds_dir = run_dir2 / "datasets" / "books" / "gemini" / "tfidf"
    ds_dir.mkdir(parents=True)
    metrics_content = {
        "dataset_name": "books",
        "iterations": [
            {"iteration_index": 1, "status": "SUCCESS"},
            {"iteration_index": 2, "status": "FAILED", "error_message": "Rate limit exceeded"},
        ],
    }
    (ds_dir / "metrics.json").write_text(json.dumps(metrics_content), encoding="utf-8")

    failed = RunResilienceHelper.find_failed_iterations(run_dir2)
    assert len(failed) == 1
    assert isinstance(failed[0], FailedIterationDescriptor)
    assert failed[0].dataset_name == "books"
    assert failed[0].model_name == "gemini"
    assert failed[0].strategy_name == "tfidf"
    assert failed[0].iteration_index == 2
    assert failed[0].error_message == "Rate limit exceeded"
