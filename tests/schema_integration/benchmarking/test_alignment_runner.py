"""Unit tests for SchemaNet reference-free schema alignment runner and artifacts."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from schema_integration.alignment.models import (
    AlignmentReport,
    ConceptualConflict,
    ConflictGroup,
    ConflictType,
)
from schema_integration.benchmarking.alignment.runner import AlignmentRunner
from shared.agents import ExecutionMetadata
from shared.schema_models import (
    DataPackage,
    TableField,
    TableResource,
    TableSchema,
)


@pytest.mark.asyncio
async def test_alignment_runner_artifact_generation(tmp_path: Path) -> None:
    """Test AlignmentRunner.run_benchmark produces all required diagnostic artifacts."""
    # Create mock dataset in tmp_path / "data"
    data_dir = tmp_path / "data"
    ds_dir = data_dir / "sample_dataset"
    ds_dir.mkdir(parents=True, exist_ok=True)

    pkg_a = DataPackage(
        schema_name="source_a",
        resources=[
            TableResource(
                name="patients",
                schema=TableSchema(
                    primaryKey="id",
                    fields=[
                        TableField(name="id", type="integer"),
                        TableField(name="gender", type="string"),
                    ],
                ),
            )
        ],
    )
    pkg_b = DataPackage(
        schema_name="source_b",
        resources=[
            TableResource(
                name="person",
                schema=TableSchema(
                    primaryKey="person_id",
                    fields=[
                        TableField(name="person_id", type="integer"),
                        TableField(name="gender_concept_id", type="integer"),
                    ],
                ),
            )
        ],
    )
    metadata = {"domain": "Healthcare"}

    with open(ds_dir / "source_a.json", "w", encoding="utf-8") as f:
        f.write(pkg_a.model_dump_json(indent=2))
    with open(ds_dir / "source_b.json", "w", encoding="utf-8") as f:
        f.write(pkg_b.model_dump_json(indent=2))
    with open(ds_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    output_dir = tmp_path / "outputs"

    mock_target_pkg = DataPackage(
        schema_name="target",
        resources=[
            TableResource(
                name="person",
                schema=TableSchema(
                    primaryKey="person_id",
                    fields=[
                        TableField(
                            name="person_id",
                            type="integer",
                            source_provenance=[
                                "source_a.patients.id",
                                "source_b.person.person_id",
                            ],
                        ),
                        TableField(
                            name="gender",
                            type="string",
                            source_provenance=[
                                "source_a.patients.gender",
                                "source_b.person.gender_concept_id",
                            ],
                        ),
                    ],
                ),
            )
        ],
    )
    mock_report = AlignmentReport(
        target_schema=mock_target_pkg,
        conflict_report=[
            ConflictGroup(
                conflict_type=ConflictType.NAMING,
                conflicts=[
                    ConceptualConflict(
                        source_references=["patients.gender", "person.gender_concept_id"],
                        description="Field name mismatch: gender vs gender_concept_id",
                        resolution="Standardized as gender",
                    )
                ],
            )
        ],
    )
    mock_meta = ExecutionMetadata(
        model_name="mock-model",
        provider="mock-provider",
        execution_time_seconds=1.25,
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        prompt_template="System prompt template",
    )

    with patch(
        "schema_integration.benchmarking.alignment.runner.align_schemas",
        new=AsyncMock(return_value=(mock_report, mock_meta)),
    ):
        summary = await AlignmentRunner.run_benchmark(
            models=["mock-model"],
            dataset_filter="sample_dataset",
            iterations=1,
            data_dir=data_dir,
            output_dir=output_dir,
        )

    assert summary.run_id.startswith("run_")
    run_dir = output_dir / summary.run_id
    assert run_dir.exists()

    # Root summary artifacts
    assert (run_dir / "summary.json").exists()
    assert (run_dir / "summary.csv").exists()
    assert (run_dir / "summary.md").exists()

    # Per-dataset, per-model artifacts
    model_ds_dir = run_dir / "datasets" / "sample_dataset" / "mock-model"
    assert model_ds_dir.exists()
    assert (model_ds_dir / "metrics.json").exists()
    assert (model_ds_dir / "alignment_report.json").exists()
    assert (model_ds_dir / "alignment_report.md").exists()
    assert (model_ds_dir / "detected_clones.csv").exists()
    assert (model_ds_dir / "execution_trace.jsonl").exists()

    # Verify detected_clones.csv content
    with open(model_ds_dir / "detected_clones.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 0  # No duplicate clones in mock schema

    # Verify execution_trace.jsonl content
    with open(model_ds_dir / "execution_trace.jsonl", "r", encoding="utf-8") as f:
        trace_lines = [json.loads(line) for line in f if line.strip()]
        assert len(trace_lines) == 1
        trace = trace_lines[0]
        assert trace["model"] == "mock-model"
        assert trace["dataset"] == "sample_dataset"
        assert trace["prompt_tokens"] == 100
        assert trace["metrics"]["completeness"] == 1.0
        assert trace["metrics"]["structural_integrity"] == 1.0
        assert trace["metrics"]["intra_table_uniqueness"] >= 0.0


@pytest.mark.asyncio
async def test_alignment_runner_multi_iteration(tmp_path: Path) -> None:
    """Test full alignment benchmark execution with multiple iterations."""
    data_dir = tmp_path / "data"
    ds_dir = data_dir / "sample_dataset"
    ds_dir.mkdir(parents=True, exist_ok=True)

    pkg_a = DataPackage(
        schema_name="source_a",
        resources=[
            TableResource(
                name="patients",
                schema=TableSchema(
                    primaryKey="id",
                    fields=[
                        TableField(name="id", type="integer"),
                        TableField(name="gender", type="string"),
                    ],
                ),
            )
        ],
    )
    pkg_b = DataPackage(
        schema_name="source_b",
        resources=[
            TableResource(
                name="person",
                schema=TableSchema(
                    primaryKey="person_id",
                    fields=[
                        TableField(name="person_id", type="integer"),
                        TableField(name="gender_concept_id", type="integer"),
                    ],
                ),
            )
        ],
    )
    with open(ds_dir / "source_a.json", "w", encoding="utf-8") as f:
        f.write(pkg_a.model_dump_json(indent=2))
    with open(ds_dir / "source_b.json", "w", encoding="utf-8") as f:
        f.write(pkg_b.model_dump_json(indent=2))
    with open(ds_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump({"domain": "Healthcare"}, f, indent=2)

    output_dir = tmp_path / "bench_outputs_multi"

    mock_schema = DataPackage(
        schema_name="target",
        resources=[
            TableResource(
                name="patients",
                schema=TableSchema(
                    primaryKey="id",
                    fields=[
                        TableField(
                            name="id",
                            type="integer",
                            source_provenance=[
                                "source_a.patients.id",
                                "source_b.person.person_id",
                            ],
                        ),
                        TableField(
                            name="gender",
                            type="string",
                            source_provenance=[
                                "source_a.patients.gender",
                                "source_b.person.gender_concept_id",
                            ],
                        ),
                    ],
                ),
            )
        ],
    )
    mock_report = AlignmentReport(
        target_schema=mock_schema,
        conflict_report=[],
    )
    mock_meta = ExecutionMetadata(
        model_name="mock-model",
        provider="mock-provider",
        total_tokens=250,
        prompt_tokens=100,
        completion_tokens=150,
        execution_time_seconds=0.4,
        prompt_template="Mock prompt",
    )

    with patch(
        "schema_integration.benchmarking.alignment.runner.align_schemas",
        new=AsyncMock(return_value=(mock_report, mock_meta)),
    ):
        summary = await AlignmentRunner.run_benchmark(
            models=["mock-model"],
            dataset_filter="sample_dataset",
            iterations=2,
            data_dir=data_dir,
            output_dir=output_dir,
        )

    assert summary.run_id.startswith("run_")
    run_dir = output_dir / summary.run_id
    model_ds_dir = run_dir / "datasets" / "sample_dataset" / "mock-model"

    assert (model_ds_dir / "mapping_consensus.csv").exists()
    assert (model_ds_dir / "alignment_report.md").exists()

    with open(
        model_ds_dir / "mapping_consensus.csv", "r", encoding="utf-8"
    ) as f:
        reader = csv.DictReader(f)
        consensus_rows = list(reader)
        assert len(consensus_rows) == 2
        for r in consensus_rows:
            assert r["status"] == "STABLE"
            assert float(r["agreement_rate"]) == 1.0
            assert int(r["coaligned_runs"]) == 2
            assert int(r["total_runs"]) == 2

    with open(
        model_ds_dir / "alignment_report.md", "r", encoding="utf-8"
    ) as f:
        md_text = f.read()
        assert "Multi-Iteration Stability Analysis" in md_text
        assert "Cross-Iteration Attribute Mapping Consensus" in md_text
        assert "Topological & Relational Drift" in md_text
        assert "mapping_consensus.csv" in md_text


@pytest.mark.asyncio
async def test_alignment_runner_signals_failures(tmp_path: Path) -> None:
    """Verify that iteration failures are explicitly signaled across artifacts."""
    data_dir = tmp_path / "data"
    ds_dir = data_dir / "sample_dataset"
    ds_dir.mkdir(parents=True, exist_ok=True)

    pkg_a = DataPackage(
        schema_name="source_a",
        resources=[
            TableResource(
                name="patients",
                schema=TableSchema(
                    primaryKey="id",
                    fields=[TableField(name="id", type="integer")],
                ),
            )
        ],
    )
    pkg_b = DataPackage(
        schema_name="source_b",
        resources=[
            TableResource(
                name="person",
                schema=TableSchema(
                    primaryKey="person_id",
                    fields=[TableField(name="person_id", type="integer")],
                ),
            )
        ],
    )
    with open(ds_dir / "source_a.json", "w", encoding="utf-8") as f:
        f.write(pkg_a.model_dump_json(indent=2))
    with open(ds_dir / "source_b.json", "w", encoding="utf-8") as f:
        f.write(pkg_b.model_dump_json(indent=2))
    with open(ds_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump({"domain": "Healthcare"}, f, indent=2)

    mock_schema = DataPackage(
        schema_name="target",
        resources=[
            TableResource(
                name="person",
                schema=TableSchema(
                    primaryKey="person_id",
                    fields=[
                        TableField(
                            name="person_id",
                            type="integer",
                            source_provenance=[
                                "source_a.patients.id",
                                "source_b.person.person_id",
                            ],
                        ),
                    ],
                ),
            )
        ],
    )
    mock_report = AlignmentReport(target_schema=mock_schema, conflict_report=[])
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

    # Iteration 1 succeeds, iteration 2 fails
    side_effects = [
        (mock_report, mock_meta),
        RuntimeError("Simulated LLM API failure"),
    ]

    with patch(
        "schema_integration.benchmarking.alignment.runner.align_schemas",
        side_effect=side_effects,
    ):
        summary = await AlignmentRunner.run_benchmark(
            models=["mock-model"],
            dataset_filter="sample_dataset",
            iterations=2,
            data_dir=data_dir,
            output_dir=output_dir,
        )

    run_dir = output_dir / summary.run_id
    model_ds_dir = run_dir / "datasets" / "sample_dataset" / "mock-model"

    # Check metrics.json
    with open(model_ds_dir / "metrics.json", "r", encoding="utf-8") as f:
        m_data = json.load(f)
        assert len(m_data["iterations"]) == 2
        assert m_data["iterations"][0]["error_message"] is None
        assert "Simulated LLM API failure" in m_data["iterations"][1]["error_message"]

    # Check summary.csv
    with open(run_dir / "summary.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["status"] == "PARTIAL (1/2)"
        assert rows[0]["success_count"] == "1"
        assert rows[0]["failure_count"] == "1"
        assert rows[0]["failed_iterations"] == "2"

    # Check summary.md
    with open(run_dir / "summary.md", "r", encoding="utf-8") as f:
        md_text = f.read()
        assert "PARTIAL (1/2)" in md_text
        assert "Failures & Errors" in md_text
        assert "Simulated LLM API failure" in md_text


@pytest.mark.asyncio
async def test_alignment_runner_in_place_retry(tmp_path: Path) -> None:
    """Verify that retry_benchmark_run only re-executes failed iterations in-place."""
    data_dir = tmp_path / "data"
    ds_dir = data_dir / "sample_dataset"
    ds_dir.mkdir(parents=True, exist_ok=True)

    pkg_a = DataPackage(
        schema_name="source_a",
        resources=[
            TableResource(
                name="patients",
                schema=TableSchema(
                    primaryKey="id",
                    fields=[TableField(name="id", type="integer")],
                ),
            )
        ],
    )
    pkg_b = DataPackage(
        schema_name="source_b",
        resources=[
            TableResource(
                name="person",
                schema=TableSchema(
                    primaryKey="person_id",
                    fields=[TableField(name="person_id", type="integer")],
                ),
            )
        ],
    )
    with open(ds_dir / "source_a.json", "w", encoding="utf-8") as f:
        f.write(pkg_a.model_dump_json(indent=2))
    with open(ds_dir / "source_b.json", "w", encoding="utf-8") as f:
        f.write(pkg_b.model_dump_json(indent=2))
    with open(ds_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump({"domain": "Healthcare"}, f, indent=2)

    mock_schema = DataPackage(
        schema_name="target",
        resources=[
            TableResource(
                name="person",
                schema=TableSchema(
                    primaryKey="person_id",
                    fields=[
                        TableField(
                            name="person_id",
                            type="integer",
                            source_provenance=[
                                "source_a.patients.id",
                                "source_b.person.person_id",
                            ],
                        ),
                    ],
                ),
            )
        ],
    )
    mock_report = AlignmentReport(target_schema=mock_schema, conflict_report=[])
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

    # Initial run: iteration 1 succeeds, iteration 2 fails
    side_effects = [
        (mock_report, mock_meta),
        RuntimeError("Transient 503 error"),
    ]
    with patch(
        "schema_integration.benchmarking.alignment.runner.align_schemas",
        side_effect=side_effects,
    ):
        initial_summary = await AlignmentRunner.run_benchmark(
            models=["mock-model"],
            dataset_filter="sample_dataset",
            iterations=2,
            data_dir=data_dir,
            output_dir=output_dir,
        )

    run_dir = output_dir / initial_summary.run_id
    model_ds_dir = run_dir / "datasets" / "sample_dataset" / "mock-model"

    # Retry the run: mock align_schemas should only be called once (for iteration 2)
    retry_mock = AsyncMock(return_value=(mock_report, mock_meta))
    with patch(
        "schema_integration.benchmarking.alignment.runner.align_schemas",
        new=retry_mock,
    ):
        retried_summary = await AlignmentRunner.retry_benchmark_run(
            run_target=initial_summary.run_id,
            data_dir=data_dir,
            output_dir=output_dir,
        )

    # Exactly 1 call was made to align_schemas on retry
    assert retry_mock.call_count == 1
    assert retried_summary.run_id == initial_summary.run_id

    # Check metrics.json in-place update
    with open(model_ds_dir / "metrics.json", "r", encoding="utf-8") as f:
        m_data = json.load(f)
        assert len(m_data["iterations"]) == 2
        assert m_data["iterations"][0]["error_message"] is None
        assert m_data["iterations"][1]["error_message"] is None

    # Check summary.csv updated in-place
    with open(run_dir / "summary.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["status"] == "SUCCESS (2/2)"
        assert rows[0]["failure_count"] == "0"
        assert rows[0]["failed_iterations"] == "none"

    # Check summary.md updated in-place
    with open(run_dir / "summary.md", "r", encoding="utf-8") as f:
        md_text = f.read()
        assert "SUCCESS (2/2)" in md_text
        assert "Zero iteration failures recorded" in md_text

    # Check execution_trace.jsonl: should have 3 lines (iter 1, iter 2 failed, iter 2 retried)
    with open(model_ds_dir / "execution_trace.jsonl", "r", encoding="utf-8") as f:
        traces = [json.loads(line) for line in f]
        assert len(traces) == 3
        assert traces[0]["iteration"] == 1
        assert traces[1]["iteration"] == 2
        assert "error_message" in traces[1]
        assert traces[2]["iteration"] == 2
        assert traces[2].get("retry") is True
        assert "error_message" not in traces[2]


@pytest.mark.asyncio
async def test_alignment_runner_retry_no_failures(tmp_path: Path) -> None:
    """Verify that retry_benchmark_run gracefully no-ops when all iterations succeeded."""
    data_dir = tmp_path / "data"
    ds_dir = data_dir / "sample_dataset"
    ds_dir.mkdir(parents=True, exist_ok=True)

    pkg_a = DataPackage(
        schema_name="source_a",
        resources=[
            TableResource(
                name="patients",
                schema=TableSchema(
                    primaryKey="id",
                    fields=[TableField(name="id", type="integer")],
                ),
            )
        ],
    )
    pkg_b = DataPackage(
        schema_name="source_b",
        resources=[
            TableResource(
                name="person",
                schema=TableSchema(
                    primaryKey="person_id",
                    fields=[TableField(name="person_id", type="integer")],
                ),
            )
        ],
    )
    with open(ds_dir / "source_a.json", "w", encoding="utf-8") as f:
        f.write(pkg_a.model_dump_json(indent=2))
    with open(ds_dir / "source_b.json", "w", encoding="utf-8") as f:
        f.write(pkg_b.model_dump_json(indent=2))
    with open(ds_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump({"domain": "Healthcare"}, f, indent=2)

    mock_schema = DataPackage(
        schema_name="target",
        resources=[
            TableResource(
                name="person",
                schema=TableSchema(
                    primaryKey="person_id",
                    fields=[
                        TableField(
                            name="person_id",
                            type="integer",
                            source_provenance=[
                                "source_a.patients.id",
                                "source_b.person.person_id",
                            ],
                        ),
                    ],
                ),
            )
        ],
    )
    mock_report = AlignmentReport(target_schema=mock_schema, conflict_report=[])
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
        "schema_integration.benchmarking.alignment.runner.align_schemas",
        new=AsyncMock(return_value=(mock_report, mock_meta)),
    ):
        summary = await AlignmentRunner.run_benchmark(
            models=["mock-model"],
            dataset_filter="sample_dataset",
            iterations=1,
            data_dir=data_dir,
            output_dir=output_dir,
        )

    retry_mock = AsyncMock()
    with patch(
        "schema_integration.benchmarking.alignment.runner.align_schemas",
        new=retry_mock,
    ):
        res = await AlignmentRunner.retry_benchmark_run(
            run_target=summary.run_id,
            data_dir=data_dir,
            output_dir=output_dir,
        )

    assert retry_mock.call_count == 0
    assert res.run_id == summary.run_id
