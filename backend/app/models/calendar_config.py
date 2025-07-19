"""Calendar configuration model and related schemas."""

from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import Column, Integer, Boolean, DateTime, Date
from pydantic import BaseModel, Field, validator
from app.database.connection import Base


class CalendarConfig(Base):
    """Calendar configuration database model."""
    
    __tablename__ = "calendar_config"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, unique=True, index=True)
    has_run = Column(Boolean, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<CalendarConfig(id={self.id}, date={self.date}, has_run={self.has_run})>"


# Pydantic schemas for API
class CalendarConfigBase(BaseModel):
    """Base calendar config schema."""
    date: date
    has_run: bool
    
    @validator('date')
    def validate_date(cls, v):
        if not isinstance(v, date):
            raise ValueError('Date must be a date object')
        return v


class CalendarConfigCreate(CalendarConfigBase):
    """Schema for creating calendar config."""
    pass


class CalendarConfigUpdate(BaseModel):
    """Schema for updating calendar config."""
    has_run: bool


class CalendarConfigResponse(CalendarConfigBase):
    """Schema for calendar config responses."""
    id: int
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CalendarDay(BaseModel):
    """Schema for calendar day (frontend compatible)."""
    date: str = Field(..., description="ISO date string (YYYY-MM-DD)")
    has_run: bool
    attendance_count: Optional[int] = None
    session_id: Optional[str] = None
    
    @validator('date')
    def validate_date_string(cls, v):
        try:
            # Validate ISO date format
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')


class CalendarMonth(BaseModel):
    """Schema for calendar month."""
    year: int = Field(..., ge=1900, le=3000)
    month: int = Field(..., ge=1, le=12)
    days: List[CalendarDay]


# Validation functions
class CalendarConfigValidator:
    """Calendar configuration validation utilities."""
    
    @staticmethod
    def validate_date(date_obj: date) -> bool:
        """Validate date object."""
        return isinstance(date_obj, date)
    
    @staticmethod
    def validate_date_string(date_string: str) -> bool:
        """Validate date string format."""
        try:
            parsed_date = datetime.strptime(date_string, '%Y-%m-%d').date()
            return date_string == parsed_date.strftime('%Y-%m-%d')
        except ValueError:
            return False
    
    @staticmethod
    def parse_date_string(date_string: str) -> Optional[date]:
        """Parse date string to date object."""
        try:
            return datetime.strptime(date_string, '%Y-%m-%d').date()
        except ValueError:
            return None
    
    @staticmethod
    def format_date_for_database(date_obj: date) -> str:
        """Format date for database storage."""
        return date_obj.strftime('%Y-%m-%d')
    
    @staticmethod
    def format_date_for_frontend(date_obj: date) -> str:
        """Format date for frontend consumption."""
        return date_obj.strftime('%Y-%m-%d')