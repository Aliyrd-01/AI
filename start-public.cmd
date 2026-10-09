@echo off
title Portfolio hub (public link)
cd /d "%~dp0"
echo Opening a public trycloudflare URL for the hub...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\serve_public.ps1"
pause
