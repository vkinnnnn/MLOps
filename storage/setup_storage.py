"""
Storage setup and initialization script
"""
import psycopg2
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def setup_database(database_url: str):
    """
    Initialize database schema by running init_db.sql
    
    Args:
        database_url: PostgreSQL connection URL
    """
    try:
        # Read SQL initialization script
        sql_file = Path(__file__).parent / 'init_db.sql'
        
        if not sql_file.exists():
            raise FileNotFoundError(f"SQL initialization file not found: {sql_file}")
        
        with open(sql_file, 'r') as f:
            sql_script = f.read()
        
        # Connect to database
        logger.info("Connecting to database...")
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        
        # Execute initialization script
        logger.info("Executing database initialization script...")
        with conn.cursor() as cursor:
            cursor.execute(sql_script)
        
        logger.info("✓ Database initialized successfully")
        
        # Verify tables were created
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = cursor.fetchall()
            
            logger.info("Created tables:")
            for table in tables:
                logger.info(f"  - {table[0]}")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def verify_storage_setup(storage_service):
    """
    Verify that storage service is properly configured
    
    Args:
        storage_service: StorageService instance
        
    Returns:
        True if setup is valid
    """
    try:
        logger.info("Verifying storage setup...")
        
        # Test database connection
        logger.info("Testing database connection...")
        with storage_service.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result[0] != 1:
                    raise Exception("Database connection test failed")
        logger.info("✓ Database connection OK")
        
        # Test object storage connection
        logger.info("Testing object storage connection...")
        storage_service.object_storage.initialize()
        logger.info("✓ Object storage connection OK")
        
        # Verify bucket exists
        logger.info("Verifying bucket exists...")
        bucket_name = storage_service.object_storage.bucket_name
        try:
            storage_service.object_storage.client.head_bucket(Bucket=bucket_name)
            logger.info(f"✓ Bucket '{bucket_name}' exists")
        except:
            logger.warning(f"Bucket '{bucket_name}' does not exist, creating...")
            storage_service.object_storage.client.create_bucket(Bucket=bucket_name)
            logger.info(f"✓ Bucket '{bucket_name}' created")
        
        logger.info("✓ Storage setup verification complete")
        return True
        
    except Exception as e:
        logger.error(f"Storage setup verification failed: {e}")
        raise


def main():
    """Main setup function"""
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from config import config
    from storage.storage_service import StorageService
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("Storage Service Setup")
    print("=" * 60)
    print()
    
    # Setup database
    print("Step 1: Initializing database schema...")
    print("-" * 60)
    try:
        setup_database(config.DATABASE_URL)
        print("✓ Database setup complete\n")
    except Exception as e:
        print(f"✗ Database setup failed: {e}\n")
        return False
    
    # Initialize and verify storage service
    print("Step 2: Verifying storage service...")
    print("-" * 60)
    try:
        storage = StorageService(
            database_url=config.DATABASE_URL,
            s3_endpoint=config.S3_ENDPOINT,
            s3_access_key=config.S3_ACCESS_KEY,
            s3_secret_key=config.S3_SECRET_KEY,
            s3_bucket_name=config.S3_BUCKET_NAME,
            s3_region=config.S3_REGION
        )
        
        storage.initialize()
        verify_storage_setup(storage)
        storage.close()
        
        print("✓ Storage service verification complete\n")
    except Exception as e:
        print(f"✗ Storage service verification failed: {e}\n")
        return False
    
    print("=" * 60)
    print("✓ Storage setup completed successfully!")
    print("=" * 60)
    print()
    print("You can now use the storage service in your application.")
    print()
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
