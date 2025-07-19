"""
Unit tests for attendance data retrieval and export functionality
Task 8: Write unit tests for data retrieval, filtering, and CSV export functionality using pytest
"""
import pytest
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
import csv
import io

from app.services.registration_service import RegistrationService
from app.models.run import Run
from app.models.attendance import Attendance
from app.schemas import RegistrationRequest


class TestAttendanceDataRetrieval:
    """Test attendance data retrieval with filtering and pagination"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def registration_service(self, mock_db):
        """Registration service with mocked database"""
        return RegistrationService(mock_db)
    
    @pytest.fixture
    def sample_attendance_data(self):
        """Sample attendance data for testing"""
        today = date.today()
        yesterday = today - timedelta(days=1)
        two_days_ago = today - timedelta(days=2)
        
        # Mock attendance records
        attendance_records = []
        
        # Today's records
        for i in range(3):
            mock_result = Mock()
            mock_result.id = i + 1
            mock_result.runner_name = f"Runner {i + 1}"
            mock_result.registered_at = datetime.combine(today, datetime.min.time()) + timedelta(hours=i)
            mock_result.run_date = today
            mock_result.session_id = f"session_today"
            attendance_records.append(mock_result)
        
        # Yesterday's records
        for i in range(2):
            mock_result = Mock()
            mock_result.id = i + 4
            mock_result.runner_name = f"Runner {i + 4}"
            mock_result.registered_at = datetime.combine(yesterday, datetime.min.time()) + timedelta(hours=i)
            mock_result.run_date = yesterday
            mock_result.session_id = f"session_yesterday"
            attendance_records.append(mock_result)
        
        # Two days ago records
        mock_result = Mock()
        mock_result.id = 6
        mock_result.runner_name = "Runner 6"
        mock_result.registered_at = datetime.combine(two_days_ago, datetime.min.time())
        mock_result.run_date = two_days_ago
        mock_result.session_id = "session_two_days_ago"
        attendance_records.append(mock_result)
        
        return attendance_records
    
    def test_get_attendance_history_no_filters(self, registration_service, mock_db, sample_attendance_data):
        """Test getting attendance history without any filters"""
        # Mock query chain
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = len(sample_attendance_data)
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = sample_attendance_data
        
        mock_db.query.return_value = mock_query
        
        # Test the method
        result = registration_service.get_attendance_history()
        
        # Assertions
        assert result["success"] is True
        assert result["total_count"] == 6
        assert result["page"] == 1
        assert result["page_size"] == 50
        assert result["total_pages"] == 1
        assert result["has_next"] is False
        assert result["has_prev"] is False
        assert len(result["data"]) == 6
        
        # Verify data format
        first_record = result["data"][0]
        assert "id" in first_record
        assert "runner_name" in first_record
        assert "registered_at" in first_record
        assert "run_date" in first_record
        assert "session_id" in first_record
    
    def test_get_attendance_history_with_date_filters(self, registration_service, mock_db, sample_attendance_data):
        """Test getting attendance history with date range filters"""
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        # Filter to only yesterday's records
        filtered_data = [record for record in sample_attendance_data if record.run_date == yesterday]
        
        # Mock query chain
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = len(filtered_data)
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = filtered_data
        
        mock_db.query.return_value = mock_query
        
        # Test with date filters
        start_date = yesterday.strftime('%Y-%m-%d')
        end_date = yesterday.strftime('%Y-%m-%d')
        
        result = registration_service.get_attendance_history(start_date=start_date, end_date=end_date)
        
        # Assertions
        assert result["success"] is True
        assert result["total_count"] == 2
        assert len(result["data"]) == 2
        
        # Verify filter was applied (mock was called with filter)
        mock_query.filter.assert_called()
    
    def test_get_attendance_history_with_pagination(self, registration_service, mock_db, sample_attendance_data):
        """Test getting attendance history with pagination"""
        # Mock query chain for pagination
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 6  # Total records
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = sample_attendance_data[:2]  # First 2 records
        
        mock_db.query.return_value = mock_query
        
        # Test pagination
        result = registration_service.get_attendance_history(page=1, page_size=2)
        
        # Assertions
        assert result["success"] is True
        assert result["total_count"] == 6
        assert result["page"] == 1
        assert result["page_size"] == 2
        assert result["total_pages"] == 3
        assert result["has_next"] is True
        assert result["has_prev"] is False
        assert len(result["data"]) == 2
        
        # Verify pagination was applied
        mock_query.offset.assert_called_with(0)
        mock_query.limit.assert_called_with(2)
    
    def test_get_attendance_history_invalid_date_format(self, registration_service, mock_db, sample_attendance_data):
        """Test handling of invalid date formats"""
        # Mock query chain
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = len(sample_attendance_data)
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = sample_attendance_data
        
        mock_db.query.return_value = mock_query
        
        # Test with invalid date format (should not crash, just ignore invalid dates)
        result = registration_service.get_attendance_history(start_date="invalid-date", end_date="also-invalid")
        
        # Should still return results (ignoring invalid dates)
        assert result["success"] is True
        assert result["total_count"] == 6
    
    def test_get_attendance_history_pagination_edge_cases(self, registration_service, mock_db, sample_attendance_data):
        """Test pagination edge cases"""
        # Mock query chain
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 6
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_db.query.return_value = mock_query
        
        # Test invalid page number (should default to 1)
        result = registration_service.get_attendance_history(page=0, page_size=50)
        assert result["page"] == 1
        
        # Test invalid page size (should default to 50)
        result = registration_service.get_attendance_history(page=1, page_size=0)
        assert result["page_size"] == 50
        
        # Test page size too large (should cap at 1000)
        result = registration_service.get_attendance_history(page=1, page_size=2000)
        assert result["page_size"] == 50  # Should default to 50


class TestCSVExport:
    """Test CSV export functionality"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def registration_service(self, mock_db):
        """Registration service with mocked database"""
        return RegistrationService(mock_db)
    
    @pytest.fixture
    def sample_export_data(self):
        """Sample data for CSV export testing"""
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        records = []
        
        # Create mock records
        for i in range(3):
            mock_result = Mock()
            mock_result.id = i + 1
            mock_result.runner_name = f"Test Runner {i + 1}"
            mock_result.registered_at = datetime.combine(today, datetime.min.time()) + timedelta(hours=i)
            mock_result.run_date = today
            mock_result.session_id = f"session_{i + 1}"
            records.append(mock_result)
        
        return records
    
    def test_export_attendance_csv_with_data(self, registration_service, mock_db, sample_export_data):
        """Test CSV export with data"""
        # Mock query chain
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = sample_export_data
        
        mock_db.query.return_value = mock_query
        
        # Test CSV export
        csv_content = registration_service.export_attendance_csv()
        
        # Parse CSV content
        csv_reader = csv.reader(io.StringIO(csv_content))
        rows = list(csv_reader)
        
        # Verify CSV structure
        assert len(rows) == 4  # Header + 3 data rows
        
        # Verify headers
        expected_headers = ['Runner Name', 'Run Date', 'Registration Time', 'Session ID', 'Attendance ID']
        assert rows[0] == expected_headers
        
        # Verify data rows
        for i, row in enumerate(rows[1:], 1):
            assert row[0] == f"Test Runner {i}"  # Runner Name
            assert row[1] == date.today().strftime('%Y-%m-%d')  # Run Date
            assert row[3] == f"session_{i}"  # Session ID
            assert row[4] == str(i)  # Attendance ID
    
    def test_export_attendance_csv_empty_data(self, registration_service, mock_db):
        """Test CSV export with no data (should still include headers)"""
        # Mock query chain returning empty results
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_db.query.return_value = mock_query
        
        # Test CSV export with no data
        csv_content = registration_service.export_attendance_csv()
        
        # Parse CSV content
        csv_reader = csv.reader(io.StringIO(csv_content))
        rows = list(csv_reader)
        
        # Should have headers even with no data
        assert len(rows) == 1  # Only header row
        expected_headers = ['Runner Name', 'Run Date', 'Registration Time', 'Session ID', 'Attendance ID']
        assert rows[0] == expected_headers
    
    def test_export_attendance_csv_with_date_filters(self, registration_service, mock_db, sample_export_data):
        """Test CSV export with date range filters"""
        # Mock query chain
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = sample_export_data[:2]  # Filtered results
        
        mock_db.query.return_value = mock_query
        
        # Test CSV export with date filters
        start_date = "2024-01-01"
        end_date = "2024-01-31"
        csv_content = registration_service.export_attendance_csv(start_date=start_date, end_date=end_date)
        
        # Parse CSV content
        csv_reader = csv.reader(io.StringIO(csv_content))
        rows = list(csv_reader)
        
        # Should have header + 2 filtered rows
        assert len(rows) == 3
        
        # Verify filter was applied (mock was called with filter)
        mock_query.filter.assert_called()
    
    def test_get_attendance_export_filename(self, registration_service):
        """Test export filename generation"""
        # Test with both dates
        filename = registration_service.get_attendance_export_filename("2024-01-01", "2024-01-31")
        assert filename == "attendance_export_2024-01-01_to_2024-01-31.csv"
        
        # Test with start date only
        filename = registration_service.get_attendance_export_filename("2024-01-01", None)
        assert filename == "attendance_export_from_2024-01-01.csv"
        
        # Test with end date only
        filename = registration_service.get_attendance_export_filename(None, "2024-01-31")
        assert filename == "attendance_export_until_2024-01-31.csv"
        
        # Test with no dates (should use current date)
        filename = registration_service.get_attendance_export_filename(None, None)
        current_date = datetime.now().strftime('%Y-%m-%d')
        assert filename == f"attendance_export_{current_date}.csv"
    
    def test_csv_export_special_characters(self, registration_service, mock_db):
        """Test CSV export handles special characters properly"""
        # Create mock data with special characters
        mock_result = Mock()
        mock_result.id = 1
        mock_result.runner_name = "Test Runner, Jr."  # Contains comma
        mock_result.registered_at = datetime.now()
        mock_result.run_date = date.today()
        mock_result.session_id = "session_1"
        
        # Mock query chain
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_result]
        
        mock_db.query.return_value = mock_query
        
        # Test CSV export
        csv_content = registration_service.export_attendance_csv()
        
        # Parse CSV content
        csv_reader = csv.reader(io.StringIO(csv_content))
        rows = list(csv_reader)
        
        # Verify special characters are handled properly
        assert len(rows) == 2  # Header + 1 data row
        assert rows[1][0] == "Test Runner, Jr."  # Should preserve comma in quoted field


class TestAttendanceExportIntegration:
    """Integration tests for attendance export functionality"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def registration_service(self, mock_db):
        """Registration service with mocked database"""
        return RegistrationService(mock_db)
    
    def test_export_error_handling(self, registration_service, mock_db):
        """Test error handling in export functionality"""
        # Mock database error
        mock_db.query.side_effect = Exception("Database error")
        
        # Should raise exception
        with pytest.raises(Exception) as exc_info:
            registration_service.export_attendance_csv()
        
        assert "Database error" in str(exc_info.value)
    
    def test_filename_generation_error_handling(self, registration_service):
        """Test filename generation error handling"""
        # Test with invalid input (should not crash)
        filename = registration_service.get_attendance_export_filename("invalid", "also-invalid")
        
        # Should return default filename
        assert filename == "attendance_export_invalid_to_also-invalid.csv"
    
    @patch('app.services.registration_service.logger')
    def test_logging_in_export_functions(self, mock_logger, registration_service, mock_db):
        """Test that appropriate logging occurs during export"""
        # Mock successful query
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_db.query.return_value = mock_query
        
        # Test CSV export
        registration_service.export_attendance_csv()
        
        # Verify logging occurred
        mock_logger.info.assert_called()
        
        # Test error logging
        mock_db.query.side_effect = Exception("Test error")
        
        with pytest.raises(Exception):
            registration_service.export_attendance_csv()
        
        mock_logger.error.assert_called()


if __name__ == "__main__":
    pytest.main([__file__])