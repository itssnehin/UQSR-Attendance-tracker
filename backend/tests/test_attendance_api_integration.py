"""
Integration tests for attendance API endpoints
Task 8: Integration tests for the new attendance history and export endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime, date, timedelta

from app.main import app


class TestAttendanceAPIIntegration:
    """Integration tests for attendance API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Test client for FastAPI app"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_registration_service(self):
        """Mock registration service"""
        return Mock()
    
    def test_get_attendance_history_endpoint(self, client):
        """Test GET /api/attendance/history endpoint"""
        # Mock the database dependency
        with patch('app.routes.registration.get_db') as mock_get_db, \
             patch('app.routes.registration.RegistrationService') as mock_service_class:
            
            # Setup mock service
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            # Mock response data
            mock_response = {
                "success": True,
                "data": [
                    {
                        "id": 1,
                        "runner_name": "Test Runner",
                        "registered_at": "2024-01-15T10:00:00",
                        "run_date": "2024-01-15",
                        "session_id": "session_123"
                    }
                ],
                "total_count": 1,
                "page": 1,
                "page_size": 50,
                "total_pages": 1,
                "has_next": False,
                "has_prev": False,
                "message": "Retrieved 1 of 1 attendance records"
            }
            
            mock_service.get_attendance_history.return_value = mock_response
            
            # Test the endpoint
            response = client.get("/api/attendance/history")
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["total_count"] == 1
            assert len(data["data"]) == 1
            assert data["data"][0]["runner_name"] == "Test Runner"
    
    def test_get_attendance_history_with_pagination(self, client):
        """Test GET /api/attendance/history endpoint with pagination parameters"""
        with patch('app.routes.registration.get_db') as mock_get_db, \
             patch('app.routes.registration.RegistrationService') as mock_service_class:
            
            # Setup mock service
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            # Mock response data
            mock_response = {
                "success": True,
                "data": [],
                "total_count": 100,
                "page": 2,
                "page_size": 10,
                "total_pages": 10,
                "has_next": True,
                "has_prev": True,
                "message": "Retrieved 0 of 100 attendance records"
            }
            
            mock_service.get_attendance_history.return_value = mock_response
            
            # Test with pagination parameters
            response = client.get("/api/attendance/history?page=2&page_size=10")
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["page"] == 2
            assert data["page_size"] == 10
            assert data["total_pages"] == 10
            assert data["has_next"] is True
            assert data["has_prev"] is True
            
            # Verify service was called with correct parameters
            mock_service.get_attendance_history.assert_called_once_with(None, None, 2, 10)
    
    def test_get_attendance_history_with_date_filters(self, client):
        """Test GET /api/attendance/history endpoint with date filters"""
        with patch('app.routes.registration.get_db') as mock_get_db, \
             patch('app.routes.registration.RegistrationService') as mock_service_class:
            
            # Setup mock service
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            # Mock response data
            mock_response = {
                "success": True,
                "data": [],
                "total_count": 5,
                "page": 1,
                "page_size": 50,
                "total_pages": 1,
                "has_next": False,
                "has_prev": False,
                "message": "Retrieved 0 of 5 attendance records"
            }
            
            mock_service.get_attendance_history.return_value = mock_response
            
            # Test with date filters
            response = client.get("/api/attendance/history?start_date=2024-01-01&end_date=2024-01-31")
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            
            # Verify service was called with correct parameters
            mock_service.get_attendance_history.assert_called_once_with("2024-01-01", "2024-01-31", 1, 50)
    
    def test_export_attendance_data_endpoint(self, client):
        """Test GET /api/attendance/export endpoint"""
        with patch('app.routes.registration.get_db') as mock_get_db, \
             patch('app.routes.registration.RegistrationService') as mock_service_class:
            
            # Setup mock service
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            # Mock CSV content
            csv_content = "Runner Name,Run Date,Registration Time,Session ID,Attendance ID\nTest Runner,2024-01-15,2024-01-15 10:00:00,session_123,1\n"
            filename = "attendance_export_2024-01-15.csv"
            
            mock_service.export_attendance_csv.return_value = csv_content
            mock_service.get_attendance_export_filename.return_value = filename
            
            # Test the endpoint
            response = client.get("/api/attendance/export")
            
            # Assertions
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/csv; charset=utf-8"
            assert "attachment" in response.headers["content-disposition"]
            assert filename in response.headers["content-disposition"]
            assert response.text == csv_content
            
            # Verify service methods were called
            mock_service.export_attendance_csv.assert_called_once_with(None, None)
            mock_service.get_attendance_export_filename.assert_called_once_with(None, None)
    
    def test_export_attendance_data_with_date_filters(self, client):
        """Test GET /api/attendance/export endpoint with date filters"""
        with patch('app.routes.registration.get_db') as mock_get_db, \
             patch('app.routes.registration.RegistrationService') as mock_service_class:
            
            # Setup mock service
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            # Mock CSV content and filename
            csv_content = "Runner Name,Run Date,Registration Time,Session ID,Attendance ID\n"
            filename = "attendance_export_2024-01-01_to_2024-01-31.csv"
            
            mock_service.export_attendance_csv.return_value = csv_content
            mock_service.get_attendance_export_filename.return_value = filename
            
            # Test with date filters
            response = client.get("/api/attendance/export?start_date=2024-01-01&end_date=2024-01-31")
            
            # Assertions
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/csv; charset=utf-8"
            assert filename in response.headers["content-disposition"]
            
            # Verify service methods were called with correct parameters
            mock_service.export_attendance_csv.assert_called_once_with("2024-01-01", "2024-01-31")
            mock_service.get_attendance_export_filename.assert_called_once_with("2024-01-01", "2024-01-31")
    
    def test_attendance_history_error_handling(self, client):
        """Test error handling in attendance history endpoint"""
        with patch('app.routes.registration.get_db') as mock_get_db, \
             patch('app.routes.registration.RegistrationService') as mock_service_class:
            
            # Setup mock service to raise exception
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_attendance_history.side_effect = Exception("Database error")
            
            # Test the endpoint
            response = client.get("/api/attendance/history")
            
            # Assertions
            assert response.status_code == 500
            response_data = response.json()
            # Check if it's in 'detail' or 'message' field depending on error handler format
            error_message = response_data.get("detail") or response_data.get("message", "")
            assert "Failed to retrieve attendance history" in error_message
    
    def test_export_error_handling(self, client):
        """Test error handling in export endpoint"""
        with patch('app.routes.registration.get_db') as mock_get_db, \
             patch('app.routes.registration.RegistrationService') as mock_service_class:
            
            # Setup mock service to raise exception
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.export_attendance_csv.side_effect = Exception("Export error")
            
            # Test the endpoint
            response = client.get("/api/attendance/export")
            
            # Assertions
            assert response.status_code == 500
            response_data = response.json()
            # Check if it's in 'detail' or 'message' field depending on error handler format
            error_message = response_data.get("detail") or response_data.get("message", "")
            assert "Failed to export attendance data" in error_message
    
    def test_pagination_parameter_validation(self, client):
        """Test pagination parameter validation"""
        with patch('app.routes.registration.get_db') as mock_get_db, \
             patch('app.routes.registration.RegistrationService') as mock_service_class:
            
            # Setup mock service
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_response = {
                "success": True,
                "data": [],
                "total_count": 0,
                "page": 1,
                "page_size": 50,
                "total_pages": 0,
                "has_next": False,
                "has_prev": False,
                "message": "Retrieved 0 of 0 attendance records"
            }
            mock_service.get_attendance_history.return_value = mock_response
            
            # Test with invalid page number (should be handled by FastAPI validation)
            response = client.get("/api/attendance/history?page=0")
            assert response.status_code == 422  # Validation error
            
            # Test with invalid page size (should be handled by FastAPI validation)
            response = client.get("/api/attendance/history?page_size=0")
            assert response.status_code == 422  # Validation error
            
            # Test with page size too large (should be handled by FastAPI validation)
            response = client.get("/api/attendance/history?page_size=2000")
            assert response.status_code == 422  # Validation error


if __name__ == "__main__":
    pytest.main([__file__])