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
    line = "#60a5fa" if dark else "#2563eb"
    text = "#f3f4f6" if dark else "#111827"
    node_bkg = "#1e293b" if dark else "#f8fafc"
    node_border = "#3b82f6" if dark else "#94a3b8"
    
    variables = {
        "fontSize": "13px",
        "fontFamily": "sans-serif",
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
    
    # CSS overrides inside iframe to force arrows and paths to be brightly visible
    extra_css = f"""
      .edgePath path.path {{
        stroke: {line} !important;
        stroke-width: 2px !important;
      }}
      .marker, marker path, marker polygon {{
        fill: {line} !important;
        stroke: {line} !important;
      }}
      .node rect, .node circle, .node polygon {{
        fill: {node_bkg} !important;
        stroke: {node_border} !important;
        stroke-width: 1.5px !important;
      }}
      .node .label {{
        color: {text} !important;
      }}
    """
    
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
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
          overflow: auto;
        }}
        .mermaid {{
          display: flex;
          justify-content: center;
        }}
        .mermaid svg {{
          max-width: 100% !important;
          height: auto !important;
        }}
        {extra_css}
      </style>
      <script src="https://cdnjs.cloudflare.com/ajax/libs/mermaid/10.9.0/mermaid.min.js"></script>
    </head>
    <body>
      <div class="mermaid">
{html.escape(code)}
      </div>
      <script>
        mermaid.initialize({{
          startOnLoad: true,
          theme: '{theme}',
          themeVariables: {json.dumps(variables)},
          flowchart: {{
            curve: 'basis',
            useMaxWidth: false,
            htmlLabels: true
          }}
        }});
      </script>
    </body>
    </html>
    """
    components.html(body, height=height, scrolling=True)
