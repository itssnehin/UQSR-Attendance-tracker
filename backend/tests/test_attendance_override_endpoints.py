"""
Unit tests for Attendance Override API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime, date

from app.main import app
from app.services.attendance_override_service import AttendanceOverrideService


class TestAttendanceOverrideEndpoints:
    """Test cases for Attendance Override API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_override_service(self):
        """Create mock override service"""
        return MagicMock(spec=AttendanceOverrideService)
    
    def test_add_attendance_record_success(self, client):
        """Test successful attendance record addition"""
        request_data = {
            "runner_name": "Test Runner",
            "run_date": "2024-01-15",
            "session_id": "test-session"
        }
        
        with patch('app.routes.attendance_override.override_service') as mock_service:
            mock_service.add_attendance_record.return_value = {
                "success": True,
                "message": "Successfully added attendance record",
                "attendance_id": 1,
                "run_id": 1,
                "session_id": "test-session"
            }
            
            response = client.post("/api/attendance/override/add", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["attendance_id"] == 1
            assert data["run_id"] == 1
            assert data["session_id"] == "test-session"
            
            # Verify service was called correctly
            mock_service.add_attendance_record.assert_called_once()
            call_args = mock_service.add_attendance_record.call_args
            assert call_args[1]["runner_name"] == "Test Runner"
            assert call_args[1]["run_date"] == date(2024, 1, 15)
    
    def test_add_attendance_record_invalid_date(self, client):
        """Test adding attendance record with invalid date"""
        request_data = {
            "runner_name": "Test Runner",
            "run_date": "invalid-date"
        }
        
        response = client.post("/api/attendance/override/add", json=request_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid date format" in data["detail"]
    
    def test_add_attendance_record_service_error(self, client):
        """Test adding attendance record with service error"""
        request_data = {
            "runner_name": "Test Runner",
            "run_date": "2024-01-15"
        }
        
        with patch('app.routes.attendance_override.override_service') as mock_service:
            mock_service.add_attendance_record.return_value = {
                "success": False,
                "message": "Duplicate attendance record"
            }
            
            response = client.post("/api/attendance/override/add", json=request_data)
            
            assert response.status_code == 400
            data = response.json()
            assert data["detail"] == "Duplicate attendance record"
    
    def test_edit_attendance_record_success(self, client):
        """Test successful attendance record editing"""
        attendance_id = 1
        request_data = {
            "runner_name": "Updated Runner",
            "run_date": "2024-01-16"
        }
        
        with patch('app.routes.attendance_override.override_service') as mock_service:
            mock_service.edit_attendance_record.return_value = {
                "success": True,
                "message": "Successfully updated attendance record",
                "changes": {
                    "runner_name": "Updated Runner",
                    "run_date": "2024-01-16"
                }
            }
            
            response = client.put(f"/api/attendance/override/{attendance_id}", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["attendance_id"] == attendance_id
            assert data["data"]["runner_name"] == "Updated Runner"
    
    def test_edit_attendance_record_not_found(self, client):
        """Test editing non-existent attendance record"""
        attendance_id = 999
        request_data = {
            "runner_name": "Updated Runner"
        }
        
        with patch('app.routes.attendance_override.override_service') as mock_service:
            mock_service.edit_attendance_record.return_value = {
                "success": False,
                "message": "Attendance record with ID 999 not found"
            }
            
            response = client.put(f"/api/attendance/override/{attendance_id}", json=request_data)
            
            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"]
    
    def test_edit_attendance_record_invalid_date(self, client):
        """Test editing attendance record with invalid date"""
        attendance_id = 1
        request_data = {
            "run_date": "invalid-date"
        }
        
        response = client.put(f"/api/attendance/override/{attendance_id}", json=request_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid date format" in data["detail"]
    
    def test_remove_attendance_record_success(self, client):
        """Test successful attendance record removal"""
        attendance_id = 1
        
        with patch('app.routes.attendance_override.override_service') as mock_service:
            mock_service.remove_attendance_record.return_value = {
                "success": True,
                "message": "Successfully removed attendance record",
                "removed_record": {
                    "attendance_id": 1,
                    "runner_name": "Test Runner",
                    "run_date": "2024-01-15"
                }
            }
            
            response = client.delete(f"/api/attendance/override/{attendance_id}")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["data"]["attendance_id"] == 1
            assert data["data"]["runner_name"] == "Test Runner"
    
    def test_remove_attendance_record_not_found(self, client):
        """Test removing non-existent attendance record"""
        attendance_id = 999
        
        with patch('app.routes.attendance_override.override_service') as mock_service:
            mock_service.remove_attendance_record.return_value = {
                "success": False,
                "message": "Attendance record with ID 999 not found"
            }
            
            response = client.delete(f"/api/attendance/override/{attendance_id}")
            
            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"]
    
    def test_bulk_operations_success(self, client):
        """Test successful bulk operations"""
        request_data = {
            "operations": [
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
                }
            ]
        }
        
        with patch('app.routes.attendance_override.override_service') as mock_service:
            mock_service.bulk_operations.return_value = {
                "success": True,
                "message": "Processed 3 operations: 3 successful, 0 failed",
                "summary": {
                    "total_operations": 3,
                    "successful": 3,
                    "failed": 0
                },
                "results": [
                    {"success": True, "message": "Added", "operation_index": 0},
                    {"success": True, "message": "Updated", "operation_index": 1},
                    {"success": True, "message": "Removed", "operation_index": 2}
                ]
            }
            
            response = client.post("/api/attendance/override/bulk", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["summary"]["total_operations"] == 3
            assert data["summary"]["successful"] == 3
            assert len(data["results"]) == 3
    
    def test_bulk_operations_mixed_results(self, client):
        """Test bulk operations with mixed success/failure"""
        request_data = {
            "operations": [
                {
                    "action": "add",
                    "runner_name": "Runner 1",
                    "run_date": "2024-01-15"
                },
                {
                    "action": "remove",
                    "attendance_id": 999
                }
            ]
        }
        
        with patch('app.routes.attendance_override.override_service') as mock_service:
            mock_service.bulk_operations.return_value = {
                "success": False,
                "message": "Processed 2 operations: 1 successful, 1 failed",
                "summary": {
                    "total_operations": 2,
                    "successful": 1,
                    "failed": 1
                },
                "results": [
                    {"success": True, "message": "Added", "operation_index": 0},
                    {"success": False, "message": "Not found", "operation_index": 1}
                ]
            }
            
            response = client.post("/api/attendance/override/bulk", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is False
            assert data["summary"]["failed"] == 1
    
    def test_get_attendance_record_success(self, client):
        """Test successful attendance record retrieval"""
        attendance_id = 1
        
        with patch('app.routes.attendance_override.override_service') as mock_service:
            mock_service.get_attendance_record.return_value = {
                "success": True,
                "data": {
                    "attendance_id": 1,
                    "runner_name": "Test Runner",
                    "registered_at": "2024-01-15T10:30:00",
                    "run": {
                        "run_id": 1,
                        "date": "2024-01-15",
                        "session_id": "test-session",
                        "is_active": True
                    }
                }
            }
            
            response = client.get(f"/api/attendance/override/{attendance_id}")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["data"]["attendance_id"] == 1
            assert data["data"]["runner_name"] == "Test Runner"
            assert data["data"]["run"]["run_id"] == 1
    
    def test_get_attendance_record_not_found(self, client):
        """Test getting non-existent attendance record"""
        attendance_id = 999
        
        with patch('app.routes.attendance_override.override_service') as mock_service:
            mock_service.get_attendance_record.return_value = {
                "success": False,
                "message": "Attendance record with ID 999 not found"
            }
            
            response = client.get(f"/api/attendance/override/{attendance_id}")
            
            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"]
    
    def test_search_attendance_records_success(self, client):
        """Test successful attendance records search"""
        with patch('app.routes.attendance_override.override_service') as mock_service:
            mock_service.search_attendance_records.return_value = {
                "success": True,
                "data": [
                    {
                        "attendance_id": 1,
                        "runner_name": "Test Runner",
                        "registered_at": "2024-01-15T10:30:00",
                        "run_date": "2024-01-15",
                        "session_id": "test-session"
                    }
                ],
                "count": 1,
                "filters": {
                    "runner_name": "Test",
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31",
                    "limit": 100
                }
            }
            
            response = client.get(
                "/api/attendance/override/search/records",
                params={
                    "runner_name": "Test",
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31",
                    "limit": 100
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["count"] == 1
            assert len(data["data"]) == 1
            assert data["data"][0]["runner_name"] == "Test Runner"
    
    def test_search_attendance_records_invalid_date(self, client):
        """Test searching with invalid date format"""
        response = client.get(
            "/api/attendance/override/search/records",
            params={"start_date": "invalid-date"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid start_date format" in data["detail"]
    
    def test_search_attendance_records_no_filters(self, client):
        """Test searching without filters"""
        with patch('app.routes.attendance_override.override_service') as mock_service:
            mock_service.search_attendance_records.return_value = {
                "success": True,
                "data": [],
                "count": 0,
                "filters": {
                    "runner_name": None,
                    "start_date": None,
                    "end_date": None,
                    "limit": 100
                }
            }
            
            response = client.get("/api/attendance/override/search/records")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["count"] == 0
    
    def test_endpoint_logging(self, client, caplog):
        """Test that endpoints log appropriately"""
        import logging
        
        request_data = {
            "runner_name": "Test Runner",
            "run_date": "2024-01-15"
        }
        
        with patch('app.routes.attendance_override.override_service') as mock_service:
            mock_service.add_attendance_record.return_value = {
                "success": True,
                "message": "Added",
                "attendance_id": 1
            }
            
            with caplog.at_level(logging.INFO):
                response = client.post("/api/attendance/override/add", json=request_data)
            
            assert response.status_code == 200
            
            # Check that appropriate log messages were created
            log_messages = [record.message for record in caplog.records]
            assert any("Adding manual attendance record" in msg for msg in log_messages)
    
    def test_request_validation(self, client):
        """Test request validation"""
        # Test missing required fields
        response = client.post("/api/attendance/override/add", json={})
        assert response.status_code == 422
        
        # Test invalid field types
        response = client.post("/api/attendance/override/add", json={
            "runner_name": 123,  # Should be string
            "run_date": "2024-01-15"
        })
        assert response.status_code == 422
        
        # Test field length validation
        response = client.post("/api/attendance/override/add", json={
            "runner_name": "",  # Too short
            "run_date": "2024-01-15"
        })
        assert response.status_code == 422


class TestAttendanceOverrideEndpointsIntegration:
    """Integration tests for Attendance Override endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_add_edit_remove_workflow(self, client):
        """Test complete workflow of add, edit, and remove"""
        # This would require actual database setup for full integration testing
        # For now, we'll test the endpoint structure and validation
        
        # Test add endpoint structure
        add_data = {
            "runner_name": "Integration Test Runner",
            "run_date": "2024-01-15",
            "registered_at": "2024-01-15T10:30:00"
        }
        
        with patch('app.routes.attendance_override.override_service') as mock_service:
            mock_service.add_attendance_record.return_value = {
                "success": True,
                "message": "Added",
                "attendance_id": 1
            }
            
            add_response = client.post("/api/attendance/override/add", json=add_data)
            assert add_response.status_code == 200
            
            # Test edit endpoint structure
            edit_data = {
                "runner_name": "Updated Integration Runner"
            }
            
            mock_service.edit_attendance_record.return_value = {
                "success": True,
                "message": "Updated"
            }
            
            edit_response = client.put("/api/attendance/override/1", json=edit_data)
            assert edit_response.status_code == 200
            
            # Test remove endpoint structure
            mock_service.remove_attendance_record.return_value = {
                "success": True,
                "message": "Removed"
            }
            
            remove_response = client.delete("/api/attendance/override/1")
            assert remove_response.status_code == 200
    
    def test_error_handling_consistency(self, client):
        """Test that error handling is consistent across endpoints"""
        with patch('app.routes.attendance_override.override_service') as mock_service:
            # Test 404 errors
            mock_service.get_attendance_record.return_value = {
                "success": False,
                "message": "Record not found"
            }
            
            response = client.get("/api/attendance/override/999")
            assert response.status_code == 404
            
            # Test 400 errors
            mock_service.add_attendance_record.return_value = {
                "success": False,
                "message": "Duplicate record"
            }
            
            response = client.post("/api/attendance/override/add", json={
                "runner_name": "Test",
                "run_date": "2024-01-15"
            })
            assert response.status_code == 400
    
    def test_response_format_consistency(self, client):
        """Test that response formats are consistent"""
        with patch('app.routes.attendance_override.override_service') as mock_service:
            mock_service.add_attendance_record.return_value = {
                "success": True,
                "message": "Added successfully",
                "attendance_id": 1,
                "run_id": 1,
                "session_id": "test"
            }
            
            response = client.post("/api/attendance/override/add", json={
                "runner_name": "Test Runner",
                "run_date": "2024-01-15"
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Check required fields in response
            assert "success" in data
            assert "message" in data
            assert isinstance(data["success"], bool)
            assert isinstance(data["message"], str)