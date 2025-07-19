"""
Unit tests for QR Code Service
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import base64
import io
from PIL import Image

from app.services.qr_service import QRCodeService


class TestQRCodeService:
    """Test cases for QR Code Service"""
    
    @pytest.fixture
    def qr_service(self):
        """Create QR service instance for testing"""
        return QRCodeService(secret_key="test-secret-key")
    
    def test_generate_token_success(self, qr_service):
        """Test successful token generation"""
        session_id = "test-session-123"
        
        token = qr_service.generate_token(session_id)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_generate_token_different_sessions(self, qr_service):
        """Test that different sessions generate different tokens"""
        session_id_1 = "session-1"
        session_id_2 = "session-2"
        
        token_1 = qr_service.generate_token(session_id_1)
        token_2 = qr_service.generate_token(session_id_2)
        
        assert token_1 != token_2
    
    def test_validate_token_success(self, qr_service):
        """Test successful token validation"""
        session_id = "test-session-456"
        
        # Generate token
        token = qr_service.generate_token(session_id)
        
        # Validate token
        result = qr_service.validate_token(token)
        
        assert result["valid"] is True
        assert result["session_id"] == session_id
        assert result["error"] is None
        assert "expires_at" in result
    
    def test_validate_token_invalid_token(self, qr_service):
        """Test validation of invalid token"""
        invalid_token = "invalid.token.here"
        
        result = qr_service.validate_token(invalid_token)
        
        assert result["valid"] is False
        assert result["session_id"] is None
        assert result["error"] is not None
    
    def test_validate_token_empty_token(self, qr_service):
        """Test validation of empty token"""
        result = qr_service.validate_token("")
        
        assert result["valid"] is False
        assert result["session_id"] is None
        assert result["error"] is not None
    
    def test_validate_token_wrong_type(self, qr_service):
        """Test validation of token with wrong type"""
        from jose import jwt
        
        # Create token with wrong type
        payload = {
            "session_id": "test-session",
            "exp": datetime.utcnow() + timedelta(hours=1),
            "type": "wrong_type"
        }
        wrong_token = jwt.encode(payload, qr_service.secret_key, algorithm=qr_service.algorithm)
        
        result = qr_service.validate_token(wrong_token)
        
        assert result["valid"] is False
        assert result["error"] == "Invalid token type"
    
    def test_validate_token_missing_session_id(self, qr_service):
        """Test validation of token without session ID"""
        from jose import jwt
        
        # Create token without session_id
        payload = {
            "exp": datetime.utcnow() + timedelta(hours=1),
            "type": "qr_token"
        }
        token_without_session = jwt.encode(payload, qr_service.secret_key, algorithm=qr_service.algorithm)
        
        result = qr_service.validate_token(token_without_session)
        
        assert result["valid"] is False
        assert result["error"] == "Missing session ID in token"
    
    def test_token_expiration(self, qr_service):
        """Test token expiration functionality"""
        from jose import jwt
        
        session_id = "test-session-expired"
        
        # Create expired token
        expired_payload = {
            "session_id": session_id,
            "exp": datetime.utcnow() - timedelta(hours=1),  # Expired 1 hour ago
            "type": "qr_token"
        }
        expired_token = jwt.encode(expired_payload, qr_service.secret_key, algorithm=qr_service.algorithm)
        
        result = qr_service.validate_token(expired_token)
        
        assert result["valid"] is False
        assert "expired" in result["error"].lower() or "signature" in result["error"].lower()
    
    def test_is_token_expired_valid_token(self, qr_service):
        """Test is_token_expired with valid token"""
        session_id = "test-session"
        token = qr_service.generate_token(session_id)
        
        is_expired = qr_service.is_token_expired(token)
        
        assert is_expired is False
    
    def test_is_token_expired_expired_token(self, qr_service):
        """Test is_token_expired with expired token"""
        from jose import jwt
        
        # Create expired token
        expired_payload = {
            "session_id": "test-session",
            "exp": datetime.utcnow() - timedelta(hours=1),
            "type": "qr_token"
        }
        expired_token = jwt.encode(expired_payload, qr_service.secret_key, algorithm=qr_service.algorithm)
        
        is_expired = qr_service.is_token_expired(expired_token)
        
        assert is_expired is True
    
    def test_is_token_expired_invalid_token(self, qr_service):
        """Test is_token_expired with invalid token"""
        invalid_token = "invalid.token"
        
        is_expired = qr_service.is_token_expired(invalid_token)
        
        assert is_expired is True
    
    @patch('qrcode.QRCode')
    def test_generate_qr_code_success(self, mock_qr_class, qr_service):
        """Test successful QR code generation"""
        # Mock QR code generation
        mock_qr_instance = MagicMock()
        mock_qr_class.return_value = mock_qr_instance
        
        # Mock image creation
        mock_image = MagicMock()
        mock_qr_instance.make_image.return_value = mock_image
        
        # Mock image save to return base64-like data
        def mock_save(buffer, format):
            buffer.write(b"fake_image_data")
        mock_image.save.side_effect = mock_save
        
        session_id = "test-session"
        base_url = "http://localhost:8000"
        
        result = qr_service.generate_qr_code(session_id, base_url)
        
        assert result is not None
        assert isinstance(result, str)
        # Should be base64 encoded
        try:
            base64.b64decode(result)
            base64_valid = True
        except:
            base64_valid = False
        assert base64_valid is True
    
    def test_generate_qr_code_contains_token(self, qr_service):
        """Test that generated QR code contains valid token"""
        session_id = "test-session-qr"
        base_url = "http://localhost:8000"
        
        # We'll test this by checking if the QR service methods are called correctly
        # Since we can't easily decode the actual QR image without complex mocking
        with patch.object(qr_service, 'generate_token') as mock_generate_token:
            mock_generate_token.return_value = "test-token"
            
            with patch('qrcode.QRCode') as mock_qr_class:
                mock_qr_instance = MagicMock()
                mock_qr_class.return_value = mock_qr_instance
                
                mock_image = MagicMock()
                mock_qr_instance.make_image.return_value = mock_image
                
                def mock_save(buffer, format):
                    buffer.write(b"fake_image_data")
                mock_image.save.side_effect = mock_save
                
                qr_service.generate_qr_code(session_id, base_url)
                
                # Verify token was generated for the session
                mock_generate_token.assert_called_once_with(session_id)
                
                # Verify QR code was created with registration URL
                mock_qr_instance.add_data.assert_called_once()
                call_args = mock_qr_instance.add_data.call_args[0][0]
                assert "register?token=test-token" in call_args
                assert base_url in call_args
    
    def test_token_expiration_24_hours(self, qr_service):
        """Test that tokens expire after 24 hours as per requirements"""
        from jose import jwt
        
        session_id = "test-session"
        token = qr_service.generate_token(session_id)
        
        # Decode token to check expiration
        payload = jwt.decode(token, qr_service.secret_key, algorithms=[qr_service.algorithm])
        exp_time = datetime.fromtimestamp(payload["exp"])
        iat_time = datetime.fromtimestamp(payload["iat"])
        
        # Should expire in approximately 24 hours
        time_diff = exp_time - iat_time
        assert abs(time_diff.total_seconds() - (24 * 3600)) < 60  # Within 1 minute tolerance
    
    def test_qr_service_initialization(self):
        """Test QR service initialization with custom parameters"""
        custom_secret = "custom-secret-key"
        service = QRCodeService(secret_key=custom_secret)
        
        assert service.secret_key == custom_secret
        assert service.algorithm == "HS256"
        assert service.token_expire_hours == 24
    
    def test_generate_token_exception_handling(self, qr_service):
        """Test token generation error handling"""
        # Test with invalid session_id type that might cause issues
        with patch('jose.jwt.encode') as mock_encode:
            mock_encode.side_effect = Exception("JWT encoding failed")
            
            with pytest.raises(Exception) as exc_info:
                qr_service.generate_token("test-session")
            
            assert "Failed to generate token" in str(exc_info.value)
    
    def test_generate_qr_code_exception_handling(self, qr_service):
        """Test QR code generation error handling"""
        with patch.object(qr_service, 'generate_token') as mock_generate_token:
            mock_generate_token.side_effect = Exception("Token generation failed")
            
            with pytest.raises(Exception) as exc_info:
                qr_service.generate_qr_code("test-session", "http://localhost:8000")
            
            assert "Failed to generate QR code" in str(exc_info.value)


class TestQRCodeIntegration:
    """Integration tests for QR code functionality"""
    
    @pytest.fixture
    def qr_service(self):
        """Create QR service instance for integration testing"""
        return QRCodeService(secret_key="integration-test-key")
    
    def test_full_qr_workflow(self, qr_service):
        """Test complete QR code generation and validation workflow"""
        session_id = "integration-test-session"
        
        # Step 1: Generate token
        token = qr_service.generate_token(session_id)
        assert token is not None
        
        # Step 2: Validate token
        validation_result = qr_service.validate_token(token)
        assert validation_result["valid"] is True
        assert validation_result["session_id"] == session_id
        
        # Step 3: Check token is not expired
        is_expired = qr_service.is_token_expired(token)
        assert is_expired is False
        
        # Step 4: Generate QR code (mocked image generation)
        with patch('qrcode.QRCode') as mock_qr_class:
            mock_qr_instance = MagicMock()
            mock_qr_class.return_value = mock_qr_instance
            
            mock_image = MagicMock()
            mock_qr_instance.make_image.return_value = mock_image
            
            def mock_save(buffer, format):
                buffer.write(b"integration_test_image")
            mock_image.save.side_effect = mock_save
            
            qr_code_data = qr_service.generate_qr_code(session_id, "http://test.com")
            assert qr_code_data is not None
            assert isinstance(qr_code_data, str)
    
    def test_token_roundtrip_different_services(self):
        """Test token generated by one service can be validated by another"""
        secret_key = "shared-secret-key"
        service1 = QRCodeService(secret_key=secret_key)
        service2 = QRCodeService(secret_key=secret_key)
        
        session_id = "roundtrip-test"
        
        # Generate token with service1
        token = service1.generate_token(session_id)
        
        # Validate token with service2
        result = service2.validate_token(token)
        
        assert result["valid"] is True
        assert result["session_id"] == session_id
    
    def test_token_different_secrets_fail(self):
        """Test that tokens from different secrets cannot be validated"""
        service1 = QRCodeService(secret_key="secret-1")
        service2 = QRCodeService(secret_key="secret-2")
        
        session_id = "security-test"
        
        # Generate token with service1
        token = service1.generate_token(session_id)
        
        # Try to validate with service2 (different secret)
        result = service2.validate_token(token)
        
        assert result["valid"] is False
        assert "signature" in result["error"].lower() or "invalid" in result["error"].lower()