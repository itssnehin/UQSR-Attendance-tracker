"""Tests for CalendarConfig model and validation."""

import pytest
from datetime import datetime, date
from app.models.calendar_config import (
    CalendarConfig, 
    CalendarConfigValidator, 
    CalendarConfigCreate, 
    CalendarConfigUpdate,
    CalendarDay
)
from pydantic import ValidationError


class TestCalendarConfigModel:
    """Test CalendarConfig database model."""
    
    def test_create_calendar_config(self, test_session):
        """Test creating a calendar config."""
        config = CalendarConfig(
            date=date(2024, 1, 15),
            has_run=True
        )
        test_session.add(config)
        test_session.commit()
        
        assert config.id is not None
        assert config.date == date(2024, 1, 15)
        assert config.has_run is True
        assert config.updated_at is not None
    
    def test_calendar_config_repr(self, test_session):
        """Test calendar config string representation."""
        config = CalendarConfig(
            date=date(2024, 1, 15),
            has_run=True
        )
        test_session.add(config)
        test_session.commit()
        
        expected = f"<CalendarConfig(id={config.id}, date={config.date}, has_run={config.has_run})>"
        assert repr(config) == expected


class TestCalendarConfigSchemas:
    """Test CalendarConfig Pydantic schemas."""
    
    def test_calendar_config_create_valid(self):
        """Test valid calendar config creation schema."""
        config_data = {
            "date": date(2024, 1, 15),
            "has_run": True
        }
        config = CalendarConfigCreate(**config_data)
        assert config.date == date(2024, 1, 15)
        assert config.has_run is True
    
    def test_calendar_config_create_has_run_false(self):
        """Test calendar config creation with has_run false."""
        config_data = {
            "date": date(2024, 1, 15),
            "has_run": False
        }
        config = CalendarConfigCreate(**config_data)
        assert config.has_run is False
    
    def test_calendar_config_create_invalid_date(self):
        """Test calendar config creation with invalid date."""
        with pytest.raises(ValidationError) as exc_info:
            CalendarConfigCreate(
                date="2024-01-15",
                has_run=True
            )
        assert "Date must be a date object" in str(exc_info.value)
    
    def test_calendar_config_update_valid(self):
        """Test valid calendar config update schema."""
        update_data = {"has_run": False}
        config_update = CalendarConfigUpdate(**update_data)
        assert config_update.has_run is False
    
    def test_calendar_day_valid(self):
        """Test valid calendar day schema."""
        day_data = {
            "date": "2024-01-15",
            "has_run": True,
            "attendance_count": 25,
            "session_id": "session-123"
        }
        day = CalendarDay(**day_data)
        assert day.date == "2024-01-15"
        assert day.has_run is True
        assert day.attendance_count == 25
        assert day.session_id == "session-123"
    
    def test_calendar_day_minimal(self):
        """Test calendar day with minimal data."""
        day_data = {
            "date": "2024-01-15",
            "has_run": False
        }
        day = CalendarDay(**day_data)
        assert day.date == "2024-01-15"
        assert day.has_run is False
        assert day.attendance_count is None
        assert day.session_id is None
    
    def test_calendar_day_invalid_date_format(self):
        """Test calendar day with invalid date format."""
        invalid_dates = [
            "24-01-15",
            "2024/01/15",
            "15-01-2024",
            "2024-13-01",
            "2024-02-30",
            "invalid-date"
        ]
        
        for invalid_date in invalid_dates:
            with pytest.raises(ValidationError):
                CalendarDay(date=invalid_date, has_run=True)


class TestCalendarConfigValidator:
    """Test CalendarConfig validation utilities."""
    
    def test_validate_date_valid(self):
        """Test valid date validation."""
        assert CalendarConfigValidator.validate_date(date.today()) is True
        assert CalendarConfigValidator.validate_date(date(2024, 1, 15)) is True
        assert CalendarConfigValidator.validate_date(date(2023, 12, 31)) is True
    
    def test_validate_date_invalid(self):
        """Test invalid date validation."""
        invalid_dates = [
            "2024-01-15",
            datetime.now(),
            None,
            123,
            "invalid"
        ]
        
        for invalid_date in invalid_dates:
            assert CalendarConfigValidator.validate_date(invalid_date) is False
    
    def test_validate_date_string_valid(self):
        """Test valid date string validation."""
        valid_dates = [
            "2024-01-15",
            "2023-12-31",
            "2024-02-29",  # Leap year
            "2000-02-29"   # Leap year
        ]
        
        for valid_date in valid_dates:
            assert CalendarConfigValidator.validate_date_string(valid_date) is True
    
    def test_validate_date_string_invalid(self):
        """Test invalid date string validation."""
        invalid_dates = [
            "invalid-date",
            "2024-13-01",
            "2024-02-30",
            "2023-02-29",  # Not leap year
            "24-01-15",
            "2024/01/15",
            "15-01-2024",
            ""
        ]
        
        for invalid_date in invalid_dates:
            assert CalendarConfigValidator.validate_date_string(invalid_date) is False
    
    def test_parse_date_string_valid(self):
        """Test valid date string parsing."""
        result = CalendarConfigValidator.parse_date_string("2024-01-15")
        assert result == date(2024, 1, 15)
        
        result = CalendarConfigValidator.parse_date_string("2023-12-31")
        assert result == date(2023, 12, 31)
    
    def test_parse_date_string_invalid(self):
        """Test invalid date string parsing."""
        invalid_dates = [
            "invalid-date",
            "2024-13-01",
            "2024-02-30",
            ""
        ]
        
        for invalid_date in invalid_dates:
            assert CalendarConfigValidator.parse_date_string(invalid_date) is None
    
    def test_format_date_for_database(self):
        """Test date formatting for database."""
        test_date = date(2024, 1, 15)
        result = CalendarConfigValidator.format_date_for_database(test_date)
        assert result == "2024-01-15"
        
        test_date = date(2023, 12, 31)
        result = CalendarConfigValidator.format_date_for_database(test_date)
        assert result == "2023-12-31"
    
    def test_format_date_for_frontend(self):
        """Test date formatting for frontend."""
        test_date = date(2024, 1, 15)
        result = CalendarConfigValidator.format_date_for_frontend(test_date)
        assert result == "2024-01-15"
        
        # Should be consistent with database format
        db_format = CalendarConfigValidator.format_date_for_database(test_date)
        frontend_format = CalendarConfigValidator.format_date_for_frontend(test_date)
        assert db_format == frontend_format