"""
Caching service with in-memory and optional Redis support for performance optimization
"""
import json
import time
import threading
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
from functools import wraps
import logging
import os

logger = logging.getLogger(__name__)

# Try to import Redis, fall back to in-memory if not available
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using in-memory cache only")


class InMemoryCache:
    """Thread-safe in-memory cache implementation."""
    
    def __init__(self, default_ttl: int = 300):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self._lock = threading.RLock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "evictions": 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            if key not in self.cache:
                self._stats["misses"] += 1
                return None
            
            entry = self.cache[key]
            
            # Check if expired
            if entry["expires_at"] < time.time():
                del self.cache[key]
                self._stats["misses"] += 1
                self._stats["evictions"] += 1
                return None
            
            self._stats["hits"] += 1
            return entry["value"]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        with self._lock:
            ttl = ttl or self.default_ttl
            expires_at = time.time() + ttl
            
            self.cache[key] = {
                "value": value,
                "expires_at": expires_at,
                "created_at": time.time()
            }
            
            self._stats["sets"] += 1
            return True
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        with self._lock:
            if key in self.cache:
                del self.cache[key]
                self._stats["deletes"] += 1
                return True
            return False
    
    def clear(self) -> bool:
        """Clear all cache entries."""
        with self._lock:
            self.cache.clear()
            return True
    
    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        return self.get(key) is not None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = (self._stats["hits"] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                **self._stats,
                "total_requests": total_requests,
                "hit_rate_percent": round(hit_rate, 2),
                "cache_size": len(self.cache),
                "memory_usage_estimate": self._estimate_memory_usage()
            }
    
    def _estimate_memory_usage(self) -> int:
        """Estimate memory usage in bytes."""
        # Rough estimation
        total_size = 0
        for key, entry in self.cache.items():
            total_size += len(str(key)) + len(str(entry["value"])) + 64  # Overhead
        return total_size
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count of removed items."""
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, entry in self.cache.items()
                if entry["expires_at"] < current_time
            ]
            
            for key in expired_keys:
                del self.cache[key]
                self._stats["evictions"] += 1
            
            return len(expired_keys)


class RedisCache:
    """Redis cache implementation."""
    
    def __init__(self, redis_url: str, default_ttl: int = 300):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.default_ttl = default_ttl
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        try:
            value = self.redis_client.get(key)
            if value is None:
                self._stats["misses"] += 1
                return None
            
            self._stats["hits"] += 1
            return json.loads(value)
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            self._stats["errors"] += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Redis cache."""
        try:
            ttl = ttl or self.default_ttl
            serialized_value = json.dumps(value, default=str)
            result = self.redis_client.setex(key, ttl, serialized_value)
            
            if result:
                self._stats["sets"] += 1
            return result
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            self._stats["errors"] += 1
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from Redis cache."""
        try:
            result = self.redis_client.delete(key)
            if result:
                self._stats["deletes"] += 1
            return bool(result)
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            self._stats["errors"] += 1
            return False
    
    def clear(self) -> bool:
        """Clear all cache entries."""
        try:
            self.redis_client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            self._stats["errors"] += 1
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            self._stats["errors"] += 1
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            redis_info = self.redis_client.info()
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = (self._stats["hits"] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                **self._stats,
                "total_requests": total_requests,
                "hit_rate_percent": round(hit_rate, 2),
                "redis_memory_usage": redis_info.get("used_memory", 0),
                "redis_connected_clients": redis_info.get("connected_clients", 0),
                "redis_keyspace_hits": redis_info.get("keyspace_hits", 0),
                "redis_keyspace_misses": redis_info.get("keyspace_misses", 0)
            }
        except Exception as e:
            logger.error(f"Redis stats error: {e}")
            return self._stats


class CacheService:
    """Unified cache service with fallback support."""
    
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL")
        self.use_redis = REDIS_AVAILABLE and self.redis_url
        
        # Initialize cache backends
        self.memory_cache = InMemoryCache(default_ttl=300)
        
        if self.use_redis:
            try:
                self.redis_cache = RedisCache(self.redis_url, default_ttl=300)
                self.primary_cache = self.redis_cache
                self.fallback_cache = self.memory_cache
                logger.info("Cache service initialized with Redis primary and in-memory fallback")
            except Exception as e:
                logger.error(f"Failed to initialize Redis cache: {e}")
                self.use_redis = False
                self.primary_cache = self.memory_cache
                self.fallback_cache = None
                logger.info("Cache service initialized with in-memory cache only")
        else:
            self.primary_cache = self.memory_cache
            self.fallback_cache = None
            logger.info("Cache service initialized with in-memory cache only")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache with fallback support."""
        # Try primary cache first
        value = self.primary_cache.get(key)
        
        # If primary cache fails and we have fallback, try fallback
        if value is None and self.fallback_cache:
            value = self.fallback_cache.get(key)
        
        return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with fallback support."""
        primary_success = self.primary_cache.set(key, value, ttl)
        
        # Also set in fallback cache if available
        if self.fallback_cache:
            fallback_success = self.fallback_cache.set(key, value, ttl)
            return primary_success or fallback_success
        
        return primary_success
    
    def delete(self, key: str) -> bool:
        """Delete key from all caches."""
        primary_success = self.primary_cache.delete(key)
        
        if self.fallback_cache:
            fallback_success = self.fallback_cache.delete(key)
            return primary_success or fallback_success
        
        return primary_success
    
    def clear(self) -> bool:
        """Clear all caches."""
        primary_success = self.primary_cache.clear()
        
        if self.fallback_cache:
            fallback_success = self.fallback_cache.clear()
            return primary_success and fallback_success
        
        return primary_success
    
    def exists(self, key: str) -> bool:
        """Check if key exists in any cache."""
        return (self.primary_cache.exists(key) or 
                (self.fallback_cache and self.fallback_cache.exists(key)))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        stats = {
            "cache_type": "redis" if self.use_redis else "memory",
            "primary_cache": self.primary_cache.get_stats()
        }
        
        if self.fallback_cache:
            stats["fallback_cache"] = self.fallback_cache.get_stats()
        
        return stats
    
    def cleanup(self):
        """Cleanup expired entries from in-memory cache."""
        if hasattr(self.memory_cache, 'cleanup_expired'):
            expired_count = self.memory_cache.cleanup_expired()
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired cache entries")


# Global cache service instance
cache_service = CacheService()


# Cache decorators for common use cases
def cache_result(key_prefix: str, ttl: int = 300):
    """Decorator to cache function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache
            cached_result = cache_service.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_service.set(cache_key, result, ttl)
            logger.debug(f"Cache miss for {func.__name__}, result cached")
            
            return result
        return wrapper
    return decorator


def invalidate_cache_pattern(pattern: str):
    """Invalidate cache entries matching a pattern (in-memory only)."""
    if hasattr(cache_service.memory_cache, 'cache'):
        with cache_service.memory_cache._lock:
            keys_to_delete = [
                key for key in cache_service.memory_cache.cache.keys()
                if pattern in key
            ]
            
            for key in keys_to_delete:
                cache_service.delete(key)
            
            logger.info(f"Invalidated {len(keys_to_delete)} cache entries matching pattern: {pattern}")


# Specific cache keys for the attendance tracker
class CacheKeys:
    """Predefined cache keys for the attendance tracker."""
    
    TODAY_ATTENDANCE = "attendance:today"
    RUN_BY_SESSION = "run:session:{session_id}"
    CALENDAR_CONFIG = "calendar:config:{date}"
    ATTENDANCE_COUNT = "attendance:count:{run_id}"
    QR_CODE = "qr:code:{session_id}"
    ATTENDANCE_HISTORY = "attendance:history:{start_date}:{end_date}:{page}"
    
    @staticmethod
    def run_by_session(session_id: str) -> str:
        return f"run:session:{session_id}"
    
    @staticmethod
    def calendar_config(date: str) -> str:
        return f"calendar:config:{date}"
    
    @staticmethod
    def attendance_count(run_id: int) -> str:
        return f"attendance:count:{run_id}"
    
    @staticmethod
    def qr_code(session_id: str) -> str:
        return f"qr:code:{session_id}"
    
    @staticmethod
    def attendance_history(start_date: str, end_date: str, page: int) -> str:
        return f"attendance:history:{start_date}:{end_date}:{page}"


# Cache warming functions
def warm_cache():
    """Warm up cache with frequently accessed data."""
    try:
        from ..services.calendar_service import CalendarService
        from ..services.registration_service import RegistrationService
        from ..database.connection import db_manager
        
        with db_manager.transaction() as session:
            calendar_service = CalendarService(session)
            registration_service = RegistrationService(session)
            
            # Cache today's attendance
            today_attendance = registration_service.get_today_attendance_count()
            cache_service.set(CacheKeys.TODAY_ATTENDANCE, today_attendance, ttl=60)
            
            # Cache current calendar config
            today = datetime.now().date().isoformat()
            calendar_config = calendar_service.get_calendar_configuration()
            cache_service.set(CacheKeys.calendar_config(today), calendar_config, ttl=300)
            
            logger.info("Cache warmed with frequently accessed data")
            
    except Exception as e:
        logger.error(f"Cache warming failed: {e}")


# Background cache cleanup task
def schedule_cache_cleanup():
    """Schedule periodic cache cleanup."""
    import threading
    
    def cleanup_task():
        while True:
            try:
                cache_service.cleanup()
                time.sleep(300)  # Run every 5 minutes
            except Exception as e:
                logger.error(f"Cache cleanup task error: {e}")
                time.sleep(60)  # Retry after 1 minute on error
    
    cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
    cleanup_thread.start()
    logger.info("Cache cleanup task scheduled")