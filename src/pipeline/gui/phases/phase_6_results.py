import gradio as gr
from .canvas import ResultsCanvasState

def render_results_canvas(state: ResultsCanvasState):
    gr.Markdown("## Phase 6: Pipeline Execution Results")
    
    if not state.final_report or not state.final_report.report_path:
        gr.Markdown("### Final Report\n*Generating...*")
        return
        
    gr.Markdown(f"### Final Report\nReport generated successfully: `{state.final_report.report_path}`")
    gr.JSON(state.final_report.summary, label="Pipeline Execution Summary", elem_id="results-summary-json")
    gr.DownloadButton("Download HTML Report", value=state.final_report.report_path, variant="primary", elem_id="results-download-report-btn")
