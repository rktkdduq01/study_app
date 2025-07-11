"""
Metrics Collection Middleware
Automatic metrics collection for HTTP requests and system operations
"""

import time
from datetime import datetime
from typing import Dict, Any, Optional
from urllib.parse import unquote

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

from app.core.logger import get_logger
from app.core.metrics_collector import metrics_collector, record_metric

logger = get_logger(__name__)

class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for automatic metrics collection"""
    
    def __init__(self, app, enable_detailed_metrics: bool = True):
        super().__init__(app)
        self.enable_detailed_metrics = enable_detailed_metrics
        
        # Request tracking
        self.request_counts: Dict[str, int] = {}
        self.response_times: Dict[str, float] = {}
        
        # Excluded paths
        self.excluded_paths = [
            "/health",
            "/metrics",
            "/static",
            "/favicon.ico"
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Process request with metrics collection"""
        
        # Skip metrics for excluded paths
        if self._should_exclude_path(request.url.path):
            return await call_next(request)
        
        start_time = time.time()
        request_start = datetime.utcnow()
        
        # Prepare labels
        labels = self._get_request_labels(request)
        
        # Increment request counter
        await record_metric("http_requests_total", 1.0, labels)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Update labels with response info
            labels.update(self._get_response_labels(response))
            
            # Record metrics
            await self._record_request_metrics(
                request, response, response_time, labels
            )
            
            # Add metrics headers
            self._add_metrics_headers(response, response_time)
            
            return response
            
        except Exception as e:
            # Record error metrics
            response_time = time.time() - start_time
            labels["status"] = "error"
            labels["error"] = type(e).__name__
            
            await record_metric("http_request_duration", response_time, labels)
            await record_metric("http_requests_errors_total", 1.0, labels)
            
            raise
    
    def _should_exclude_path(self, path: str) -> bool:
        """Check if path should be excluded from metrics"""
        return any(path.startswith(excluded) for excluded in self.excluded_paths)
    
    def _get_request_labels(self, request: Request) -> Dict[str, str]:
        """Extract labels from request"""
        labels = {
            "method": request.method,
            "endpoint": self._normalize_path(request.url.path),
            "scheme": request.url.scheme
        }
        
        # Add route pattern if available
        if hasattr(request, 'route') and request.route:
            labels["route"] = getattr(request.route, 'path', request.url.path)
        
        return labels
    
    def _get_response_labels(self, response: Response) -> Dict[str, str]:
        """Extract labels from response"""
        status_code = response.status_code
        
        return {
            "status_code": str(status_code),
            "status_class": f"{status_code // 100}xx"
        }
    
    def _normalize_path(self, path: str) -> str:
        """Normalize path for metrics (remove dynamic segments)"""
        # Simple normalization - replace numeric segments with placeholders
        import re
        
        # Replace UUIDs
        path = re.sub(r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '/{uuid}', path)
        
        # Replace numeric IDs
        path = re.sub(r'/\d+', '/{id}', path)
        
        return path
    
    async def _record_request_metrics(self, request: Request, response: Response,
                                    response_time: float, labels: Dict[str, str]):
        """Record comprehensive request metrics"""
        try:
            # Response time
            await record_metric("http_request_duration", response_time, labels)
            
            # Request size
            request_size = int(request.headers.get("content-length", 0))
            if request_size > 0:
                await record_metric("http_request_size_bytes", request_size, labels)
            
            # Response size
            response_size = int(response.headers.get("content-length", 0))
            if response_size > 0:
                await record_metric("http_response_size_bytes", response_size, labels)
            
            # Status-specific metrics
            if response.status_code >= 400:
                error_labels = {**labels, "error_type": "http_error"}
                await record_metric("http_requests_errors_total", 1.0, error_labels)
            
            # Detailed metrics if enabled
            if self.enable_detailed_metrics:
                await self._record_detailed_metrics(request, response, response_time, labels)
            
        except Exception as e:
            logger.error(f"Failed to record request metrics: {e}")
    
    async def _record_detailed_metrics(self, request: Request, response: Response,
                                     response_time: float, labels: Dict[str, str]):
        """Record detailed request metrics"""
        try:
            # Slow request detection
            if response_time > 1.0:  # > 1 second
                slow_labels = {**labels, "threshold": "1s"}
                await record_metric("http_requests_slow_total", 1.0, slow_labels)
            
            if response_time > 5.0:  # > 5 seconds
                very_slow_labels = {**labels, "threshold": "5s"}
                await record_metric("http_requests_very_slow_total", 1.0, very_slow_labels)
            
            # Large response detection
            response_size = int(response.headers.get("content-length", 0))
            if response_size > 1024 * 1024:  # > 1MB
                large_labels = {**labels, "size_threshold": "1MB"}
                await record_metric("http_responses_large_total", 1.0, large_labels)
            
            # Client information
            user_agent = request.headers.get("user-agent", "")
            if user_agent:
                client_labels = {**labels, "client_type": self._classify_user_agent(user_agent)}
                await record_metric("http_requests_by_client_total", 1.0, client_labels)
            
            # Geographic information (if available)
            client_ip = self._get_client_ip(request)
            if client_ip:
                geo_labels = {**labels, "region": self._get_region_from_ip(client_ip)}
                await record_metric("http_requests_by_region_total", 1.0, geo_labels)
            
        except Exception as e:
            logger.error(f"Failed to record detailed metrics: {e}")
    
    def _classify_user_agent(self, user_agent: str) -> str:
        """Classify user agent type"""
        user_agent_lower = user_agent.lower()
        
        if "bot" in user_agent_lower or "crawler" in user_agent_lower:
            return "bot"
        elif "mobile" in user_agent_lower:
            return "mobile"
        elif "tablet" in user_agent_lower:
            return "tablet"
        else:
            return "desktop"
    
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
    
    def _get_region_from_ip(self, ip: str) -> str:
        """Get region from IP address (simplified)"""
        # This would integrate with a GeoIP service
        # For now, return a default region
        return "unknown"
    
    def _add_metrics_headers(self, response: Response, response_time: float):
        """Add metrics headers to response"""
        try:
            response.headers["X-Response-Time"] = f"{response_time:.3f}s"
            response.headers["X-Metrics-Collected"] = "true"
        except Exception as e:
            logger.error(f"Failed to add metrics headers: {e}")

class DatabaseMetricsMiddleware:
    """Middleware for database operation metrics"""
    
    def __init__(self):
        self.active_queries: Dict[str, Dict[str, Any]] = {}
    
    async def before_query(self, query: str, operation: str = "select") -> str:
        """Called before database query"""
        query_id = f"db_query_{int(time.time() * 1000000)}"
        
        self.active_queries[query_id] = {
            "query": query[:100],  # Truncated query
            "operation": operation.lower(),
            "start_time": time.time()
        }
        
        # Record query start
        labels = {"operation": operation.lower()}
        await record_metric("database_queries_total", 1.0, labels)
        
        return query_id
    
    async def after_query(self, query_id: str, rows_affected: int = 0, 
                         error: Exception = None):
        """Called after database query"""
        if query_id not in self.active_queries:
            return
        
        query_info = self.active_queries[query_id]
        execution_time = time.time() - query_info["start_time"]
        
        labels = {
            "operation": query_info["operation"],
            "status": "error" if error else "success"
        }
        
        # Record execution time
        await record_metric("database_query_duration", execution_time, labels)
        
        # Record rows affected
        if rows_affected > 0:
            await record_metric("database_rows_affected", rows_affected, labels)
        
        # Record errors
        if error:
            error_labels = {**labels, "error_type": type(error).__name__}
            await record_metric("database_queries_errors_total", 1.0, error_labels)
        
        # Slow query detection
        if execution_time > 1.0:  # > 1 second
            slow_labels = {**labels, "threshold": "1s"}
            await record_metric("database_queries_slow_total", 1.0, slow_labels)
        
        # Clean up
        del self.active_queries[query_id]

class CacheMetricsMiddleware:
    """Middleware for cache operation metrics"""
    
    async def record_cache_operation(self, operation: str, key: str, 
                                   hit: bool = None, size: int = None):
        """Record cache operation metrics"""
        try:
            labels = {"operation": operation}
            
            # Record operation
            await record_metric("cache_operations_total", 1.0, labels)
            
            # Record hit/miss
            if hit is not None:
                hit_labels = {**labels, "result": "hit" if hit else "miss"}
                await record_metric("cache_hit_miss_total", 1.0, hit_labels)
                
                # Update hit rate calculation
                if hit:
                    await record_metric("cache_hits_total", 1.0, labels)
                else:
                    await record_metric("cache_misses_total", 1.0, labels)
            
            # Record size
            if size is not None:
                await record_metric("cache_operation_size_bytes", size, labels)
            
        except Exception as e:
            logger.error(f"Failed to record cache metrics: {e}")

class BusinessMetricsCollector:
    """Collector for business-specific metrics"""
    
    def __init__(self):
        self.metrics_buffer: Dict[str, float] = {}
    
    async def record_user_action(self, action: str, user_id: str = None,
                                metadata: Dict[str, str] = None):
        """Record user action metrics"""
        try:
            labels = {"action": action}
            
            if metadata:
                labels.update(metadata)
            
            await record_metric("user_actions_total", 1.0, labels)
            
            # Record by user type if available
            if user_id:
                user_labels = {**labels, "user_type": self._classify_user(user_id)}
                await record_metric("user_actions_by_type_total", 1.0, user_labels)
            
        except Exception as e:
            logger.error(f"Failed to record user action: {e}")
    
    async def record_business_event(self, event: str, value: float = 1.0,
                                  labels: Dict[str, str] = None):
        """Record business event metrics"""
        try:
            event_labels = {"event": event}
            if labels:
                event_labels.update(labels)
            
            await record_metric("business_events_total", value, event_labels)
            
        except Exception as e:
            logger.error(f"Failed to record business event: {e}")
    
    def _classify_user(self, user_id: str) -> str:
        """Classify user type (simplified)"""
        # This would integrate with your user classification logic
        return "regular"

# Global middleware instances
metrics_middleware = MetricsMiddleware
database_metrics_middleware = DatabaseMetricsMiddleware()
cache_metrics_middleware = CacheMetricsMiddleware()
business_metrics_collector = BusinessMetricsCollector()