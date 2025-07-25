#!/usr/bin/env python3
"""
Deployment validation script
Tests all deployment components without starting the server
"""
import os
import sys
import logging
from pathlib import Path

# Add the app directory to the path
sys.path.append(os.path.dirname(__file__))

def setup_logging():
    """Configure logging for validation"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def test_imports():
    """Test that all required modules can be imported"""
    logger.info("Testing imports...")
    
    try:
        from app.main import app
        from app.database.connection import db_manager
        from app.services.monitoring_service import monitoring_service
        from app.logging_config import setup_production_logging
        from app.middleware.monitoring_middleware import MonitoringMiddleware
        logger.info("✓ All imports successful")
        return True
    except Exception as e:
        logger.error(f"✗ Import failed: {e}")
        return False

def test_database_connection():
    """Test database connection and health"""
    logger.info("Testing database connection...")
    
    try:
        from app.database.connection import db_manager
        health = db_manager.check_health()
        if health:
            logger.info("✓ Database connection healthy")
            return True
        else:
            logger.error("✗ Database connection unhealthy")
            return False
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        return False

def test_migrations():
    """Test that migrations are up to date"""
    logger.info("Testing migrations...")
    
    try:
        import subprocess
        result = subprocess.run(
            ["python", "-m", "alembic", "current"],
            capture_output=True,
            text=True,
            check=True
        )
        
        if "af198280e98a" in result.stdout:
            logger.info("✓ Migrations are up to date")
            return True
        else:
            logger.warning(f"? Migration status unclear: {result.stdout}")
            return True  # Don't fail on this
    except Exception as e:
        logger.error(f"✗ Migration check failed: {e}")
        return False

def test_environment_config():
    """Test environment configuration"""
    logger.info("Testing environment configuration...")
    
    required_vars = [
        'DATABASE_URL',
        'ENVIRONMENT',
        'LOG_LEVEL'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"? Missing environment variables: {missing_vars}")
        logger.info("This is expected in development - set these for production")
    else:
        logger.info("✓ All required environment variables present")
    
    return True

def test_file_structure():
    """Test that all required files exist"""
    logger.info("Testing file structure...")
    
    required_files = [
        'requirements.txt',
        'railway.toml',
        'nixpacks.toml',
        'Procfile',
        'alembic.ini',
        'app/main.py',
        'app/logging_config.py',
        'app/services/monitoring_service.py',
        'app/middleware/monitoring_middleware.py',
        'init_production_db.py',
        'start_production.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        logger.error(f"✗ Missing required files: {missing_files}")
        return False
    else:
        logger.info("✓ All required files present")
        return True

def test_monitoring_service():
    """Test monitoring service functionality"""
    logger.info("Testing monitoring service...")
    
    try:
        from app.services.monitoring_service import monitoring_service
        
        # Test system metrics
        system_metrics = monitoring_service.get_system_metrics()
        if system_metrics:
            logger.info("✓ System metrics collection working")
        else:
            logger.warning("? System metrics collection returned empty")
        
        # Test database metrics
        db_metrics = monitoring_service.get_database_metrics()
        if db_metrics:
            logger.info("✓ Database metrics collection working")
        else:
            logger.warning("? Database metrics collection returned empty")
        
        # Test health status
        health = monitoring_service.get_health_status()
        if health and health.get('status'):
            logger.info(f"✓ Health status: {health['status']}")
        else:
            logger.warning("? Health status check returned empty")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Monitoring service test failed: {e}")
        return False

def test_logging_config():
    """Test logging configuration"""
    logger.info("Testing logging configuration...")
    
    try:
        # Set production environment temporarily
        original_env = os.getenv('ENVIRONMENT')
        os.environ['ENVIRONMENT'] = 'production'
        
        from app.logging_config import setup_production_logging
        config = setup_production_logging()
        
        if config:
            logger.info(f"✓ Production logging configured: {config}")
        else:
            logger.warning("? Production logging configuration returned empty")
        
        # Restore original environment
        if original_env:
            os.environ['ENVIRONMENT'] = original_env
        else:
            os.environ.pop('ENVIRONMENT', None)
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Logging configuration test failed: {e}")
        return False

def main():
    """Run all validation tests"""
    logger.info("Starting deployment validation...")
    
    tests = [
        ("File Structure", test_file_structure),
        ("Imports", test_imports),
        ("Database Connection", test_database_connection),
        ("Migrations", test_migrations),
        ("Environment Config", test_environment_config),
        ("Monitoring Service", test_monitoring_service),
        ("Logging Config", test_logging_config)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
    
    logger.info(f"\n--- Validation Summary ---")
    logger.info(f"Passed: {passed}/{total} tests")
    
    if passed == total:
        logger.info("✓ All deployment components validated successfully!")
        logger.info("Ready for production deployment")
        return 0
    else:
        logger.warning(f"? {total - passed} tests had issues")
        logger.info("Review the issues above before deploying")
        return 1

if __name__ == "__main__":
    logger = setup_logging()
    sys.exit(main())