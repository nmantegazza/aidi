import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock

from pipeline.models import PipelineRunReport, StepResults, TableRunResult
from pipeline.visualization import generate_pipeline_html_report
from shared.ingestion.models import SourceData, IngestionReport, TableIngestionReport
from shared.schema_models import (
    DataPackage,
    TableResource,
    TableSchema,
    TableField,
    IntegrationReport,
    ConflictReport,
    Conflict,
    ConflictType,
)
from shared.agents import ExecutionMetadata
from shared.porting.models import PortingInstructionsReport, TablePortingInstruction
from entity_resolution.models import EntityResolutionResult, ERPipelineConfiguration
from shared.porting import PortedTable, PortingReport

def test_generate_pipeline_html_report_smoke():
    """Smoke test to ensure HTML report generation doesn't crash due to attribute errors."""
    
    # 1. Setup minimal valid objects
    pkg_a = DataPackage(name="source_a", resources=[])
    pkg_b = DataPackage(name="source_b", resources=[])
    pkg_global = DataPackage(name="global", resources=[
        TableResource(name="users", schema=TableSchema(fields=[TableField(name="id")]))
    ])
    
    source_a = SourceData(package=pkg_a, tables={}, base_path=Path("/tmp"))
    source_b = SourceData(package=pkg_b, tables={}, base_path=Path("/tmp"))
    
    ing_report_a = IngestionReport(source_name="source_a", base_path="/tmp", tables={"t1": TableIngestionReport(name="t1", row_count=10, col_count=2, columns={}, primary_keys=["id"])})
    ing_report_b = IngestionReport(source_name="source_b", base_path="/tmp", tables={})
    
    int_report = IntegrationReport(
        conflicts_report=[ConflictReport(conflict_type=ConflictType.NAMING, conflicts=[
            Conflict(source_items=["a.u"], target_items=["g.u"], description="d", resolution_strategy="rename")
        ])],
        global_schema=pkg_global
    )
    
    porting_inst = PortingInstructionsReport(
        global_table_instructions={
            "users": TablePortingInstruction(construction_recipes=[], field_transformations={})
        }
    )
    
    er_config = ERPipelineConfiguration(
        indexing_keys=["id"],
        sorting_key="id",
        window_size=3,
        matching_columns={"id": {"algorithm": "jarowinkler", "weight": 1.0}},
        reasoning="test"
    )
    
    er_result = EntityResolutionResult(
        config=er_config,
        er_config_metadata=ExecutionMetadata(model_name="m", provider="p", execution_time_seconds=1, prompt_tokens=1, completion_tokens=1, total_tokens=2),
        profile_a=MagicMock(),
        profile_b=MagicMock(),
        df_a_clean=pd.DataFrame({"id": [1]}),
        df_b_clean=pd.DataFrame({"id": [1]}),
        matches=pd.DataFrame(),
        uncertain=pd.DataFrame(),
        non_matches=pd.DataFrame(),
        candidate_pairs=pd.MultiIndex.from_tuples([(0,0)])
    )
    
    step_results = StepResults(
        source_a=source_a,
        source_b=source_b,
        ingestion_report_a=ing_report_a,
        ingestion_report_b=ing_report_b,
        clean_source_a=source_a,
        clean_source_b=source_b,
        cleaning_reports_a={},
        cleaning_reports_b={},
        profiles_a={},
        profiles_b={},
        integration_report=int_report,
        porting_instructions=porting_inst,
        gav_metadata={"arch": ExecutionMetadata(model_name="m", provider="p", execution_time_seconds=1, prompt_tokens=1, completion_tokens=1, total_tokens=2)},
        ported_tables={"users": PortedTable("users", pd.DataFrame({"id": [1]}), pd.DataFrame({"id": [1]}), [])},
        porting_report=PortingReport(total_tables=1, total_rows_source_a=1, total_rows_source_b=1, total_warnings=0, processing_time_ms=10.0),
        er_results={"users": er_result}
    )
    
    table_results = {
        "users": TableRunResult(
            global_table_name="users",
            source_a_table="t1",
            source_b_table="t2",
            porting_warnings=[],
            num_rows_a=1,
            num_rows_b=1,
            num_matches=0,
            num_uncertain=0,
            num_non_matches=0,
            er_config=er_config
        )
    }
    
    report = PipelineRunReport(
        data_root="/tmp",
        model_name="test-model",
        gav_metadata=step_results.gav_metadata,
        integration_report=int_report,
        porting_instructions=porting_inst,
        table_results=table_results,
        step_results=step_results
    )
    
    # 2. RUN VISUALIZATION
    try:
        html = generate_pipeline_html_report(report, "test-provider")
        assert "Data Integration Pipeline Report" in html
        assert "source_a" in html
        assert "source_b" in html
        print("Success: HTML report generated without errors.")
    except Exception as e:
        pytest.fail(f"HTML report generation failed: {e}")

if __name__ == "__main__":
    test_generate_pipeline_html_report_smoke()
