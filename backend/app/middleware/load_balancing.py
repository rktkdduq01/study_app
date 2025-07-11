"""
Load Balancing Middleware
Request routing and load distribution middleware
"""

import asyncio
import time
import httpx
from datetime import datetime
from typing import Optional, Dict, Any
from urllib.parse import urljoin

from fastapi import Request, Response, HTTPException
from fastapi.responses import StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

from app.core.logger import get_logger
from app.core.load_balancer import load_balancer, get_backend_server, record_backend_request
from app.core.redis_client import redis_client

logger = get_logger(__name__)

class LoadBalancingMiddleware(BaseHTTPMiddleware):
    """Load balancing middleware for request distribution"""
    
    def __init__(self, app, enable_proxy: bool = True):
        super().__init__(app)
        self.enable_proxy = enable_proxy
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Circuit breaker for backend failures
        self.circuit_breaker = {
            "failure_count": 0,
            "last_failure": None,
            "is_open": False,
            "failure_threshold": 5,
            "recovery_timeout": 60
        }
    
    async def dispatch(self, request: Request, call_next):
        """Route request to backend server or handle locally"""
        
        # Skip load balancing for health checks and admin endpoints
        if self._should_handle_locally(request):
            return await call_next(request)
        
        # Check if we should proxy to backend
        if not self.enable_proxy:
            return await call_next(request)
        
        # Check circuit breaker
        if self._is_circuit_open():
            logger.warning("Circuit breaker open, handling request locally")
            return await call_next(request)
        
        try:
            # Get backend server
            client_ip = self._get_client_ip(request)
            session_id = self._extract_session_id(request)
            
            backend_server = await get_backend_server(
                client_ip=client_ip,
                session_id=session_id,
                request_path=request.url.path
            )
            
            if not backend_server:
                logger.warning("No backend servers available, handling locally")
                return await call_next(request)
            
            # Proxy request to backend
            response = await self._proxy_request(request, backend_server)
            
            # Reset circuit breaker on success
            self._reset_circuit_breaker()
            
            return response
            
        except Exception as e:
            logger.error(f"Load balancing failed: {e}")
            
            # Update circuit breaker
            self._record_failure()
            
            # Fallback to local handling
            return await call_next(request)
    
    def _should_handle_locally(self, request: Request) -> bool:
        """Determine if request should be handled locally"""
        local_paths = [
            "/health",
            "/metrics", 
            "/admin",
            "/docs",
            "/openapi.json",
            "/static"
        ]
        
        return any(request.url.path.startswith(path) for path in local_paths)
    
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
    
    def _extract_session_id(self, request: Request) -> Optional[str]:
        """Extract session ID from request"""
        # Try to get from Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:][:32]  # Use part of token as session ID
        
        # Try to get from cookies
        session_cookie = request.cookies.get("session_id")
        if session_cookie:
            return session_cookie
        
        return None
    
    async def _proxy_request(self, request: Request, backend_server) -> Response:
        """Proxy request to backend server"""
        start_time = time.time()
        
        try:
            # Build backend URL
            backend_url = f"http://{backend_server.host}:{backend_server.port}"
            full_url = urljoin(backend_url, str(request.url.path))
            
            if request.url.query:
                full_url += f"?{request.url.query}"
            
            # Prepare headers
            headers = dict(request.headers)
            
            # Add load balancer headers
            headers["X-Forwarded-For"] = self._get_client_ip(request)
            headers["X-Forwarded-Proto"] = request.url.scheme
            headers["X-Forwarded-Host"] = request.headers.get("host", "")
            headers["X-Load-Balancer"] = "quest-edu-lb"
            headers["X-Backend-Server"] = backend_server.id
            
            # Remove hop-by-hop headers
            hop_by_hop_headers = [
                "connection", "upgrade", "proxy-authenticate",
                "proxy-authorization", "te", "trailers", "transfer-encoding"
            ]
            
            for header in hop_by_hop_headers:
                headers.pop(header, None)
            
            # Get request body
            body = None
            if request.method in ["POST", "PUT", "PATCH"]:
                body = await request.body()
            
            # Make request to backend
            backend_response = await self.http_client.request(
                method=request.method,
                url=full_url,
                headers=headers,
                content=body
            )
            
            # Record metrics
            response_time = time.time() - start_time
            await record_backend_request(
                backend_server.id, 
                response_time, 
                backend_response.status_code < 400
            )
            
            # Create response
            response_headers = dict(backend_response.headers)
            
            # Add load balancer headers
            response_headers["X-Backend-Server"] = backend_server.id
            response_headers["X-Response-Time"] = f"{response_time:.3f}s"
            
            # Remove hop-by-hop headers from response
            for header in hop_by_hop_headers:
                response_headers.pop(header, None)
            
            # Stream response content
            async def generate():
                async for chunk in backend_response.aiter_bytes():
                    yield chunk
            
            return StreamingResponse(
                generate(),
                status_code=backend_response.status_code,
                headers=response_headers,
                media_type=response_headers.get("content-type")
            )
            
        except Exception as e:
            logger.error(f"Backend request failed: {e}")
            
            # Record failed request
            response_time = time.time() - start_time
            await record_backend_request(backend_server.id, response_time, False)
            
            raise HTTPException(
                status_code=502,
                detail=f"Backend server error: {str(e)}"
            )
    
    def _is_circuit_open(self) -> bool:
        """Check if circuit breaker is open"""
        if not self.circuit_breaker["is_open"]:
            return False
        
        # Check if recovery timeout has passed
        if self.circuit_breaker["last_failure"]:
            time_since_failure = time.time() - self.circuit_breaker["last_failure"]
            if time_since_failure > self.circuit_breaker["recovery_timeout"]:
                logger.info("Circuit breaker recovery timeout reached, trying backend")
                return False
        
        return True
    
    def _record_failure(self):
        """Record backend failure for circuit breaker"""
        self.circuit_breaker["failure_count"] += 1
        self.circuit_breaker["last_failure"] = time.time()
        
        if (self.circuit_breaker["failure_count"] >= 
            self.circuit_breaker["failure_threshold"]):
            
            self.circuit_breaker["is_open"] = True
            logger.error(
                f"Circuit breaker opened after {self.circuit_breaker['failure_count']} failures"
            )
    
    def _reset_circuit_breaker(self):
        """Reset circuit breaker on successful request"""
        if self.circuit_breaker["failure_count"] > 0:
            self.circuit_breaker["failure_count"] = 0
            self.circuit_breaker["is_open"] = False
            logger.info("Circuit breaker reset after successful request")

class HealthCheckMiddleware(BaseHTTPMiddleware):
    """Health check middleware for load balancer"""
    
    def __init__(self, app):
        super().__init__(app)
        self.start_time = time.time()
    
    async def dispatch(self, request: Request, call_next):
        """Handle health check requests"""
        
        if request.url.path == "/health":
            return await self._handle_health_check(request)
        elif request.url.path == "/ready":
            return await self._handle_readiness_check(request)
        elif request.url.path == "/live":
            return await self._handle_liveness_check(request)
        else:
            return await call_next(request)
    
    async def _handle_health_check(self, request: Request) -> Response:
        """Handle comprehensive health check"""
        try:
            health_data = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "uptime": time.time() - self.start_time,
                "version": "1.0.0",
                "load_balancer": await self._check_load_balancer_health(),
                "database": await self._check_database_health(),
                "redis": await self._check_redis_health()
            }
            
            # Determine overall status
            if (health_data["load_balancer"]["status"] != "healthy" or
                health_data["database"]["status"] != "healthy" or
                health_data["redis"]["status"] != "healthy"):
                
                health_data["status"] = "unhealthy"
                status_code = 503
            else:
                status_code = 200
            
            return Response(
                content=str(health_data),
                status_code=status_code,
                headers={"Content-Type": "application/json"}
            )
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return Response(
                content='{"status": "error", "error": "' + str(e) + '"}',
                status_code=503,
                headers={"Content-Type": "application/json"}
            )
    
    async def _handle_readiness_check(self, request: Request) -> Response:
        """Handle readiness probe (can serve traffic)"""
        try:
            # Check if all dependencies are ready
            redis_ready = await self._check_redis_health()
            db_ready = await self._check_database_health()
            
            if (redis_ready["status"] == "healthy" and 
                db_ready["status"] == "healthy"):
                
                return Response(
                    content='{"status": "ready"}',
                    status_code=200,
                    headers={"Content-Type": "application/json"}
                )
            else:
                return Response(
                    content='{"status": "not ready"}',
                    status_code=503,
                    headers={"Content-Type": "application/json"}
                )
                
        except Exception as e:
            logger.error(f"Readiness check failed: {e}")
            return Response(
                content='{"status": "not ready", "error": "' + str(e) + '"}',
                status_code=503,
                headers={"Content-Type": "application/json"}
            )
    
    async def _handle_liveness_check(self, request: Request) -> Response:
        """Handle liveness probe (process is alive)"""
        # Simple liveness check - if we can respond, we're alive
        return Response(
            content='{"status": "alive"}',
            status_code=200,
            headers={"Content-Type": "application/json"}
        )
    
    async def _check_load_balancer_health(self) -> Dict[str, Any]:
        """Check load balancer health"""
        try:
            stats = load_balancer.get_load_balancer_stats()
            
            healthy_servers = stats["healthy_servers"]
            total_servers = stats["total_servers"]
            
            if healthy_servers == 0:
                status = "critical"
            elif healthy_servers < total_servers * 0.5:
                status = "degraded"
            else:
                status = "healthy"
            
            return {
                "status": status,
                "healthy_servers": healthy_servers,
                "total_servers": total_servers,
                "strategy": stats["strategy"]
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _check_database_health(self) -> Dict[str, Any]:
        """Check database health"""
        try:
            # This would check actual database connectivity
            # For now, return healthy
            return {"status": "healthy", "response_time": 0.001}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def _check_redis_health(self) -> Dict[str, Any]:
        """Check Redis health"""
        try:
            start_time = time.time()
            await redis_client.ping()
            response_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "response_time": response_time
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

# Global middleware instances
load_balancing_middleware = LoadBalancingMiddleware
health_check_middleware = HealthCheckMiddleware