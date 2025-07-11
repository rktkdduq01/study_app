"""
Logging configuration for the application
"""
import logging
import logging.config
import os
from typing import Dict, Any

from app.core.config import settings


def get_logging_config() -> Dict[str, Any]:
    """
    Get logging configuration dictionary.
    
    Returns:
        Logging configuration dict
    """
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "security": {
                "format": "%(asctime)s - SECURITY - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "default",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": f"{log_dir}/app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8",
            },
            "security_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "security",
                "filename": f"{log_dir}/security.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 10,
                "encoding": "utf8",
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": f"{log_dir}/error.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 10,
                "encoding": "utf8",
            },
        },
        "loggers": {
            "app": {
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "app.core.security": {
                "level": "INFO",
                "handlers": ["console", "security_file"],
                "propagate": False,
            },
            "app.api.deps": {
                "level": "INFO",
                "handlers": ["console", "security_file"],
                "propagate": False,
            },
            "app.core.exceptions": {
                "level": "INFO",
                "handlers": ["console", "error_file"],
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["console", "error_file"],
                "level": "INFO",
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "handlers": ["file"],
                "level": "WARNING",
                "propagate": False,
            },
        },
        "root": {
            "level": "INFO",
            "handlers": ["console", "file"],
        },
    }


def setup_logging():
    """Set up logging configuration"""
    config = get_logging_config()
    logging.config.dictConfig(config)
    
    # Log startup
    logger = logging.getLogger("app")
    logger.info("Logging configuration initialized")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Log level: {settings.LOG_LEVEL}")


# Security event logger
security_logger = logging.getLogger("app.core.security")


def log_security_event(event_type: str, details: Dict[str, Any], level: str = "INFO"):
    """
    Log a security event.
    
    Args:
        event_type: Type of security event
        details: Event details
        level: Log level (INFO, WARNING, ERROR)
    """
    message = f"Security Event: {event_type} - {details}"
    
    if level == "WARNING":
        security_logger.warning(message)
    elif level == "ERROR":
        security_logger.error(message)
    else:
        security_logger.info(message)