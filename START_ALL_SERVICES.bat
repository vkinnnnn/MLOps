@echo off
echo ========================================
echo Starting DocAI EXTRACTOR Full Stack Application
echo ========================================
echo.

REM Project root is the folder where this script resides
set ROOT=%~dp0

echo [1/2] Starting FastAPI Backend on port 8000...
REM Use the refactored DocAI EXTRACTOR entrypoint under src.api.main:app
start "DocAI Backend" cmd /k "cd /d \"%ROOT%\" && python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

echo [2/2] Starting Frontend on port 3000...
start "DocAI Frontend" cmd /k "cd /d \"%ROOT%frontend\" && npm run dev"

timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo All Services Started!
echo ========================================
echo.
echo Backend API:  http://localhost:8000
echo API Docs:     http://localhost:8000/docs
echo Frontend App: http://localhost:3000
echo.
echo Press Ctrl+C in each window to stop services
echo ========================================
