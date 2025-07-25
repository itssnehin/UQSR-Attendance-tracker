"""
Production monitoring service for Runner Attendance Tracker
"""
import os
import time
import psutil
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy import text
from ..database.connection import db_manager
from ..logging_config import log_performance_metric

logger = logging.getLogger(__name__)

class MonitoringService:
    """Service for monitoring application performance and health"""
    
    def __init__(self):
        self.enabled = os.getenv('ENABLE_PERFORMANCE_MONITORING', 'true').lower() == 'true'
        self.start_time = time.time()
        
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'memory_used_mb': psutil.virtual_memory().used / 1024 / 1024,
                'memory_available_mb': psutil.virtual_memory().available / 1024 / 1024,
                'disk_usage_percent': psutil.disk_usage('/').percent,
                'uptime_seconds': time.time() - self.start_time,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {}
    
    def get_database_metrics(self) -> Dict[str, Any]:
        """Get database performance metrics"""
        try:
            with db_manager.transaction() as session:
                # Get table sizes
                tables_info = []
                tables = ['runs', 'attendances', 'calendar_config', 'performance_metrics', 'application_logs']
                
                for table in tables:
                    result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    tables_info.append({
                        'table': table,
                        'row_count': count
                    })
                
                # Get database file size (SQLite specific)
                db_url = os.getenv('DATABASE_URL', 'sqlite:///./data/runner_attendance.db')
                if db_url.startswith('sqlite'):
                    db_path = db_url.replace('sqlite:///', '')
                    try:
                        db_size_mb = os.path.getsize(db_path) / 1024 / 1024
                    except:
                        db_size_mb = 0
                else:
                    db_size_mb = 0
                
                return {
                    'tables': tables_info,
                    'database_size_mb': db_size_mb,
                    'pool_status': db_manager.get_pool_status(),
                    'session_stats': db_manager.get_session_stats(),
                    'timestamp': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get database metrics: {e}")
            return {}
    
    def get_application_metrics(self) -> Dict[str, Any]:
        """Get application-specific metrics"""
        try:
            with db_manager.transaction() as session:
                # Get recent attendance registrations
                result = session.execute(text("""
                    SELECT COUNT(*) FROM attendances 
                    WHERE registered_at >= datetime('now', '-1 hour')
                """))
                recent_registrations = result.scalar()
                
                # Get today's attendance count
                result = session.execute(text("""
                    SELECT COUNT(*) FROM attendances a
                    JOIN runs r ON a.run_id = r.id
                    WHERE date(r.date) = date('now')
                """))
                today_attendance = result.scalar()
                
                # Get active runs count
                result = session.execute(text("""
                    SELECT COUNT(*) FROM runs 
                    WHERE is_active = 1 AND date = date('now')
                """))
                active_runs = result.scalar()
                
                # Get error rate from logs (last hour)
                result = session.execute(text("""
                    SELECT COUNT(*) FROM application_logs 
                    WHERE level = 'ERROR' AND timestamp >= datetime('now', '-1 hour')
                """))
                error_count = result.scalar()
                
                return {
                    'recent_registrations_1h': recent_registrations,
                    'today_attendance': today_attendance,
                    'active_runs_today': active_runs,
                    'errors_last_hour': error_count,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get application metrics: {e}")
            return {}
    
    def record_request_metrics(self, endpoint: str, method: str, status_code: int, response_time: float):
        """Record metrics for an API request"""
        if not self.enabled:
            return
            
        try:
            # Log performance metric
            log_performance_metric(
                f"request_{method.lower()}_{endpoint.replace('/', '_')}",
                response_time,
                {
                    'endpoint': endpoint,
                    'method': method,
                    'status_code': status_code
                }
            )
            
            # Log slow requests
            if response_time > 2.0:  # 2 seconds threshold
                logger.warning(
                    f"Slow request detected",
                    extra={
                        'endpoint': endpoint,
                        'method': method,
                        'status_code': status_code,
                        'response_time': response_time
                    }
                )
                
        except Exception as e:
            logger.error(f"Failed to record request metrics: {e}")
    
    def record_websocket_metrics(self, event: str, connection_count: int, processing_time: float = None):
        """Record WebSocket metrics"""
        if not self.enabled:
            return
            
        try:
            log_performance_metric(
                f"websocket_{event}",
                connection_count,
                {
                    'event': event,
                    'processing_time': processing_time
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to record WebSocket metrics: {e}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        try:
            system_metrics = self.get_system_metrics()
            db_metrics = self.get_database_metrics()
            app_metrics = self.get_application_metrics()
            
            # Determine health status
            health_issues = []
            
            # Check system resources
            if system_metrics.get('cpu_percent', 0) > 80:
                health_issues.append("High CPU usage")
            if system_metrics.get('memory_percent', 0) > 85:
                health_issues.append("High memory usage")
            if system_metrics.get('disk_usage_percent', 0) > 90:
                health_issues.append("High disk usage")
            
            # Check database
            if not db_metrics:
                health_issues.append("Database metrics unavailable")
            
            # Check error rate
            if app_metrics.get('errors_last_hour', 0) > 10:
                health_issues.append("High error rate")
            
            status = "healthy" if not health_issues else "degraded" if len(health_issues) < 3 else "unhealthy"
            
            return {
                'status': status,
                'issues': health_issues,
                'system': system_metrics,
                'database': db_metrics,
                'application': app_metrics,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get health status: {e}")
            return {
                'status': 'unhealthy',
                'issues': ['Health check failed'],
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def cleanup_old_metrics(self, days_to_keep: int = 7):
        """Clean up old performance metrics and logs"""
        if not self.enabled:
            return
            
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            with db_manager.transaction() as session:
                # Clean up old performance metrics
                result = session.execute(text("""
                    DELETE FROM performance_metrics 
                    WHERE recorded_at < :cutoff_date
                """), {'cutoff_date': cutoff_date})
                
                metrics_deleted = result.rowcount
                
                # Clean up old application logs (keep errors longer)
                result = session.execute(text("""
                    DELETE FROM application_logs 
                    WHERE timestamp < :cutoff_date AND level NOT IN ('ERROR', 'CRITICAL')
                """), {'cutoff_date': cutoff_date})
                
                logs_deleted = result.rowcount
                
                # Clean up old error logs (keep for 30 days)
                error_cutoff = datetime.utcnow() - timedelta(days=30)
                result = session.execute(text("""
                    DELETE FROM application_logs 
                    WHERE timestamp < :cutoff_date AND level IN ('ERROR', 'CRITICAL')
                """), {'cutoff_date': error_cutoff})
                
                error_logs_deleted = result.rowcount
                
                logger.info(f"Cleanup completed: {metrics_deleted} metrics, {logs_deleted} logs, {error_logs_deleted} error logs deleted")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old metrics: {e}")

# Global monitoring service instance
monitoring_service = MonitoringService()