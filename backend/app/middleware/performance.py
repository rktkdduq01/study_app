"""
Performance monitoring middleware for FastAPI
"""
import time
import psutil
import asyncio
from typing import Callable, Dict, Any, Optional
from datetime import datetime
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import prometheus_client
from prometheus_client import Counter, Histogram, Gauge
import json

from app.core.config import settings
from app.utils.logger import performance_logger


# Prometheus metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10)
)

active_requests = Gauge(
    'http_requests_active',
    'Number of active HTTP requests'
)

db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation', 'table']
)

cache_hit_rate = Counter(
    'cache_hits_total',
    'Cache hit/miss counter',
    ['cache_type', 'hit']
)

websocket_connections = Gauge(
    'websocket_connections_active',
    'Number of active WebSocket connections'
)

# System metrics
cpu_usage = Gauge('system_cpu_usage_percent', 'CPU usage percentage')
memory_usage = Gauge('system_memory_usage_percent', 'Memory usage percentage')
disk_usage = Gauge('system_disk_usage_percent', 'Disk usage percentage')


class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    Middleware for performance monitoring and metrics collection.
    
    Tracks:
    - Request duration and count
    - Response status codes
    - Slow requests (> threshold)
    - Memory and CPU usage
    - Active connections
    """
    
    def __init__(
        self,
        app: ASGIApp,
        slow_request_threshold: float = 1.0,
        enable_profiling: bool = False
    ):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold
        self.enable_profiling = enable_profiling
        
        # Start background system metrics collector
        if settings.ENABLE_METRICS:
            asyncio.create_task(self._collect_system_metrics())
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with performance monitoring"""
        # Skip metrics for health check
        if request.url.path == "/health":
            return await call_next(request)
        
        # Track active requests
        active_requests.inc()
        
        # Start timing
        start_time = time.time()
        
        # Get request details
        method = request.method
        path = request.url.path
        
        # Process size tracking
        request_size = int(request.headers.get('content-length', 0))
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Record metrics
            request_count.labels(
                method=method,
                endpoint=path,
                status=response.status_code
            ).inc()
            
            request_duration.labels(
                method=method,
                endpoint=path
            ).observe(duration)
            
            # Log slow requests
            if duration > self.slow_request_threshold:
                performance_logger.warning(
                    "Slow request detected",
                    path=path,
                    method=method,
                    duration=duration,
                    status=response.status_code,
                    threshold=self.slow_request_threshold
                )
            
            # Add performance headers
            response.headers["X-Request-Duration"] = f"{duration:.3f}"
            response.headers["X-Process-Time"] = f"{duration:.3f}"
            
            # Log request metrics
            performance_logger.info(
                "Request completed",
                path=path,
                method=method,
                duration=duration,
                status=response.status_code,
                request_size=request_size,
                response_size=response.headers.get('content-length', 0)
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Record error metrics
            request_count.labels(
                method=method,
                endpoint=path,
                status=500
            ).inc()
            
            performance_logger.error(
                "Request failed",
                path=path,
                method=method,
                duration=duration,
                error=str(e)
            )
            
            raise
            
        finally:
            active_requests.dec()
    
    async def _collect_system_metrics(self):
        """Collect system metrics periodically"""
        while True:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                cpu_usage.set(cpu_percent)
                
                # Memory usage
                memory = psutil.virtual_memory()
                memory_usage.set(memory.percent)
                
                # Disk usage
                disk = psutil.disk_usage('/')
                disk_usage.set(disk.percent)
                
                # Log if thresholds exceeded
                if cpu_percent > 80:
                    performance_logger.warning(
                        "High CPU usage detected",
                        cpu_percent=cpu_percent
                    )
                
                if memory.percent > 85:
                    performance_logger.warning(
                        "High memory usage detected",
                        memory_percent=memory.percent,
                        available_mb=memory.available / 1024 / 1024
                    )
                
                await asyncio.sleep(30)  # Collect every 30 seconds
                
            except Exception as e:
                performance_logger.error(
                    "Failed to collect system metrics",
                    error=str(e)
                )
                await asyncio.sleep(60)


class RequestTimingMiddleware:
    """
    Lightweight timing middleware for development.
    Adds timing information to response headers.
    """
    
    def __init__(self, app: ASGIApp):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                duration = time.time() - start_time
                headers = dict(message.get("headers", []))
                headers[b"x-response-time"] = f"{duration:.3f}s".encode()
                message["headers"] = list(headers.items())
            await send(message)
        
        await self.app(scope, receive, send_wrapper)


def track_db_query(operation: str, table: str):
    """
    Decorator to track database query performance.
    
    Usage:
        @track_db_query("select", "users")
        async def get_user(user_id: int):
            ...
    """
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Record metric
                db_query_duration.labels(
                    operation=operation,
                    table=table
                ).observe(duration)
                
                # Log slow queries
                if duration > 0.5:
                    performance_logger.warning(
                        "Slow database query",
                        operation=operation,
                        table=table,
                        duration=duration
                    )
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                performance_logger.error(
                    "Database query failed",
                    operation=operation,
                    table=table,
                    duration=duration,
                    error=str(e)
                )
                raise
        
        return wrapper
    return decorator


def track_cache_access(cache_type: str):
    """
    Decorator to track cache hit rates.
    
    Usage:
        @track_cache_access("user_profile")
        async def get_cached_user(user_id: int):
            ...
    """
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            # Determine if cache hit based on result
            is_hit = result is not None
            
            cache_hit_rate.labels(
                cache_type=cache_type,
                hit=str(is_hit)
            ).inc()
            
            return result
        
        return wrapper
    return decorator


class PerformanceProfiler:
    """
    Context manager for profiling code blocks.
    
    Usage:
        async with PerformanceProfiler("process_quest_submission") as profiler:
            # Code to profile
            pass
    """
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.start_memory = None
    
    async def __aenter__(self):
        self.start_time = time.time()
        self.start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_delta = end_memory - self.start_memory
        
        performance_logger.info(
            "Performance profile",
            operation=self.operation_name,
            duration=duration,
            memory_delta_mb=memory_delta,
            success=exc_type is None
        )
        
        # Alert on concerning metrics
        if duration > 5:
            performance_logger.warning(
                "Long-running operation",
                operation=self.operation_name,
                duration=duration
            )
        
        if memory_delta > 100:  # 100MB
            performance_logger.warning(
                "High memory usage",
                operation=self.operation_name,
                memory_delta_mb=memory_delta
            )


# Export Prometheus metrics endpoint
def get_metrics():
    """Get Prometheus metrics"""
    return prometheus_client.generate_latest()