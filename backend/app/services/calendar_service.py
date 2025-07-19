"""
Calendar Service for managing run day configuration and calendar operations.
"""
import uuid
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging

from ..models.calendar_config import CalendarConfig
from ..models.run import Run
from ..models.attendance import Attendance

logger = logging.getLogger(__name__)


class CalendarService:
    """Service class for calendar management operations."""
    
    def __init__(self, db: Session):
        """Initialize calendar service with database session."""
        self.db = db
    
    def configure_run_day(self, target_date: date, has_run: bool) -> Dict[str, Any]:
        """
        Configure whether a specific date has a scheduled run.
        
        Args:
            target_date: The date to configure
            has_run: Whether this date should have a run
            
        Returns:
            Dict with success status and message
            
        Requirements: 1.2, 1.3 - Allow marking run days and persist configuration
        """
        try:
            # Check if configuration already exists for this date
            existing_config = self.db.query(CalendarConfig).filter(
                CalendarConfig.date == target_date
            ).first()
            
            if existing_config:
                # Update existing configuration
                existing_config.has_run = has_run
                existing_config.updated_at = datetime.utcnow()
                logger.info(f"Updated calendar config for {target_date}: has_run={has_run}")
            else:
                # Create new configuration
                new_config = CalendarConfig(
                    date=target_date,
                    has_run=has_run
                )
                self.db.add(new_config)
                logger.info(f"Created calendar config for {target_date}: has_run={has_run}")
            
            # If marking as run day, ensure a Run record exists
            if has_run:
                self._ensure_run_exists(target_date)
            else:
                # If marking as no-run day, deactivate any existing run
                self._deactivate_run(target_date)
            
            self.db.commit()
            
            return {
                "success": True,
                "message": f"Calendar configuration updated for {target_date}",
                "date": target_date.strftime('%Y-%m-%d'),
                "has_run": has_run
            }
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Database integrity error configuring calendar: {e}")
            return {
                "success": False,
                "message": "Database error occurred while updating calendar"
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error configuring calendar for {target_date}: {e}")
            return {
                "success": False,
                "message": f"Failed to configure calendar: {str(e)}"
            }
    
    def get_calendar_configuration(self, start_date: Optional[date] = None, 
                                 end_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Retrieve calendar configuration for a date range.
        
        Args:
            start_date: Start date for range (optional)
            end_date: End date for range (optional)
            
        Returns:
            Dict with calendar configuration data
            
        Requirements: 1.1 - Display calendar interface
        """
        try:
            query = self.db.query(CalendarConfig)
            
            # Apply date range filters if provided
            if start_date:
                query = query.filter(CalendarConfig.date >= start_date)
            if end_date:
                query = query.filter(CalendarConfig.date <= end_date)
            
            # Order by date
            configs = query.order_by(CalendarConfig.date).all()
            
            # Convert to calendar day format with attendance counts
            calendar_days = []
            for config in configs:
                day_data = {
                    "date": config.date.strftime('%Y-%m-%d'),
                    "has_run": config.has_run,
                    "attendance_count": None,
                    "session_id": None
                }
                
                # Get run and attendance data if it's a run day
                if config.has_run:
                    run = self.db.query(Run).filter(
                        Run.date == config.date,
                        Run.is_active == True
                    ).first()
                    
                    if run:
                        day_data["session_id"] = run.session_id
                        # Count attendances for this run
                        attendance_count = self.db.query(Attendance).filter(
                            Attendance.run_id == run.id
                        ).count()
                        day_data["attendance_count"] = attendance_count
                
                calendar_days.append(day_data)
            
            logger.info(f"Retrieved {len(calendar_days)} calendar configurations")
            
            return {
                "success": True,
                "data": calendar_days,
                "message": "Calendar configuration retrieved successfully"
            }
            
        except Exception as e:
            logger.error(f"Error retrieving calendar configuration: {e}")
            return {
                "success": False,
                "data": [],
                "message": f"Failed to retrieve calendar configuration: {str(e)}"
            }
    
    def get_today_status(self) -> Dict[str, Any]:
        """
        Get today's run status and attendance information.
        
        Returns:
            Dict with today's run status
            
        Requirements: 3.1 - Display current day attendance, 3.4 - Show appropriate message when no runs
        """
        try:
            today = date.today()
            
            # Check if today has a configured run
            config = self.db.query(CalendarConfig).filter(
                CalendarConfig.date == today
            ).first()
            
            if not config or not config.has_run:
                return {
                    "success": True,
                    "has_run_today": False,
                    "session_id": None,
                    "attendance_count": 0,
                    "message": "No run scheduled for today"
                }
            
            # Get today's run information
            run = self.db.query(Run).filter(
                Run.date == today,
                Run.is_active == True
            ).first()
            
            if not run:
                # Configuration says there's a run but no Run record exists
                logger.warning(f"Calendar config indicates run for {today} but no Run record found")
                return {
                    "success": True,
                    "has_run_today": True,
                    "session_id": None,
                    "attendance_count": 0,
                    "message": "Run scheduled but not yet active"
                }
            
            # Count today's attendance
            attendance_count = self.db.query(Attendance).filter(
                Attendance.run_id == run.id
            ).count()
            
            logger.info(f"Today's run status: session_id={run.session_id}, attendance={attendance_count}")
            
            return {
                "success": True,
                "has_run_today": True,
                "session_id": run.session_id,
                "attendance_count": attendance_count,
                "message": f"Run scheduled for today with {attendance_count} attendees"
            }
            
        except Exception as e:
            logger.error(f"Error getting today's status: {e}")
            return {
                "success": False,
                "has_run_today": False,
                "session_id": None,
                "attendance_count": 0,
                "message": f"Failed to get today's status: {str(e)}"
            }
    
    def _ensure_run_exists(self, target_date: date) -> None:
        """
        Ensure a Run record exists for the given date.
        
        Args:
            target_date: Date to ensure run exists for
        """
        existing_run = self.db.query(Run).filter(
            Run.date == target_date
        ).first()
        
        if not existing_run:
            # Generate unique session ID
            session_id = self._generate_session_id(target_date)
            
            new_run = Run(
                date=target_date,
                session_id=session_id,
                is_active=True
            )
            self.db.add(new_run)
            logger.info(f"Created new run for {target_date} with session_id={session_id}")
        elif not existing_run.is_active:
            # Reactivate existing run
            existing_run.is_active = True
            logger.info(f"Reactivated run for {target_date}")
    
    def _deactivate_run(self, target_date: date) -> None:
        """
        Deactivate run for the given date.
        
        Args:
            target_date: Date to deactivate run for
        """
        existing_run = self.db.query(Run).filter(
            Run.date == target_date
        ).first()
        
        if existing_run and existing_run.is_active:
            existing_run.is_active = False
            logger.info(f"Deactivated run for {target_date}")
    
    def _generate_session_id(self, target_date: date) -> str:
        """
        Generate a unique session ID for a run.
        
        Args:
            target_date: Date for the run
            
        Returns:
            Unique session ID string
        """
        # Format: YYYYMMDD-UUID4
        date_str = target_date.strftime('%Y%m%d')
        unique_id = str(uuid.uuid4())[:8]  # First 8 characters of UUID
        return f"{date_str}-{unique_id}"
    
    def get_run_by_session_id(self, session_id: str) -> Optional[Run]:
        """
        Get run by session ID.
        
        Args:
            session_id: Session ID to search for
            
        Returns:
            Run object if found, None otherwise
        """
        try:
            return self.db.query(Run).filter(
                Run.session_id == session_id,
                Run.is_active == True
            ).first()
        except Exception as e:
            logger.error(f"Error getting run by session_id {session_id}: {e}")
            return None
    
    def validate_run_date(self, target_date: date) -> bool:
        """
        Validate if a date is configured for runs.
        
        Args:
            target_date: Date to validate
            
        Returns:
            True if date is configured for runs, False otherwise
        """
        try:
            config = self.db.query(CalendarConfig).filter(
                CalendarConfig.date == target_date
            ).first()
            
            return config is not None and config.has_run
        except Exception as e:
            logger.error(f"Error validating run date {target_date}: {e}")
            return False