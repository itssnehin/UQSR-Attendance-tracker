"""
Unit tests for Registration Service
"""
import pytest
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.services.registration_service import RegistrationService
from app.models.run import Run
from app.models.attendance import Attendance
from app.models.calendar_config import CalendarConfig
from app.schemas import RegistrationRequest


class TestRegistrationService:
    """Test cases for RegistrationService"""
    
    def test_register_attendance_success(self, test_session: Session):
        """Test successful attendance registration"""
        # Create a test run
        test_run = Run(
            date=date.today(),
            session_id="test-session-123",
            is_active=True,
            created_at=datetime.utcnow()
        )
        test_session.add(test_run)
        test_session.commit()
        test_session.refresh(test_run)
        
        # Create registration request
        registration = RegistrationRequest(
            session_id="test-session-123",
            runner_name="John Doe"
        )
        
        # Test registration
        service = RegistrationService(test_session)
        result = service.register_attendance(registration)
        
        # Assertions
        assert result.success is True
        assert "Registration successful" in result.message
        assert result.current_count == 1
        assert result.runner_name == "John Doe"
        
        # Verify attendance was created in database
        attendance = test_session.query(Attendance).filter(
            Attendance.run_id == test_run.id
        ).first()
        assert attendance is not None
        assert attendance.runner_name == "John Doe"
        assert attendance.run_id == test_run.id
    
    def test_register_attendance_duplicate_prevention(self, test_session: Session):
        """Test duplicate registration prevention"""
        # Create a test run
        test_run = Run(
            date=date.today(),
            session_id="test-session-456",
            is_active=True,
            created_at=datetime.utcnow()
        )
        test_session.add(test_run)
        test_session.commit()
        test_session.refresh(test_run)
        
        # Create first attendance
        first_attendance = Attendance(
            run_id=test_run.id,
            runner_name="Jane Smith",
            registered_at=datetime.utcnow()
        )
        test_session.add(first_attendance)
        test_session.commit()
        
        # Try to register the same runner again
        registration = RegistrationRequest(
            session_id="test-session-456",
            runner_name="Jane Smith"
        )
        
        service = RegistrationService(test_session)
        result = service.register_attendance(registration)
        
        # Assertions
        assert result.success is False
        assert "already registered" in result.message.lower()
        assert result.current_count == 1
        assert result.runner_name == "Jane Smith"
        
        # Verify only one attendance record exists
        attendance_count = test_session.query(Attendance).filter(
            Attendance.run_id == test_run.id
        ).count()
        assert attendance_count == 1
    
    def test_register_attendance_invalid_session_id(self, test_session: Session):
        """Test registration with invalid session ID"""
        registration = RegistrationRequest(
            session_id="invalid-session-id",
            runner_name="Bob Wilson"
        )
        
        service = RegistrationService(test_session)
        result = service.register_attendance(registration)
        
        # Assertions
        assert result.success is False
        assert "Invalid session ID" in result.message
        assert result.current_count == 0
    
    def test_register_attendance_inactive_run(self, test_session: Session):
        """Test registration with inactive run"""
        # Create an inactive test run
        test_run = Run(
            date=date.today(),
            session_id="inactive-session-789",
            is_active=False,
            created_at=datetime.utcnow()
        )
        test_session.add(test_run)
        test_session.commit()
        
        registration = RegistrationRequest(
            session_id="inactive-session-789",
            runner_name="Alice Brown"
        )
        
        service = RegistrationService(test_session)
        result = service.register_attendance(registration)
        
        # Assertions
        assert result.success is False
        assert "Invalid session ID" in result.message
        assert result.current_count == 0
    
    def test_register_attendance_name_trimming(self, test_session: Session):
        """Test that runner names are properly trimmed"""
        # Create a test run
        test_run = Run(
            date=date.today(),
            session_id="test-session-trim",
            is_active=True,
            created_at=datetime.utcnow()
        )
        test_session.add(test_run)
        test_session.commit()
        test_session.refresh(test_run)
        
        # Register with name that has extra whitespace
        registration = RegistrationRequest(
            session_id="test-session-trim",
            runner_name="  Charlie Davis  "
        )
        
        service = RegistrationService(test_session)
        result = service.register_attendance(registration)
        
        # Assertions
        assert result.success is True
        
        # Verify name was trimmed in database
        attendance = test_session.query(Attendance).filter(
            Attendance.run_id == test_run.id
        ).first()
        assert attendance.runner_name == "Charlie Davis"
    
    def test_get_today_attendance_count_with_run(self, test_session: Session):
        """Test getting today's attendance count when run exists"""
        # Create today's run
        today_run = Run(
            date=date.today(),
            session_id="today-session",
            is_active=True,
            created_at=datetime.utcnow()
        )
        test_session.add(today_run)
        test_session.commit()
        test_session.refresh(today_run)
        
        # Add some attendances
        attendances = [
            Attendance(run_id=today_run.id, runner_name="Runner 1", registered_at=datetime.utcnow()),
            Attendance(run_id=today_run.id, runner_name="Runner 2", registered_at=datetime.utcnow()),
            Attendance(run_id=today_run.id, runner_name="Runner 3", registered_at=datetime.utcnow())
        ]
        for attendance in attendances:
            test_session.add(attendance)
        test_session.commit()
        
        service = RegistrationService(test_session)
        result = service.get_today_attendance_count()
        
        # Assertions
        assert result["success"] is True
        assert result["count"] == 3
        assert result["has_run_today"] is True
        assert result["session_id"] == "today-session"
        assert "3 runners" in result["message"]
    
    def test_get_today_attendance_count_no_run(self, test_session: Session):
        """Test getting today's attendance count when no run exists"""
        service = RegistrationService(test_session)
        result = service.get_today_attendance_count()
        
        # Assertions
        assert result["success"] is True
        assert result["count"] == 0
        assert result["has_run_today"] is False
        assert "No run scheduled" in result["message"]
    
    def test_get_attendance_count_for_run(self, test_session: Session):
        """Test getting attendance count for specific run"""
        # Create a test run
        test_run = Run(
            date=date.today(),
            session_id="count-test-session",
            is_active=True,
            created_at=datetime.utcnow()
        )
        test_session.add(test_run)
        test_session.commit()
        test_session.refresh(test_run)
        
        # Add attendances
        attendances = [
            Attendance(run_id=test_run.id, runner_name="Runner A", registered_at=datetime.utcnow()),
            Attendance(run_id=test_run.id, runner_name="Runner B", registered_at=datetime.utcnow())
        ]
        for attendance in attendances:
            test_session.add(attendance)
        test_session.commit()
        
        service = RegistrationService(test_session)
        count = service.get_attendance_count_for_run(test_run.id)
        
        assert count == 2
    
    def test_get_attendance_count_for_nonexistent_run(self, test_session: Session):
        """Test getting attendance count for non-existent run"""
        service = RegistrationService(test_session)
        count = service.get_attendance_count_for_run(99999)
        
        assert count == 0
    
    def test_get_attendance_history_no_filters(self, test_session: Session):
        """Test getting attendance history without date filters"""
        # Create test runs and attendances
        run1 = Run(
            date=date(2024, 1, 15),
            session_id="history-session-1",
            is_active=True,
            created_at=datetime.utcnow()
        )
        run2 = Run(
            date=date(2024, 1, 16),
            session_id="history-session-2",
            is_active=True,
            created_at=datetime.utcnow()
        )
        test_session.add_all([run1, run2])
        test_session.commit()
        test_session.refresh(run1)
        test_session.refresh(run2)
        
        # Add attendances
        attendances = [
            Attendance(run_id=run1.id, runner_name="History Runner 1", registered_at=datetime(2024, 1, 15, 10, 0)),
            Attendance(run_id=run1.id, runner_name="History Runner 2", registered_at=datetime(2024, 1, 15, 10, 5)),
            Attendance(run_id=run2.id, runner_name="History Runner 3", registered_at=datetime(2024, 1, 16, 10, 0))
        ]
        for attendance in attendances:
            test_session.add(attendance)
        test_session.commit()
        
        service = RegistrationService(test_session)
        result = service.get_attendance_history()
        
        # Assertions
        assert result["success"] is True
        assert result["total_count"] == 3
        assert len(result["data"]) == 3
        
        # Check data structure
        first_record = result["data"][0]
        assert "id" in first_record
        assert "runner_name" in first_record
        assert "registered_at" in first_record
        assert "run_date" in first_record
        assert "session_id" in first_record
    
    def test_get_attendance_history_with_date_filters(self, test_session: Session):
        """Test getting attendance history with date filters"""
        # Create test runs
        run1 = Run(
            date=date(2024, 1, 10),
            session_id="filter-session-1",
            is_active=True,
            created_at=datetime.utcnow()
        )
        run2 = Run(
            date=date(2024, 1, 15),
            session_id="filter-session-2",
            is_active=True,
            created_at=datetime.utcnow()
        )
        run3 = Run(
            date=date(2024, 1, 20),
            session_id="filter-session-3",
            is_active=True,
            created_at=datetime.utcnow()
        )
        test_session.add_all([run1, run2, run3])
        test_session.commit()
        test_session.refresh(run1)
        test_session.refresh(run2)
        test_session.refresh(run3)
        
        # Add attendances
        attendances = [
            Attendance(run_id=run1.id, runner_name="Filter Runner 1", registered_at=datetime.utcnow()),
            Attendance(run_id=run2.id, runner_name="Filter Runner 2", registered_at=datetime.utcnow()),
            Attendance(run_id=run3.id, runner_name="Filter Runner 3", registered_at=datetime.utcnow())
        ]
        for attendance in attendances:
            test_session.add(attendance)
        test_session.commit()
        
        service = RegistrationService(test_session)
        result = service.get_attendance_history(start_date="2024-01-12", end_date="2024-01-18")
        
        # Should only return the middle run (2024-01-15)
        assert result["success"] is True
        assert result["total_count"] == 1
        assert len(result["data"]) == 1
        assert result["data"][0]["runner_name"] == "Filter Runner 2"
    
    def test_get_attendance_history_invalid_date_format(self, test_session: Session):
        """Test getting attendance history with invalid date format"""
        service = RegistrationService(test_session)
        # Should not raise exception, just ignore invalid dates
        result = service.get_attendance_history(start_date="invalid-date", end_date="2024-01-15")
        
        assert result["success"] is True
        assert isinstance(result["data"], list)
    
    def test_validate_session_id_valid(self, test_session: Session):
        """Test session ID validation with valid session"""
        # Create a test run
        test_run = Run(
            date=date.today(),
            session_id="valid-session-id",
            is_active=True,
            created_at=datetime.utcnow()
        )
        test_session.add(test_run)
        test_session.commit()
        
        service = RegistrationService(test_session)
        is_valid = service.validate_session_id("valid-session-id")
        
        assert is_valid is True
    
    def test_validate_session_id_invalid(self, test_session: Session):
        """Test session ID validation with invalid session"""
        service = RegistrationService(test_session)
        is_valid = service.validate_session_id("invalid-session-id")
        
        assert is_valid is False
    
    def test_validate_session_id_inactive_run(self, test_session: Session):
        """Test session ID validation with inactive run"""
        # Create an inactive test run
        test_run = Run(
            date=date.today(),
            session_id="inactive-session-id",
            is_active=False,
            created_at=datetime.utcnow()
        )
        test_session.add(test_run)
        test_session.commit()
        
        service = RegistrationService(test_session)
        is_valid = service.validate_session_id("inactive-session-id")
        
        assert is_valid is False
    
    def test_get_run_by_session_id_valid(self, test_session: Session):
        """Test getting run by valid session ID"""
        # Create a test run
        test_run = Run(
            date=date.today(),
            session_id="get-run-session",
            is_active=True,
            created_at=datetime.utcnow()
        )
        test_session.add(test_run)
        test_session.commit()
        test_session.refresh(test_run)
        
        service = RegistrationService(test_session)
        found_run = service.get_run_by_session_id("get-run-session")
        
        assert found_run is not None
        assert found_run.id == test_run.id
        assert found_run.session_id == "get-run-session"
    
    def test_get_run_by_session_id_invalid(self, test_session: Session):
        """Test getting run by invalid session ID"""
        service = RegistrationService(test_session)
        found_run = service.get_run_by_session_id("nonexistent-session")
        
        assert found_run is None
    
    def test_concurrent_registration_prevention(self, test_session: Session):
        """Test that concurrent registrations are handled properly"""
        # Create a test run
        test_run = Run(
            date=date.today(),
            session_id="concurrent-session",
            is_active=True,
            created_at=datetime.utcnow()
        )
        test_session.add(test_run)
        test_session.commit()
        test_session.refresh(test_run)
        
        # Create first registration
        registration1 = RegistrationRequest(
            session_id="concurrent-session",
            runner_name="Concurrent Runner"
        )
        
        service1 = RegistrationService(test_session)
        result1 = service1.register_attendance(registration1)
        
        # Create second registration with same name (simulating concurrent request)
        registration2 = RegistrationRequest(
            session_id="concurrent-session",
            runner_name="Concurrent Runner"
        )
        
        service2 = RegistrationService(test_session)
        result2 = service2.register_attendance(registration2)
        
        # First should succeed, second should fail
        assert result1.success is True
        assert result2.success is False
        assert "already registered" in result2.message.lower()
        
        # Verify only one attendance record exists
        attendance_count = test_session.query(Attendance).filter(
            Attendance.run_id == test_run.id
        ).count()
        assert attendance_count == 1