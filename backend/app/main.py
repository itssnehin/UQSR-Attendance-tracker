"""
Main FastAPI application for Runner Attendance Tracker with Performance Optimizations
"""
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
from typing import Dict, Any
import asyncio
import atexit

from .routes import calendar, registration, qr_code
from .services.websocket_service import websocket_service
from .middleware.rate_limiting import setup_rate_limiting_middleware, limiter
from .middleware.monitoring_middleware import setup_monitoring_middleware
from .services.cache_service import cache_service, schedule_cache_cleanup, warm_cache
from .services.monitoring_service import monitoring_service
from .database.connection import db_manager
from .database.optimization import initialize_optimizer
from .logging_config import setup_production_logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Runner Attendance Tracker API",
    description="API for tracking attendance at university social runs with performance optimizations",
    version="1.0.0"
)

# Setup production logging if in production environment
import os
if os.getenv('ENVIRONMENT') == 'production':
    logging_config = setup_production_logging()
    logger.info(f"Production logging configured: {logging_config}")

# Setup rate limiting middleware
app = setup_rate_limiting_middleware(app)

# Setup monitoring middleware
app = setup_monitoring_middleware(app)

# CORS middleware configuration
default_origins = [
    "http://localhost:3000",
    "http://localhost:3001", 
    "https://srcatttrackerbeta.vercel.app",
    "https://srcatttrackerbeta-*.vercel.app",
    "https://*.vercel.app",
    "https://srcatttrackerbeta-np15pmt84-itssnehins-projects.vercel.app",
    "https://srcatttrackerbeta-ars678kvf-itssnehins-projects.vercel.app",
    "https://srcatttrackerbeta-yhg2lz99t-itssnehins-projects.vercel.app"
]

# Get allowed origins from environment or use defaults
env_origins = os.getenv('ALLOWED_ORIGINS', '')
if env_origins:
    allowed_origins = env_origins.split(',')
else:
    allowed_origins = default_origins

# Add wildcard for development
if os.getenv('ENVIRONMENT') != 'production':
    allowed_origins.append('*')

logger.info(f"CORS allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
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

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize performance optimizations on startup."""
    try:
        # Initialize database optimizer
        optimizer = initialize_optimizer(db_manager.engine)
        
        # Create performance indexes
        with db_manager.transaction() as session:
            optimizer.create_performance_indexes(session)
        
        # Schedule cache cleanup
        schedule_cache_cleanup()
        
        # Warm up cache with frequently accessed data
        warm_cache()
        
        # Schedule monitoring cleanup (daily)
        import asyncio
        async def cleanup_monitoring_data():
            while True:
                await asyncio.sleep(24 * 60 * 60)  # 24 hours
                try:
                    monitoring_service.cleanup_old_metrics()
                except Exception as e:
                    logger.error(f"Failed to cleanup monitoring data: {e}")
        
        asyncio.create_task(cleanup_monitoring_data())
        
        logger.info("Performance optimizations and monitoring initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize performance optimizations: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    try:
        # Close database connections
        db_manager.close_all_connections()
        
        # Clear cache
        cache_service.clear()
        
        logger.info("Application shutdown completed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Enhanced health check endpoint with performance metrics
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Enhanced health check endpoint with performance metrics"""
    try:
        # Basic health check
        db_healthy = db_manager.check_health()
        
        # Get performance metrics
        pool_status = db_manager.get_pool_status()
        cache_stats = cache_service.get_stats()
        session_stats = db_manager.get_session_stats()
        
        return {
            "status": "healthy" if db_healthy else "unhealthy",
            "service": "Runner Attendance Tracker API",
            "version": "1.0.0",
            "database": {
                "healthy": db_healthy,
                "pool_status": pool_status,
                "session_stats": session_stats
            },
            "cache": cache_stats,
            "timestamp": asyncio.get_event_loop().time()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "Runner Attendance Tracker API",
            "version": "1.0.0",
            "error": str(e)
        }


# Performance monitoring endpoint
@app.get("/api/performance/stats")
async def performance_stats() -> Dict[str, Any]:
    """Get detailed performance statistics"""
    try:
        return {
            "database": {
                "pool_status": db_manager.get_pool_status(),
                "session_stats": db_manager.get_session_stats()
            },
            "cache": cache_service.get_stats(),
            "rate_limiting": {
                "limiter_stats": "Rate limiting active"
            }
        }
    except Exception as e:
        logger.error(f"Failed to get performance stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve performance statistics")

# Comprehensive monitoring endpoint
@app.get("/api/monitoring/health")
async def monitoring_health() -> Dict[str, Any]:
    """Get comprehensive health and monitoring status"""
    try:
        return monitoring_service.get_health_status()
    except Exception as e:
        logger.error(f"Failed to get monitoring health: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve monitoring health status")

# System metrics endpoint
@app.get("/api/monitoring/metrics")
async def system_metrics() -> Dict[str, Any]:
    """Get current system metrics"""
    try:
        return {
            "system": monitoring_service.get_system_metrics(),
            "database": monitoring_service.get_database_metrics(),
            "application": monitoring_service.get_application_metrics()
        }
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system metrics")

# Include routers
app.include_router(calendar.router, prefix="/api/calendar", tags=["calendar"])
app.include_router(registration.router, prefix="/api", tags=["registration"])
app.include_router(qr_code.router, prefix="/api/qr", tags=["qr-code"])

# Import and include attendance override router
from .routes import attendance_override
app.include_router(attendance_override.router, prefix="/api/attendance/override", tags=["attendance-override"])

# WebSocket status endpoint
@app.get("/api/websocket/status")
async def websocket_status() -> Dict[str, Any]:
    """Get WebSocket connection status and statistics"""
    return websocket_service.get_connection_stats()

# Mount Socket.IO app
socket_app = websocket_service.get_socketio_app()
app.mount("/socket.io", socket_app)

# Root endpoint
@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint"""
    return {"message": "Runner Attendance Tracker API"}