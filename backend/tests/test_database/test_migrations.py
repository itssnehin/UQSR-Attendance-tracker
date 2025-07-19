"""Tests for database migration management."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.database.migrations import MigrationManager, migration_manager


class TestMigrationManager:
    """Test MigrationManager class."""
    
    def test_migration_manager_initialization(self):
        """Test migration manager initialization."""
        manager = MigrationManager()
        assert manager.alembic_cfg is not None
    
    @patch('app.database.migrations.command')
    def test_run_migrations_success(self, mock_command):
        """Test successful migration run."""
        mock_command.upgrade = Mock()
        
        manager = MigrationManager()
        result = manager.run_migrations()
        
        assert result["success"] is True
        assert "completed successfully" in result["message"]
        mock_command.upgrade.assert_called_once_with(manager.alembic_cfg, "head")
    
    @patch('app.database.migrations.command')
    def test_run_migrations_failure(self, mock_command):
        """Test migration run failure."""
        mock_command.upgrade.side_effect = Exception("Migration failed")
        
        manager = MigrationManager()
        result = manager.run_migrations()
        
        assert result["success"] is False
        assert result["error"] == "Migration failed"
    
    @patch('app.database.migrations.engine')
    def test_get_current_revision_success(self, mock_engine):
        """Test getting current revision successfully."""
        mock_connection = Mock()
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        
        with patch('app.database.migrations.MigrationContext') as mock_context_class:
            mock_context = Mock()
            mock_context.get_current_revision.return_value = "abc123"
            mock_context_class.configure.return_value = mock_context
            
            manager = MigrationManager()
            result = manager.get_current_revision()
            
            assert result == "abc123"
            mock_context_class.configure.assert_called_once_with(mock_connection)
    
    @patch('app.database.migrations.engine')
    def test_get_current_revision_failure(self, mock_engine):
        """Test getting current revision failure."""
        mock_engine.connect.side_effect = Exception("Connection failed")
        
        manager = MigrationManager()
        result = manager.get_current_revision()
        
        assert result is None
    
    @patch('app.database.migrations.ScriptDirectory')
    def test_get_pending_migrations_no_current(self, mock_script_dir_class):
        """Test getting pending migrations when no current revision."""
        mock_script_dir = Mock()
        mock_rev1 = Mock()
        mock_rev1.revision = "rev1"
        mock_rev2 = Mock()
        mock_rev2.revision = "rev2"
        mock_script_dir.walk_revisions.return_value = [mock_rev1, mock_rev2]
        mock_script_dir_class.from_config.return_value = mock_script_dir
        
        manager = MigrationManager()
        with patch.object(manager, 'get_current_revision', return_value=None):
            result = manager.get_pending_migrations()
            
            assert result == ["rev1", "rev2"]
    
    @patch('app.database.migrations.ScriptDirectory')
    def test_get_pending_migrations_with_current(self, mock_script_dir_class):
        """Test getting pending migrations with current revision."""
        mock_script_dir = Mock()
        mock_rev1 = Mock()
        mock_rev1.revision = "current"
        mock_rev2 = Mock()
        mock_rev2.revision = "rev2"
        mock_script_dir.walk_revisions.return_value = [mock_rev2, mock_rev1]
        mock_script_dir_class.from_config.return_value = mock_script_dir
        
        manager = MigrationManager()
        with patch.object(manager, 'get_current_revision', return_value="current"):
            result = manager.get_pending_migrations()
            
            assert result == ["rev2"]
    
    @patch('app.database.migrations.ScriptDirectory')
    def test_get_pending_migrations_failure(self, mock_script_dir_class):
        """Test getting pending migrations failure."""
        mock_script_dir_class.from_config.side_effect = Exception("Script error")
        
        manager = MigrationManager()
        result = manager.get_pending_migrations()
        
        assert result == []
    
    @patch('app.database.migrations.engine')
    def test_check_database_health_success(self, mock_engine):
        """Test successful database health check."""
        mock_connection = Mock()
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        
        manager = MigrationManager()
        result = manager.check_database_health()
        
        assert result is True
        mock_connection.execute.assert_called_once()
    
    @patch('app.database.migrations.engine')
    def test_check_database_health_failure(self, mock_engine):
        """Test database health check failure."""
        mock_engine.connect.side_effect = Exception("Connection failed")
        
        manager = MigrationManager()
        result = manager.check_database_health()
        
        assert result is False
    
    @patch('app.database.migrations.Base')
    @patch('app.database.migrations.engine')
    def test_create_tables_success(self, mock_engine, mock_base):
        """Test successful table creation."""
        mock_metadata = Mock()
        mock_base.metadata = mock_metadata
        mock_metadata.create_all = Mock()
        
        manager = MigrationManager()
        result = manager.create_tables()
        
        assert result["success"] is True
        assert "created successfully" in result["message"]
        mock_metadata.create_all.assert_called_once_with(bind=mock_engine)
    
    @patch('app.database.migrations.Base')
    def test_create_tables_failure(self, mock_base):
        """Test table creation failure."""
        mock_metadata = Mock()
        mock_base.metadata = mock_metadata
        mock_metadata.create_all.side_effect = Exception("Create failed")
        
        manager = MigrationManager()
        result = manager.create_tables()
        
        assert result["success"] is False
        assert result["error"] == "Create failed"
    
    @patch('app.database.migrations.Base')
    @patch('app.database.migrations.engine')
    def test_drop_tables_success(self, mock_engine, mock_base):
        """Test successful table dropping."""
        mock_metadata = Mock()
        mock_base.metadata = mock_metadata
        mock_metadata.drop_all = Mock()
        
        manager = MigrationManager()
        result = manager.drop_tables()
        
        assert result["success"] is True
        assert "dropped successfully" in result["message"]
        mock_metadata.drop_all.assert_called_once_with(bind=mock_engine)
    
    @patch('app.database.migrations.Base')
    def test_drop_tables_failure(self, mock_base):
        """Test table dropping failure."""
        mock_metadata = Mock()
        mock_base.metadata = mock_metadata
        mock_metadata.drop_all.side_effect = Exception("Drop failed")
        
        manager = MigrationManager()
        result = manager.drop_tables()
        
        assert result["success"] is False
        assert result["error"] == "Drop failed"
    
    def test_reset_database_success(self):
        """Test successful database reset."""
        manager = MigrationManager()
        
        with patch.object(manager, 'drop_tables', return_value={"success": True}):
            with patch.object(manager, 'create_tables', return_value={"success": True}):
                result = manager.reset_database()
                
                assert result["success"] is True
                assert "reset completed successfully" in result["message"]
    
    def test_reset_database_drop_failure(self):
        """Test database reset with drop failure."""
        manager = MigrationManager()
        
        with patch.object(manager, 'drop_tables', return_value={"success": False, "error": "Drop failed"}):
            result = manager.reset_database()
            
            assert result["success"] is False
            assert result["error"] == "Drop failed"
    
    def test_reset_database_create_failure(self):
        """Test database reset with create failure."""
        manager = MigrationManager()
        
        with patch.object(manager, 'drop_tables', return_value={"success": True}):
            with patch.object(manager, 'create_tables', return_value={"success": False, "error": "Create failed"}):
                result = manager.reset_database()
                
                assert result["success"] is False
                assert result["error"] == "Create failed"
    
    def test_reset_database_exception(self):
        """Test database reset with exception."""
        manager = MigrationManager()
        
        with patch.object(manager, 'drop_tables', side_effect=Exception("Unexpected error")):
            result = manager.reset_database()
            
            assert result["success"] is False
            assert result["error"] == "Unexpected error"
    
    def test_global_migration_manager_instance(self):
        """Test global migration manager instance."""
        assert migration_manager is not None
        assert isinstance(migration_manager, MigrationManager)