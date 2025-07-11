"""
Request/Response logging middleware.
"""
import time
import json
from typing import Optional, Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Message

from app.core.logger import logger
from app.utils.security_logger import get_client_ip


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses"""
    
    def __init__(self, app, **kwargs):
        super().__init__(app)
        self.log_request_body = kwargs.get("log_request_body", False)
        self.log_response_body = kwargs.get("log_response_body", False)
        self.exclude_paths = kwargs.get("exclude_paths", ["/health", "/metrics", "/docs"])
        self.sensitive_fields = kwargs.get("sensitive_fields", [
            "password", "token", "secret", "api_key", "authorization"
        ])
        self.max_body_size = kwargs.get("max_body_size", 1024)  # 1KB
    
    async def dispatch(self, request: Request, call_next):
        """Process request and log details"""
        # Skip logging for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Start timing
        start_time = time.time()
        
        # Extract request details
        request_details = await self._extract_request_details(request)
        
        # Log incoming request
        logger.info(
            "Incoming request",
            **request_details,
            log_type="request"
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Extract response details
        response_details = await self._extract_response_details(response, duration)
        
        # Combine request and response details
        log_data = {**request_details, **response_details}
        
        # Log based on status code
        if response.status_code >= 500:
            logger.error("Request failed with server error", **log_data)
        elif response.status_code >= 400:
            logger.warning("Request failed with client error", **log_data)
        else:
            logger.info("Request completed successfully", **log_data)
        
        return response
    
    async def _extract_request_details(self, request: Request) -> Dict[str, Any]:
        """Extract relevant details from request"""
        # Get client IP
        client_ip = get_client_ip(request)
        
        # Get request ID
        request_id = getattr(request.state, "request_id", None)
        
        # Get user ID if available
        user_id = None
        if hasattr(request.state, "user") and request.state.user:
            user_id = request.state.user.id
        
        details = {
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "path_params": request.path_params,
            "client_ip": client_ip,
            "user_agent": request.headers.get("user-agent"),
            "request_id": request_id,
            "user_id": user_id,
        }
        
        # Add headers (excluding sensitive ones)
        headers = {}
        for header, value in request.headers.items():
            if not any(sensitive in header.lower() for sensitive in self.sensitive_fields):
                headers[header] = value
        details["headers"] = headers
        
        # Add request body if enabled and not too large
        if self.log_request_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if len(body) <= self.max_body_size:
                    content_type = request.headers.get("content-type", "")
                    
                    if "application/json" in content_type:
                        body_data = json.loads(body)
                        # Mask sensitive fields
                        body_data = self._mask_sensitive_data(body_data)
                        details["request_body"] = body_data
                    else:
                        details["request_body"] = f"<{content_type} data>"
                else:
                    details["request_body"] = f"<body too large: {len(body)} bytes>"
            except Exception as e:
                details["request_body"] = f"<error reading body: {str(e)}>"
        
        return details
    
    async def _extract_response_details(
        self,
        response: Response,
        duration: float
    ) -> Dict[str, Any]:
        """Extract relevant details from response"""
        details = {
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
            "response_headers": dict(response.headers),
        }
        
        # Add response body if enabled
        if self.log_response_body and response.status_code != 204:
            try:
                # This is tricky with streaming responses
                # For now, we'll skip body logging for responses
                pass
            except Exception:
                pass
        
        return details
    
    def _mask_sensitive_data(
        self,
        data: Any,
        mask: str = "***MASKED***"
    ) -> Any:
        """Recursively mask sensitive fields in data"""
        if isinstance(data, dict):
            masked_data = {}
            for key, value in data.items():
                if any(sensitive in key.lower() for sensitive in self.sensitive_fields):
                    masked_data[key] = mask
                else:
                    masked_data[key] = self._mask_sensitive_data(value, mask)
            return masked_data
        elif isinstance(data, list):
            return [self._mask_sensitive_data(item, mask) for item in data]
        else:
            return data


class PerformanceLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging performance metrics"""
    
    def __init__(self, app, **kwargs):
        super().__init__(app)
        self.slow_request_threshold = kwargs.get("slow_request_threshold", 1.0)  # 1 second
        self.log_all_requests = kwargs.get("log_all_requests", False)
    
    async def dispatch(self, request: Request, call_next):
        """Track and log performance metrics"""
        start_time = time.time()
        
        # Track memory usage before request (if psutil available)
        memory_before = 0
        memory_after = 0
        memory_delta = 0
        
        try:
            import psutil
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            pass
        
        # Process request
        response = await call_next(request)
        
        # Calculate metrics
        duration = time.time() - start_time
        
        try:
            import psutil
            process = psutil.Process()
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_delta = memory_after - memory_before
        except ImportError:
            pass
        
        # Log if slow or if logging all requests
        if duration > self.slow_request_threshold or self.log_all_requests:
            logger.log_performance(
                operation=f"{request.method} {request.url.path}",
                duration=duration,
                metadata={
                    "memory_before_mb": round(memory_before, 2),
                    "memory_after_mb": round(memory_after, 2),
                    "memory_delta_mb": round(memory_delta, 2),
                    "status_code": response.status_code,
                    "slow_request": duration > self.slow_request_threshold
                }
            )
        
        # Add performance headers
        response.headers["X-Response-Time"] = f"{round(duration * 1000, 2)}ms"
        
        return response


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for audit logging of sensitive operations"""
    
    def __init__(self, app, **kwargs):
        super().__init__(app)
        # Define paths that require audit logging
        self.audit_paths = kwargs.get("audit_paths", [
            "/api/v1/users",
            "/api/v1/auth",
            "/api/v1/admin",
            "/api/v1/payments",
        ])
        # Define methods that modify data
        self.audit_methods = kwargs.get("audit_methods", ["POST", "PUT", "PATCH", "DELETE"])
    
    async def dispatch(self, request: Request, call_next):
        """Log sensitive operations for audit trail"""
        # Check if this request needs audit logging
        needs_audit = (
            any(request.url.path.startswith(path) for path in self.audit_paths) and
            request.method in self.audit_methods
        )
        
        if not needs_audit:
            return await call_next(request)
        
        # Extract audit information
        user_id = None
        if hasattr(request.state, "user") and request.state.user:
            user_id = request.state.user.id
        
        client_ip = get_client_ip(request)
        request_id = getattr(request.state, "request_id", None)
        
        # Log audit event before processing
        logger.info(
            "Audit: Operation started",
            user_id=user_id,
            client_ip=client_ip,
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            log_type="audit",
            audit_phase="start"
        )
        
        # Process request
        response = await call_next(request)
        
        # Log audit event after processing
        logger.info(
            "Audit: Operation completed",
            user_id=user_id,
            client_ip=client_ip,
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            success=response.status_code < 400,
            log_type="audit",
            audit_phase="complete"
        )
        
        return response