"""
Attendance Override API routes for manual attendance management
"""
from fastapi import APIRouter, HTTPException, Query, Path, Depends
from typing import Optional, List
from datetime import datetime, date
from sqlalchemy.orm import Session
import logging

from ..schemas import SuccessResponse, ErrorResponse
from ..services.attendance_override_service import AttendanceOverrideService
from ..database.connection import get_db
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter()

# Service will be initialized with database session in each endpoint

# Request/Response models
class AddAttendanceRequest(BaseModel):
    """Request model for adding attendance record"""
    runner_name: str = Field(..., min_length=1, max_length=255, description="Name of the runner")
    run_date: str = Field(..., description="Date of the run (YYYY-MM-DD)")
    session_id: Optional[str] = Field(None, description="Optional session ID")
    registered_at: Optional[str] = Field(None, description="Optional registration timestamp (ISO format)")

class EditAttendanceRequest(BaseModel):
    """Request model for editing attendance record"""
    runner_name: Optional[str] = Field(None, min_length=1, max_length=255, description="New runner name")
    run_date: Optional[str] = Field(None, description="New run date (YYYY-MM-DD)")
    registered_at: Optional[str] = Field(None, description="New registration timestamp (ISO format)")

class BulkOperation(BaseModel):
    """Model for bulk operation item"""
    action: str = Field(..., description="Action: 'add', 'edit', or 'remove'")
    attendance_id: Optional[int] = Field(None, description="Required for edit/remove operations")
    runner_name: Optional[str] = Field(None, description="Runner name for add/edit operations")
    run_date: Optional[str] = Field(None, description="Run date for add/edit operations")
    session_id: Optional[str] = Field(None, description="Session ID for add operations")
    registered_at: Optional[str] = Field(None, description="Registration timestamp")

class BulkOperationsRequest(BaseModel):
    """Request model for bulk operations"""
    operations: List[BulkOperation] = Field(..., description="List of operations to perform")

class AttendanceOverrideResponse(BaseModel):
    """Response model for attendance override operations"""
    success: bool
    message: str
    attendance_id: Optional[int] = None
    run_id: Optional[int] = None
    session_id: Optional[str] = None
    data: Optional[dict] = None

@router.post("/add", response_model=AttendanceOverrideResponse)
async def add_attendance_record(request: AddAttendanceRequest, db: Session = Depends(get_db)):
    """
    Manually add an attendance record for a runner
    
    This endpoint allows administrators to add attendance records for runners
    who were present but didn't scan QR codes or for historical data entry.
    """
    try:
        logger.info(f"Adding manual attendance record for {request.runner_name} on {request.run_date}")
        
        # Parse date
        try:
            run_date = datetime.fromisoformat(request.run_date).date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        # Parse registration timestamp if provided
        registered_at = None
        if request.registered_at:
            try:
                registered_at = datetime.fromisoformat(request.registered_at)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid timestamp format. Use ISO format")
        
        # Create service instance with database session
        override_service = AttendanceOverrideService(db)
        
        # Add attendance record
        result = override_service.add_attendance_record(
            runner_name=request.runner_name,
            run_date=run_date,
            session_id=request.session_id,
            registered_at=registered_at
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        
        return AttendanceOverrideResponse(
            success=True,
            message=result["message"],
            attendance_id=result.get("attendance_id"),
            run_id=result.get("run_id"),
            session_id=result.get("session_id")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding attendance record: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to add attendance record")

@router.put("/{attendance_id}", response_model=AttendanceOverrideResponse)
async def edit_attendance_record(
    attendance_id: int = Path(..., description="ID of the attendance record to edit"),
    request: EditAttendanceRequest = None,
    db: Session = Depends(get_db)
):
    """
    Edit an existing attendance record
    
    This endpoint allows administrators to modify existing attendance records,
    including changing runner names, run dates, or registration timestamps.
    """
    try:
        logger.info(f"Editing attendance record {attendance_id}")
        
        # Parse date if provided
        run_date = None
        if request.run_date:
            try:
                run_date = datetime.fromisoformat(request.run_date).date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        # Parse registration timestamp if provided
        registered_at = None
        if request.registered_at:
            try:
                registered_at = datetime.fromisoformat(request.registered_at)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid timestamp format. Use ISO format")
        
        # Create service instance with database session
        override_service = AttendanceOverrideService(db)
        
        # Edit attendance record
        result = override_service.edit_attendance_record(
            attendance_id=attendance_id,
            runner_name=request.runner_name,
            run_date=run_date,
            registered_at=registered_at
        )
        
        if not result["success"]:
            if "not found" in result["message"].lower():
                raise HTTPException(status_code=404, detail=result["message"])
            else:
                raise HTTPException(status_code=400, detail=result["message"])
        
        return AttendanceOverrideResponse(
            success=True,
            message=result["message"],
            attendance_id=attendance_id,
            data=result.get("changes")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error editing attendance record {attendance_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to edit attendance record")

@router.delete("/{attendance_id}", response_model=AttendanceOverrideResponse)
async def remove_attendance_record(
    attendance_id: int = Path(..., description="ID of the attendance record to remove"),
    db: Session = Depends(get_db)
):
    """
    Remove an attendance record
    
    This endpoint allows administrators to delete attendance records that were
    marked incorrectly or need to be removed for other reasons.
    """
    try:
        logger.info(f"Removing attendance record {attendance_id}")
        
        # Create service instance with database session
        override_service = AttendanceOverrideService(db)
        
        # Remove attendance record
        result = override_service.remove_attendance_record(attendance_id)
        
        if not result["success"]:
            if "not found" in result["message"].lower():
                raise HTTPException(status_code=404, detail=result["message"])
            else:
                raise HTTPException(status_code=400, detail=result["message"])
        
        return AttendanceOverrideResponse(
            success=True,
            message=result["message"],
            data=result.get("removed_record")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing attendance record {attendance_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to remove attendance record")

@router.post("/bulk", response_model=dict)
async def bulk_operations(request: BulkOperationsRequest, db: Session = Depends(get_db)):
    """
    Perform bulk operations on attendance records
    
    This endpoint allows administrators to perform multiple add, edit, or remove
    operations in a single request for efficient batch processing.
    """
    try:
        logger.info(f"Processing {len(request.operations)} bulk operations")
        
        # Convert operations to service format
        operations = []
        for op in request.operations:
            operation = {"action": op.action}
            
            if op.attendance_id is not None:
                operation["attendance_id"] = op.attendance_id
            if op.runner_name is not None:
                operation["runner_name"] = op.runner_name
            if op.run_date is not None:
                operation["run_date"] = op.run_date
            if op.session_id is not None:
                operation["session_id"] = op.session_id
            if op.registered_at is not None:
                operation["registered_at"] = op.registered_at
            
            operations.append(operation)
        
        # Create service instance with database session
        override_service = AttendanceOverrideService(db)
        
        # Perform bulk operations
        result = override_service.bulk_operations(operations)
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing bulk operations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process bulk operations")

@router.get("/{attendance_id}", response_model=dict)
async def get_attendance_record(
    attendance_id: int = Path(..., description="ID of the attendance record to retrieve"),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific attendance record
    
    This endpoint retrieves detailed information about a specific attendance record,
    including associated run information.
    """
    try:
        logger.info(f"Getting attendance record {attendance_id}")
        
        # Create service instance with database session
        override_service = AttendanceOverrideService(db)
        
        result = override_service.get_attendance_record(attendance_id)
        
        if not result["success"]:
            if "not found" in result["message"].lower():
                raise HTTPException(status_code=404, detail=result["message"])
            else:
                raise HTTPException(status_code=400, detail=result["message"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting attendance record {attendance_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get attendance record")

@router.get("/search/records", response_model=dict)
async def search_attendance_records(
    runner_name: Optional[str] = Query(None, description="Filter by runner name (partial match)"),
    start_date: Optional[str] = Query(None, description="Filter by start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter by end date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """
    Search attendance records with filters
    
    This endpoint allows administrators to search and filter attendance records
    by runner name, date range, and other criteria for management purposes.
    """
    try:
        logger.info(f"Searching attendance records with filters: runner={runner_name}, start={start_date}, end={end_date}")
        
        # Parse dates if provided
        parsed_start_date = None
        parsed_end_date = None
        
        if start_date:
            try:
                parsed_start_date = datetime.fromisoformat(start_date).date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")
        
        if end_date:
            try:
                parsed_end_date = datetime.fromisoformat(end_date).date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")
        
        # Create service instance with database session
        override_service = AttendanceOverrideService(db)
        
        # Search records
        result = override_service.search_attendance_records(
            runner_name=runner_name,
            start_date=parsed_start_date,
            end_date=parsed_end_date,
            limit=limit
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching attendance records: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search attendance records")