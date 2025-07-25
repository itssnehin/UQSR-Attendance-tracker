"""
Rate limiting middleware for FastAPI using slowapi
"""
import time
from typing import Dict, Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import logging
import redis
import os

logger = logging.getLogger(__name__)

# Redis configuration for distributed rate limiting (optional)
REDIS_URL = os.getenv("REDIS_URL")

# Initialize rate limiter
if REDIS_URL:
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        limiter = Limiter(
            key_func=get_remote_address,
            storage_uri=REDIS_URL,
            default_limits=["1000 per hour"]
        )
        logger.info("Rate limiter initialized with Redis backend")
    except Exception as e:
        logger.warning(f"Failed to connect to Redis, falling back to in-memory: {e}")
        limiter = Limiter(
            key_func=get_remote_address,
            default_limits=["1000 per hour"]
        )
else:
    # In-memory rate limiting
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["1000 per hour"]
    )
    logger.info("Rate limiter initialized with in-memory backend")


class RateLimitingMiddleware:
    """Custom rate limiting middleware with enhanced features."""
    
    def __init__(self):
        self.limiter = limiter
        self.request_counts: Dict[str, Dict[str, int]] = {}
        self.last_reset: Dict[str, float] = {}
    
    def get_client_identifier(self, request: Request) -> str:
        """Get client identifier for rate limiting."""
        # Try to get real IP from headers (for reverse proxy setups)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        return get_remote_address(request)
    
    def is_rate_limited(self, client_id: str, endpoint: str, limit: int, window: int) -> bool:
        """Check if client is rate limited for specific endpoint."""
        current_time = time.time()
        
        # Initialize tracking for client if not exists
        if client_id not in self.request_counts:
            self.request_counts[client_id] = {}
            self.last_reset[client_id] = current_time
        
        # Reset counts if window has passed
        if current_time - self.last_reset.get(client_id, 0) > window:
            self.request_counts[client_id] = {}
            self.last_reset[client_id] = current_time
        
        # Check current count for endpoint
        current_count = self.request_counts[client_id].get(endpoint, 0)
        
        if current_count >= limit:
            return True
        
        # Increment count
        self.request_counts[client_id][endpoint] = current_count + 1
        return False
    
    def get_rate_limit_info(self, client_id: str, endpoint: str, limit: int, window: int) -> Dict[str, int]:
        """Get rate limit information for client."""
        current_time = time.time()
        
        if client_id not in self.request_counts:
            return {
                "limit": limit,
                "remaining": limit,
                "reset_time": int(current_time + window)
            }
        
        current_count = self.request_counts[client_id].get(endpoint, 0)
        reset_time = int(self.last_reset.get(client_id, current_time) + window)
        
        return {
            "limit": limit,
            "remaining": max(0, limit - current_count),
            "reset_time": reset_time
        }


# Global middleware instance
rate_limiting_middleware = RateLimitingMiddleware()


# Rate limit decorators for different endpoints
def registration_rate_limit():
    """Rate limit for registration endpoints - 10 requests per minute per IP."""
    return limiter.limit("10/minute")


def qr_generation_rate_limit():
    """Rate limit for QR code generation - 30 requests per minute per IP."""
    return limiter.limit("30/minute")


def calendar_rate_limit():
    """Rate limit for calendar endpoints - 60 requests per minute per IP."""
    return limiter.limit("60/minute")


def export_rate_limit():
    """Rate limit for data export - 5 requests per minute per IP."""
    return limiter.limit("5/minute")


def general_api_rate_limit():
    """General API rate limit - 100 requests per minute per IP."""
    return limiter.limit("100/minute")


# Custom rate limit exceeded handler
def custom_rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded errors."""
    client_id = rate_limiting_middleware.get_client_identifier(request)
    
    logger.warning(f"Rate limit exceeded for client {client_id} on {request.url.path}")
    
    response = JSONResponse(
        status_code=429,
        content={
            "error": True,
            "message": "Rate limit exceeded. Please try again later.",
            "status_code": 429,
            "retry_after": exc.retry_after,
            "detail": str(exc.detail)
        }
    )
    
    # Add rate limit headers
    response.headers["X-RateLimit-Limit"] = str(exc.detail.split("/")[0])
    response.headers["X-RateLimit-Remaining"] = "0"
    response.headers["X-RateLimit-Reset"] = str(int(time.time() + exc.retry_after))
    response.headers["Retry-After"] = str(exc.retry_after)
    
    return response


# Peak load rate limiting for high-traffic scenarios
class PeakLoadRateLimiter:
    """Enhanced rate limiter for peak load scenarios."""
    
    def __init__(self):
        self.peak_mode = False
        self.peak_limits = {
            "registration": {"limit": 5, "window": 60},  # 5 per minute during peak
            "qr_generation": {"limit": 10, "window": 60},  # 10 per minute during peak
            "general": {"limit": 30, "window": 60}  # 30 per minute during peak
        }
        self.normal_limits = {
            "registration": {"limit": 10, "window": 60},
            "qr_generation": {"limit": 30, "window": 60},
            "general": {"limit": 100, "window": 60}
        }
    
    def enable_peak_mode(self):
        """Enable peak load rate limiting."""
        self.peak_mode = True
        logger.info("Peak load rate limiting enabled")
    
    def disable_peak_mode(self):
        """Disable peak load rate limiting."""
        self.peak_mode = False
        logger.info("Peak load rate limiting disabled")
    
    def get_limits(self, endpoint_type: str) -> Dict[str, int]:
        """Get rate limits based on current mode."""
        limits = self.peak_limits if self.peak_mode else self.normal_limits
        return limits.get(endpoint_type, limits["general"])


# Global peak load limiter
peak_load_limiter = PeakLoadRateLimiter()


# Middleware setup function
def setup_rate_limiting_middleware(app):
    """Setup rate limiting middleware for FastAPI app."""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, custom_rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    
    logger.info("Rate limiting middleware configured")
    
    return app