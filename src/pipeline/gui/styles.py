# --- Custom CSS for Premium Look ---
custom_css = """
html, body {
    height: 100vh !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
}
.gradio-container {
    height: 100vh !important;
    max-height: 100vh !important;
    display: flex !important;
    flex-direction: column !important;
    overflow: hidden !important;
    padding: 12px 24px !important;
    box-sizing: border-box !important;
}
.header-row {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    padding: 12px 20px !important;
    border-radius: 12px;
    margin-bottom: 12px !important;
    text-align: center;
    color: white !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    flex-shrink: 0 !important;
}
.header-row h1 {
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    font-weight: 700;
    letter-spacing: -0.025em;
    margin: 0;
    font-size: 1.5rem !important;
    line-height: 1.2 !important;
}
.header-row * {
    color: white !important;
}
.two-column-layout {
    display: flex !important;
    flex-direction: row !important;
    gap: 20px !important;
    margin-top: 0 !important;
    width: 100% !important;
    flex: 1 1 0 !important;
    min-height: 0 !important;
    overflow: hidden !important;
}
.orchestrator-col {
    background: #f8fafc !important;
    padding: 16px !important;
    border-radius: 16px !important;
    border: 1px solid #e2e8f0 !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
    height: 100% !important;
    max-height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    overflow: hidden !important;
    min-height: 0 !important;
    position: relative !important;
    gap: 8px !important;
}
.orchestrator-col > .prose:first-child,
.orchestrator-col > div:first-child h3 {
    margin: 0 !important;
    padding-bottom: 4px !important;
}
.orchestrator-col #copilot-chatbot {
    flex: 1 1 0px !important;
    min-height: 0 !important;
    height: 100% !important;
    max-height: none !important;
    display: flex !important;
    flex-direction: column !important;
}
#copilot-chatbot > div {
    height: 100% !important;
    flex: 1 1 0 !important;
}
#copilot-chatbot .wrapper,
#copilot-chatbot .bubble-wrap {
    height: 100% !important;
    flex: 1 1 0 !important;
}
.orchestrator-col .chat-input-container {
    flex: 0 0 auto !important;
    flex-shrink: 0 !important;
    margin-top: 4px !important;
}

/* --- DEV TOOLS OVERLAY DRAWER --- */
#dev-tools-accordion {
    flex: 0 0 auto !important;
    flex-shrink: 0 !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 8px !important;
    background: #f1f5f9 !important;
    margin-top: 4px !important;
    position: relative !important;
    transition: all 0.2s ease-in-out !important;
}
#dev-tools-accordion:has(button.label-wrap.open) {
    position: absolute !important;
    bottom: 16px !important;
    left: 16px !important;
    right: 16px !important;
    z-index: 50 !important;
    background: #ffffff !important;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.15), 0 8px 10px -6px rgba(0, 0, 0, 0.1) !important;
    border: 1px solid #94a3b8 !important;
    padding: 8px !important;
}
.canvas-col {
    background: #ffffff !important;
    padding: 20px !important;
    border-radius: 16px !important;
    border: 1px solid #e2e8f0 !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
    height: 100% !important;
    max-height: 100% !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
    min-height: 0 !important;
    scrollbar-width: thin;
}
.canvas-col::-webkit-scrollbar,
.orchestrator-col ::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
.canvas-col::-webkit-scrollbar-thumb,
.orchestrator-col ::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 9999px;
}
.canvas-col::-webkit-scrollbar-track {
    background: transparent;
}

/* --- NUCLEAR OVERRIDE FOR MERMAID READABILITY & SCREEN FIT --- */
.mermaid {
    background-color: #ffffff !important;
    padding: 12px !important;
    border-radius: 12px;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
    border: 1px solid #e2e8f0;
    max-height: calc(100vh - 290px) !important;
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    overflow: hidden !important;
    box-sizing: border-box !important;
}
.mermaid svg {
    max-width: 88% !important;
    max-height: calc(100vh - 320px) !important;
    width: auto !important;
    height: auto !important;
    object-fit: contain !important;
    background-color: transparent !important;
}
.mermaid svg text, 
.mermaid svg tspan, 
.mermaid svg .label, 
.mermaid svg .edgeLabel, 
.mermaid svg foreignObject, 
.mermaid svg foreignObject div {
    fill: #0f172a !important;
    color: #0f172a !important;
    font-weight: 600 !important;
}
.mermaid svg path, 
.mermaid svg line, 
.mermaid svg rect, 
.mermaid svg circle {
    stroke: #334155 !important;
    stroke-width: 1px !important;
}
.mermaid svg rect.er.entityBox {
    fill: #f1f5f9 !important;
}
.mermaid svg rect.er.attributeBox {
    fill: #ffffff !important;
}
.mermaid svg .er.entityLabel {
    fill: #0f172a !important;
}

/* --- HEALTH DASHBOARD STYLES --- */
.health-summary {
    padding: 8px 12px;
    background: var(--background-fill-secondary, #f1f5f9);
    border-radius: 6px;
    margin-bottom: 12px;
}
.completeness-container {
    width: 100%;
    background-color: #e2e8f0;
    border-radius: 9999px;
    height: 8px;
    margin-top: 4px;
    overflow: hidden;
}
.completeness-fill {
    height: 100%;
    border-radius: 9999px;
}
.fill-high { background-color: #10b981; }
.fill-medium { background-color: #f59e0b; }
.fill-low { background-color: #ef4444; }

.metric-table table {
    font-size: 0.85rem !important;
}
.source-card {
    border: 1px solid var(--border-color-primary, #e2e8f0) !important;
    border-radius: 8px !important;
    margin-bottom: 16px !important;
    overflow: hidden !important;
    background: white !important;
}
.source-card .metric-table {
    margin: 0 !important;
}
.source-card .metric-table thead {
    background: white !important;
}
.source-card .metric-table th {
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    border-bottom: 1px solid var(--border-color-primary, #e2e8f0) !important;
}
.source-card .metric-table td, 
.source-card .metric-table th {
    border-right: none !important;
}
.source-card .metric-table {
    overflow-x: hidden !important;
}
.source-card .metric-table table {
    width: 100% !important;
}
.source-card .metric-table ::-webkit-scrollbar {
    display: none !important;
}

/* --- LOADER & SPINNER --- */
.loader-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px;
    background: var(--background-fill-secondary, #f1f5f9);
    border-radius: 12px;
    border: 1px solid var(--border-color-primary, #e2e8f0);
    margin: 20px 0;
}
.spinner {
    width: 40px;
    height: 40px;
    border: 4px solid #e2e8f0;
    border-top: 4px solid var(--primary-500, #3b82f6);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 16px;
}
@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
.loader-text {
    font-weight: 600;
    color: var(--body-text-color, #1e293b);
    margin-bottom: 4px;
}

/* --- DATAFRAME WRAPPING --- */
.metric-table td {
    white-space: normal !important;
    word-break: break-word !important;
    line-height: 1.4 !important;
    vertical-align: top !important;
    min-width: 120px;
}
.metric-table td div {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
}

#data_root_upload {
    border: 1px dashed var(--border-color-primary, #e2e8f0) !important;
    border-radius: 12px !important;
    background: var(--background-fill-secondary, #f8fafc) !important;
}
.change-source-btn {
    margin-bottom: 16px !important;
    font-size: 0.85rem !important;
}
"""

# JavaScript to force light mode by appending the __theme=light query parameter
force_light_mode_js = """
<script>
    (function() {
        const url = new URL(window.location.href);
        if (url.searchParams.get('__theme') !== 'light') {
            url.searchParams.set('__theme', 'light');
            window.location.replace(url.toString());
        }
    })();
</script>
"""
