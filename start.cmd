@echo off
title Portfolio hub (local)
cd /d "%~dp0"
echo Starting portfolio hub on http://localhost:8501 ...
python -m streamlit run hub/Home.py
pause
