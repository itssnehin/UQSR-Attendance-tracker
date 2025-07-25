"""
Monitoring middleware for production request tracking
"""
import time
import uuid
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from ..services.monitoring_service import monitoring_service
from ..logging_config import get_request_logger

logger = logging.getLogger(__name__)

class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware to monitor requests and log performance metrics"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Get client info
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Create request logger with context
        request_logger = get_request_logger(
            request_id=request_id,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        # Log request start
        request_logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                'endpoint': request.url.path,
                'method': request.method,
                'query_params': str(request.query_params) if request.query_params else None
            }
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Log request completion
            request_logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                extra={
                    'endpoint': request.url.path,
                    'method': request.method,
                    'status_code': response.status_code,
                    'response_time': response_time
                }
            )
            
            # Record metrics
            monitoring_service.record_request_metrics(
                endpoint=request.url.path,
                method=request.method,
                status_code=response.status_code,
                response_time=response_time
            )
            
            # Add response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{response_time:.3f}s"
            
            return response
            
        except Exception as e:
            # Calculate response time for error case
            response_time = time.time() - start_time
            
            # Log error
            request_logger.error(
                f"Request failed: {request.method} {request.url.path} - {str(e)}",
                extra={
                    'endpoint': request.url.path,
                    'method': request.method,
                    'response_time': response_time,
                    'error': str(e)
                },
                exc_info=True
            )
            
            # Record error metrics
            monitoring_service.record_request_metrics(
                endpoint=request.url.path,
                method=request.method,
                status_code=500,
                response_time=response_time
            )
            
            # Re-raise the exception
            raise

def setup_monitoring_middleware(app):
    """Set up monitoring middleware on FastAPI app"""
    app.add_middleware(MonitoringMiddleware)
    logger.info("Monitoring middleware configured")
    return app