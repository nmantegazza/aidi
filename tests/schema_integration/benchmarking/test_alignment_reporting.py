"""Tests for reference-free schema alignment benchmark reporting and visualizers."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from schema_integration.alignment.models import AlignmentReport
from schema_integration.benchmarking.alignment.evaluation import (
    AlignmentEvaluator,
)
from schema_integration.benchmarking.alignment.loader import (
    SchemaAlignmentDataset,
)
from schema_integration.benchmarking.alignment.models import (
    AlignmentDatasetMetrics,
    AlignmentIterationMetrics,
    AlignmentRunSummary,
    DetectedCloneRecord,
    MacroModelSummary,
    StructuralIntegrityStats,
    SynonymPair,
)
from schema_integration.benchmarking.alignment.runner import AlignmentRunner
from schema_integration.benchmarking.common.models import TokenUsage
from schema_integration.benchmarking.common.reporting import (
    BenchmarkReporter,
    export_summary_csv,
    format_markdown_table,
)
from schema_integration.benchmarking.common.visualizer import (
    generate_schema_er_mermaid,
)
from shared.schema_models import (
    DataPackage,
    ForeignKey,
    ForeignKeyReference,
    TableField,
    TableResource,
    TableSchema,
)


@pytest.fixture
def sample_packages() -> tuple[DataPackage, DataPackage]:
    """Create sample Source A and Source B DataPackages."""
    src_a = DataPackage(
        schema_name="bank_a",
        resources=[
            TableResource(
                name="customers",
                schema=TableSchema(
                    primaryKey="cust_id",
                    fields=[
                        TableField(name="cust_id", type="integer"),
                        TableField(name="full_name", type="string"),
                        TableField(name="branch_code", type="string"),
                    ],
                    foreignKeys=[
                        ForeignKey(
                            fields="branch_code",
                            reference=ForeignKeyReference(
                                resource="branches", fields="code"
                            ),
                        )
                    ],
                ),
            ),
            TableResource(
                name="branches",
                schema=TableSchema(
                    primaryKey="code",
                    fields=[
                        TableField(name="code", type="string"),
                        TableField(name="address", type="string"),
                    ],
                ),
            ),
        ],
    )

    src_b = DataPackage(
        schema_name="bank_b",
        resources=[
            TableResource(
                name="clients",
                schema=TableSchema(
                    primaryKey="client_id",
                    fields=[
                        TableField(name="client_id", type="integer"),
                        TableField(name="client_name", type="string"),
                        TableField(name="location", type="string"),
                    ],
                ),
            )
        ],
    )
    return src_a, src_b


def test_mermaid_schema_er_generator(
    sample_packages: tuple[DataPackage, DataPackage],
) -> None:
    """Test generating valid Mermaid ER diagram from a DataPackage."""
    src_a, _ = sample_packages
    diagram = generate_schema_er_mermaid(src_a)

    assert "erDiagram" in diagram
    assert "customers {" in diagram
    assert "branches {" in diagram
    assert "integer cust_id PK" in diagram
    assert "string branch_code FK" in diagram
    assert 'customers }o--|| branches : "branch_code"' in diagram


def test_markdown_table_formatter() -> None:
    """Test pure markdown table formatter."""
    headers = ["Col A", "Col B", "Score"]
    rows = [["x", "y", "1.00"], ["a", "b", "0.50"]]
    md = format_markdown_table(headers, rows, alignments=["left", "center", "right"])

    lines = md.strip().split("\n")
    assert len(lines) == 4
    assert "| Col A | Col B | Score |" in lines[0]
    assert "| :--- | :---: | ---: |" in lines[1]
    assert "| x | y | 1.00 |" in lines[2]


def test_csv_summary_export(tmp_path: Path) -> None:
    """Test flat CSV export."""
    csv_file = tmp_path / "summary.csv"
    rows = [
        {
            "dataset": "bank1-bank2",
            "domain": "Finance",
            "model": "gemini-2.0-flash",
            "completeness": 0.95,
            "structural_integrity": 1.0,
            "intra_table_uniqueness": 1.0,
            "clones_detected": 0,
            "latency_sec": 12.5,
            "prompt_tokens": 1200,
            "completion_tokens": 400,
            "total_tokens": 1600,
        }
    ]
    out = export_summary_csv(rows, csv_file)
    assert out.exists()

    with open(out, newline="", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) == 1
        assert reader[0]["dataset"] == "bank1-bank2"
        assert float(reader[0]["completeness"]) == 0.95
        assert int(reader[0]["total_tokens"]) == 1600


def test_flakiness_analysis() -> None:
    """Test stability analysis across multiple iterations."""
    clone1 = DetectedCloneRecord(
        target_table="users",
        column_a="name",
        column_b="full_name",
        source_prov_a=["a.t.name"],
        source_prov_b=["b.t.full_name"],
        data_type="string",
        similarity_score=0.92,
    )
    it1 = AlignmentIterationMetrics(
        iteration_index=1,
        completeness=1.0,
        structural_integrity=1.0,
        intra_table_uniqueness=0.92,
        detected_clones=[clone1],
        structural_stats=StructuralIntegrityStats(
            pk_validity=1.0, fk_validity=1.0, score=1.0
        ),
    )
    it2 = AlignmentIterationMetrics(
        iteration_index=2,
        completeness=1.0,
        structural_integrity=1.0,
        intra_table_uniqueness=1.0,
        detected_clones=[],
        structural_stats=StructuralIntegrityStats(
            pk_validity=1.0, fk_validity=1.0, score=1.0
        ),
    )

    flakiness = AlignmentEvaluator.compute_flakiness([it1, it2])
    assert flakiness["total_distinct_clones"] == 1
    assert flakiness["stable_clones_count"] == 0
    assert flakiness["stability_ratio"] == 0.0


def test_3tier_dataset_markdown_report(
    sample_packages: tuple[DataPackage, DataPackage],
) -> None:
    """Test generating diagnostic dataset report with ER diagrams and target schema details."""
    src_a, src_b = sample_packages
    ds = SchemaAlignmentDataset(
        name="bank1-bank2",
        domain="Finance",
        source_a=src_a,
        source_b=src_b,
        ground_truth=[
            SynonymPair(
                source_a="customers.cust_id", source_b="clients.client_id"
            ),
        ],
    )

    target_pkg = DataPackage(
        schema_name="unified_bank",
        resources=[
            TableResource(
                name="unified_customer",
                schema=TableSchema(
                    primaryKey="customer_id",
                    fields=[
                        TableField(
                            name="customer_id",
                            type="integer",
                            source_provenance=[
                                "source_a.customers.cust_id",
                                "source_b.clients.client_id",
                            ],
                            description="Global Customer ID",
                        ),
                        TableField(
                            name="name",
                            type="string",
                            source_provenance=[
                                "source_a.customers.full_name",
                                "source_b.clients.client_name",
                            ],
                            description="Full customer name",
                        ),
                    ],
                ),
            )
        ],
    )

    mock_report = AlignmentReport(
        target_schema=target_pkg,
        conflict_report=[],
    )

    it = AlignmentIterationMetrics(
        iteration_index=1,
        completeness=0.8,
        structural_integrity=0.85,
        intra_table_uniqueness=1.0,
        unmapped_source_columns=["a:branches.code"],
        structural_stats=StructuralIntegrityStats(
            pk_validity=1.0,
            fk_validity=0.7,
            score=0.85,
            total_tables=2,
            total_fks=1,
            broken_fks=["Table 'customers' references missing table 'branches'"],
        ),
        token_usage=TokenUsage(
            prompt_tokens=500,
            completion_tokens=200,
            total_tokens=700,
        ),
        alignment_report=mock_report,
    )

    dm = AlignmentDatasetMetrics(
        dataset_name=ds.name,
        domain=ds.domain,
        table_count_a=len(src_a.resources),
        table_count_b=len(src_b.resources),
        column_count_a=5,
        column_count_b=3,
        ground_truth_count=len(ds.ground_truth),
        iterations=[it],
        mean_completeness=0.8,
        mean_structural_integrity=0.85,
        mean_intra_table_uniqueness=1.0,
        mean_latency_sec=8.5,
        prompt_tokens=500,
        completion_tokens=200,
        total_tokens=700,
    )

    md = AlignmentRunner._build_dataset_markdown_report(
        dataset=ds,
        model_name="gemini-2.0-flash",
        dm=dm,
    )

    assert "# Schema Alignment Diagnostic Report — bank1-bank2" in md
    assert "## Schema Architectures (ER Diagrams)" in md
    assert "### Source A Schema (`bank_a`)" in md
    assert "### Source B Schema (`bank_b`)" in md
    assert "### Generated Unified Target Schema" in md
    assert "## Target Schema Detailed Specifications" in md
    assert "### Target Table: `unified_customer`" in md
    assert "Global Customer ID" in md
    assert "## 3-Pillar Reference-Free Diagnostic Inspection" in md
    assert "### Pillar 1: Information Preservation (Completeness)" in md
    assert "### Pillar 2: Structural & Referential Constraints" in md
    assert "Broken FK" in md
    assert "### Pillar 3: Intrinsic Minimality & Non-Redundancy" in md
    assert "`a:branches.code`" in md


def test_alignment_run_summary_serialization(tmp_path: Path) -> None:
    """Test full AlignmentRunSummary model JSON serialization and export."""
    macro = MacroModelSummary(
        model_name="test-model",
        completeness=1.0,
        structural_integrity=1.0,
        intra_table_uniqueness=1.0,
        mean_latency_sec=10.0,
        prompt_tokens=1000,
        completion_tokens=300,
        total_tokens=1300,
    )

    run_summary = AlignmentRunSummary(
        run_id="run_20260817_120000",
        models=["test-model"],
        iterations=1,
        macro_summaries={"test-model": macro},
        dataset_results={},
    )

    out_file = tmp_path / "summary.json"
    BenchmarkReporter.save_json(run_summary, out_file)
    assert out_file.exists()

    with open(out_file, encoding="utf-8") as f:
        data = json.load(f)
        assert data["run_id"] == "run_20260817_120000"
        assert data["macro_summaries"]["test-model"]["completeness"] == 1.0
