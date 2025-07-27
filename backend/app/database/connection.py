"""Database connection and session management."""

import os
import threading
import time
from typing import Generator, Optional
from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.pool import Pool, StaticPool, QueuePool
from sqlalchemy.exc import DisconnectionError, OperationalError
import logging

logger = logging.getLogger(__name__)

# Database configuration - prefer PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL")

# If no DATABASE_URL is provided, try to construct PostgreSQL URL from individual components
if not DATABASE_URL:
    pg_user = os.getenv("PGUSER", "postgres")
    pg_password = os.getenv("PGPASSWORD", "")
    pg_host = os.getenv("PGHOST", "localhost")
    pg_port = os.getenv("PGPORT", "5432")
    pg_database = os.getenv("PGDATABASE", "railway")
    
    if pg_password:  # If we have PostgreSQL credentials, use them
        DATABASE_URL = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}"
        logger.info(f"Constructed PostgreSQL URL from environment variables")
    else:
        # Fallback to SQLite only if no PostgreSQL credentials
        DATABASE_URL = "sqlite:///./runner_attendance.db"
        logger.warning("No PostgreSQL credentials found, falling back to SQLite")

logger.info(f"Using database: {'PostgreSQL' if DATABASE_URL.startswith('postgresql') else 'SQLite'}")

# Ensure data directory exists for SQLite in production
if DATABASE_URL.startswith("sqlite"):
    import pathlib

    db_path = DATABASE_URL.replace("sqlite:///", "")
    db_dir = pathlib.Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)

# Enhanced engine configuration for concurrent access
if DATABASE_URL.startswith("sqlite"):
    # SQLite specific configuration optimized for concurrent access
    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "check_same_thread": False,
            "timeout": 30,  # 30 second timeout for busy database
            "isolation_level": None,  # Autocommit mode for better concurrency
        },
        poolclass=StaticPool,  # Use StaticPool for SQLite
        pool_pre_ping=True,  # Verify connections before use
        pool_recycle=3600,  # Recycle connections every hour
        echo=os.getenv("DB_ECHO", "false").lower() == "true",
    )
else:
    # PostgreSQL configuration
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_timeout=10,
        echo=os.getenv("DB_ECHO", "false").lower() == "true",
    )


# Add connection event listeners for monitoring
@event.listens_for(engine, "connect")
def receive_connect(dbapi_connection, connection_record):
    """Log database connections."""
    logger.info("Database connection established")


@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """Log connection checkout from pool."""
    logger.debug("Connection checked out from pool")


@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    """Log connection checkin to pool."""
    logger.debug("Connection checked in to pool")


# Create session factory with enhanced configuration
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,  # Keep objects accessible after commit
)

# Thread-safe scoped session for concurrent access
ScopedSession = scoped_session(SessionLocal)

# Base class for all models
Base = declarative_base()


class ConnectionPool:
    """Enhanced connection pool management."""

    def __init__(self, engine):
        self.engine = engine
        self._lock = threading.Lock()
        self._connection_count = 0
        self._active_connections = {}
        self._connection_stats = {
            "total_created": 0,
            "total_closed": 0,
            "current_active": 0,
            "peak_active": 0,
            "errors": 0,
        }

    def get_connection_stats(self) -> dict:
        """Get detailed connection statistics."""
        with self._lock:
            pool = self.engine.pool
            stats = {**self._connection_stats}

            # Handle different pool types
            try:
                if hasattr(pool, "size"):
                    stats["pool_size"] = pool.size()
                else:
                    stats["pool_size"] = "N/A (StaticPool)"

                if hasattr(pool, "checkedin"):
                    stats["checked_in"] = pool.checkedin()
                else:
                    stats["checked_in"] = "N/A"

                if hasattr(pool, "checkedout"):
                    stats["checked_out"] = pool.checkedout()
                else:
                    stats["checked_out"] = "N/A"

                if hasattr(pool, "overflow"):
                    stats["overflow"] = pool.overflow()
                else:
                    stats["overflow"] = "N/A"

                if hasattr(pool, "invalid"):
                    stats["invalid"] = pool.invalid()
                else:
                    stats["invalid"] = "N/A"

            except Exception as e:
                logger.warning(f"Error getting pool stats: {e}")
                stats.update(
                    {
                        "pool_size": "Error",
                        "checked_in": "Error",
                        "checked_out": "Error",
                        "overflow": "Error",
                        "invalid": "Error",
                    }
                )

            return stats

    def track_connection(self, connection_id: str, operation: str):
        """Track connection operations."""
        with self._lock:
            if operation == "created":
                self._connection_stats["total_created"] += 1
                self._connection_stats["current_active"] += 1
                self._active_connections[connection_id] = time.time()

                if (
                    self._connection_stats["current_active"]
                    > self._connection_stats["peak_active"]
                ):
                    self._connection_stats["peak_active"] = self._connection_stats[
                        "current_active"
                    ]

            elif operation == "closed":
                self._connection_stats["total_closed"] += 1
                self._connection_stats["current_active"] -= 1
                self._active_connections.pop(connection_id, None)

            elif operation == "error":
                self._connection_stats["errors"] += 1


class DatabaseManager:
    """Enhanced database connection and health management."""

    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
        self.ScopedSession = ScopedSession
        self.connection_pool = ConnectionPool(engine)
        self._session_registry = {}
        self._lock = threading.Lock()

        # Initialize database optimizations
        self._setup_optimizations()

    def _setup_optimizations(self):
        """Setup database optimizations."""
        try:
            from .optimization import initialize_optimizer

            self.optimizer = initialize_optimizer(self.engine)
            logger.info("Database optimizer initialized")
        except ImportError:
            logger.warning("Database optimizer not available")
            self.optimizer = None

    def get_session(self) -> Generator[Session, None, None]:
        """Get database session with enhanced error handling and retry logic."""
        session = None
        retry_count = 0
        max_retries = 3

        while retry_count < max_retries:
            try:
                session = self.SessionLocal()

                # Track session
                session_id = id(session)
                with self._lock:
                    self._session_registry[session_id] = {
                        "created_at": time.time(),
                        "thread_id": threading.current_thread().ident,
                    }

                yield session

                # Successful completion
                break

            except (DisconnectionError, OperationalError) as e:
                retry_count += 1
                logger.warning(
                    f"Database connection error (attempt {retry_count}/{max_retries}): {e}"
                )

                if session:
                    session.rollback()
                    session.close()

                if retry_count < max_retries:
                    time.sleep(0.1 * retry_count)  # Exponential backoff
                    continue
                else:
                    logger.error(
                        f"Database connection failed after {max_retries} attempts"
                    )
                    raise

            except Exception as e:
                if session:
                    session.rollback()
                logger.error(f"Database session error: {e}")
                raise

            finally:
                if session:
                    session_id = id(session)
                    with self._lock:
                        self._session_registry.pop(session_id, None)
                    session.close()

    def get_scoped_session(self) -> Session:
        """Get thread-local scoped session for concurrent access."""
        return self.ScopedSession()

    def remove_scoped_session(self):
        """Remove thread-local scoped session."""
        self.ScopedSession.remove()

    @contextmanager
    def transaction(self):
        """Context manager for database transactions with automatic rollback."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Transaction rolled back due to error: {e}")
            raise
        finally:
            session.close()

    @contextmanager
    def bulk_transaction(self):
        """Context manager optimized for bulk operations."""
        session = self.SessionLocal()
        try:
            # Disable autoflush for bulk operations
            session.autoflush = False
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Bulk transaction rolled back due to error: {e}")
            raise
        finally:
            session.close()

    def check_health(self) -> bool:
        """Enhanced database connection health check."""
        try:
            from sqlalchemy import text

            with self.engine.connect() as connection:
                # Test basic connectivity
                connection.execute(text("SELECT 1"))

                # Test write capability
                connection.execute(text("CREATE TEMP TABLE health_check (id INTEGER)"))
                connection.execute(text("INSERT INTO health_check (id) VALUES (1)"))
                connection.execute(text("DROP TABLE health_check"))

                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    def get_pool_status(self) -> dict:
        """Get enhanced connection pool status."""
        return self.connection_pool.get_connection_stats()

    def get_session_stats(self) -> dict:
        """Get session statistics."""
        with self._lock:
            current_time = time.time()
            active_sessions = len(self._session_registry)
            long_running_sessions = sum(
                1
                for session_info in self._session_registry.values()
                if current_time - session_info["created_at"]
                > 30  # Sessions older than 30 seconds
            )

            return {
                "active_sessions": active_sessions,
                "long_running_sessions": long_running_sessions,
                "session_details": list(self._session_registry.values()),
            }

    def cleanup_stale_sessions(self):
        """Clean up stale database sessions."""
        with self._lock:
            current_time = time.time()
            stale_sessions = [
                session_id
                for session_id, session_info in self._session_registry.items()
                if current_time - session_info["created_at"] > 300  # 5 minutes
            ]

            for session_id in stale_sessions:
                self._session_registry.pop(session_id, None)
                logger.warning(f"Cleaned up stale session: {session_id}")

    def close_all_connections(self):
        """Close all database connections and clean up resources."""
        try:
            # Remove all scoped sessions
            self.ScopedSession.remove()

            # Close engine connections
            self.engine.dispose()

            # Clear session registry
            with self._lock:
                self._session_registry.clear()

            logger.info("All database connections closed and resources cleaned up")

        except Exception as e:
            logger.error(f"Error closing database connections: {e}")

    def optimize_database(self):
        """Run database optimization if optimizer is available."""
        if self.optimizer:
            try:
                with self.transaction() as session:
                    self.optimizer.optimize_database(session)
                logger.info("Database optimization completed")
            except Exception as e:
                logger.error(f"Database optimization failed: {e}")
        else:
            logger.warning("Database optimizer not available")


# Global database manager instance
db_manager = DatabaseManager()


# Dependency for FastAPI
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions."""
    yield from db_manager.get_session()
