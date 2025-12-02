@echo off
REM MLOps Pipeline Initialization Script
REM Student Loan Document Extractor

echo ========================================
echo MLOps Pipeline Initialization
echo ========================================
echo.

REM Check if .env exists
if not exist .env (
    echo [1/6] Creating .env from .env.example...
    copy .env.example .env
    echo DONE: Please edit .env with your actual values
    echo.
) else (
    echo [1/6] .env already exists, skipping...
    echo.
)

REM Create required directories
echo [2/6] Creating required directories...
if not exist logs mkdir logs
if not exist "data\raw" mkdir "data\raw"
if not exist "data\processed" mkdir "data\processed"
if not exist "logs\reports" mkdir "logs\reports"
echo DONE
echo.

REM Set permissions (Windows doesn't need chmod)
echo [3/6] Setting up directory permissions...
echo DONE (Not required on Windows)
echo.

REM Initialize Airflow
echo [4/6] Starting Docker services...
docker-compose up -d
echo DONE
echo.

echo [5/6] Waiting for services to be healthy...
timeout /t 30 /nobreak >nul
echo DONE
echo.

echo [6/6] Checking service status...
docker-compose ps
echo.

echo ========================================
echo Initialization Complete!
echo ========================================
echo.
echo Services running:
echo - Airflow UI:     http://localhost:8080  (admin/admin123)
echo - API:            http://localhost:8000
echo - Dashboard:      http://localhost:8501
echo - MinIO Console:  http://localhost:9001  (minioadmin/minioadmin123)
echo.
echo Next steps:
echo 1. Edit .env file with your actual configuration
echo 2. Access Airflow UI at http://localhost:8080
echo 3. Trigger the pipeline DAG: document_processing_pipeline
echo.
echo For troubleshooting, see MLOPS_PHASE1_README.md
echo.

pause
