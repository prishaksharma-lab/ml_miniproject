@echo off
echo Starting NASA C-MAPSS Turbofan Health Telemetry Dashboard...
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Project virtual environment not found. Create it with: python -m venv .venv
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -m streamlit run app.py --server.port 8501
pause
