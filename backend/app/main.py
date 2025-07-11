from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import socketio

from app.core.config import settings
from app.core.database import engine, Base
from app.core.logging_config import setup_logging
from app.api.v1.router import api_router
from app.websocket.manager import websocket_manager
from app.middleware.security import (
    SecurityMiddleware,
    IPWhitelistMiddleware,
    RateLimitMiddleware as EnhancedRateLimitMiddleware,
    XSSProtectionMiddleware as EnhancedXSSProtectionMiddleware,
    setup_cors
)
from app.middleware import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    SQLInjectionProtectionMiddleware,
    XSSProtectionMiddleware,
    RequestValidationMiddleware,
    create_cors_middleware
)
from app.middleware.error_handler import error_handler_middleware, create_exception_handlers
from app.middleware.logging_middleware import (
    LoggingMiddleware,
    PerformanceLoggingMiddleware,
    AuditLoggingMiddleware
)
from app.core.logger import logger, configure_external_loggers
from app.core.i18n_middleware import I18nMiddleware

# Configure external loggers
configure_external_loggers()

# Setup application logging
setup_logging()

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Educational RPG platform that gamifies learning",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json"
)

# Register exception handlers
create_exception_handlers(app)

# Add security middlewares (order matters - executed in reverse order)

# 1. CORS middleware (should be last to be added, first to execute)
setup_cors(app)

# 2. GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 3. Enhanced Security Middleware
app.add_middleware(SecurityMiddleware)

# 4. IP Whitelist for admin endpoints
if hasattr(settings, 'ADMIN_IP_WHITELIST'):
    app.add_middleware(
        IPWhitelistMiddleware,
        whitelist=settings.ADMIN_IP_WHITELIST
    )

# 5. Trusted host middleware
if hasattr(settings, 'ALLOWED_HOSTS'):
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# 6. Security headers
app.add_middleware(SecurityHeadersMiddleware)

# 7. Request validation
app.add_middleware(RequestValidationMiddleware)

# 8. Enhanced XSS protection
app.add_middleware(EnhancedXSSProtectionMiddleware)

# 9. SQL injection protection
app.add_middleware(SQLInjectionProtectionMiddleware)

# 10. Enhanced Rate limiting
app.add_middleware(
    EnhancedRateLimitMiddleware,
    requests_per_minute=settings.RATE_LIMIT_PER_MINUTE if hasattr(settings, 'RATE_LIMIT_PER_MINUTE') else 60
)

# 11. I18n middleware
app.add_middleware(I18nMiddleware)

# 12. Logging middlewares
app.add_middleware(
    AuditLoggingMiddleware,
    audit_paths=["/api/v1/users", "/api/v1/auth", "/api/v1/admin"],
    audit_methods=["POST", "PUT", "PATCH", "DELETE"]
)

app.add_middleware(
    PerformanceLoggingMiddleware,
    slow_request_threshold=1.0,
    log_all_requests=settings.DEBUG
)

app.add_middleware(
    LoggingMiddleware,
    log_request_body=settings.DEBUG,
    log_response_body=False,
    exclude_paths=["/health", "/metrics", "/docs", "/openapi.json"],
    sensitive_fields=["password", "token", "secret", "api_key", "authorization"]
)

# 13. Error handler middleware (should be one of the first middleware added)
app.middleware("http")(error_handler_middleware)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to EduRPG API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info(
        "Application starting up",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment="development" if settings.DEBUG else "production"
    )
    
    # Start analytics services
    from app.services.data_aggregation import data_aggregation_service
    from app.services.analytics_websocket import analytics_websocket_manager
    
    data_aggregation_service.start()
    await analytics_websocket_manager.start_analytics_stream()
    
    logger.info("Analytics services started")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("Application shutting down")
    
    # Stop analytics services
    from app.services.data_aggregation import data_aggregation_service
    from app.services.analytics_websocket import analytics_websocket_manager
    
    data_aggregation_service.stop()
    await analytics_websocket_manager.stop_analytics_stream()
    
    logger.info("Analytics services stopped")


# Mount Socket.IO app
app.mount("/ws", websocket_manager.get_app())