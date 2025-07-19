"""
Calendar management routes
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
import logging

from ..database.connection import get_db
from ..services.calendar_service import CalendarService
from ..schemas import (
    CalendarConfigRequest, 
    CalendarResponse, 
    TodayStatusResponse,
    SuccessResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=CalendarResponse)
async def get_calendar(db: Session = Depends(get_db)):
    """
    Retrieve calendar configuration
    Requirements: 1.1 - Display calendar interface
    """
    try:
        logger.info("Retrieving calendar configuration")
        calendar_service = CalendarService(db)
        result = calendar_service.get_calendar_configuration()
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["message"])
        
        return CalendarResponse(
            success=result["success"],
            data=result["data"],
            message=result["message"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving calendar: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve calendar data")

@router.post("/configure", response_model=SuccessResponse)
async def configure_calendar(config: CalendarConfigRequest, db: Session = Depends(get_db)):
    """
    Update run day settings
    Requirements: 1.2, 1.3 - Allow marking run days and persist configuration
    """
    try:
        logger.info(f"Configuring calendar for date {config.date}: has_run={config.has_run}")
        
        # Parse date string to date object
        try:
            target_date = datetime.strptime(config.date, '%Y-%m-%d').date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        calendar_service = CalendarService(db)
        result = calendar_service.configure_run_day(target_date, config.has_run)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["message"])
        
        return SuccessResponse(
            success=result["success"],
            message=result["message"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error configuring calendar: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update calendar configuration")

@router.get("/today", response_model=TodayStatusResponse)
async def get_today_status(db: Session = Depends(get_db)):
    """
    Check current day run status
    Requirements: 3.1 - Display current day attendance, 3.4 - Show appropriate message when no runs
    """
    try:
        logger.info("Checking today's run status")
        
        calendar_service = CalendarService(db)
        result = calendar_service.get_today_status()
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["message"])
        
        return TodayStatusResponse(
            success=result["success"],
            has_run_today=result["has_run_today"],
            session_id=result["session_id"],
            attendance_count=result["attendance_count"],
            message=result["message"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking today's status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to check today's run status")