"""Database migration utilities."""

import logging
from typing import Dict, List, Optional
from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import text
from app.database.connection import engine

logger = logging.getLogger(__name__)


class MigrationManager:
    """Database migration management."""
    
    def __init__(self):
        self.alembic_cfg = Config("alembic.ini")
    
    def run_migrations(self) -> Dict[str, any]:
        """Run all pending migrations."""
        try:
            command.upgrade(self.alembic_cfg, "head")
            logger.info("Database migrations completed successfully")
            return {
                "success": True,
                "message": "Migrations completed successfully"
            }
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_current_revision(self) -> Optional[str]:
        """Get current database revision."""
        try:
            with engine.connect() as connection:
                context = MigrationContext.configure(connection)
                return context.get_current_revision()
        except Exception as e:
            logger.error(f"Failed to get current revision: {e}")
            return None
    
    def get_pending_migrations(self) -> List[str]:
        """Get list of pending migrations."""
        try:
            script = ScriptDirectory.from_config(self.alembic_cfg)
            current_rev = self.get_current_revision()
            
            if current_rev is None:
                # No migrations have been run
                return [rev.revision for rev in script.walk_revisions()]
            
            # Get revisions between current and head
            pending = []
            for rev in script.walk_revisions(current_rev, "head"):
                if rev.revision != current_rev:
                    pending.append(rev.revision)
            
            return pending
        except Exception as e:
            logger.error(f"Failed to get pending migrations: {e}")
            return []
    
    def check_database_health(self) -> bool:
        """Check if database is accessible and healthy."""
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def create_tables(self) -> Dict[str, any]:
        """Create all tables (alternative to migrations for development)."""
        try:
            from app.database.connection import Base
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")
            return {
                "success": True,
                "message": "Tables created successfully"
            }
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def drop_tables(self) -> Dict[str, any]:
        """Drop all tables (for development/testing)."""
        try:
            from app.database.connection import Base
            Base.metadata.drop_all(bind=engine)
            logger.info("Database tables dropped successfully")
            return {
                "success": True,
                "message": "Tables dropped successfully"
            }
        except Exception as e:
            logger.error(f"Failed to drop tables: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def reset_database(self) -> Dict[str, any]:
        """Reset database (drop and recreate tables)."""
        try:
            drop_result = self.drop_tables()
            if not drop_result["success"]:
                return drop_result
            
            create_result = self.create_tables()
            if not create_result["success"]:
                return create_result
            
            logger.info("Database reset completed successfully")
            return {
                "success": True,
                "message": "Database reset completed successfully"
            }
        except Exception as e:
            logger.error(f"Database reset failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Global migration manager instance
migration_manager = MigrationManager()