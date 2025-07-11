"""
Advanced API Request Optimization Middleware
Request/Response optimization, rate limiting, and performance monitoring
"""

import asyncio
import time
import json
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from collections import defaultdict, deque
from dataclasses import dataclass

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

from app.core.logger import get_logger
from app.core.redis_client import redis_client
from app.core.api_optimizer import api_optimizer

logger = get_logger(__name__)

@dataclass
class RequestMetrics:
    """Request processing metrics"""
    path: str
    method: str
    processing_time: float
    queue_time: float
    response_size: int
    status_code: int
    timestamp: datetime
    user_id: Optional[str] = None

class RequestQueue:
    """Smart request queue for load balancing"""
    
    def __init__(self, max_concurrent: int = 100, max_queue_size: int = 1000):
        self.max_concurrent = max_concurrent
        self.max_queue_size = max_queue_size
        self.active_requests = 0
        self.queue = asyncio.Queue(maxsize=max_queue_size)
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        # Priority queues
        self.high_priority_queue = asyncio.Queue()
        self.normal_priority_queue = asyncio.Queue()
        self.low_priority_queue = asyncio.Queue()
        
        # Queue processor
        self._processor_task = asyncio.create_task(self._process_queues())
    
    async def _process_queues(self):
        """Process requests from priority queues"""
        while True:
            try:
                # Process high priority first
                if not self.high_priority_queue.empty():
                    request_data = await self.high_priority_queue.get()
                    await self._execute_request(request_data)
                elif not self.normal_priority_queue.empty():
                    request_data = await self.normal_priority_queue.get()
                    await self._execute_request(request_data)
                elif not self.low_priority_queue.empty():
                    request_data = await self.low_priority_queue.get()
                    await self._execute_request(request_data)
                else:
                    await asyncio.sleep(0.01)  # Short sleep to prevent busy waiting
                    
            except Exception as e:
                logger.error(f"Queue processor error: {e}")
    
    async def _execute_request(self, request_data: Dict[str, Any]):
        """Execute queued request"""
        try:
            async with self.semaphore:
                self.active_requests += 1
                future = request_data["future"]
                handler = request_data["handler"]
                args = request_data["args"]
                
                result = await handler(*args)
                future.set_result(result)
                
        except Exception as e:
            request_data["future"].set_exception(e)
        finally:
            self.active_requests -= 1
    
    async def enqueue_request(self, handler: Callable, args: tuple, 
                            priority: str = "normal") -> Any:
        """Enqueue request with priority"""
        future = asyncio.Future()
        request_data = {
            "handler": handler,
            "args": args,
            "future": future,
            "enqueued_at": time.time()
        }
        
        # Select appropriate queue
        if priority == "high":
            await self.high_priority_queue.put(request_data)
        elif priority == "low":
            await self.low_priority_queue.put(request_data)
        else:
            await self.normal_priority_queue.put(request_data)
        
        return await future
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        return {
            "active_requests": self.active_requests,
            "high_priority_queued": self.high_priority_queue.qsize(),
            "normal_priority_queued": self.normal_priority_queue.qsize(),
            "low_priority_queued": self.low_priority_queue.qsize(),
            "total_queued": (
                self.high_priority_queue.qsize() + 
                self.normal_priority_queue.qsize() + 
                self.low_priority_queue.qsize()
            ),
            "semaphore_available": self.semaphore._value
        }

class AdaptiveRateLimiter:
    """Adaptive rate limiting based on system load"""
    
    def __init__(self, base_limit: int = 100, window_seconds: int = 60):
        self.base_limit = base_limit
        self.window_seconds = window_seconds
        self.request_counts = defaultdict(lambda: deque())
        self.user_limits = defaultdict(lambda: base_limit)
        
        # System load tracking
        self.system_load = 0.0
        self.last_load_check = time.time()
        
    async def is_allowed(self, identifier: str, 
                        request_type: str = "api") -> tuple[bool, Dict[str, Any]]:
        """Check if request is allowed"""
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        self.request_counts[identifier] = deque([
            timestamp for timestamp in self.request_counts[identifier]
            if timestamp > window_start
        ])
        
        current_count = len(self.request_counts[identifier])
        
        # Adaptive limit based on system load
        adaptive_limit = await self._calculate_adaptive_limit(identifier, request_type)
        
        rate_limit_info = {
            "limit": adaptive_limit,
            "remaining": max(0, adaptive_limit - current_count),
            "reset_time": int(now + self.window_seconds),
            "retry_after": None
        }
        
        if current_count >= adaptive_limit:
            rate_limit_info["retry_after"] = self.window_seconds
            return False, rate_limit_info
        
        # Record request
        self.request_counts[identifier].append(now)
        return True, rate_limit_info
    
    async def _calculate_adaptive_limit(self, identifier: str, 
                                      request_type: str) -> int:
        """Calculate adaptive rate limit based on system conditions"""
        base_limit = self.user_limits[identifier]
        
        # Update system load
        await self._update_system_load()
        
        # Adjust limit based on system load
        if self.system_load > 0.8:  # High load
            return int(base_limit * 0.5)
        elif self.system_load > 0.6:  # Medium load
            return int(base_limit * 0.7)
        elif self.system_load < 0.3:  # Low load
            return int(base_limit * 1.2)
        else:
            return base_limit
    
    async def _update_system_load(self):
        """Update system load metrics"""
        now = time.time()
        if now - self.last_load_check > 10:  # Update every 10 seconds
            try:
                # Get queue stats from request queue
                queue_stats = request_queue.get_queue_stats()
                active_ratio = queue_stats["active_requests"] / request_queue.max_concurrent
                queue_ratio = queue_stats["total_queued"] / request_queue.max_queue_size
                
                self.system_load = (active_ratio + queue_ratio) / 2
                self.last_load_check = now
                
            except Exception as e:
                logger.error(f"System load update failed: {e}")

class RequestOptimizationMiddleware(BaseHTTPMiddleware):
    """Comprehensive request optimization middleware"""
    
    def __init__(self, app):
        super().__init__(app)
        self.rate_limiter = AdaptiveRateLimiter()
        self.metrics: deque = deque(maxlen=10000)
        
        # Request deduplication
        self.pending_requests: Dict[str, asyncio.Future] = {}
        
        # Response compression thresholds
        self.compression_threshold = 1024  # 1KB
        
    async def dispatch(self, request: Request, call_next):
        """Optimize request processing"""
        start_time = time.time()
        queue_start = time.time()
        
        try:
            # Generate request ID
            request_id = hashlib.md5(
                f"{time.time()}:{request.url}:{id(request)}".encode()
            ).hexdigest()[:8]
            
            # Add request ID to headers
            request.headers.__dict__['_list'].append(
                (b'x-request-id', request_id.encode())
            )
            
            # Rate limiting
            client_ip = self._get_client_ip(request)
            allowed, rate_info = await self.rate_limiter.is_allowed(client_ip)
            
            if not allowed:
                return self._create_rate_limit_response(rate_info)
            
            # Request deduplication for idempotent requests
            if request.method in ["GET", "HEAD", "OPTIONS"]:
                dedup_key = self._generate_dedup_key(request)
                if dedup_key in self.pending_requests:
                    # Wait for existing request
                    try:
                        return await self.pending_requests[dedup_key]
                    except Exception:
                        pass  # Continue with new request if original failed
            
            # Queue request based on priority
            priority = self._determine_request_priority(request)
            
            queue_end = time.time()
            queue_time = queue_end - queue_start
            
            # Process request
            if dedup_key and request.method in ["GET", "HEAD", "OPTIONS"]:
                future = asyncio.Future()
                self.pending_requests[dedup_key] = future
                
                try:
                    response = await request_queue.enqueue_request(
                        call_next, (request,), priority
                    )
                    future.set_result(response)
                    
                    # Clean up
                    if dedup_key in self.pending_requests:
                        del self.pending_requests[dedup_key]
                    
                except Exception as e:
                    future.set_exception(e)
                    if dedup_key in self.pending_requests:
                        del self.pending_requests[dedup_key]
                    raise
            else:
                response = await request_queue.enqueue_request(
                    call_next, (request,), priority
                )
            
            # Add optimization headers
            response = await self._add_optimization_headers(
                request, response, rate_info
            )
            
            # Record metrics
            processing_time = time.time() - start_time
            await self._record_metrics(
                request, response, processing_time, queue_time
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Request optimization error: {e}")
            return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check X-Forwarded-For header
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct connection
        return request.client.host
    
    def _determine_request_priority(self, request: Request) -> str:
        """Determine request priority"""
        # High priority for auth and critical endpoints
        if request.url.path.startswith(("/api/v1/auth", "/api/v1/health")):
            return "high"
        
        # Low priority for analytics and reporting
        if request.url.path.startswith(("/api/v1/analytics", "/api/v1/reports")):
            return "low"
        
        # Check user priority (premium users get higher priority)
        user_tier = request.headers.get("X-User-Tier", "standard")
        if user_tier == "premium":
            return "high"
        
        return "normal"
    
    def _generate_dedup_key(self, request: Request) -> str:
        """Generate deduplication key for request"""
        key_parts = [
            request.method,
            str(request.url),
            request.headers.get("authorization", "")[:20]
        ]
        
        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _create_rate_limit_response(self, rate_info: Dict[str, Any]) -> Response:
        """Create rate limit exceeded response"""
        headers = {
            "X-RateLimit-Limit": str(rate_info["limit"]),
            "X-RateLimit-Remaining": str(rate_info["remaining"]),
            "X-RateLimit-Reset": str(rate_info["reset_time"]),
            "Retry-After": str(rate_info["retry_after"])
        }
        
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Try again in {rate_info['retry_after']} seconds.",
                "rate_limit": rate_info
            },
            headers=headers
        )
    
    async def _add_optimization_headers(self, request: Request, 
                                      response: Response,
                                      rate_info: Dict[str, Any]) -> Response:
        """Add optimization and performance headers"""
        # Rate limiting headers
        response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(rate_info["reset_time"])
        
        # Request ID
        request_id = request.headers.get("X-Request-ID", "unknown")
        response.headers["X-Request-ID"] = request_id
        
        # Performance headers
        queue_stats = request_queue.get_queue_stats()
        response.headers["X-Queue-Length"] = str(queue_stats["total_queued"])
        response.headers["X-Active-Requests"] = str(queue_stats["active_requests"])
        
        # Cache headers for GET requests
        if request.method == "GET" and response.status_code == 200:
            response.headers["Cache-Control"] = "public, max-age=300"
            
            # Generate ETag for response
            if hasattr(response, 'body'):
                content_hash = hashlib.md5(response.body).hexdigest()[:16]
                response.headers["ETag"] = f'"{content_hash}"'
        
        return response
    
    async def _record_metrics(self, request: Request, response: Response,
                            processing_time: float, queue_time: float):
        """Record request metrics"""
        try:
            response_size = 0
            if hasattr(response, 'headers') and 'content-length' in response.headers:
                response_size = int(response.headers['content-length'])
            
            metric = RequestMetrics(
                path=request.url.path,
                method=request.method,
                processing_time=processing_time,
                queue_time=queue_time,
                response_size=response_size,
                status_code=response.status_code,
                timestamp=datetime.utcnow(),
                user_id=request.headers.get("X-User-ID")
            )
            
            self.metrics.append(metric)
            
            # Store in Redis for persistence
            await self._store_metrics_in_redis(metric)
            
        except Exception as e:
            logger.error(f"Metrics recording failed: {e}")
    
    async def _store_metrics_in_redis(self, metric: RequestMetrics):
        """Store metrics in Redis"""
        try:
            key = f"request_metrics:{datetime.utcnow().strftime('%Y%m%d')}:{metric.path.replace('/', '_')}"
            metric_data = {
                "path": metric.path,
                "method": metric.method,
                "processing_time": metric.processing_time,
                "queue_time": metric.queue_time,
                "response_size": metric.response_size,
                "status_code": metric.status_code,
                "timestamp": metric.timestamp.isoformat(),
                "user_id": metric.user_id
            }
            
            await redis_client.lpush(key, json.dumps(metric_data))
            await redis_client.expire(key, 86400 * 7)  # Keep for 7 days
            
        except Exception as e:
            logger.error(f"Redis metrics storage failed: {e}")
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics"""
        recent_metrics = [
            m for m in self.metrics 
            if m.timestamp > datetime.utcnow() - timedelta(minutes=5)
        ]
        
        if not recent_metrics:
            return {"message": "No recent metrics available"}
        
        total_processing_time = sum(m.processing_time for m in recent_metrics)
        total_queue_time = sum(m.queue_time for m in recent_metrics)
        avg_processing_time = total_processing_time / len(recent_metrics)
        avg_queue_time = total_queue_time / len(recent_metrics)
        
        status_codes = defaultdict(int)
        for metric in recent_metrics:
            status_codes[metric.status_code] += 1
        
        return {
            "recent_requests": len(recent_metrics),
            "avg_processing_time_ms": round(avg_processing_time * 1000, 2),
            "avg_queue_time_ms": round(avg_queue_time * 1000, 2),
            "status_code_distribution": dict(status_codes),
            "queue_stats": request_queue.get_queue_stats(),
            "rate_limiter_active_users": len(self.rate_limiter.request_counts),
            "deduplication_active": len(self.pending_requests)
        }

# Global instances
request_queue = RequestQueue(
    max_concurrent=getattr(settings, 'MAX_CONCURRENT_REQUESTS', 100),
    max_queue_size=getattr(settings, 'MAX_QUEUE_SIZE', 1000)
)

request_optimization_middleware = RequestOptimizationMiddleware

# Utility functions
async def get_system_performance_stats() -> Dict[str, Any]:
    """Get comprehensive system performance statistics"""
    try:
        # Combine stats from various components
        middleware_stats = {}
        
        # This would be called from an instance of the middleware
        # For now, return basic queue stats
        queue_stats = request_queue.get_queue_stats()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "queue_performance": queue_stats,
            "system_load": getattr(request_queue, 'system_load', 0.0)
        }
        
    except Exception as e:
        logger.error(f"Performance stats retrieval failed: {e}")
        return {"error": str(e)}

async def optimize_api_endpoint(endpoint_path: str, 
                              optimization_config: Dict[str, Any]) -> bool:
    """Optimize specific API endpoint"""
    try:
        # This would configure specific optimizations for an endpoint
        logger.info(f"Applying optimizations to {endpoint_path}: {optimization_config}")
        
        # Store optimization config in Redis
        await redis_client.setex(
            f"endpoint_optimization:{endpoint_path}",
            3600,  # 1 hour
            json.dumps(optimization_config)
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Endpoint optimization failed: {e}")
        return False