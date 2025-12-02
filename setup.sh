#!/bin/bash
# Setup script for Student Loan Document Extractor Platform (Linux/macOS)

set -e

echo "========================================"
echo "Student Loan Document Extractor Setup"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.10 or higher"
    exit 1
fi

echo "[1/5] Python found"
python3 --version
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "[2/5] Creating virtual environment..."
    python3 -m venv venv
    echo "Virtual environment created"
else
    echo "[2/5] Virtual environment already exists"
fi
echo ""

# Activate virtual environment and install dependencies
echo "[3/5] Installing dependencies..."
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
echo ""

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "[4/5] Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file with your configuration"
else
    echo "[4/5] .env file already exists"
fi
echo ""

# Verify setup
echo "[5/5] Verifying setup..."
python scripts/verify_setup.py
echo ""

echo "========================================"
echo "Setup complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Install system dependencies:"
echo "   Ubuntu/Debian: sudo apt-get install tesseract-ocr poppler-utils"
echo "   macOS: brew install tesseract poppler"
echo "3. Start services with: docker-compose up -d"
echo "   OR run locally:"
echo "   - API: uvicorn src.api.main:app --reload"
echo "   - Dashboard: streamlit run dashboard/app.py"
echo ""
