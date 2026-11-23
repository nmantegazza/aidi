import pandas as pd
import gradio as gr
from shared.porting.visualization import format_column_transformations, format_construction_recipe
from .canvas import PortingCanvasState

def render_porting_canvas(state: PortingCanvasState):
    gr.Markdown("## Phase 4: Data Porting")
    
    if not state.porting_result or not state.porting_result.ported_tables:
        gr.Markdown("*Awaiting data porting...*")
        return
        
    ported_tables = state.porting_result.ported_tables
    porting_instructions = state.porting_result.porting_instructions
    
    clean_a = state.cleaning_result.clean_a if state.cleaning_result else None
    clean_b = state.cleaning_result.clean_b if state.cleaning_result else None
    
    source_a_label = clean_a.package.name if clean_a else "source_a"
    source_b_label = clean_b.package.name if clean_b else "source_b"
    
    with gr.Column(elem_id="porting-recipes-container"):
        for table_name, ported_table in ported_tables.items():
            with gr.Accordion(f"Ported Table: {table_name}", open=False, elem_id=f"porting-table-accordion-{table_name}"):
                with gr.Column(elem_id=f"porting-recipes-{table_name}"):
                    if porting_instructions:
                        instructions = porting_instructions.global_table_instructions.get(table_name)
                        if instructions:
                            gr.Markdown("### Construction Strategy & Recipes")
                            for recipe in instructions.construction_recipes:
                                gr.Markdown(f"- {format_construction_recipe(recipe)}")
                        
                        gr.Markdown("### Schema Alignments & Field Transformations")
                        trans_data = []
                        for col_name, trans_list in instructions.field_transformations.items():
                            trans_data.append([
                                col_name,
                                format_column_transformations(trans_list, source_a_label),
                                format_column_transformations(trans_list, source_b_label)
                            ])
                        
                        trans_df = pd.DataFrame(trans_data, columns=["Global Column", f"{source_a_label} Mapping", f"{source_b_label} Mapping"])
                        gr.Dataframe(trans_df, interactive=False, elem_classes="metric-table")
                    
            gr.Markdown("### Preview of Ported Data")
            with gr.Row(equal_height=False):
                with gr.Column():
                    gr.Markdown(f"**Source A Data (Ported) ({len(ported_table.df_a)} rows)**")
                    gr.Dataframe(ported_table.df_a.head(30), interactive=False)
                with gr.Column():
                    gr.Markdown(f"**Source B Data (Ported) ({len(ported_table.df_b)} rows)**")
                    gr.Dataframe(ported_table.df_b.head(30), interactive=False)
