"""Tests for Run model and validation."""

import pytest
from datetime import datetime, date
from app.models.run import Run, RunValidator, RunCreate, RunUpdate
from pydantic import ValidationError


class TestRunModel:
    """Test Run database model."""
    
    def test_create_run(self, test_session):
        """Test creating a run."""
        run = Run(
            date=date(2024, 1, 15),
            session_id="session-123",
            is_active=True
        )
        test_session.add(run)
        test_session.commit()
        
        assert run.id is not None
        assert run.date == date(2024, 1, 15)
        assert run.session_id == "session-123"
        assert run.is_active is True
        assert run.created_at is not None
    
    def test_run_repr(self, test_session):
        """Test run string representation."""
        run = Run(
            date=date(2024, 1, 15),
            session_id="session-123"
        )
        test_session.add(run)
        test_session.commit()
        
        expected = f"<Run(id={run.id}, date={run.date}, session_id={run.session_id})>"
        assert repr(run) == expected


class TestRunSchemas:
    """Test Run Pydantic schemas."""
    
    def test_run_create_valid(self):
        """Test valid run creation schema."""
        run_data = {
            "date": datetime(2024, 1, 15),
            "session_id": "session-123",
            "is_active": True
        }
        run = RunCreate(**run_data)
        assert run.date == datetime(2024, 1, 15)
        assert run.session_id == "session-123"
        assert run.is_active is True
    
    def test_run_create_default_active(self):
        """Test run creation with default is_active."""
        run_data = {
            "date": datetime(2024, 1, 15),
            "session_id": "session-123"
        }
        run = RunCreate(**run_data)
        assert run.is_active is True
    
    def test_run_create_invalid_session_id(self):
        """Test run creation with invalid session ID."""
        with pytest.raises(ValidationError) as exc_info:
            RunCreate(
                date=datetime(2024, 1, 15),
                session_id="",
                is_active=True
            )
        assert "Session ID cannot be empty" in str(exc_info.value)
    
    def test_run_create_session_id_too_long(self):
        """Test run creation with session ID too long."""
        with pytest.raises(ValidationError) as exc_info:
            RunCreate(
                date=datetime(2024, 1, 15),
                session_id="a" * 256,
                is_active=True
            )
        assert "Session ID too long" in str(exc_info.value)
    
    def test_run_create_invalid_date(self):
        """Test run creation with invalid date."""
        with pytest.raises(ValidationError) as exc_info:
            RunCreate(
                date="invalid-date",
                session_id="session-123",
                is_active=True
            )
        assert "Date must be a datetime object" in str(exc_info.value)
    
    def test_run_update_valid(self):
        """Test valid run update schema."""
        update_data = {"is_active": False}
        run_update = RunUpdate(**update_data)
        assert run_update.is_active is False
    
    def test_run_update_empty(self):
        """Test empty run update schema."""
        run_update = RunUpdate()
        assert run_update.is_active is None


class TestRunValidator:
    """Test Run validation utilities."""
    
    def test_validate_session_id_valid(self):
        """Test valid session ID validation."""
        assert RunValidator.validate_session_id("session-123") is True
        assert RunValidator.validate_session_id("a") is True
        assert RunValidator.validate_session_id("  valid  ") is True
    
    def test_validate_session_id_invalid(self):
        """Test invalid session ID validation."""
        assert RunValidator.validate_session_id("") is False
        assert RunValidator.validate_session_id("   ") is False
        assert RunValidator.validate_session_id("a" * 256) is False
        assert RunValidator.validate_session_id(123) is False
        assert RunValidator.validate_session_id(None) is False
    
    def test_validate_date_valid(self):
        """Test valid date validation."""
        assert RunValidator.validate_date(datetime.now()) is True
        assert RunValidator.validate_date(datetime(2024, 1, 15)) is True
    
    def test_validate_date_invalid(self):
        """Test invalid date validation."""
        assert RunValidator.validate_date("2024-01-15") is False
        assert RunValidator.validate_date(None) is False
        assert RunValidator.validate_date(123) is False
    
    def test_sanitize_session_id(self):
        """Test session ID sanitization."""
        assert RunValidator.sanitize_session_id("  session-123  ") == "session-123"
        assert RunValidator.sanitize_session_id("session-123") == "session-123"
        assert RunValidator.sanitize_session_id("") == ""
        assert RunValidator.sanitize_session_id(123) == ""