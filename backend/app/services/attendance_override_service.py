"""
Attendance Override Service for manual attendance record management
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import logging

from ..models.attendance import Attendance, AttendanceCreate, AttendanceResponse
from ..models.run import Run, RunCreate
from ..services.calendar_service import CalendarService

logger = logging.getLogger(__name__)

class AttendanceOverrideService:
    """Service for managing attendance record overrides"""
    
    def __init__(self, db: Session):
        """Initialize service with database session"""
        self.db = db
    
    def add_attendance_record(
        self, 
        runner_name: str, 
        run_date: date, 
        session_id: Optional[str] = None,
        registered_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Manually add an attendance record for a runner
        
        Args:
            runner_name: Name of the runner
            run_date: Date of the run
            session_id: Optional session ID (will be generated if not provided)
            registered_at: Optional registration timestamp (defaults to now)
            
        Returns:
            Dictionary with operation result
        """
        try:
            # Check if run exists for the date
            existing_run = self.db.query(Run).filter(Run.date == run_date).first()
            
            if not existing_run:
                # Create run if it doesn't exist
                if not session_id:
                    session_id = f"manual-{run_date.isoformat()}-{datetime.now().timestamp()}"
                
                existing_run = Run(
                    date=run_date,
                    session_id=session_id,
                    is_active=True
                )
                self.db.add(existing_run)
                self.db.flush()  # Get the ID
                logger.info(f"Created new run for date {run_date} with session {session_id}")
            
            # Check for duplicate attendance
            existing_attendance = self.db.query(Attendance).filter(
                and_(
                    Attendance.run_id == existing_run.id,
                    Attendance.runner_name == runner_name
                )
            ).first()
            
            if existing_attendance:
                return {
                    "success": False,
                    "message": f"Attendance record already exists for {runner_name} on {run_date}",
                    "attendance_id": existing_attendance.id
                }
            
            # Create attendance record
            attendance = Attendance(
                run_id=existing_run.id,
                runner_name=runner_name,
                registered_at=registered_at or datetime.now()
            )
            self.db.add(attendance)
            self.db.commit()
            
            logger.info(f"Added manual attendance record for {runner_name} on {run_date}")
            
            return {
                "success": True,
                "message": f"Successfully added attendance record for {runner_name}",
                "attendance_id": attendance.id,
                "run_id": existing_run.id,
                "session_id": existing_run.session_id
            }
            
        except Exception as e:
            logger.error(f"Error adding attendance record: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to add attendance record: {str(e)}"
            }
    
    def edit_attendance_record(
        self, 
        attendance_id: int, 
        runner_name: Optional[str] = None,
        run_date: Optional[date] = None,
        registered_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Edit an existing attendance record
        
        Args:
            attendance_id: ID of the attendance record to edit
            runner_name: New runner name (optional)
            run_date: New run date (optional)
            registered_at: New registration timestamp (optional)
            
        Returns:
            Dictionary with operation result
        """
        try:
            # Get existing attendance record
            attendance = self.db.query(Attendance).filter(Attendance.id == attendance_id).first()
            
            if not attendance:
                return {
                    "success": False,
                    "message": f"Attendance record with ID {attendance_id} not found"
                }
            
            # Store original values for logging
            original_name = attendance.runner_name
            original_run_id = attendance.run_id
            
            # Update runner name if provided
            if runner_name is not None:
                # Check for duplicate with new name
                duplicate = self.db.query(Attendance).filter(
                    and_(
                        Attendance.run_id == attendance.run_id,
                        Attendance.runner_name == runner_name,
                        Attendance.id != attendance_id
                    )
                ).first()
                
                if duplicate:
                    return {
                        "success": False,
                        "message": f"Another attendance record already exists for {runner_name} on this run"
                    }
                
                attendance.runner_name = runner_name
            
            # Update run date if provided
            if run_date is not None:
                # Find or create run for new date
                target_run = self.db.query(Run).filter(Run.date == run_date).first()
                
                if not target_run:
                    # Create new run
                    session_id = f"manual-{run_date.isoformat()}-{datetime.now().timestamp()}"
                    target_run = Run(
                        date=run_date,
                        session_id=session_id,
                        is_active=True
                    )
                    self.db.add(target_run)
                    self.db.flush()
                
                # Check for duplicate with new run
                duplicate = self.db.query(Attendance).filter(
                    and_(
                        Attendance.run_id == target_run.id,
                        Attendance.runner_name == attendance.runner_name,
                        Attendance.id != attendance_id
                    )
                ).first()
                
                if duplicate:
                    return {
                        "success": False,
                        "message": f"Attendance record already exists for {attendance.runner_name} on {run_date}"
                    }
                
                attendance.run_id = target_run.id
            
            # Update registration time if provided
            if registered_at is not None:
                attendance.registered_at = registered_at
            
            self.db.commit()
            
            logger.info(f"Updated attendance record {attendance_id}: {original_name} -> {attendance.runner_name}")
            
            return {
                "success": True,
                "message": f"Successfully updated attendance record",
                "attendance_id": attendance_id,
                "changes": {
                    "runner_name": attendance.runner_name if runner_name else None,
                    "run_date": run_date.isoformat() if run_date else None,
                    "registered_at": registered_at.isoformat() if registered_at else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error editing attendance record {attendance_id}: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to edit attendance record: {str(e)}"
            }
    
    def remove_attendance_record(self, attendance_id: int) -> Dict[str, Any]:
        """
        Remove an attendance record
        
        Args:
            attendance_id: ID of the attendance record to remove
            
        Returns:
            Dictionary with operation result
        """
        try:
            # Get attendance record
            attendance = self.db.query(Attendance).filter(Attendance.id == attendance_id).first()
            
            if not attendance:
                return {
                    "success": False,
                    "message": f"Attendance record with ID {attendance_id} not found"
                }
            
            # Store info for logging
            runner_name = attendance.runner_name
            run = self.db.query(Run).filter(Run.id == attendance.run_id).first()
            run_date = run.date if run else "unknown"
            
            # Delete the record
            self.db.delete(attendance)
            self.db.commit()
            
            logger.info(f"Removed attendance record {attendance_id} for {runner_name} on {run_date}")
            
            return {
                "success": True,
                "message": f"Successfully removed attendance record for {runner_name}",
                "removed_record": {
                    "attendance_id": attendance_id,
                    "runner_name": runner_name,
                    "run_date": run_date.isoformat() if hasattr(run_date, 'isoformat') else str(run_date)
                }
            }
            
        except Exception as e:
            logger.error(f"Error removing attendance record {attendance_id}: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to remove attendance record: {str(e)}"
            }
    
    def bulk_operations(self, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform bulk operations on attendance records
        
        Args:
            operations: List of operation dictionaries with 'action' and parameters
            
        Returns:
            Dictionary with bulk operation results
        """
        results = []
        success_count = 0
        error_count = 0
        
        for i, operation in enumerate(operations):
            try:
                action = operation.get('action')
                
                if action == 'add':
                    result = self.add_attendance_record(
                        runner_name=operation['runner_name'],
                        run_date=datetime.fromisoformat(operation['run_date']).date(),
                        session_id=operation.get('session_id'),
                        registered_at=datetime.fromisoformat(operation['registered_at']) if operation.get('registered_at') else None
                    )
                elif action == 'edit':
                    result = self.edit_attendance_record(
                        attendance_id=operation['attendance_id'],
                        runner_name=operation.get('runner_name'),
                        run_date=datetime.fromisoformat(operation['run_date']).date() if operation.get('run_date') else None,
                        registered_at=datetime.fromisoformat(operation['registered_at']) if operation.get('registered_at') else None
                    )
                elif action == 'remove':
                    result = self.remove_attendance_record(
                        attendance_id=operation['attendance_id']
                    )
                else:
                    result = {
                        "success": False,
                        "message": f"Unknown action: {action}"
                    }
                
                result['operation_index'] = i
                results.append(result)
                
                if result['success']:
                    success_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                error_result = {
                    "success": False,
                    "message": f"Error processing operation {i}: {str(e)}",
                    "operation_index": i
                }
                results.append(error_result)
                error_count += 1
        
        logger.info(f"Bulk operations completed: {success_count} successful, {error_count} failed")
        
        return {
            "success": error_count == 0,
            "message": f"Processed {len(operations)} operations: {success_count} successful, {error_count} failed",
            "summary": {
                "total_operations": len(operations),
                "successful": success_count,
                "failed": error_count
            },
            "results": results
        }
    
    def get_attendance_record(self, attendance_id: int) -> Dict[str, Any]:
        """
        Get details of a specific attendance record
        
        Args:
            attendance_id: ID of the attendance record
            
        Returns:
            Dictionary with attendance record details
        """
        try:
            attendance = self.db.query(Attendance).filter(Attendance.id == attendance_id).first()
            
            if not attendance:
                return {
                    "success": False,
                    "message": f"Attendance record with ID {attendance_id} not found"
                }
            
            # Get run details
            run = self.db.query(Run).filter(Run.id == attendance.run_id).first()
            
            return {
                "success": True,
                "data": {
                    "attendance_id": attendance.id,
                    "runner_name": attendance.runner_name,
                    "registered_at": attendance.registered_at.isoformat(),
                    "run": {
                        "run_id": run.id,
                        "date": run.date.isoformat(),
                        "session_id": run.session_id,
                        "is_active": run.is_active
                    } if run else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting attendance record {attendance_id}: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to get attendance record: {str(e)}"
            }
    
    def search_attendance_records(
        self, 
        runner_name: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Search attendance records with filters
        
        Args:
            runner_name: Filter by runner name (partial match)
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of records to return
            
        Returns:
            Dictionary with search results
        """
        try:
            query = self.db.query(Attendance).join(Run)
            
            # Apply filters
            if runner_name:
                query = query.filter(Attendance.runner_name.ilike(f"%{runner_name}%"))
            
            if start_date:
                query = query.filter(Run.date >= start_date)
            
            if end_date:
                query = query.filter(Run.date <= end_date)
            
            # Order by most recent first
            query = query.order_by(Run.date.desc(), Attendance.registered_at.desc())
            
            # Apply limit
            attendances = query.limit(limit).all()
            
            # Format results
            results = []
            for attendance in attendances:
                run = self.db.query(Run).filter(Run.id == attendance.run_id).first()
                results.append({
                    "attendance_id": attendance.id,
                    "runner_name": attendance.runner_name,
                    "registered_at": attendance.registered_at.isoformat(),
                    "run_date": run.date.isoformat() if run else None,
                    "session_id": run.session_id if run else None
                })
            
            return {
                "success": True,
                "data": results,
                "count": len(results),
                "filters": {
                    "runner_name": runner_name,
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None,
                    "limit": limit
                }
            }
            
        except Exception as e:
            logger.error(f"Error searching attendance records: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to search attendance records: {str(e)}"
            }