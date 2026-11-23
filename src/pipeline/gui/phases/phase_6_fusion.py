import gradio as gr
import pandas as pd
from .canvas import DataFusionConfigCanvasState, DataFusionResultCanvasState
from data_fusion.models import FusionStrategy, MultiTableFusionPolicy

def _make_strategy_mutator(policy: MultiTableFusionPolicy, tname: str, col_name: str):
    def mutate(new_value: str):
        # Mutate the policy object in place
        for cp in policy.tables[tname].column_policies:
            if cp.column_name == col_name:
                cp.strategy = FusionStrategy(new_value)
                break
    return mutate

def render_fusion_config_canvas(state: DataFusionConfigCanvasState):
    gr.Markdown("## Phase 6: Data Fusion — Policy Review")
    
    if not state.config_result or not state.config_result.fusion_profile or not state.config_result.fusion_policy:
        gr.Markdown("*Generating fusion policy...*")
        return
        
    sorted_tables = sorted(state.config_result.fusion_profile.tables.items())
    
    for table_name, table_profile in sorted_tables:
        with gr.Accordion(label=f"Table: {table_name}", open=True):
            # 1. Conflict Profile Accordion (collapsed by default)
            with gr.Accordion(label="Conflict Profile Summary", open=False):
                profile_rows = []
                for col_name, col_prof in sorted(table_profile.columns.items()):
                    conflict_pct = f"{col_prof.conflict_rate * 100:.1f}%"
                    null_a_pct = f"{col_prof.source_a_null_rate * 100:.1f}%"
                    null_b_pct = f"{col_prof.source_b_null_rate * 100:.1f}%"
                    trust_score = f"{col_prof.source_trust_score:.3f}"
                    profile_rows.append({
                        "Column": col_name,
                        "Physical Type": col_prof.physical_type.value,
                        "Semantic Type": col_prof.semantic_type.value,
                        "Conflict %": conflict_pct,
                        "A Null %": null_a_pct,
                        "B Null %": null_b_pct,
                        "Trust Score": trust_score
                    })
                
                df_profile = pd.DataFrame(
                    profile_rows,
                    columns=["Column", "Physical Type", "Semantic Type", "Conflict %", "A Null %", "B Null %", "Trust Score"]
                )
                gr.DataFrame(value=df_profile, interactive=False)
                
            # 2. Column Policies
            policy_container_id = "fusion-policies-container" if table_name == "organizations" else f"fusion-policies-container-{table_name}"
            with gr.Column(elem_id=policy_container_id):
                gr.Markdown("#### Column Policies")
                table_policy = state.config_result.fusion_policy.tables[table_name]
                if not table_policy.column_policies:
                    gr.Markdown("*No linked entity pairs found for this table. Records will be preserved directly without conflict resolution.*")

                for col_policy in table_policy.column_policies:
                    col_name = col_policy.column_name
                    with gr.Row():
                        with gr.Column(scale=2):
                            gr.Markdown(f"**{col_name}**")
                        
                        with gr.Column(scale=3):
                            strategy_dd = gr.Dropdown(
                                choices=[s.value for s in FusionStrategy],
                                value=col_policy.strategy.value,
                                label="Strategy",
                                elem_id=f"fusion_strategy_{table_name}_{col_name}"
                            )
                        
                        with gr.Column(scale=2):
                            with gr.Accordion(label="Reasoning", open=False):
                                gr.Markdown(col_policy.reasoning)
                    
                    strategy_dd.change(
                        fn=_make_strategy_mutator(state.config_result.fusion_policy, table_name, col_name),
                        inputs=[strategy_dd],
                        outputs=[]
                    )

def render_fusion_result_canvas(state: DataFusionResultCanvasState):
    gr.Markdown("## Phase 6: Data Fusion — Golden Records")
    
    if not state.fusion_result or not state.fusion_result.fused_tables:
        gr.Markdown("*Executing fusion...*")
        return
        
    sorted_tables = sorted(state.fusion_result.fused_tables.items())
    
    for table_name, df in sorted_tables:
        row_count = len(df)
        with gr.Accordion(label=f"Table: {table_name} ({row_count:,} rows)", open=True):
            policy_summary = []
            table_policy = state.fusion_result.fusion_policy.tables.get(table_name)
            if table_policy:
                for cp in table_policy.column_policies:
                    policy_summary.append(f"{cp.column_name} → {cp.strategy.value}")
                policy_text = " | ".join(policy_summary)
            else:
                policy_text = "*(No conflict resolution applied — all rows are unlinked)*"
                
            gr.Markdown(f"**Applied Policy**: {policy_text}")
            
            golden_df_id = "fusion-golden-records-df" if table_name == "organizations" else f"fusion-golden-records-df-{table_name}"
            gr.DataFrame(
                value=df.head(50),
                label=f"Golden Records (showing first 50 of {row_count:,} rows)",
                interactive=False,
                elem_id=golden_df_id
            )
