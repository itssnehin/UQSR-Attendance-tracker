"""Attendance model and related schemas."""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, validator
from app.database.connection import Base
import re


class Attendance(Base):
    """Attendance database model."""
    
    __tablename__ = "attendances"
    
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("runs.id", ondelete="CASCADE"), nullable=False, index=True)
    runner_name = Column(String(255), nullable=False, index=True)
    registered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship to run
    run = relationship("Run", back_populates="attendances")
    
    # Unique constraint on run_id and runner_name
    __table_args__ = (
        {"sqlite_autoincrement": True}
    )
    
    def __repr__(self):
        return f"<Attendance(id={self.id}, run_id={self.run_id}, runner_name={self.runner_name})>"


# Pydantic schemas for API
class AttendanceBase(BaseModel):
    """Base attendance schema."""
    run_id: int = Field(..., gt=0)
    runner_name: str = Field(..., min_length=1, max_length=255)
    
    @validator('runner_name')
    def validate_runner_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Runner name cannot be empty')
        
        # Sanitize the name
        sanitized = v.strip()
        
        # Check length
        if len(sanitized) > 255:
            raise ValueError('Runner name too long')
        
        # Check for valid characters (letters, spaces, hyphens, apostrophes, periods)
        if not re.match(r"^[a-zA-Z\s\-'\.]+$", sanitized):
            raise ValueError('Runner name contains invalid characters')
        
        return sanitized
    
    @validator('run_id')
    def validate_run_id(cls, v):
        if not isinstance(v, int) or v <= 0:
            raise ValueError('Run ID must be a positive integer')
        return v


class AttendanceCreate(AttendanceBase):
    """Schema for creating attendance."""
    pass


class AttendanceResponse(AttendanceBase):
    """Schema for attendance responses."""
    id: int
    registered_at: datetime
    
    class Config:
        from_attributes = True


class AttendanceWithRunInfo(AttendanceResponse):
    """Schema for attendance with run information."""
    run_date: datetime
    session_id: str


class AttendanceSummary(BaseModel):
    """Schema for attendance summary."""
    date: datetime
    total_attendees: int
    attendees: List[str]


# Validation functions
class AttendanceValidator:
    """Attendance validation utilities."""
    
    @staticmethod
    def validate_runner_name(name: str) -> bool:
        """Validate runner name format."""
        if not isinstance(name, str):
            return False
        
        trimmed_name = name.strip()
        return (
            len(trimmed_name) > 0 and
            len(trimmed_name) <= 255 and
            re.match(r"^[a-zA-Z\s\-'\.]+$", trimmed_name) is not None
        )
    
    @staticmethod
    def sanitize_runner_name(name: str) -> str:
        """Sanitize runner name."""
        if not isinstance(name, str):
            return ""
        
        # Remove extra whitespace
        return re.sub(r'\s+', ' ', name.strip())
    
    @staticmethod
    def validate_run_id(run_id: int) -> bool:
        """Validate run ID."""
        return isinstance(run_id, int) and run_id > 0