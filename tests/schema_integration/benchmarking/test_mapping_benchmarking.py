"""Unit tests for schema mapping benchmarking suite (Valentine)."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest

from schema_integration.benchmarking.mapping.baselines import (
    ExactMatcher,
)
from schema_integration.benchmarking.mapping.evaluation import (
    MappingEvaluator,
)
from schema_integration.benchmarking.mapping.loader import (
    BenchmarkDataset,
    SchemaMappingLoader,
)
from schema_integration.benchmarking.mapping.models import (
    AggregatedMetrics,
    DatasetBenchmarkResult,
    IterationResult,
    MatchMetrics,
)
from schema_integration.benchmarking.mapping.runner import (
    MappingRunner,
)
from schema_integration.mapping.models import (
    DirectCopy,
    MappingReport,
    MappingRule,
    TypeCast,
)
from shared.agents import ExecutionMetadata
from shared.schema_models import (
    DataPackage,
    TableField,
    TableResource,
    TableSchema,
)


@pytest.fixture
def mock_mapping_dataset_dir(tmp_path: Path) -> Path:
    """Create a mock standardized Valentine dataset folder structure."""
    ds_dir = tmp_path / "test_dataset_unionable"
    ds_dir.mkdir(parents=True)

    df_src = pd.DataFrame(
        {
            "user_id": [1, 2, 3],
            "full_name": ["Alice Smith", "Bob Jones", "Charlie Brown"],
            "age": [25, 30, 35],
        }
    )
    df_tgt = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "name": ["Alice Smith", "Bob Jones", "Charlie Brown"],
            "years": [25, 30, 35],
        }
    )

    df_src.to_csv(ds_dir / "test_dataset_unionable_source.csv", index=False)
    df_tgt.to_csv(ds_dir / "test_dataset_unionable_target.csv", index=False)

    mapping_data = {
        "dataset_name": "test_dataset_unionable",
        "domain": "Synthetic",
        "scenario": "Unionable",
        "matches": [
            {"source_column": "user_id", "target_column": "id"},
            {"source_column": "full_name", "target_column": "name"},
            {"source_column": "age", "target_column": "years"},
        ],
    }
    with open(
        ds_dir / "test_dataset_unionable_mapping.json", "w", encoding="utf-8"
    ) as f:
        json.dump(mapping_data, f, indent=2)

    metadata = {
        "name": "test_dataset_unionable",
        "domain": "Synthetic",
        "scenario": "Unionable",
    }
    with open(ds_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return ds_dir


def test_schema_mapping_loader(mock_mapping_dataset_dir: Path) -> None:
    """Test loading a Valentine benchmark dataset."""
    ds = SchemaMappingLoader.load_dataset(mock_mapping_dataset_dir)

    assert isinstance(ds, BenchmarkDataset)
    assert ds.name == "test_dataset_unionable"
    assert len(ds.source_df) == 3
    assert len(ds.target_df) == 3
    assert len(ds.ground_truth) == 3
    assert ("user_id", "id") in ds.ground_truth


def test_exact_matcher() -> None:
    """Test ExactMatcher case-insensitive baseline."""
    df_src = pd.DataFrame({"First_Name": [1], "age": [2], "EXTRA": [3]})
    df_tgt = pd.DataFrame({"first_name": [1], "AGE": [2], "other": [4]})

    matches = ExactMatcher.match(df_src, df_tgt)
    assert matches == {("First_Name", "first_name"), ("age", "AGE")}


def test_mapping_evaluator_metrics() -> None:
    """Test precision, recall, F1 computation in MappingEvaluator."""
    pred = {("a", "x"), ("b", "y"), ("extra", "z")}
    gt = {("a", "x"), ("b", "y"), ("missed", "w")}

    metrics = MappingEvaluator.compute_match_metrics(pred, gt)
    assert metrics.true_positives == 2
    assert metrics.false_positives == 1
    assert metrics.false_negatives == 1
    assert metrics.precision == pytest.approx(0.6667, rel=1e-3)
    assert metrics.recall == pytest.approx(0.6667, rel=1e-3)
    assert metrics.f1 == pytest.approx(0.6667, rel=1e-3)


def test_mapping_evaluator_iteration() -> None:
    """Test evaluating a MappingReport iteration."""
    report = MappingReport(
        rules=[
            MappingRule(
                source_label="src",
                source_table="src",
                target_table="tgt",
                target_column="name",
                source_columns=["full_name"],
                transformations=[DirectCopy()],
            ),
            MappingRule(
                source_label="src",
                source_table="src",
                target_table="tgt",
                target_column="years",
                source_columns=["age"],
                transformations=[TypeCast(target_type="integer")],
            ),
        ]
    )

    src_pkg = DataPackage(
        schema_name="src",
        resources=[
            TableResource(
                name="src",
                schema=TableSchema(
                    fields=[
                        TableField(name="full_name", type="string"),
                        TableField(name="age", type="string"),
                    ]
                ),
            )
        ],
    )
    tgt_pkg = DataPackage(
        schema_name="tgt",
        resources=[
            TableResource(
                name="tgt",
                schema=TableSchema(
                    fields=[
                        TableField(name="name", type="string"),
                        TableField(name="years", type="integer"),
                    ]
                ),
            )
        ],
    )
    dataset = BenchmarkDataset(
        name="test",
        domain="synthetic",
        scenario="unionable",
        source_package=src_pkg,
        target_package=tgt_pkg,
        source_df=pd.DataFrame(),
        target_df=pd.DataFrame(),
        ground_truth={("full_name", "name"), ("age", "years")},
    )

    it_res = MappingEvaluator.evaluate_mapping_iteration(
        report=report, dataset=dataset, iteration_index=1
    )
    assert it_res.metrics.f1 == 1.0
    assert it_res.transformation_counts == {"direct_copy": 1, "type_cast": 1}
    assert len(it_res.field_inspections) == 2


def test_exact_matcher_multi_table() -> None:
    """Test strict qualified exact matching across multi-table schemas."""
    src_pkg = DataPackage(
        schema_name="src",
        resources=[
            TableResource(
                name="customer",
                schema=TableSchema(
                    fields=[
                        TableField(name="cust_id", type="integer"),
                        TableField(name="name", type="string"),
                    ]
                ),
            ),
            TableResource(
                name="branch",
                schema=TableSchema(
                    fields=[
                        TableField(name="branch_id", type="integer"),
                        TableField(name="name", type="string"),
                    ]
                ),
            ),
        ],
    )
    tgt_pkg = DataPackage(
        schema_name="tgt",
        resources=[
            TableResource(
                name="customer",
                schema=TableSchema(
                    fields=[
                        TableField(name="cust_id", type="integer"),
                        TableField(name="full_name", type="string"),
                    ]
                ),
            ),
            TableResource(
                name="branch",
                schema=TableSchema(
                    fields=[
                        TableField(name="branch_id", type="integer"),
                        TableField(name="name", type="string"),
                    ]
                ),
            ),
        ],
    )

    matches = ExactMatcher.match_multi_table(src_pkg, tgt_pkg)
    # customer.cust_id and branch.branch_id and branch.name match identically
    assert ("customer.cust_id", "customer.cust_id") in matches
    assert ("branch.branch_id", "branch.branch_id") in matches
    assert ("branch.name", "branch.name") in matches
    # customer.name vs customer.full_name does not match
    assert ("customer.name", "customer.full_name") not in matches
    assert len(matches) == 3


def test_multi_table_mapping_evaluation() -> None:
    """Test evaluation of qualified mapping rules for multi-table datasets."""
    report = MappingReport(
        rules=[
            MappingRule(
                source_label="src",
                source_table="customer",
                target_table="borrower",
                target_column="customer_id",
                source_columns=["custid"],
                transformations=[DirectCopy()],
            ),
            MappingRule(
                source_label="src",
                source_table="branch",
                target_table="branch",
                target_column="branch_name",
                source_columns=["name"],
                transformations=[DirectCopy()],
            ),
        ]
    )

    src_pkg = DataPackage(
        schema_name="src",
        resources=[
            TableResource(
                name="customer",
                schema=TableSchema(fields=[TableField(name="custid", type="string")]),
            ),
            TableResource(
                name="branch",
                schema=TableSchema(fields=[TableField(name="name", type="string")]),
            ),
        ],
    )
    tgt_pkg = DataPackage(
        schema_name="tgt",
        resources=[
            TableResource(
                name="borrower",
                schema=TableSchema(fields=[TableField(name="customer_id", type="string")]),
            ),
            TableResource(
                name="branch",
                schema=TableSchema(fields=[TableField(name="branch_name", type="string")]),
            ),
        ],
    )

    dataset = BenchmarkDataset(
        name="test_multi",
        domain="Banking",
        scenario="Multi-Table Relational Schema",
        source_package=src_pkg,
        target_package=tgt_pkg,
        source_df=pd.DataFrame(),
        target_df=pd.DataFrame(),
        ground_truth={
            ("customer.custid", "borrower.customer_id"),
            ("branch.name", "branch.branch_name"),
        },
        category="multi_table",
    )

    it_res = MappingEvaluator.evaluate_mapping_iteration(
        report=report, dataset=dataset, iteration_index=1
    )
    assert it_res.metrics.f1 == 1.0
    assert it_res.category == "multi_table"
    assert ("customer.custid", "borrower.customer_id") in it_res.tp_pairs
    assert ("branch.name", "branch.branch_name") in it_res.tp_pairs


def test_schema_mapping_loader_category_filtering() -> None:
    """Test loading suite with category filters on actual data/schema_mapping directory."""
    data_dir = Path("data/schema_mapping")
    if not data_dir.exists():
        pytest.skip("data/schema_mapping not found")

    all_ds = SchemaMappingLoader.load_suite(data_dir, category_filter="all")
    assert len(all_ds) == 10

    single_ds = SchemaMappingLoader.load_suite(data_dir, category_filter="single_table")
    assert len(single_ds) == 5
    for d in single_ds:
        assert d.category == "single_table"

    multi_ds = SchemaMappingLoader.load_suite(data_dir, category_filter="multi_table")
    assert len(multi_ds) == 5
    for d in multi_ds:
        assert d.category == "multi_table"


def test_dataset_benchmark_result_status_properties() -> None:
    """Test status, successful_iterations, and failed_iterations properties."""
    base_metrics = MatchMetrics(
        precision=1.0,
        recall=1.0,
        f1=1.0,
        true_positives=1,
        false_positives=0,
        false_negatives=0,
        predicted_pairs_count=1,
        gold_pairs_count=1,
    )
    it_succ1 = IterationResult(
        iteration_index=1,
        metrics=base_metrics,
        latency_seconds=0.5,
    )
    it_succ2 = IterationResult(
        iteration_index=2,
        metrics=base_metrics,
        latency_seconds=0.5,
    )
    it_fail = IterationResult(
        iteration_index=2,
        metrics=MatchMetrics(
            precision=0.0,
            recall=0.0,
            f1=0.0,
            true_positives=0,
            false_positives=0,
            false_negatives=1,
            predicted_pairs_count=0,
            gold_pairs_count=1,
        ),
        latency_seconds=0.0,
        error_message="API Error",
    )

    agg = AggregatedMetrics(
        precision_mean=1.0,
        precision_std=0.0,
        recall_mean=1.0,
        recall_std=0.0,
        f1_mean=1.0,
        f1_std=0.0,
        latency_mean_sec=0.5,
        latency_std_sec=0.0,
        total_tokens=100,
    )

    # Empty
    res_empty = DatasetBenchmarkResult(
        dataset_name="ds",
        domain="D",
        scenario="S",
        model_name="M",
        iterations=0,
        aggregated_metrics=agg,
        iteration_results=[],
    )
    assert res_empty.status == "NO_RUNS"
    assert res_empty.total_iterations == 0
    assert res_empty.successful_iterations == 0
    assert res_empty.failed_iterations == 0

    # All success
    res_succ = DatasetBenchmarkResult(
        dataset_name="ds",
        domain="D",
        scenario="S",
        model_name="M",
        iterations=2,
        aggregated_metrics=agg,
        iteration_results=[it_succ1, it_succ2],
    )
    assert res_succ.status == "SUCCESS (2/2)"
    assert res_succ.successful_iterations == 2
    assert res_succ.failed_iterations == 0
    assert res_succ.failed_iteration_indices == []

    # Partial failure
    res_part = DatasetBenchmarkResult(
        dataset_name="ds",
        domain="D",
        scenario="S",
        model_name="M",
        iterations=2,
        aggregated_metrics=agg,
        iteration_results=[it_succ1, it_fail],
    )
    assert res_part.status == "PARTIAL (1/2)"
    assert res_part.successful_iterations == 1
    assert res_part.failed_iterations == 1
    assert res_part.failed_iteration_indices == [2]

    # All failed
    it_fail1 = IterationResult(
        iteration_index=1,
        metrics=it_fail.metrics,
        latency_seconds=0.0,
        error_message="API Error",
    )
    res_fail = DatasetBenchmarkResult(
        dataset_name="ds",
        domain="D",
        scenario="S",
        model_name="M",
        iterations=2,
        aggregated_metrics=agg,
        iteration_results=[it_fail1, it_fail],
    )
    assert res_fail.status == "FAILED (0/2)"
    assert res_fail.successful_iterations == 0
    assert res_fail.failed_iterations == 2
    assert res_fail.failed_iteration_indices == [1, 2]


@pytest.mark.asyncio
async def test_mapping_runner_in_place_retry(tmp_path: Path) -> None:
    """Verify that retry_benchmark_run only re-executes failed iterations."""
    data_dir = tmp_path / "data"
    ds_dir = data_dir / "test_retry_ds"
    ds_dir.mkdir(parents=True, exist_ok=True)

    df_src = pd.DataFrame({"user_id": [1], "name": ["A"]})
    df_tgt = pd.DataFrame({"id": [1], "full_name": ["A"]})
    df_src.to_csv(ds_dir / "test_retry_ds_source.csv", index=False)
    df_tgt.to_csv(ds_dir / "test_retry_ds_target.csv", index=False)

    mapping_data = {
        "dataset_name": "test_retry_ds",
        "domain": "Synthetic",
        "scenario": "Unionable",
        "matches": [
            {"source_column": "user_id", "target_column": "id"},
            {"source_column": "name", "target_column": "full_name"},
        ],
    }
    with open(
        ds_dir / "test_retry_ds_mapping.json", "w", encoding="utf-8"
    ) as f:
        json.dump(mapping_data, f, indent=2)

    with open(ds_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "name": "test_retry_ds",
                "domain": "Synthetic",
                "scenario": "Unionable",
            },
            f,
            indent=2,
        )

    mock_report = MappingReport(
        rules=[
            MappingRule(
                source_label="test_retry_ds",
                source_table="source",
                target_table="target",
                target_column="id",
                source_columns=["user_id"],
                transformations=[DirectCopy()],
            ),
            MappingRule(
                source_label="test_retry_ds",
                source_table="source",
                target_table="target",
                target_column="full_name",
                source_columns=["name"],
                transformations=[DirectCopy()],
            ),
        ]
    )
    mock_meta = ExecutionMetadata(
        model_name="mock-model",
        provider="mock-provider",
        total_tokens=100,
        prompt_tokens=50,
        completion_tokens=50,
        execution_time_seconds=0.2,
        prompt_template="Mock prompt",
    )

    output_dir = tmp_path / "outputs"

    # Initial run: iteration 1 succeeds, iteration 2 fails
    side_effects = [
        (mock_report, mock_meta),
        RuntimeError("Simulated LLM API timeout"),
    ]
    with patch(
        "schema_integration.benchmarking.mapping.runner.map_schema",
        side_effect=side_effects,
    ):
        initial_report = await MappingRunner.run_benchmark(
            models=["mock-model"],
            dataset_filter="test_retry_ds",
            iterations=2,
            data_dir=data_dir,
            output_dir=output_dir,
        )

    run_id = initial_report.configuration["run_id"]
    run_dir = output_dir / run_id
    model_ds_dir = run_dir / "datasets" / "test_retry_ds" / "mock-model"

    assert initial_report.dataset_results[0].status == "PARTIAL (1/2)"
    assert initial_report.dataset_results[0].failed_iterations == 1

    # Check summary.csv has iteration 2 marked FAILED
    with open(run_dir / "summary.csv", "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        assert len(rows) == 2
        assert rows[0]["status"] == "SUCCESS"
        assert rows[1]["status"] == "FAILED"
        assert "Simulated LLM API timeout" in rows[1]["error"]

    # Check summary.md has warning
    with open(run_dir / "summary.md", "r", encoding="utf-8") as f:
        md_text = f.read()
        assert "1 iteration failure(s) recorded" in md_text
        assert f"--retry-run {run_id}" in md_text

    # Check execution_trace.jsonl has 2 traces
    with open(
        model_ds_dir / "execution_trace.jsonl", "r", encoding="utf-8"
    ) as f:
        traces = [json.loads(line) for line in f]
        assert len(traces) == 2
        assert traces[0]["iteration"] == 1
        assert "error_message" not in traces[0]
        assert traces[1]["iteration"] == 2
        assert "error_message" in traces[1]

    # Retry the run: map_schema should only be called once (for iteration 2)
    retry_mock = AsyncMock(return_value=(mock_report, mock_meta))
    with patch(
        "schema_integration.benchmarking.mapping.runner.map_schema",
        new=retry_mock,
    ):
        retried_report = await MappingRunner.retry_benchmark_run(
            run_target=run_id,
            data_dir=data_dir,
            output_dir=output_dir,
        )

    assert retry_mock.call_count == 1
    assert retried_report.dataset_results[0].status == "SUCCESS (2/2)"
    assert retried_report.dataset_results[0].failed_iterations == 0

    # Check metrics.json in-place update
    with open(model_ds_dir / "metrics.json", "r", encoding="utf-8") as f:
        m_data = json.load(f)
        assert len(m_data["iteration_results"]) == 2
        assert m_data["iteration_results"][0]["error_message"] is None
        assert m_data["iteration_results"][1]["error_message"] is None

    # Check summary.csv updated in-place
    with open(run_dir / "summary.csv", "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        assert len(rows) == 2
        assert rows[0]["status"] == "SUCCESS"
        assert rows[1]["status"] == "SUCCESS"
        assert rows[1]["error"] == ""

    # Check summary.md updated in-place
    with open(run_dir / "summary.md", "r", encoding="utf-8") as f:
        md_text = f.read()
        assert "SUCCESS (2/2)" in md_text
        assert "Zero iteration failures recorded" in md_text

    # Check execution_trace.jsonl: should now have 3 traces
    with open(
        model_ds_dir / "execution_trace.jsonl", "r", encoding="utf-8"
    ) as f:
        traces = [json.loads(line) for line in f]
        assert len(traces) == 3
        assert traces[0]["iteration"] == 1
        assert traces[1]["iteration"] == 2
        assert "error_message" in traces[1]
        assert traces[2]["iteration"] == 2
        assert traces[2].get("retry") is True
        assert "error_message" not in traces[2]


@pytest.mark.asyncio
async def test_mapping_runner_retry_no_failures(tmp_path: Path) -> None:
    """Verify that retry_benchmark_run gracefully no-ops when clean."""
    data_dir = tmp_path / "data"
    ds_dir = data_dir / "test_clean_ds"
    ds_dir.mkdir(parents=True, exist_ok=True)

    df_src = pd.DataFrame({"c1": [1]})
    df_tgt = pd.DataFrame({"c1": [1]})
    df_src.to_csv(ds_dir / "test_clean_ds_source.csv", index=False)
    df_tgt.to_csv(ds_dir / "test_clean_ds_target.csv", index=False)

    mapping_data = {
        "dataset_name": "test_clean_ds",
        "domain": "Synthetic",
        "scenario": "Unionable",
        "matches": [{"source_column": "c1", "target_column": "c1"}],
    }
    with open(
        ds_dir / "test_clean_ds_mapping.json", "w", encoding="utf-8"
    ) as f:
        json.dump(mapping_data, f, indent=2)

    with open(ds_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "name": "test_clean_ds",
                "domain": "Synthetic",
                "scenario": "Unionable",
            },
            f,
            indent=2,
        )

    mock_report = MappingReport(
        rules=[
            MappingRule(
                source_label="test_clean_ds",
                source_table="source",
                target_table="target",
                target_column="c1",
                source_columns=["c1"],
                transformations=[DirectCopy()],
            )
        ]
    )
    mock_meta = ExecutionMetadata(
        model_name="mock-model",
        provider="mock-provider",
        total_tokens=100,
        prompt_tokens=50,
        completion_tokens=50,
        execution_time_seconds=0.2,
        prompt_template="Mock",
    )

    output_dir = tmp_path / "outputs"
    with patch(
        "schema_integration.benchmarking.mapping.runner.map_schema",
        return_value=(mock_report, mock_meta),
    ):
        initial_report = await MappingRunner.run_benchmark(
            models=["mock-model"],
            dataset_filter="test_clean_ds",
            iterations=1,
            data_dir=data_dir,
            output_dir=output_dir,
        )

    run_id = initial_report.configuration["run_id"]
    retry_mock = AsyncMock()
    with patch(
        "schema_integration.benchmarking.mapping.runner.map_schema",
        new=retry_mock,
    ):
        res = await MappingRunner.retry_benchmark_run(
            run_target=run_id,
            data_dir=data_dir,
            output_dir=output_dir,
        )

    assert retry_mock.call_count == 0
    assert res.dataset_results[0].status == "SUCCESS (1/1)"
