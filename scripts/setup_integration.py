"""
Setup Script for LoanQA Integration
Runs database migrations and initializes vector store
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import psycopg2
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_environment():
    """Load environment variables"""
    env_path = project_root / '.env'
    if not env_path.exists():
        logger.error(f".env file not found at {env_path}")
        logger.info("Please copy .env.example to .env and configure")
        return False
    
    load_dotenv(env_path)
    logger.info("Environment variables loaded")
    return True


def check_database_connection():
    """Check if database is accessible"""
    try:
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            # Build from components
            db_url = (
                f"postgresql://{os.getenv('POSTGRES_USER', 'loanuser')}:"
                f"{os.getenv('POSTGRES_PASSWORD', 'loanpass123')}@"
                f"localhost:{os.getenv('POSTGRES_PORT', '5433')}/"
                f"{os.getenv('POSTGRES_DB', 'loanextractor')}"
            )
        
        conn = psycopg2.connect(db_url)
        conn.close()
        logger.info("✅ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        logger.info("Please ensure PostgreSQL is running (docker-compose up db)")
        return False


def run_migration():
    """Run database migration for vector tables"""
    try:
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            db_url = (
                f"postgresql://{os.getenv('POSTGRES_USER', 'loanuser')}:"
                f"{os.getenv('POSTGRES_PASSWORD', 'loanpass123')}@"
                f"localhost:{os.getenv('POSTGRES_PORT', '5433')}/"
                f"{os.getenv('POSTGRES_DB', 'loanextractor')}"
            )
        
        # Read migration file
        migration_file = project_root / 'storage' / 'migrations' / '001_add_vector_tables.sql'
        
        if not migration_file.exists():
            logger.error(f"Migration file not found: {migration_file}")
            return False
        
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        # Execute migration
        logger.info("Running database migration...")
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        cur.execute(migration_sql)
        conn.commit()
        
        cur.close()
        conn.close()
        
        logger.info("✅ Database migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False


def check_chromadb():
    """Check if ChromaDB is accessible"""
    try:
        import chromadb
        from chromadb.config import Settings
        
        host = os.getenv('CHROMADB_HOST', 'localhost')
        port = int(os.getenv('CHROMADB_PORT', '8001'))
        
        client = chromadb.HttpClient(
            host=host,
            port=port,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Test connection
        client.heartbeat()
        
        logger.info(f"✅ ChromaDB connection successful (http://{host}:{port})")
        return True
        
    except Exception as e:
        logger.error(f"❌ ChromaDB connection failed: {e}")
        logger.info("Please ensure ChromaDB is running:")
        logger.info("  Option 1: docker-compose up chromadb")
        logger.info("  Option 2: docker run -p 8001:8000 chromadb/chroma")
        return False


def check_api_keys():
    """Check if API keys are configured"""
    openai_key = os.getenv('OPENAI_API_KEY', '')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY', '')
    
    issues = []
    
    if not openai_key or openai_key == 'your-openai-api-key-here':
        issues.append("⚠️  OpenAI API key not configured")
    else:
        logger.info("✅ OpenAI API key found")
    
    if not anthropic_key or anthropic_key == 'your-anthropic-api-key-here':
        issues.append("⚠️  Anthropic API key not configured")
    else:
        logger.info("✅ Anthropic API key found")
    
    if issues:
        logger.warning("API Keys Issues:")
        for issue in issues:
            logger.warning(f"  {issue}")
        logger.info("\nTo add API keys, edit .env file:")
        logger.info("  OPENAI_API_KEY=sk-...")
        logger.info("  ANTHROPIC_API_KEY=sk-ant-...")
        return False
    
    return True


def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'chromadb',
        'openai',
        'anthropic',
        'tiktoken',
        'sentence_transformers',
        'langchain'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"✅ {package} installed")
        except ImportError:
            missing.append(package)
            logger.error(f"❌ {package} not installed")
    
    if missing:
        logger.error("\nMissing packages detected!")
        logger.info("Install with: pip install -r requirements.txt")
        return False
    
    return True


def main():
    """Main setup function"""
    print("="*60)
    print("LoanQA Integration Setup")
    print("="*60)
    print()
    
    # Step 1: Load environment
    print("Step 1: Loading environment...")
    if not load_environment():
        return False
    print()
    
    # Step 2: Check dependencies
    print("Step 2: Checking Python dependencies...")
    if not check_dependencies():
        print("\n❌ Setup failed: Missing dependencies")
        return False
    print()
    
    # Step 3: Check database
    print("Step 3: Checking database connection...")
    if not check_database_connection():
        print("\n❌ Setup failed: Database not accessible")
        return False
    print()
    
    # Step 4: Run migration
    print("Step 4: Running database migration...")
    if not run_migration():
        print("\n❌ Setup failed: Migration failed")
        return False
    print()
    
    # Step 5: Check ChromaDB
    print("Step 5: Checking ChromaDB connection...")
    chromadb_ok = check_chromadb()
    print()
    
    # Step 6: Check API keys
    print("Step 6: Checking API keys...")
    api_keys_ok = check_api_keys()
    print()
    
    # Summary
    print("="*60)
    print("Setup Summary")
    print("="*60)
    print("✅ Environment: OK")
    print("✅ Dependencies: OK")
    print("✅ Database: OK")
    print("✅ Migration: OK")
    print(f"{'✅' if chromadb_ok else '⚠️ '} ChromaDB: {'OK' if chromadb_ok else 'Not running'}")
    print(f"{'✅' if api_keys_ok else '⚠️ '} API Keys: {'Configured' if api_keys_ok else 'Missing'}")
    print()
    
    if not chromadb_ok:
        print("⚠️  ChromaDB is not running. Vector search will not work.")
        print("   Start it with: docker-compose up -d chromadb")
        print()
    
    if not api_keys_ok:
        print("⚠️  API keys not configured. LLM features will not work.")
        print("   Add keys to .env file")
        print()
    
    if chromadb_ok and api_keys_ok:
        print("🎉 Setup complete! Integration is ready.")
        print()
        print("Next steps:")
        print("  1. Start all services: docker-compose up -d")
        print("  2. Test vector store: python scripts/test_vector_store.py")
        print("  3. Process a document to see end-to-end flow")
    else:
        print("⚠️  Setup incomplete. Please resolve the issues above.")
    
    print("="*60)
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Setup failed with error: {e}", exc_info=True)
        sys.exit(1)
