import pytest
import pandas as pd
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path

from pipeline.runner import run_pipeline
from pipeline.models import PipelineRunReport
from shared.ingestion import SourceData
from shared.schema_models import DataPackage, TableResource, TableSchema, TableField, IntegrationReport
from shared.agents import ExecutionMetadata
from entity_resolution.models import EntityResolutionResult, ERPipelineConfiguration

@pytest.fixture
def mock_source_data():
    pkg = DataPackage(schema_name="source_a", resources=[
        TableResource(name="users", schema=TableSchema(fields=[TableField(name="id"), TableField(name="name")]))
    ])
    df = pd.DataFrame({"id": [1], "name": ["Alice"]})
    return SourceData(package=pkg, tables={"users": df}, base_path=Path("/tmp"))

@pytest.fixture
def mock_integration_report():
    global_schema = DataPackage(schema_name="global", resources=[
        TableResource(
            name="global_users", 
            schema=TableSchema(fields=[TableField(name="user_id"), TableField(name="full_name")]),
            mapped_entities=["source_a.users", "source_b.users"]
        )
    ])
    return IntegrationReport(
        conflicts_report=[],
        global_schema=global_schema
    )

@pytest.fixture
def mock_er_result():
    return EntityResolutionResult(
        config=ERPipelineConfiguration(
            sorting_key="full_name",
            window_size=3,
            matching_columns={"full_name": {"algorithm": "jarowinkler", "weight": 1.0}},
            reasoning="test"
        ),
        er_config_metadata=ExecutionMetadata(
            model_name="manual",
            provider="manual",
            execution_time_seconds=0,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0
        ),
        profile_a=MagicMock(),
        profile_b=MagicMock(),
        df_a_clean=pd.DataFrame(),
        df_b_clean=pd.DataFrame(),
        matches=pd.DataFrame({"id_a": [1], "id_b": [1]}),
        uncertain=pd.DataFrame(),
        non_matches=pd.DataFrame()
    )

@patch("pipeline.runner.DataLoader")
@patch("pipeline.runner.clean_source_data")
@patch("pipeline.runner.perform_gav_architect")
@patch("pipeline.runner.generate_porting_instructions")
@patch("pipeline.runner.port_data_to_global_schema")
@patch("pipeline.runner.run_entity_resolution", new_callable=AsyncMock)
def test_run_pipeline_happy_path(
    mock_execute_er,
    mock_port_data,
    mock_generate_porting,
    mock_gav_architect,
    mock_clean_data,
    mock_dataloader,
    mock_source_data,
    mock_integration_report,
    mock_er_result
):
    # Setup mocks
    rep_a = MagicMock()
    rep_a.total_rows = 10
    rep_b = MagicMock()
    rep_b.total_rows = 10
    mock_dataloader.return_value.load_integration_input.return_value = (mock_source_data, rep_a, mock_source_data, rep_b)
    clean_rep = MagicMock()
    clean_rep.total_transformations = 0
    mock_clean_data.return_value = (mock_source_data, {"users": clean_rep})
    
    metadata = ExecutionMetadata(
        model_name="gpt-4o",
        provider="openai",
        execution_time_seconds=1.0,
        prompt_tokens=10,
        completion_tokens=10,
        total_tokens=20
    )
    from shared.porting.models import PortingInstructionsReport
    porting_instructions = PortingInstructionsReport(global_table_instructions={})
    mock_gav_architect.return_value = (mock_integration_report, metadata)
    mock_generate_porting.return_value = (porting_instructions, metadata)
    
    from shared.porting import PortedTable
    mock_port_data.return_value = ({
        "global_users": PortedTable(
            global_table_name="global_users", 
            df_a=pd.DataFrame(), 
            df_b=pd.DataFrame(), 
            warnings=[]
        )
    }, MagicMock())
    
    mock_execute_er.return_value = mock_er_result

    # Run
    report = run_pipeline("/fake/path")

    # Assertions
    assert isinstance(report, PipelineRunReport)
    assert report.total_tables == 1
    assert report.matched_count == 1
    assert "global_users" in report.table_results
    assert mock_execute_er.await_count == 1
    
    # Check that it bridged to async correctly via asyncio.run (which our mock handles)
    args, kwargs = mock_execute_er.call_args
    assert args[4].name == "global_users" # table_resource

@patch("pipeline.runner.DataLoader")
@patch("pipeline.runner.clean_source_data")
@patch("pipeline.runner.perform_gav_architect")
@patch("pipeline.runner.generate_porting_instructions")
@patch("pipeline.runner.port_data_to_global_schema")
@patch("pipeline.runner.run_entity_resolution", new_callable=AsyncMock)
def test_run_pipeline_er_override_respected(
    mock_execute_er,
    mock_port_data,
    mock_generate_porting,
    mock_gav_architect,
    mock_clean_data,
    mock_dataloader,
    mock_source_data,
    mock_integration_report,
    mock_er_result
):
    # Setup mocks
    rep_a = MagicMock()
    rep_a.total_rows = 10
    rep_b = MagicMock()
    rep_b.total_rows = 10
    mock_dataloader.return_value.load_integration_input.return_value = (mock_source_data, rep_a, mock_source_data, rep_b)
    clean_rep = MagicMock()
    clean_rep.total_transformations = 0
    mock_clean_data.return_value = (mock_source_data, {"users": clean_rep})
    metadata = ExecutionMetadata(
        model_name="gpt-4o",
        provider="openai",
        execution_time_seconds=1.0,
        prompt_tokens=10,
        completion_tokens=10,
        total_tokens=20
    )
    from shared.porting.models import PortingInstructionsReport
    porting_instructions = PortingInstructionsReport(global_table_instructions={})
    mock_gav_architect.return_value = (mock_integration_report, metadata)
    mock_generate_porting.return_value = (porting_instructions, metadata)
    
    from shared.porting import PortedTable
    mock_port_data.return_value = ({"global_users": PortedTable("global_users", pd.DataFrame(), pd.DataFrame(), [])}, MagicMock())
    mock_execute_er.return_value = mock_er_result

    override_config = ERPipelineConfiguration(
        sorting_key="full_name_OVERRIDE",
        window_size=5,
        matching_columns={"full_name": {"algorithm": "jarowinkler", "weight": 1.0}},
        reasoning="override"
    )

    # Run with override
    run_pipeline("/fake/path", er_override_configs={"global_users": override_config})

    # Assertions
    args, kwargs = mock_execute_er.call_args
    assert kwargs["override_config"] == override_config
