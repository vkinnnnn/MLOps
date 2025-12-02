# Multi-stage Dockerfile for Student Loan Document Extractor Platform
FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    libtesseract-dev \
    poppler-utils \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app/

# Create necessary directories
RUN mkdir -p /app/uploads /app/temp /app/processing

# Set environment variables
ENV PYTHONUNBUFFERED=1
# Ensure Python can import the API package under src/ as `api`
ENV PYTHONPATH=/app:/app/src

# API Service Stage
FROM base as api
EXPOSE 8000
# Run the FastAPI app defined in src/api/main.py (imported as `src.api.main`)
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Dashboard Service Stage
FROM base as dashboard
EXPOSE 8501
CMD ["streamlit", "run", "dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0"]

# Worker Service Stage
FROM base as worker
CMD ["python", "-m", "worker.processor"]
