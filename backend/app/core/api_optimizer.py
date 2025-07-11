"""
API Response Time Optimization System
Advanced API performance optimization with caching, compression, and monitoring
"""

import asyncio
import time
import json
import gzip
import brotli
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, asdict, field
from collections import defaultdict, deque
from functools import wraps
from contextlib import asynccontextmanager
import hashlib

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

from app.core.logger import get_logger
from app.core.redis_client import redis_client
from app.core.advanced_cache import multi_layer_cache
from app.core.config import settings

logger = get_logger(__name__)

@dataclass
class APIMetrics:
    """API performance metrics"""
    endpoint: str
    method: str
    status_code: int
    response_time: float
    response_size: int
    cache_hit: bool
    compression_used: Optional[str]
    timestamp: datetime
    user_id: Optional[str] = None
    request_id: Optional[str] = None

@dataclass
class OptimizationConfig:
    """API optimization configuration"""
    enable_compression: bool = True
    compression_threshold: int = 1024  # 1KB
    enable_response_caching: bool = True
    default_cache_ttl: int = 300  # 5 minutes
    enable_request_batching: bool = True
    batch_timeout: float = 0.1  # 100ms
    enable_query_optimization: bool = True
    max_response_size: int = 10 * 1024 * 1024  # 10MB

class APIPerformanceOptimizer:
    """API performance optimization system"""
    
    def __init__(self, config: OptimizationConfig = None):
        self.config = config or OptimizationConfig()
        self.metrics: deque = deque(maxlen=10000)
        
        # Performance tracking
        self.endpoint_stats: Dict[str, Dict] = defaultdict(lambda: {
            "total_requests": 0,
            "total_time": 0.0,
            "avg_time": 0.0,
            "min_time": float('inf'),
            "max_time": 0.0,
            "cache_hits": 0,
            "errors": 0,
            "slow_requests": 0
        })
        
        # Request batching
        self.batch_requests: Dict[str, List] = defaultdict(list)
        self.batch_timers: Dict[str, asyncio.Task] = {}
        
        # Slow query threshold
        self.slow_query_threshold = 1.0  # 1 second
        
        # Response templates for common patterns
        self.response_templates: Dict[str, Dict] = {}
    
    async def optimize_response(self, request: Request, response_data: Any,
                              cache_key: Optional[str] = None,
                              cache_ttl: Optional[int] = None) -> Response:
        """Optimize API response with caching and compression"""
        start_time = time.time()
        
        try:
            # Convert response to JSON if needed
            if not isinstance(response_data, (str, bytes)):
                response_json = json.dumps(response_data, default=str, separators=(',', ':'))
            else:
                response_json = response_data
            
            response_bytes = response_json.encode('utf-8')
            original_size = len(response_bytes)
            
            # Apply compression if beneficial
            compressed_data, content_encoding = await self._compress_response(
                response_bytes, request
            )
            
            # Create response
            response = Response(
                content=compressed_data,
                media_type="application/json",
                headers=self._get_optimization_headers(content_encoding, original_size)
            )
            
            # Cache response if enabled
            if self.config.enable_response_caching and cache_key:
                await self._cache_response(cache_key, response_data, cache_ttl)
            
            # Record metrics
            await self._record_api_metrics(
                request, response, time.time() - start_time,
                len(compressed_data), content_encoding
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Response optimization failed: {e}")
            # Fallback to simple JSON response
            return JSONResponse(content=response_data)
    
    async def _compress_response(self, data: bytes, request: Request) -> tuple[bytes, Optional[str]]:
        """Compress response based on client capabilities and size"""
        if not self.config.enable_compression or len(data) < self.config.compression_threshold:
            return data, None
        
        # Get accepted encodings
        accept_encoding = request.headers.get('accept-encoding', '').lower()
        
        # Try Brotli first (better compression)
        if 'br' in accept_encoding:
            try:
                compressed = brotli.compress(data, quality=6)
                if len(compressed) < len(data) * 0.9:  # At least 10% reduction
                    return compressed, 'br'
            except Exception as e:
                logger.error(f"Brotli compression failed: {e}")
        
        # Try Gzip
        if 'gzip' in accept_encoding:
            try:
                compressed = gzip.compress(data, compresslevel=6)
                if len(compressed) < len(data) * 0.9:  # At least 10% reduction
                    return compressed, 'gzip'
            except Exception as e:
                logger.error(f"Gzip compression failed: {e}")
        
        return data, None
    
    def _get_optimization_headers(self, content_encoding: Optional[str], 
                                original_size: int) -> Dict[str, str]:
        """Get headers for optimized response"""
        headers = {
            "X-Original-Size": str(original_size),
            "X-Optimized": "true",
            "Cache-Control": "public, max-age=300"  # 5 minutes default
        }
        
        if content_encoding:
            headers["Content-Encoding"] = content_encoding
            headers["Vary"] = "Accept-Encoding"
        
        return headers
    
    async def _cache_response(self, cache_key: str, data: Any, ttl: Optional[int]):
        """Cache API response"""
        try:
            cache_ttl = ttl or self.config.default_cache_ttl
            await multi_layer_cache.set(cache_key, data, cache_ttl)
            logger.debug(f"Cached response: {cache_key}")
        except Exception as e:
            logger.error(f"Response caching failed: {e}")
    
    async def get_cached_response(self, cache_key: str) -> Optional[Any]:
        """Get cached API response"""
        try:
            cached_data = await multi_layer_cache.get(cache_key)
            if cached_data is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_data
            return None
        except Exception as e:
            logger.error(f"Cache retrieval failed: {e}")
            return None
    
    async def _record_api_metrics(self, request: Request, response: Response,
                                response_time: float, response_size: int,
                                compression: Optional[str]):
        """Record API performance metrics"""
        try:
            endpoint = f"{request.method} {request.url.path}"
            
            metric = APIMetrics(
                endpoint=endpoint,
                method=request.method,
                status_code=response.status_code,
                response_time=response_time,
                response_size=response_size,
                cache_hit=bool(request.headers.get('X-Cache-Hit')),
                compression_used=compression,
                timestamp=datetime.utcnow(),
                request_id=request.headers.get('X-Request-ID')
            )
            
            self.metrics.append(metric)
            
            # Update endpoint statistics
            stats = self.endpoint_stats[endpoint]
            stats["total_requests"] += 1
            stats["total_time"] += response_time
            stats["avg_time"] = stats["total_time"] / stats["total_requests"]
            stats["min_time"] = min(stats["min_time"], response_time)
            stats["max_time"] = max(stats["max_time"], response_time)
            
            if metric.cache_hit:
                stats["cache_hits"] += 1
            
            if response.status_code >= 400:
                stats["errors"] += 1
            
            if response_time > self.slow_query_threshold:
                stats["slow_requests"] += 1
                logger.warning(f"Slow API request: {endpoint} took {response_time:.3f}s")
            
            # Store metrics in Redis for persistence
            await self._store_metrics_in_redis(metric)
            
        except Exception as e:
            logger.error(f"Metrics recording failed: {e}")
    
    async def _store_metrics_in_redis(self, metric: APIMetrics):
        """Store API metrics in Redis"""
        try:
            key = f"api_metrics:{datetime.utcnow().strftime('%Y%m%d')}:{metric.endpoint.replace(' ', '_')}"
            metric_data = asdict(metric)
            metric_data['timestamp'] = metric.timestamp.isoformat()
            
            await redis_client.lpush(key, json.dumps(metric_data))
            await redis_client.expire(key, 86400 * 7)  # Keep for 7 days
            
        except Exception as e:
            logger.error(f"Redis metrics storage failed: {e}")
    
    async def batch_requests(self, batch_key: str, request_data: Dict[str, Any],
                           handler: Callable) -> Any:
        """Batch similar requests for optimization"""
        if not self.config.enable_request_batching:
            return await handler(request_data)
        
        # Add request to batch
        self.batch_requests[batch_key].append({
            "data": request_data,
            "future": asyncio.Future(),
            "timestamp": time.time()
        })
        
        # Start timer if not already running
        if batch_key not in self.batch_timers:
            self.batch_timers[batch_key] = asyncio.create_task(
                self._process_batch_after_timeout(batch_key, handler)
            )
        
        # Wait for result
        request_entry = self.batch_requests[batch_key][-1]
        return await request_entry["future"]
    
    async def _process_batch_after_timeout(self, batch_key: str, handler: Callable):
        """Process batched requests after timeout"""
        await asyncio.sleep(self.config.batch_timeout)
        
        if batch_key in self.batch_requests and self.batch_requests[batch_key]:
            batch = self.batch_requests[batch_key]
            self.batch_requests[batch_key] = []
            
            try:
                # Process batch
                batch_data = [item["data"] for item in batch]
                results = await handler(batch_data)
                
                # Return results to individual futures
                for i, item in enumerate(batch):
                    if i < len(results):
                        item["future"].set_result(results[i])
                    else:
                        item["future"].set_exception(
                            Exception("Batch processing failed")
                        )
                        
            except Exception as e:
                # Set exception for all futures
                for item in batch:
                    item["future"].set_exception(e)
            
            # Clean up timer
            if batch_key in self.batch_timers:
                del self.batch_timers[batch_key]
    
    def create_response_template(self, template_name: str, template: Dict[str, Any]):
        """Create response template for common patterns"""
        self.response_templates[template_name] = template
    
    def get_response_template(self, template_name: str, **kwargs) -> Dict[str, Any]:
        """Get response template with substitutions"""
        if template_name not in self.response_templates:
            return {}
        
        template = self.response_templates[template_name].copy()
        
        # Simple template substitution
        def substitute_values(obj, values):
            if isinstance(obj, dict):
                return {k: substitute_values(v, values) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [substitute_values(item, values) for item in obj]
            elif isinstance(obj, str) and obj.startswith('{{') and obj.endswith('}}'):
                key = obj[2:-2].strip()
                return values.get(key, obj)
            else:
                return obj
        
        return substitute_values(template, kwargs)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get API performance statistics"""
        total_requests = sum(stats["total_requests"] for stats in self.endpoint_stats.values())
        total_cache_hits = sum(stats["cache_hits"] for stats in self.endpoint_stats.values())
        total_errors = sum(stats["errors"] for stats in self.endpoint_stats.values())
        total_slow_requests = sum(stats["slow_requests"] for stats in self.endpoint_stats.values())
        
        # Recent metrics analysis
        recent_metrics = [
            m for m in self.metrics 
            if m.timestamp > datetime.utcnow() - timedelta(minutes=5)
        ]
        
        avg_response_time = 0
        if recent_metrics:
            avg_response_time = sum(m.response_time for m in recent_metrics) / len(recent_metrics)
        
        return {
            "total_requests": total_requests,
            "cache_hit_rate": (total_cache_hits / total_requests * 100) if total_requests > 0 else 0,
            "error_rate": (total_errors / total_requests * 100) if total_requests > 0 else 0,
            "slow_request_rate": (total_slow_requests / total_requests * 100) if total_requests > 0 else 0,
            "avg_response_time_ms": round(avg_response_time * 1000, 2),
            "recent_requests": len(recent_metrics),
            "endpoint_stats": dict(self.endpoint_stats),
            "compression_stats": self._get_compression_stats(),
            "top_slow_endpoints": self._get_top_slow_endpoints()
        }
    
    def _get_compression_stats(self) -> Dict[str, Any]:
        """Get compression statistics"""
        recent_metrics = [
            m for m in self.metrics 
            if m.timestamp > datetime.utcnow() - timedelta(hours=1)
        ]
        
        total_requests = len(recent_metrics)
        compressed_requests = len([m for m in recent_metrics if m.compression_used])
        
        compression_types = defaultdict(int)
        for metric in recent_metrics:
            if metric.compression_used:
                compression_types[metric.compression_used] += 1
        
        return {
            "total_requests": total_requests,
            "compressed_requests": compressed_requests,
            "compression_rate": (compressed_requests / total_requests * 100) if total_requests > 0 else 0,
            "compression_types": dict(compression_types)
        }
    
    def _get_top_slow_endpoints(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top slow endpoints"""
        slow_endpoints = [
            {
                "endpoint": endpoint,
                "avg_time": stats["avg_time"],
                "slow_requests": stats["slow_requests"],
                "total_requests": stats["total_requests"]
            }
            for endpoint, stats in self.endpoint_stats.items()
            if stats["total_requests"] > 5  # Only consider endpoints with significant traffic
        ]
        
        return sorted(slow_endpoints, key=lambda x: x["avg_time"], reverse=True)[:limit]

class APIOptimizationMiddleware(BaseHTTPMiddleware):
    """Middleware for API response optimization"""
    
    def __init__(self, app, optimizer: APIPerformanceOptimizer):
        super().__init__(app)
        self.optimizer = optimizer
    
    async def dispatch(self, request: Request, call_next):
        """Apply optimizations to API responses"""
        start_time = time.time()
        
        # Generate request ID
        request_id = hashlib.md5(f"{time.time()}:{id(request)}".encode()).hexdigest()[:8]
        request.headers.__dict__['_list'].append((b'x-request-id', request_id.encode()))
        
        # Check for cached response
        if request.method == "GET":
            cache_key = self._generate_cache_key(request)
            cached_response = await self.optimizer.get_cached_response(cache_key)
            
            if cached_response is not None:
                # Create response from cache
                response = await self.optimizer.optimize_response(
                    request, cached_response
                )
                response.headers["X-Cache-Hit"] = "true"
                return response
        
        # Process request
        response = await call_next(request)
        
        # Optimize response if it's JSON
        if (response.headers.get('content-type', '').startswith('application/json') and
            hasattr(response, 'body')):
            
            try:
                # Read response body
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk
                
                # Parse JSON and optimize
                if body:
                    response_data = json.loads(body)
                    
                    # Cache GET responses
                    cache_key = None
                    if request.method == "GET":
                        cache_key = self._generate_cache_key(request)
                    
                    optimized_response = await self.optimizer.optimize_response(
                        request, response_data, cache_key
                    )
                    
                    # Copy status code and any additional headers
                    optimized_response.status_code = response.status_code
                    for key, value in response.headers.items():
                        if key.lower() not in ['content-length', 'content-encoding']:
                            optimized_response.headers[key] = value
                    
                    return optimized_response
                
            except Exception as e:
                logger.error(f"Response optimization failed: {e}")
        
        # Record metrics for non-optimized responses
        await self.optimizer._record_api_metrics(
            request, response, time.time() - start_time, 0, None
        )
        
        return response
    
    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key for request"""
        # Include path, query parameters, and relevant headers
        key_parts = [
            request.method,
            request.url.path,
            str(request.query_params),
            request.headers.get('authorization', '')[:20]  # Include part of auth for user-specific caching
        ]
        
        key_string = ":".join(key_parts)
        return f"api_cache:{hashlib.md5(key_string.encode()).hexdigest()}"

# Decorators for API optimization
def cached_response(ttl: int = 300, key_prefix: str = "api"):
    """Decorator for caching API responses"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached_result = await api_optimizer.get_cached_response(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await api_optimizer._cache_response(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

def optimized_response(compression: bool = True, template: Optional[str] = None):
    """Decorator for optimizing API responses"""
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            result = await func(request, *args, **kwargs)
            
            # Apply template if specified
            if template and isinstance(result, dict):
                template_data = api_optimizer.get_response_template(template, **result)
                if template_data:
                    result = template_data
            
            # Optimize response
            return await api_optimizer.optimize_response(request, result)
        return wrapper
    return decorator

def batched_request(batch_key: str, timeout: float = 0.1):
    """Decorator for batching similar requests"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await api_optimizer.batch_requests(
                batch_key, {"args": args, "kwargs": kwargs}, func
            )
        return wrapper
    return decorator

# Global optimizer instance
optimization_config = OptimizationConfig(
    enable_compression=getattr(settings, 'API_ENABLE_COMPRESSION', True),
    compression_threshold=getattr(settings, 'API_COMPRESSION_THRESHOLD', 1024),
    enable_response_caching=getattr(settings, 'API_ENABLE_CACHING', True),
    default_cache_ttl=getattr(settings, 'API_DEFAULT_CACHE_TTL', 300)
)

api_optimizer = APIPerformanceOptimizer(optimization_config)

# Create middleware
def create_api_optimization_middleware():
    """Create API optimization middleware"""
    return APIOptimizationMiddleware

# Common response templates
api_optimizer.create_response_template("success", {
    "success": True,
    "data": "{{data}}",
    "message": "{{message}}",
    "timestamp": "{{timestamp}}"
})

api_optimizer.create_response_template("error", {
    "success": False,
    "error": {
        "code": "{{error_code}}",
        "message": "{{error_message}}"
    },
    "timestamp": "{{timestamp}}"
})

api_optimizer.create_response_template("paginated", {
    "success": True,
    "data": "{{items}}",
    "pagination": {
        "page": "{{page}}",
        "per_page": "{{per_page}}",
        "total": "{{total}}",
        "pages": "{{pages}}"
    }
})

# Context manager for API optimization
@asynccontextmanager
async def api_optimization_context():
    """Context manager for API optimization"""
    try:
        yield api_optimizer
    except Exception as e:
        logger.error(f"API optimization context error: {e}")
        raise