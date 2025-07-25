#!/usr/bin/env python3
"""
Production database initialization script
Ensures proper database setup with all optimizations
"""
import os
import sys
import logging
from pathlib import Path
from sqlalchemy import text
import subprocess

# Add the app directory to the path
sys.path.append(os.path.dirname(__file__))

from app.database.connection import db_manager, engine, Base

def setup_logging():
    """Configure logging for database initialization"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def ensure_data_directory():
    """Ensure data directory exists with proper permissions"""
    data_dir = Path("./data")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Set proper permissions for SQLite database
    os.chmod(data_dir, 0o755)
    
    logger.info(f"Data directory ensured: {data_dir.absolute()}")
    return data_dir

def run_alembic_migrations():
    """Run Alembic migrations to set up database schema"""
    try:
        logger.info("Running Alembic migrations...")
        
        # Run migrations
        result = subprocess.run(
            ["python", "-m", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            check=True
        )
        
        logger.info("Database migrations completed successfully")
        if result.stdout:
            logger.info(f"Migration output: {result.stdout}")
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Migration failed: {e}")
        logger.error(f"Migration stderr: {e.stderr}")
        raise

def optimize_sqlite_settings():
    """Apply SQLite-specific optimizations for production"""
    try:
        with engine.connect() as conn:
            # Enable WAL mode for better concurrency
            conn.execute(text("PRAGMA journal_mode=WAL;"))
            
            # Set synchronous mode for better performance
            conn.execute(text("PRAGMA synchronous=NORMAL;"))
            
            # Set cache size (negative value means KB)
            conn.execute(text("PRAGMA cache_size=-64000;"))  # 64MB cache
            
            # Enable foreign key constraints
            conn.execute(text("PRAGMA foreign_keys=ON;"))
            
            # Set temp store to memory
            conn.execute(text("PRAGMA temp_store=MEMORY;"))
            
            # Set mmap size for better I/O performance
            conn.execute(text("PRAGMA mmap_size=268435456;"))  # 256MB
            
            conn.commit()
            
        logger.info("SQLite optimizations applied successfully")
        
    except Exception as e:
        logger.error(f"Failed to apply SQLite optimizations: {e}")
        raise

def verify_database_setup():
    """Verify that database is properly set up"""
    try:
        with engine.connect() as conn:
            # Check that all tables exist
            tables = ['runs', 'attendances', 'calendar_config', 'performance_metrics', 'application_logs']
            
            for table in tables:
                result = conn.execute(text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}';"))
                if not result.fetchone():
                    raise Exception(f"Table {table} not found")
            
            # Check indexes
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='index';"))
            indexes = [row[0] for row in result.fetchall()]
            
            required_indexes = [
                'ix_runs_date',
                'ix_runs_session_id',
                'ix_attendances_run_id',
                'ix_calendar_config_date',
                'ix_runs_date_active',
                'ix_attendances_run_date_registered'
            ]
            
            for index in required_indexes:
                if index not in indexes:
                    logger.warning(f"Index {index} not found")
            
            logger.info("Database verification completed successfully")
            
    except Exception as e:
        logger.error(f"Database verification failed: {e}")
        raise

def create_initial_data():
    """Create any initial data needed for production"""
    try:
        # This could include default calendar configurations, etc.
        # For now, we'll just log that the database is ready
        logger.info("Database is ready for production use")
        
    except Exception as e:
        logger.error(f"Failed to create initial data: {e}")
        raise

def main():
    """Main initialization function"""
    logger.info("Starting production database initialization...")
    
    try:
        # Ensure data directory exists
        ensure_data_directory()
        
        # Run migrations
        run_alembic_migrations()
        
        # Apply SQLite optimizations
        optimize_sqlite_settings()
        
        # Verify setup
        verify_database_setup()
        
        # Create initial data
        create_initial_data()
        
        logger.info("Production database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    logger = setup_logging()
    main()