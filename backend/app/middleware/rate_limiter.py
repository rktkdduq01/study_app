from typing import Dict, Optional, Tuple
import time
import redis
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
import asyncio

from app.core.config import settings


class RateLimiter:
    """Rate limiter implementation using token bucket algorithm"""
    
    def __init__(
        self,
        redis_client: Optional[redis.StrictRedis] = None,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_size: int = 10
    ):
        self.redis_client = redis_client
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_size = burst_size
        
        # Fallback to in-memory storage if Redis not available
        self.memory_storage: Dict[str, Dict[str, any]] = defaultdict(dict)
        self.cleanup_task = None
    
    async def _get_redis_key(self, identifier: str, window: str) -> str:
        """Generate Redis key for rate limiting"""
        return f"rate_limit:{identifier}:{window}"
    
    async def _check_redis_limit(
        self,
        identifier: str,
        limit: int,
        window_seconds: int,
        window_name: str
    ) -> Tuple[bool, dict]:
        """Check rate limit using Redis"""
        if not self.redis_client:
            return await self._check_memory_limit(identifier, limit, window_seconds, window_name)
        
        try:
            key = await self._get_redis_key(identifier, window_name)
            current_time = int(time.time())
            window_start = current_time - window_seconds
            
            # Use Redis sorted set for sliding window
            pipeline = self.redis_client.pipeline()
            
            # Remove old entries
            pipeline.zremrangebyscore(key, 0, window_start)
            
            # Count requests in current window
            pipeline.zcard(key)
            
            # Add current request
            pipeline.zadd(key, {str(current_time): current_time})
            
            # Set expiry
            pipeline.expire(key, window_seconds)
            
            results = pipeline.execute()
            request_count = results[1]
            
            if request_count >= limit:
                return False, {
                    "limit": limit,
                    "remaining": 0,
                    "reset": current_time + window_seconds
                }
            
            return True, {
                "limit": limit,
                "remaining": limit - request_count - 1,
                "reset": current_time + window_seconds
            }
            
        except Exception:
            # Fallback to memory if Redis fails
            return await self._check_memory_limit(identifier, limit, window_seconds, window_name)
    
    async def _check_memory_limit(
        self,
        identifier: str,
        limit: int,
        window_seconds: int,
        window_name: str
    ) -> Tuple[bool, dict]:
        """Check rate limit using in-memory storage"""
        current_time = time.time()
        window_key = f"{identifier}:{window_name}"
        
        if window_key not in self.memory_storage:
            self.memory_storage[window_key] = {
                "requests": [],
                "tokens": self.burst_size
            }
        
        storage = self.memory_storage[window_key]
        window_start = current_time - window_seconds
        
        # Remove old requests
        storage["requests"] = [
            req_time for req_time in storage["requests"]
            if req_time > window_start
        ]
        
        # Check if under limit
        if len(storage["requests"]) >= limit:
            return False, {
                "limit": limit,
                "remaining": 0,
                "reset": int(current_time + window_seconds)
            }
        
        # Add current request
        storage["requests"].append(current_time)
        
        return True, {
            "limit": limit,
            "remaining": limit - len(storage["requests"]),
            "reset": int(current_time + window_seconds)
        }
    
    async def check_rate_limit(
        self,
        identifier: str,
        is_authenticated: bool = False
    ) -> Tuple[bool, dict]:
        """Check if request is within rate limits"""
        # Different limits for authenticated vs anonymous users
        if is_authenticated:
            minute_limit = self.requests_per_minute * 2  # Double for authenticated
            hour_limit = self.requests_per_hour * 2
        else:
            minute_limit = self.requests_per_minute
            hour_limit = self.requests_per_hour
        
        # Check minute limit
        minute_allowed, minute_info = await self._check_redis_limit(
            identifier, minute_limit, 60, "minute"
        )
        
        if not minute_allowed:
            return False, minute_info
        
        # Check hour limit
        hour_allowed, hour_info = await self._check_redis_limit(
            identifier, hour_limit, 3600, "hour"
        )
        
        return hour_allowed, hour_info
    
    async def cleanup_memory_storage(self):
        """Periodically clean up old entries from memory storage"""
        while True:
            await asyncio.sleep(300)  # Clean up every 5 minutes
            current_time = time.time()
            
            keys_to_delete = []
            for key, storage in self.memory_storage.items():
                # Remove entries older than 1 hour
                storage["requests"] = [
                    req_time for req_time in storage["requests"]
                    if req_time > current_time - 3600
                ]
                
                # Delete empty entries
                if not storage["requests"]:
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                del self.memory_storage[key]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware for FastAPI"""
    
    def __init__(self, app, **kwargs):
        super().__init__(app)
        
        # Initialize Redis client
        try:
            self.redis_client = redis.StrictRedis(
                host=settings.REDIS_HOST if hasattr(settings, 'REDIS_HOST') else "localhost",
                port=settings.REDIS_PORT if hasattr(settings, 'REDIS_PORT') else 6379,
                db=settings.REDIS_DB if hasattr(settings, 'REDIS_DB') else 1,
                decode_responses=True
            )
            self.redis_client.ping()
        except:
            self.redis_client = None
        
        # Initialize rate limiter
        self.rate_limiter = RateLimiter(
            redis_client=self.redis_client,
            requests_per_minute=kwargs.get('requests_per_minute', 60),
            requests_per_hour=kwargs.get('requests_per_hour', 1000),
            burst_size=kwargs.get('burst_size', 10)
        )
        
        # Paths to exclude from rate limiting
        self.exclude_paths = kwargs.get('exclude_paths', [
            "/docs",
            "/openapi.json",
            "/health",
            "/metrics"
        ])
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Get client identifier
        client_ip = request.client.host
        identifier = client_ip
        
        # Check if user is authenticated
        is_authenticated = False
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            is_authenticated = True
            # Use user ID as identifier if possible
            # This would require decoding the token, which we skip for performance
            identifier = f"auth:{client_ip}"
        
        # Check rate limit
        allowed, limit_info = await self.rate_limiter.check_rate_limit(
            identifier, is_authenticated
        )
        
        # Add rate limit headers
        response = Response(
            content="",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )
        response.headers["X-RateLimit-Limit"] = str(limit_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(limit_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(limit_info["reset"])
        response.headers["Retry-After"] = str(
            limit_info["reset"] - int(time.time())
        )
        
        if not allowed:
            response.content = b"Rate limit exceeded. Please try again later."
            return response
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to successful response
        response.headers["X-RateLimit-Limit"] = str(limit_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(limit_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(limit_info["reset"])
        
        return response


def create_rate_limit_decorator(
    requests_per_minute: int = 60,
    requests_per_hour: int = 1000,
    key_func: Optional[callable] = None
):
    """Create a rate limit decorator for specific endpoints"""
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            # Get identifier
            if key_func:
                identifier = key_func(request, *args, **kwargs)
            else:
                identifier = request.client.host
            
            # Initialize rate limiter
            rate_limiter = RateLimiter(
                requests_per_minute=requests_per_minute,
                requests_per_hour=requests_per_hour
            )
            
            # Check rate limit
            allowed, limit_info = await rate_limiter.check_rate_limit(identifier)
            
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                    headers={
                        "X-RateLimit-Limit": str(limit_info["limit"]),
                        "X-RateLimit-Remaining": str(limit_info["remaining"]),
                        "X-RateLimit-Reset": str(limit_info["reset"]),
                        "Retry-After": str(limit_info["reset"] - int(time.time()))
                    }
                )
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator