"""
Unit tests for Registration API endpoints
"""
import pytest
from datetime import datetime, date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.run import Run
from app.models.attendance import Attendance


class TestRegistrationEndpoints:
    """Test cases for registration API endpoints"""
    
    def test_register_attendance_success(self, client: TestClient, test_session: Session):
        """Test successful attendance registration via API"""
        # Create a test run
        test_run = Run(
            date=date.today(),
            session_id="api-test-session-123",
            is_active=True,
            created_at=datetime.utcnow()
        )
        test_session.add(test_run)
        test_session.commit()
        
        # Make registration request
        response = client.post("/api/register", json={
            "session_id": "api-test-session-123",
            "runner_name": "API Test Runner"
        })
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Registration successful" in data["message"]
        assert data["current_count"] == 1
        assert data["runner_name"] == "API Test Runner"
    
    def test_register_attendance_duplicate(self, client: TestClient, test_session: Session):
        """Test duplicate registration prevention via API"""
        # Create a test run
        test_run = Run(
            date=date.today(),
            session_id="api-duplicate-session",
            is_active=True,
            created_at=datetime.utcnow()
        )
        test_session.add(test_run)
        test_session.commit()
        test_session.refresh(test_run)
        
        # Create first attendance
        first_attendance = Attendance(
            run_id=test_run.id,
            runner_name="Duplicate Test Runner",
            registered_at=datetime.utcnow()
        )
        test_session.add(first_attendance)
        test_session.commit()
        
        # Try to register the same runner again
        response = client.post("/api/register", json={
            "session_id": "api-duplicate-session",
            "runner_name": "Duplicate Test Runner"
        })
        
        # Should return 409 Conflict
        assert response.status_code == 409
        data = response.json()
        assert "already registered" in data["message"].lower()
    
    def test_register_attendance_invalid_session(self, client: TestClient, test_session: Session):
        """Test registration with invalid session ID via API"""
        response = client.post("/api/register", json={
            "session_id": "invalid-api-session",
            "runner_name": "Invalid Session Runner"
        })
        
        # Should return 404 Not Found
        assert response.status_code == 404
        # The error message might be in different fields depending on the error handler
        data = response.json()
        # Check if it's in the error field or message field
        error_text = data.get("message", data.get("detail", ""))
        assert "Invalid session ID" in error_text or "Not Found" in error_text
    
    def test_register_attendance_validation_error(self, client: TestClient):
        """Test registration with validation errors"""
        # Test missing session_id
        response = client.post("/api/register", json={
            "runner_name": "Missing Session Runner"
        })
        assert response.status_code == 422
        
        # Test missing runner_name
        response = client.post("/api/register", json={
            "session_id": "test-session"
        })
        assert response.status_code == 422
        
        # Test empty session_id
        response = client.post("/api/register", json={
            "session_id": "",
            "runner_name": "Empty Session Runner"
        })
        assert response.status_code == 422
        
        # Test empty runner_name
        response = client.post("/api/register", json={
            "session_id": "test-session",
            "runner_name": ""
        })
        assert response.status_code == 422
    
    def test_register_attendance_long_names(self, client: TestClient, test_session: Session):
        """Test registration with maximum length names"""
        # Create a test run
        test_run = Run(
            date=date.today(),
            session_id="long-name-session",
            is_active=True,
            created_at=datetime.utcnow()
        )
        test_session.add(test_run)
        test_session.commit()
        
        # Test with 255 character name (should work)
        long_name = "A" * 255
        response = client.post("/api/register", json={
            "session_id": "long-name-session",
            "runner_name": long_name
        })
        assert response.status_code == 200
        
        # Test with 256 character name (should fail validation)
        too_long_name = "B" * 256
        response = client.post("/api/register", json={
            "session_id": "long-name-session",
            "runner_name": too_long_name
        })
        assert response.status_code == 422
    
    def test_get_today_attendance_with_run(self, client: TestClient, test_session: Session):
        """Test getting today's attendance count when run exists"""
        # Create today's run
        today_run = Run(
            date=date.today(),
            session_id="today-api-session",
            is_active=True,
            created_at=datetime.utcnow()
        )
        test_session.add(today_run)
        test_session.commit()
        test_session.refresh(today_run)
        
        # Add some attendances
        attendances = [
            Attendance(run_id=today_run.id, runner_name="API Runner 1", registered_at=datetime.utcnow()),
            Attendance(run_id=today_run.id, runner_name="API Runner 2", registered_at=datetime.utcnow())
        ]
        for attendance in attendances:
            test_session.add(attendance)
        test_session.commit()
        
        # Make API request
        response = client.get("/api/attendance/today")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 2
        assert data["has_run_today"] is True
        assert data["session_id"] == "today-api-session"
    
    def test_get_today_attendance_no_run(self, client: TestClient, test_session: Session):
        """Test getting today's attendance count when no run exists"""
        response = client.get("/api/attendance/today")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 0
        assert data["has_run_today"] is False
        assert "No run scheduled" in data["message"]
    
    def test_get_attendance_history_no_filters(self, client: TestClient, test_session: Session):
        """Test getting attendance history without filters"""
        # Create test runs and attendances
        run1 = Run(
            date=date(2024, 1, 15),
            session_id="history-api-session-1",
            is_active=True,
            created_at=datetime.utcnow()
        )
        run2 = Run(
            date=date(2024, 1, 16),
            session_id="history-api-session-2",
            is_active=True,
            created_at=datetime.utcnow()
        )
        test_session.add_all([run1, run2])
        test_session.commit()
        test_session.refresh(run1)
        test_session.refresh(run2)
        
        # Add attendances
        attendances = [
            Attendance(run_id=run1.id, runner_name="History API Runner 1", registered_at=datetime(2024, 1, 15, 10, 0)),
            Attendance(run_id=run2.id, runner_name="History API Runner 2", registered_at=datetime(2024, 1, 16, 10, 0))
        ]
        for attendance in attendances:
            test_session.add(attendance)
        test_session.commit()
        
        # Make API request
        response = client.get("/api/attendance/history")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_count"] == 2
        assert len(data["data"]) == 2
    
    def test_get_attendance_history_with_filters(self, client: TestClient, test_session: Session):
        """Test getting attendance history with date filters"""
        # Create test runs
        run1 = Run(
            date=date(2024, 1, 10),
            session_id="filter-api-session-1",
            is_active=True,
            created_at=datetime.utcnow()
        )
        run2 = Run(
            date=date(2024, 1, 15),
            session_id="filter-api-session-2",
            is_active=True,
            created_at=datetime.utcnow()
        )
        run3 = Run(
            date=date(2024, 1, 20),
            session_id="filter-api-session-3",
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
            Attendance(run_id=run1.id, runner_name="Filter API Runner 1", registered_at=datetime.utcnow()),
            Attendance(run_id=run2.id, runner_name="Filter API Runner 2", registered_at=datetime.utcnow()),
            Attendance(run_id=run3.id, runner_name="Filter API Runner 3", registered_at=datetime.utcnow())
        ]
        for attendance in attendances:
            test_session.add(attendance)
        test_session.commit()
        
        # Make API request with date filters
        response = client.get("/api/attendance/history?start_date=2024-01-12&end_date=2024-01-18")
        
        # Should only return the middle run (2024-01-15)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_count"] == 1
        assert len(data["data"]) == 1
        assert data["data"][0]["runner_name"] == "Filter API Runner 2"
    
    def test_get_attendance_history_empty_result(self, client: TestClient, test_session: Session):
        """Test getting attendance history with no matching records"""
        response = client.get("/api/attendance/history?start_date=2025-01-01&end_date=2025-01-31")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_count"] == 0
        assert len(data["data"]) == 0
    
    def test_export_attendance_data_placeholder(self, client: TestClient):
        """Test attendance data export endpoint (placeholder implementation)"""
        response = client.get("/api/attendance/export")
        
        # This endpoint is still a placeholder, so just verify it responds
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
    
    def test_registration_performance_simulation(self, client: TestClient, test_session: Session):
        """Test multiple registrations to simulate performance under load"""
        # Create a test run
        test_run = Run(
            date=date.today(),
            session_id="performance-test-session",
            is_active=True,
            created_at=datetime.utcnow()
        )
        test_session.add(test_run)
        test_session.commit()
        
        # Register multiple runners quickly
        successful_registrations = 0
        for i in range(10):
            response = client.post("/api/register", json={
                "session_id": "performance-test-session",
                "runner_name": f"Performance Runner {i}"
            })
            if response.status_code == 200:
                successful_registrations += 1
        
        # All registrations should succeed
        assert successful_registrations == 10
        
        # Verify final count
        response = client.get("/api/attendance/today")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 10
    
    def test_registration_with_special_characters(self, client: TestClient, test_session: Session):
        """Test registration with names containing special characters"""
        # Create a test run
        test_run = Run(
            date=date.today(),
            session_id="special-chars-session",
            is_active=True,
            created_at=datetime.utcnow()
        )
        test_session.add(test_run)
        test_session.commit()
        
        # Test names with valid special characters
        valid_names = [
            "Mary O'Connor",
            "Jean-Pierre Dubois",
            "Dr. Smith",
            "Anna-Maria Rodriguez"
        ]
        
        for name in valid_names:
            response = client.post("/api/register", json={
                "session_id": "special-chars-session",
                "runner_name": name
            })
            assert response.status_code == 200, f"Failed for name: {name}"
    
    def test_registration_case_sensitivity(self, client: TestClient, test_session: Session):
        """Test that registration is case-sensitive for names"""
        # Create a test run
        test_run = Run(
            date=date.today(),
            session_id="case-test-session",
            is_active=True,
            created_at=datetime.utcnow()
        )
        test_session.add(test_run)
        test_session.commit()
        
        # Register with lowercase name
        response1 = client.post("/api/register", json={
            "session_id": "case-test-session",
            "runner_name": "john doe"
        })
        assert response1.status_code == 200
        
        # Register with different case (should be treated as different person)
        response2 = client.post("/api/register", json={
            "session_id": "case-test-session",
            "runner_name": "John Doe"
        })
        assert response2.status_code == 200
        
        # Verify both registrations succeeded
        response = client.get("/api/attendance/today")
        data = response.json()
        assert data["count"] == 2