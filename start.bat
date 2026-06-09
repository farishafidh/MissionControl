@echo off
echo Starting Mission Control AI...
echo.
cd /d "%~dp0"
venv\Scripts\python.exe -m mission_control.main
