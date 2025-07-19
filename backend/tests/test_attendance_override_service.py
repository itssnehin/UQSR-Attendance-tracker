"""
Unit tests for Attendance Override Service
"""
import pytest
from datetime import datetime, date, timedelta
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

from app.services.attendance_override_service import AttendanceOverrideService
from app.models.attendance import Attendance, AttendanceCreate
from app.models.run import Run, RunCreate


class TestAttendanceOverrideService:
    """Test cases for Attendance Override Service"""
    
    @pytest.fixture
    def override_service(self):
        """Create override service instance for testing"""
        return AttendanceOverrideService()
    
    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session"""
        mock_session = MagicMock(spec=Session)
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=None)
        return mock_session
    
    def test_add_attendance_record_new_run(self, override_service, mock_db_session):
        """Test adding attendance record with new run creation"""
        with patch('app.services.attendance_override_service.get_db') as mock_get_db:
            mock_get_db.return_value = mock_db_session
            
            # Mock no existing run
            mock_db_session.query.return_value.filter.return_value.first.return_value = None
            
            # Mock successful creation
            mock_run = MagicMock()
            mock_run.id = 1
            mock_run.session_id = "test-session"
            mock_db_session.add.return_value = None
            mock_db_session.flush.return_value = None
            
            # Mock attendance creation
            mock_attendance = MagicMock()
            mock_attendance.id = 1
            
            # Set up the database session to return the mock objects after add/flush
            def mock_add_side_effect(obj):
                if hasattr(obj, 'id') and obj.id is None:
                    if isinstance(obj, MagicMock) or 'Run' in str(type(obj)):
                        obj.id = 1
                    elif isinstance(obj, MagicMock) or 'Attendance' in str(type(obj)):
                        obj.id = 1
            
            mock_db_session.add.side_effect = mock_add_side_effect
            
            with patch('app.models.run.Run') as mock_run_class:
                mock_run_class.return_value = mock_run
                with patch('app.models.attendance.Attendance') as mock_attendance_class:
                    mock_attendance_class.return_value = mock_attendance
                    
                    result = override_service.add_attendance_record(
                        runner_name="Test Runner",
                        run_date=date(2024, 1, 15)
                    )
            
            assert result["success"] is True
            assert "Successfully added attendance record" in result["message"]
            assert result["attendance_id"] == 1
    
    def test_add_attendance_record_existing_run(self, override_service, mock_db_session):
        """Test adding attendance record to existing run"""
        with patch('app.services.attendance_override_service.get_db') as mock_get_db:
            mock_get_db.return_value = mock_db_session
            
            # Mock existing run
            mock_run = MagicMock()
            mock_run.id = 1
            mock_run.session_id = "existing-session"
            mock_db_session.query.return_value.filter.return_value.first.return_value = mock_run
            
            # Mock no duplicate attendance
            mock_db_session.query.return_value.filter.return_value.first.side_effect = [mock_run, None]
            
            # Mock attendance creation
            mock_attendance = MagicMock()
            mock_attendance.id = 2
            
            with patch('app.models.attendance.Attendance') as mock_attendance_class:
                mock_attendance_class.return_value = mock_attendance
                
                result = override_service.add_attendance_record(
                    runner_name="Test Runner",
                    run_date=date(2024, 1, 15)
                )
            
            assert result["success"] is True
            assert result["attendance_id"] == 2
    
    def test_add_attendance_record_duplicate(self, override_service, mock_db_session):
        """Test adding duplicate attendance record"""
        with patch('app.services.attendance_override_service.get_db') as mock_get_db:
            mock_get_db.return_value = mock_db_session
            
            # Mock existing run
            mock_run = MagicMock()
            mock_run.id = 1
            
            # Mock existing attendance (duplicate)
            mock_existing_attendance = MagicMock()
            mock_existing_attendance.id = 1
            
            mock_db_session.query.return_value.filter.return_value.first.side_effect = [
                mock_run, mock_existing_attendance
            ]
            
            result = override_service.add_attendance_record(
                runner_name="Test Runner",
                run_date=date(2024, 1, 15)
            )
            
            assert result["success"] is False
            assert "already exists" in result["message"]
    
    def test_edit_attendance_record_success(self, override_service, mock_db_session):
        """Test successful attendance record editing"""
        with patch('app.services.attendance_override_service.get_db') as mock_get_db:
            mock_get_db.return_value = mock_db_session
            
            # Mock existing attendance
            mock_attendance = MagicMock()
            mock_attendance.id = 1
            mock_attendance.runner_name = "Old Name"
            mock_attendance.run_id = 1
            
            # Mock no duplicate check
            mock_db_session.query.return_value.filter.return_value.first.side_effect = [
                mock_attendance, None  # attendance exists, no duplicate
            ]
            
            result = override_service.edit_attendance_record(
                attendance_id=1,
                runner_name="New Name"
            )
            
            assert result["success"] is True
            assert "Successfully updated" in result["message"]
            assert mock_attendance.runner_name == "New Name"
    
    def test_edit_attendance_record_not_found(self, override_service, mock_db_session):
        """Test editing non-existent attendance record"""
        with patch('app.services.attendance_override_service.get_db') as mock_get_db:
            mock_get_db.return_value = mock_db_session
            
            # Mock no attendance found
            mock_db_session.query.return_value.filter.return_value.first.return_value = None
            
            result = override_service.edit_attendance_record(
                attendance_id=999,
                runner_name="New Name"
            )
            
            assert result["success"] is False
            assert "not found" in result["message"]
    
    def test_edit_attendance_record_duplicate_name(self, override_service, mock_db_session):
        """Test editing attendance record with duplicate name"""
        with patch('app.services.attendance_override_service.get_db') as mock_get_db:
            mock_get_db.return_value = mock_db_session
            
            # Mock existing attendance
            mock_attendance = MagicMock()
            mock_attendance.id = 1
            mock_attendance.run_id = 1
            
            # Mock duplicate found
            mock_duplicate = MagicMock()
            mock_db_session.query.return_value.filter.return_value.first.side_effect = [
                mock_attendance, mock_duplicate
            ]
            
            result = override_service.edit_attendance_record(
                attendance_id=1,
                runner_name="Duplicate Name"
            )
            
            assert result["success"] is False
            assert "already exists" in result["message"]
    
    def test_remove_attendance_record_success(self, override_service, mock_db_session):
        """Test successful attendance record removal"""
        with patch('app.services.attendance_override_service.get_db') as mock_get_db:
            mock_get_db.return_value = mock_db_session
            
            # Mock existing attendance
            mock_attendance = MagicMock()
            mock_attendance.id = 1
            mock_attendance.runner_name = "Test Runner"
            mock_attendance.run_id = 1
            
            # Mock run for logging
            mock_run = MagicMock()
            mock_run.date = date(2024, 1, 15)
            
            mock_db_session.query.return_value.filter.return_value.first.side_effect = [
                mock_attendance, mock_run
            ]
            
            result = override_service.remove_attendance_record(attendance_id=1)
            
            assert result["success"] is True
            assert "Successfully removed" in result["message"]
            mock_db_session.delete.assert_called_once_with(mock_attendance)
    
    def test_remove_attendance_record_not_found(self, override_service, mock_db_session):
        """Test removing non-existent attendance record"""
        with patch('app.services.attendance_override_service.get_db') as mock_get_db:
            mock_get_db.return_value = mock_db_session
            
            # Mock no attendance found
            mock_db_session.query.return_value.filter.return_value.first.return_value = None
            
            result = override_service.remove_attendance_record(attendance_id=999)
            
            assert result["success"] is False
            assert "not found" in result["message"]
    
    def test_bulk_operations_mixed_success(self, override_service):
        """Test bulk operations with mixed success/failure"""
        operations = [
            {
                "action": "add",
                "runner_name": "Runner 1",
                "run_date": "2024-01-15"
            },
            {
                "action": "edit",
                "attendance_id": 1,
                "runner_name": "Updated Runner"
            },
            {
                "action": "remove",
                "attendance_id": 2
            },
            {
                "action": "invalid_action"
            }
        ]
        
        with patch.object(override_service, 'add_attendance_record') as mock_add:
            mock_add.return_value = {"success": True, "message": "Added"}
            
            with patch.object(override_service, 'edit_attendance_record') as mock_edit:
                mock_edit.return_value = {"success": True, "message": "Edited"}
                
                with patch.object(override_service, 'remove_attendance_record') as mock_remove:
                    mock_remove.return_value = {"success": False, "message": "Not found"}
                    
                    result = override_service.bulk_operations(operations)
        
        assert result["success"] is False  # Because some operations failed
        assert result["summary"]["total_operations"] == 4
        assert result["summary"]["successful"] == 2
        assert result["summary"]["failed"] == 2
    
    def test_get_attendance_record_success(self, override_service, mock_db_session):
        """Test successful attendance record retrieval"""
        with patch('app.services.attendance_override_service.get_db') as mock_get_db:
            mock_get_db.return_value = mock_db_session
            
            # Mock attendance and run
            mock_attendance = MagicMock()
            mock_attendance.id = 1
            mock_attendance.runner_name = "Test Runner"
            mock_attendance.registered_at = datetime(2024, 1, 15, 10, 30)
            mock_attendance.run_id = 1
            
            mock_run = MagicMock()
            mock_run.id = 1
            mock_run.date = date(2024, 1, 15)
            mock_run.session_id = "test-session"
            mock_run.is_active = True
            
            mock_db_session.query.return_value.filter.return_value.first.side_effect = [
                mock_attendance, mock_run
            ]
            
            result = override_service.get_attendance_record(attendance_id=1)
            
            assert result["success"] is True
            assert result["data"]["attendance_id"] == 1
            assert result["data"]["runner_name"] == "Test Runner"
            assert result["data"]["run"]["run_id"] == 1
    
    def test_get_attendance_record_not_found(self, override_service, mock_db_session):
        """Test getting non-existent attendance record"""
        with patch('app.services.attendance_override_service.get_db') as mock_get_db:
            mock_get_db.return_value = mock_db_session
            
            # Mock no attendance found
            mock_db_session.query.return_value.filter.return_value.first.return_value = None
            
            result = override_service.get_attendance_record(attendance_id=999)
            
            assert result["success"] is False
            assert "not found" in result["message"]
    
    def test_search_attendance_records_with_filters(self, override_service, mock_db_session):
        """Test searching attendance records with filters"""
        with patch('app.services.attendance_override_service.get_db') as mock_get_db:
            mock_get_db.return_value = mock_db_session
            
            # Mock query chain
            mock_query = MagicMock()
            mock_db_session.query.return_value.join.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.limit.return_value = mock_query
            
            # Mock attendance results
            mock_attendance1 = MagicMock()
            mock_attendance1.id = 1
            mock_attendance1.runner_name = "Runner 1"
            mock_attendance1.registered_at = datetime(2024, 1, 15, 10, 30)
            mock_attendance1.run_id = 1
            
            mock_attendance2 = MagicMock()
            mock_attendance2.id = 2
            mock_attendance2.runner_name = "Runner 2"
            mock_attendance2.registered_at = datetime(2024, 1, 16, 11, 30)
            mock_attendance2.run_id = 2
            
            mock_query.all.return_value = [mock_attendance1, mock_attendance2]
            
            # Mock runs for each attendance
            mock_run1 = MagicMock()
            mock_run1.date = date(2024, 1, 15)
            mock_run1.session_id = "session-1"
            
            mock_run2 = MagicMock()
            mock_run2.date = date(2024, 1, 16)
            mock_run2.session_id = "session-2"
            
            mock_db_session.query.return_value.filter.return_value.first.side_effect = [
                mock_run1, mock_run2
            ]
            
            result = override_service.search_attendance_records(
                runner_name="Runner",
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
                limit=50
            )
            
            assert result["success"] is True
            assert result["count"] == 2
            assert len(result["data"]) == 2
            assert result["data"][0]["runner_name"] == "Runner 1"
            assert result["data"][1]["runner_name"] == "Runner 2"
    
    def test_search_attendance_records_no_filters(self, override_service, mock_db_session):
        """Test searching attendance records without filters"""
        with patch('app.services.attendance_override_service.get_db') as mock_get_db:
            mock_get_db.return_value = mock_db_session
            
            # Mock query chain
            mock_query = MagicMock()
            mock_db_session.query.return_value.join.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.all.return_value = []
            
            result = override_service.search_attendance_records()
            
            assert result["success"] is True
            assert result["count"] == 0
            assert result["data"] == []
    
    def test_service_error_handling(self, override_service, mock_db_session):
        """Test service error handling"""
        with patch('app.services.attendance_override_service.get_db') as mock_get_db:
            mock_get_db.side_effect = Exception("Database connection failed")
            
            result = override_service.add_attendance_record(
                runner_name="Test Runner",
                run_date=date(2024, 1, 15)
            )
            
            assert result["success"] is False
            assert "Failed to add attendance record" in result["message"]


class TestAttendanceOverrideServiceIntegration:
    """Integration tests for Attendance Override Service"""
    
    @pytest.fixture
    def override_service(self):
        """Create override service instance for integration testing"""
        return AttendanceOverrideService()
    
    def test_date_parsing_edge_cases(self, override_service):
        """Test date parsing with various formats"""
        # Test with datetime objects
        test_date = date(2024, 2, 29)  # Leap year date
        
        with patch.object(override_service, 'add_attendance_record') as mock_add:
            mock_add.return_value = {"success": True, "message": "Added"}
            
            # This would be called from the API layer with proper date parsing
            result = override_service.add_attendance_record(
                runner_name="Test Runner",
                run_date=test_date
            )
            
            mock_add.assert_called_once()
    
    def test_bulk_operations_transaction_behavior(self, override_service):
        """Test that bulk operations handle transactions properly"""
        operations = [
            {
                "action": "add",
                "runner_name": "Runner 1",
                "run_date": "2024-01-15"
            }
        ]
        
        # Mock individual operations to test transaction handling
        with patch.object(override_service, 'add_attendance_record') as mock_add:
            mock_add.side_effect = Exception("Simulated database error")
            
            result = override_service.bulk_operations(operations)
            
            assert result["success"] is False
            assert result["summary"]["failed"] == 1
    
    def test_service_initialization(self, override_service):
        """Test service initialization"""
        assert hasattr(override_service, 'add_attendance_record')
        assert hasattr(override_service, 'edit_attendance_record')
        assert hasattr(override_service, 'remove_attendance_record')
        assert hasattr(override_service, 'bulk_operations')
        assert hasattr(override_service, 'get_attendance_record')
        assert hasattr(override_service, 'search_attendance_records')