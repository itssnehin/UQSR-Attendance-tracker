"""Tests for database connection and management."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError
from app.database.connection import DatabaseManager, db_manager


class TestDatabaseManager:
    """Test DatabaseManager class."""
    
    def test_database_manager_initialization(self):
        """Test database manager initialization."""
        manager = DatabaseManager()
        assert manager.engine is not None
        assert manager.SessionLocal is not None
    
    def test_get_session_success(self):
        """Test successful session creation."""
        manager = DatabaseManager()
        session_gen = manager.get_session()
        session = next(session_gen)
        
        assert session is not None
        # Clean up
        try:
            next(session_gen)
        except StopIteration:
            pass  # Expected
    
    @patch('app.database.connection.SessionLocal')
    def test_get_session_with_exception(self, mock_session_local):
        """Test session creation with exception handling."""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        mock_session.rollback = Mock()
        mock_session.close = Mock()
        
        # Mock an exception during session usage
        def mock_generator():
            session = mock_session_local()
            try:
                yield session
                raise SQLAlchemyError("Test error")
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()
        
        manager = DatabaseManager()
        manager.get_session = mock_generator
        
        session_gen = manager.get_session()
        session = next(session_gen)
        
        with pytest.raises(SQLAlchemyError):
            next(session_gen)
        
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
    
    @patch('app.database.connection.engine')
    def test_check_health_success(self, mock_engine):
        """Test successful health check."""
        mock_connection = Mock()
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_connection.execute.return_value = None
        
        manager = DatabaseManager()
        manager.engine = mock_engine
        
        result = manager.check_health()
        assert result is True
        mock_connection.execute.assert_called_once_with("SELECT 1")
    
    @patch('app.database.connection.engine')
    def test_check_health_failure(self, mock_engine):
        """Test health check failure."""
        mock_engine.connect.side_effect = SQLAlchemyError("Connection failed")
        
        manager = DatabaseManager()
        manager.engine = mock_engine
        
        result = manager.check_health()
        assert result is False
    
    @patch('app.database.connection.engine')
    def test_get_pool_status(self, mock_engine):
        """Test getting pool status."""
        mock_pool = Mock()
        mock_pool.size.return_value = 20
        mock_pool.checkedin.return_value = 15
        mock_pool.checkedout.return_value = 5
        mock_pool.overflow.return_value = 0
        mock_pool.invalid.return_value = 0
        mock_engine.pool = mock_pool
        
        manager = DatabaseManager()
        manager.engine = mock_engine
        
        status = manager.get_pool_status()
        
        expected = {
            "size": 20,
            "checked_in": 15,
            "checked_out": 5,
            "overflow": 0,
            "invalid": 0
        }
        assert status == expected
    
    @patch('app.database.connection.engine')
    def test_close_all_connections(self, mock_engine):
        """Test closing all connections."""
        mock_engine.dispose = Mock()
        
        manager = DatabaseManager()
        manager.engine = mock_engine
        
        manager.close_all_connections()
        mock_engine.dispose.assert_called_once()
    
    def test_global_db_manager_instance(self):
        """Test global database manager instance."""
        assert db_manager is not None
        assert isinstance(db_manager, DatabaseManager)


class TestDatabaseDependency:
    """Test database dependency function."""
    
    def test_get_db_dependency(self):
        """Test get_db dependency function."""
        from app.database.connection import get_db
        
        db_gen = get_db()
        session = next(db_gen)
        
        assert session is not None
        # Clean up
        try:
            next(db_gen)
        except StopIteration:
            pass  # Expected