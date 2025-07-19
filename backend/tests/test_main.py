"""
Integration tests for main FastAPI application
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestMainApplication:
    """Test main application setup and middleware"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Runner Attendance Tracker API"
        assert data["version"] == "1.0.0"
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Runner Attendance Tracker API"
    
    def test_cors_headers(self):
        """Test CORS middleware configuration"""
        # Test CORS headers with a GET request that should include CORS headers
        response = client.get("/health", headers={"Origin": "http://localhost:3000"})
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers
    
    def test_404_error_handling(self):
        """Test 404 error handling"""
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404
        data = response.json()
        assert data["error"] is True
        assert data["status_code"] == 404
    
    def test_validation_error_handling(self):
        """Test Pydantic validation error handling"""
        # Send invalid data to calendar configure endpoint
        response = client.post("/api/calendar/configure", json={
            "invalid_field": "invalid_value"
        })
        assert response.status_code == 422
        data = response.json()
        assert data["error"] is True
        assert data["message"] == "Validation error"
        assert "details" in data
        assert data["status_code"] == 422

class TestAPIRouting:
    """Test API routing structure"""
    
    def test_calendar_routes_accessible(self):
        """Test calendar routes are properly mounted"""
        # Test calendar root
        response = client.get("/api/calendar/")
        assert response.status_code == 200
        
        # Test today status
        response = client.get("/api/calendar/today")
        assert response.status_code == 200
    
    def test_registration_routes_accessible(self):
        """Test registration routes are properly mounted"""
        # Test today attendance
        response = client.get("/api/attendance/today")
        assert response.status_code == 200
        
        # Test attendance history
        response = client.get("/api/attendance/history")
        assert response.status_code == 200
    
    def test_qr_code_routes_accessible(self):
        """Test QR code routes are properly mounted"""
        # Test QR code generation
        response = client.get("/api/qr/generate/test-session-id")
        assert response.status_code == 200
        
        # Test QR code validation
        response = client.get("/api/qr/validate/test-token")
        assert response.status_code == 200

class TestMiddleware:
    """Test middleware functionality"""
    
    def test_json_parsing_middleware(self):
        """Test JSON parsing works correctly"""
        response = client.post("/api/calendar/configure", json={
            "date": "2024-01-01",
            "has_run": True
        })
        assert response.status_code == 200
        # Should parse JSON successfully
    
    def test_error_response_format(self):
        """Test consistent error response format"""
        response = client.get("/nonexistent")
        assert response.status_code == 404
        data = response.json()
        
        # Check error response structure
        assert "error" in data
        assert "message" in data
        assert "status_code" in data
        assert data["error"] is True
        assert isinstance(data["message"], str)
        assert isinstance(data["status_code"], int)