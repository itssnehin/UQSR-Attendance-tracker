"""
QR Code Service for generating and validating QR codes with JWT tokens
"""
import qrcode
import io
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from PIL import Image
import logging

logger = logging.getLogger(__name__)

class QRCodeService:
    """Service for QR code generation and JWT token validation"""
    
    def __init__(self, secret_key: str = "your-secret-key-change-in-production"):
        """
        Initialize QR Code Service
        
        Args:
            secret_key: Secret key for JWT token signing
        """
        self.secret_key = secret_key
        self.algorithm = "HS256"
        self.token_expire_hours = 24  # 24-hour expiration as per requirements
    
    def generate_token(self, session_id: str) -> str:
        """
        Generate JWT token for QR code with 24-hour expiration
        
        Args:
            session_id: Unique session identifier for the run
            
        Returns:
            JWT token string
            
        Requirements: 5.1, 5.3 - Generate unique codes with secure tokens
        """
        try:
            # Create token payload with expiration
            expire = datetime.utcnow() + timedelta(hours=self.token_expire_hours)
            payload = {
                "session_id": session_id,
                "exp": expire,
                "iat": datetime.utcnow(),
                "type": "qr_token"
            }
            
            # Generate JWT token
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            logger.info(f"Generated token for session {session_id}, expires at {expire}")
            
            return token
            
        except Exception as e:
            logger.error(f"Error generating token for session {session_id}: {str(e)}")
            raise Exception(f"Failed to generate token: {str(e)}")
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate JWT token and extract session information
        
        Args:
            token: JWT token to validate
            
        Returns:
            Dictionary with validation result and session info
            
        Requirements: 5.3, 5.4 - Validate tokens and handle expiration
        """
        try:
            # Decode and validate JWT token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check token type
            if payload.get("type") != "qr_token":
                return {
                    "valid": False,
                    "session_id": None,
                    "error": "Invalid token type"
                }
            
            # Extract session ID
            session_id = payload.get("session_id")
            if not session_id:
                return {
                    "valid": False,
                    "session_id": None,
                    "error": "Missing session ID in token"
                }
            
            logger.info(f"Token validated successfully for session {session_id}")
            
            return {
                "valid": True,
                "session_id": session_id,
                "expires_at": datetime.fromtimestamp(payload.get("exp", 0)),
                "error": None
            }
            
        except JWTError as e:
            logger.warning(f"JWT validation failed: {str(e)}")
            return {
                "valid": False,
                "session_id": None,
                "error": f"Token validation failed: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error validating token: {str(e)}")
            return {
                "valid": False,
                "session_id": None,
                "error": f"Validation error: {str(e)}"
            }
    
    def generate_qr_code(self, session_id: str, base_url: str = "http://localhost:8000") -> str:
        """
        Generate QR code image for a session and return as base64 string
        
        Args:
            session_id: Unique session identifier
            base_url: Base URL for the registration endpoint
            
        Returns:
            Base64 encoded PNG image of QR code
            
        Requirements: 5.1, 5.2 - Generate QR codes suitable for projection/printing
        """
        try:
            # Generate JWT token for the session
            token = self.generate_token(session_id)
            
            # Create registration URL with token
            registration_url = f"{base_url}/register?token={token}"
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,  # Controls size (1 is smallest)
                error_correction=qrcode.constants.ERROR_CORRECT_L,  # Low error correction for faster scanning
                box_size=10,  # Size of each box in pixels
                border=4,  # Border size in boxes
            )
            
            qr.add_data(registration_url)
            qr.make(fit=True)
            
            # Create QR code image
            qr_image = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64 string
            img_buffer = io.BytesIO()
            qr_image.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            # Encode as base64
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
            
            logger.info(f"Generated QR code for session {session_id}")
            
            return img_base64
            
        except Exception as e:
            logger.error(f"Error generating QR code for session {session_id}: {str(e)}")
            raise Exception(f"Failed to generate QR code: {str(e)}")
    
    def is_token_expired(self, token: str) -> bool:
        """
        Check if a token is expired without full validation
        
        Args:
            token: JWT token to check
            
        Returns:
            True if token is expired, False otherwise
            
        Requirements: 5.4 - Handle token expiration
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            exp_timestamp = payload.get("exp", 0)
            return datetime.utcnow().timestamp() > exp_timestamp
        except JWTError:
            return True  # Consider invalid tokens as expired
        except Exception:
            return True  # Consider any error as expired