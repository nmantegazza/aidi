import asyncio
import logging
import os
import traceback
from typing import Any

import gradio as gr
import pandas as pd

from data_fusion.entrypoint import DataFusionEngine
from entity_resolution.agents import (
    identify_er_config_via_llm,
    refine_uncertain_matches_via_llm,
)
from entity_resolution.models import EntityResolutionResult, ERPipelineConfiguration
from pipeline.schema_architect import refine_schema_via_llm
from shared.profiling.engine import DataProfiler

from .contracts import (
    CleaningResult,
    DataFusionConfigResult,
    DataFusionResult,
    DataPortingResult,
    FinalReportResult,
    IngestionResult,
    RecordLinkageResult,
    SchemaMatchingResult,
)
from .phases.canvas import DataFusionConfigCanvasState
from .wrappers import (
    build_results_summary,
    run_cleaning,
    run_data_porting,
    run_ingestion,
    run_record_linkage,
    run_schema_matching,
    save_final_pipeline_report,
)

logger = logging.getLogger(__name__)

def handle_ingestion(data_root_files: Any, current_unlocked: int = 0) -> tuple[IngestionResult, int, str, Any, Any, Any]:
    if not data_root_files:
        raise gr.Error("Please select a data directory or datapackage.json.")

    try:
        # Resolve paths from input
        paths = []
        if isinstance(data_root_files, str):
            paths.append(data_root_files)
        elif isinstance(data_root_files, list):
            for f in data_root_files:
                if hasattr(f, 'name'):
                    paths.append(f.name)
                elif hasattr(f, 'path'):
                    paths.append(f.path)
                elif isinstance(f, str):
                    paths.append(f)
                elif isinstance(f, dict):
                    val = f.get('path') or f.get('name')
                    if val:
                        paths.append(val)
        
        if not paths:
            raise ValueError("No valid file paths found in selection.")

        abs_paths = [os.path.abspath(p) for p in paths]
        start_path = os.path.commonpath(abs_paths)
        if not os.path.isdir(start_path):
            start_path = os.path.dirname(start_path)
        
        data_root = start_path
        current = start_path
        for _ in range(3):
            if os.path.isdir(os.path.join(current, "source_a")) and \
               os.path.isdir(os.path.join(current, "source_b")):
                data_root = current
                break
            parent = os.path.dirname(current)
            if parent == current: break
            current = parent

        (
            src_a, rep_a, src_b, rep_b, 
            prof_a, prof_b
        ) = run_ingestion(data_root)

        res = IngestionResult(
            source_a=src_a,
            report_a=rep_a,
            source_b=src_b,
            report_b=rep_b,
            profiles_a=prof_a,
            profiles_b=prof_b,
            data_root=data_root
        )
        
        new_unlocked = max(current_unlocked, 1)
        return (
            res,
            new_unlocked,
            "",
            gr.update(interactive=(0 < new_unlocked)),
            gr.update(visible=False),
            gr.update(visible=True)
        )
    except Exception as e:
        logger.error(f"Ingestion failed: {traceback.format_exc()}")
        raise gr.Error(str(e))

def handle_cleaning(ingestion_state: IngestionResult) -> tuple[CleaningResult, str]:
    if not ingestion_state or not ingestion_state.source_a or not ingestion_state.source_b:
        raise gr.Error("Missing source data for cleaning. Please complete Phase 1.")
    try:
        c_a, rep_a, c_b, rep_b = run_cleaning(ingestion_state.source_a, ingestion_state.source_b)
        res = CleaningResult(
            clean_a=c_a,
            clean_b=c_b,
            reports_a=rep_a,
            reports_b=rep_b
        )
        total_trans = sum(r.total_transformations for r in rep_a.values()) + sum(r.total_transformations for r in rep_b.values())
        sys_msg = f"**System**: Data cleaning completed. Applied standardisation rules. {total_trans:,} column transformations and duplicates resolved successfully."
        return res, sys_msg
    except Exception as e:
        logger.error(f"Cleaning failed: {traceback.format_exc()}")
        raise gr.Error(str(e))

def handle_ingestion_and_cleaning(data_root_files: Any) -> tuple[IngestionResult, CleaningResult, str]:
    if not data_root_files:
        raise gr.Error("Please select a data directory or datapackage.json.")

    try:
        # Resolve paths from input
        paths = []
        if isinstance(data_root_files, str):
            paths.append(data_root_files)
        elif isinstance(data_root_files, list):
            for f in data_root_files:
                if hasattr(f, 'name'):
                    paths.append(f.name)
                elif hasattr(f, 'path'):
                    paths.append(f.path)
                elif isinstance(f, str):
                    paths.append(f)
                elif isinstance(f, dict):
                    val = f.get('path') or f.get('name')
                    if val:
                        paths.append(val)
        
        if not paths:
            raise ValueError("No valid file paths found in selection.")

        abs_paths = [os.path.abspath(p) for p in paths]
        start_path = os.path.commonpath(abs_paths)
        if not os.path.isdir(start_path):
            start_path = os.path.dirname(start_path)
        
        data_root = start_path
        current = start_path
        for _ in range(3):
            if os.path.isdir(os.path.join(current, "source_a")) and \
               os.path.isdir(os.path.join(current, "source_b")):
                data_root = current
                break
            parent = os.path.dirname(current)
            if parent == current: break
            current = parent

        # 1. Run Ingestion
        (
            src_a, rep_a, src_b, rep_b, 
            prof_a, prof_b
        ) = run_ingestion(data_root)

        ingest_res = IngestionResult(
            source_a=src_a,
            report_a=rep_a,
            source_b=src_b,
            report_b=rep_b,
            profiles_a=prof_a,
            profiles_b=prof_b,
            data_root=data_root
        )

        # 2. Run Cleaning
        c_a, clean_rep_a, c_b, clean_rep_b = run_cleaning(src_a, src_b)
        clean_res = CleaningResult(
            clean_a=c_a,
            clean_b=c_b,
            reports_a=clean_rep_a,
            reports_b=clean_rep_b
        )

        total_rows = sum(p.total_rows for p in prof_a.values()) + sum(p.total_rows for p in prof_b.values())
        total_trans = sum(r.total_transformations for r in clean_rep_a.values()) + sum(r.total_transformations for r in clean_rep_b.values())

        sys_msg = (
            f"**System**: Data ingestion and cleaning completed successfully.\n"
            f"- Loaded **{total_rows:,}** rows.\n"
            f"- Applied standardization rules; resolved **{total_trans:,}** column transformations and duplicates."
        )

        return ingest_res, clean_res, sys_msg
    except Exception as e:
        logger.error(f"Ingestion and cleaning failed: {traceback.format_exc()}")
        raise gr.Error(str(e))

def handle_schema_matching(
    cleaning_state: CleaningResult, provider: str, model_name: str
) -> tuple[SchemaMatchingResult, str]:
    if not cleaning_state or not cleaning_state.clean_a or not cleaning_state.clean_b:
        raise gr.Error("Missing clean source data for schema matching. Please complete Phase 2.")
    try:
        i_report, metadata = run_schema_matching(
            cleaning_state.clean_a, cleaning_state.clean_b, provider=provider, model_name=model_name
        )
        res = SchemaMatchingResult(
            integration_report=i_report,
            architect_metadata=metadata
        )
        sys_msg = "**System**: Integrated Global Schema generated successfully. You can now inspect the ER Diagram and refine it if needed by typing feedback in the chat."
        return res, sys_msg
    except Exception as e:
        logger.error(f"Schema matching failed: {traceback.format_exc()}")
        raise gr.Error(str(e))

def handle_schema_refinement(
    matching_state: SchemaMatchingResult, user_prompt: str, provider: str, model_name: str
) -> tuple[SchemaMatchingResult, str]:
    if not matching_state or not matching_state.integration_report:
        raise gr.Error("Missing integration report to refine.")
    try:
        new_report, metadata = refine_schema_via_llm(
            matching_state.integration_report,
            user_prompt,
            provider=provider,
            model_name=model_name
        )
        res = SchemaMatchingResult(
            integration_report=new_report,
            architect_metadata=matching_state.architect_metadata or {}
        )
        res.architect_metadata["refinement"] = metadata
        sys_msg = f"**System**: Refined schema based on your request: *\"{user_prompt}\"*"
        return res, sys_msg
    except Exception as e:
        logger.error(f"Schema refinement failed: {traceback.format_exc()}")
        raise gr.Error(str(e))

def handle_data_porting(
    cleaning_state: CleaningResult, matching_state: SchemaMatchingResult, 
    provider: str, model_name: str
) -> tuple[DataPortingResult, str]:
    if not cleaning_state or not matching_state or not matching_state.integration_report:
        raise gr.Error("Missing required schemas or integration report for data porting. Please complete Phase 3.")
    try:
        p_inst, p_tabs, p_rep, metadata = run_data_porting(
            cleaning_state.clean_a, cleaning_state.clean_b, 
            matching_state.integration_report, provider=provider, model_name=model_name
        )
        res = DataPortingResult(
            porting_instructions=p_inst,
            ported_tables=p_tabs,
            porting_report=p_rep,
            engineer_metadata=metadata
        )
        sys_msg = "**System**: Data porting complete. Source datasets successfully transformed and mapped to the global tables."
        return res, sys_msg
    except Exception as e:
        logger.error(f"Data porting failed: {traceback.format_exc()}")
        raise gr.Error(str(e))

def handle_er_propose(
    matching_state: SchemaMatchingResult, porting_state: DataPortingResult,
    provider: str, model_name: str
) -> tuple[dict[str, ERPipelineConfiguration], str]:
    if not matching_state or not matching_state.integration_report or not porting_state or not porting_state.ported_tables:
        raise gr.Error("Missing integration report or ported tables.")

    async def _propose_all():
        er_configs = {}
        for table_name, ported_table in porting_state.ported_tables.items():
            global_resource = next(
                (r for r in matching_state.integration_report.global_schema.resources if r.name == table_name),
                None
            )
            if not global_resource:
                continue
            
            profile_a = DataProfiler.profile_dataframe(ported_table.df_a, f"{table_name}_a")
            profile_b = DataProfiler.profile_dataframe(ported_table.df_b, f"{table_name}_b")
            
            config_obj, _ = await identify_er_config_via_llm(
                profile_a, profile_b, global_resource,
                model_name=model_name, provider=provider
            )
            er_configs[table_name] = config_obj
        return er_configs

    try:
        er_configs = asyncio.run(_propose_all())
        sys_msg = "**System**: Entity Resolution configurations proposed by LLM. You can adjust the weights, indexing keys, and threshold in the form."
        return er_configs, sys_msg
    except Exception as e:
        logger.error(f"ER proposal generation failed: {traceback.format_exc()}")
        raise gr.Error(str(e))

def handle_record_linkage(
    matching_state: SchemaMatchingResult, porting_state: DataPortingResult,
    provider: str, model_name: str, er_override_configs: dict[str, ERPipelineConfiguration] | None = None
) -> tuple[RecordLinkageResult, str]:
    if not matching_state or not matching_state.integration_report or not porting_state or not porting_state.ported_tables:
        raise gr.Error("Missing integration report or ported tables for record linkage. Please complete Phase 4.")
    try:
        er_res = run_record_linkage(
            matching_state.integration_report, porting_state.ported_tables,
            provider=provider, model_name=model_name,
            er_override_configs=er_override_configs,
            enable_refinement=False
        )
        res = RecordLinkageResult(
            er_results=er_res
        )
        total_matches = sum(len(r.matches) for r in er_res.values())
        total_uncertain = sum(len(r.uncertain) for r in er_res.values())
        sys_msg = f"**System**: Record linkage complete. Identified {total_matches:,} matches and {total_uncertain:,} uncertain pairs across all tables."
        return res, sys_msg
    except Exception as e:
        logger.error(f"Record linkage failed: {traceback.format_exc()}")
        raise gr.Error(str(e))

def handle_llm_refinement(result: EntityResolutionResult, model_name: str, provider: str) -> tuple[EntityResolutionResult, str]:
    if not result or result.uncertain is None or result.uncertain.empty:
        return result, "LLM refined 0 pairs: 0 matched, 0 rejected"
        
    try:
        # Call the async agent function synchronously
        coro = refine_uncertain_matches_via_llm(
            uncertain_pairs_df=result.uncertain,
            df_source_a=result.df_a_clean,
            df_source_b=result.df_b_clean,
            model_name=model_name,
            provider=provider
        )
        try:
            resolutions_map, metadata = asyncio.run(coro)
        except RuntimeError as e:
            if "running event loop" in str(e):
                resolutions_map, metadata = asyncio.get_event_loop().run_until_complete(coro)
            else:
                raise
            
        # Update/create the columns in result.uncertain in place
        if "llm_decision" not in result.uncertain.columns:
            result.uncertain["llm_decision"] = None
        if "llm_reasoning" not in result.uncertain.columns:
            result.uncertain["llm_reasoning"] = None
            
        matched_count = 0
        rejected_count = 0
        
        # Update result.uncertain for the resolved pairs.
        for pair, res in resolutions_map.items():
            if pair in result.uncertain.index:
                result.uncertain.loc[[pair], "llm_decision"] = res.is_match
                result.uncertain.loc[[pair], "llm_reasoning"] = res.reasoning
                if res.is_match:
                    matched_count += 1
                else:
                    rejected_count += 1
                    
        total_refined = len(resolutions_map)
        log_msg = f"LLM refined {total_refined} pairs: {matched_count} matched, {rejected_count} rejected"
        
        # Save metadata to result
        result.er_refinement_metadata = metadata
        
        return result, log_msg
        
    except Exception as e:
        logger.error(f"LLM refinement failed: {traceback.format_exc()}")
        raise gr.Error(str(e))


def handle_results_wrapper(
    data_root: str, provider: str, model_name: str,
    ingestion: IngestionResult, cleaning: CleaningResult,
    matching: SchemaMatchingResult, porting: DataPortingResult,
    linkage: RecordLinkageResult,
    fusion_result: DataFusionResult | None = None
) -> tuple[FinalReportResult, str]:
    try:
        merged_gav_meta = {}
        if matching.architect_metadata:
            merged_gav_meta.update(matching.architect_metadata)
        if porting.engineer_metadata:
            merged_gav_meta.update(porting.engineer_metadata)

        summary = build_results_summary(
            porting.ported_tables, linkage.er_results, porting.porting_report
        )
        
        report_file = save_final_pipeline_report(
            data_root, model_name, provider,
            ingestion.source_a, ingestion.source_b, ingestion.report_a, ingestion.report_b,
            cleaning.clean_a, cleaning.clean_b, cleaning.reports_a, cleaning.reports_b,
            ingestion.profiles_a, ingestion.profiles_b,
            matching.integration_report, porting.porting_instructions, merged_gav_meta,
            porting.ported_tables, porting.porting_report, linkage.er_results
        )
        
        res = FinalReportResult(
            report_path=report_file,
            summary=summary
        )
        sys_msg = f"**System**: Final pipeline execution report successfully compiled and saved to {report_file}."
        return res, sys_msg
    except Exception as e:
        logger.error(f"Results summary failed: {traceback.format_exc()}")
        raise gr.Error(f"Results summary failed: {e!s}")


def handle_run_fusion(
    porting_state: DataPortingResult,
    linkage_state: RecordLinkageResult,
    ingestion_state: IngestionResult,
    provider: str,
    model_name: str
) -> tuple[DataFusionConfigResult, dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]], str]:
    if not porting_state or not porting_state.ported_tables:
        raise gr.Error("Missing ported tables. Please complete Phase 4.")
    if not linkage_state or not linkage_state.er_results:
        raise gr.Error("Missing linkage results. Please complete Phase 5.")
    if not ingestion_state or not ingestion_state.source_a or not ingestion_state.source_b:
        raise gr.Error("Missing ingestion state.")
        
    try:
        tables = {}
        for table_name, ported_table in porting_state.ported_tables.items():
            df_a = ported_table.df_a
            df_b = ported_table.df_b
            er_res = linkage_state.er_results.get(table_name)
            
            if er_res is None or er_res.matches.empty:
                df_links = pd.DataFrame(columns=["left_id", "right_id"])
            else:
                df_links = pd.DataFrame(
                    list(er_res.matches.index),
                    columns=["left_id", "right_id"],
                )
            
            tables[table_name] = (df_a, df_b, df_links)
            
        source_a_origin = ingestion_state.source_a.package.name
        source_b_origin = ingestion_state.source_b.package.name
        
        engine = DataFusionEngine(model_name=model_name, provider=provider)
        multi_profile, multi_policy = engine.profile_and_propose(source_a_origin, source_b_origin, tables)
        
        config_result = DataFusionConfigResult(
            fusion_profile=multi_profile,
            fusion_policy=multi_policy
        )
        sys_msg = "**System**: Conflict profile and fusion policy generated. Please review the proposed strategy in the canvas and click **Execute Fusion** when ready."
        return config_result, tables, sys_msg
    except Exception as e:
        logger.error(f"Run data fusion failed: {traceback.format_exc()}")
        raise gr.Error(str(e))

def handle_execute_fusion(
    canvas_s: DataFusionConfigCanvasState,
    provider: str,
    model_name: str
) -> tuple[DataFusionResult, str]:
    if not canvas_s or not canvas_s.config_result:
        raise gr.Error("No fusion configuration state found. Please run Data Fusion proposal first.")
        
    try:
        policy = canvas_s.config_result.fusion_policy
        profile = canvas_s.config_result.fusion_profile
        tables = canvas_s.tables
        
        engine = DataFusionEngine(model_name=model_name, provider=provider)
        fused_tables = engine.execute(tables, policy, profile, merge_unlinked=True)
        
        total_rows = sum(len(df) for df in fused_tables.values())
        res = DataFusionResult(
            fused_tables=fused_tables,
            fusion_policy=policy,
            fusion_profile=profile
        )
        sys_msg = f"**System**: Data Fusion execution completed. Generated **{total_rows:,}** golden records in total. You can now generate the final pipeline report."
        return res, sys_msg
    except Exception as e:
        logger.error(f"Execute data fusion failed: {traceback.format_exc()}")
        raise gr.Error(str(e))
