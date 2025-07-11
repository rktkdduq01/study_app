import time
import hashlib
import hmac
from typing import Optional, List, Set
from fastapi import Request, HTTPException, status
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
import re

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enhanced security headers middleware with configurable policies"""
    
    def __init__(self, app, environment: str = "development"):
        super().__init__(app)
        self.environment = environment
        self.is_production = environment == "production"
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Core security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # HSTS (only for HTTPS/production)
        if self.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        # Enhanced Permissions Policy
        permissions_policies = [
            "geolocation=()",
            "microphone=()",
            "camera=()",
            "payment=()",
            "usb=()",
            "magnetometer=()",
            "gyroscope=()",
            "speaker=()",
            "ambient-light-sensor=()",
            "accelerometer=()",
            "battery=()",
            "display-capture=()",
            "document-domain=()"
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions_policies)
        
        # Remove revealing server headers
        response.headers.pop("server", None)
        response.headers.pop("x-powered-by", None)
        
        # Enhanced Content Security Policy
        if self.is_production:
            csp_directives = [
                "default-src 'self'",
                "script-src 'self' 'nonce-${nonce}' 'strict-dynamic'",
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
                "font-src 'self' https://fonts.gstatic.com data:",
                "img-src 'self' data: https: blob:",
                "connect-src 'self' wss: https:",
                "media-src 'self'",
                "object-src 'none'",
                "frame-ancestors 'none'",
                "frame-src 'none'",
                "base-uri 'self'",
                "form-action 'self'",
                "upgrade-insecure-requests",
                "block-all-mixed-content"
            ]
        else:
            # More relaxed CSP for development
            csp_directives = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net",
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
                "font-src 'self' https://fonts.gstatic.com data:",
                "img-src 'self' data: https: blob:",
                "connect-src 'self' ws: wss: https: http:",
                "media-src 'self'",
                "object-src 'none'",
                "frame-ancestors 'none'",
                "base-uri 'self'",
                "form-action 'self'"
            ]
        
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
        
        # Security.txt reference
        response.headers["X-Security-Contact"] = "security@quest-edu.com"
        
        # Additional security headers
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        
        # Cache control for sensitive endpoints
        if any(path in request.url.path for path in ["/api/v1/auth", "/api/v1/admin", "/api/v1/users/me"]):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        return response


class SQLInjectionProtectionMiddleware(BaseHTTPMiddleware):
    """Protect against SQL injection attempts"""
    
    def __init__(self, app):
        super().__init__(app)
        # Common SQL injection patterns
        self.sql_patterns = [
            r"(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b)",
            r"(--|\#|\/\*|\*\/)",
            r"(\bor\b\s*\d+\s*=\s*\d+)",
            r"(\band\b\s*\d+\s*=\s*\d+)",
            r"(\'|\"|;|\\x00|\\n|\\r|\\x1a)",
            r"(\bwaitfor\s+delay\b)",
            r"(\bbenchmark\b)",
            r"(\bsleep\b\s*\()"
        ]
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.sql_patterns]
    
    async def dispatch(self, request: Request, call_next):
        # Check URL parameters
        if request.url.query:
            for pattern in self.compiled_patterns:
                if pattern.search(request.url.query):
                    return Response(
                        content="Potential SQL injection detected",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
        
        # Check body for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                body_text = body.decode('utf-8')
                
                for pattern in self.compiled_patterns:
                    if pattern.search(body_text):
                        return Response(
                            content="Potential SQL injection detected",
                            status_code=status.HTTP_400_BAD_REQUEST
                        )
            except:
                pass
        
        return await call_next(request)


class XSSProtectionMiddleware(BaseHTTPMiddleware):
    """Protect against XSS attacks"""
    
    def __init__(self, app):
        super().__init__(app)
        # XSS patterns
        self.xss_patterns = [
            r"<\s*script[^>]*>.*?<\s*/\s*script\s*>",
            r"javascript\s*:",
            r"on\w+\s*=",
            r"<\s*iframe[^>]*>",
            r"<\s*object[^>]*>",
            r"<\s*embed[^>]*>",
            r"<\s*link[^>]*>",
            r"eval\s*\(",
            r"expression\s*\(",
            r"vbscript\s*:",
            r"data\s*:\s*text/html"
        ]
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE | re.DOTALL) for pattern in self.xss_patterns]
    
    async def dispatch(self, request: Request, call_next):
        # Check URL parameters
        if request.url.query:
            for pattern in self.compiled_patterns:
                if pattern.search(request.url.query):
                    return Response(
                        content="Potential XSS attack detected",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
        
        # Check body for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                body_text = body.decode('utf-8')
                
                for pattern in self.compiled_patterns:
                    if pattern.search(body_text):
                        return Response(
                            content="Potential XSS attack detected",
                            status_code=status.HTTP_400_BAD_REQUEST
                        )
            except:
                pass
        
        return await call_next(request)


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Validate incoming requests"""
    
    def __init__(self, app):
        super().__init__(app)
        self.max_content_length = 10 * 1024 * 1024  # 10MB
        self.allowed_methods = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
        self.allowed_content_types = {
            "application/json",
            "application/x-www-form-urlencoded",
            "multipart/form-data",
            "text/plain"
        }
    
    async def dispatch(self, request: Request, call_next):
        # Validate HTTP method
        if request.method not in self.allowed_methods:
            return Response(
                content="Method not allowed",
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED
            )
        
        # Validate content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_content_length:
            return Response(
                content="Request entity too large",
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            )
        
        # Validate content type for requests with body
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "").split(";")[0].strip()
            if content_type and not any(allowed in content_type for allowed in self.allowed_content_types):
                return Response(
                    content="Unsupported media type",
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
                )
        
        return await call_next(request)


class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """IP whitelist middleware for admin endpoints"""
    
    def __init__(self, app, whitelist: Optional[List[str]] = None, protected_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.whitelist = set(whitelist or [])
        self.protected_paths = protected_paths or ["/admin", "/api/v1/admin"]
    
    async def dispatch(self, request: Request, call_next):
        # Check if path needs protection
        path_protected = any(request.url.path.startswith(path) for path in self.protected_paths)
        
        if path_protected and self.whitelist:
            client_ip = request.client.host
            
            # Check if IP is whitelisted
            if client_ip not in self.whitelist:
                # Also check for X-Forwarded-For header (for proxies)
                forwarded_for = request.headers.get("X-Forwarded-For")
                if forwarded_for:
                    # Get the first IP in the chain
                    real_ip = forwarded_for.split(",")[0].strip()
                    if real_ip not in self.whitelist:
                        return Response(
                            content="Access denied",
                            status_code=status.HTTP_403_FORBIDDEN
                        )
                else:
                    return Response(
                        content="Access denied",
                        status_code=status.HTTP_403_FORBIDDEN
                    )
        
        return await call_next(request)


class APIKeyMiddleware(BaseHTTPMiddleware):
    """API key validation for certain endpoints"""
    
    def __init__(self, app, protected_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.protected_paths = protected_paths or ["/api/v1/webhook", "/api/v1/internal"]
    
    async def dispatch(self, request: Request, call_next):
        # Check if path needs API key
        path_protected = any(request.url.path.startswith(path) for path in self.protected_paths)
        
        if path_protected:
            api_key = request.headers.get("X-API-Key")
            
            if not api_key:
                return Response(
                    content="API key required",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            
            # Validate API key (in production, check against database)
            valid_api_key = settings.INTERNAL_API_KEY if hasattr(settings, 'INTERNAL_API_KEY') else None
            if not valid_api_key or api_key != valid_api_key:
                return Response(
                    content="Invalid API key",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
        
        return await call_next(request)


class EnhancedCORSMiddleware(BaseHTTPMiddleware):
    """Enhanced CORS middleware with origin validation and security features"""
    
    def __init__(
        self, 
        app,
        allowed_origins: Optional[List[str]] = None,
        allowed_methods: Optional[List[str]] = None,
        allowed_headers: Optional[List[str]] = None,
        environment: str = "development"
    ):
        super().__init__(app)
        self.environment = environment
        self.is_production = environment == "production"
        
        # Configure allowed origins based on environment
        if allowed_origins is None:
            if self.is_production:
                # Production: strict origin control
                self.allowed_origins = set([
                    "https://quest-edu.com",
                    "https://www.quest-edu.com",
                    "https://app.quest-edu.com"
                ])
            elif environment == "staging":
                # Staging: controlled testing origins
                self.allowed_origins = set([
                    "https://staging.quest-edu.com",
                    "https://staging-app.quest-edu.com",
                    "http://localhost:3000",
                    "http://localhost:5173"
                ])
            else:
                # Development: local development origins
                self.allowed_origins = set([
                    "http://localhost:3000",
                    "http://localhost:5173",
                    "http://localhost:8080",
                    "http://127.0.0.1:3000",
                    "http://127.0.0.1:5173",
                    "http://127.0.0.1:8080"
                ])
        else:
            self.allowed_origins = set(allowed_origins)
        
        # Configure allowed methods
        self.allowed_methods = set(allowed_methods or [
            "GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"
        ])
        
        # Configure allowed headers
        self.allowed_headers = set(allowed_headers or [
            "Authorization",
            "Content-Type",
            "X-Requested-With",
            "X-API-Key",
            "X-Client-Version",
            "Accept",
            "Accept-Language",
            "Cache-Control"
        ])
        
        # Exposed headers
        self.expose_headers = [
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
            "X-Total-Count",
            "X-Page-Count"
        ]
        
        self.max_age = 3600 if self.is_production else 86400
    
    def _is_origin_allowed(self, origin: str) -> bool:
        """Validate if origin is allowed with enhanced security checks"""
        if not origin:
            return False
        
        # Check against allowed origins
        if origin in self.allowed_origins:
            return True
        
        # In development, allow wildcard for localhost
        if not self.is_production:
            # Allow any localhost/127.0.0.1 with common ports in development
            import re
            localhost_pattern = r'^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$'
            if re.match(localhost_pattern, origin):
                return True
        
        return False
    
    def _validate_request_headers(self, headers: dict) -> bool:
        """Validate request headers for security"""
        # Check for suspicious headers
        suspicious_headers = ['x-forwarded-host', 'x-real-ip']
        for header in suspicious_headers:
            if header in headers and self.is_production:
                # In production, be more strict about proxy headers
                return False
        
        return True
    
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        method = request.method
        
        # Validate request headers
        if not self._validate_request_headers(dict(request.headers)):
            return Response(
                content="Invalid request headers",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Handle preflight requests
        if method == "OPTIONS":
            # Validate origin for preflight
            if origin and not self._is_origin_allowed(origin):
                return Response(
                    content="Origin not allowed",
                    status_code=status.HTTP_403_FORBIDDEN
                )
            
            # Check requested method
            requested_method = request.headers.get("access-control-request-method")
            if requested_method and requested_method not in self.allowed_methods:
                return Response(
                    content="Method not allowed",
                    status_code=status.HTTP_405_METHOD_NOT_ALLOWED
                )
            
            # Check requested headers
            requested_headers = request.headers.get("access-control-request-headers", "")
            if requested_headers:
                requested_header_list = [h.strip().lower() for h in requested_headers.split(",")]
                for header in requested_header_list:
                    if header not in {h.lower() for h in self.allowed_headers}:
                        return Response(
                            content="Header not allowed",
                            status_code=status.HTTP_403_FORBIDDEN
                        )
            
            # Create preflight response
            response = Response(status_code=status.HTTP_200_OK)
            
            # Set CORS headers
            if origin:
                response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allowed_methods)
            response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allowed_headers)
            response.headers["Access-Control-Max-Age"] = str(self.max_age)
            response.headers["Access-Control-Allow-Credentials"] = "true"
            
            return response
        
        # Handle actual request
        response = await call_next(request)
        
        # Validate origin for actual requests
        if origin:
            if self._is_origin_allowed(origin):
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
            else:
                # Origin not allowed - don't set CORS headers
                # This will cause browser to block the response
                pass
        
        # Set additional CORS headers
        response.headers["Access-Control-Expose-Headers"] = ", ".join(self.expose_headers)
        response.headers["Vary"] = "Origin"
        
        return response


def create_cors_middleware(
    allowed_origins: Optional[List[str]] = None,
    allowed_methods: Optional[List[str]] = None,
    allowed_headers: Optional[List[str]] = None,
    environment: str = "development"
) -> EnhancedCORSMiddleware:
    """Create enhanced CORS middleware with secure defaults"""
    
    return EnhancedCORSMiddleware(
        app=None,  # Will be set by FastAPI
        allowed_origins=allowed_origins,
        allowed_methods=allowed_methods,
        allowed_headers=allowed_headers,
        environment=environment
    )