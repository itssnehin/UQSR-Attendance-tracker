#!/usr/bin/env python3
"""
Production startup script for Runner Attendance Tracker
Ensures proper database initialization and logging setup
"""
import os
import sys
import logging
import subprocess
from pathlib import Path

def setup_logging():
    """Configure production logging"""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def ensure_data_directory():
    """Ensure data directory exists for SQLite database"""
    data_dir = Path("./data")
    data_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Data directory ensured: {data_dir.absolute()}")
    
    # Set proper permissions
    os.chmod(data_dir, 0o755)
    return data_dir

def run_migrations():
    """Run Alembic migrations"""
    try:
        logger.info("Running database migrations...")
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
        sys.exit(1)

def start_server():
    """Start the FastAPI server"""
    port = os.getenv("PORT", "8000")
    workers = os.getenv("WORKERS", "1")
    
    cmd = [
        "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", port,
        "--workers", workers
    ]
    
    logger.info(f"Starting server with command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Server failed to start: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
        sys.exit(0)

if __name__ == "__main__":
    logger = setup_logging()
    logger.info("Starting Runner Attendance Tracker in production mode")
    
    # Ensure environment is set
    os.environ.setdefault("ENVIRONMENT", "production")
    
    # Setup data directory
    ensure_data_directory()
    
    # Run migrations
    run_migrations()
    
    # Start server
    start_server()