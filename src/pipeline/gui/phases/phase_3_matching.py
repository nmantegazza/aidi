import pandas as pd
import gradio as gr
from pipeline.visualization import generate_mermaid_code
from .canvas import MatchingCanvasState

def render_matching_canvas(state: MatchingCanvasState):
    gr.Markdown("## Phase 3: Schema Integration")
        
    if not state.matching_result or not state.matching_result.integration_report:
        gr.Markdown("*Awaiting schema integration...*")
        return
        
    report = state.matching_result.integration_report
    
    with gr.Tabs(selected="er_diagram", elem_id="matching-tabs"):
        with gr.TabItem("Conflict Resolution Report", id="conflicts", elem_id="matching-conflicts-tab"):
            if not report.conflicts_report:
                gr.Markdown("No conflicts reported.")
            else:
                for idx, group in enumerate(report.conflicts_report):
                    with gr.Accordion(
                        f"{group.conflict_type.value} ({len(group.conflicts)})",
                        open=False,
                        elem_id=f"matching-conflict-accordion-{idx}"
                    ):
                        data = []
                        for c in group.conflicts:
                            data.append([
                                c.description, 
                                c.resolution_strategy, 
                                ", ".join(c.source_items), 
                                ", ".join(c.target_items)
                            ])
                        df = pd.DataFrame(data, columns=["Description", "Resolution", "Source A", "Source B"])
                        gr.Dataframe(
                            df,
                            interactive=False,
                            elem_classes="metric-table",
                            elem_id=f"matching-conflict-df-{idx}"
                        )
                        
        with gr.TabItem("Integrated Schema (ER Diagram)", id="er_diagram", elem_id="matching-er-diagram"):
            if hasattr(report, "global_schema"):
                gr.Markdown(f"```mermaid\n{generate_mermaid_code(report.global_schema)}\n```")
                gr.HTML("<script>setTimeout(() => { if (window.mermaid) { mermaid.initialize({ startOnLoad: false, securityLevel: 'loose', er: { useMaxWidth: true } }); mermaid.run(); } }, 200);</script>", visible=False)
            else:
                gr.Markdown("*Failed to generate ER Diagram*")
