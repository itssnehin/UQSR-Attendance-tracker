"""
Integration tests for QR code generation and validation flow
Tests the complete QR code workflow from generation to validation
"""

import pytest
import qrcode
import io
import base64
from datetime import date, datetime, timedelta
from PIL import Image
from fastapi.testclient import TestClient  # FastAPI TestClient for API testing
from sqlalchemy.orm import Session

from app.main import app
from app.database.connection import get_db
from app.models.database import Run, CalendarConfig
from app.services.qr_service import QRService
from tests.conftest import override_get_db


class TestQRCodeIntegration:
    """Test complete QR code generation and validation workflow"""
    
    @pytest.fixture
    def client(self):
        """Create test client with database override"""
        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app) as client:
            yield client
        app.dependency_overrides.clear()
    
    @pytest.fixture
    def db_session(self):
        """Create test database session"""
        db = next(override_get_db())
        yield db
        db.close()
    
    @pytest.fixture
    def qr_service(self, db_session):
        """Create QR service instance"""
        return QRService(db_session)
    
    @pytest.fixture
    def setup_run_day(self, db_session: Session):
        """Set up a run day for testing"""
        today = date.today()
        
        # Create calendar config
        calendar_config = CalendarConfig(date=today, has_run=True)
        db_session.add(calendar_config)
        
        # Create run
        run = Run(
            date=today,
            session_id=f"test-session-{today.isoformat()}",
            is_active=True
        )
        db_session.add(run)
        db_session.commit()
        
        return run
    
    def test_qr_code_generation_endpoint(self, client, setup_run_day):
        """Test QR code generation via API endpoint"""
        run = setup_run_day
        
        # Generate QR code
        response = client.get(f"/api/qr/{run.session_id}")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        
        # Verify it's a valid PNG image
        image_data = response.content
        image = Image.open(io.BytesIO(image_data))
        assert image.format == "PNG"
        assert image.size[0] > 0 and image.size[1] > 0
    
    def test_qr_code_contains_valid_url(self, client, setup_run_day):
        """Test that generated QR code contains valid registration URL"""
        run = setup_run_day
        
        # Generate QR code
        response = client.get(f"/api/qr/{run.session_id}")
        assert response.status_code == 200
        
        # Decode QR code to verify content
        image = Image.open(io.BytesIO(response.content))
        
        # Use pyzbar to decode QR code (would need to install pyzbar)
        # For now, we'll test the service directly
        qr_service = QRService(next(override_get_db()))
        qr_data = qr_service.generate_qr_data(run.session_id)
        
        # Verify QR data contains registration URL
        expected_url = f"http://localhost:3000/register/{run.session_id}"
        assert qr_data == expected_url
    
    def test_qr_code_validation_endpoint(self, client, setup_run_day):
        """Test QR code token validation endpoint"""
        run = setup_run_day
        
        # Test valid session ID
        response = client.get(f"/api/qr/validate/{run.session_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["valid"] is True
        assert data["session_id"] == run.session_id
        assert data["date"] == run.date.isoformat()
    
    def test_qr_code_validation_invalid_token(self, client):
        """Test QR code validation with invalid token"""
        # Test with non-existent session ID
        response = client.get("/api/qr/validate/invalid-session-id")
        assert response.status_code == 404
        
        data = response.json()
        assert data["detail"] == "Invalid or expired QR code"
    
    def test_qr_code_validation_expired_session(self, client, db_session):
        """Test QR code validation with expired session"""
        # Create an old run (yesterday)
        yesterday = date.today() - timedelta(days=1)
        
        old_run = Run(
            date=yesterday,
            session_id=f"old-session-{yesterday.isoformat()}",
            is_active=False
        )
        db_session.add(old_run)
        db_session.commit()
        
        # Test validation of old session
        response = client.get(f"/api/qr/validate/{old_run.session_id}")
        assert response.status_code == 404
        
        data = response.json()
        assert data["detail"] == "Invalid or expired QR code"
    
    def test_qr_code_generation_for_invalid_session(self, client):
        """Test QR code generation for invalid session ID"""
        response = client.get("/api/qr/invalid-session-id")
        assert response.status_code == 404
        
        data = response.json()
        assert data["detail"] == "Session not found"
    
    def test_qr_code_service_generate_data(self, qr_service, setup_run_day):
        """Test QR service data generation"""
        run = setup_run_day
        
        qr_data = qr_service.generate_qr_data(run.session_id)
        
        # Verify URL format
        expected_url = f"http://localhost:3000/register/{run.session_id}"
        assert qr_data == expected_url
    
    def test_qr_code_service_generate_image(self, qr_service, setup_run_day):
        """Test QR service image generation"""
        run = setup_run_day
        
        qr_image = qr_service.generate_qr_image(run.session_id)
        
        # Verify it's a PIL Image
        assert isinstance(qr_image, Image.Image)
        assert qr_image.format == "PNG"
        assert qr_image.size == (300, 300)  # Default size
    
    def test_qr_code_service_validate_token(self, qr_service, setup_run_day):
        """Test QR service token validation"""
        run = setup_run_day
        
        # Test valid token
        validation_result = qr_service.validate_qr_token(run.session_id)
        
        assert validation_result["valid"] is True
        assert validation_result["session_id"] == run.session_id
        assert validation_result["date"] == run.date.isoformat()
        assert validation_result["is_active"] is True
    
    def test_qr_code_service_validate_invalid_token(self, qr_service):
        """Test QR service validation with invalid token"""
        validation_result = qr_service.validate_qr_token("invalid-token")
        
        assert validation_result["valid"] is False
        assert "error" in validation_result
    
    def test_qr_code_different_sizes(self, client, setup_run_day):
        """Test QR code generation with different sizes"""
        run = setup_run_day
        
        # Test different sizes
        sizes = [200, 300, 400, 500]
        
        for size in sizes:
            response = client.get(f"/api/qr/{run.session_id}?size={size}")
            assert response.status_code == 200
            
            # Verify image size
            image = Image.open(io.BytesIO(response.content))
            assert image.size == (size, size)
    
    def test_qr_code_error_correction_levels(self, qr_service, setup_run_day):
        """Test QR code generation with different error correction levels"""
        run = setup_run_day
        
        # Test different error correction levels
        error_corrections = [
            qrcode.constants.ERROR_CORRECT_L,
            qrcode.constants.ERROR_CORRECT_M,
            qrcode.constants.ERROR_CORRECT_Q,
            qrcode.constants.ERROR_CORRECT_H
        ]
        
        for error_correct in error_corrections:
            qr_image = qr_service.generate_qr_image(
                run.session_id, 
                size=300, 
                error_correction=error_correct
            )
            
            assert isinstance(qr_image, Image.Image)
            assert qr_image.size == (300, 300)
    
    def test_qr_code_concurrent_generation(self, client, setup_run_day):
        """Test concurrent QR code generation requests"""
        run = setup_run_day
        
        import concurrent.futures
        import threading
        
        def generate_qr():
            response = client.get(f"/api/qr/{run.session_id}")
            return response.status_code == 200
        
        # Generate QR codes concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(generate_qr) for _ in range(20)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed
        assert all(results)
    
    def test_qr_code_caching_behavior(self, client, setup_run_day):
        """Test QR code caching behavior"""
        run = setup_run_day
        
        # First request
        response1 = client.get(f"/api/qr/{run.session_id}")
        assert response1.status_code == 200
        
        # Second request (should be cached)
        response2 = client.get(f"/api/qr/{run.session_id}")
        assert response2.status_code == 200
        
        # Images should be identical
        assert response1.content == response2.content
    
    def test_qr_code_registration_flow_integration(self, client, setup_run_day):
        """Test complete flow from QR generation to registration"""
        run = setup_run_day
        
        # Step 1: Generate QR code
        qr_response = client.get(f"/api/qr/{run.session_id}")
        assert qr_response.status_code == 200
        
        # Step 2: Validate QR token
        validate_response = client.get(f"/api/qr/validate/{run.session_id}")
        assert validate_response.status_code == 200
        
        validation_data = validate_response.json()
        assert validation_data["valid"] is True
        
        # Step 3: Use session ID for registration
        register_response = client.post("/api/register", json={
            "session_id": run.session_id,
            "runner_name": "QR Flow Test Runner"
        })
        assert register_response.status_code == 200
        
        # Step 4: Verify registration was successful
        attendance_response = client.get("/api/attendance/today")
        assert attendance_response.status_code == 200
        
        attendance_data = attendance_response.json()
        assert attendance_data["count"] >= 1
        assert any(a["runner_name"] == "QR Flow Test Runner" for a in attendance_data["attendances"])
    
    def test_qr_code_security_validation(self, client, setup_run_day):
        """Test QR code security measures"""
        run = setup_run_day
        
        # Test that session IDs are not predictable
        session_id = run.session_id
        assert len(session_id) >= 20  # Minimum length for security
        assert session_id != f"session-{run.date.isoformat()}"  # Not predictable
        
        # Test that old sessions are properly invalidated
        # (This would be tested in the expired session test above)
        
        # Test that malformed session IDs are rejected
        malformed_ids = [
            "../../../etc/passwd",
            "<script>alert('xss')</script>",
            "'; DROP TABLE runs; --",
            "session-id-with-sql-injection'; DELETE FROM runs; --"
        ]
        
        for malformed_id in malformed_ids:
            response = client.get(f"/api/qr/validate/{malformed_id}")
            assert response.status_code == 404
    
    def test_qr_code_performance_metrics(self, client, setup_run_day):
        """Test QR code generation performance"""
        run = setup_run_day
        
        import time
        
        # Measure QR generation time
        start_time = time.time()
        response = client.get(f"/api/qr/{run.session_id}")
        end_time = time.time()
        
        assert response.status_code == 200
        
        # QR generation should be fast (< 1 second)
        generation_time = end_time - start_time
        assert generation_time < 1.0, f"QR generation too slow: {generation_time:.2f}s"
        
        # Measure validation time
        start_time = time.time()
        response = client.get(f"/api/qr/validate/{run.session_id}")
        end_time = time.time()
        
        assert response.status_code == 200
        
        # Validation should be very fast (< 0.5 seconds)
        validation_time = end_time - start_time
        assert validation_time < 0.5, f"QR validation too slow: {validation_time:.2f}s"
    
    def test_qr_code_image_quality(self, client, setup_run_day):
        """Test QR code image quality and readability"""
        run = setup_run_day
        
        # Generate QR code
        response = client.get(f"/api/qr/{run.session_id}")
        assert response.status_code == 200
        
        # Load image and verify properties
        image = Image.open(io.BytesIO(response.content))
        
        # Check image properties for readability
        assert image.mode in ["RGB", "RGBA", "L"]  # Valid color modes
        assert image.size[0] >= 200  # Minimum size for scanning
        assert image.size[1] >= 200
        
        # Check that image has good contrast (basic check)
        # Convert to grayscale for analysis
        if image.mode != "L":
            gray_image = image.convert("L")
        else:
            gray_image = image
        
        # Get pixel values
        pixels = list(gray_image.getdata())
        
        # Should have both dark and light pixels (good contrast)
        min_pixel = min(pixels)
        max_pixel = max(pixels)
        contrast = max_pixel - min_pixel
        
        assert contrast > 100, f"Poor contrast: {contrast}"  # Good contrast for scanning