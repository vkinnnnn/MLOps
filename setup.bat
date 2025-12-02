@echo off
REM Setup script for Student Loan Document Extractor Platform (Windows)

echo ========================================
echo Student Loan Document Extractor Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10 or higher from https://www.python.org/
    pause
    exit /b 1
)

echo [1/5] Python found
python --version
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo [2/5] Creating virtual environment...
    python -m venv venv
    echo Virtual environment created
) else (
    echo [2/5] Virtual environment already exists
)
echo.

REM Activate virtual environment and install dependencies
echo [3/5] Installing dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
echo.

REM Copy environment file if it doesn't exist
if not exist ".env" (
    echo [4/5] Creating .env file from template...
    copy .env.example .env
    echo Please edit .env file with your configuration
) else (
    echo [4/5] .env file already exists
)
echo.

REM Verify setup
echo [5/5] Verifying setup...
python scripts\verify_setup.py
echo.

echo ========================================
echo Setup complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file with your configuration
echo 2. Install Tesseract OCR from: https://github.com/UB-Mannheim/tesseract/wiki
echo 3. Start services with: docker-compose up -d
echo    OR run locally:
echo    - API: uvicorn src.api.main:app --reload
echo    - Dashboard: streamlit run dashboard/app.py
echo.
pause
