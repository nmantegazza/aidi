import logging

import gradio as gr
import pandas as pd

from shared.config import config

from .handlers import (
    handle_data_porting,
    handle_er_propose,
    handle_execute_fusion,
    handle_ingestion_and_cleaning,
    handle_record_linkage,
    handle_results_wrapper,
    handle_run_fusion,
    handle_schema_matching,
    handle_schema_refinement,
)
from .phases.canvas import (
    DataFusionConfigCanvasState,
    DataFusionResultCanvasState,
    ERConfigCanvasState,
    ERReviewCanvasState,
    IngestionCanvasState,
    MatchingCanvasState,
    PortingCanvasState,
    ResultsCanvasState,
)
from .phases.phase_1_ingestion import render_ingestion_canvas
from .phases.phase_3_matching import render_matching_canvas
from .phases.phase_4_porting import render_porting_canvas
from .phases.phase_5_linkage import render_er_config_canvas, render_er_review_canvas
from .phases.phase_6_fusion import (
    render_fusion_config_canvas,
    render_fusion_result_canvas,
)
from .phases.phase_6_results import render_results_canvas
from .snapshot import list_snapshots, load_snapshot, save_snapshot

logger = logging.getLogger(__name__)




with gr.Blocks(title="Data Integration Pipeline", fill_width=True, fill_height=True) as app:
    # --- PERSISTENT STATE VARIABLES ---
    ingestion_state = gr.State(None)
    cleaning_state = gr.State(None)
    matching_state = gr.State(None)
    porting_state = gr.State(None)
    linkage_state = gr.State(None)
    fusion_state = gr.State(None)
    final_report_state = gr.State(None)

    # --- UI STATE VARIABLES ---
    canvas_state = gr.State(IngestionCanvasState())
    chatbot_history = gr.State([{
        "role": "assistant",
        "content": "System: Data Integration Pipeline initialized. Please enter the source data directory path in the chat input below, or select an option below to load a test case:",
        "options": [
            {"label": "Load Running Example (Enterprise)", "value": "load:data/test_cases/running_example"},
        ]
    }])
    current_stage = gr.State("initial")  # initial, ingested, cleaned, matched, ported, configured, review, fusion_config, fused, results

    with gr.Row(elem_id="header-banner", elem_classes="header-row"):
        gr.Markdown("# Agentic AI for Data Integration")

    # --- TWO-COLUMN LAYOUT ---
    with gr.Row(elem_id="two-column-layout", elem_classes="two-column-layout"):
        
        # Left Column: Orchestrator
        with gr.Column(scale=1, elem_id="orchestrator-column", elem_classes="orchestrator-col"):
            gr.Markdown("### Integration Log")
            
            chatbot = gr.Chatbot(
                value=[{
                    "role": "assistant",
                    "content": "System: Data Integration Pipeline initialized. Please enter the source data directory path in the chat input below, or select an option below to load a test case:",
                    "options": [
                        {"label": "Load Running Example (Enterprise)", "value": "load:data/test_cases/running_example"},
                    ]
                }],
                elem_id="copilot-chatbot",
                height="100%",
                scale=1,
                group_consecutive_messages=False
            )
            
            # Central chat input area
            with gr.Column(elem_classes="chat-input-container"):
                chat_input = gr.Textbox(
                    placeholder="Enter source data directory path ",
                    label="Chat Input / Commands",
                    interactive=True,
                    elem_id="chat-input-box"
                )
                
                # Single Model Selection Dropdown directly under it
                model_choices = []
                for provider, models in config.SUPPORTED_MODELS.items():
                    nice_prov = "Google" if provider == config.PROVIDER_GOOGLE else provider.title()
                    for model in models:
                        model_choices.append((f"{nice_prov} -> {model}", f"{provider}/{model}"))
                
                model_dropdown = gr.Dropdown(
                    choices=model_choices,
                    value=f"{config.DEFAULT_PROVIDER}/{config.SUPPORTED_MODELS[config.DEFAULT_PROVIDER][0]}",
                    label="Active Model",
                    elem_id="active-model-dropdown"
                )

            # --- DEV TOOLS ACCORDION ---
            with gr.Accordion("Dev Tools (Snapshots)", open=False, elem_id="dev-tools-accordion"):
                with gr.Row():
                    snapshot_name = gr.Textbox(
                        placeholder="e.g. initial_load",
                        label="Snapshot Name",
                        scale=2
                    )
                    save_btn = gr.Button("Save", scale=1)
                
                with gr.Row():
                    snapshot_dropdown = gr.Dropdown(
                        choices=list_snapshots(),
                        value=list_snapshots()[0] if list_snapshots() else None,
                        label="Select Snapshot",
                        scale=2
                    )
                    refresh_btn = gr.Button("Refresh", scale=1)
                    load_btn = gr.Button("Load", scale=1)
                
                dev_status = gr.Markdown("", visible=False)

        # Right Column: Dynamic Canvas
        with gr.Column(scale=2, elem_id="canvas-column", elem_classes="canvas-col"):
            @gr.render(inputs=canvas_state)
            def render_canvas(state):
                if isinstance(state, IngestionCanvasState):
                    render_ingestion_canvas(state, canvas_state, chatbot_history, current_stage, ingestion_state, chatbot)
                elif isinstance(state, MatchingCanvasState):
                    render_matching_canvas(state)
                elif isinstance(state, PortingCanvasState):
                    render_porting_canvas(state)
                elif isinstance(state, ERConfigCanvasState):
                    render_er_config_canvas(state)
                elif isinstance(state, ERReviewCanvasState):
                    render_er_review_canvas(state, canvas_state, chatbot_history, linkage_state, chatbot, model_dropdown)
                elif isinstance(state, DataFusionConfigCanvasState):
                    render_fusion_config_canvas(state)
                elif isinstance(state, DataFusionResultCanvasState):
                    render_fusion_result_canvas(state)
                elif isinstance(state, ResultsCanvasState):
                    render_results_canvas(state)

    # --- CHAT / COMMANDS SUBMIT HANDLER ---
    def on_chat_input_submit(user_msg, stage, hist, ingest_s, match_s, model_val):
        if not user_msg.strip():
            return "", hist, hist, gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()
        
        provider, model_name = model_val.split("/")
        
        if stage == "initial":
            path = user_msg.strip()
            new_hist = hist + [{"role": "user", "content": f"Load Data: {path}"}]
            try:
                ingest_res, clean_res, msg = handle_ingestion_and_cleaning(path)
                new_hist = new_hist + [{
                    "role": "assistant",
                    "content": f"{msg}\n\nPlease proceed to the next step:",
                    "options": [{"label": "Generate Integrated Schema", "value": "match"}]
                }]
                return (
                    "", # clear input
                    new_hist, # chatbot_history state
                    new_hist, # chatbot UI
                    ingest_res, # ingestion_state
                    clean_res, # cleaning_state
                    gr.update(), # matching_state
                    "cleaned", # current_stage
                    IngestionCanvasState(ingested=True, ingestion_result=ingest_res, cleaned=True, cleaning_result=clean_res), # canvas_state
                    gr.update(interactive=False, placeholder="Awaiting action")
                )
            except Exception as e:
                new_hist = new_hist + [{
                    "role": "assistant",
                    "content": f"System Error: Data ingestion/cleaning failed: {e!s}",
                    "options": [{"label": "Load Running Example (Enterprise)", "value": "load:data/test_cases/running_example"}]
                }]
                return (
                    "",
                    new_hist,
                    new_hist,
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    "initial",
                    gr.update(),
                    gr.update(interactive=True, placeholder="Enter source data directory path (e.g. data/test_cases/running_example)...")
                )
                
        elif stage == "matched":
            prompt = user_msg.strip()
            new_hist = hist + [{"role": "user", "content": prompt}]
            try:
                res, msg = handle_schema_refinement(match_s, prompt, provider, model_name)
                next_msg = (
                    f"{msg}\n\n"
                    "You can continue refining the schema, or proceed to porting:"
                )
                new_hist = new_hist + [{
                    "role": "assistant",
                    "content": next_msg,
                    "options": [{"label": "Generate Porting Instructions & Port", "value": "port"}]
                }]
                new_st = MatchingCanvasState(matching_result=res)
                return (
                    "",
                    new_hist,
                    new_hist,
                    gr.update(), # ingestion_state
                    gr.update(), # cleaning_state
                    res, # matching_state
                    "matched",
                    new_st,
                    gr.update(interactive=True, placeholder="Type schema refinement instruction...")
                )
            except Exception as e:
                new_hist = new_hist + [{
                    "role": "assistant",
                    "content": f"System Error: Schema refinement failed: {e!s}",
                    "options": [{"label": "Proceed to Data Porting", "value": "port"}]
                }]
                return (
                    "",
                    new_hist,
                    new_hist,
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    "matched",
                    gr.update(),
                    gr.update(interactive=True, placeholder="Type schema refinement instruction...")
                )
        else:
            new_hist = hist + [
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": "System: Chat input is not accepted in this stage. Please use the interactive action buttons in the chat."}
            ]
            return "", new_hist, new_hist, gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()

    chat_input.submit(
        fn=on_chat_input_submit,
        inputs=[chat_input, current_stage, chatbot_history, ingestion_state, matching_state, model_dropdown],
        outputs=[
            chat_input, chatbot_history, chatbot,
            ingestion_state, cleaning_state, matching_state,
            current_stage, canvas_state, chat_input
        ]
    )

    # --- CHAT OPTIONS EVENT HANDLER ---
    def on_option_select(
        evt: gr.SelectData, stage, hist,
        ingest_s, clean_s, match_s,
        port_s, linkage_s, fusion_s, model_val, canvas_s
    ):
        action = evt.value
        provider, model_name = model_val.split("/")
        
        # User selection logging in history
        user_label = action.split("load:", 1)[1] if action.startswith("load:") else action
        user_action_label = f"{user_label.upper().replace('_', ' ')}"
        new_hist = hist + [{"role": "user", "content": user_action_label}]
        
        if action.startswith("load:"):
            path = action.split("load:", 1)[1]
            try:
                ingest_res, clean_res, msg = handle_ingestion_and_cleaning(path)
                new_hist = new_hist + [{
                    "role": "assistant",
                    "content": f"{msg}\n\nPlease proceed to the next step:",
                    "options": [{"label": "Generate Integrated Schema", "value": "match"}]
                }]
                return (
                    new_hist, new_hist, "cleaned", IngestionCanvasState(ingested=True, ingestion_result=ingest_res, cleaned=True, cleaning_result=clean_res),
                    ingest_res, clean_res, gr.update(), gr.update(), gr.update(), gr.update(), gr.update(),
                    gr.update(interactive=False, placeholder="Awaiting action")
                )
            except Exception as e:
                new_hist = new_hist + [{
                    "role": "assistant",
                    "content": f"System Error: Data ingestion/cleaning failed: {e!s}",
                    "options": [{"label": "Load Running Example (Enterprise)", "value": "load:data/test_cases/running_example"}]
                }]
                return (
                    new_hist, new_hist, "initial", gr.update(),
                    gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(),
                    gr.update(interactive=True, placeholder="Enter source data directory path (e.g. data/test_cases/running_example)...")
                )
                
        elif action == "match":
            try:
                res, msg = handle_schema_matching(clean_s, provider, model_name)
                next_msg = (
                    f"{msg}\n\n"
                    "To refine the schema, type your instructions in the Chat Input (e.g. 'rename phone to phone_number').\n"
                    "Otherwise, click below to proceed to data porting:"
                )
                new_hist = new_hist + [{
                    "role": "assistant",
                    "content": next_msg,
                    "options": [{"label": "Proceed to Data Porting", "value": "port"}]
                }]
                new_st = MatchingCanvasState(matching_result=res)
                return (
                    new_hist, new_hist, "matched", new_st,
                    gr.update(), gr.update(), res, gr.update(), gr.update(), gr.update(), gr.update(),
                    gr.update(interactive=True, placeholder="Type schema refinement instruction...")
                )
            except Exception as e:
                new_hist = new_hist + [{
                    "role": "assistant",
                    "content": f"System Error: Schema matching failed: {e!s}",
                    "options": [{"label": "Retry Schema Matching", "value": "match"}]
                }]
                return (
                    new_hist, new_hist, "cleaned", gr.update(),
                    gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(),
                    gr.update(interactive=False, placeholder="Awaiting action")
                )
                
        elif action == "port":
            try:
                res, msg = handle_data_porting(clean_s, match_s, provider, model_name)
                next_msg = (
                    f"{msg}\n\n"
                    "Please configure Entity Resolution:"
                )
                new_hist = new_hist + [{
                    "role": "assistant",
                    "content": next_msg,
                    "options": [{"label": "Configure Entity Resolution", "value": "er_propose"}]
                }]
                new_st = PortingCanvasState(porting_result=res, cleaning_result=clean_s)
                return (
                    new_hist, new_hist, "ported", new_st,
                    gr.update(), gr.update(), gr.update(), res, gr.update(), gr.update(), gr.update(),
                    gr.update(interactive=False, placeholder="Awaiting action")
                )
            except Exception as e:
                new_hist = new_hist + [{
                    "role": "assistant",
                    "content": f"System Error: Data porting failed: {e!s}",
                    "options": [{"label": "Retry Data Porting", "value": "port"}]
                }]
                return (
                    new_hist, new_hist, "matched", gr.update(),
                    gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(),
                    gr.update(interactive=False, placeholder="Awaiting action")
                )
                
        elif action == "er_propose":
            try:
                configs, msg = handle_er_propose(match_s, port_s, provider, model_name)
                config_dfs = {}
                for tname, cfg in configs.items():
                    rows = []
                    for col, match_config in cfg.matching_columns.items():
                        rows.append({
                            "Column": col,
                            "Algorithm": match_config.algorithm.value,
                            "Weight": match_config.weight
                        })
                    config_dfs[tname] = pd.DataFrame(rows, columns=["Column", "Algorithm", "Weight"])
                    
                new_st = ERConfigCanvasState(
                    matching_result=match_s,
                    porting_result=port_s,
                    er_configs=configs,
                    er_config_dfs=config_dfs
                )
                new_hist = new_hist + [{
                    "role": "assistant",
                    "content": f"{msg}\n\n*Please review the configuration in the Canvas. When ready, click below to run Record Linkage:*",
                    "options": [{"label": "Run Record Linkage", "value": "run_linkage"}]
                }]
                return (
                    new_hist, new_hist, "configured", new_st,
                    gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(),
                    gr.update(interactive=False, placeholder="Awaiting action")
                )
            except Exception as e:
                new_hist = new_hist + [{
                    "role": "assistant",
                    "content": f"System Error: ER configuration proposal failed: {e!s}",
                    "options": [{"label": "Retry ER Configuration Propose", "value": "er_propose"}]
                }]
                return (
                    new_hist, new_hist, "ported", gr.update(),
                    gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(),
                    gr.update(interactive=False, placeholder="Awaiting action")
                )
                
        elif action == "run_linkage":
            try:
                er_override_configs = canvas_s.er_configs
                
                linkage_res, msg = handle_record_linkage(
                    canvas_s.matching_result,
                    canvas_s.porting_result,
                    provider,
                    model_name,
                    er_override_configs=er_override_configs
                )
                
                new_st = ERReviewCanvasState(
                    linkage_result=linkage_res
                )
                
                new_hist = new_hist + [{
                    "role": "assistant",
                    "content": f"{msg}\n\nPlease review the uncertain pairs in the Canvas. When done, click below to run Data Fusion:",
                    "options": [{"label": "Run Data Fusion", "value": "run_fusion"}]
                }]
                return (
                    new_hist, new_hist, "review", new_st,
                    gr.update(), gr.update(), gr.update(), gr.update(), linkage_res, gr.update(), gr.update(),
                    gr.update(interactive=False, placeholder="Awaiting action")
                )
            except Exception as e:
                new_hist = new_hist + [{
                    "role": "assistant",
                    "content": f"System Error: Record linkage failed: {e!s}",
                    "options": [{"label": "Retry Record Linkage", "value": "run_linkage"}]
                }]
                return (
                    new_hist, new_hist, "configured", gr.update(),
                    gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(),
                    gr.update(interactive=False, placeholder="Awaiting action")
                )
                
        elif action == "run_fusion":
            try:
                config_result, tables_dict, msg = handle_run_fusion(
                    port_s, linkage_s, ingest_s, provider, model_name
                )
                new_canvas = DataFusionConfigCanvasState(
                    config_result=config_result,
                    linkage_result=linkage_s,
                    porting_result=port_s,
                    tables=tables_dict
                )
                new_hist = new_hist + [{
                    "role": "assistant",
                    "content": f"{msg}\n\nWhen ready, click below to execute the merge:",
                    "options": [{"label": "Execute Fusion", "value": "execute_fusion"}]
                }]
                return (
                    new_hist, new_hist, "fusion_config", new_canvas,
                    gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(),
                    gr.update(interactive=False, placeholder="Awaiting action")
                )
            except Exception as e:
                new_hist = new_hist + [{
                    "role": "assistant",
                    "content": f"System Error: Data fusion policy generation failed: {e!s}",
                    "options": [{"label": "Retry Data Fusion", "value": "run_fusion"}]
                }]
                return (
                    new_hist, new_hist, "review", gr.update(),
                    gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(),
                    gr.update(interactive=False, placeholder="Awaiting action")
                )
                
        elif action == "execute_fusion":
            try:
                fusion_res, msg = handle_execute_fusion(canvas_s, provider, model_name)
                new_canvas = DataFusionResultCanvasState(fusion_result=fusion_res)
                new_hist = new_hist + [{
                    "role": "assistant",
                    "content": f"{msg}\n\nWhen ready, click below to generate the final report:",
                    "options": [{"label": "Generate Final Report", "value": "gen_report"}]
                }]
                return (
                    new_hist, new_hist, "fused", new_canvas,
                    gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), fusion_res, gr.update(),
                    gr.update(interactive=False, placeholder="Awaiting action")
                )
            except Exception as e:
                new_hist = new_hist + [{
                    "role": "assistant",
                    "content": f"System Error: Data fusion execution failed: {e!s}",
                    "options": [{"label": "Retry Execute Fusion", "value": "execute_fusion"}]
                }]
                return (
                    new_hist, new_hist, "fusion_config", gr.update(),
                    gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(),
                    gr.update(interactive=False, placeholder="Awaiting action")
                )
                
        elif action == "gen_report":
            try:
                res, msg = handle_results_wrapper(
                    ingest_s.data_root, provider, model_name,
                    ingest_s, clean_s, match_s, port_s, linkage_s,
                    fusion_s
                )
                next_msg = (
                    f"{msg}\n\n"
                    "Pipeline execution complete. Click below to start a new run:"
                )
                new_hist = new_hist + [{
                    "role": "assistant",
                    "content": next_msg,
                    "options": [{"label": "Start New Run", "value": "restart"}]
                }]
                new_st = ResultsCanvasState(final_report=res)
                return (
                    new_hist, new_hist, "results", new_st,
                    gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), res,
                    gr.update(interactive=False, placeholder="Pipeline execution complete.")
                )
            except Exception as e:
                new_hist = new_hist + [{
                    "role": "assistant",
                    "content": f"System Error: Final report generation failed: {e!s}",
                    "options": [{"label": "Retry Final Report Generation", "value": "gen_report"}]
                }]
                return (
                    new_hist, new_hist, "review", gr.update(),
                    gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(),
                    gr.update(interactive=False, placeholder="Awaiting action")
                )
                
        elif action == "restart":
            init_hist = [{
                "role": "assistant",
                "content": "System: Data Integration Pipeline restarted. Please enter the source data directory path in the chat input below, or select the option below to load the running example:",
                "options": [{"label": "Load Running Example (Enterprise)", "value": "load:data/test_cases/running_example"}]
            }]
            return (
                init_hist, init_hist, "initial", IngestionCanvasState(),
                None, None, None, None, None, None, None,
                gr.update(interactive=True, placeholder="Enter source data directory path (e.g. data/test_cases/running_example)...")
            )
            
        return (
            new_hist, new_hist, stage, gr.update(),
            gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(),
            gr.update()
        )

    chatbot.option_select(
        fn=on_option_select,
        inputs=[
            current_stage, chatbot_history,
            ingestion_state, cleaning_state, matching_state,
            porting_state, linkage_state, fusion_state, model_dropdown, canvas_state
        ],
        outputs=[
            chatbot_history, chatbot, current_stage, canvas_state,
            ingestion_state, cleaning_state, matching_state,
            porting_state, linkage_state, fusion_state, final_report_state,
            chat_input
        ]
    )

    # --- DEV TOOLS EVENT HANDLERS ---
    def handle_save_snapshot(
        name, ingest_s, clean_s, match_s, port_s, linkage_s, fusion_s, final_s,
        canvas_s, current_s, chatbot_h
    ):
        if not name or not name.strip():
            return gr.update(value="Please provide a snapshot name", visible=True), gr.update()
        
        name = name.strip()
        try:
            state = {
                "ingestion_state": ingest_s,
                "cleaning_state": clean_s,
                "matching_state": match_s,
                "porting_state": port_s,
                "linkage_state": linkage_s,
                "fusion_state": fusion_s,
                "final_report_state": final_s,
                "canvas_state": canvas_s,
                "current_stage": current_s,
                "chatbot_history": chatbot_h,
            }
            save_snapshot(name, state)
            new_choices = list_snapshots()
            selected_val = f"{name}.pkl" if not name.endswith(".pkl") else name
            return (
                gr.update(value=f"Snapshot '{selected_val}' saved successfully!", visible=True),
                gr.update(choices=new_choices, value=selected_val)
            )
        except Exception as e:
            logger.exception("Failed to save snapshot")
            return gr.update(value=f"Failed to save snapshot: {e!s}", visible=True), gr.update()

    def handle_load_snapshot(name):
        if not name:
            return (
                gr.update(value="Please select a snapshot", visible=True),
                gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(),
                gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()
            )
        
        try:
            state = load_snapshot(name)
            
            ingest_s = state.get("ingestion_state")
            clean_s = state.get("cleaning_state")
            match_s = state.get("matching_state")
            port_s = state.get("porting_state")
            linkage_s = state.get("linkage_state")
            fusion_s = state.get("fusion_state")
            final_s = state.get("final_report_state")
            canvas_s = state.get("canvas_state")
            current_s = state.get("current_stage")
            chatbot_h = state.get("chatbot_history", [])
            
            if current_s == "initial":
                chat_placeholder = "Enter source data directory path (e.g. data/test_cases/running_example)..."
                chat_interactive = True
            elif current_s == "matched":
                chat_placeholder = "Type schema refinement instruction..."
                chat_interactive = True
            else:
                chat_placeholder = "Awaiting action"
                chat_interactive = False
                
            return (
                gr.update(value=f"Snapshot '{name}' loaded successfully!", visible=True),
                ingest_s,
                clean_s,
                match_s,
                port_s,
                linkage_s,
                fusion_s,
                final_s,
                canvas_s,
                chatbot_h,
                chatbot_h,
                current_s,
                gr.update(interactive=chat_interactive, placeholder=chat_placeholder)
            )
        except Exception as e:
            logger.exception("Failed to load snapshot")
            return (
                gr.update(value=f"Failed to load snapshot: {e!s}", visible=True),
                gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(),
                gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()
            )

    def handle_refresh_snapshots():
        new_choices = list_snapshots()
        selected_val = new_choices[0] if new_choices else None
        return gr.update(choices=new_choices, value=selected_val)

    save_btn.click(
        fn=handle_save_snapshot,
        inputs=[
            snapshot_name, ingestion_state, cleaning_state, matching_state,
            porting_state, linkage_state, fusion_state, final_report_state,
            canvas_state, current_stage, chatbot_history
        ],
        outputs=[dev_status, snapshot_dropdown]
    )

    load_btn.click(
        fn=handle_load_snapshot,
        inputs=[snapshot_dropdown],
        outputs=[
            dev_status,
            ingestion_state, cleaning_state, matching_state,
            porting_state, linkage_state, fusion_state, final_report_state,
            canvas_state, chatbot_history, chatbot,
            current_stage, chat_input
        ]
    )

    refresh_btn.click(
        fn=handle_refresh_snapshots,
        inputs=[],
        outputs=[snapshot_dropdown]
    )

