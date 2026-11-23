import pandas as pd
import gradio as gr
from .formatters import (
    prepare_column_stats_df, prepare_column_freq_df,
    prepare_cleaning_stats_df, prepare_cleaning_samples_df
)

def get_loader_html(message="AI is aligning your schemas..."):
    return f"""
    <div class="loader-container">
        <div class="spinner"></div>
        <div class="loader-text">{message}</div>
    </div>
    """

def render_loader(message="AI is aligning your schemas...", visible=True):
    """Returns a styled loading component."""
    return gr.HTML(value=get_loader_html(message), visible=visible)

def render_source_overview(profiles, source_label: str):
    """Renders data overview metrics and table columns profile cards."""
    if not profiles:
        gr.Markdown(f"*Awaiting {source_label} data ingestion...*")
        return
    
    total_rows = sum(p.total_rows for p in profiles.values())
    avg_comp = sum(p.completeness_score for p in profiles.values()) / len(profiles)
    overview_df = pd.DataFrame(
        [[len(profiles), f"{total_rows:,}", f"{avg_comp:.1f}%"]],
        columns=["Tables", "Rows", "Avg Comp"]
    )
    with gr.Group(elem_classes="source-card"):
        gr.Dataframe(overview_df, interactive=False, elem_classes="metric-table")

    source_slug = source_label.lower().replace(" ", "-")
    for table_name, profile in profiles.items():
        label = f"Table: {table_name} ({profile.total_rows:,} rows, {profile.total_columns} cols, {profile.completeness_score:.0f}% complete)"
        with gr.Accordion(label, open=False, elem_id=f"profile-{source_slug}-table-{table_name}"):
            for col_name, p in profile.column_profiles.items():
                with gr.Accordion(f"Column: {col_name} ({p.dtype})", open=False, elem_id=f"profile-{source_slug}-col-{table_name}-{col_name}"):
                    with gr.Column(elem_id=f"profile-{source_slug}-detail-{table_name}-{col_name}"):
                        gr.Dataframe(prepare_column_stats_df(p), interactive=False, elem_classes="metric-table")
                        
                        freq_df = prepare_column_freq_df(p)
                        if freq_df is not None:
                            gr.Markdown("**Top Frequencies**")
                            gr.Dataframe(freq_df, interactive=False, elem_classes="metric-table")

def render_previews(src, source_label: str):
    """Renders tabular data preview accordions."""
    if not src or not src.tables:
        gr.Markdown(f"*Awaiting {source_label} data...*")
        return
    for name, df in src.tables.items():
        with gr.Accordion(f"Table: {name} ({len(df):,} rows)", open=False):
            gr.Dataframe(df.head(50), interactive=False)

def render_cleaning_report(reports, source_label: str):
    """Renders data cleaning statistics and transformation sample accordions."""
    if not reports:
        gr.Markdown(f"*Awaiting {source_label} cleaning...*")
        return
    
    total_trans = sum(r.total_transformations for r in reports.values())
    total_dupes = sum(r.duplicates_removed for r in reports.values())
    overview_df = pd.DataFrame(
        [[len(reports), f"{total_trans:,}", f"{total_dupes:,}"]],
        columns=["Tables", "Transformations", "Dupes Removed"]
    )
    with gr.Group(elem_classes="source-card"):
        gr.Dataframe(overview_df, interactive=False, elem_classes="metric-table")

    for table_name, report in reports.items():
        label = f"Table: {table_name} ({report.total_transformations:,} changes)"
        with gr.Accordion(label, open=False):
            gr.Dataframe(prepare_cleaning_stats_df(report), interactive=False, elem_classes="metric-table")

    samples_df = prepare_cleaning_samples_df(reports)
    if samples_df is not None:
        with gr.Accordion("Transformation Samples (Unified)", open=False):
            gr.Dataframe(samples_df, interactive=False, elem_classes="metric-table")
