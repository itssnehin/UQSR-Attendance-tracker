"""Tests for Attendance model and validation."""

import pytest
from datetime import datetime, date
from app.models.attendance import Attendance, AttendanceValidator, AttendanceCreate
from app.models.run import Run
from pydantic import ValidationError


class TestAttendanceModel:
    """Test Attendance database model."""
    
    def test_create_attendance(self, test_session):
        """Test creating an attendance record."""
        # First create a run
        run = Run(
            date=date(2024, 1, 15),
            session_id="session-123"
        )
        test_session.add(run)
        test_session.commit()
        
        # Create attendance
        attendance = Attendance(
            run_id=run.id,
            runner_name="John Doe"
        )
        test_session.add(attendance)
        test_session.commit()
        
        assert attendance.id is not None
        assert attendance.run_id == run.id
        assert attendance.runner_name == "John Doe"
        assert attendance.registered_at is not None
        assert attendance.run == run
    
    def test_attendance_repr(self, test_session):
        """Test attendance string representation."""
        # Create run first
        run = Run(
            date=date(2024, 1, 15),
            session_id="session-123"
        )
        test_session.add(run)
        test_session.commit()
        
        attendance = Attendance(
            run_id=run.id,
            runner_name="John Doe"
        )
        test_session.add(attendance)
        test_session.commit()
        
        expected = f"<Attendance(id={attendance.id}, run_id={attendance.run_id}, runner_name={attendance.runner_name})>"
        assert repr(attendance) == expected


class TestAttendanceSchemas:
    """Test Attendance Pydantic schemas."""
    
    def test_attendance_create_valid(self):
        """Test valid attendance creation schema."""
        attendance_data = {
            "run_id": 1,
            "runner_name": "John Doe"
        }
        attendance = AttendanceCreate(**attendance_data)
        assert attendance.run_id == 1
        assert attendance.runner_name == "John Doe"
    
    def test_attendance_create_with_special_characters(self):
        """Test attendance creation with special characters in name."""
        valid_names = [
            "Mary-Jane Smith",
            "O'Connor",
            "Dr. Smith",
            "Jean-Luc",
            "Anne-Marie"
        ]
        
        for name in valid_names:
            attendance = AttendanceCreate(run_id=1, runner_name=name)
            assert attendance.runner_name == name
    
    def test_attendance_create_invalid_run_id(self):
        """Test attendance creation with invalid run ID."""
        with pytest.raises(ValidationError) as exc_info:
            AttendanceCreate(run_id=0, runner_name="John Doe")
        assert "Run ID must be a positive integer" in str(exc_info.value)
        
        with pytest.raises(ValidationError) as exc_info:
            AttendanceCreate(run_id=-1, runner_name="John Doe")
        assert "Run ID must be a positive integer" in str(exc_info.value)
    
    def test_attendance_create_invalid_runner_name(self):
        """Test attendance creation with invalid runner name."""
        invalid_names = [
            "",
            "   ",
            "John123",
            "John@Doe",
            "John#Doe",
            "John$Doe"
        ]
        
        for name in invalid_names:
            with pytest.raises(ValidationError):
                AttendanceCreate(run_id=1, runner_name=name)
    
    def test_attendance_create_runner_name_too_long(self):
        """Test attendance creation with runner name too long."""
        with pytest.raises(ValidationError) as exc_info:
            AttendanceCreate(run_id=1, runner_name="a" * 256)
        assert "Runner name too long" in str(exc_info.value)
    
    def test_attendance_create_runner_name_sanitization(self):
        """Test runner name sanitization."""
        attendance = AttendanceCreate(run_id=1, runner_name="  John Doe  ")
        assert attendance.runner_name == "John Doe"


class TestAttendanceValidator:
    """Test Attendance validation utilities."""
    
    def test_validate_runner_name_valid(self):
        """Test valid runner name validation."""
        valid_names = [
            "John Doe",
            "Mary-Jane Smith",
            "O'Connor",
            "Dr. Smith",
            "Jean-Luc",
            "a" * 255  # Max length
        ]
        
        for name in valid_names:
            assert AttendanceValidator.validate_runner_name(name) is True
    
    def test_validate_runner_name_invalid(self):
        """Test invalid runner name validation."""
        invalid_names = [
            "",
            "   ",
            "John123",
            "John@Doe",
            "John#Doe",
            "John$Doe",
            "a" * 256,  # Too long
            123,
            None
        ]
        
        for name in invalid_names:
            assert AttendanceValidator.validate_runner_name(name) is False
    
    def test_sanitize_runner_name(self):
        """Test runner name sanitization."""
        test_cases = [
            ("  John Doe  ", "John Doe"),
            ("John    Doe", "John Doe"),
            ("John\t\nDoe", "John Doe"),
            ("  John   \t  Doe  \n ", "John Doe"),
            ("", ""),
            (123, "")
        ]
        
        for input_name, expected in test_cases:
            assert AttendanceValidator.sanitize_runner_name(input_name) == expected
    
    def test_validate_run_id_valid(self):
        """Test valid run ID validation."""
        assert AttendanceValidator.validate_run_id(1) is True
        assert AttendanceValidator.validate_run_id(100) is True
        assert AttendanceValidator.validate_run_id(999999) is True
    
    def test_validate_run_id_invalid(self):
        """Test invalid run ID validation."""
        invalid_ids = [0, -1, -100, 1.5, 3.14, "1", None, float('inf'), float('nan')]
        
        for run_id in invalid_ids:
            assert AttendanceValidator.validate_run_id(run_id) is False