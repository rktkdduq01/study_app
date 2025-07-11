"""
Enhanced Security Audit and Monitoring System
Comprehensive security event logging, threat detection, and monitoring
"""
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta, timezone
from fastapi import Request, HTTPException
from sqlalchemy.orm import Session
import hashlib
import hmac
import secrets
import re
from ipaddress import ip_address, ip_network
import asyncio
from collections import defaultdict
import json
import os
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, asdict
import geoip2.database
import geoip2.errors

from app.core.logger import get_logger
from app.core.config import settings
from app.models.user import User
from app.core.redis_client import redis_client

logger = get_logger(__name__)

class SecurityEventType(Enum):
    """Types of security events for detailed categorization"""
    AUTHENTICATION_SUCCESS = "auth_success"
    AUTHENTICATION_FAILURE = "auth_failure"
    AUTHORIZATION_FAILURE = "authz_failure"
    SUSPICIOUS_REQUEST = "suspicious_request"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    XSS_ATTEMPT = "xss_attempt"
    CSRF_ATTEMPT = "csrf_attempt"
    BRUTE_FORCE_ATTEMPT = "brute_force_attempt"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    ADMIN_ACTION = "admin_action"
    SECURITY_POLICY_VIOLATION = "security_policy_violation"
    VULNERABILITY_SCAN = "vulnerability_scan"
    MALICIOUS_USER_AGENT = "malicious_user_agent"
    IP_REPUTATION_THREAT = "ip_reputation_threat"
    PASSWORD_BREACH_DETECTED = "password_breach_detected"

class SeverityLevel(Enum):
    """Security event severity levels"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityEvent:
    """Enhanced security event data structure"""
    event_id: str
    timestamp: datetime
    event_type: SecurityEventType
    severity: SeverityLevel
    user_id: Optional[str]
    session_id: Optional[str]
    ip_address: str
    user_agent: str
    request_path: str
    request_method: str
    response_status: Optional[int]
    details: Dict[str, Any]
    geolocation: Optional[Dict[str, str]]
    risk_score: int
    tags: List[str]
    correlation_id: Optional[str]


class SecurityAudit:
    """Security audit and monitoring system"""
    
    def __init__(self):
        self.suspicious_patterns = [
            r"(?i)(union\s+select|select\s+\*|drop\s+table|insert\s+into|delete\s+from)",  # SQL injection
            r"(?i)(<script|javascript:|onerror=|onload=|onclick=)",  # XSS attempts
            r"(?i)(\.\.\/|\.\.\\|%2e%2e)",  # Path traversal
            r"(?i)(eval\(|exec\(|system\(|passthru\()",  # Code injection
            r"(?i)(base64_decode|convert\.from|hex2bin)",  # Encoding attacks
        ]
        
        self.blocked_ips = set()
        self.failed_attempts = defaultdict(list)
        self.request_history = defaultdict(list)
        
    async def audit_request(self, request: Request) -> Dict[str, Any]:
        """Audit incoming request for security threats"""
        audit_result = {
            "timestamp": datetime.utcnow(),
            "ip": self._get_client_ip(request),
            "path": request.url.path,
            "method": request.method,
            "threats": [],
            "risk_score": 0
        }
        
        # Check if IP is blocked
        if audit_result["ip"] in self.blocked_ips:
            audit_result["threats"].append("blocked_ip")
            audit_result["risk_score"] = 100
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Check request patterns
        threats = await self._check_request_patterns(request)
        audit_result["threats"].extend(threats)
        
        # Check rate limiting
        if await self._check_rate_limit_violation(audit_result["ip"], request.url.path):
            audit_result["threats"].append("rate_limit_violation")
            audit_result["risk_score"] += 30
        
        # Check authentication failures
        if self._check_auth_failures(audit_result["ip"]):
            audit_result["threats"].append("multiple_auth_failures")
            audit_result["risk_score"] += 40
        
        # Calculate final risk score
        audit_result["risk_score"] += len(threats) * 20
        
        # Log high-risk requests
        if audit_result["risk_score"] >= 50:
            logger.warning(f"High-risk request detected: {audit_result}")
            await self._handle_security_threat(audit_result)
        
        # Store audit log
        await self._store_audit_log(audit_result)
        
        return audit_result
    
    async def _check_request_patterns(self, request: Request) -> List[str]:
        """Check request for suspicious patterns"""
        threats = []
        
        # Check URL parameters
        if request.url.query:
            for pattern in self.suspicious_patterns:
                if re.search(pattern, request.url.query):
                    threats.append(f"suspicious_query_pattern:{pattern}")
        
        # Check headers
        suspicious_headers = ["X-Forwarded-Host", "X-Original-URL", "X-Rewrite-URL"]
        for header in suspicious_headers:
            if header in request.headers:
                threats.append(f"suspicious_header:{header}")
        
        # Check user agent
        user_agent = request.headers.get("user-agent", "")
        if self._is_malicious_user_agent(user_agent):
            threats.append("malicious_user_agent")
        
        # Check request body for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                body_str = body.decode('utf-8')
                for pattern in self.suspicious_patterns:
                    if re.search(pattern, body_str):
                        threats.append(f"suspicious_body_pattern:{pattern}")
            except:
                pass
        
        return threats
    
    def _is_malicious_user_agent(self, user_agent: str) -> bool:
        """Check if user agent is known malicious bot"""
        malicious_agents = [
            "sqlmap", "nikto", "havij", "brutus", "metasploit",
            "arachni", "dirbuster", "nessus", "openvas", "w3af"
        ]
        return any(agent in user_agent.lower() for agent in malicious_agents)
    
    async def _check_rate_limit_violation(self, ip: str, path: str) -> bool:
        """Check if IP has violated rate limits"""
        key = f"security:rate_limit:{ip}:{path}"
        count = await redis_client.incr(key)
        
        if count == 1:
            await redis_client.expire(key, 60)  # 1 minute window
        
        # Different limits for different endpoints
        limits = {
            "/api/v1/auth": 5,
            "/api/v1/login": 5,
            "/api/v1/register": 3,
            "default": 60
        }
        
        limit = limits.get(path, limits["default"])
        return count > limit
    
    def _check_auth_failures(self, ip: str) -> bool:
        """Check if IP has multiple authentication failures"""
        failures = self.failed_attempts.get(ip, [])
        recent_failures = [f for f in failures if f > datetime.utcnow() - timedelta(minutes=15)]
        self.failed_attempts[ip] = recent_failures
        return len(recent_failures) >= 5
    
    def _get_client_ip(self, request: Request) -> str:
        """Get real client IP considering proxies"""
        # Check X-Forwarded-For header
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Get the first IP in the chain
            return forwarded.split(",")[0].strip()
        
        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct connection
        return request.client.host
    
    async def _handle_security_threat(self, audit_result: Dict[str, Any]):
        """Handle detected security threat"""
        ip = audit_result["ip"]
        risk_score = audit_result["risk_score"]
        
        # Auto-block high-risk IPs
        if risk_score >= 80:
            self.blocked_ips.add(ip)
            await redis_client.sadd("security:blocked_ips", ip)
            logger.error(f"IP {ip} blocked due to high risk score: {risk_score}")
        
        # Send alert for medium-risk
        if risk_score >= 60:
            await self._send_security_alert(audit_result)
    
    async def _send_security_alert(self, audit_result: Dict[str, Any]):
        """Send security alert to monitoring system"""
        alert = {
            "type": "security_threat",
            "severity": "high" if audit_result["risk_score"] >= 80 else "medium",
            "details": audit_result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send to monitoring queue
        await redis_client.lpush("security:alerts", json.dumps(alert))
        
        # Log alert
        logger.error(f"Security alert: {alert}")
    
    async def _store_audit_log(self, audit_result: Dict[str, Any]):
        """Store audit log for analysis"""
        key = f"security:audit:{datetime.utcnow().strftime('%Y%m%d')}"
        await redis_client.lpush(key, json.dumps(audit_result, default=str))
        await redis_client.expire(key, 86400 * 30)  # Keep for 30 days
    
    async def record_auth_failure(self, ip: str, username: Optional[str] = None):
        """Record authentication failure"""
        self.failed_attempts[ip].append(datetime.utcnow())
        
        # Store in Redis for persistence
        key = f"security:auth_failures:{ip}"
        await redis_client.zadd(key, {str(datetime.utcnow()): datetime.utcnow().timestamp()})
        await redis_client.expire(key, 3600)  # 1 hour
        
        # Check if we should block the IP
        if len(self.failed_attempts[ip]) >= 10:
            self.blocked_ips.add(ip)
            await redis_client.sadd("security:blocked_ips", ip)
            logger.warning(f"IP {ip} blocked due to multiple auth failures")
    
    async def check_password_breach(self, password: str) -> bool:
        """Check if password has been in a data breach using k-anonymity"""
        # Hash password with SHA-1 (as used by HaveIBeenPwned)
        sha1_hash = hashlib.sha1(password.encode()).hexdigest().upper()
        prefix = sha1_hash[:5]
        suffix = sha1_hash[5:]
        
        try:
            # Query HaveIBeenPwned API
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.pwnedpasswords.com/range/{prefix}",
                    headers={"User-Agent": "Educational-RPG-Security-Check"}
                )
                
                if response.status_code == 200:
                    # Check if our hash suffix is in the response
                    for line in response.text.splitlines():
                        hash_suffix, count = line.split(":")
                        if hash_suffix == suffix:
                            logger.warning(f"Password found in {count} breaches")
                            return True
        except Exception as e:
            logger.error(f"Error checking password breach: {e}")
        
        return False
    
    def generate_csrf_token(self, session_id: str) -> str:
        """Generate CSRF token for session"""
        secret = settings.SECRET_KEY.encode()
        message = f"{session_id}:{datetime.utcnow().isoformat()}".encode()
        return hmac.new(secret, message, hashlib.sha256).hexdigest()
    
    def verify_csrf_token(self, token: str, session_id: str) -> bool:
        """Verify CSRF token"""
        # Generate expected token
        expected = self.generate_csrf_token(session_id)
        
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(token, expected)
    
    async def scan_user_input(self, input_data: str) -> Dict[str, Any]:
        """Scan user input for malicious content"""
        scan_result = {
            "clean": True,
            "threats": [],
            "sanitized": input_data
        }
        
        # Check for SQL injection patterns
        sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE)\b)",
            r"(--|#|\/\*|\*\/)",
            r"(\bOR\b\s*\d+\s*=\s*\d+)",
            r"(\bAND\b\s*\d+\s*=\s*\d+)"
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                scan_result["clean"] = False
                scan_result["threats"].append("sql_injection")
                break
        
        # Check for XSS patterns
        xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>"
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                scan_result["clean"] = False
                scan_result["threats"].append("xss")
                break
        
        # Sanitize input if threats found
        if not scan_result["clean"]:
            # Basic sanitization - in production, use a proper library
            sanitized = input_data
            sanitized = re.sub(r'<[^>]+>', '', sanitized)  # Remove HTML tags
            sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
            scan_result["sanitized"] = sanitized
        
        return scan_result
    
    async def check_ip_reputation(self, ip: str) -> Dict[str, Any]:
        """Check IP reputation against threat intelligence"""
        reputation = {
            "ip": ip,
            "is_vpn": False,
            "is_tor": False,
            "is_proxy": False,
            "is_hostile": False,
            "country": "unknown",
            "risk_score": 0
        }
        
        # Check against known VPN/proxy ranges
        vpn_ranges = [
            "10.0.0.0/8",
            "172.16.0.0/12",
            "192.168.0.0/16"
        ]
        
        try:
            ip_obj = ip_address(ip)
            for range_str in vpn_ranges:
                if ip_obj in ip_network(range_str):
                    reputation["is_vpn"] = True
                    reputation["risk_score"] += 10
                    break
        except:
            pass
        
        # Check if IP is in blocked list
        if ip in self.blocked_ips or await redis_client.sismember("security:blocked_ips", ip):
            reputation["is_hostile"] = True
            reputation["risk_score"] += 50
        
        return reputation
    
    async def generate_security_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate security report for date range"""
        report = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_requests": 0,
            "blocked_requests": 0,
            "unique_ips": set(),
            "threats_detected": defaultdict(int),
            "top_blocked_ips": [],
            "auth_failures": 0,
            "high_risk_requests": 0
        }
        
        # Analyze audit logs
        current = start_date
        while current <= end_date:
            key = f"security:audit:{current.strftime('%Y%m%d')}"
            logs = await redis_client.lrange(key, 0, -1)
            
            for log_str in logs:
                try:
                    log = json.loads(log_str)
                    report["total_requests"] += 1
                    report["unique_ips"].add(log["ip"])
                    
                    if log["risk_score"] >= 80:
                        report["blocked_requests"] += 1
                    
                    if log["risk_score"] >= 50:
                        report["high_risk_requests"] += 1
                    
                    for threat in log.get("threats", []):
                        report["threats_detected"][threat] += 1
                except:
                    continue
            
            current += timedelta(days=1)
        
        # Convert set to count
        report["unique_ips"] = len(report["unique_ips"])
        
        return report


# Global security audit instance
security_audit = SecurityAudit()


class SecurityHeaders:
    """Security headers middleware"""
    
    def __init__(self):
        self.headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            "Content-Security-Policy": self._build_csp()
        }
    
    def _build_csp(self) -> str:
        """Build Content Security Policy"""
        directives = {
            "default-src": ["'self'"],
            "script-src": ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"],
            "style-src": ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
            "font-src": ["'self'", "https://fonts.gstatic.com"],
            "img-src": ["'self'", "data:", "https:"],
            "connect-src": ["'self'", settings.BACKEND_CORS_ORIGINS[0], "wss:"],
            "frame-ancestors": ["'none'"],
            "base-uri": ["'self'"],
            "form-action": ["'self'"]
        }
        
        return "; ".join([f"{key} {' '.join(values)}" for key, values in directives.items()])
    
    def get_headers(self) -> Dict[str, str]:
        """Get security headers"""
        return self.headers.copy()


# Global security headers instance
security_headers = SecurityHeaders()