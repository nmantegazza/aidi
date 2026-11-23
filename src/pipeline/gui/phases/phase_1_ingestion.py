import gradio as gr
from ..components import render_source_overview, render_previews, render_cleaning_report
from pipeline.visualization import generate_mermaid_code
from ..handlers import handle_ingestion
from .canvas import IngestionCanvasState

def render_ingestion_canvas(
    state: IngestionCanvasState,
    canvas_state: gr.State,
    chatbot_history: gr.State,
    current_stage: gr.State,
    ingestion_state: gr.State,
    chatbot: gr.Chatbot
):
    gr.Markdown("## Phase 1 & 2: Data Ingestion & Cleaning")
    
    if not state.ingested:
        gr.Markdown("**Awaiting Data Ingestion**\n\nPlease enter the root directory containing your source data in the Chat Input panel to begin (e.g. `data/test_cases/running_example`).")
    else:
        # Determine showing tabs
        tabs_list = ["Database Schemas", "Data Profile", "Data Preview"]
        if state.cleaned:
            tabs_list.append("Cleaning Report")
            
        with gr.Tabs(elem_id="ingestion-tabs"):
            with gr.TabItem("Database Schemas"):
                with gr.Row(equal_height=False, elem_id="ingestion-schemas-container"):
                    with gr.Column(elem_id="ingestion-schema-source-a"):
                        gr.Markdown("### Source A")
                        if state.ingestion_result and state.ingestion_result.source_a:
                            m_a = f"```mermaid\n{generate_mermaid_code(state.ingestion_result.source_a.package)}\n```"
                            gr.Markdown(m_a)
                        else:
                            gr.Markdown("*Awaiting data ingestion...*")
                            
                    with gr.Column(elem_id="ingestion-schema-source-b"):
                        gr.Markdown("### Source B")
                        if state.ingestion_result and state.ingestion_result.source_b:
                            m_b = f"```mermaid\n{generate_mermaid_code(state.ingestion_result.source_b.package)}\n```"
                            gr.Markdown(m_b)
                        else:
                            gr.Markdown("*Awaiting data ingestion...*")
                
                gr.HTML("<script>setTimeout(() => { if (window.mermaid) { mermaid.initialize({ startOnLoad: false, securityLevel: 'loose', er: { useMaxWidth: true } }); mermaid.run(); } }, 200);</script>", visible=False)
            
            with gr.TabItem("Data Profile", elem_id="ingestion-profile-tab"):
                with gr.Row(equal_height=False):
                    with gr.Column():
                        gr.Markdown("### Source A")
                        profiles_a = state.ingestion_result.profiles_a if state.ingestion_result else None
                        render_source_overview(profiles_a, "Source A")
                        
                    with gr.Column():
                        gr.Markdown("### Source B")
                        profiles_b = state.ingestion_result.profiles_b if state.ingestion_result else None
                        render_source_overview(profiles_b, "Source B")
            
            with gr.TabItem("Data Preview"):
                with gr.Row(equal_height=False):
                    with gr.Column():
                        gr.Markdown("### Source A")
                        src_a = state.ingestion_result.source_a if state.ingestion_result else None
                        render_previews(src_a, "Source A")
                        
                    with gr.Column():
                        gr.Markdown("### Source B")
                        src_b = state.ingestion_result.source_b if state.ingestion_result else None
                        render_previews(src_b, "Source B")
            
            if state.cleaned:
                with gr.TabItem("Cleaning Report"):
                    with gr.Row(equal_height=False):
                        with gr.Column():
                            gr.Markdown("### Source A")
                            reports_a = state.cleaning_result.reports_a if state.cleaning_result else None
                            render_cleaning_report(reports_a, "Source A")
                            
                        with gr.Column():
                            gr.Markdown("### Source B")
                            reports_b = state.cleaning_result.reports_b if state.cleaning_result else None
                            render_cleaning_report(reports_b, "Source B")
