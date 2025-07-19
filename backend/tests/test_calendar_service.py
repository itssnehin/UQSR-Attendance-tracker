"""
Unit tests for Calendar Service
"""
import pytest
from datetime import date, datetime
from sqlalchemy.orm import Session
from app.services.calendar_service import CalendarService
from app.models.calendar_config import CalendarConfig
from app.models.run import Run
from app.models.attendance import Attendance


class TestCalendarService:
    """Test Calendar Service functionality"""
    
    def test_configure_run_day_new_date(self, test_session: Session):
        """Test configuring a new run day"""
        service = CalendarService(test_session)
        target_date = date(2024, 1, 15)
        
        result = service.configure_run_day(target_date, True)
        
        assert result["success"] is True
        assert "Calendar configuration updated" in result["message"]
        assert result["date"] == "2024-01-15"
        assert result["has_run"] is True
        
        # Verify database record was created
        config = test_session.query(CalendarConfig).filter(
            CalendarConfig.date == target_date
        ).first()
        assert config is not None
        assert config.has_run is True
        
        # Verify Run record was created
        run = test_session.query(Run).filter(Run.date == target_date).first()
        assert run is not None
        assert run.is_active is True
        assert run.session_id is not None
    
    def test_configure_run_day_update_existing(self, test_session: Session):
        """Test updating existing run day configuration"""
        service = CalendarService(test_session)
        target_date = date(2024, 1, 15)
        
        # Create initial configuration
        initial_config = CalendarConfig(date=target_date, has_run=True)
        test_session.add(initial_config)
        test_session.commit()
        
        # Update configuration
        result = service.configure_run_day(target_date, False)
        
        assert result["success"] is True
        assert result["has_run"] is False
        
        # Verify database record was updated
        config = test_session.query(CalendarConfig).filter(
            CalendarConfig.date == target_date
        ).first()
        assert config.has_run is False
    
    def test_configure_run_day_deactivates_run(self, test_session: Session):
        """Test that setting has_run=False deactivates existing run"""
        service = CalendarService(test_session)
        target_date = date(2024, 1, 15)
        
        # Create run and config
        config = CalendarConfig(date=target_date, has_run=True)
        run = Run(date=target_date, session_id="test-session", is_active=True)
        test_session.add(config)
        test_session.add(run)
        test_session.commit()
        
        # Set has_run to False
        result = service.configure_run_day(target_date, False)
        
        assert result["success"] is True
        
        # Verify run was deactivated
        updated_run = test_session.query(Run).filter(Run.date == target_date).first()
        assert updated_run.is_active is False
    
    def test_get_calendar_configuration_empty(self, test_session: Session):
        """Test getting calendar configuration when no data exists"""
        service = CalendarService(test_session)
        
        result = service.get_calendar_configuration()
        
        assert result["success"] is True
        assert result["data"] == []
        assert "retrieved successfully" in result["message"]
    
    def test_get_calendar_configuration_with_data(self, test_session: Session):
        """Test getting calendar configuration with existing data"""
        service = CalendarService(test_session)
        
        # Create test data
        date1 = date(2024, 1, 15)
        date2 = date(2024, 1, 16)
        
        config1 = CalendarConfig(date=date1, has_run=True)
        config2 = CalendarConfig(date=date2, has_run=False)
        run1 = Run(date=date1, session_id="session-1", is_active=True)
        
        test_session.add_all([config1, config2, run1])
        test_session.commit()
        
        # Add attendance for run1
        attendance = Attendance(run_id=run1.id, runner_name="Test Runner")
        test_session.add(attendance)
        test_session.commit()
        
        result = service.get_calendar_configuration()
        
        assert result["success"] is True
        assert len(result["data"]) == 2
        
        # Check first day (has run)
        day1 = next(d for d in result["data"] if d["date"] == "2024-01-15")
        assert day1["has_run"] is True
        assert day1["session_id"] == "session-1"
        assert day1["attendance_count"] == 1
        
        # Check second day (no run)
        day2 = next(d for d in result["data"] if d["date"] == "2024-01-16")
        assert day2["has_run"] is False
        assert day2["session_id"] is None
        assert day2["attendance_count"] is None
    
    def test_get_calendar_configuration_date_range(self, test_session: Session):
        """Test getting calendar configuration with date range filters"""
        service = CalendarService(test_session)
        
        # Create test data across multiple dates
        dates = [date(2024, 1, 10), date(2024, 1, 15), date(2024, 1, 20)]
        for d in dates:
            config = CalendarConfig(date=d, has_run=True)
            test_session.add(config)
        test_session.commit()
        
        # Test with date range
        result = service.get_calendar_configuration(
            start_date=date(2024, 1, 12),
            end_date=date(2024, 1, 18)
        )
        
        assert result["success"] is True
        assert len(result["data"]) == 1
        assert result["data"][0]["date"] == "2024-01-15"
    
    def test_get_today_status_no_run(self, test_session: Session):
        """Test getting today's status when no run is scheduled"""
        service = CalendarService(test_session)
        
        result = service.get_today_status()
        
        assert result["success"] is True
        assert result["has_run_today"] is False
        assert result["session_id"] is None
        assert result["attendance_count"] == 0
        assert "No run scheduled" in result["message"]
    
    def test_get_today_status_with_run(self, test_session: Session):
        """Test getting today's status when run is scheduled"""
        service = CalendarService(test_session)
        today = date.today()
        
        # Create today's configuration and run
        config = CalendarConfig(date=today, has_run=True)
        run = Run(date=today, session_id="today-session", is_active=True)
        test_session.add_all([config, run])
        test_session.commit()
        
        # Add some attendance
        attendance1 = Attendance(run_id=run.id, runner_name="Runner 1")
        attendance2 = Attendance(run_id=run.id, runner_name="Runner 2")
        test_session.add_all([attendance1, attendance2])
        test_session.commit()
        
        result = service.get_today_status()
        
        assert result["success"] is True
        assert result["has_run_today"] is True
        assert result["session_id"] == "today-session"
        assert result["attendance_count"] == 2
        assert "2 attendees" in result["message"]
    
    def test_get_today_status_config_without_run(self, test_session: Session):
        """Test getting today's status when config exists but no run record"""
        service = CalendarService(test_session)
        today = date.today()
        
        # Create only configuration, no run record
        config = CalendarConfig(date=today, has_run=True)
        test_session.add(config)
        test_session.commit()
        
        result = service.get_today_status()
        
        assert result["success"] is True
        assert result["has_run_today"] is True
        assert result["session_id"] is None
        assert result["attendance_count"] == 0
        assert "scheduled but not yet active" in result["message"]
    
    def test_ensure_run_exists_creates_new(self, test_session: Session):
        """Test _ensure_run_exists creates new run"""
        service = CalendarService(test_session)
        target_date = date(2024, 1, 15)
        
        service._ensure_run_exists(target_date)
        test_session.commit()  # Commit the transaction to persist the new run
        
        run = test_session.query(Run).filter(Run.date == target_date).first()
        assert run is not None
        assert run.is_active is True
        assert run.session_id is not None
        assert target_date.strftime('%Y%m%d') in run.session_id
    
    def test_ensure_run_exists_reactivates_existing(self, test_session: Session):
        """Test _ensure_run_exists reactivates inactive run"""
        service = CalendarService(test_session)
        target_date = date(2024, 1, 15)
        
        # Create inactive run
        run = Run(date=target_date, session_id="test-session", is_active=False)
        test_session.add(run)
        test_session.commit()
        
        service._ensure_run_exists(target_date)
        
        updated_run = test_session.query(Run).filter(Run.date == target_date).first()
        assert updated_run.is_active is True
    
    def test_deactivate_run(self, test_session: Session):
        """Test _deactivate_run deactivates active run"""
        service = CalendarService(test_session)
        target_date = date(2024, 1, 15)
        
        # Create active run
        run = Run(date=target_date, session_id="test-session", is_active=True)
        test_session.add(run)
        test_session.commit()
        
        service._deactivate_run(target_date)
        
        updated_run = test_session.query(Run).filter(Run.date == target_date).first()
        assert updated_run.is_active is False
    
    def test_generate_session_id_format(self, test_session: Session):
        """Test session ID generation format"""
        service = CalendarService(test_session)
        target_date = date(2024, 1, 15)
        
        session_id = service._generate_session_id(target_date)
        
        assert session_id.startswith("20240115-")
        assert len(session_id) == 17  # YYYYMMDD-XXXXXXXX (8+1+8)
    
    def test_get_run_by_session_id(self, test_session: Session):
        """Test getting run by session ID"""
        service = CalendarService(test_session)
        
        # Create test run
        run = Run(date=date(2024, 1, 15), session_id="test-session", is_active=True)
        test_session.add(run)
        test_session.commit()
        
        result = service.get_run_by_session_id("test-session")
        
        assert result is not None
        assert result.session_id == "test-session"
        assert result.is_active is True
    
    def test_get_run_by_session_id_inactive(self, test_session: Session):
        """Test getting inactive run by session ID returns None"""
        service = CalendarService(test_session)
        
        # Create inactive run
        run = Run(date=date(2024, 1, 15), session_id="test-session", is_active=False)
        test_session.add(run)
        test_session.commit()
        
        result = service.get_run_by_session_id("test-session")
        
        assert result is None
    
    def test_validate_run_date_true(self, test_session: Session):
        """Test validate_run_date returns True for configured run day"""
        service = CalendarService(test_session)
        target_date = date(2024, 1, 15)
        
        # Create configuration
        config = CalendarConfig(date=target_date, has_run=True)
        test_session.add(config)
        test_session.commit()
        
        result = service.validate_run_date(target_date)
        
        assert result is True
    
    def test_validate_run_date_false(self, test_session: Session):
        """Test validate_run_date returns False for non-run day"""
        service = CalendarService(test_session)
        target_date = date(2024, 1, 15)
        
        # Create configuration with has_run=False
        config = CalendarConfig(date=target_date, has_run=False)
        test_session.add(config)
        test_session.commit()
        
        result = service.validate_run_date(target_date)
        
        assert result is False
    
    def test_validate_run_date_no_config(self, test_session: Session):
        """Test validate_run_date returns False when no configuration exists"""
        service = CalendarService(test_session)
        target_date = date(2024, 1, 15)
        
        result = service.validate_run_date(target_date)
        
        assert result is False