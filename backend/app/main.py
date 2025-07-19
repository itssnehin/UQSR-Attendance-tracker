"""
Main FastAPI application for Runner Attendance Tracker
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
from typing import Dict, Any

from .routes import calendar, registration, qr_code

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Runner Attendance Tracker API",
    description="API for tracking attendance at university social runs",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions with consistent error format"""
    logger.error(f"HTTP {exc.status_code}: {exc.detail} - {request.url}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors"""
    logger.error(f"Validation error: {exc.errors()} - {request.url}")
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "message": "Validation error",
            "details": exc.errors(),
            "status_code": 422
        }
    )

@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle 404 Not Found errors"""
    logger.error(f"404 Not Found: {request.url}")
    return JSONResponse(
        status_code=404,
        content={
            "error": True,
            "message": "Not Found",
            "status_code": 404
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {str(exc)} - {request.url}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Internal server error",
            "status_code": 500
        }
    )

# Health check endpoint
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Runner Attendance Tracker API",
        "version": "1.0.0"
    }

# Include routers
app.include_router(calendar.router, prefix="/api/calendar", tags=["calendar"])
app.include_router(registration.router, prefix="/api", tags=["registration"])
app.include_router(qr_code.router, prefix="/api/qr", tags=["qr-code"])

# Import and include attendance override router
from .routes import attendance_override
app.include_router(attendance_override.router, prefix="/api/attendance/override", tags=["attendance-override"])

# Root endpoint
@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint"""
    return {"message": "Runner Attendance Tracker API"}