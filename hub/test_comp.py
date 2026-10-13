import streamlit as st
import streamlit.components.v1 as components

st.title("Component Test")

html = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
</head>
<body style="background:#111827; color:#fff; padding:10px;">
<div class="mermaid">
flowchart TD
  A[Node 1] --> B[Node 2]
</div>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.0/dist/mermaid.min.js"></script>
<script>
  mermaid.initialize({ startOnLoad: true, theme: 'dark' });
</script>
</body>
</html>
"""

components.html(html, height=200)
st.write("Below component")
