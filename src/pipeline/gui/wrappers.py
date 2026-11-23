"""
Pipeline phase wrappers for the Gradio interactive UI.

Each function corresponds to one wizard step and accepts/returns plain Python
objects (DataFrames, dicts, Pydantic models) so they can be stored in
``gr.State`` between steps. Rich console output is suppressed intentionally;
progress feedback is handled by the Gradio UI layer instead.
"""

from __future__ import annotations

import asyncio
import json
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple, List

import pandas as pd

from shared.ingestion import DataLoader, SourceData, IngestionReport
from shared.cleaning.engine import clean_source_data
from shared.profiling.engine import DataProfiler, GUIProfiler
from shared.profiling.models import TableProfile, GUITableProfile
from shared.porting import PortedTable, PortingReport
from shared.porting.executor import port_data_to_global_schema
from shared.porting.agent import generate_porting_instructions
from shared.config import config as app_config
from shared.schema_models import IntegrationReport
from pipeline.schema_architect import perform_gav_architect
from shared.porting.models import PortingInstructionsReport
from entity_resolution.pipeline import run_entity_resolution
from entity_resolution.models import ERPipelineConfiguration, EntityResolutionResult

from ..models import PipelineRunReport, StepResults, TableRunResult
from ..visualization import finalize_pipeline_report

logger = logging.getLogger(__name__)


def resolve_model(provider: Optional[str] = None, model_name: Optional[str] = None) -> str:
    """Resolve default model for a given provider if model_name is not provided."""
    provider = provider or app_config.DEFAULT_PROVIDER
    if not model_name:
        if provider == app_config.PROVIDER_GOOGLE:
            return app_config.DEFAULT_GOOGLE_MODEL
        elif provider == app_config.PROVIDER_OPENAI:
            return app_config.DEFAULT_OPENAI_MODEL
        else:
            return app_config.DEFAULT_GOOGLE_MODEL
    return model_name


# ---------------------------------------------------------------------------
# Phase 1: Ingestion


def run_ingestion(
    data_root: str | Path,
    *,
    strict: bool = False,
) -> Tuple[
    SourceData,
    IngestionReport,
    SourceData,
    IngestionReport,
    Dict[str, GUITableProfile],
    Dict[str, GUITableProfile],
]:
    """Load and ingest both source datasets from *data_root*."""
    loader = DataLoader(strict_type_validation=strict)
    source_a, report_a, source_b, report_b = loader.load_integration_input(
        Path(data_root).resolve()
    )

    profiles_a = GUIProfiler.profile_source_data(source_a)
    profiles_b = GUIProfiler.profile_source_data(source_b)

    logger.info(
        "Ingestion complete: %s (%d tables), %s (%d tables)",
        report_a.source_name,
        len(report_a.tables),
        report_b.source_name,
        len(report_b.tables),
    )
    return source_a, report_a, source_b, report_b, profiles_a, profiles_b

# ---------------------------------------------------------------------------
# Phase 2: Cleaning
# ---------------------------------------------------------------------------

def run_cleaning(
    source_a: SourceData,
    source_b: SourceData,
) -> Tuple[
    SourceData,
    Dict,
    SourceData,
    Dict,
]:
    """Apply standardisation rules to both sources."""
    clean_a, reports_a = clean_source_data(source_a)
    clean_b, reports_b = clean_source_data(source_b)

    total_changes = (
        sum(r.total_transformations for r in reports_a.values())
        + sum(r.total_transformations for r in reports_b.values())
    )
    logger.info("Cleaning complete: %d total transformations.", total_changes)

    return clean_a, reports_a, clean_b, reports_b


# ---------------------------------------------------------------------------
# Phase 3: Schema Integration
# ---------------------------------------------------------------------------

def run_schema_matching(
    source_a: SourceData,
    source_b: SourceData,
    *,
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
) -> Tuple[IntegrationReport, Dict]:
    """Run AI-driven schema integration (architect stage) on the two source schemas."""
    provider = provider or app_config.DEFAULT_PROVIDER
    model_name = resolve_model(provider, model_name)

    schema_a_json = json.dumps(source_a.package.model_dump())
    schema_b_json = json.dumps(source_b.package.model_dump())

    integration_report, architect_metadata = perform_gav_architect(
        schema_a_json,
        schema_b_json,
        label_a=source_a.package.name,
        label_b=source_b.package.name,
        provider=provider,
        model_name=model_name,
    )

    logger.info(
        "Schema integration architect complete: %d tokens used.", architect_metadata.total_tokens
    )

    return integration_report, {"architect": architect_metadata}


# ---------------------------------------------------------------------------
# Phase 4: Data Porting (Execution)
# ---------------------------------------------------------------------------

def run_data_porting(
    clean_a: SourceData,
    clean_b: SourceData,
    integration_report: IntegrationReport,
    *,
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
) -> Tuple[PortingInstructionsReport, Dict[str, PortedTable], PortingReport, Dict]:
    """Run PortingEngineer agent to generate instructions and execute data porting."""
    provider = provider or app_config.DEFAULT_PROVIDER
    model_name = resolve_model(provider, model_name)

    schema_a_json = json.dumps(clean_a.package.model_dump())
    schema_b_json = json.dumps(clean_b.package.model_dump())

    porting_instructions, engineer_metadata = generate_porting_instructions(
        schema_a=schema_a_json,
        schema_b=schema_b_json,
        integration_report=integration_report,
        label_a=clean_a.package.name,
        label_b=clean_b.package.name,
        provider=provider,
        model_name=model_name,
    )

    ported_tables, porting_report = port_data_to_global_schema(
        clean_a, clean_b, integration_report, porting_instructions
    )

    logger.info(
        "Data porting complete: %d tokens used.", engineer_metadata.total_tokens
    )

    return porting_instructions, ported_tables, porting_report, {"engineer": engineer_metadata}


# ---------------------------------------------------------------------------
# Phase 4: Record Linkage (Entity Resolution configuration + execution)
# ---------------------------------------------------------------------------

def run_record_linkage(
    integration_report: IntegrationReport,
    ported_tables: Dict[str, PortedTable],
    *,
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
    er_override_configs: Optional[Dict[str, ERPipelineConfiguration]] = None,
    enable_refinement: bool = False,
) -> Tuple[
    Dict[str, EntityResolutionResult],
]:
    """Run entity resolution on each table using pre-ported data."""
    provider = provider or app_config.DEFAULT_PROVIDER
    model_name = resolve_model(provider, model_name)

    # Run ER per global table
    er_results: Dict[str, EntityResolutionResult] = {}

    for global_table_name, ported_table in ported_tables.items():
        global_resource = next(
            (
                r
                for r in integration_report.global_schema.resources
                if r.name == global_table_name
            ),
            None,
        )
        if not global_resource:
            logger.warning(
                "Global resource '%s' not found in integration report; skipping ER.",
                global_table_name,
            )
            continue

        profile_a = DataProfiler.profile_dataframe(
            ported_table.df_a, f"{global_table_name}_a"
        )
        profile_b = DataProfiler.profile_dataframe(
            ported_table.df_b, f"{global_table_name}_b"
        )

        override = (
            er_override_configs.get(global_table_name) if er_override_configs else None
        )

        result = asyncio.run(
            run_entity_resolution(
                ported_table.df_a,
                ported_table.df_b,
                profile_a,
                profile_b,
                global_resource,
                override_config=override,
                model_name=model_name,
                provider=provider,
                enable_refinement=enable_refinement,
            )
        )
        er_results[global_table_name] = result
        logger.info(
            "ER complete for '%s': %d matches, %d uncertain.",
            global_table_name,
            len(result.matches),
            len(result.uncertain),
        )

    return er_results


# ---------------------------------------------------------------------------
# Phase 5: Results helpers
# ---------------------------------------------------------------------------

def build_results_summary(
    ported_tables: Dict[str, PortedTable],
    er_results: Dict[str, EntityResolutionResult],
    porting_report: PortingReport,
) -> Dict:
    """Aggregate a plain-dict summary of the final pipeline results."""
    tables_summary = []
    for name, result in er_results.items():
        ported = ported_tables.get(name)
        tables_summary.append(
            {
                "table": name,
                "rows_a": len(ported.df_a) if ported is not None else 0,
                "rows_b": len(ported.df_b) if ported is not None else 0,
                "matches": len(result.matches),
                "uncertain": len(result.uncertain),
                "non_matches": len(result.non_matches),
            }
        )

    return {
        "tables": tables_summary,
        "total_warnings": porting_report.total_warnings,
        "total_matches": sum(r["matches"] for r in tables_summary),
        "total_uncertain": sum(r["uncertain"] for r in tables_summary),
    }


def save_final_pipeline_report(
    data_root: str | Path,
    model_name: str,
    provider: str,
    source_a: SourceData,
    source_b: SourceData,
    ingestion_report_a: IngestionReport,
    ingestion_report_b: IngestionReport,
    clean_source_a: SourceData,
    clean_source_b: SourceData,
    cleaning_reports_a: Dict,
    cleaning_reports_b: Dict,
    profiles_a: Dict,
    profiles_b: Dict,
    integration_report: IntegrationReport,
    porting_instructions: PortingInstructionsReport,
    gav_metadata: Dict,
    ported_tables: Dict,
    porting_report: PortingReport,
    er_results: Dict,
) -> str:
    """
    Constructs the full PipelineRunReport and saves the HTML report.
    Uses the shared visualization logic.
    """
    # 1. Assemble StepResults
    step_results = StepResults(
        source_a=source_a,
        source_b=source_b,
        ingestion_report_a=ingestion_report_a,
        ingestion_report_b=ingestion_report_b,
        clean_source_a=clean_source_a,
        clean_source_b=clean_source_b,
        cleaning_reports_a=cleaning_reports_a,
        cleaning_reports_b=cleaning_reports_b,
        profiles_a=profiles_a,
        profiles_b=profiles_b,
        integration_report=integration_report,
        porting_instructions=porting_instructions,
        gav_metadata=gav_metadata,
        ported_tables=ported_tables,
        porting_report=porting_report,
        er_results=er_results
    )

    # 2. Finalize and save
    try:
        _, report_file = finalize_pipeline_report(
            data_root=data_root,
            model_name=model_name,
            provider=provider,
            step_results=step_results,
            save_html=True
        )
        return str(report_file)
    except Exception as e:
        logger.error(f"Failed to generate final report: {traceback.format_exc()}")
        return f"Error: {e}"
