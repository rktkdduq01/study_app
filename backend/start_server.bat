@echo off
echo Starting EduRPG Backend Server...
cd /d "%~dp0"

echo Installing dependencies...
pip install -r requirements-dev.txt

echo.
echo Starting server...
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause