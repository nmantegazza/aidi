import pandas as pd
from datetime import datetime
from rich.markup import escape
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich import box
from pathlib import Path
from typing import Tuple, Optional
from .models import PipelineRunReport, StepResults, TableRunResult
from shared.profiling.models import TableProfile
from shared.html_builder import build_html_document, render_markdown_to_html, render_mermaid_to_html
from shared.config import config
from shared.schema_models import DataPackage

def generate_mermaid_code(schema: DataPackage) -> str:
    """Generates Mermaid ER diagram code from a DataPackage schema."""
    lines = ["erDiagram"]
    
    all_relationships = []
    for resource in schema.resources:
        table_schema = resource.schema_info
        for fk in table_schema.foreignKeys:
            target_res = fk.reference.resource
            target_field = fk.reference.fields
            if isinstance(target_field, list):
                target_field = target_field[0]
            
            all_relationships.append({
                "source": resource.name,
                "target": target_res,
                "label": fk.fields if isinstance(fk.fields, str) else fk.fields[0]
            })

    for resource in schema.resources:
        safe_name = resource.name.replace(" ", "_").replace("-", "_")
        lines.append(f"    {safe_name} {{")
        
        table_schema = resource.schema_info
        pk_cols = set(table_schema.primary_key_columns)
        
        fk_cols = set()
        for fk in table_schema.foreignKeys:
            if isinstance(fk.fields, str):
                fk_cols.add(fk.fields)
            else:
                fk_cols.update(fk.fields)
        
        for field in table_schema.fields:
            d_type = field.type.lower()
            safe_attr_name = field.name.replace(" ", "_").replace("-", "_")
            keys = []
            if field.name in pk_cols:
                keys.append("PK")
            if field.name in fk_cols:
                keys.append("FK")
            key_str = f" {','.join(keys)}" if keys else ""
            lines.append(f"        {d_type} {safe_attr_name}{key_str}")
        lines.append("    }")

    for rel in all_relationships:
        src = rel["source"].replace(" ", "_").replace("-", "_")
        trg = rel["target"].replace(" ", "_").replace("-", "_")
        lines.append(f'    {src} ||--o{{ {trg} : "{rel["label"]}"')

    return "\n".join(lines)

console = Console()

def print_pipeline_summary(report: PipelineRunReport) -> None:
    """
    Prints a structured Rich panel per stage to summarize the pipeline run.
    """
    console.print("\n")
    console.print(Panel(
        f"[bold blue]Pipeline Run Summary[/bold blue]\n"
        f"Data Root: {escape(str(report.data_root))}\n"
        f"Timestamp: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"LLM Model: {escape(str(report.model_name))}",
        expand=False,
        box=box.DOUBLE
    ))

    # 1. SCHEMA INTEGRATION STAGE
    gav_table = Table(title="Stage 1: Schema Integration", box=box.SIMPLE)
    gav_table.add_column("Metric", style="cyan")
    gav_table.add_column("Value", style="white")
    
    # Count conflicts
    total_conflicts = sum(len(cr.conflicts) for cr in report.integration_report.conflicts_report)
    
    gav_table.add_row("Conflicts Found", str(total_conflicts))
    gav_table.add_row("Global Tables", str(len(report.integration_report.global_schema.resources)))
    gav_table.add_row("Execution Time", f"{report.gav_metadata.execution_time_seconds:.2f}s")
    gav_table.add_row("Total Tokens", f"{report.gav_metadata.total_tokens:,}")
    
    console.print(gav_table)

    # 2. CLEANING STAGE
    clean_table = Table(title="Stage 2: Data Cleaning", box=box.SIMPLE)
    clean_table.add_column("Source", style="cyan")
    clean_table.add_column("Table", style="cyan")
    clean_table.add_column("Rows Before", style="white")
    clean_table.add_column("Duplicates Removed", style="yellow")
    clean_table.add_column("WS Nullified", style="yellow")
    
    for table, report_a in report.step_results.cleaning_reports_a.items():
        clean_table.add_row(
            "Source A", table, str(report_a.rows_before), 
            str(report_a.duplicates_removed), str(report_a.whitespace_cells_nullified)
        )
    for table, report_b in report.step_results.cleaning_reports_b.items():
        clean_table.add_row(
            "Source B", table, str(report_b.rows_before), 
            str(report_b.duplicates_removed), str(report_b.whitespace_cells_nullified)
        )
    
    console.print(clean_table)

    # 3. PORTING & ER STAGE
    er_table = Table(title="Stage 3: Porting & Entity Resolution", box=box.SIMPLE)
    er_table.add_column("Global Table", style="cyan")
    er_table.add_column("Porting Warnings", style="yellow")
    er_table.add_column("Rows A/B", style="white")
    er_table.add_column("Matches", style="green", justify="right")
    er_table.add_column("Uncertain", style="yellow", justify="right")
    er_table.add_column("Non-Matches", style="red", justify="right")
    er_table.add_column("ER Indexing Keys", style="dim")
    
    for name, tr in report.table_results.items():
        keys_str = ", ".join(tr.er_config.indexing_keys) if hasattr(tr.er_config, "indexing_keys") else getattr(tr.er_config, "sorting_key", "N/A")
        er_table.add_row(
            name,
            str(len(tr.porting_warnings)),
            f"{tr.num_rows_a} / {tr.num_rows_b}",
            str(tr.num_matches),
            str(tr.num_uncertain),
            str(tr.num_non_matches),
            keys_str
        )
    
    console.print(er_table)


    # FINAL TOTALS
    summary_panel = Panel(
        f"[bold green]Final Integration Results[/bold green]\n"
        f"Total Global Tables: [bold]{report.total_tables}[/bold]\n"
        f"Total Matched Entities: [bold green]{report.matched_count}[/bold green]\n"
        f"Total Porting Warnings: [bold yellow]{report.total_porting_warnings}[/bold yellow]",
        expand=False,
        border_style="green"
    )
    console.print(summary_panel)
    console.print("\n")

# --- SHARED REPORTING LOGIC ---

def finalize_pipeline_report(
    data_root: str | Path,
    model_name: str,
    provider: str,
    step_results: StepResults,
    save_html: bool = False,
) -> Tuple[PipelineRunReport, Optional[Path]]:
    """
    Assembles the full PipelineRunReport, generates the HTML, and saves it if save_html is True.
    This logic is shared between the synchronous runner (CLI) and step-by-step wrappers (GUI).
    """
    # 1. Construct TableRunResult for each global table
    table_run_results = {}
    
    for global_table_name, er_result in step_results.er_results.items():
        ported_table = step_results.ported_tables.get(global_table_name)
        if not ported_table:
            continue
            
        source_a_table = "N/A"
        source_b_table = "N/A"
        
        # Try to resolve source table names from porting instructions for the summary
        instructions = step_results.porting_instructions.global_table_instructions.get(global_table_name)
        if instructions:
            for recipe in instructions.construction_recipes:
                if recipe.type == "single":
                    if recipe.source_label == step_results.source_a.package.name:
                        source_a_table = recipe.table_name
                    elif recipe.source_label == step_results.source_b.package.name:
                        source_b_table = recipe.table_name
                elif recipe.type == "join":
                    if recipe.left_source == step_results.source_a.package.name:
                        source_a_table = recipe.left_table
                    elif recipe.left_source == step_results.source_b.package.name:
                        source_b_table = recipe.left_table
                    
                    if recipe.right_source == step_results.source_a.package.name:
                        source_a_table = recipe.right_table
                    elif recipe.right_source == step_results.source_b.package.name:
                        source_b_table = recipe.right_table

        table_run_results[global_table_name] = TableRunResult(
            global_table_name=global_table_name,
            source_a_table=source_a_table,
            source_b_table=source_b_table,
            porting_warnings=ported_table.warnings,
            num_rows_a=len(ported_table.df_a),
            num_rows_b=len(ported_table.df_b),
            num_matches=len(er_result.matches),
            num_uncertain=len(er_result.uncertain),
            num_non_matches=len(er_result.non_matches),
            er_config=er_result.config
        )

    # 2. Assemble PipelineRunReport
    pipeline_report = PipelineRunReport(
        data_root=str(data_root),
        model_name=model_name,
        timestamp=datetime.now(),
        gav_metadata=step_results.gav_metadata,
        integration_report=step_results.integration_report,
        porting_instructions=step_results.porting_instructions,
        table_results=table_run_results,
        step_results=step_results
    )

    if not save_html:
        return pipeline_report, None

    # 3. Save HTML report
    data_root_path = Path(data_root).resolve()
    input_name = data_root_path.name
    safe_model_name = model_name.replace(":", "_").replace("/", "_")
    
    base_output = config.OUTPUT_BASE_DIR / "pipeline"
    output_dir = base_output / input_name / provider / safe_model_name
    output_dir.mkdir(parents=True, exist_ok=True)

    ts_str = pipeline_report.timestamp.strftime("%Y%m%d_%H%M%S")
    report_file = output_dir / f"{ts_str}_report.html"

    html_content = generate_pipeline_html_report(pipeline_report, provider)
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    return pipeline_report, report_file


# --- HTML REPORT GENERATION ---

def _render_df_sample(df: pd.DataFrame, max_rows: int = 10) -> str:
    """Renders a sample of a DataFrame as an HTML table."""
    if df.empty:
        return "_No data._"
    
    sample = df.head(max_rows)
    return sample.to_html(classes='table table-striped', index=False, border=0)

def _render_source_insight_table(profile: TableProfile) -> str:
    rows = []
    for col_name, p in profile.column_profiles.items():
        samples = ", ".join(p.distinct_samples[:3])
        rows.append(f"<tr><td>{col_name}</td><td>{p.dtype}</td><td>{100-p.null_percentage:.1f}%</td><td>{p.uniqueness_percentage:.1f}%</td><td><i style='color: #666;'>{samples}</i></td></tr>")
    
    return f"""
    <table class="source-insight-table">
        <thead><tr><th>Column</th><th>Type</th><th>Comp.</th><th>Uniq.</th><th>Samples</th></tr></thead>
        <tbody>{"".join(rows)}</tbody>
    </table>
    """

def _format_trans_logic(trans_list: list, source_label: str) -> str:
    """Helper to turn AST objects into readable strings for the report."""
    relevant = [t for t in trans_list if t.source_label == source_label]
    if not relevant: return "-"
    
    parts = []
    for t in relevant:
        if t.type == "direct": parts.append(f"Direct({t.source_column})")
        elif t.type == "concat": parts.append(f"Concat({', '.join(t.source_columns)})")
        elif t.type == "split": parts.append(f"Split({t.source_column}, idx={t.index})")
        elif t.type == "slice": parts.append(f"Slice({t.source_column}, {t.start}:{t.end})")
        elif t.type == "type_cast": parts.append(f"Cast({t.target_type})")
        elif t.type == "math_operation": parts.append(f"Math({t.operator}{t.operand})")
    return " → ".join(parts)

def generate_pipeline_html_report(report: PipelineRunReport, provider: str) -> str:
    """
    Generates a complete HTML report for the entire pipeline run.
    """
    md_content = []
    
    # 1. RUN SUMMARY
    md_content.append("# Data Integration Pipeline Report\n")
    md_content.append(f"**Data Root:** `{report.data_root}`\n")
    md_content.append(f"**Timestamp:** {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
    md_content.append(f"**LLM Provider:** `{provider}`\n")
    md_content.append(f"**LLM Model:** `{report.model_name}`\n")
    
    summary_stats = [
        {"Metric": "Total Global Tables", "Value": report.total_tables},
        {"Metric": "Total Matched Entities", "Value": report.matched_count},
        {"Metric": "Total Porting Warnings", "Value": report.total_porting_warnings}
    ]
    md_content.append("\n## Overall Summary\n")
    md_content.append(pd.DataFrame(summary_stats).to_markdown(index=False) + "\n")
    md_content.append("---")

    # 2. INGESTION
    md_content.append("## Stage 1: Ingestion\n")
    for source_label, ing_report in [("Source A", report.step_results.ingestion_report_a), 
                                     ("Source B", report.step_results.ingestion_report_b)]:
        md_content.append(f"### {source_label}\n")
        md_content.append(f"- **Base Path:** `{ing_report.base_path}`\n")
        md_content.append(f"- **Total Rows:** {ing_report.total_rows:,}\n")
        
        table_data = []
        for table_name, tr in ing_report.tables.items():
            table_data.append({
                "Table": table_name,
                "Rows": tr.row_count,
                "Cols": tr.col_count,
                "PKs": ", ".join(tr.primary_keys)
            })
        md_content.append(pd.DataFrame(table_data).to_markdown(index=False) + "\n")
    md_content.append("---")

    # 3. CLEANING
    md_content.append("## Stage 2: Data Cleaning\n")
    cleaning_summary = []
    for table, r in report.step_results.cleaning_reports_a.items():
        cleaning_summary.append({"Source": "Source A", "Table": table, "Rows Before": r.rows_before, "Dupes Removed": r.duplicates_removed, "WS Nullified": r.whitespace_cells_nullified})
    for table, r in report.step_results.cleaning_reports_b.items():
        cleaning_summary.append({"Source": "Source B", "Table": table, "Rows Before": r.rows_before, "Dupes Removed": r.duplicates_removed, "WS Nullified": r.whitespace_cells_nullified})
    
    md_content.append(pd.DataFrame(cleaning_summary).to_markdown(index=False) + "\n")
    
    # Cleaning Examples
    md_content.append("### Example Transformations\n")
    examples_found = False
    for source_label, reports in [("Source A", report.step_results.cleaning_reports_a), ("Source B", report.step_results.cleaning_reports_b)]:
        for table, r in reports.items():
            if r.examples:
                examples_found = True
                md_content.append(f"#### {source_label}: {table}\n")
                ex_data = [{"Column": ex.column, "Operation": ex.operation, "Before": f"`{ex.before}`", "After": f"`{ex.after}`"} for ex in r.examples[:5]]
                md_content.append(pd.DataFrame(ex_data).to_markdown(index=False) + "\n")
    if not examples_found:
        md_content.append("_No specific transformations recorded._\n")
    md_content.append("---")

    # 4. PROFILING
    md_content.append("## Stage 3: Profiling & Input Schemas\n")
    
    # We'll use Mermaid for schemas
    mermaid_a = generate_mermaid_code(report.step_results.source_a.package)
    mermaid_b = generate_mermaid_code(report.step_results.source_b.package)
    
    # Render Source Insight Tables
    insight_a = []
    for table_name, profile in report.step_results.profiles_a.items():
        insight_a.append(f"<h4>Table: {table_name}</h4>")
        insight_a.append(_render_source_insight_table(profile))
        
    insight_b = []
    for table_name, profile in report.step_results.profiles_b.items():
        insight_b.append(f"<h4>Table: {table_name}</h4>")
        insight_b.append(_render_source_insight_table(profile))

    profiling_html = f"""
<div class="side-by-side">
    <div class="flex-col">
        <h3>Source A Schema</h3>
{render_mermaid_to_html(mermaid_a)}
        <h3>Source A Insight</h3>
{"".join(insight_a)}
    </div>
    <div class="flex-col">
        <h3>Source B Schema</h3>
{render_mermaid_to_html(mermaid_b)}
        <h3>Source B Insight</h3>
{"".join(insight_b)}
    </div>
</div>
"""
    md_content.append(profiling_html)
    md_content.append("---")

    # 5. SCHEMA INTEGRATION
    md_content.append("## Stage 4: Schema Integration\n")
    
    # Execution Summary
    md_content.append("## Schema Integration Summary\n")
    
    total_tokens = sum(m.total_tokens for m in report.gav_metadata.values())
    total_time = sum(m.execution_time_seconds for m in report.gav_metadata.values())
    
    md_content.append(f"- **Aggregate Execution Time:** {total_time:.2f}s\n")
    md_content.append(f"- **Aggregate Tokens:** {total_tokens:,}\n")
    
    for label, meta in report.gav_metadata.items():
        md_content.append(f"  - **{label.capitalize()} Agent:** {meta.total_tokens:,} tokens in {meta.execution_time_seconds:.1f}s\n")
    
    # Conflict Resolution
    md_content.append("### Conflict Resolution\n")
    if report.integration_report.conflicts_report:
        for group in report.integration_report.conflicts_report:
            if group.conflicts:
                md_content.append(f"#### Type: `{group.conflict_type.value}`\n")
                c_data = [{"Source Items": ", ".join(c.source_items), "Target Items": ", ".join(c.target_items), "Resolution": c.resolution_strategy} for c in group.conflicts]
                md_content.append(pd.DataFrame(c_data).to_markdown(index=False) + "\n")
    else:
        md_content.append("_No schema conflicts detected._\n")

    md_content.append("### Global Schema Definition\n")
    global_mermaid = generate_mermaid_code(report.integration_report.global_schema)
    md_content.append(render_mermaid_to_html(global_mermaid))

    # Physical Porting Plan (AST)
    md_content.append("### Physical Porting Plan (Data Engineer Decisions)\n")
    md_content.append("This section describes how the Data Engineer agent decided to build each global table from source data.\n")
    
    label_a = report.step_results.source_a.package.name or "Source A"
    label_b = report.step_results.source_b.package.name or "Source B"

    for global_table, instructions in report.porting_instructions.global_table_instructions.items():
        md_content.append(f"#### Table: `{global_table}`\n")
        
        # Recipes
        recipes_str = []
        for r in instructions.construction_recipes:
            if r.type == "single":
                recipes_str.append(f"Loaded from `{r.source_label}.{r.table_name}`")
            elif r.type == "join":
                recipes_str.append(f"Joined `{r.left_table}` and `{r.right_table}` on `{r.left_on} == {r.right_on}`")
        
        md_content.append(f"- **Strategy:** {', '.join(recipes_str)}\n")
        
        # Field Transformations (Unified Table)
        unified_trans = []
        for field_name, trans_list in instructions.field_transformations.items():
            unified_trans.append({
                "Global Column": field_name,
                label_a: _format_trans_logic(trans_list, label_a),
                label_b: _format_trans_logic(trans_list, label_b)
            })
        
        if unified_trans:
            md_content.append(pd.DataFrame(unified_trans).to_markdown(index=False) + "\n")
        md_content.append("\n")

    md_content.append("---")

    # 6. DATA PORTING
    md_content.append("## Stage 5: Data Porting\n")
    porting_data = []
    for table_name, tr in report.table_results.items():
        porting_data.append({
            "Global Table": table_name,
            f"{label_a} Rows": tr.num_rows_a,
            f"{label_b} Rows": tr.num_rows_b,
            "Warnings": len(tr.porting_warnings)
        })
    md_content.append(pd.DataFrame(porting_data).to_markdown(index=False) + "\n")
    
    # Result Preview (DataFrames)
    md_content.append("### Result Preview\n")
    for table_name, ported_table in report.step_results.ported_tables.items():
        md_content.append(f"#### Table: `{table_name}`\n")
        
        df_a_html = ported_table.df_a.head(5).to_html(classes='table table-sm table-striped', index=False, border=0)
        df_b_html = ported_table.df_b.head(5).to_html(classes='table table-sm table-striped', index=False, border=0)
        
        preview_html = f"""
<div class="preview-container">
    <div class="preview-box">
        <h5>{label_a}</h5>
        {df_a_html}
    </div>
    <div class="preview-box">
        <h5>{label_b}</h5>
        {df_b_html}
    </div>
</div>
"""
        md_content.append(preview_html)

    if report.total_porting_warnings > 0:
        md_content.append("### Porting Warnings\n")
        all_warnings = []
        for table_name, tr in report.table_results.items():
            for w in tr.porting_warnings:
                all_warnings.append({"Table": table_name, "Column": w.global_column, "Source": w.source_label, "Message": w.message})
        md_content.append(pd.DataFrame(all_warnings[:20]).to_markdown(index=False) + ("\n_... (showing first 20 warnings)_" if len(all_warnings) > 20 else "") + "\n")
    md_content.append("---")

    # 7. ENTITY RESOLUTION
    md_content.append("## Stage 6: Entity Resolution\n")
    
    for table_name, tr in report.table_results.items():
        er_result = report.step_results.er_results.get(table_name)
        if not er_result: continue
        
        md_content.append(f"### Global Table: `{table_name}`\n")
        
        # Stats
        er_stats = [
            {"Metric": "Matched", "Value": tr.num_matches},
            {"Metric": "Uncertain", "Value": tr.num_uncertain},
            {"Metric": "Non-Matches", "Value": tr.num_non_matches},
            {"Metric": "SN Window Efficiency (Reduction Ratio)", "Value": f"{(1 - len(er_result.candidate_pairs) / (len(er_result.df_a_clean) * len(er_result.df_b_clean))):.2%}" if er_result.candidate_pairs is not None and not er_result.df_a_clean.empty and not er_result.df_b_clean.empty else "N/A"}
        ]
        md_content.append(pd.DataFrame(er_stats).to_markdown(index=False) + "\n")
        
        # Config
        md_content.append("**LLM Configuration:**\n")
        if hasattr(er_result.config, "indexing_keys"):
            md_content.append(f"- **Indexing Keys:** `{', '.join(er_result.config.indexing_keys)}`\n")
            md_content.append(f"- **Indexing Threshold:** {er_result.config.indexing_threshold}\n")
        else:
            md_content.append(f"- **Primary Key:** `{getattr(er_result.config, 'sorting_key', 'N/A')}`\n")
            if getattr(er_result.config, "backup_sorting_key", None):
                md_content.append(f"- **Backup Key:** `{er_result.config.backup_sorting_key}`\n")
            if getattr(er_result.config, "window_size", None):
                md_content.append(f"- **Window Size:** {er_result.config.window_size}\n")
        
        # Matching Columns
        md_content.append("**Matching Columns:**\n")
        mc_data = [
            {"Column": k, "Algorithm": v.algorithm.value, "Weight": v.weight}
            for k, v in er_result.config.matching_columns.items()
        ]
        md_content.append(pd.DataFrame(mc_data).to_markdown(index=False) + "\n")
        
        # Reasoning
        reasoning_html = f"""
<div class="llm-reasoning">
    <div class="llm-reasoning-header">Model Configuration Reasoning</div>
    {render_markdown_to_html(er_result.config.reasoning)}
</div>
"""
        md_content.append(reasoning_html)
        
        # Sample Matches
        if not er_result.matches.empty:
            md_content.append("#### Sample Matches\n")
            # We need to render the DataFrame carefully. 
            # The matches DF usually has multi-index columns or prefixed columns.
            md_content.append(_render_df_sample(er_result.matches, max_rows=5))
            md_content.append("\n")

    full_md = "\n".join(md_content)
    body_html = render_markdown_to_html(full_md)
    
    return build_html_document(f"Pipeline Report - {report.timestamp.strftime('%Y%m%d')}", body_html)
