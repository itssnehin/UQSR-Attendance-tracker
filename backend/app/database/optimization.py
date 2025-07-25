"""
Database optimization utilities for SQLite performance
"""
import logging
from typing import Dict, Any, List
from sqlalchemy import text, Index, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import Pool
import sqlite3
import time

logger = logging.getLogger(__name__)


class SQLiteOptimizer:
    """SQLite database optimization utilities."""
    
    def __init__(self, engine: Engine):
        self.engine = engine
        self.setup_sqlite_optimizations()
    
    def setup_sqlite_optimizations(self):
        """Setup SQLite-specific optimizations."""
        
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set SQLite PRAGMA settings for performance."""
            if isinstance(dbapi_connection, sqlite3.Connection):
                cursor = dbapi_connection.cursor()
                
                # Performance optimizations
                cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
                cursor.execute("PRAGMA synchronous=NORMAL")  # Balanced durability/performance
                cursor.execute("PRAGMA cache_size=10000")  # 10MB cache
                cursor.execute("PRAGMA temp_store=MEMORY")  # Store temp tables in memory
                cursor.execute("PRAGMA mmap_size=268435456")  # 256MB memory-mapped I/O
                
                # Concurrency optimizations
                cursor.execute("PRAGMA busy_timeout=30000")  # 30 second timeout
                cursor.execute("PRAGMA wal_autocheckpoint=1000")  # Checkpoint every 1000 pages
                
                # Query optimization
                cursor.execute("PRAGMA optimize")  # Analyze query patterns
                
                cursor.close()
                logger.info("SQLite performance optimizations applied")
    
    def create_performance_indexes(self, session: Session):
        """Create performance indexes for common queries."""
        try:
            # Index for run lookups by session_id (most common query)
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_runs_session_id_active 
                ON runs(session_id, is_active)
            """))
            
            # Index for run lookups by date
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_runs_date_active 
                ON runs(date, is_active)
            """))
            
            # Index for attendance lookups by run_id
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_attendances_run_id 
                ON attendances(run_id)
            """))
            
            # Composite index for duplicate prevention
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_attendances_run_runner 
                ON attendances(run_id, runner_name)
            """))
            
            # Index for attendance history queries
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_attendances_registered_at 
                ON attendances(registered_at)
            """))
            
            # Index for calendar config lookups
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_calendar_config_date 
                ON calendar_config(date)
            """))
            
            # Index for calendar config with has_run filter
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_calendar_config_date_has_run 
                ON calendar_config(date, has_run)
            """))
            
            session.commit()
            logger.info("Performance indexes created successfully")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating performance indexes: {e}")
            raise
    
    def analyze_query_performance(self, session: Session, query: str) -> Dict[str, Any]:
        """Analyze query performance using EXPLAIN QUERY PLAN."""
        try:
            result = session.execute(text(f"EXPLAIN QUERY PLAN {query}")).fetchall()
            
            analysis = {
                "query": query,
                "execution_plan": [],
                "uses_index": False,
                "table_scans": 0
            }
            
            for row in result:
                plan_step = {
                    "id": row[0],
                    "parent": row[1],
                    "detail": row[3]
                }
                analysis["execution_plan"].append(plan_step)
                
                # Check if index is used
                if "USING INDEX" in row[3].upper():
                    analysis["uses_index"] = True
                
                # Count table scans
                if "SCAN TABLE" in row[3].upper():
                    analysis["table_scans"] += 1
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing query performance: {e}")
            return {"error": str(e)}
    
    def get_database_stats(self, session: Session) -> Dict[str, Any]:
        """Get database statistics for monitoring."""
        try:
            stats = {}
            
            # Table sizes
            tables = ["runs", "attendances", "calendar_config"]
            for table in tables:
                result = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                stats[f"{table}_count"] = result
            
            # Database file size
            result = session.execute(text("PRAGMA page_count")).scalar()
            page_size = session.execute(text("PRAGMA page_size")).scalar()
            stats["database_size_bytes"] = result * page_size
            stats["database_size_mb"] = round((result * page_size) / (1024 * 1024), 2)
            
            # Cache statistics
            cache_size = session.execute(text("PRAGMA cache_size")).scalar()
            stats["cache_size_pages"] = cache_size
            
            # WAL mode status
            journal_mode = session.execute(text("PRAGMA journal_mode")).scalar()
            stats["journal_mode"] = journal_mode
            
            # Index usage statistics
            stats["indexes"] = []
            index_list = session.execute(text("PRAGMA index_list('runs')")).fetchall()
            for index in index_list:
                index_info = session.execute(text(f"PRAGMA index_info('{index[1]}')")).fetchall()
                stats["indexes"].append({
                    "name": index[1],
                    "unique": bool(index[2]),
                    "columns": [col[2] for col in index_info]
                })
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {"error": str(e)}
    
    def optimize_database(self, session: Session):
        """Run database optimization commands."""
        try:
            # Analyze tables for query optimizer
            session.execute(text("ANALYZE"))
            
            # Rebuild indexes if needed
            session.execute(text("REINDEX"))
            
            # Optimize database
            session.execute(text("PRAGMA optimize"))
            
            # Vacuum if needed (compact database)
            # Note: VACUUM can be expensive, so only run when necessary
            session.execute(text("PRAGMA auto_vacuum=INCREMENTAL"))
            session.execute(text("PRAGMA incremental_vacuum"))
            
            session.commit()
            logger.info("Database optimization completed")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error optimizing database: {e}")
            raise
    
    def get_slow_queries(self, session: Session, threshold_ms: int = 100) -> List[Dict[str, Any]]:
        """Get queries that are slower than threshold (requires query logging)."""
        # This would require query logging to be enabled
        # For now, return common potentially slow queries to monitor
        
        slow_query_patterns = [
            {
                "pattern": "SELECT without WHERE clause",
                "example": "SELECT * FROM attendances",
                "recommendation": "Add WHERE clause or LIMIT"
            },
            {
                "pattern": "JOIN without proper indexes",
                "example": "SELECT * FROM attendances JOIN runs ON attendances.run_id = runs.id",
                "recommendation": "Ensure indexes exist on join columns"
            },
            {
                "pattern": "ORDER BY without index",
                "example": "SELECT * FROM attendances ORDER BY registered_at",
                "recommendation": "Create index on ORDER BY columns"
            }
        ]
        
        return slow_query_patterns


class QueryOptimizer:
    """Query optimization utilities."""
    
    @staticmethod
    def optimize_attendance_queries():
        """Optimized queries for attendance operations."""
        return {
            "get_today_attendance": """
                SELECT COUNT(*) 
                FROM attendances a 
                JOIN runs r ON a.run_id = r.id 
                WHERE r.date = ? AND r.is_active = 1
            """,
            
            "check_duplicate_registration": """
                SELECT 1 
                FROM attendances a 
                JOIN runs r ON a.run_id = r.id 
                WHERE r.session_id = ? AND a.runner_name = ? 
                LIMIT 1
            """,
            
            "get_attendance_history_paginated": """
                SELECT a.id, a.runner_name, a.registered_at, r.date, r.session_id
                FROM attendances a 
                JOIN runs r ON a.run_id = r.id 
                WHERE r.date BETWEEN ? AND ?
                ORDER BY r.date DESC, a.registered_at DESC 
                LIMIT ? OFFSET ?
            """,
            
            "get_run_by_session_id": """
                SELECT id, date, session_id, is_active, created_at 
                FROM runs 
                WHERE session_id = ? AND is_active = 1 
                LIMIT 1
            """
        }
    
    @staticmethod
    def get_query_hints() -> Dict[str, str]:
        """Get query optimization hints."""
        return {
            "use_indexes": "Ensure WHERE clauses use indexed columns",
            "limit_results": "Use LIMIT for large result sets",
            "avoid_select_star": "Select only needed columns",
            "use_prepared_statements": "Use parameterized queries",
            "batch_inserts": "Use batch inserts for multiple records",
            "use_transactions": "Wrap multiple operations in transactions"
        }


# Performance monitoring decorator
def monitor_query_performance(func):
    """Decorator to monitor query performance."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            if execution_time > 100:  # Log slow queries (>100ms)
                logger.warning(f"Slow query detected in {func.__name__}: {execution_time:.2f}ms")
            else:
                logger.debug(f"Query {func.__name__} executed in {execution_time:.2f}ms")
            
            return result
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Query {func.__name__} failed after {execution_time:.2f}ms: {e}")
            raise
    
    return wrapper


# Global optimizer instance
sqlite_optimizer = None

def initialize_optimizer(engine: Engine):
    """Initialize the global SQLite optimizer."""
    global sqlite_optimizer
    sqlite_optimizer = SQLiteOptimizer(engine)
    return sqlite_optimizer