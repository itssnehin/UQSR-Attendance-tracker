"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List

# Calendar schemas
class CalendarConfigRequest(BaseModel):
    """Request model for calendar configuration"""
    date: str = Field(..., min_length=1, description="ISO date string (YYYY-MM-DD)")
    has_run: bool = Field(..., description="Whether this date has a scheduled run")

class CalendarDay(BaseModel):
    """Response model for calendar day information"""
    date: str = Field(..., description="ISO date string (YYYY-MM-DD)")
    has_run: bool
    attendance_count: Optional[int] = None
    session_id: Optional[str] = None

class CalendarResponse(BaseModel):
    """Response model for calendar data"""
    success: bool
    data: List[CalendarDay]
    message: Optional[str] = None

class TodayStatusResponse(BaseModel):
    """Response model for today's run status"""
    success: bool
    has_run_today: bool
    session_id: Optional[str] = None
    attendance_count: int = 0
    message: Optional[str] = None

# Registration schemas
class RegistrationRequest(BaseModel):
    """Request model for attendance registration"""
    session_id: str = Field(..., min_length=1, max_length=255, description="Unique session ID for the run")
    runner_name: str = Field(..., min_length=1, max_length=255, description="Name of the runner")

class RegistrationResponse(BaseModel):
    """Response model for registration result"""
    success: bool
    message: str
    current_count: int
    runner_name: Optional[str] = None

class AttendanceHistoryResponse(BaseModel):
    """Response model for attendance history"""
    success: bool
    data: List[dict]
    total_count: int
    message: Optional[str] = None

# QR Code schemas
class QRCodeResponse(BaseModel):
    """Response model for QR code generation"""
    success: bool
    qr_code_data: Optional[str] = None
    session_id: str
    message: Optional[str] = None

class QRValidationResponse(BaseModel):
    """Response model for QR code validation"""
    success: bool
    valid: bool
    session_id: Optional[str] = None
    message: str

# Generic response schemas
class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool = True
    message: str

class ErrorResponse(BaseModel):
    """Generic error response"""
    error: bool = True
    message: str
    status_code: int
    details: Optional[dict] = None