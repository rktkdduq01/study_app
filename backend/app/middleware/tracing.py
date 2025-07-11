"""
Distributed Tracing Middleware
Request tracing and correlation middleware for observability
"""

import time
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from urllib.parse import unquote

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

from app.core.logger import get_logger
from app.core.distributed_tracing import (
    distributed_tracer, get_trace_id, get_span_id, correlate_user
)

logger = get_logger(__name__)

class TracingMiddleware(BaseHTTPMiddleware):
    """Middleware for distributed tracing and request correlation"""
    
    def __init__(self, app, service_name: str = "quest-edu-backend"):
        super().__init__(app)
        self.service_name = service_name
        
        # Paths to exclude from tracing
        self.excluded_paths = [
            "/health",
            "/metrics", 
            "/docs",
            "/openapi.json",
            "/static"
        ]
        
        # Headers for trace propagation
        self.trace_headers = [
            "traceparent",
            "tracestate", 
            "x-trace-id",
            "x-span-id",
            "x-request-id"
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Process request with distributed tracing"""
        
        # Skip tracing for excluded paths
        if self._should_exclude_path(request.url.path):
            return await call_next(request)
        
        start_time = time.time()
        
        # Generate or extract request ID
        request_id = self._get_or_generate_request_id(request)
        
        # Extract trace context from headers
        trace_context = self._extract_trace_context(request)
        
        # Create operation name
        operation_name = f"{request.method} {request.url.path}"
        
        # Start tracing
        async with distributed_tracer.trace_context(
            operation_name,
            **self._get_request_attributes(request, request_id)
        ) as span:
            
            try:
                # Add request details to span
                self._enrich_span_with_request_data(span, request, request_id)
                
                # Extract and correlate user information
                await self._correlate_user_context(request)
                
                # Process request
                response = await call_next(request)
                
                # Add response details to span
                self._enrich_span_with_response_data(span, response, start_time)
                
                # Add tracing headers to response
                self._add_trace_headers_to_response(response, request_id)
                
                return response
                
            except Exception as e:
                # Record exception in span
                distributed_tracer.record_exception(span, e)
                
                # Add error details
                span.set_attribute("error", True)
                span.set_attribute("error.type", type(e).__name__)
                span.set_attribute("error.message", str(e))
                
                raise
    
    def _should_exclude_path(self, path: str) -> bool:
        """Check if path should be excluded from tracing"""
        return any(path.startswith(excluded) for excluded in self.excluded_paths)
    
    def _get_or_generate_request_id(self, request: Request) -> str:
        """Get existing request ID or generate new one"""
        # Try to get from headers
        request_id = (
            request.headers.get("x-request-id") or
            request.headers.get("x-correlation-id") or
            request.headers.get("request-id")
        )
        
        if not request_id:
            request_id = str(uuid.uuid4())
        
        return request_id
    
    def _extract_trace_context(self, request: Request) -> Dict[str, str]:
        """Extract trace context from request headers"""
        trace_context = {}
        
        for header_name in self.trace_headers:
            header_value = request.headers.get(header_name)
            if header_value:
                trace_context[header_name] = header_value
        
        return trace_context
    
    def _get_request_attributes(self, request: Request, request_id: str) -> Dict[str, Any]:
        """Get request attributes for span"""
        return {
            "http.method": request.method,
            "http.url": str(request.url),
            "http.scheme": request.url.scheme,
            "http.host": request.url.hostname,
            "http.target": request.url.path,
            "http.user_agent": request.headers.get("user-agent", ""),
            "http.request_id": request_id,
            "service.name": self.service_name,
            "request.timestamp": datetime.utcnow().isoformat()
        }
    
    def _enrich_span_with_request_data(self, span, request: Request, request_id: str):
        """Add detailed request information to span"""
        try:
            # Basic HTTP attributes
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))
            span.set_attribute("http.route", getattr(request, 'route', {}).get('path', ''))
            
            # Client information
            client_ip = self._get_client_ip(request)
            if client_ip:
                span.set_attribute("http.client_ip", client_ip)
            
            # Request headers (selective)
            important_headers = [
                "content-type", "content-length", "authorization",
                "x-forwarded-for", "x-real-ip", "user-agent"
            ]
            
            for header in important_headers:
                value = request.headers.get(header)
                if value:
                    # Sanitize sensitive headers
                    if header == "authorization":
                        value = value[:20] + "..." if len(value) > 20 else value
                    span.set_attribute(f"http.request.header.{header}", value)
            
            # Query parameters (sanitized)
            if request.query_params:
                query_string = str(request.query_params)
                # Sanitize sensitive parameters
                sanitized_query = self._sanitize_query_string(query_string)
                span.set_attribute("http.query_string", sanitized_query)
            
            # Path parameters
            if hasattr(request, 'path_params') and request.path_params:
                for key, value in request.path_params.items():
                    span.set_attribute(f"http.path_param.{key}", str(value))
            
            # Request ID correlation
            span.set_attribute("request.id", request_id)
            
        except Exception as e:
            logger.error(f"Failed to enrich span with request data: {e}")
    
    def _enrich_span_with_response_data(self, span, response: Response, start_time: float):
        """Add response information to span"""
        try:
            processing_time = time.time() - start_time
            
            # Response attributes
            span.set_attribute("http.status_code", response.status_code)
            span.set_attribute("http.response_time_ms", round(processing_time * 1000, 2))
            
            # Response size
            content_length = response.headers.get("content-length")
            if content_length:
                span.set_attribute("http.response_size", int(content_length))
            
            # Response headers (selective)
            important_response_headers = [
                "content-type", "content-length", "cache-control",
                "x-ratelimit-limit", "x-ratelimit-remaining"
            ]
            
            for header in important_response_headers:
                value = response.headers.get(header)
                if value:
                    span.set_attribute(f"http.response.header.{header}", value)
            
            # Status categorization
            if response.status_code >= 400:
                span.set_attribute("error", True)
                if response.status_code >= 500:
                    span.set_attribute("error.type", "server_error")
                else:
                    span.set_attribute("error.type", "client_error")
            
        except Exception as e:
            logger.error(f"Failed to enrich span with response data: {e}")
    
    async def _correlate_user_context(self, request: Request):
        """Extract and correlate user context"""
        try:
            # Try to extract user ID from different sources
            user_id = None
            
            # From JWT token (if available)
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # This would decode JWT to get user ID
                # For now, use a placeholder
                user_id = "user_from_jwt"
            
            # From session cookie
            session_id = request.cookies.get("session_id")
            if session_id:
                # This would look up user from session
                # For now, use session ID as user identifier
                user_id = f"session_{session_id[:8]}"
            
            # From custom header
            if not user_id:
                user_id = request.headers.get("x-user-id")
            
            # Correlate user with trace
            if user_id:
                await correlate_user(
                    user_id,
                    ip_address=self._get_client_ip(request),
                    user_agent=request.headers.get("user-agent", ""),
                    session_id=session_id
                )
                
        except Exception as e:
            logger.error(f"Failed to correlate user context: {e}")
    
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
    
    def _sanitize_query_string(self, query_string: str) -> str:
        """Sanitize query string to remove sensitive data"""
        sensitive_params = ['password', 'token', 'secret', 'api_key', 'auth']
        
        # Simple sanitization - in production, use more sophisticated logic
        for param in sensitive_params:
            if param in query_string.lower():
                # Replace the value with [REDACTED]
                import re
                pattern = rf'({param}=)[^&]*'
                query_string = re.sub(pattern, r'\1[REDACTED]', query_string, flags=re.IGNORECASE)
        
        return query_string[:500]  # Limit length
    
    def _add_trace_headers_to_response(self, response: Response, request_id: str):
        """Add tracing headers to response"""
        try:
            # Add request ID
            response.headers["X-Request-ID"] = request_id
            
            # Add trace ID if available
            trace_id = get_trace_id()
            if trace_id:
                response.headers["X-Trace-ID"] = trace_id
            
            # Add span ID if available
            span_id = get_span_id()
            if span_id:
                response.headers["X-Span-ID"] = span_id
            
            # Add service identification
            response.headers["X-Service-Name"] = self.service_name
            
        except Exception as e:
            logger.error(f"Failed to add trace headers to response: {e}")

class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    """Middleware for request correlation and baggage propagation"""
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        """Propagate request correlation data"""
        
        # Extract correlation data from headers
        correlation_data = self._extract_correlation_data(request)
        
        # Store in request state for later use
        request.state.correlation_data = correlation_data
        
        # Add correlation data to current span
        await self._add_correlation_to_span(correlation_data)
        
        response = await call_next(request)
        
        # Add correlation headers to response
        self._add_correlation_headers(response, correlation_data)
        
        return response
    
    def _extract_correlation_data(self, request: Request) -> Dict[str, str]:
        """Extract correlation data from request"""
        correlation_data = {}
        
        # Standard correlation headers
        correlation_headers = [
            "x-correlation-id",
            "x-request-id", 
            "x-session-id",
            "x-user-id",
            "x-tenant-id",
            "x-organization-id"
        ]
        
        for header in correlation_headers:
            value = request.headers.get(header)
            if value:
                correlation_data[header] = value
        
        return correlation_data
    
    async def _add_correlation_to_span(self, correlation_data: Dict[str, str]):
        """Add correlation data to current span"""
        try:
            # This would add the correlation data to the current span
            # For now, we'll log it
            if correlation_data:
                logger.debug(f"Request correlation data: {correlation_data}")
                
        except Exception as e:
            logger.error(f"Failed to add correlation to span: {e}")
    
    def _add_correlation_headers(self, response: Response, correlation_data: Dict[str, str]):
        """Add correlation headers to response"""
        for key, value in correlation_data.items():
            response.headers[key] = value

# Global middleware instances
tracing_middleware = TracingMiddleware
request_correlation_middleware = RequestCorrelationMiddleware