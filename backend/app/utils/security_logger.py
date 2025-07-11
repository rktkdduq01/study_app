import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import Request
from sqlalchemy.orm import Session

from app.models.user import User


class SecurityLogger:
    """Security event logger"""
    
    def __init__(self, name: str = "security"):
        self.logger = logging.getLogger(name)
        handler = logging.FileHandler("logs/security.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def _create_log_entry(
        self,
        event_type: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create standardized log entry"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "ip_address": ip_address,
            "details": details or {}
        }
    
    def log_login_attempt(
        self,
        email: str,
        ip_address: str,
        success: bool,
        reason: Optional[str] = None
    ):
        """Log login attempt"""
        entry = self._create_log_entry(
            event_type="login_attempt",
            ip_address=ip_address,
            details={
                "email": email,
                "success": success,
                "reason": reason
            }
        )
        
        if success:
            self.logger.info(json.dumps(entry))
        else:
            self.logger.warning(json.dumps(entry))
    
    def log_logout(self, user_id: int, ip_address: str):
        """Log user logout"""
        entry = self._create_log_entry(
            event_type="logout",
            user_id=user_id,
            ip_address=ip_address
        )
        self.logger.info(json.dumps(entry))
    
    def log_token_refresh(self, user_id: int, ip_address: str):
        """Log token refresh"""
        entry = self._create_log_entry(
            event_type="token_refresh",
            user_id=user_id,
            ip_address=ip_address
        )
        self.logger.info(json.dumps(entry))
    
    def log_password_change(
        self,
        user_id: int,
        ip_address: str,
        success: bool
    ):
        """Log password change attempt"""
        entry = self._create_log_entry(
            event_type="password_change",
            user_id=user_id,
            ip_address=ip_address,
            details={"success": success}
        )
        
        if success:
            self.logger.info(json.dumps(entry))
        else:
            self.logger.warning(json.dumps(entry))
    
    def log_unauthorized_access(
        self,
        ip_address: str,
        path: str,
        method: str,
        user_id: Optional[int] = None
    ):
        """Log unauthorized access attempt"""
        entry = self._create_log_entry(
            event_type="unauthorized_access",
            user_id=user_id,
            ip_address=ip_address,
            details={
                "path": path,
                "method": method
            }
        )
        self.logger.warning(json.dumps(entry))
    
    def log_rate_limit_exceeded(
        self,
        ip_address: str,
        path: str,
        user_id: Optional[int] = None
    ):
        """Log rate limit exceeded"""
        entry = self._create_log_entry(
            event_type="rate_limit_exceeded",
            user_id=user_id,
            ip_address=ip_address,
            details={"path": path}
        )
        self.logger.warning(json.dumps(entry))
    
    def log_suspicious_activity(
        self,
        ip_address: str,
        activity_type: str,
        details: Dict[str, Any],
        user_id: Optional[int] = None
    ):
        """Log suspicious activity"""
        entry = self._create_log_entry(
            event_type="suspicious_activity",
            user_id=user_id,
            ip_address=ip_address,
            details={
                "activity_type": activity_type,
                **details
            }
        )
        self.logger.warning(json.dumps(entry))
    
    def log_data_access(
        self,
        user_id: int,
        resource_type: str,
        resource_id: Any,
        action: str,
        ip_address: str
    ):
        """Log sensitive data access"""
        entry = self._create_log_entry(
            event_type="data_access",
            user_id=user_id,
            ip_address=ip_address,
            details={
                "resource_type": resource_type,
                "resource_id": str(resource_id),
                "action": action
            }
        )
        self.logger.info(json.dumps(entry))
    
    def log_permission_denied(
        self,
        user_id: int,
        resource: str,
        permission: str,
        ip_address: str
    ):
        """Log permission denied"""
        entry = self._create_log_entry(
            event_type="permission_denied",
            user_id=user_id,
            ip_address=ip_address,
            details={
                "resource": resource,
                "permission": permission
            }
        )
        self.logger.warning(json.dumps(entry))
    
    def log_api_key_usage(
        self,
        api_key_id: str,
        ip_address: str,
        path: str,
        success: bool
    ):
        """Log API key usage"""
        entry = self._create_log_entry(
            event_type="api_key_usage",
            ip_address=ip_address,
            details={
                "api_key_id": api_key_id,
                "path": path,
                "success": success
            }
        )
        self.logger.info(json.dumps(entry))


# Global security logger instance
security_logger = SecurityLogger()


def get_client_ip(request: Request) -> str:
    """Get client IP address from request"""
    # Check for X-Forwarded-For header (proxy/load balancer)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Get the first IP in the chain
        return forwarded_for.split(",")[0].strip()
    
    # Check for X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct client IP
    return request.client.host if request.client else "unknown"


class AuditLogEntry:
    """Database model for audit logs"""
    
    @staticmethod
    def create_audit_log(
        db: Session,
        user_id: int,
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ):
        """Create an audit log entry in database"""
        # This would create an entry in an audit_logs table
        # Implementation depends on your database schema
        pass