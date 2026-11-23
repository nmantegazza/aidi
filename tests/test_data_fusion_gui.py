import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import pandas as pd
import gradio as gr

from pipeline.gui.contracts import IngestionResult, DataPortingResult, RecordLinkageResult
from pipeline.gui.phases.canvas import DataFusionConfigCanvasState, DataFusionResultCanvasState
from pipeline.gui.handlers import handle_run_fusion, handle_execute_fusion
from pipeline.gui.phases.phase_6_fusion import render_fusion_config_canvas, render_fusion_result_canvas

from data_fusion.models import (
    MultiTableFusionPolicy, TableFusionPolicy, ColumnPolicy, FusionStrategy,
    MultiTableFusionProfile, TableFusionProfile, ColumnConflictProfile,
    PhysicalType, SemanticType
)
from shared.ingestion import SourceData

def test_handle_run_and_execute_fusion():
    df_a = pd.DataFrame({"id": ["1", "2"], "name": ["Acme", "Beta"]}).set_index("id")
    df_b = pd.DataFrame({"id": ["1", "3"], "name": ["Acme Corp", "Gamma"]}).set_index("id")
    
    ported_table = MagicMock()
    ported_table.df_a = df_a
    ported_table.df_b = df_b
    
    porting_state = DataPortingResult(
        porting_instructions=MagicMock(),
        ported_tables={"companies": ported_table},
        porting_report=MagicMock(),
        engineer_metadata={}
    )
    
    er_result_mock = MagicMock()
    er_result_mock.matches = pd.DataFrame(
        {"aggregate_score": [0.99]},
        index=pd.MultiIndex.from_tuples([("1", "1")], names=["left_id", "right_id"])
    )
    
    linkage_state = RecordLinkageResult(
        er_results={"companies": er_result_mock}
    )
    
    src_a = MagicMock(spec=SourceData)
    src_a.package = MagicMock()
    src_a.package.name = "source_a"
    
    src_b = MagicMock(spec=SourceData)
    src_b.package = MagicMock()
    src_b.package.name = "source_b"
    
    ingestion_state = IngestionResult(
        source_a=src_a,
        report_a=MagicMock(),
        source_b=src_b,
        report_b=MagicMock(),
        profiles_a={},
        profiles_b={},
        data_root="dummy_root"
    )
    
    mock_profile = MultiTableFusionProfile(
        source_a_origin="source_a",
        source_b_origin="source_b",
        tables={
            "companies": TableFusionProfile(
                table_name="companies",
                total_pairs=1,
                columns={
                    "name": ColumnConflictProfile(
                        column_name="name",
                        physical_type=PhysicalType.TEXT,
                        semantic_type=SemanticType.NONE,
                        conflict_rate=1.0,
                        source_a_null_rate=0.0,
                        source_b_null_rate=0.0,
                        source_trust_score=0.8,
                        samples=[]
                    )
                }
            )
        }
    )
    
    mock_policy = MultiTableFusionPolicy(
        tables={
            "companies": TableFusionPolicy(
                table_name="companies",
                column_policies=[
                    ColumnPolicy(
                        column_name="name",
                        strategy=FusionStrategy.LONGEST_STRING,
                        reasoning="Use longest string"
                    )
                ],
                reasoning="Overall table reasoning"
            )
        }
    )
    
    with patch("pipeline.gui.handlers.DataFusionEngine") as MockEngineClass:
        mock_engine = MockEngineClass.return_value
        mock_engine.profile_and_propose = MagicMock(return_value=(mock_profile, mock_policy))
        
        config_result, tables, sys_msg = handle_run_fusion(
            porting_state, linkage_state, ingestion_state, "google", "gemini-1.5-pro"
        )
        
        assert config_result.fusion_profile == mock_profile
        assert config_result.fusion_policy == mock_policy
        assert "companies" in tables
        assert "fusion policy generated" in sys_msg.lower()
        
        canvas_state = DataFusionConfigCanvasState(
            config_result=config_result,
            linkage_result=linkage_state,
            porting_result=porting_state,
            tables=tables
        )
        
        mock_fused_df = pd.DataFrame([{"id": "1", "name": "Acme Corp"}])
        mock_engine.execute.return_value = {"companies": mock_fused_df}
        
        fusion_result, exec_msg = handle_execute_fusion(
            canvas_state, "google", "gemini-1.5-pro"
        )
        
        assert fusion_result.fused_tables["companies"].equals(mock_fused_df)
        assert fusion_result.fusion_policy == mock_policy
        assert "execution completed" in exec_msg.lower()

def test_render_fusion_canvases():
    mock_profile = MultiTableFusionProfile(
        source_a_origin="source_a",
        source_b_origin="source_b",
        tables={
            "companies": TableFusionProfile(
                table_name="companies",
                total_pairs=1,
                columns={
                    "name": ColumnConflictProfile(
                        column_name="name",
                        physical_type=PhysicalType.TEXT,
                        semantic_type=SemanticType.NONE,
                        conflict_rate=1.0,
                        source_a_null_rate=0.0,
                        source_b_null_rate=0.0,
                        source_trust_score=0.8,
                        samples=[]
                    )
                }
            )
        }
    )
    
    mock_policy = MultiTableFusionPolicy(
        tables={
            "companies": TableFusionPolicy(
                table_name="companies",
                column_policies=[
                    ColumnPolicy(
                        column_name="name",
                        strategy=FusionStrategy.LONGEST_STRING,
                        reasoning="Use longest string"
                    )
                ],
                reasoning="Overall table reasoning"
            )
        }
    )
    
    from pipeline.gui.contracts import DataFusionConfigResult, DataFusionResult
    config_result = DataFusionConfigResult(
        fusion_profile=mock_profile,
        fusion_policy=mock_policy
    )
    
    canvas_state = DataFusionConfigCanvasState(
        config_result=config_result,
        linkage_result=MagicMock(),
        porting_result=MagicMock(),
        tables={"companies": (pd.DataFrame(), pd.DataFrame(), pd.DataFrame())}
    )
    
    with gr.Blocks():
        render_fusion_config_canvas(canvas_state)
        
    fusion_result = DataFusionResult(
        fused_tables={"companies": pd.DataFrame([{"id": "1", "name": "Acme Corp"}])},
        fusion_policy=mock_policy,
        fusion_profile=mock_profile
    )
    result_canvas_state = DataFusionResultCanvasState(
        fusion_result=fusion_result
    )
    with gr.Blocks():
        render_fusion_result_canvas(result_canvas_state)
