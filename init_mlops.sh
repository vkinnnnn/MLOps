#!/bin/bash
# MLOps Pipeline Initialization Script
# Student Loan Document Extractor

set -e  # Exit on error

echo "========================================"
echo "MLOps Pipeline Initialization"
echo "========================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "[1/7] Creating .env from .env.example..."
    cp .env.example .env
    echo "DONE: Please edit .env with your actual values"
    echo ""
else
    echo "[1/7] .env already exists, skipping..."
    echo ""
fi

# Create required directories
echo "[2/7] Creating required directories..."
mkdir -p logs data/raw data/processed logs/reports
echo "DONE"
echo ""

# Set permissions
echo "[3/7] Setting directory permissions..."
chmod 777 logs data
echo "DONE"
echo ""

# Set AIRFLOW_UID
echo "[4/7] Configuring Airflow UID..."
if ! grep -q "AIRFLOW_UID" .env; then
    echo "AIRFLOW_UID=$(id -u)" >> .env
    echo "DONE: Set AIRFLOW_UID=$(id -u)"
else
    echo "DONE: AIRFLOW_UID already set"
fi
echo ""

# Start Docker services
echo "[5/7] Starting Docker services..."
docker-compose up -d
echo "DONE"
echo ""

# Wait for services
echo "[6/7] Waiting for services to be healthy (30 seconds)..."
sleep 30
echo "DONE"
echo ""

# Check service status
echo "[7/7] Checking service status..."
docker-compose ps
echo ""

echo "========================================"
echo "Initialization Complete!"
echo "========================================"
echo ""
echo "Services running:"
echo "- Airflow UI:     http://localhost:8080  (admin/admin123)"
echo "- API:            http://localhost:8000"
echo "- Dashboard:      http://localhost:8501"
echo "- MinIO Console:  http://localhost:9001  (minioadmin/minioadmin123)"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your actual configuration"
echo "2. Access Airflow UI at http://localhost:8080"
echo "3. Trigger the pipeline DAG: document_processing_pipeline"
echo ""
echo "For troubleshooting, see MLOPS_PHASE1_README.md"
echo ""
