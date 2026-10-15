"""Mermaid-диаграммы, адаптирующиеся к теме Streamlit (light/dark)."""

import html
import json

import streamlit as st
import streamlit.components.v1 as components


def _is_dark_theme() -> bool:
    # Streamlit 1.45+: st.context.theme отражает АКТИВНУЮ тему (в т.ч. системную).
    try:
        theme = getattr(getattr(st, "context", None), "theme", None)
        t = getattr(theme, "type", None)
        if t:
            return str(t).lower() == "dark"
    except Exception:
        pass
    # Fallback для старых версий.
    return (st.get_option("theme.base") or "light").lower() == "dark"


def render_mermaid(code: str, height: int = 420):
    dark = _is_dark_theme()
    theme = "dark" if dark else "default"
    line = "#38bdf8" if dark else "#0284c7"
    text = "#f8fafc" if dark else "#0f172a"
    node_bkg = "#1e293b" if dark else "#ffffff"
    node_border = "#0284c7" if dark else "#94a3b8"
    
    variables = {
        "fontSize": "13px",
        "fontFamily": "-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif",
        "primaryColor": node_bkg,
        "primaryTextColor": text,
        "primaryBorderColor": node_border,
        "lineColor": line,
        "arrowheadColor": line,
        "edgeLabelBackground": node_bkg,
        "textColor": text,
        "clusterBkg": node_bkg,
        "clusterBorder": node_border,
    }
    
    extra_css = f"""
      html, body {{
        background: transparent !important;
        color: {text} !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      }}
      .mermaid {{
        display: flex !important;
        justify-content: center !important;
        background: transparent !important;
        min-height: 100px;
      }}
      .mermaid svg {{
        max-width: 100% !important;
        width: 100% !important;
        height: auto !important;
        display: block !important;
      }}
      .edgePath .path, .edgePath path, path.flowchart-link {{
        stroke: {line} !important;
        stroke-width: 2.5px !important;
      }}
      .marker, marker path, marker polygon, #flowchart-pointEnd, #flowchart-pointStart {{
        fill: {line} !important;
        stroke: {line} !important;
      }}
      .node rect, .node circle, .node polygon, .node path {{
        fill: {node_bkg} !important;
        stroke: {node_border} !important;
        stroke-width: 2px !important;
      }}
      .node .label, .node span, .node div, text {{
        color: {text} !important;
        fill: {text} !important;
      }}
      #error-svg {{
        background: #fee2e2;
        color: #991b1b;
        padding: 10px;
        border-radius: 6px;
      }}
    """
    
    raw_code_js = json.dumps(code)
    
    body = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8" />
      <style>
        body {{
          margin: 0;
          padding: 10px;
          background: transparent;
          overflow: auto;
        }}
        {extra_css}
      </style>
      <script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.0/dist/mermaid.min.js"></script>
    </head>
    <body>
      <div id="mermaid-container" class="mermaid"></div>
      <div id="diag-error" style="display:none; color:#ef4444; font-family:monospace; padding:10px;"></div>
      <script>
        const graphDefinition = {raw_code_js};
        mermaid.initialize({{
          startOnLoad: false,
          theme: '{theme}',
          themeVariables: {json.dumps(variables)},
          flowchart: {{
            curve: 'basis',
            useMaxWidth: true,
            htmlLabels: true
          }}
        }});
        
        async function renderGraph() {{
          const container = document.getElementById('mermaid-container');
          try {{
            // Generate unique ID for each render
            const id = 'mermaid-svg-' + Math.random().toString(36).substring(2, 9);
            const {{ svg }} = await mermaid.render(id, graphDefinition);
            container.innerHTML = svg;
            const svgEl = container.querySelector('svg');
            if (svgEl) {{
              svgEl.removeAttribute('width');
              svgEl.removeAttribute('height');
              svgEl.style.width = '100%';
              svgEl.style.maxWidth = '100%';
              svgEl.style.height = 'auto';
            }}
          }} catch (err) {{
            console.error('Mermaid error:', err);
            document.getElementById('diag-error').style.display = 'block';
            document.getElementById('diag-error').innerText = 'Mermaid render error: ' + err.message;
          }}
        }}

        // If iframe is initially hidden inside a tab, re-render when visible
        if (document.hidden) {{
          document.addEventListener('visibilitychange', () => {{
            if (!document.hidden) renderGraph();
          }});
        }}
        window.addEventListener('resize', renderGraph);

        // Multiple attempts to ensure layout engine has computed container width
        renderGraph();
        setTimeout(renderGraph, 500);
        setTimeout(renderGraph, 1500);
      </script>
    </body>
    </html>
    """
    components.html(body, height=height, scrolling=True)
