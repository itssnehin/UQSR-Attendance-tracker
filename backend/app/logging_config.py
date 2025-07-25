"""
Production logging configuration for Runner Attendance Tracker
"""
import os
import sys
import logging
import logging.handlers
from pathlib import Path
from typing import Dict, Any
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'user_agent'):
            log_entry['user_agent'] = record.user_agent
        if hasattr(record, 'ip_address'):
            log_entry['ip_address'] = record.ip_address
        if hasattr(record, 'endpoint'):
            log_entry['endpoint'] = record.endpoint
        if hasattr(record, 'method'):
            log_entry['method'] = record.method
        if hasattr(record, 'status_code'):
            log_entry['status_code'] = record.status_code
        if hasattr(record, 'response_time'):
            log_entry['response_time'] = record.response_time
        
        return json.dumps(log_entry)

class DatabaseLogHandler(logging.Handler):
    """Custom handler to store logs in database"""
    
    def __init__(self):
        super().__init__()
        self.db_manager = None
    
    def emit(self, record: logging.LogRecord):
        """Store log record in database"""
        try:
            if not self.db_manager:
                from .database.connection import db_manager
                self.db_manager = db_manager
            
            with self.db_manager.transaction() as session:
                from sqlalchemy import text
                
                # Insert log record into application_logs table
                session.execute(text("""
                    INSERT INTO application_logs 
                    (level, message, module, timestamp, request_id, user_agent, ip_address)
                    VALUES (:level, :message, :module, :timestamp, :request_id, :user_agent, :ip_address)
                """), {
                    'level': record.levelname,
                    'message': record.getMessage(),
                    'module': record.module,
                    'timestamp': datetime.utcnow(),
                    'request_id': getattr(record, 'request_id', None),
                    'user_agent': getattr(record, 'user_agent', None),
                    'ip_address': getattr(record, 'ip_address', None)
                })
                
        except Exception:
            # Don't let logging errors crash the application
            pass

def setup_production_logging() -> Dict[str, Any]:
    """Set up production logging configuration"""
    
    # Get configuration from environment
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_format = os.getenv('LOG_FORMAT', 'json').lower()
    log_directory = Path(os.getenv('LOG_DIRECTORY', './logs'))
    enable_db_logging = os.getenv('ENABLE_DETAILED_LOGGING', 'false').lower() == 'true'
    
    # Ensure log directory exists
    log_directory.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level))
    
    if log_format == 'json':
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
    
    root_logger.addHandler(console_handler)
    
    # File handler for application logs
    app_log_file = log_directory / 'application.log'
    file_handler = logging.handlers.RotatingFileHandler(
        app_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(getattr(logging, log_level))
    
    if log_format == 'json':
        file_handler.setFormatter(JSONFormatter())
    else:
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
    
    root_logger.addHandler(file_handler)
    
    # Error log file
    error_log_file = log_directory / 'error.log'
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    
    if log_format == 'json':
        error_handler.setFormatter(JSONFormatter())
    else:
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
    
    root_logger.addHandler(error_handler)
    
    # Database handler (optional)
    if enable_db_logging:
        try:
            db_handler = DatabaseLogHandler()
            db_handler.setLevel(logging.WARNING)  # Only store warnings and errors
            root_logger.addHandler(db_handler)
        except Exception as e:
            logging.warning(f"Failed to set up database logging: {e}")
    
    # Configure specific loggers
    
    # FastAPI access logs
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.setLevel(logging.INFO)
    
    # Database logs
    db_logger = logging.getLogger("sqlalchemy.engine")
    db_echo = os.getenv('DATABASE_ECHO', 'false').lower() == 'true'
    db_logger.setLevel(logging.INFO if db_echo else logging.WARNING)
    
    # WebSocket logs
    ws_logger = logging.getLogger("socketio")
    ws_logger.setLevel(logging.INFO)
    
    # Application logger
    app_logger = logging.getLogger("app")
    app_logger.setLevel(getattr(logging, log_level))
    
    return {
        'log_level': log_level,
        'log_format': log_format,
        'log_directory': str(log_directory),
        'handlers': len(root_logger.handlers),
        'db_logging_enabled': enable_db_logging
    }

def get_request_logger(request_id: str = None, ip_address: str = None, user_agent: str = None):
    """Get a logger with request context"""
    logger = logging.getLogger("app.request")
    
    # Create a custom adapter to add request context
    class RequestLoggerAdapter(logging.LoggerAdapter):
        def process(self, msg, kwargs):
            return msg, kwargs
        
        def _log(self, level, msg, args, **kwargs):
            if self.extra:
                # Add extra fields to the log record
                record = self.logger.makeRecord(
                    self.logger.name, level, "(unknown file)", 0, msg, args, None
                )
                for key, value in self.extra.items():
                    setattr(record, key, value)
                self.logger.handle(record)
            else:
                self.logger._log(level, msg, args, **kwargs)
    
    return RequestLoggerAdapter(logger, {
        'request_id': request_id,
        'ip_address': ip_address,
        'user_agent': user_agent
    })

def log_performance_metric(metric_name: str, metric_value: float, metadata: Dict[str, Any] = None):
    """Log a performance metric"""
    try:
        from .database.connection import db_manager
        from sqlalchemy import text
        import json
        
        with db_manager.transaction() as session:
            # Check if performance_metrics table exists
            result = session.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='performance_metrics'
            """)).fetchone()
            
            if not result:
                # Table doesn't exist, skip logging (migrations haven't run yet)
                return
                
            session.execute(text("""
                INSERT INTO performance_metrics (metric_name, metric_value, recorded_at, metadata)
                VALUES (:metric_name, :metric_value, :recorded_at, :metadata)
            """), {
                'metric_name': metric_name,
                'metric_value': metric_value,
                'recorded_at': datetime.utcnow(),
                'metadata': json.dumps(metadata) if metadata else None
            })
            
    except Exception as e:
        logging.error(f"Failed to log performance metric: {e}")

# Initialize logging when module is imported
if os.getenv('ENVIRONMENT') == 'production':
    setup_production_logging()