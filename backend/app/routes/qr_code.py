"""
QR code generation and validation routes
"""
from fastapi import APIRouter, HTTPException, Path, Request
import logging

from ..schemas import QRCodeResponse, QRValidationResponse
from ..services.qr_service import QRCodeService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize QR service
qr_service = QRCodeService()

@router.get("/validate/{token}", response_model=QRValidationResponse)
async def validate_qr_token(
    token: str = Path(..., description="QR code token to validate")
):
    """
    Validate QR code token
    Requirements: 5.3 - Direct users to correct registration form
    Requirements: 5.4 - Invalidate old codes when runs are cancelled/rescheduled
    """
    try:
        logger.info(f"Validating QR token: {token[:10]}...")
        
        # Validate token using QR service
        validation_result = qr_service.validate_token(token)
        
        if validation_result["valid"]:
            return QRValidationResponse(
                success=True,
                valid=True,
                session_id=validation_result["session_id"],
                message="Token validation successful"
            )
        else:
            return QRValidationResponse(
                success=True,
                valid=False,
                session_id=None,
                message=validation_result["error"] or "Token is invalid or expired"
            )
            
    except Exception as e:
        logger.error(f"Error validating QR token: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to validate QR token")

@router.get("/{session_id}", response_model=QRCodeResponse)
async def generate_qr_code(
    request: Request,
    session_id: str = Path(..., description="Unique session ID for the run")
):
    """
    Generate QR code for a specific run session
    Requirements: 5.1 - Automatically generate unique QR code for each session
    Requirements: 5.2 - Show QR code suitable for projection/printing
    """
    try:
        logger.info(f"Generating QR code for session {session_id}")
        
        # Get base URL from request
        base_url = f"{request.url.scheme}://{request.url.netloc}"
        
        # Generate QR code using service
        qr_code_data = qr_service.generate_qr_code(session_id, base_url)
        
        return QRCodeResponse(
            success=True,
            qr_code_data=qr_code_data,
            session_id=session_id,
            message="QR code generated successfully"
        )
        
    except Exception as e:
        logger.error(f"Error generating QR code: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate QR code")