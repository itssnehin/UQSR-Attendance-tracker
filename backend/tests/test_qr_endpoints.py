"""
Unit tests for QR Code API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import base64

from app.main import app
from app.services.qr_service import QRCodeService


class TestQRCodeEndpoints:
    """Test cases for QR Code API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_qr_service(self):
        """Create mock QR service"""
        return MagicMock(spec=QRCodeService)
    
    def test_generate_qr_code_success(self, client):
        """Test successful QR code generation endpoint"""
        session_id = "test-session-123"
        
        with patch('app.routes.qr_code.qr_service') as mock_service:
            # Mock successful QR code generation
            mock_service.generate_qr_code.return_value = "base64encodedimage"
            
            response = client.get(f"/api/qr/{session_id}")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["qr_code_data"] == "base64encodedimage"
            assert data["session_id"] == session_id
            assert data["message"] == "QR code generated successfully"
            
            # Verify service was called correctly
            mock_service.generate_qr_code.assert_called_once()
            call_args = mock_service.generate_qr_code.call_args
            assert call_args[0][0] == session_id  # session_id argument
            assert "http://testserver" in call_args[0][1]  # base_url argument
    
    def test_generate_qr_code_service_error(self, client):
        """Test QR code generation with service error"""
        session_id = "error-session"
        
        with patch('app.routes.qr_code.qr_service') as mock_service:
            # Mock service error
            mock_service.generate_qr_code.side_effect = Exception("QR generation failed")
            
            response = client.get(f"/api/qr/{session_id}")
            
            assert response.status_code == 500
            data = response.json()
            
            assert data["error"] is True
            assert data["message"] == "Failed to generate QR code"
            assert data["status_code"] == 500
    
    def test_generate_qr_code_empty_session_id(self, client):
        """Test QR code generation with empty session ID"""
        # FastAPI will handle path parameter validation
        response = client.get("/api/qr/")
        
        # Should return 404 since the path doesn't match
        assert response.status_code == 404
    
    def test_validate_qr_token_success(self, client):
        """Test successful QR token validation"""
        token = "valid.jwt.token"
        
        with patch('app.routes.qr_code.qr_service') as mock_service:
            # Mock successful validation
            mock_service.validate_token.return_value = {
                "valid": True,
                "session_id": "test-session-456",
                "error": None
            }
            
            response = client.get(f"/api/qr/validate/{token}")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["valid"] is True
            assert data["session_id"] == "test-session-456"
            assert data["message"] == "Token validation successful"
            
            # Verify service was called correctly
            mock_service.validate_token.assert_called_once_with(token)
    
    def test_validate_qr_token_invalid(self, client):
        """Test QR token validation with invalid token"""
        token = "invalid.jwt.token"
        
        with patch('app.routes.qr_code.qr_service') as mock_service:
            # Mock invalid token
            mock_service.validate_token.return_value = {
                "valid": False,
                "session_id": None,
                "error": "Token is expired"
            }
            
            response = client.get(f"/api/qr/validate/{token}")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["valid"] is False
            assert data["session_id"] is None
            assert "expired" in data["message"].lower()
    
    def test_validate_qr_token_service_error(self, client):
        """Test QR token validation with service error"""
        token = "error.token"
        
        with patch('app.routes.qr_code.qr_service') as mock_service:
            # Mock service error
            mock_service.validate_token.side_effect = Exception("Validation service failed")
            
            response = client.get(f"/api/qr/validate/{token}")
            
            assert response.status_code == 500
            data = response.json()
            
            assert data["error"] is True
            assert data["message"] == "Failed to validate QR token"
            assert data["status_code"] == 500
    
    def test_validate_qr_token_empty_token(self, client):
        """Test QR token validation with empty token"""
        # Test with a space character as token to ensure it goes to validation endpoint
        empty_token = " "
        
        with patch('app.routes.qr_code.qr_service') as mock_service:
            # Mock service to return invalid for empty token
            mock_service.validate_token.return_value = {
                "valid": False,
                "session_id": None,
                "error": "Empty token provided"
            }
            
            response = client.get(f"/api/qr/validate/{empty_token}")
            
            # Should return 200 with validation failure
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["valid"] is False
    
    def test_qr_endpoints_logging(self, client, caplog):
        """Test that QR endpoints log appropriately"""
        import logging
        
        session_id = "logging-test-session"
        
        with patch('app.routes.qr_code.qr_service') as mock_service:
            mock_service.generate_qr_code.return_value = "test-qr-data"
            
            with caplog.at_level(logging.INFO):
                response = client.get(f"/api/qr/{session_id}")
            
            assert response.status_code == 200
            
            # Check that appropriate log messages were created
            log_messages = [record.message for record in caplog.records]
            assert any(f"Generating QR code for session {session_id}" in msg for msg in log_messages)
    
    def test_validate_token_logging(self, client, caplog):
        """Test that token validation logs appropriately"""
        import logging
        
        token = "test.logging.token"
        
        with patch('app.routes.qr_code.qr_service') as mock_service:
            mock_service.validate_token.return_value = {
                "valid": True,
                "session_id": "test-session",
                "error": None
            }
            
            with caplog.at_level(logging.INFO):
                response = client.get(f"/api/qr/validate/{token}")
            
            assert response.status_code == 200
            
            # Check that appropriate log messages were created
            log_messages = [record.message for record in caplog.records]
            assert any("Validating QR token" in msg for msg in log_messages)
    
    def test_generate_qr_code_with_custom_base_url(self, client):
        """Test QR code generation uses correct base URL from request"""
        session_id = "base-url-test"
        
        with patch('app.routes.qr_code.qr_service') as mock_service:
            mock_service.generate_qr_code.return_value = "test-qr-data"
            
            # Make request with custom headers to simulate different host
            headers = {"Host": "custom.example.com"}
            response = client.get(f"/api/qr/{session_id}", headers=headers)
            
            assert response.status_code == 200
            
            # Verify service was called with correct base URL
            mock_service.generate_qr_code.assert_called_once()
            call_args = mock_service.generate_qr_code.call_args
            base_url = call_args[0][1]
            # Custom host header should be used in the base URL
            assert "custom.example.com" in base_url


class TestQRCodeEndpointsIntegration:
    """Integration tests for QR Code endpoints with real service"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_generate_and_validate_qr_workflow(self, client):
        """Test complete workflow of generating QR code and validating token"""
        session_id = "integration-workflow-test"
        
        # Mock only the QR image generation part to avoid PIL dependencies in tests
        with patch('qrcode.QRCode') as mock_qr_class:
            mock_qr_instance = MagicMock()
            mock_qr_class.return_value = mock_qr_instance
            
            mock_image = MagicMock()
            mock_qr_instance.make_image.return_value = mock_image
            
            def mock_save(buffer, format):
                buffer.write(b"test_qr_image_data")
            mock_image.save.side_effect = mock_save
            
            # Step 1: Generate QR code
            response = client.get(f"/api/qr/{session_id}")
            assert response.status_code == 200
            
            qr_data = response.json()
            assert qr_data["success"] is True
            assert qr_data["qr_code_data"] is not None
            
            # Step 2: Extract token from the QR generation process
            # We need to get the token that was generated
            # Since we can't easily extract it from the QR code, we'll generate one directly
            from app.services.qr_service import QRCodeService
            qr_service = QRCodeService()
            token = qr_service.generate_token(session_id)
            
            # Step 3: Validate the token
            response = client.get(f"/api/qr/validate/{token}")
            assert response.status_code == 200
            
            validation_data = response.json()
            assert validation_data["success"] is True
            assert validation_data["valid"] is True
            assert validation_data["session_id"] == session_id
    
    def test_real_token_expiration_validation(self, client):
        """Test token expiration with real JWT tokens"""
        from jose import jwt
        from datetime import datetime, timedelta
        from app.services.qr_service import QRCodeService
        
        qr_service = QRCodeService()
        
        # Create an expired token
        expired_payload = {
            "session_id": "expired-test-session",
            "exp": datetime.utcnow() - timedelta(hours=1),  # Expired 1 hour ago
            "iat": datetime.utcnow() - timedelta(hours=2),
            "type": "qr_token"
        }
        expired_token = jwt.encode(expired_payload, qr_service.secret_key, algorithm=qr_service.algorithm)
        
        # Validate expired token
        response = client.get(f"/api/qr/validate/{expired_token}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["valid"] is False
        assert "expired" in data["message"].lower() or "signature" in data["message"].lower()
    
    def test_qr_code_response_format(self, client):
        """Test that QR code response has correct format"""
        session_id = "format-test-session"
        
        with patch('qrcode.QRCode') as mock_qr_class:
            mock_qr_instance = MagicMock()
            mock_qr_class.return_value = mock_qr_instance
            
            mock_image = MagicMock()
            mock_qr_instance.make_image.return_value = mock_image
            
            def mock_save(buffer, format):
                # Simulate actual image data
                buffer.write(b"fake_png_data_for_testing")
            mock_image.save.side_effect = mock_save
            
            response = client.get(f"/api/qr/{session_id}")
            assert response.status_code == 200
            
            data = response.json()
            
            # Verify response structure matches schema
            assert "success" in data
            assert "qr_code_data" in data
            assert "session_id" in data
            assert "message" in data
            
            # Verify QR code data is base64 encoded
            qr_code_data = data["qr_code_data"]
            assert qr_code_data is not None
            
            # Should be valid base64
            try:
                decoded = base64.b64decode(qr_code_data)
                assert len(decoded) > 0
            except Exception:
                pytest.fail("QR code data is not valid base64")
    
    def test_token_validation_response_format(self, client):
        """Test that token validation response has correct format"""
        from app.services.qr_service import QRCodeService
        
        qr_service = QRCodeService()
        session_id = "format-validation-test"
        token = qr_service.generate_token(session_id)
        
        response = client.get(f"/api/qr/validate/{token}")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify response structure matches schema
        assert "success" in data
        assert "valid" in data
        assert "session_id" in data
        assert "message" in data
        
        # For valid token
        assert data["success"] is True
        assert data["valid"] is True
        assert data["session_id"] == session_id
        assert isinstance(data["message"], str)