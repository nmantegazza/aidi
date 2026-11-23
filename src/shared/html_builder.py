import markdown
import uuid

CSS_STYLES = """
<style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 1200px; margin: 0 auto; padding: 20px; }
    table { border-collapse: collapse; width: 100%; margin: 20px 0; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    th { background-color: #f4f4f4; }
    h1, h2, h3 { color: #2c3e50; border-bottom: 1px solid #eee; padding-bottom: 5px; }
    hr { border: 0; border-top: 1px solid #eee; margin: 40px 0; }
    .mermaid-wrapper { background-color: white; padding: 20px; border: 1px solid #e0e0e0; border-radius: 5px; margin-bottom: 10px; }
    .side-by-side { display: flex; flex-direction: row; gap: 20px; align-items: flex-start; }
    .flex-col { flex: 1; min-width: 0; }
    .llm-reasoning {
        background-color: #f8f9fa;
        border-left: 4px solid #6c757d;
        padding: 15px;
        margin: 15px 0;
        border-radius: 0 4px 4px 0;
        font-size: 0.95em;
    }
    .llm-reasoning-header {
        font-weight: bold;
        color: #495057;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .source-insight-table { font-size: 0.85em; }
    .mapping-table th { background-color: #e9ecef; }
    .preview-container { display: flex; gap: 20px; margin-top: 10px; overflow-x: auto; }
    .preview-box { flex: 1; min-width: 400px; }
    .preview-box h5 { margin-top: 0; color: #666; }
</style>
"""

def render_markdown_to_html(md_content: str) -> str:
    """Converts a markdown string to HTML using the python-markdown library."""
    return markdown.markdown(md_content, extensions=['extra', 'toc'])

def render_mermaid_to_html(mermaid_code: str) -> str:
    """Returns an HTML snippet that renders the mermaid code using a CDN-loaded Mermaid library."""
    unique_id = f"mermaid-graph-{uuid.uuid4()}"
    svg_output_id = f"mermaid-svg-output-{uuid.uuid4()}"
    
    escaped_mermaid_code = mermaid_code.replace("`", "\\`").replace("\n", "\\n")
    return f"""<div class="mermaid-wrapper">
    <div id="{svg_output_id}"></div>
</div>
<script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
    mermaid.initialize({{ startOnLoad: false, theme: 'default' }});
    const {{ svg }} = await mermaid.render('{unique_id}', `{escaped_mermaid_code}`);
    document.getElementById('{svg_output_id}').innerHTML = svg;
</script>"""

def build_html_document(title: str, body_html: str, extra_head: str = "", extra_body: str = "") -> str:
    """
    Wraps the provided HTML body content within a standard HTML5 document skeleton,
    injecting consistent CSS styling.
    """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    {CSS_STYLES}
    {extra_head}
</head>
<body>
    {body_html}
    {extra_body}
</body>
</html>
"""
