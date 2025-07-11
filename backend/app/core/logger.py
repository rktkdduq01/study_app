"""
Structured logging configuration for the application.
"""
import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path
import traceback
from functools import wraps
import time

from app.core.config import settings


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process_id": record.process,
            "thread_id": record.thread,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add custom fields from extra
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        # Add request context if available
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        
        if hasattr(record, "ip_address"):
            log_data["ip_address"] = record.ip_address
        
        return json.dumps(log_data)


class AppLogger:
    """Application logger with structured logging support"""
    
    def __init__(self, name: str = "app"):
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Setup logger with appropriate handlers and formatters"""
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Set log level based on environment
        log_level = logging.DEBUG if settings.DEBUG else logging.INFO
        self.logger.setLevel(log_level)
        
        # Console handler with JSON formatter
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(console_handler)
        
        # File handler for errors
        error_log_path = Path("logs/error.log")
        error_log_path.parent.mkdir(exist_ok=True)
        
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(error_handler)
        
        # File handler for all logs
        app_log_path = Path("logs/app.log")
        app_handler = logging.handlers.RotatingFileHandler(
            app_log_path,
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=10
        )
        app_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(app_handler)
    
    def _log_with_context(
        self,
        level: int,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: bool = False
    ):
        """Log with additional context"""
        extra_fields = extra or {}
        
        # Add environment info
        extra_fields["environment"] = "development" if settings.DEBUG else "production"
        extra_fields["app_name"] = settings.APP_NAME
        extra_fields["app_version"] = settings.APP_VERSION
        
        self.logger.log(
            level,
            message,
            exc_info=exc_info,
            extra={"extra_fields": extra_fields}
        )
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self._log_with_context(logging.DEBUG, message, kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self._log_with_context(logging.INFO, message, kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self._log_with_context(logging.WARNING, message, kwargs)
    
    def error(self, message: str, exc_info: bool = True, **kwargs):
        """Log error message"""
        self._log_with_context(logging.ERROR, message, kwargs, exc_info=exc_info)
    
    def critical(self, message: str, exc_info: bool = True, **kwargs):
        """Log critical message"""
        self._log_with_context(logging.CRITICAL, message, kwargs, exc_info=exc_info)
    
    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration: float,
        request_id: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None
    ):
        """Log HTTP request"""
        self.info(
            f"{method} {path} - {status_code}",
            request_id=request_id,
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=round(duration * 1000, 2),
            user_id=user_id,
            ip_address=ip_address,
            log_type="http_request"
        )
    
    def log_database_query(
        self,
        query: str,
        duration: float,
        success: bool,
        error: Optional[str] = None
    ):
        """Log database query"""
        log_data = {
            "query": query[:200],  # Truncate long queries
            "duration_ms": round(duration * 1000, 2),
            "success": success,
            "log_type": "database_query"
        }
        
        if error:
            log_data["error"] = error
        
        if success:
            self.debug("Database query executed", **log_data)
        else:
            self.error("Database query failed", **log_data)
    
    def log_external_api_call(
        self,
        service: str,
        endpoint: str,
        method: str,
        status_code: Optional[int],
        duration: float,
        success: bool,
        error: Optional[str] = None
    ):
        """Log external API call"""
        log_data = {
            "service": service,
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "duration_ms": round(duration * 1000, 2),
            "success": success,
            "log_type": "external_api_call"
        }
        
        if error:
            log_data["error"] = error
        
        if success:
            self.info(f"External API call to {service}", **log_data)
        else:
            self.error(f"External API call to {service} failed", **log_data)
    
    def log_business_event(
        self,
        event_type: str,
        description: str,
        user_id: Optional[int] = None,
        data: Optional[Dict[str, Any]] = None
    ):
        """Log business event"""
        log_data = {
            "event_type": event_type,
            "user_id": user_id,
            "log_type": "business_event"
        }
        
        if data:
            log_data["event_data"] = data
        
        self.info(description, **log_data)
    
    def log_performance(
        self,
        operation: str,
        duration: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log performance metrics"""
        log_data = {
            "operation": operation,
            "duration_ms": round(duration * 1000, 2),
            "log_type": "performance"
        }
        
        if metadata:
            log_data.update(metadata)
        
        self.info(f"Performance: {operation}", **log_data)


# Global logger instance
logger = AppLogger()


def log_function_call(log_args: bool = False, log_result: bool = False):
    """Decorator to log function calls"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            function_name = f"{func.__module__}.{func.__name__}"
            
            log_data = {"function": function_name}
            if log_args:
                log_data["args"] = str(args)[:200]
                log_data["kwargs"] = str(kwargs)[:200]
            
            logger.debug(f"Calling function: {function_name}", **log_data)
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                log_data["duration_ms"] = round(duration * 1000, 2)
                log_data["success"] = True
                
                if log_result:
                    log_data["result"] = str(result)[:200]
                
                logger.debug(f"Function completed: {function_name}", **log_data)
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                log_data["duration_ms"] = round(duration * 1000, 2)
                log_data["success"] = False
                log_data["error"] = str(e)
                
                logger.error(f"Function failed: {function_name}", **log_data)
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            function_name = f"{func.__module__}.{func.__name__}"
            
            log_data = {"function": function_name}
            if log_args:
                log_data["args"] = str(args)[:200]
                log_data["kwargs"] = str(kwargs)[:200]
            
            logger.debug(f"Calling function: {function_name}", **log_data)
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                log_data["duration_ms"] = round(duration * 1000, 2)
                log_data["success"] = True
                
                if log_result:
                    log_data["result"] = str(result)[:200]
                
                logger.debug(f"Function completed: {function_name}", **log_data)
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                log_data["duration_ms"] = round(duration * 1000, 2)
                log_data["success"] = False
                log_data["error"] = str(e)
                
                logger.error(f"Function failed: {function_name}", **log_data)
                raise
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Configure third-party loggers
def configure_external_loggers():
    """Configure logging for third-party libraries"""
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("aioredis").setLevel(logging.WARNING)


# Import required modules
import asyncio
import logging.handlers