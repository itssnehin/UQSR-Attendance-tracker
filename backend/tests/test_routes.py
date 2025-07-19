"""
Integration tests for API routes
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestCalendarRoutes:
    """Test calendar management routes"""
    
    def test_get_calendar(self):
        """Test calendar retrieval endpoint"""
        response = client.get("/api/calendar/")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
    
    def test_configure_calendar_valid_data(self):
        """Test calendar configuration with valid data"""
        response = client.post("/api/calendar/configure", json={
            "date": "2024-01-15",
            "has_run": True
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "2024-01-15" in data["message"]
    
    def test_configure_calendar_invalid_data(self):
        """Test calendar configuration with invalid data"""
        response = client.post("/api/calendar/configure", json={
            "date": "",  # Empty date should fail validation
            "has_run": True
        })
        assert response.status_code == 422
        data = response.json()
        assert data["error"] is True
    
    def test_get_today_status(self):
        """Test today's run status endpoint"""
        response = client.get("/api/calendar/today")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "has_run_today" in data
        assert "attendance_count" in data
        assert isinstance(data["has_run_today"], bool)
        assert isinstance(data["attendance_count"], int)

class TestRegistrationRoutes:
    """Test registration and attendance routes"""
    
    def test_register_attendance_valid_data(self):
        """Test attendance registration with valid data"""
        response = client.post("/api/register", json={
            "session_id": "test-session-123",
            "runner_name": "John Doe"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["runner_name"] == "John Doe"
        assert data["current_count"] >= 0
    
    def test_register_attendance_invalid_data(self):
        """Test attendance registration with invalid data"""
        response = client.post("/api/register", json={
            "session_id": "",  # Empty session_id should fail
            "runner_name": "John Doe"
        })
        assert response.status_code == 422
        data = response.json()
        assert data["error"] is True
    
    def test_register_attendance_missing_fields(self):
        """Test attendance registration with missing fields"""
        response = client.post("/api/register", json={
            "session_id": "test-session-123"
            # Missing runner_name
        })
        assert response.status_code == 422
        data = response.json()
        assert data["error"] is True
    
    def test_get_today_attendance(self):
        """Test today's attendance count endpoint"""
        response = client.get("/api/attendance/today")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "count" in data
        assert isinstance(data["count"], int)
    
    def test_get_attendance_history(self):
        """Test attendance history endpoint"""
        response = client.get("/api/attendance/history")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "total_count" in data
        assert isinstance(data["data"], list)
        assert isinstance(data["total_count"], int)
    
    def test_get_attendance_history_with_dates(self):
        """Test attendance history with date parameters"""
        response = client.get("/api/attendance/history?start_date=2024-01-01&end_date=2024-01-31")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_export_attendance_data(self):
        """Test attendance data export endpoint"""
        response = client.get("/api/attendance/export")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

class TestQRCodeRoutes:
    """Test QR code generation and validation routes"""
    
    def test_generate_qr_code(self):
        """Test QR code generation endpoint"""
        session_id = "test-session-456"
        response = client.get(f"/api/qr/generate/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["session_id"] == session_id
    
    def test_generate_qr_code_empty_session(self):
        """Test QR code generation with empty session ID"""
        # FastAPI should handle this as a 404 since it's a path parameter
        response = client.get("/api/qr/")
        assert response.status_code == 404
    
    def test_validate_qr_token(self):
        """Test QR token validation endpoint"""
        token = "test-token-789"
        response = client.get(f"/api/qr/validate/{token}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "valid" in data
        assert isinstance(data["valid"], bool)
    
    def test_validate_qr_token_empty(self):
        """Test QR token validation with empty token"""
        # FastAPI should handle this as a 404 since it's a path parameter
        # Note: "/api/qr/validate/" without a token should return 404
        response = client.get("/api/qr/validate")
        assert response.status_code == 404

class TestRequestValidation:
    """Test Pydantic request validation"""
    
    def test_calendar_config_validation(self):
        """Test calendar configuration request validation"""
        # Test with missing required fields
        response = client.post("/api/calendar/configure", json={})
        assert response.status_code == 422
        
        # Test with invalid data types
        response = client.post("/api/calendar/configure", json={
            "date": 123,  # Should be string
            "has_run": "yes"  # Should be boolean
        })
        assert response.status_code == 422
    
    def test_registration_validation(self):
        """Test registration request validation"""
        # Test with string length validation
        response = client.post("/api/register", json={
            "session_id": "",  # Too short
            "runner_name": "A" * 300  # Too long
        })
        assert response.status_code == 422
        
        # Test with correct data
        response = client.post("/api/register", json={
            "session_id": "valid-session",
            "runner_name": "Valid Name"
        })
        assert response.status_code == 200