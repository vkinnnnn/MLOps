#!/usr/bin/env python3
"""
Automated Integration Script for Lab3 Extractor → LoanQA-MLOps
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LoanQAIntegrator:
    """Automate Lab3 extractor integration with LoanQA-MLOps"""
    
    def __init__(self, loanqa_path: str):
        self.lab3_root = Path(__file__).parent.parent
        self.loanqa_root = Path(loanqa_path)
        self.integration_dir = self.loanqa_root / "integrations" / "lab3-extractor"
    
    def validate_paths(self) -> bool:
        """Validate source and destination paths"""
        if not self.lab3_root.exists():
            logger.error(f"Lab3 root not found: {self.lab3_root}")
            return False
        
        if not self.loanqa_root.exists():
            logger.error(f"LoanQA root not found: {self.loanqa_root}")
            logger.info("Please clone LoanQA-MLOps first:")
            logger.info("  git clone https://github.com/nkousik18/LoanQA-MLOps.git")
            return False
        
        return True
    
    def create_directory_structure(self):
        """Create integration directory structure"""
        logger.info("Creating directory structure...")
        
        dirs = [
            self.integration_dir,
            self.integration_dir / "processing",
            self.integration_dir / "extraction",
            self.integration_dir / "api",
            self.integration_dir / "storage" / "migrations",
            self.integration_dir / "normalization",
            self.integration_dir / "mlops",  # MLOps modules for DAG
            self.integration_dir / "dags",   # Airflow DAGs
            self.integration_dir / "tests",
            self.integration_dir / "docs",
            self.integration_dir / "scripts",
        ]
        
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"  Created: {dir_path.relative_to(self.loanqa_root)}")
    
    def copy_files(self):
        """Copy Lab3 files to LoanQA integration directory"""
        logger.info("Copying Lab3 files...")
        
        file_mappings = [
            # Processing
            ("processing", "processing", ["*.py"]),
            # Extraction
            ("src/extraction", "extraction", ["*.py"]),
            # API
            ("src/api", "api", ["routes.py", "document_ingestion.py", "batch_processor.py", "models.py"]),
            # Storage
            ("storage", "storage", ["*.py"]),
            ("storage/migrations", "storage/migrations", ["*.sql"]),
            # Normalization
            ("normalization", "normalization", ["*.py"]),
            # MLOps modules (for DAG)
            ("mlops", "mlops", ["*.py"]),
            # DAG files
            ("dags", "dags", ["Doc_process_Dag.py", "__init__.py"]),
            # Scripts
            ("scripts", "scripts", ["setup_integration.py", "test_*.py"]),
        ]
        
        # Exclude .md files from copying
        exclude_patterns = ["*.md", "*.MD"]
        
        for src_rel, dst_rel, patterns in file_mappings:
            src_dir = self.lab3_root / src_rel
            dst_dir = self.integration_dir / dst_rel
            
            if not src_dir.exists():
                logger.warning(f"  Source not found: {src_dir}")
                continue
            
            for pattern in patterns:
                for file_path in src_dir.glob(pattern):
                    if file_path.is_file():
                        # Skip .md files
                        if file_path.suffix.lower() in ['.md', '.MD']:
                            logger.debug(f"  Skipped .md file: {file_path.name}")
                            continue
                        dst_file = dst_dir / file_path.name
                        shutil.copy2(file_path, dst_file)
                        logger.info(f"  Copied: {file_path.name}")
    
    def create_adapter(self):
        """Create integration adapter"""
        logger.info("Creating integration adapter...")
        
        adapter_code = '''"""
Adapter to integrate Lab3 Document Extractor with LoanQA-MLOps
"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class Lab3ExtractorAdapter:
    """Adapter for Lab3 Document Extractor"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize Lab3 services"""
        from .processing.complete_document_extractor import CompleteDocumentExtractor
        from .storage.storage_service import StorageService
        
        self.extractor = CompleteDocumentExtractor()
        self.storage = StorageService()
        logger.info("Lab3 Extractor initialized")
    
    async def extract_document(
        self, 
        file_data: bytes, 
        file_name: str,
        mime_type: str
    ) -> Dict[str, Any]:
        """Extract document"""
        result = self.extractor.extract_complete_document(
            file_data, mime_type, file_name
        )
        
        document_id = self.storage.store_document(
            file_data=file_data,
            file_name=file_name,
            file_type=mime_type
        )
        
        result['document_id'] = document_id
        return result
'''
        
        adapter_file = self.integration_dir / "adapter.py"
        adapter_file.write_text(adapter_code, encoding='utf-8')
        logger.info(f"  Created: adapter.py")
    
    def create_dockerfile(self):
        """Create Dockerfile for Lab3 extractor"""
        logger.info("Creating Dockerfile...")

        
        dockerfile_content = '''FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc postgresql-client && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
'''
        
        dockerfile = self.integration_dir / "Dockerfile"
        dockerfile.write_text(dockerfile_content, encoding='utf-8')
        logger.info(f"  Created: Dockerfile")
    
    def create_requirements(self):
        """Create requirements.txt"""
        logger.info("Creating requirements.txt...")
        
        # Copy from Lab3 requirements
        src_req = self.lab3_root / "requirements.txt"
        dst_req = self.integration_dir / "requirements.txt"
        
        if src_req.exists():
            shutil.copy2(src_req, dst_req)
            logger.info(f"  Created: requirements.txt")
        else:
            logger.warning("  requirements.txt not found in Lab3")
    
    def update_docker_compose(self):
        """Update docker-compose.yml"""
        logger.info("Updating docker-compose.yml...")
        
        docker_compose_addition = '''
  # Lab3 Document Extractor
  lab3-extractor-api:
    build:
      context: ./integrations/lab3-extractor
      dockerfile: Dockerfile
    ports:
      - "8100:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/gcp-key.json
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./credentials:/app/credentials:ro
    depends_on:
      - postgres
      - redis
    networks:
      - loanqa-network

  lab3-chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8101:8000"
    volumes:
      - chromadb-data:/chroma/chroma
    networks:
      - loanqa-network
'''
        
        compose_file = self.loanqa_root / "docker-compose.yml"
        if compose_file.exists():
            logger.info("  Please manually add Lab3 services to docker-compose.yml")
            logger.info("  See LOANQA_MLOPS_INTEGRATION_GUIDE.md for details")
        else:
            logger.warning("  docker-compose.yml not found")
    
    def create_env_template(self):
        """Create .env.example additions"""
        logger.info("Creating environment template...")
        
        env_additions = '''
# Lab3 Extractor Configuration
LAB3_EXTRACTOR_ENABLED=true
LAB3_API_URL=http://lab3-extractor-api:8000
LAB3_CHROMADB_URL=http://lab3-chromadb:8000

# Google Cloud Document AI - All Three Processors Required
# Form Parser: Specialized in structured forms and tables
DOCUMENT_AI_FORM_PARSER_ID=337aa94aac26006
# Document OCR: General text extraction
DOCUMENT_AI_DOC_OCR_ID=c0c01b0942616db6
# Layout Parser: Complex nested document structures
DOCUMENT_AI_LAYOUT_PARSER_ID=41972eaa15f517f2

# Google Cloud Configuration
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/gcp-key.json
GOOGLE_CLOUD_PROJECT=your-project-id

# Storage
LAB3_MINIO_ENDPOINT=minio:9000
LAB3_MINIO_ACCESS_KEY=minioadmin
LAB3_MINIO_SECRET_KEY=minioadmin
LAB3_MINIO_BUCKET=lab3-documents
'''
        
        env_file = self.integration_dir / ".env.lab3.example"
        env_file.write_text(env_additions, encoding='utf-8')
        logger.info(f"  Created: .env.lab3.example")
    
    def create_dag_integration_guide(self):
        """Create DAG integration guide"""
        logger.info("Creating DAG integration guide...")
        
        guide_content = '''# Airflow DAG Integration Guide for LoanQA-MLOps

## Overview

This guide explains how to integrate the complete 10-step MLOps pipeline DAG (`Doc_process_Dag.py`) into the LoanQA-MLOps repository.

## DAG Pipeline Steps

The DAG orchestrates the following 10-step pipeline:

1. **acquire_documents** - Fetch pending documents from database
2. **validate_documents** - Validate file integrity and format
3. **preprocess_documents** - Clean, normalize, optimize documents
4. **extract_with_document_ai** - OCR + Entity extraction using Google Document AI
5. **extract_entities** - Extract loan-specific fields
6. **normalize_data** - Standardize data to schema
7. **generate_embeddings** - Chunk document and create vector embeddings
8. **detect_anomalies** - Detect unusual patterns in data (parallel)
9. **detect_bias** - Check for discriminatory content (parallel)
10. **store_results** - Save all results to PostgreSQL

## Integration Steps

### Step 1: Copy DAG to LoanQA-MLOps

The DAG file has been copied to:
```
integrations/lab3-extractor/dags/Doc_process_Dag.py
```

### Step 2: Copy MLOps Modules

The MLOps modules have been copied to:
```
integrations/lab3-extractor/mlops/
├── data_acquisition.py
├── preprocessing.py
├── validation.py
├── anomaly_detection.py
└── bias_detection.py
```

### Step 3: Update Airflow Configuration

Add the following to your `docker-compose.yml` in LoanQA-MLOps:

```yaml
services:
  # Airflow Webserver
  airflow-webserver:
    image: apache/airflow:2.7.3-python3.11
    environment:
      # ... existing environment variables ...
      # Add Lab3 DAG paths
      AIRFLOW__CORE__DAGS_FOLDER: /opt/airflow/dags
    volumes:
      - ./integrations/lab3-extractor/dags:/opt/airflow/dags/lab3
      - ./integrations/lab3-extractor/mlops:/opt/airflow/mlops
      - ./integrations/lab3-extractor/processing:/opt/airflow/processing
      - ./integrations/lab3-extractor/src:/opt/airflow/src
      - ./integrations/lab3-extractor/normalization:/opt/airflow/normalization
      - ./integrations/lab3-extractor/storage:/opt/airflow/storage
    depends_on:
      - postgres
      - redis
      - minio

  # Airflow Scheduler
  airflow-scheduler:
    image: apache/airflow:2.7.3-python3.11
    environment:
      # ... same as webserver ...
    volumes:
      # ... same as webserver ...
```

### Step 4: Update DAG Paths

The DAG uses these path configurations:
```python
sys.path.insert(0, '/opt/airflow')
sys.path.insert(0, '/opt/airflow/mlops')
sys.path.insert(0, '/opt/airflow/processing')
sys.path.insert(0, '/opt/airflow/src')
```

Ensure these paths match your volume mounts.

### Step 5: Configure Environment Variables

Add to your `.env` file:
```bash
# Airflow Configuration
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow123@airflow-db:5432/airflow
AIRFLOW__CORE__FERNET_KEY=your-fernet-key-here

# DAG Configuration
API_BASE_URL=http://api:8000
CHROMADB_HOST=chromadb
CHROMADB_PORT=8001
DATABASE_URL=postgresql://loanuser:loanpass123@postgres:5432/loanqa
```

### Step 6: Install Dependencies

Add to your Airflow requirements:
```txt
requests>=2.31.0
psycopg2-binary>=2.9.0
boto3>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
Pillow>=10.0.0
pdf2image>=1.16.0
```

### Step 7: Initialize Airflow Database

```bash
docker-compose run airflow-webserver airflow db init
docker-compose run airflow-webserver airflow users create \
  --username admin \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@example.com \
  --password admin123
```

### Step 8: Start Services

```bash
docker-compose up -d airflow-webserver airflow-scheduler
```

### Step 9: Access Airflow UI

Open http://localhost:8080 and log in with:
- Username: `admin`
- Password: `admin123`

### Step 10: Enable and Test DAG

1. In Airflow UI, find the `Doc_process_Dag` DAG
2. Toggle it ON (unpause)
3. Trigger a test run manually
4. Monitor execution in the Graph View

## DAG Schedule

The DAG is configured to run every 5 minutes:
```python
schedule_interval=timedelta(minutes=5)
```

You can modify this in the DAG file if needed.

## Task Dependencies

```
acquire_documents
      |
      v
validate_documents
      |
      v
preprocess_documents
      |
      v
extract_with_document_ai
      |
      v
extract_entities
      |
      v
normalize_data
      |
      ├─────────────┬─────────────┐
      v             v             v
generate_embeddings  detect_anomalies  detect_bias
      |             |             |
      └─────────────┴─────────────┘
                    |
                    v
              store_results
```

## Troubleshooting

### DAG Not Appearing

1. Check DAG file is in correct location
2. Verify Python syntax: `python -m py_compile dags/Doc_process_Dag.py`
3. Check Airflow logs: `docker-compose logs airflow-scheduler`

### Import Errors

1. Verify all modules are in correct paths
2. Check sys.path in DAG file matches volume mounts
3. Ensure all dependencies are installed

### Task Failures

1. Check task logs in Airflow UI
2. Verify API endpoints are accessible
3. Check database connections
4. Verify environment variables are set

## Monitoring

Monitor DAG execution:
- Airflow UI: http://localhost:8080
- Task logs: Available in Airflow UI for each task
- Database: Check `airflow` database for execution metadata

## Next Steps

After successful integration:
1. Configure email notifications for failures
2. Set up monitoring and alerting
3. Tune retry and timeout settings
4. Add custom operators if needed
5. Integrate with monitoring tools (Prometheus, Grafana)

## Support

For issues:
1. Check Airflow logs
2. Review DAG code
3. Verify all services are running
4. Check environment variables
'''
        
        guide_file = self.integration_dir / "DAG_INTEGRATION_GUIDE.md"
        guide_file.write_text(guide_content, encoding='utf-8')
        logger.info(f"  Created: DAG_INTEGRATION_GUIDE.md")
    
    def run_integration(self):
        """Run complete integration"""
        logger.info("="*60)
        logger.info("Lab3 → LoanQA-MLOps Integration")
        logger.info("="*60)
        
        # Step 1: Validate
        if not self.validate_paths():
            return False
        
        # Step 2: Create structure
        self.create_directory_structure()
        
        # Step 3: Copy files
        self.copy_files()
        
        # Step 4: Create adapter
        self.create_adapter()
        
        # Step 5: Create Dockerfile
        self.create_dockerfile()
        
        # Step 6: Create requirements
        self.create_requirements()
        
        # Step 7: Update docker-compose
        self.update_docker_compose()
        
        # Step 8: Create env template
        self.create_env_template()
        
        # Step 9: Create DAG integration instructions
        self.create_dag_integration_guide()
        
        logger.info("="*60)
        logger.info("Integration Complete!")
        logger.info("="*60)
        logger.info("")
        logger.info("Next Steps:")
        logger.info("1. Review LOANQA_MLOPS_INTEGRATION_GUIDE.md")
        logger.info("2. Review DAG_INTEGRATION_GUIDE.md for Airflow setup")
        logger.info("3. Update docker-compose.yml with Lab3 services")
        logger.info("4. Configure environment variables")
        logger.info("5. Run: docker-compose build")
        logger.info("6. Run: docker-compose up -d")
        logger.info("7. Test: curl http://localhost:8100/api/v1/health")
        logger.info("8. Access Airflow UI: http://localhost:8080")
        logger.info("")
        
        return True


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python integrate_with_loanqa.py <path-to-loanqa-mlops>")
        print("")
        print("Example:")
        print("  python integrate_with_loanqa.py C:/Projects/LoanQA-MLOps")
        sys.exit(1)
    
    loanqa_path = sys.argv[1]
    
    integrator = LoanQAIntegrator(loanqa_path)
    success = integrator.run_integration()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
