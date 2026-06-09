@echo off
echo === Mission Control AI Setup ===
echo.

:: Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

:: Install dependencies
echo Installing dependencies...
venv\Scripts\pip.exe install -r requirements.txt --quiet

echo.
echo === Setup complete! ===
echo.
echo To run the server:
echo   venv\Scripts\python.exe -m mission_control.main
echo.
echo Or use: start.bat
pause
