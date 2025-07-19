"""Run model and related schemas."""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, validator
from app.database.connection import Base


class Run(Base):
    """Run database model."""
    
    __tablename__ = "runs"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, unique=True, index=True)
    session_id = Column(String(255), nullable=False, unique=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship to attendances
    attendances = relationship("Attendance", back_populates="run", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Run(id={self.id}, date={self.date}, session_id={self.session_id})>"


# Pydantic schemas for API
class RunBase(BaseModel):
    """Base run schema."""
    date: datetime
    session_id: str = Field(..., min_length=1, max_length=255)
    is_active: bool = True
    
    @validator('session_id')
    def validate_session_id(cls, v):
        if not v or not v.strip():
            raise ValueError('Session ID cannot be empty')
        if len(v) > 255:
            raise ValueError('Session ID too long')
        return v.strip()
    
    @validator('date')
    def validate_date(cls, v):
        if not isinstance(v, datetime):
            raise ValueError('Date must be a datetime object')
        return v


class RunCreate(RunBase):
    """Schema for creating a run."""
    pass


class RunUpdate(BaseModel):
    """Schema for updating a run."""
    is_active: Optional[bool] = None


class RunResponse(RunBase):
    """Schema for run responses."""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class RunWithAttendanceCount(RunResponse):
    """Schema for run with attendance count."""
    attendance_count: int


# Validation functions
class RunValidator:
    """Run validation utilities."""
    
    @staticmethod
    def validate_session_id(session_id: str) -> bool:
        """Validate session ID format."""
        return (
            isinstance(session_id, str) and
            len(session_id.strip()) > 0 and
            len(session_id) <= 255
        )
    
    @staticmethod
    def validate_date(date: datetime) -> bool:
        """Validate date."""
        return isinstance(date, datetime)
    
    @staticmethod
    def sanitize_session_id(session_id: str) -> str:
        """Sanitize session ID."""
        return session_id.strip() if isinstance(session_id, str) else ""