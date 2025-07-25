"""
Registration and attendance routes with performance optimizations
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Optional
import logging

from ..database.connection import get_db
from ..services.registration_service import RegistrationService
from ..services.websocket_service import websocket_service
from ..services.cache_service import cache_service, CacheKeys
from ..middleware.rate_limiting import (
    registration_rate_limit, 
    export_rate_limit, 
    general_api_rate_limit,
    limiter
)
from ..schemas import (
    RegistrationRequest,
    RegistrationResponse,
    AttendanceHistoryResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/register", response_model=RegistrationResponse)
@limiter.limit("10/minute")  # Rate limit: 10 registrations per minute per IP
async def register_attendance(
    request: Request, 
    registration: RegistrationRequest, 
    db: Session = Depends(get_db)
):
    """
    Register attendance for a runner with rate limiting and cache invalidation
    Requirements: 2.1, 2.2 - Quick registration and record within 2 seconds
    Requirements: 2.3 - Prevent duplicate registration
    Requirements: 4.4 - Maintain data integrity during peak load
    """
    try:
        registration_service = RegistrationService(db, websocket_service)
        result = registration_service.register_attendance(registration)
        
        # Invalidate relevant cache entries on successful registration
        if result.success:
            cache_service.delete(CacheKeys.TODAY_ATTENDANCE)
            cache_service.delete(CacheKeys.attendance_count(result.current_count))
            # Invalidate attendance history cache pattern
            from ..services.cache_service import invalidate_cache_pattern
            invalidate_cache_pattern("attendance:history")
        
        if not result.success:
            # Return appropriate HTTP status for different failure types
            if "already registered" in result.message.lower():
                raise HTTPException(status_code=409, detail=result.message)
            elif "invalid session" in result.message.lower():
                raise HTTPException(status_code=404, detail=result.message)
            else:
                raise HTTPException(status_code=400, detail=result.message)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing registration: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process registration")

@router.get("/attendance/today", response_model=dict)
@limiter.limit("100/minute")  # Rate limit: 100 requests per minute per IP
async def get_today_attendance(request: Request, db: Session = Depends(get_db)):
    """
    Get current day attendance count with caching
    Requirements: 3.1 - Display current day attendance count
    """
    try:
        # Try to get from cache first
        cached_result = cache_service.get(CacheKeys.TODAY_ATTENDANCE)
        if cached_result is not None:
            return cached_result
        
        registration_service = RegistrationService(db)
        result = registration_service.get_today_attendance_count()
        
        # Cache the result for 60 seconds (frequent updates expected)
        cache_service.set(CacheKeys.TODAY_ATTENDANCE, result, ttl=60)
        
        return result
    except Exception as e:
        logger.error(f"Error retrieving today's attendance: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve attendance count")

@router.get("/attendance/history", response_model=dict)
@limiter.limit("60/minute")  # Rate limit: 60 requests per minute per IP
async def get_attendance_history(
    request: Request,
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(50, ge=1, le=1000, description="Number of records per page"),
    db: Session = Depends(get_db)
):
    """
    Get historical attendance data with pagination support and caching
    Requirements: 3.3 - Display attendance records for previous runs
    Requirements: 6.3 - Export data within specified date range
    Task 8: Add pagination support for large attendance datasets using FastAPI Query parameters
    """
    try:
        # Generate cache key for this specific query
        cache_key = CacheKeys.attendance_history(
            start_date or "all", 
            end_date or "all", 
            page
        )
        
        # Try to get from cache first
        cached_result = cache_service.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        registration_service = RegistrationService(db)
        result = registration_service.get_attendance_history(start_date, end_date, page, page_size)
        
        # Cache the result for 5 minutes (historical data changes less frequently)
        cache_service.set(cache_key, result, ttl=300)
        
        return result
    except Exception as e:
        logger.error(f"Error retrieving attendance history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve attendance history")

@router.get("/attendance/export")
@limiter.limit("5/minute")  # Rate limit: 5 exports per minute per IP (resource intensive)
async def export_attendance_data(
    request: Request,
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
    db: Session = Depends(get_db)
):
    """
    Export attendance data in CSV format with rate limiting
    Requirements: 6.1, 6.2 - Provide data in CSV format with names, dates, timestamps
    Requirements: 6.3 - Export data within specified date range
    Requirements: 6.4 - Provide empty export with headers if no data
    Task 8: Implement GET /api/attendance/export endpoint with date range parameters and CSV response
    """
    try:
        logger.info(f"Exporting attendance data from {start_date} to {end_date}")
        
        registration_service = RegistrationService(db)
        
        # Generate CSV content
        csv_content = registration_service.export_attendance_csv(start_date, end_date)
        
        # Generate appropriate filename
        filename = registration_service.get_attendance_export_filename(start_date, end_date)
        
        # Return CSV as downloadable file
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "text/csv; charset=utf-8"
            }
        )
        
    except Exception as e:
        logger.error(f"Error exporting attendance data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to export attendance data")