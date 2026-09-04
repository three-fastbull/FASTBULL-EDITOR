@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\setup_fastbull_windows.ps1"
if errorlevel 1 pause
