import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from shared.ingestion import DataLoader, SourceData
from shared.cleaning.engine import clean_source_data
from shared.profiling.engine import DataProfiler
from .schema_architect import perform_gav_architect
from shared.porting.agent import generate_porting_instructions
from shared.porting.executor import port_data_to_global_schema
from entity_resolution.pipeline import run_entity_resolution
from entity_resolution.models import ERPipelineConfiguration

from .models import PipelineRunReport, TableRunResult, StepResults
from .visualization import print_pipeline_summary, finalize_pipeline_report

from shared.config import config
from shared.console import console

logger = logging.getLogger(__name__)

def run_pipeline(
    data_root: str | Path,
    *,
    model_name: Optional[str] = None,
    provider: Optional[str] = None,
    er_override_configs: Optional[Dict[str, ERPipelineConfiguration]] = None,
    strict_ingestion: bool = False,
    enable_er_refinement: bool = False,
    save_html: bool = False,
) -> PipelineRunReport:
    """
    Fully synchronous top-level orchestrator for the data integration pipeline.
    """
    # 0. RESOLVE DEFAULTS FROM CONFIG
    provider = provider or config.DEFAULT_PROVIDER
    if not model_name:
        if provider == config.PROVIDER_GOOGLE:
            model_name = config.DEFAULT_GOOGLE_MODEL
        elif provider == config.PROVIDER_OPENAI:
            model_name = config.DEFAULT_OPENAI_MODEL
        elif provider == config.PROVIDER_DEEPSEEK:
            model_name = config.DEFAULT_DEEPSEEK_MODEL
        else:
            model_name = "unknown"
    
    data_root_path = Path(data_root).resolve()
    timestamp = datetime.now()

    # 1. INGESTION
    with console.status("[bold blue]Ingesting sources..."):
        loader = DataLoader(strict_type_validation=strict_ingestion)
        source_a, report_a, source_b, report_b = loader.load_integration_input(data_root_path)
    console.print(f"Ingested: [cyan]{report_a.source_name}[/cyan] ({len(report_a.tables)} tables), [cyan]{report_b.source_name}[/cyan] ({len(report_b.tables)} tables) | Total: {report_a.total_rows + report_b.total_rows:,} rows")

    # 2. CLEANING
    with console.status("[bold green]Cleaning data..."):
        clean_a, reports_a = clean_source_data(source_a)
        clean_b, reports_b = clean_source_data(source_b)
    total_changes = sum(r.total_transformations for r in reports_a.values()) + sum(r.total_transformations for r in reports_b.values())
    console.print(f"Cleaned: {total_changes:,} transformations")

    # 3. PROFILING
    with console.status("[bold magenta]Profiling sources..."):
        profiles_a = DataProfiler.profile_source_data(clean_a)
        profiles_b = DataProfiler.profile_source_data(clean_b)
    console.print(f"Profiled: {len(profiles_a) + len(profiles_b)} tables")

    # 4. SCHEMA INTEGRATION & PORTING GENERATION (Decoupled)
    with console.status(f"[bold yellow]Schema Integration ([cyan]{model_name}[/cyan])..."):
        schema_a_json = json.dumps(source_a.package.model_dump())
        schema_b_json = json.dumps(source_b.package.model_dump())
        
        integration_report, architect_metadata = perform_gav_architect(
            schema_a_json, 
            schema_b_json,
            label_a=source_a.package.name,
            label_b=source_b.package.name,
            provider=provider,
            model_name=model_name
        )
        
    with console.status(f"[bold yellow]Porting Instructions Generation ([cyan]{model_name}[/cyan])..."):
        porting_instructions, engineer_metadata = generate_porting_instructions(
            schema_a=schema_a_json,
            schema_b=schema_b_json,
            integration_report=integration_report,
            label_a=source_a.package.name,
            label_b=source_b.package.name,
            provider=provider,
            model_name=model_name
        )
        
    gav_metadata = {
        "architect": architect_metadata,
        "engineer": engineer_metadata
    }
    
    logger.info(f"Porting Instructions: {porting_instructions.model_dump_json(indent=2)}")
    
    total_tokens = sum(m.total_tokens for m in gav_metadata.values())
    total_time = sum(m.execution_time_seconds for m in gav_metadata.values())
    console.print(f"Schema Integration & Porting: {total_tokens:,} tokens | {total_time:.1f}s")

    # 5. DATA PORTING
    with console.status("[bold blue]Porting data to global schema..."):
        ported_tables, porting_report = port_data_to_global_schema(clean_a, clean_b, integration_report, porting_instructions)
    console.print(f"Ported: {len(ported_tables)} global tables | {porting_report.total_warnings} warnings")

    # 6. ENTITY RESOLUTION
    console.print("[bold cyan]Starting Entity Resolution...[/bold cyan]")
    er_results = {}
    table_run_results = {}

    for global_table_name, ported_table in ported_tables.items():
        # Find global resource metadata
        global_resource = next(
            (r for r in integration_report.global_schema.resources if r.name == global_table_name), 
            None
        )
        if not global_resource:
            logger.warning(f"Global resource '{global_table_name}' not found in integration report.")
            continue

        # Resolve source table names for profiling lookup via porting instructions
        source_a_table = None
        source_b_table = None
        
        instructions = porting_instructions.global_table_instructions.get(global_table_name)
        if instructions:
            for recipe in instructions.construction_recipes:
                if recipe.type == "single":
                    if recipe.source_label == source_a.package.name:
                        source_a_table = recipe.table_name
                    elif recipe.source_label == source_b.package.name:
                        source_b_table = recipe.table_name
                elif recipe.type == "join":
                    # Check both sides of the join
                    if recipe.left_source == source_a.package.name:
                        source_a_table = recipe.left_table
                    elif recipe.left_source == source_b.package.name:
                        source_b_table = recipe.left_table
                    
                    if recipe.right_source == source_a.package.name:
                        source_a_table = recipe.right_table
                    elif recipe.right_source == source_b.package.name:
                        source_b_table = recipe.right_table

        # Compute profiles on the ported data (aligned to global schema)
        profile_a = DataProfiler.profile_dataframe(ported_table.df_a, f"{global_table_name}_a")
        profile_b = DataProfiler.profile_dataframe(ported_table.df_b, f"{global_table_name}_b")

        # Fallback if profile_a/b are still None (though profile_dataframe should return something)
        if profile_a is None:
            profile_a = DataProfiler.profile_dataframe(ported_table.df_a, f"{global_table_name}_a")
        if profile_b is None:
            profile_b = DataProfiler.profile_dataframe(ported_table.df_b, f"{global_table_name}_b")

        override = er_override_configs.get(global_table_name) if er_override_configs else None
        
        # Diagnostics for empty indexing
        logger.info(f"ER Diagnostics for '{global_table_name}':")
        logger.info(f"  df_a shape: {ported_table.df_a.shape}, nulls: {ported_table.df_a.isnull().sum().to_dict()}")
        logger.info(f"  df_b shape: {ported_table.df_b.shape}, nulls: {ported_table.df_b.isnull().sum().to_dict()}")
        if not ported_table.df_a.empty:
            logger.info(f"  df_a head:\n{ported_table.df_a.head(3)}")
        if not ported_table.df_b.empty:
            logger.info(f"  df_b head:\n{ported_table.df_b.head(3)}")

        # Bridge to async ER pipeline
        with console.status(f"[bold cyan]ER for table [cyan]'{global_table_name}'[/cyan]..."):
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
                    enable_refinement=enable_er_refinement,
                )
            )
        console.print(f"  └─ [cyan]{global_table_name}[/cyan]: {len(result.matches)} matches, {len(result.uncertain)} uncertain")
        er_results[global_table_name] = result

        # Summary result
        table_run_results[global_table_name] = TableRunResult(
            global_table_name=global_table_name,
            source_a_table=source_a_table or "N/A",
            source_b_table=source_b_table or "N/A",
            porting_warnings=ported_table.warnings,
            num_rows_a=len(ported_table.df_a),
            num_rows_b=len(ported_table.df_b),
            num_matches=len(result.matches),
            num_uncertain=len(result.uncertain),
            num_non_matches=len(result.non_matches),
            er_config=result.config
        )

    # 7. ASSEMBLE REPORT
    step_results = StepResults(
        source_a=source_a,
        source_b=source_b,
        ingestion_report_a=report_a,
        ingestion_report_b=report_b,
        clean_source_a=clean_a,
        clean_source_b=clean_b,
        cleaning_reports_a=reports_a,
        cleaning_reports_b=reports_b,
        profiles_a=profiles_a,
        profiles_b=profiles_b,
        integration_report=integration_report,
        porting_instructions=porting_instructions,
        gav_metadata=gav_metadata,
        ported_tables=ported_tables,
        porting_report=porting_report,
        er_results=er_results
    )

    pipeline_report = PipelineRunReport(
        data_root=str(data_root_path),
        model_name=model_name,
        gav_metadata=gav_metadata,
        integration_report=integration_report,
        porting_instructions=porting_instructions,
        table_results=table_run_results,
        step_results=step_results
    )

    # 8. SAVE HTML REPORT
    try:
        report, report_file = finalize_pipeline_report(
            data_root=data_root_path,
            model_name=model_name,
            provider=provider,
            step_results=step_results,
            save_html=save_html
        )
        if report_file:
            console.print(f"Pipeline complete. Report: [dim]{report_file}[/dim]")
        else:
            console.print("Pipeline complete. (Report export skipped)")
        return report
    except Exception as e:
        console.print(f"Failed to generate HTML report: {e}")
        return pipeline_report
