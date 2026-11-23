import gradio as gr
import pandas as pd

from entity_resolution.models import EntityResolutionResult, SimilarityAlgorithm

from ..handlers import handle_llm_refinement
from .canvas import ERConfigCanvasState, ERReviewCanvasState


def get_bucket_len(result: EntityResolutionResult, category: str) -> int:
    if category == "uncertain":
        df_bucket = result.uncertain
    elif category == "matches":
        df_bucket = result.matches
    elif category == "non_matches":
        df_bucket = result.non_matches
    else:
        df_bucket = None
    return len(df_bucket) if df_bucket is not None else 0

def load_pair_at(res_obj: EntityResolutionResult, category: str, pair_idx: int):
    # Determine the bucket
    if category == "uncertain":
        df_bucket = res_obj.uncertain
    elif category == "matches":
        df_bucket = res_obj.matches
    elif category == "non_matches":
        df_bucket = res_obj.non_matches
    else:
        df_bucket = None

    N = len(df_bucket) if df_bucket is not None else 0

    # Default/empty return values
    comp_df = pd.DataFrame(columns=["Field", "Record A", "Record B"])
    pair_header_md = ""
    pair_label = "Pair 0 of 0"
    pair_id = None
    llm_visible = False
    llm_md = ""
    accept_btn_visible = False
    match_btn_vis = False
    uncertain_btn_vis = False
    non_match_btn_vis = False
    first_ia = prev_ia = next_ia = last_ia = False

    if df_bucket is not None and N > 0:
        # Sort and slice
        if "aggregate_score" in df_bucket.columns:
            df_bucket_sorted = df_bucket.sort_values(by="aggregate_score", ascending=False, kind="stable")
        else:
            df_bucket_sorted = df_bucket
        
        # Safe out-of-range clamp / check
        if 0 <= pair_idx < N:
            pair = df_bucket_sorted.index[pair_idx]
            id_a, id_b = pair
            pair_id = (str(id_a), str(id_b))
            
            # Build comp_df
            row_a = res_obj.df_a_clean.loc[id_a] if id_a in res_obj.df_a_clean.index else {}
            row_b = res_obj.df_b_clean.loc[id_b] if id_b in res_obj.df_b_clean.index else {}
            
            cols_a = list(res_obj.df_a_clean.columns)
            cols_b = list(res_obj.df_b_clean.columns)
            all_cols = sorted(list(set(cols_a) | set(cols_b)))
            
            comp_rows = []
            for col in all_cols:
                val_a = row_a.get(col, "") if not isinstance(row_a, dict) else row_a.get(col, "")
                val_b = row_b.get(col, "") if not isinstance(row_b, dict) else row_b.get(col, "")
                
                str_a = str(val_a)
                str_b = str(val_b)
                
                col_display = col
                if str_a.strip().lower() != str_b.strip().lower():
                    col_display = f"{col}"
                    
                comp_rows.append({
                    "Field": col_display,
                    "Record A": str_a,
                    "Record B": str_b
                })
            comp_df = pd.DataFrame(comp_rows, columns=["Field", "Record A", "Record B"])

            # Build pair_header_md
            score = df_bucket_sorted.loc[pair, "aggregate_score"] if "aggregate_score" in df_bucket_sorted.columns else 0.0
            pair_header_md = f"**Score**: {score:.4f} · **Pair**: {pair_idx + 1} of {N}"
            pair_label = f"Pair {pair_idx + 1} of {N}"

            # Extract LLM data
            if category == "uncertain" and "llm_decision" in df_bucket_sorted.columns:
                df_row = df_bucket_sorted.loc[pair]
                decision = df_row["llm_decision"]
                reasoning = df_row["llm_reasoning"]
                
                if not pd.isna(decision):
                    llm_visible = True
                    accept_btn_visible = True
                    suggestion_str = "Match" if bool(decision) else "Non-Match"
                    llm_md = (
                        f"**Suggestion**: {suggestion_str}\n\n"
                        f"**Reasoning**: {reasoning}"
                    )

            # Button states depending on the active category
            match_btn_vis = (category != "matches")
            uncertain_btn_vis = (category != "uncertain")
            non_match_btn_vis = (category != "non_matches")

            # Navigation interactive states
            first_ia = prev_ia = (pair_idx > 0)
            next_ia = last_ia = (pair_idx < N - 1)

    return (
        comp_df,
        pair_header_md,
        pair_label,
        pair_id,
        llm_visible,
        llm_md,
        accept_btn_visible,
        match_btn_vis,
        uncertain_btn_vis,
        non_match_btn_vis,
        first_ia,
        prev_ia,
        next_ia,
        last_ia
    )



def render_er_config_canvas(
    state: ERConfigCanvasState
):
    gr.Markdown("## Phase 5: Entity Resolution Configuration")
    
    if not state.er_configs:
        gr.Markdown("*Awaiting configuration proposal...*")
        return
        
    table_inputs = {}
    
    with gr.Column(elem_id="er-config-container"):
        for table_name, er_cfg in state.er_configs.items():
            with gr.Accordion(f"Table: {table_name}", open=True, elem_id=f"er-config-table-{table_name}"):
                # Indexing keys choices from global columns
                cols = []
                if state.porting_result and table_name in state.porting_result.ported_tables:
                    cols = list(state.porting_result.ported_tables[table_name].df_a.columns)
                
                with gr.Row():
                    keys_dropdown = gr.Dropdown(
                        choices=cols,
                        value=er_cfg.indexing_keys,
                        multiselect=True,
                        label="TF-IDF Indexing Keys",
                        interactive=True,
                        elem_id=f"er-config-keys-{table_name}"
                    )
                    threshold_slider = gr.Slider(
                        minimum=0.01,
                        maximum=0.50,
                        step=0.01,
                        value=er_cfg.indexing_threshold,
                        label="Candidate Indexing Cosine Threshold",
                        interactive=True,
                        elem_id=f"er-config-threshold-{table_name}"
                    )
                    
                    def update_keys(val, t=table_name):
                        state.er_configs[t].indexing_keys = val if isinstance(val, list) else [val]
                    keys_dropdown.change(fn=update_keys, inputs=[keys_dropdown])

                    def update_thresh(val, t=table_name):
                        state.er_configs[t].indexing_threshold = float(val)
                    threshold_slider.change(fn=update_thresh, inputs=[threshold_slider])
                    
                gr.Markdown("### Per Column Configuration")
                cols_inputs = {}
                algo_choices = [a.value for a in SimilarityAlgorithm]
                
                for col, cfg in er_cfg.matching_columns.items():
                    gr.Markdown(f"**{col}**")
                    with gr.Row():
                        algo_dropdown = gr.Dropdown(
                            choices=algo_choices,
                            value=cfg.algorithm.value,
                            label="Algorithm",
                            interactive=True,
                            elem_id=f"er-config-algo-{table_name}-{col}"
                        )
                        weight_slider = gr.Slider(
                            minimum=0.0,
                            maximum=1.0,
                            step=0.05,
                            value=cfg.weight,
                            label="Weight",
                            interactive=True,
                            elem_id=f"er-config-weight-{table_name}-{col}"
                        )
                        
                        def update_algo(val, t=table_name, c=col):
                            state.er_configs[t].matching_columns[c].algorithm = SimilarityAlgorithm(val)
                        algo_dropdown.change(fn=update_algo, inputs=[algo_dropdown])

                        def update_weight(val, t=table_name, c=col):
                            state.er_configs[t].matching_columns[c].weight = float(val)
                        weight_slider.change(fn=update_weight, inputs=[weight_slider])
                        
                    cols_inputs[col] = {
                        "algorithm": algo_dropdown,
                        "weight": weight_slider
                    }
                
                reasoning_elem_id = "er-config-reasoning-accordion" if table_name == "organizations" else f"er-config-reasoning-accordion-{table_name}"
                with gr.Accordion("View LLM Configuration Reasoning", open=False, elem_id=reasoning_elem_id):
                    reasoning_component = gr.Textbox(
                        value=er_cfg.reasoning,
                        show_label=False,
                        lines=3,
                        interactive=False,
                        elem_id=f"er-config-reasoning-box-{table_name}"
                    )
                
                table_inputs[table_name] = {
                    "indexing_keys": keys_dropdown,
                    "indexing_threshold": threshold_slider,
                    "cols": cols_inputs,
                    "reasoning": reasoning_component
                }

def render_er_review_canvas(
    state: ERReviewCanvasState,
    canvas_state: gr.State,
    chatbot_history: gr.State,
    linkage_state: gr.State,
    chatbot: gr.Chatbot,
    model_dropdown: gr.Dropdown
):
    gr.Markdown("## Phase 5: Entity Resolution Uncertain Review")
    gr.Markdown("Review the candidate record pairs that were flagged as uncertain matches. Adjust their decision and confirm.")
    
    if not state.linkage_result or not state.linkage_result.er_results:
        gr.Markdown("*Awaiting record linkage results...*")
        return
        
    for table_name, result in state.linkage_result.er_results.items():
        with gr.Accordion(f"Table: {table_name}", open=True):
            # States for active view and selected pair
            active_view = gr.State(value=None)
            selected_pair_state = gr.State(value=None)
            pair_index_state = gr.State(value=0)
            
            # Metrics Card Calculation
            total_cand = len(result.candidate_pairs) if result.candidate_pairs is not None else 0
            len_a = len(result.df_a_clean) if result.df_a_clean is not None else 0
            len_b = len(result.df_b_clean) if result.df_b_clean is not None else 0
            max_pairs = len_a * len_b if len_a > 0 and len_b > 0 else 1
            1 - (total_cand / max_pairs) if result.candidate_pairs is not None else 0.0
            
            # Three column metrics cards with count & CTA buttons
            with gr.Row(elem_id=f"er-metrics-row-{table_name}") as metrics_row:
                with gr.Column(variant="panel", scale=1, min_width=150):
                    gr.Markdown("### Matches")
                    match_count = gr.Label(value=str(len(result.matches)), show_label=False)
                    inspect_matches_btn = gr.Button(
                        "Inspect Matches",
                        variant="primary",
                        elem_id="er-inspect-matches-btn" if table_name == "organizations" else f"er-inspect-matches-btn-{table_name}"
                    )
                    
                with gr.Column(variant="panel", scale=1, min_width=150):
                    gr.Markdown("### Uncertain")
                    uncertain_count = gr.Label(value=str(len(result.uncertain)), show_label=False)
                    review_uncertain_btn = gr.Button(
                        "Review Uncertain",
                        variant="primary",
                        elem_id="er-review-uncertain-btn" if table_name == "organizations" else f"er-review-uncertain-btn-{table_name}"
                    )
                    
                with gr.Column(variant="panel", scale=1, min_width=150):
                    gr.Markdown("### Non-Matches")
                    non_match_count = gr.Label(value=str(len(result.non_matches)), show_label=False)
                    inspect_non_matches_btn = gr.Button(
                        "Inspect Non-Matches",
                        variant="primary",
                        elem_id="er-inspect-non-matches-btn" if table_name == "organizations" else f"er-inspect-non-matches-btn-{table_name}"
                    )
            
            # Drill-down view container (always visible, child component visibility is controlled instead to prevent Gradio container re-render discard bugs)
            with gr.Column(visible=True):
                back_btn = gr.Button(
                    "← Back to Metrics",
                    size="sm",
                    variant="secondary",
                    visible=False,
                    elem_id="er-back-to-metrics-btn" if table_name == "organizations" else f"er-back-to-metrics-btn-{table_name}"
                )
                
                # Add action buttons row above the data grid
                with gr.Row(visible=False) as batch_action_row:
                    batch_refine_btn = gr.Button(
                        "Batch Refine with LLM",
                        variant="secondary",
                        visible=False,
                        elem_id="er-batch-refine-btn" if table_name == "organizations" else f"er-batch-refine-btn-{table_name}"
                    )
                    accept_all_llm_btn = gr.Button(
                        "Accept All LLM Suggestions",
                        variant="primary",
                        visible=False,
                        elem_id="er-accept-all-llm-btn" if table_name == "organizations" else f"er-accept-all-llm-btn-{table_name}"
                    )
                
                view_title = gr.Markdown("### Inspecting", visible=False)
                
                # Pair-by-pair navigation UI controls
                with gr.Row(visible=False) as pair_nav_row:
                    first_btn = gr.Button("« First", interactive=False, min_width=60, size="sm")
                    prev_btn = gr.Button("‹ Prev", interactive=False, min_width=60, size="sm")
                    pair_label = gr.Markdown("Pair 1 of 1")
                    next_btn = gr.Button("Next ›", interactive=False, min_width=60, size="sm")
                    last_btn = gr.Button("Last »", interactive=False, min_width=60, size="sm")
                
                pair_header = gr.Markdown("", visible=False)
                
                # Empty state view shown when the bucket is empty
                with gr.Column(visible=False) as empty_state:
                    gr.Markdown("### All pairs reviewed\n\nThis bucket is empty.")
                
                # Detail comparison workspace (always visible, child component visibility is controlled instead)
                with gr.Column(visible=True):
                    comparison_title = gr.Markdown("### Record Pair Side-by-Side Comparison", visible=False)
                    
                    comparison_df_component = gr.Dataframe(
                        headers=["Field", "Record A", "Record B"],
                        interactive=False,
                        elem_classes="metric-table",
                        visible=False,
                        elem_id="er-pair-comparison-table" if table_name == "organizations" else f"er-pair-comparison-table-{table_name}"
                    )
                    
                    # LLM Insight panel
                    with gr.Column(
                        visible=False,
                        elem_id="er-llm-reasoning-box" if table_name == "organizations" else f"er-llm-reasoning-box-{table_name}"
                    ) as llm_insight_panel:
                        gr.Markdown("#### LLM Insight")
                        llm_insight_text = gr.Markdown("")
                        
                    # Accept LLM suggestion button (hidden until uncertain pair with LLM data selected)
                    accept_llm_btn = gr.Button(
                        "Accept LLM Suggestion",
                        variant="primary",
                        visible=False,
                        elem_id="er-accept-llm-btn" if table_name == "organizations" else f"er-accept-llm-btn-{table_name}"
                    )
                    
                    reclassify_title = gr.Markdown("#### Reclassify this pair:", visible=False)
                    with gr.Row():
                        match_btn = gr.Button("Mark as Match", variant="primary", visible=False)
                        uncertain_btn = gr.Button("Move to Uncertain", variant="secondary", visible=False)
                        non_match_btn = gr.Button("Mark as Non-Match", variant="stop", visible=False)
            
            # --- 2.1 View Selection Click Callbacks ---
            # Merged prep + load into a single handler.
            # Previously two chained .click().then() calls caused Gradio to re-render
            # the drill_down_container children from their static defaults (visible=False)
            # when the container itself changed visibility, discarding the .then() updates.
            def make_view_handler(tname, target_view):
                def handle_view():
                    title_map = {
                        "matches": "### Inspecting: Matches",
                        "uncertain": "### Reviewing: Uncertain",
                        "non_matches": "### Inspecting: Non-Matches"
                    }
                    res_obj = state.linkage_result.er_results[tname]
                    has_llm = (
                        res_obj.uncertain is not None
                        and "llm_decision" in res_obj.uncertain.columns
                    )
                    N = get_bucket_len(res_obj, target_view)
                    show_empty = (N == 0)
                    show_workspace = (N > 0)

                    (
                        comp_df,
                        pair_header_md,
                        pair_label_val,
                        pair_id,
                        llm_visible,
                        llm_md,
                        accept_btn_visible,
                        match_btn_vis,
                        uncertain_btn_vis,
                        non_match_btn_vis,
                        first_ia,
                        prev_ia,
                        next_ia,
                        last_ia
                    ) = load_pair_at(res_obj, target_view, 0)

                    return (
                        target_view,                           # active_view
                        pair_id,                               # selected_pair_state
                        0,                                     # pair_index_state
                        gr.update(visible=False),              # metrics_row
                        gr.update(visible=True),               # back_btn
                        gr.update(value=title_map.get(target_view, "### Inspecting"), visible=True),  # view_title
                        gr.update(visible=show_workspace),     # comparison_title
                        gr.update(visible=show_workspace),     # reclassify_title
                        gr.update(interactive=first_ia),       # first_btn
                        gr.update(interactive=prev_ia),        # prev_btn
                        pair_label_val,                        # pair_label
                        gr.update(interactive=next_ia),        # next_btn
                        gr.update(interactive=last_ia),        # last_btn
                        gr.update(visible=(target_view == "uncertain")),                     # batch_action_row
                        gr.update(visible=(target_view == "uncertain" and not has_llm)),     # batch_refine_btn
                        gr.update(visible=(target_view == "uncertain" and has_llm)),         # accept_all_llm_btn
                        gr.update(visible=match_btn_vis),      # match_btn
                        gr.update(visible=uncertain_btn_vis),  # uncertain_btn
                        gr.update(visible=non_match_btn_vis),  # non_match_btn
                        gr.update(visible=llm_visible),        # llm_insight_panel
                        llm_md,                                # llm_insight_text
                        gr.update(visible=accept_btn_visible), # accept_llm_btn
                        gr.update(visible=show_empty),         # empty_state
                        gr.update(value=pair_header_md, visible=show_workspace), # pair_header
                        gr.update(value=comp_df, visible=show_workspace), # comparison_df_component
                        gr.update(visible=show_workspace),     # pair_nav_row
                    )
                return handle_view

            _VIEW_OUTPUTS = [
                active_view,
                selected_pair_state,
                pair_index_state,
                metrics_row,
                back_btn,
                view_title,
                comparison_title,
                reclassify_title,
                first_btn,
                prev_btn,
                pair_label,
                next_btn,
                last_btn,
                batch_action_row,
                batch_refine_btn,
                accept_all_llm_btn,
                match_btn,
                uncertain_btn,
                non_match_btn,
                llm_insight_panel,
                llm_insight_text,
                accept_llm_btn,
                empty_state,
                pair_header,
                comparison_df_component,
                pair_nav_row,
            ]

            back_btn.click(
                fn=lambda: (
                    gr.update(visible=True),   # metrics_row
                    gr.update(visible=False),  # back_btn
                    gr.update(visible=False),  # view_title
                    gr.update(visible=False),  # pair_nav_row
                    gr.update(visible=False),  # pair_header
                    gr.update(visible=False),  # comparison_title
                    gr.update(visible=False),  # reclassify_title
                    gr.update(visible=False),  # empty_state
                    gr.update(visible=False),  # batch_action_row
                    gr.update(visible=False),  # comparison_df_component
                    gr.update(visible=False),  # llm_insight_panel
                    gr.update(visible=False),  # accept_llm_btn
                    gr.update(visible=False),  # match_btn
                    gr.update(visible=False),  # uncertain_btn
                    gr.update(visible=False),  # non_match_btn
                ),
                inputs=[],
                outputs=[
                    metrics_row,
                    back_btn,
                    view_title,
                    pair_nav_row,
                    pair_header,
                    comparison_title,
                    reclassify_title,
                    empty_state,
                    batch_action_row,
                    comparison_df_component,
                    llm_insight_panel,
                    accept_llm_btn,
                    match_btn,
                    uncertain_btn,
                    non_match_btn
                ],
                show_progress="hidden",
            )

            inspect_matches_btn.click(
                fn=make_view_handler(table_name, "matches"),
                inputs=[],
                outputs=_VIEW_OUTPUTS,
                show_progress="hidden",
            )
            review_uncertain_btn.click(
                fn=make_view_handler(table_name, "uncertain"),
                inputs=[],
                outputs=_VIEW_OUTPUTS,
                show_progress="hidden",
            )
            inspect_non_matches_btn.click(
                fn=make_view_handler(table_name, "non_matches"),
                inputs=[],
                outputs=_VIEW_OUTPUTS,
                show_progress="hidden",
            )
            
            # --- First/Prev/Next/Last Click Callbacks ---
            def make_pair_navigator(tname, direction):
                def navigate_pair(current_pair_idx, active_view_val):
                    res_obj = state.linkage_result.er_results[tname]
                    N = get_bucket_len(res_obj, active_view_val)
                    
                    if N == 0 or direction == "first":
                        new_idx = 0
                    elif direction == "last":
                        new_idx = N - 1
                    elif direction == "next":
                        new_idx = current_pair_idx + 1
                    else:
                        new_idx = current_pair_idx - 1
                        
                    # Clamp index
                    new_idx = max(0, min(new_idx, N - 1))
                    
                    (
                        comp_df,
                        pair_header_md,
                        pair_label_val,
                        pair_id,
                        llm_visible,
                        llm_md,
                        accept_btn_visible,
                        match_btn_vis,
                        uncertain_btn_vis,
                        non_match_btn_vis,
                        first_ia,
                        prev_ia,
                        next_ia,
                        last_ia
                    ) = load_pair_at(res_obj, active_view_val, new_idx)
                    
                    return (
                        new_idx,
                        comp_df,
                        pair_header_md,
                        pair_label_val,
                        pair_id,
                        gr.update(visible=llm_visible),
                        llm_md,
                        gr.update(visible=accept_btn_visible),
                        gr.update(visible=match_btn_vis),
                        gr.update(visible=uncertain_btn_vis),
                        gr.update(visible=non_match_btn_vis),
                        gr.update(interactive=first_ia),
                        gr.update(interactive=prev_ia),
                        gr.update(interactive=next_ia),
                        gr.update(interactive=last_ia)
                    )
                return navigate_pair
                
            first_btn.click(
                fn=make_pair_navigator(table_name, "first"),
                inputs=[pair_index_state, active_view],
                outputs=[
                    pair_index_state,
                    comparison_df_component,
                    pair_header,
                    pair_label,
                    selected_pair_state,
                    llm_insight_panel,
                    llm_insight_text,
                    accept_llm_btn,
                    match_btn,
                    uncertain_btn,
                    non_match_btn,
                    first_btn,
                    prev_btn,
                    next_btn,
                    last_btn
                ],
                show_progress="hidden",
            )
            prev_btn.click(
                fn=make_pair_navigator(table_name, "prev"),
                inputs=[pair_index_state, active_view],
                outputs=[
                    pair_index_state,
                    comparison_df_component,
                    pair_header,
                    pair_label,
                    selected_pair_state,
                    llm_insight_panel,
                    llm_insight_text,
                    accept_llm_btn,
                    match_btn,
                    uncertain_btn,
                    non_match_btn,
                    first_btn,
                    prev_btn,
                    next_btn,
                    last_btn
                ],
                show_progress="hidden",
            )
            next_btn.click(
                fn=make_pair_navigator(table_name, "next"),
                inputs=[pair_index_state, active_view],
                outputs=[
                    pair_index_state,
                    comparison_df_component,
                    pair_header,
                    pair_label,
                    selected_pair_state,
                    llm_insight_panel,
                    llm_insight_text,
                    accept_llm_btn,
                    match_btn,
                    uncertain_btn,
                    non_match_btn,
                    first_btn,
                    prev_btn,
                    next_btn,
                    last_btn
                ],
                show_progress="hidden",
            )
            last_btn.click(
                fn=make_pair_navigator(table_name, "last"),
                inputs=[pair_index_state, active_view],
                outputs=[
                    pair_index_state,
                    comparison_df_component,
                    pair_header,
                    pair_label,
                    selected_pair_state,
                    llm_insight_panel,
                    llm_insight_text,
                    accept_llm_btn,
                    match_btn,
                    uncertain_btn,
                    non_match_btn,
                    first_btn,
                    prev_btn,
                    next_btn,
                    last_btn
                ],
                show_progress="hidden",
            )
            
            # --- 2.3 Workspace Action Click Callbacks ---
            def make_action_handler(tname, target_bucket):
                def handle_action(selected_pair, active_view_val, pair_idx_val, history):
                    # 26 outputs (includes comparison_title + reclassify_title + pair_nav_row to avoid stale visibility)
                    _no_op = (
                        gr.update(), gr.update(), gr.update(),           # match_count, uncertain_count, non_match_count
                        history, history, pair_idx_val,                  # chatbot_history, chatbot, pair_index_state
                        gr.update(),                                     # empty_state
                        gr.update(), gr.update(),                        # comparison_title, reclassify_title
                        gr.update(), gr.update(), gr.update(), None,     # comparison_df_component, pair_header, pair_label, selected_pair_state
                        gr.update(), gr.update(), gr.update(),           # llm_insight_panel, llm_insight_text, accept_llm_btn
                        gr.update(), gr.update(), gr.update(),           # match_btn, uncertain_btn, non_match_btn
                        gr.update(), gr.update(), gr.update(), gr.update(), # first_btn, prev_btn, next_btn, last_btn
                        gr.update(), gr.update(),                        # batch_refine_btn, accept_all_llm_btn
                        gr.update()                                      # pair_nav_row
                    )
                    if selected_pair is None:
                        return _no_op

                    res_obj = state.linkage_result.er_results[tname]

                    idx_a_type = type(res_obj.df_a_clean.index[0]) if not res_obj.df_a_clean.empty else str
                    idx_b_type = type(res_obj.df_b_clean.index[0]) if not res_obj.df_b_clean.empty else str

                    try:
                        id_a = idx_a_type(selected_pair[0])
                    except Exception:
                        id_a = selected_pair[0]

                    try:
                        id_b = idx_b_type(selected_pair[1])
                    except Exception:
                        id_b = selected_pair[1]

                    pair = (id_a, id_b)

                    # Move pair across buckets
                    source_name = None
                    source_df = None
                    for name, df in [("matches", res_obj.matches), ("uncertain", res_obj.uncertain), ("non_matches", res_obj.non_matches)]:
                        if df is not None and pair in df.index:
                            source_df = df
                            source_name = name
                            break

                    if source_name and source_name != target_bucket:
                        row = source_df.loc[[pair]]

                        # Remove from source
                        if source_name == "matches":
                            res_obj.matches = res_obj.matches.drop(index=[pair])
                        elif source_name == "uncertain":
                            res_obj.uncertain = res_obj.uncertain.drop(index=[pair])
                        elif source_name == "non_matches":
                            res_obj.non_matches = res_obj.non_matches.drop(index=[pair])

                        # Add to target
                        if target_bucket == "matches":
                            res_obj.matches = pd.concat([res_obj.matches, row])
                        elif target_bucket == "uncertain":
                            res_obj.uncertain = pd.concat([res_obj.uncertain, row])
                        elif target_bucket == "non_matches":
                            res_obj.non_matches = pd.concat([res_obj.non_matches, row])

                    log_msg = f"**System**: Pair `{selected_pair[0]} - {selected_pair[1]}` moved to **{target_bucket.title()}** in table *{tname}*."

                    new_hist = history + [{
                        "role": "assistant",
                        "content": f"{log_msg}\n\nIf you have finished reviewing, you can click below to run Data Fusion:",
                        "options": [{"label": "Run Data Fusion", "value": "run_fusion"}]
                    }]

                    # Recompute batch-action button visibility for the current view
                    has_llm = (
                        res_obj.uncertain is not None
                        and "llm_decision" in res_obj.uncertain.columns
                    )
                    is_uncertain_view = (active_view_val == "uncertain")
                    batch_refine_vis = is_uncertain_view and not has_llm
                    accept_all_vis = is_uncertain_view and has_llm

                    new_N = get_bucket_len(res_obj, active_view_val)
                    if new_N == 0:
                        empty_visible = True
                        workspace_visible = False
                        new_idx = 0

                        comp_df = pd.DataFrame(columns=["Field", "Record A", "Record B"])
                        pair_header_md = ""
                        pair_label_val = "Pair 0 of 0"
                        pair_id = None
                        llm_visible = False
                        llm_md = ""
                        accept_btn_visible = False
                        match_btn_vis = False
                        uncertain_btn_vis = False
                        non_match_btn_vis = False
                        first_ia = prev_ia = next_ia = last_ia = False
                    else:
                        empty_visible = False
                        workspace_visible = True
                        new_idx = min(pair_idx_val, new_N - 1)
                        (
                            comp_df,
                            pair_header_md,
                            pair_label_val,
                            pair_id,
                            llm_visible,
                            llm_md,
                            accept_btn_visible,
                            match_btn_vis,
                            uncertain_btn_vis,
                            non_match_btn_vis,
                            first_ia,
                            prev_ia,
                            next_ia,
                            last_ia
                        ) = load_pair_at(res_obj, active_view_val, new_idx)

                    return (
                        gr.update(value=str(len(res_obj.matches))),     # 1 (match_count)
                        gr.update(value=str(len(res_obj.uncertain))),   # 2 (uncertain_count)
                        gr.update(value=str(len(res_obj.non_matches))), # 3 (non_match_count)
                        new_hist,                                       # 4 (chatbot_history)
                        new_hist,                                       # 5 (chatbot)
                        new_idx,                                        # 6 (pair_index_state)
                        gr.update(visible=empty_visible),               # 7 (empty_state)
                        gr.update(visible=workspace_visible),           # 8 (comparison_title)
                        gr.update(visible=workspace_visible),           # 9 (reclassify_title)
                        gr.update(value=comp_df, visible=workspace_visible), # 10 (comparison_df_component)
                        pair_header_md,                                 # 11 (pair_header)
                        pair_label_val,                                 # 12 (pair_label)
                        pair_id,                                        # 13 (selected_pair_state)
                        gr.update(visible=llm_visible),                 # 14 (llm_insight_panel)
                        llm_md,                                         # 15 (llm_insight_text)
                        gr.update(visible=accept_btn_visible),          # 16 (accept_llm_btn)
                        gr.update(visible=match_btn_vis),               # 17 (match_btn)
                        gr.update(visible=uncertain_btn_vis),           # 18 (uncertain_btn)
                        gr.update(visible=non_match_btn_vis),           # 19 (non_match_btn)
                        gr.update(interactive=first_ia),                # 20 (first_btn)
                        gr.update(interactive=prev_ia),                 # 21 (prev_btn)
                        gr.update(interactive=next_ia),                 # 22 (next_btn)
                        gr.update(interactive=last_ia),                 # 23 (last_btn)
                        gr.update(visible=batch_refine_vis),            # 24 (batch_refine_btn)
                        gr.update(visible=accept_all_vis),              # 25 (accept_all_llm_btn)
                        gr.update(visible=workspace_visible),           # 26 (pair_nav_row)
                    )
            _REFINE_OUTPUTS = [
                chatbot_history,
                chatbot,
                uncertain_count,
                batch_refine_btn,
                accept_all_llm_btn,
                comparison_df_component,
                pair_header,
                pair_label,
                selected_pair_state,
                llm_insight_panel,
                llm_insight_text,
                accept_llm_btn,
                match_btn,
                uncertain_btn,
                non_match_btn,
                first_btn,
                prev_btn,
                next_btn,
                last_btn,
                comparison_title,
                reclassify_title,
            ]

            def make_batch_refine_handler(tname, outputs_list):
                def handle_batch_refine(model_val, history, selected_pair, current_pair_idx):


                    if "/" in model_val:
                        provider, model = model_val.split("/", 1)
                    else:
                        provider, model = "unknown", model_val
                        
                    res_obj = state.linkage_result.er_results[tname]
                    try:
                        updated_result, log_msg = handle_llm_refinement(res_obj, model, provider)
                        
                        state.linkage_result.er_results[tname] = updated_result
                        
                        new_hist = history + [{
                            "role": "assistant",
                            "content": f"LLM Refinement: {log_msg}"
                        }]
                        
                        u_count = len(updated_result.uncertain)
                        has_llm = "llm_decision" in updated_result.uncertain.columns
                        
                        (
                            comp_df,
                            pair_header_md,
                            pair_label_val,
                            pair_id,
                            llm_visible,
                            llm_md,
                            accept_btn_visible,
                            match_btn_vis,
                            uncertain_btn_vis,
                            non_match_btn_vis,
                            first_ia,
                            prev_ia,
                            next_ia,
                            last_ia
                        ) = load_pair_at(updated_result, "uncertain", current_pair_idx)
                        
                        res_tuple = (
                            new_hist,
                            new_hist,
                            gr.update(value=str(u_count)),
                            gr.update(visible=False),            # batch_refine_btn
                            gr.update(visible=has_llm),          # accept_all_llm_btn
                            gr.update(value=comp_df, visible=True),  # comparison_df_component
                            pair_header_md,                      # pair_header
                            pair_label_val,                      # pair_label
                            pair_id,                             # selected_pair_state
                            gr.update(visible=llm_visible),      # llm_insight_panel
                            llm_md,                              # llm_insight_text
                            gr.update(visible=accept_btn_visible), # accept_llm_btn
                            gr.update(visible=match_btn_vis),    # match_btn
                            gr.update(visible=uncertain_btn_vis),# uncertain_btn
                            gr.update(visible=non_match_btn_vis),# non_match_btn
                            gr.update(interactive=first_ia),     # first_btn
                            gr.update(interactive=prev_ia),      # prev_btn
                            gr.update(interactive=next_ia),      # next_btn
                            gr.update(interactive=last_ia),      # last_btn
                            gr.update(visible=True),             # comparison_title
                            gr.update(visible=True),             # reclassify_title
                        )
                        return res_tuple

                    except Exception as e:
                        err_msg = str(e)
                        if hasattr(e, 'message'):
                            err_msg = e.message
                        new_hist = history + [{
                            "role": "assistant",
                            "content": f"LLM Refinement Error: {err_msg}"
                        }]
                        
                        (
                            comp_df,
                            pair_header_md,
                            pair_label_val,
                            pair_id,
                            llm_visible,
                            llm_md,
                            accept_btn_visible,
                            match_btn_vis,
                            uncertain_btn_vis,
                            non_match_btn_vis,
                            first_ia,
                            prev_ia,
                            next_ia,
                            last_ia
                        ) = load_pair_at(res_obj, "uncertain", current_pair_idx)

                        return (
                            new_hist,                 # chatbot_history
                            new_hist,                 # chatbot
                            gr.update(),              # uncertain_count
                            gr.update(visible=True),  # batch_refine_btn
                            gr.update(),              # accept_all_llm_btn
                            gr.update(value=comp_df, visible=True), # comparison_df_component
                            pair_header_md,           # pair_header
                            pair_label_val,           # pair_label
                            pair_id,                  # selected_pair_state
                            gr.update(visible=llm_visible),
                            llm_md,
                            gr.update(visible=accept_btn_visible),
                            gr.update(visible=match_btn_vis),
                            gr.update(visible=uncertain_btn_vis),
                            gr.update(visible=non_match_btn_vis),
                            gr.update(interactive=first_ia),
                            gr.update(interactive=prev_ia),
                            gr.update(interactive=next_ia),
                            gr.update(interactive=last_ia),
                            gr.update(visible=True),  # comparison_title
                            gr.update(visible=True),  # reclassify_title
                        )
                return handle_batch_refine

            def make_accept_llm_suggestion_handler(tname):
                def accept_llm_suggestion(selected_pair, active_view_val, pair_idx_val, history):
                    # 26 outputs (includes comparison_title + reclassify_title + pair_nav_row)
                    _no_op = (
                        gr.update(), gr.update(), gr.update(),           # match_count, uncertain_count, non_match_count
                        history, history, pair_idx_val,                  # chatbot_history, chatbot, pair_index_state
                        gr.update(),                                     # empty_state
                        gr.update(), gr.update(),                        # comparison_title, reclassify_title
                        gr.update(), gr.update(), gr.update(), None,     # comparison_df_component, pair_header, pair_label, selected_pair_state
                        gr.update(), gr.update(), gr.update(),           # llm_insight_panel, llm_insight_text, accept_llm_btn
                        gr.update(), gr.update(), gr.update(),           # match_btn, uncertain_btn, non_match_btn
                        gr.update(), gr.update(), gr.update(), gr.update(), # first_btn, prev_btn, next_btn, last_btn
                        gr.update(), gr.update(),                        # batch_refine_btn, accept_all_llm_btn
                        gr.update()                                      # pair_nav_row
                    )
                    if selected_pair is None:
                        return _no_op

                    res_obj = state.linkage_result.er_results[tname]

                    idx_a_type = type(res_obj.df_a_clean.index[0]) if not res_obj.df_a_clean.empty else str
                    idx_b_type = type(res_obj.df_b_clean.index[0]) if not res_obj.df_b_clean.empty else str

                    try:
                        id_a = idx_a_type(selected_pair[0])
                    except Exception:
                        id_a = selected_pair[0]

                    try:
                        id_b = idx_b_type(selected_pair[1])
                    except Exception:
                        id_b = selected_pair[1]

                    pair = (id_a, id_b)
                    target_bucket = "uncertain"  # fallback

                    if res_obj.uncertain is not None and pair in res_obj.uncertain.index:
                        decision_val = res_obj.uncertain.loc[pair, "llm_decision"]
                        target_bucket = "matches" if bool(decision_val) else "non_matches"

                        row = res_obj.uncertain.loc[[pair]]
                        res_obj.uncertain = res_obj.uncertain.drop(index=[pair])

                        if target_bucket == "matches":
                            res_obj.matches = pd.concat([res_obj.matches, row])
                        else:
                            res_obj.non_matches = pd.concat([res_obj.non_matches, row])

                    log_msg = f"**System**: Pair `{selected_pair[0]} - {selected_pair[1]}` moved to **{target_bucket.title()}** based on LLM suggestion."

                    new_hist = history + [{
                        "role": "assistant",
                        "content": f"{log_msg}\n\nIf you have finished reviewing, you can click below to run Data Fusion:",
                        "options": [{"label": "Run Data Fusion", "value": "run_fusion"}]
                    }]

                    # Recompute batch-action button visibility for current view (always uncertain here)
                    has_llm = (
                        res_obj.uncertain is not None
                        and "llm_decision" in res_obj.uncertain.columns
                    )
                    is_uncertain_view = (active_view_val == "uncertain")
                    batch_refine_vis = is_uncertain_view and not has_llm
                    accept_all_vis = is_uncertain_view and has_llm

                    new_N = get_bucket_len(res_obj, active_view_val)
                    if new_N == 0:
                        empty_visible = True
                        workspace_visible = False
                        new_idx = 0

                        comp_df = pd.DataFrame(columns=["Field", "Record A", "Record B"])
                        pair_header_md = ""
                        pair_label_val = "Pair 0 of 0"
                        pair_id = None
                        llm_visible = False
                        llm_md = ""
                        accept_btn_visible = False
                        match_btn_vis = False
                        uncertain_btn_vis = False
                        non_match_btn_vis = False
                        first_ia = prev_ia = next_ia = last_ia = False
                    else:
                        empty_visible = False
                        workspace_visible = True
                        new_idx = min(pair_idx_val, new_N - 1)
                        (
                            comp_df,
                            pair_header_md,
                            pair_label_val,
                            pair_id,
                            llm_visible,
                            llm_md,
                            accept_btn_visible,
                            match_btn_vis,
                            uncertain_btn_vis,
                            non_match_btn_vis,
                            first_ia,
                            prev_ia,
                            next_ia,
                            last_ia
                        ) = load_pair_at(res_obj, active_view_val, new_idx)

                    return (
                        gr.update(value=str(len(res_obj.matches))),     # 1 (match_count)
                        gr.update(value=str(len(res_obj.uncertain))),   # 2 (uncertain_count)
                        gr.update(value=str(len(res_obj.non_matches))), # 3 (non_match_count)
                        new_hist,                                       # 4 (chatbot_history)
                        new_hist,                                       # 5 (chatbot)
                        new_idx,                                        # 6 (pair_index_state)
                        gr.update(visible=empty_visible),               # 7 (empty_state)
                        gr.update(visible=workspace_visible),           # 8 (comparison_title)
                        gr.update(visible=workspace_visible),           # 9 (reclassify_title)
                        gr.update(value=comp_df, visible=workspace_visible), # 10 (comparison_df_component)
                        pair_header_md,                                 # 11 (pair_header)
                        pair_label_val,                                 # 12 (pair_label)
                        pair_id,                                        # 13 (selected_pair_state)
                        gr.update(visible=llm_visible),                 # 14 (llm_insight_panel)
                        llm_md,                                         # 15 (llm_insight_text)
                        gr.update(visible=accept_btn_visible),          # 16 (accept_llm_btn)
                        gr.update(visible=match_btn_vis),               # 17 (match_btn)
                        gr.update(visible=uncertain_btn_vis),           # 18 (uncertain_btn)
                        gr.update(visible=non_match_btn_vis),           # 19 (non_match_btn)
                        gr.update(interactive=first_ia),                # 20 (first_btn)
                        gr.update(interactive=prev_ia),                 # 21 (prev_btn)
                        gr.update(interactive=next_ia),                 # 22 (next_btn)
                        gr.update(interactive=last_ia),                 # 23 (last_btn)
                        gr.update(visible=batch_refine_vis),            # 24 (batch_refine_btn)
                        gr.update(visible=accept_all_vis),              # 25 (accept_all_llm_btn)
                        gr.update(visible=workspace_visible),           # 26 (pair_nav_row)
                    )
                return accept_llm_suggestion

            def make_bulk_accept_handler(tname):
                def bulk_accept_llm_suggestions(active_view_val, history):
                    res_obj = state.linkage_result.er_results[tname]
                    
                    if res_obj.uncertain is None or res_obj.uncertain.empty or "llm_decision" not in res_obj.uncertain.columns:
                        return (
                            gr.update(), gr.update(), gr.update(),           # counts
                            history, history, 0,                             # history, chatbot, index
                            gr.update(),                                     # empty_state
                            gr.update(), gr.update(),                        # comparison_title, reclassify_title
                            gr.update(), gr.update(), gr.update(), None,     # df_component, header, label, pair_id
                            gr.update(), gr.update(), gr.update(),           # llm panel, text, accept button
                            gr.update(), gr.update(), gr.update(),           # match, uncertain, non-match buttons
                            gr.update(), gr.update(), gr.update(), gr.update(), # first, prev, next, last buttons
                            gr.update(),                                     # accept_all_llm_btn
                            gr.update()                                      # pair_nav_row
                        )
                        
                    valid_mask = ~pd.isna(res_obj.uncertain["llm_decision"])
                    df_to_move = res_obj.uncertain[valid_mask]
                    
                    if df_to_move.empty:
                        return (
                            gr.update(), gr.update(), gr.update(),           # counts
                            history, history, 0,                             # history, chatbot, index
                            gr.update(),                                     # empty_state
                            gr.update(), gr.update(),                        # comparison_title, reclassify_title
                            gr.update(), gr.update(), gr.update(), None,     # df_component, header, label, pair_id
                            gr.update(), gr.update(), gr.update(),           # llm panel, text, accept button
                            gr.update(), gr.update(), gr.update(),           # match, uncertain, non-match buttons
                            gr.update(), gr.update(), gr.update(), gr.update(), # first, prev, next, last buttons
                            gr.update(),                                     # accept_all_llm_btn
                            gr.update()                                      # pair_nav_row
                        )
                        
                    matches_to_move = df_to_move[df_to_move["llm_decision"] == True]
                    non_matches_to_move = df_to_move[df_to_move["llm_decision"] == False]
                    
                    if not matches_to_move.empty:
                        res_obj.matches = pd.concat([res_obj.matches, matches_to_move])
                        
                    if not non_matches_to_move.empty:
                        res_obj.non_matches = pd.concat([res_obj.non_matches, non_matches_to_move])
                        
                    res_obj.uncertain = res_obj.uncertain.drop(index=df_to_move.index)
                    
                    moved_matches = len(matches_to_move)
                    moved_non_matches = len(non_matches_to_move)
                    log_msg = f"**System**: Bulk accepted LLM suggestions. Moved {moved_matches} pairs to Matches and {moved_non_matches} pairs to Non-Matches in table *{tname}*."
                    
                    new_hist = history + [{
                        "role": "assistant",
                        "content": f"{log_msg}\n\nIf you have finished reviewing, you can click below to run Data Fusion:",
                        "options": [{"label": "Run Data Fusion", "value": "run_fusion"}]
                    }]
                    
                    new_N = get_bucket_len(res_obj, active_view_val)
                    if new_N == 0:
                        empty_visible = True
                        workspace_visible = False
                        new_idx = 0
                        
                        comp_df = pd.DataFrame(columns=["Field", "Record A", "Record B"])
                        pair_header_md = ""
                        pair_label_val = "Pair 0 of 0"
                        pair_id = None
                        llm_visible = False
                        llm_md = ""
                        accept_btn_visible = False
                        match_btn_vis = False
                        uncertain_btn_vis = False
                        non_match_btn_vis = False
                        first_ia = prev_ia = next_ia = last_ia = False
                    else:
                        empty_visible = False
                        workspace_visible = True
                        new_idx = 0
                        (
                            comp_df,
                            pair_header_md,
                            pair_label_val,
                            pair_id,
                            llm_visible,
                            llm_md,
                            accept_btn_visible,
                            match_btn_vis,
                            uncertain_btn_vis,
                            non_match_btn_vis,
                            first_ia,
                            prev_ia,
                            next_ia,
                            last_ia
                        ) = load_pair_at(res_obj, active_view_val, new_idx)
                        
                    return (
                        gr.update(value=str(len(res_obj.matches))),     # 1 (match_count)
                        gr.update(value=str(len(res_obj.uncertain))),   # 2 (uncertain_count)
                        gr.update(value=str(len(res_obj.non_matches))), # 3 (non_match_count)
                        new_hist,                                       # 4 (chatbot_history)
                        new_hist,                                       # 5 (chatbot)
                        new_idx,                                        # 6 (pair_index_state)
                        gr.update(visible=empty_visible),               # 7 (empty_state)
                        gr.update(visible=workspace_visible),           # 8 (comparison_title)
                        gr.update(visible=workspace_visible),           # 9 (reclassify_title)
                        gr.update(value=comp_df, visible=workspace_visible), # 10 (comparison_df_component)
                        pair_header_md,                                 # 11 (pair_header)
                        pair_label_val,                                 # 12 (pair_label)
                        pair_id,                                        # 13 (selected_pair_state)
                        gr.update(visible=llm_visible),                 # 14 (llm_insight_panel)
                        llm_md,                                         # 15 (llm_insight_text)
                        gr.update(visible=accept_btn_visible),          # 16 (accept_llm_btn)
                        gr.update(visible=match_btn_vis),               # 17 (match_btn)
                        gr.update(visible=uncertain_btn_vis),           # 18 (uncertain_btn)
                        gr.update(visible=non_match_btn_vis),           # 19 (non_match_btn)
                        gr.update(interactive=first_ia),                # 20 (first_btn)
                        gr.update(interactive=prev_ia),                 # 21 (prev_btn)
                        gr.update(interactive=next_ia),                 # 22 (next_btn)
                        gr.update(interactive=last_ia),                 # 23 (last_btn)
                        gr.update(visible=False),                       # 24 (accept_all_llm_btn)
                        gr.update(visible=workspace_visible)            # 25 (pair_nav_row)
                    )
                return bulk_accept_llm_suggestions
                
            _ACTION_OUTPUTS = [
                match_count, uncertain_count, non_match_count,
                chatbot_history, chatbot,
                pair_index_state,
                empty_state,
                comparison_title,
                reclassify_title,
                comparison_df_component,
                pair_header,
                pair_label,
                selected_pair_state,
                llm_insight_panel,
                llm_insight_text,
                accept_llm_btn,
                match_btn,
                uncertain_btn,
                non_match_btn,
                first_btn,
                prev_btn,
                next_btn,
                last_btn,
                batch_refine_btn,
                accept_all_llm_btn,
                pair_nav_row,
            ]

            match_btn.click(
                fn=make_action_handler(table_name, "matches"),
                inputs=[selected_pair_state, active_view, pair_index_state, chatbot_history],
                outputs=_ACTION_OUTPUTS,
                show_progress="hidden",
            )
            uncertain_btn.click(
                fn=make_action_handler(table_name, "uncertain"),
                inputs=[selected_pair_state, active_view, pair_index_state, chatbot_history],
                outputs=_ACTION_OUTPUTS,
                show_progress="hidden",
            )
            non_match_btn.click(
                fn=make_action_handler(table_name, "non_matches"),
                inputs=[selected_pair_state, active_view, pair_index_state, chatbot_history],
                outputs=_ACTION_OUTPUTS,
                show_progress="hidden",
            )
            batch_refine_btn.click(
                fn=make_batch_refine_handler(table_name, _REFINE_OUTPUTS),
                inputs=[model_dropdown, chatbot_history, selected_pair_state, pair_index_state],
                outputs=_REFINE_OUTPUTS,
                show_progress="hidden",
            ).then(
                fn=None,
                inputs=[],
                outputs=[],
                js=f"""() => {{
                    const tbl = '{table_name}';
                    const suffix = tbl === 'organizations' ? '' : '-' + tbl;
                    const showIds = [
                        'er-accept-all-llm-btn' + suffix,
                        'er-llm-reasoning-box' + suffix,
                        'er-accept-llm-btn' + suffix
                    ];
                    showIds.forEach(id => {{
                        const el = document.getElementById(id);
                        if (el) {{
                            el.classList.remove('hidden', 'hide');
                            el.style.removeProperty('display');
                            if (el.parentElement && (el.parentElement.classList.contains('hidden') || el.parentElement.classList.contains('hide'))) {{
                                el.parentElement.classList.remove('hidden', 'hide');
                                el.parentElement.style.removeProperty('display');
                            }}
                        }}
                    }});
                    const hideBtn = document.getElementById('er-batch-refine-btn' + suffix);
                    if (hideBtn) {{
                        hideBtn.classList.add('hidden');
                        hideBtn.style.display = 'none';
                    }}
                }}""",
            )


            accept_llm_btn.click(
                fn=make_accept_llm_suggestion_handler(table_name),
                inputs=[selected_pair_state, active_view, pair_index_state, chatbot_history],
                outputs=_ACTION_OUTPUTS,
                show_progress="hidden",
            )
            accept_all_llm_btn.click(
                fn=make_bulk_accept_handler(table_name),
                inputs=[active_view, chatbot_history],
                outputs=[
                    match_count, uncertain_count, non_match_count,
                    chatbot_history, chatbot,
                    pair_index_state,
                    empty_state,
                    comparison_title,
                    reclassify_title,
                    comparison_df_component,
                    pair_header,
                    pair_label,
                    selected_pair_state,
                    llm_insight_panel,
                    llm_insight_text,
                    accept_llm_btn,
                    match_btn,
                    uncertain_btn,
                    non_match_btn,
                    first_btn,
                    prev_btn,
                    next_btn,
                    last_btn,
                    accept_all_llm_btn,
                    pair_nav_row
                ]
            )
