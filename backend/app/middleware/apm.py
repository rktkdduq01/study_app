"""
APM Middleware
Application Performance Monitoring middleware for automatic metrics collection
"""

import time
import psutil
from datetime import datetime
from typing import Optional, Dict, Any
from urllib.parse import unquote

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

from app.core.logger import get_logger
from app.core.apm import apm_collector, record_endpoint_performance, performance_context
from app.core.distributed_tracing import distributed_tracer

logger = get_logger(__name__)

class APMMiddleware(BaseHTTPMiddleware):
    """APM middleware for automatic performance monitoring"""
    
    def __init__(self, app, enable_detailed_profiling: bool = True):
        super().__init__(app)
        self.enable_detailed_profiling = enable_detailed_profiling
        
        # Request tracking
        self.active_requests: Dict[str, Dict[str, Any]] = {}
        
        # Sampling configuration
        self.sampling_rate = 1.0  # Sample 100% of requests
        
        # Excluded paths for performance monitoring
        self.excluded_paths = [
            "/health",
            "/metrics",
            "/apm",
            "/static",
            "/favicon.ico"
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Process request with APM monitoring"""
        
        # Skip monitoring for excluded paths
        if self._should_exclude_path(request.url.path):
            return await call_next(request)
        
        # Apply sampling
        if not self._should_sample():
            return await call_next(request)
        
        request_id = self._get_request_id(request)
        start_time = time.time()
        
        # Record request start
        self._record_request_start(request, request_id, start_time)
        
        try:
            # Process request with performance monitoring
            async with performance_context(f"http_request_{request.method}_{request.url.path}") as span:
                
                # Add request metadata to span
                span.set_attribute("http.method", request.method)
                span.set_attribute("http.url", str(request.url))
                span.set_attribute("http.route", getattr(request, 'route', {}).get('path', ''))
                span.set_attribute("apm.request_id", request_id)
                
                # Get system metrics before request
                system_before = self._capture_system_snapshot()
                
                # Process request
                response = await call_next(request)
                
                # Get system metrics after request
                system_after = self._capture_system_snapshot()
                
                # Calculate metrics
                response_time = time.time() - start_time
                
                # Record performance metrics
                await self._record_request_metrics(
                    request, response, request_id, response_time,
                    system_before, system_after, span
                )
                
                # Add APM headers to response
                self._add_apm_headers(response, request_id, response_time)
                
                return response
                
        except Exception as e:
            # Record error metrics
            response_time = time.time() - start_time
            await self._record_error_metrics(request, request_id, response_time, e)
            raise
            
        finally:
            # Clean up request tracking
            self._cleanup_request(request_id)
    
    def _should_exclude_path(self, path: str) -> bool:
        """Check if path should be excluded from APM monitoring"""
        return any(path.startswith(excluded) for excluded in self.excluded_paths)
    
    def _should_sample(self) -> bool:
        """Determine if request should be sampled"""
        import random
        return random.random() < self.sampling_rate
    
    def _get_request_id(self, request: Request) -> str:
        """Get or generate request ID"""
        return (
            request.headers.get("x-request-id") or
            request.headers.get("x-correlation-id") or
            f"req_{int(time.time() * 1000000)}"
        )
    
    def _record_request_start(self, request: Request, request_id: str, start_time: float):
        """Record request start metrics"""
        self.active_requests[request_id] = {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "start_time": start_time,
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent", ""),
            "content_length": request.headers.get("content-length", 0)
        }
    
    def _capture_system_snapshot(self) -> Dict[str, Any]:
        """Capture system metrics snapshot"""
        try:
            process = psutil.Process()
            
            return {
                "cpu_percent": process.cpu_percent(),
                "memory_mb": process.memory_info().rss / 1024 / 1024,
                "open_files": len(process.open_files()),
                "num_threads": process.num_threads(),
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"Failed to capture system snapshot: {e}")
            return {}
    
    async def _record_request_metrics(self, request: Request, response: Response,
                                    request_id: str, response_time: float,
                                    system_before: Dict[str, Any],
                                    system_after: Dict[str, Any], span):
        """Record comprehensive request metrics"""
        try:
            # Basic endpoint metrics
            await record_endpoint_performance(
                endpoint=request.url.path,
                method=request.method,
                response_time=response_time,
                status_code=response.status_code
            )
            
            # Detailed profiling if enabled
            if self.enable_detailed_profiling:
                await self._record_detailed_metrics(
                    request, response, request_id, response_time,
                    system_before, system_after, span
                )
            
            # Performance analysis
            self._analyze_request_performance(
                request, response, response_time, span
            )
            
        except Exception as e:
            logger.error(f"Failed to record request metrics: {e}")
    
    async def _record_detailed_metrics(self, request: Request, response: Response,
                                     request_id: str, response_time: float,
                                     system_before: Dict[str, Any],
                                     system_after: Dict[str, Any], span):
        """Record detailed performance metrics"""
        try:
            # Calculate resource deltas
            cpu_delta = system_after.get("cpu_percent", 0) - system_before.get("cpu_percent", 0)
            memory_delta = system_after.get("memory_mb", 0) - system_before.get("memory_mb", 0)
            
            # Request size metrics
            request_size = int(request.headers.get("content-length", 0))
            response_size = int(response.headers.get("content-length", 0))
            
            # Add detailed attributes to span
            span.set_attribute("performance.response_time_ms", response_time * 1000)
            span.set_attribute("performance.cpu_delta", cpu_delta)
            span.set_attribute("performance.memory_delta_mb", memory_delta)
            span.set_attribute("performance.request_size_bytes", request_size)
            span.set_attribute("performance.response_size_bytes", response_size)
            span.set_attribute("http.status_code", response.status_code)
            
            # Database query analysis (if available)
            db_metrics = await self._analyze_database_performance(request_id)
            if db_metrics:
                span.set_attribute("database.query_count", db_metrics.get("query_count", 0))
                span.set_attribute("database.total_time_ms", db_metrics.get("total_time", 0))
            
            # Cache performance (if available)
            cache_metrics = await self._analyze_cache_performance(request_id)
            if cache_metrics:
                span.set_attribute("cache.hit_count", cache_metrics.get("hits", 0))
                span.set_attribute("cache.miss_count", cache_metrics.get("misses", 0))
                span.set_attribute("cache.hit_rate", cache_metrics.get("hit_rate", 0))
            
        except Exception as e:
            logger.error(f"Failed to record detailed metrics: {e}")
    
    def _analyze_request_performance(self, request: Request, response: Response,
                                   response_time: float, span):
        """Analyze request performance and set performance indicators"""
        try:
            # Performance classification
            if response_time < 0.1:
                performance_level = "excellent"
            elif response_time < 0.5:
                performance_level = "good"
            elif response_time < 1.0:
                performance_level = "average"
            elif response_time < 3.0:
                performance_level = "poor"
            else:
                performance_level = "critical"
            
            span.set_attribute("performance.level", performance_level)
            
            # Detect performance issues
            issues = []
            
            if response_time > 3.0:
                issues.append("slow_response")
            
            if response.status_code >= 500:
                issues.append("server_error")
            elif response.status_code >= 400:
                issues.append("client_error")
            
            # Large response detection
            response_size = int(response.headers.get("content-length", 0))
            if response_size > 10 * 1024 * 1024:  # > 10MB
                issues.append("large_response")
            
            if issues:
                span.set_attribute("performance.issues", ",".join(issues))
                logger.warning(f"Performance issues detected for {request.method} {request.url.path}: {issues}")
            
        except Exception as e:
            logger.error(f"Failed to analyze request performance: {e}")
    
    async def _analyze_database_performance(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Analyze database performance for the request"""
        try:
            # This would integrate with your database monitoring
            # For now, return mock data
            return {
                "query_count": 3,
                "total_time": 150,  # ms
                "slow_queries": 0
            }
        except Exception as e:
            logger.error(f"Database performance analysis failed: {e}")
            return None
    
    async def _analyze_cache_performance(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Analyze cache performance for the request"""
        try:
            # This would integrate with your cache monitoring
            # For now, return mock data
            return {
                "hits": 5,
                "misses": 1,
                "hit_rate": 83.3
            }
        except Exception as e:
            logger.error(f"Cache performance analysis failed: {e}")
            return None
    
    async def _record_error_metrics(self, request: Request, request_id: str,
                                  response_time: float, error: Exception):
        """Record error metrics"""
        try:
            # Record error endpoint metrics
            await record_endpoint_performance(
                endpoint=request.url.path,
                method=request.method,
                response_time=response_time,
                status_code=500
            )
            
            # Log error details
            logger.error(f"Request error for {request.method} {request.url.path}: {error}")
            
        except Exception as e:
            logger.error(f"Failed to record error metrics: {e}")
    
    def _add_apm_headers(self, response: Response, request_id: str, response_time: float):
        """Add APM headers to response"""
        try:
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{response_time:.3f}s"
            response.headers["X-APM-Enabled"] = "true"
            
            # Performance indicator
            if response_time < 0.1:
                response.headers["X-Performance-Level"] = "excellent"
            elif response_time < 0.5:
                response.headers["X-Performance-Level"] = "good"
            elif response_time < 1.0:
                response.headers["X-Performance-Level"] = "average"
            else:
                response.headers["X-Performance-Level"] = "poor"
                
        except Exception as e:
            logger.error(f"Failed to add APM headers: {e}")
    
    def _cleanup_request(self, request_id: str):
        """Clean up request tracking data"""
        self.active_requests.pop(request_id, None)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check X-Forwarded-For header
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        # Check X-Real-IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to direct connection
        return getattr(request.client, 'host', 'unknown')
    
    def get_active_requests(self) -> Dict[str, Dict[str, Any]]:
        """Get currently active requests"""
        return self.active_requests.copy()
    
    def get_apm_stats(self) -> Dict[str, Any]:
        """Get APM middleware statistics"""
        return {
            "active_requests": len(self.active_requests),
            "sampling_rate": self.sampling_rate,
            "detailed_profiling_enabled": self.enable_detailed_profiling,
            "excluded_paths": self.excluded_paths
        }

class DatabaseAPMMiddleware:
    """APM middleware for database operations"""
    
    def __init__(self):
        self.query_metrics: Dict[str, Any] = {}
    
    async def before_query(self, query: str, parameters: Any = None):
        """Called before database query execution"""
        query_id = f"query_{int(time.time() * 1000000)}"
        
        self.query_metrics[query_id] = {
            "query": query[:1000],  # Limit query length
            "parameters": str(parameters)[:500] if parameters else None,
            "start_time": time.time(),
            "query_id": query_id
        }
        
        return query_id
    
    async def after_query(self, query_id: str, result_count: int = 0, error: Exception = None):
        """Called after database query execution"""
        if query_id not in self.query_metrics:
            return
        
        metrics = self.query_metrics[query_id]
        execution_time = time.time() - metrics["start_time"]
        
        # Record in APM profiler
        apm_collector.profiler.profile_function(
            "database_query",
            execution_time,
            0,  # memory delta not available here
            query=metrics["query"][:100],  # Abbreviated query
            result_count=result_count,
            success=error is None,
            error=str(error) if error else None
        )
        
        # Log slow queries
        if execution_time > 1.0:  # > 1 second
            logger.warning(f"Slow database query detected: {execution_time:.3f}s - {metrics['query'][:100]}")
        
        # Clean up
        del self.query_metrics[query_id]

# Global middleware instances
apm_middleware = APMMiddleware
database_apm_middleware = DatabaseAPMMiddleware()