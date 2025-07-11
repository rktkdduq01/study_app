"""
Security Configuration Module
Centralized security settings and policies
"""

import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Environment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

@dataclass
class CORSConfig:
    """CORS configuration settings"""
    allowed_origins: List[str] = field(default_factory=list)
    allowed_methods: List[str] = field(default_factory=lambda: [
        "GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"
    ])
    allowed_headers: List[str] = field(default_factory=lambda: [
        "Authorization", "Content-Type", "X-Requested-With", 
        "X-API-Key", "X-Client-Version", "Accept", "Accept-Language", "Cache-Control"
    ])
    expose_headers: List[str] = field(default_factory=lambda: [
        "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset",
        "X-Total-Count", "X-Page-Count"
    ])
    allow_credentials: bool = True
    max_age: int = 3600

@dataclass
class CSPConfig:
    """Content Security Policy configuration"""
    default_src: List[str] = field(default_factory=lambda: ["'self'"])
    script_src: List[str] = field(default_factory=list)
    style_src: List[str] = field(default_factory=lambda: ["'self'", "'unsafe-inline'"])
    img_src: List[str] = field(default_factory=lambda: ["'self'", "data:", "https:", "blob:"])
    font_src: List[str] = field(default_factory=lambda: ["'self'", "data:"])
    connect_src: List[str] = field(default_factory=list)
    media_src: List[str] = field(default_factory=lambda: ["'self'"])
    object_src: List[str] = field(default_factory=lambda: ["'none'"])
    frame_ancestors: List[str] = field(default_factory=lambda: ["'none'"])
    frame_src: List[str] = field(default_factory=lambda: ["'none'"])
    base_uri: List[str] = field(default_factory=lambda: ["'self'"])
    form_action: List[str] = field(default_factory=lambda: ["'self'"])
    upgrade_insecure_requests: bool = False
    block_all_mixed_content: bool = False

@dataclass
class SecurityHeadersConfig:
    """Security headers configuration"""
    x_content_type_options: str = "nosniff"
    x_frame_options: str = "DENY"
    x_xss_protection: str = "1; mode=block"
    referrer_policy: str = "strict-origin-when-cross-origin"
    strict_transport_security: Optional[str] = None
    permissions_policy: Dict[str, List[str]] = field(default_factory=lambda: {
        "geolocation": [],
        "microphone": [],
        "camera": [],
        "payment": [],
        "usb": [],
        "magnetometer": [],
        "gyroscope": [],
        "speaker": [],
        "ambient-light-sensor": [],
        "accelerometer": [],
        "battery": [],
        "display-capture": [],
        "document-domain": []
    })
    cross_origin_embedder_policy: str = "require-corp"
    cross_origin_opener_policy: str = "same-origin"
    cross_origin_resource_policy: str = "same-origin"

@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    enabled: bool = True
    default_limit: str = "100/hour"
    auth_limit: str = "5/minute"
    api_limit: str = "1000/hour"
    admin_limit: str = "50/hour"
    burst_limit: int = 10
    storage_backend: str = "redis"

@dataclass
class AuthConfig:
    """Authentication and authorization configuration"""
    jwt_algorithm: str = "HS256"
    jwt_expiration_delta: int = 3600  # 1 hour
    jwt_refresh_expiration_delta: int = 604800  # 7 days
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_special: bool = True
    max_login_attempts: int = 5
    lockout_duration: int = 900  # 15 minutes
    session_timeout: int = 1800  # 30 minutes
    require_email_verification: bool = True
    enable_2fa: bool = False

@dataclass
class InputValidationConfig:
    """Input validation and sanitization configuration"""
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    max_json_depth: int = 10
    max_array_length: int = 1000
    max_string_length: int = 10000
    allowed_content_types: List[str] = field(default_factory=lambda: [
        "application/json",
        "application/x-www-form-urlencoded",
        "multipart/form-data",
        "text/plain"
    ])
    enable_sql_injection_protection: bool = True
    enable_xss_protection: bool = True
    enable_path_traversal_protection: bool = True

@dataclass
class SecurityMonitoringConfig:
    """Security monitoring and logging configuration"""
    enable_security_logs: bool = True
    log_failed_authentications: bool = True
    log_suspicious_requests: bool = True
    log_admin_actions: bool = True
    alert_on_multiple_failures: bool = True
    failure_threshold: int = 10
    alert_email: Optional[str] = None
    enable_honeypots: bool = False

class SecurityConfigManager:
    """Centralized security configuration manager"""
    
    def __init__(self, environment: Environment = Environment.DEVELOPMENT):
        self.environment = environment
        self._load_configuration()
    
    def _load_configuration(self):
        """Load security configuration based on environment"""
        if self.environment == Environment.PRODUCTION:
            self._load_production_config()
        elif self.environment == Environment.STAGING:
            self._load_staging_config()
        else:
            self._load_development_config()
    
    def _load_production_config(self):
        """Production security configuration - maximum security"""
        self.cors = CORSConfig(
            allowed_origins=[
                "https://quest-edu.com",
                "https://www.quest-edu.com",
                "https://app.quest-edu.com"
            ],
            max_age=3600
        )
        
        self.csp = CSPConfig(
            script_src=["'self'", "'nonce-{nonce}'", "'strict-dynamic'"],
            connect_src=["'self'", "wss:", "https:"],
            upgrade_insecure_requests=True,
            block_all_mixed_content=True
        )
        
        self.security_headers = SecurityHeadersConfig(
            strict_transport_security="max-age=31536000; includeSubDomains; preload"
        )
        
        self.rate_limiting = RateLimitConfig(
            default_limit="50/hour",
            auth_limit="3/minute",
            api_limit="500/hour"
        )
        
        self.auth = AuthConfig(
            jwt_expiration_delta=1800,  # 30 minutes
            password_min_length=12,
            enable_2fa=True,
            max_login_attempts=3,
            lockout_duration=3600  # 1 hour
        )
        
        self.input_validation = InputValidationConfig(
            max_request_size=5 * 1024 * 1024,  # 5MB
            max_json_depth=5,
            max_array_length=500
        )
        
        self.monitoring = SecurityMonitoringConfig(
            alert_on_multiple_failures=True,
            failure_threshold=5,
            enable_honeypots=True
        )
    
    def _load_staging_config(self):
        """Staging security configuration - production-like with some relaxations"""
        self.cors = CORSConfig(
            allowed_origins=[
                "https://staging.quest-edu.com",
                "https://staging-app.quest-edu.com",
                "http://localhost:3000",
                "http://localhost:5173"
            ]
        )
        
        self.csp = CSPConfig(
            script_src=["'self'", "'unsafe-inline'", "'unsafe-eval'"],
            connect_src=["'self'", "ws:", "wss:", "https:", "http:"],
            upgrade_insecure_requests=False
        )
        
        self.security_headers = SecurityHeadersConfig(
            strict_transport_security="max-age=86400; includeSubDomains"
        )
        
        self.rate_limiting = RateLimitConfig(
            default_limit="200/hour",
            auth_limit="10/minute"
        )
        
        self.auth = AuthConfig(
            jwt_expiration_delta=3600,  # 1 hour
            enable_2fa=False,
            max_login_attempts=5
        )
        
        self.input_validation = InputValidationConfig()
        
        self.monitoring = SecurityMonitoringConfig(
            enable_honeypots=False
        )
    
    def _load_development_config(self):
        """Development security configuration - relaxed for development ease"""
        self.cors = CORSConfig(
            allowed_origins=[
                "http://localhost:3000",
                "http://localhost:5173",
                "http://localhost:8080",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173",
                "http://127.0.0.1:8080"
            ],
            max_age=86400
        )
        
        self.csp = CSPConfig(
            script_src=["'self'", "'unsafe-inline'", "'unsafe-eval'", "https://cdn.jsdelivr.net"],
            style_src=["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
            font_src=["'self'", "https://fonts.gstatic.com", "data:"],
            connect_src=["'self'", "ws:", "wss:", "https:", "http:"]
        )
        
        self.security_headers = SecurityHeadersConfig()
        
        self.rate_limiting = RateLimitConfig(
            enabled=False  # Disabled in development
        )
        
        self.auth = AuthConfig(
            jwt_expiration_delta=86400,  # 24 hours
            password_min_length=6,
            password_require_special=False,
            enable_2fa=False,
            max_login_attempts=10
        )
        
        self.input_validation = InputValidationConfig(
            max_request_size=50 * 1024 * 1024,  # 50MB for development
            enable_sql_injection_protection=False,  # Can interfere with testing
            enable_xss_protection=False
        )
        
        self.monitoring = SecurityMonitoringConfig(
            enable_security_logs=False,
            enable_honeypots=False
        )
    
    def get_csp_header_value(self) -> str:
        """Generate CSP header value from configuration"""
        directives = []
        
        if self.csp.default_src:
            directives.append(f"default-src {' '.join(self.csp.default_src)}")
        if self.csp.script_src:
            directives.append(f"script-src {' '.join(self.csp.script_src)}")
        if self.csp.style_src:
            directives.append(f"style-src {' '.join(self.csp.style_src)}")
        if self.csp.img_src:
            directives.append(f"img-src {' '.join(self.csp.img_src)}")
        if self.csp.font_src:
            directives.append(f"font-src {' '.join(self.csp.font_src)}")
        if self.csp.connect_src:
            directives.append(f"connect-src {' '.join(self.csp.connect_src)}")
        if self.csp.media_src:
            directives.append(f"media-src {' '.join(self.csp.media_src)}")
        if self.csp.object_src:
            directives.append(f"object-src {' '.join(self.csp.object_src)}")
        if self.csp.frame_ancestors:
            directives.append(f"frame-ancestors {' '.join(self.csp.frame_ancestors)}")
        if self.csp.frame_src:
            directives.append(f"frame-src {' '.join(self.csp.frame_src)}")
        if self.csp.base_uri:
            directives.append(f"base-uri {' '.join(self.csp.base_uri)}")
        if self.csp.form_action:
            directives.append(f"form-action {' '.join(self.csp.form_action)}")
        
        if self.csp.upgrade_insecure_requests:
            directives.append("upgrade-insecure-requests")
        if self.csp.block_all_mixed_content:
            directives.append("block-all-mixed-content")
        
        return "; ".join(directives)
    
    def get_permissions_policy_header_value(self) -> str:
        """Generate Permissions Policy header value from configuration"""
        policies = []
        for permission, origins in self.security_headers.permissions_policy.items():
            if not origins:
                policies.append(f"{permission}=()")
            else:
                origin_list = " ".join(f'"{origin}"' for origin in origins)
                policies.append(f"{permission}=({origin_list})")
        
        return ", ".join(policies)
    
    def is_origin_allowed(self, origin: str) -> bool:
        """Check if origin is allowed by CORS policy"""
        if not origin:
            return False
        
        return origin in self.cors.allowed_origins
    
    def get_security_level(self) -> SecurityLevel:
        """Get current security level based on environment"""
        if self.environment == Environment.PRODUCTION:
            return SecurityLevel.CRITICAL
        elif self.environment == Environment.STAGING:
            return SecurityLevel.HIGH
        else:
            return SecurityLevel.MEDIUM

# Global security configuration instance
security_config = SecurityConfigManager(
    Environment(os.getenv("ENVIRONMENT", "development"))
)