"""
Registration Service for handling attendance registration with duplicate prevention
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, func
import logging
import asyncio
import csv
import io

from ..models.run import Run
from ..models.attendance import Attendance
from ..models.calendar_config import CalendarConfig
from ..schemas import RegistrationRequest, RegistrationResponse

logger = logging.getLogger(__name__)


class RegistrationService:
    """Service for handling attendance registration with duplicate prevention logic"""
    
    def __init__(self, db: Session, websocket_service=None):
        self.db = db
        self.websocket_service = websocket_service
    
    def register_attendance(self, registration: RegistrationRequest) -> RegistrationResponse:
        """
        Register attendance for a runner with duplicate prevention
        
        Requirements:
        - 2.1: Quick registration process
        - 2.2: Record attendance within 2 seconds
        - 2.3: Prevent duplicate registration
        - 4.4: Maintain data integrity during peak load
        
        Args:
            registration: RegistrationRequest with session_id and runner_name
            
        Returns:
            RegistrationResponse with success status and current count
            
        Raises:
            ValueError: If session_id is invalid or run not found
            IntegrityError: If duplicate registration attempted
        """
        try:
            logger.info(f"Processing registration for {registration.runner_name} in session {registration.session_id}")
            
            # Find the run by session_id
            run = self.db.query(Run).filter(
                and_(
                    Run.session_id == registration.session_id,
                    Run.is_active == True
                )
            ).first()
            
            if not run:
                logger.warning(f"Run not found for session_id: {registration.session_id}")
                return RegistrationResponse(
                    success=False,
                    message="Invalid session ID or run not active",
                    current_count=0
                )
            
            # Check if runner already registered for this run
            existing_attendance = self.db.query(Attendance).filter(
                and_(
                    Attendance.run_id == run.id,
                    Attendance.runner_name == registration.runner_name.strip()
                )
            ).first()
            
            if existing_attendance:
                logger.info(f"Duplicate registration attempt for {registration.runner_name} in session {registration.session_id}")
                current_count = self.get_attendance_count_for_run(run.id)
                return RegistrationResponse(
                    success=False,
                    message=f"You have already registered for this run",
                    current_count=current_count,
                    runner_name=registration.runner_name
                )
            
            # Create new attendance record
            new_attendance = Attendance(
                run_id=run.id,
                runner_name=registration.runner_name.strip(),
                registered_at=datetime.utcnow()
            )
            
            self.db.add(new_attendance)
            self.db.commit()
            self.db.refresh(new_attendance)
            
            # Get updated attendance count
            current_count = self.get_attendance_count_for_run(run.id)
            
            # Create response
            response = RegistrationResponse(
                success=True,
                message=f"Registration successful! Welcome to the run, {registration.runner_name}",
                current_count=current_count,
                runner_name=registration.runner_name
            )
            
            # Broadcast real-time update if WebSocket service is available
            if self.websocket_service:
                try:
                    # Prepare attendance data for broadcast
                    attendance_data = {
                        "runner_name": registration.runner_name,
                        "current_count": current_count,
                        "registered_at": new_attendance.registered_at.isoformat(),
                        "run_date": run.date.isoformat(),
                        "message": response.message
                    }
                    
                    # Schedule the broadcast (non-blocking)
                    asyncio.create_task(
                        self.websocket_service.broadcast_attendance_update(
                            registration.session_id, 
                            attendance_data
                        )
                    )
                    
                    # Also broadcast registration success
                    asyncio.create_task(
                        self.websocket_service.broadcast_registration_success(
                            registration.session_id,
                            attendance_data
                        )
                    )
                    
                except Exception as ws_error:
                    # Don't fail the registration if WebSocket broadcast fails
                    logger.warning(f"WebSocket broadcast failed: {str(ws_error)}")
            
            logger.info(f"Successfully registered {registration.runner_name} for session {registration.session_id}")
            
            return response
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Database integrity error during registration: {str(e)}")
            # This handles the database-level unique constraint
            current_count = self.get_attendance_count_for_run(run.id) if 'run' in locals() else 0
            return RegistrationResponse(
                success=False,
                message="You have already registered for this run",
                current_count=current_count,
                runner_name=registration.runner_name
            )
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error processing registration: {str(e)}")
            raise
    
    def get_today_attendance_count(self) -> Dict[str, Any]:
        """
        Get current day attendance count
        
        Requirements:
        - 3.1: Display current day attendance count
        
        Returns:
            Dict with success status, count, and message
        """
        try:
            today = date.today()
            
            # Find today's run
            today_run = self.db.query(Run).filter(
                and_(
                    Run.date == today,
                    Run.is_active == True
                )
            ).first()
            
            if not today_run:
                logger.info(f"No active run found for today: {today}")
                return {
                    "success": True,
                    "count": 0,
                    "has_run_today": False,
                    "message": "No run scheduled for today"
                }
            
            # Get attendance count for today's run
            count = self.get_attendance_count_for_run(today_run.id)
            
            logger.info(f"Today's attendance count: {count}")
            
            return {
                "success": True,
                "count": count,
                "has_run_today": True,
                "session_id": today_run.session_id,
                "message": f"Today's attendance: {count} runners"
            }
            
        except Exception as e:
            logger.error(f"Error retrieving today's attendance count: {str(e)}")
            raise
    
    def get_attendance_count_for_run(self, run_id: int) -> int:
        """
        Get attendance count for a specific run
        
        Args:
            run_id: ID of the run
            
        Returns:
            Number of attendees for the run
        """
        try:
            count = self.db.query(func.count(Attendance.id)).filter(
                Attendance.run_id == run_id
            ).scalar()
            
            return count or 0
            
        except Exception as e:
            logger.error(f"Error getting attendance count for run {run_id}: {str(e)}")
            return 0
    
    def get_attendance_history(
        self, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Get historical attendance data with optional date filtering and pagination
        
        Requirements:
        - 3.3: Display attendance records for previous runs
        - 6.3: Export data within specified date range
        - Task 8: Add pagination support for large attendance datasets
        
        Args:
            start_date: Optional start date in YYYY-MM-DD format
            end_date: Optional end date in YYYY-MM-DD format
            page: Page number (1-based)
            page_size: Number of records per page
            
        Returns:
            Dict with success status, data list, total count, and pagination info
        """
        try:
            # Validate pagination parameters
            if page < 1:
                page = 1
            if page_size < 1 or page_size > 1000:  # Limit max page size
                page_size = 50
            
            query = self.db.query(
                Attendance.id,
                Attendance.runner_name,
                Attendance.registered_at,
                Run.date.label('run_date'),
                Run.session_id
            ).join(Run, Attendance.run_id == Run.id)
            
            # Apply date filters if provided
            if start_date:
                try:
                    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                    query = query.filter(Run.date >= start_date_obj)
                except ValueError:
                    logger.warning(f"Invalid start_date format: {start_date}")
            
            if end_date:
                try:
                    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                    query = query.filter(Run.date <= end_date_obj)
                except ValueError:
                    logger.warning(f"Invalid end_date format: {end_date}")
            
            # Get total count before pagination
            total_count = query.count()
            
            # Order by run date and registration time
            query = query.order_by(Run.date.desc(), Attendance.registered_at.desc())
            
            # Apply pagination
            offset = (page - 1) * page_size
            results = query.offset(offset).limit(page_size).all()
            
            # Format data for response
            data = []
            for result in results:
                data.append({
                    "id": result.id,
                    "runner_name": result.runner_name,
                    "registered_at": result.registered_at.isoformat(),
                    "run_date": result.run_date.isoformat(),
                    "session_id": result.session_id
                })
            
            # Calculate pagination info
            total_pages = (total_count + page_size - 1) // page_size
            has_next = page < total_pages
            has_prev = page > 1
            
            logger.info(f"Retrieved {len(data)} attendance records (page {page}/{total_pages})")
            
            return {
                "success": True,
                "data": data,
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev,
                "message": f"Retrieved {len(data)} of {total_count} attendance records"
            }
            
        except Exception as e:
            logger.error(f"Error retrieving attendance history: {str(e)}")
            raise
    
    def validate_session_id(self, session_id: str) -> bool:
        """
        Validate if session_id corresponds to an active run
        
        Args:
            session_id: Session ID to validate
            
        Returns:
            True if session_id is valid and run is active
        """
        try:
            run = self.db.query(Run).filter(
                and_(
                    Run.session_id == session_id,
                    Run.is_active == True
                )
            ).first()
            
            return run is not None
            
        except Exception as e:
            logger.error(f"Error validating session_id {session_id}: {str(e)}")
            return False
    
    def get_run_by_session_id(self, session_id: str) -> Optional[Run]:
        """
        Get run by session ID
        
        Args:
            session_id: Session ID to look up
            
        Returns:
            Run object if found, None otherwise
        """
        try:
            return self.db.query(Run).filter(
                and_(
                    Run.session_id == session_id,
                    Run.is_active == True
                )
            ).first()
            
        except Exception as e:
            logger.error(f"Error getting run by session_id {session_id}: {str(e)}")
            return None
    
    def export_attendance_csv(
        self, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> str:
        """
        Export attendance data in CSV format
        
        Requirements:
        - 6.1: Provide attendance data in CSV format
        - 6.2: Include runner names, dates, and timestamps
        - 6.3: Export data within specified date range
        - 6.4: Provide empty export with headers if no data
        - Task 8: Create data export functionality using Python csv module
        
        Args:
            start_date: Optional start date in YYYY-MM-DD format
            end_date: Optional end date in YYYY-MM-DD format
            
        Returns:
            CSV string with attendance data
        """
        try:
            # Create CSV in memory
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write CSV headers
            headers = [
                'Runner Name',
                'Run Date', 
                'Registration Time',
                'Session ID',
                'Attendance ID'
            ]
            writer.writerow(headers)
            
            # Get attendance data (without pagination for export)
            query = self.db.query(
                Attendance.id,
                Attendance.runner_name,
                Attendance.registered_at,
                Run.date.label('run_date'),
                Run.session_id
            ).join(Run, Attendance.run_id == Run.id)
            
            # Apply date filters if provided
            if start_date:
                try:
                    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                    query = query.filter(Run.date >= start_date_obj)
                except ValueError:
                    logger.warning(f"Invalid start_date format: {start_date}")
            
            if end_date:
                try:
                    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                    query = query.filter(Run.date <= end_date_obj)
                except ValueError:
                    logger.warning(f"Invalid end_date format: {end_date}")
            
            # Order by run date and registration time
            query = query.order_by(Run.date.desc(), Attendance.registered_at.desc())
            
            results = query.all()
            
            # Write data rows
            for result in results:
                writer.writerow([
                    result.runner_name,
                    result.run_date.strftime('%Y-%m-%d'),
                    result.registered_at.strftime('%Y-%m-%d %H:%M:%S'),
                    result.session_id,
                    result.id
                ])
            
            csv_content = output.getvalue()
            output.close()
            
            logger.info(f"Generated CSV export with {len(results)} attendance records")
            
            return csv_content
            
        except Exception as e:
            logger.error(f"Error generating CSV export: {str(e)}")
            raise
    
    def get_attendance_export_filename(
        self, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> str:
        """
        Generate appropriate filename for attendance export
        
        Args:
            start_date: Optional start date in YYYY-MM-DD format
            end_date: Optional end date in YYYY-MM-DD format
            
        Returns:
            Filename string for the export
        """
        try:
            base_name = "attendance_export"
            
            if start_date and end_date:
                filename = f"{base_name}_{start_date}_to_{end_date}.csv"
            elif start_date:
                filename = f"{base_name}_from_{start_date}.csv"
            elif end_date:
                filename = f"{base_name}_until_{end_date}.csv"
            else:
                # Use current date for filename
                current_date = datetime.now().strftime('%Y-%m-%d')
                filename = f"{base_name}_{current_date}.csv"
            
            return filename
            
        except Exception as e:
            logger.error(f"Error generating export filename: {str(e)}")
            return "attendance_export.csv"