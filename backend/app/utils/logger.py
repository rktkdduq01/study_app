"""
Enhanced logger utilities for the backend application
"""
import logging
import json
from typing import Any, Dict, Optional
from datetime import datetime
from functools import wraps
import traceback

from app.core.config import settings


class StructuredLogger:
    """Logger that outputs structured JSON logs"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.is_production = settings.ENVIRONMENT == "production"
    
    def _format_log_entry(
        self,
        level: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None
    ) -> Dict[str, Any]:
        """Format log entry as structured data"""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            "logger": self.logger.name,
            "environment": settings.ENVIRONMENT
        }
        
        if context:
            entry["context"] = context
        
        if error:
            entry["error"] = {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": traceback.format_exc() if not self.is_production else None
            }
        
        return entry
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        if not self.is_production:
            entry = self._format_log_entry("DEBUG", message, kwargs)
            self.logger.debug(json.dumps(entry))
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        entry = self._format_log_entry("INFO", message, kwargs)
        self.logger.info(json.dumps(entry))
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        entry = self._format_log_entry("WARNING", message, kwargs)
        self.logger.warning(json.dumps(entry))
    
    def error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log error message"""
        entry = self._format_log_entry("ERROR", message, kwargs, error)
        self.logger.error(json.dumps(entry))
    
    def critical(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log critical message"""
        entry = self._format_log_entry("CRITICAL", message, kwargs, error)
        self.logger.critical(json.dumps(entry))


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance"""
    return StructuredLogger(name)


# Service-specific loggers
api_logger = get_logger("app.api")
service_logger = get_logger("app.services")
db_logger = get_logger("app.database")
security_logger = get_logger("app.security")
ai_logger = get_logger("app.ai")
game_logger = get_logger("app.game")


def log_api_request(func):
    """Decorator to log API requests"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request = kwargs.get('request')
        if request:
            api_logger.info(
                "API request received",
                method=request.method,
                path=str(request.url.path),
                client=request.client.host if request.client else None
            )
        
        try:
            result = await func(*args, **kwargs)
            if request:
                api_logger.info(
                    "API request completed",
                    method=request.method,
                    path=str(request.url.path),
                    status="success"
                )
            return result
        except Exception as e:
            if request:
                api_logger.error(
                    "API request failed",
                    error=e,
                    method=request.method,
                    path=str(request.url.path)
                )
            raise
    
    return wrapper


def log_service_call(service_name: str):
    """Decorator to log service method calls"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            service_logger.debug(
                f"Service call: {service_name}.{func.__name__}",
                args=args[1:] if args else None,  # Skip self
                kwargs=kwargs
            )
            
            try:
                result = await func(*args, **kwargs)
                service_logger.debug(
                    f"Service call completed: {service_name}.{func.__name__}",
                    status="success"
                )
                return result
            except Exception as e:
                service_logger.error(
                    f"Service call failed: {service_name}.{func.__name__}",
                    error=e
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            service_logger.debug(
                f"Service call: {service_name}.{func.__name__}",
                args=args[1:] if args else None,  # Skip self
                kwargs=kwargs
            )
            
            try:
                result = func(*args, **kwargs)
                service_logger.debug(
                    f"Service call completed: {service_name}.{func.__name__}",
                    status="success"
                )
                return result
            except Exception as e:
                service_logger.error(
                    f"Service call failed: {service_name}.{func.__name__}",
                    error=e
                )
                raise
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def log_db_operation(operation: str):
    """Decorator to log database operations"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            db_logger.debug(
                f"Database operation: {operation}",
                function=func.__name__
            )
            
            try:
                result = await func(*args, **kwargs)
                db_logger.debug(
                    f"Database operation completed: {operation}",
                    status="success"
                )
                return result
            except Exception as e:
                db_logger.error(
                    f"Database operation failed: {operation}",
                    error=e
                )
                raise
        
        return wrapper
    
    return decorator


# Import asyncio only when needed to avoid circular imports
import asyncio