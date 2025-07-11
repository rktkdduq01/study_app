"""
Security API endpoints
"""
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.api import deps
from app.core.security_audit import security_audit
from app.core.encryption import encryption_service
from app.models.user import User
from app.core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


class SecurityCheckRequest(BaseModel):
    password: Optional[str] = None
    email: Optional[EmailStr] = None
    ip_address: Optional[str] = None


class SecurityCheckResponse(BaseModel):
    password_strength: Optional[dict] = None
    password_breached: Optional[bool] = None
    email_valid: Optional[bool] = None
    ip_reputation: Optional[dict] = None


class SecurityReportRequest(BaseModel):
    start_date: datetime
    end_date: datetime
    report_type: str = "summary"


class TwoFactorSetupResponse(BaseModel):
    secret: str
    qr_code: str
    backup_codes: List[str]


class TwoFactorVerifyRequest(BaseModel):
    code: str


@router.post("/check", response_model=SecurityCheckResponse)
async def security_check(
    request: SecurityCheckRequest,
    current_user: User = Depends(deps.get_current_user)
):
    """Perform security checks on user input"""
    response = SecurityCheckResponse()
    
    # Check password
    if request.password:
        # Check password strength
        strength = check_password_strength(request.password)
        response.password_strength = strength
        
        # Check if password has been breached
        response.password_breached = await security_audit.check_password_breach(request.password)
    
    # Check email
    if request.email:
        # Basic email validation is done by Pydantic
        response.email_valid = True
    
    # Check IP reputation
    if request.ip_address:
        response.ip_reputation = await security_audit.check_ip_reputation(request.ip_address)
    
    return response


@router.get("/audit-log")
async def get_audit_log(
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(deps.get_current_admin_user),
    db: Session = Depends(deps.get_db)
):
    """Get security audit logs (admin only)"""
    # Default to last 24 hours if no dates provided
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=1)
    
    # Get audit logs from Redis
    logs = []
    current = start_date
    
    while current <= end_date:
        key = f"security:audit:{current.strftime('%Y%m%d')}"
        daily_logs = await redis_client.lrange(key, skip, skip + limit - 1)
        
        for log_str in daily_logs:
            try:
                log = json.loads(log_str)
                logs.append(log)
            except:
                continue
        
        current += timedelta(days=1)
    
    return {
        "logs": logs[:limit],
        "total": len(logs),
        "skip": skip,
        "limit": limit
    }


@router.post("/report")
async def generate_security_report(
    request: SecurityReportRequest,
    current_user: User = Depends(deps.get_current_admin_user)
):
    """Generate security report (admin only)"""
    report = await security_audit.generate_security_report(
        request.start_date,
        request.end_date
    )
    
    # Add additional analysis
    if request.report_type == "detailed":
        report["recommendations"] = generate_security_recommendations(report)
    
    return report


@router.post("/2fa/setup", response_model=TwoFactorSetupResponse)
async def setup_two_factor(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """Setup two-factor authentication"""
    import pyotp
    import qrcode
    import io
    import base64
    
    # Generate secret
    secret = pyotp.random_base32()
    
    # Generate QR code
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=current_user.email,
        issuer_name='Educational RPG'
    )
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    
    qr_code = base64.b64encode(buf.getvalue()).decode()
    
    # Generate backup codes
    backup_codes = [secrets.token_urlsafe(8) for _ in range(10)]
    
    # Store encrypted secret and backup codes
    current_user.two_factor_secret = encryption_service.encrypt_field(secret)
    current_user.two_factor_backup_codes = encryption_service.encrypt_field(backup_codes)
    current_user.two_factor_enabled = False  # Not enabled until first verification
    
    db.commit()
    
    return TwoFactorSetupResponse(
        secret=secret,
        qr_code=f"data:image/png;base64,{qr_code}",
        backup_codes=backup_codes
    )


@router.post("/2fa/verify")
async def verify_two_factor(
    request: TwoFactorVerifyRequest,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """Verify two-factor authentication code"""
    import pyotp
    
    if not current_user.two_factor_secret:
        raise HTTPException(status_code=400, detail="2FA not set up")
    
    # Decrypt secret
    secret = encryption_service.decrypt_field(current_user.two_factor_secret)
    
    # Verify code
    totp = pyotp.TOTP(secret)
    if totp.verify(request.code):
        # Enable 2FA if first time
        if not current_user.two_factor_enabled:
            current_user.two_factor_enabled = True
            db.commit()
        
        return {"status": "verified", "message": "2FA code verified successfully"}
    else:
        # Check backup codes
        backup_codes = encryption_service.decrypt_field(current_user.two_factor_backup_codes)
        if request.code in backup_codes:
            # Remove used backup code
            backup_codes.remove(request.code)
            current_user.two_factor_backup_codes = encryption_service.encrypt_field(backup_codes)
            db.commit()
            
            return {"status": "verified", "message": "Backup code used successfully"}
    
    raise HTTPException(status_code=400, detail="Invalid 2FA code")


@router.post("/2fa/disable")
async def disable_two_factor(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """Disable two-factor authentication"""
    current_user.two_factor_enabled = False
    current_user.two_factor_secret = None
    current_user.two_factor_backup_codes = None
    
    db.commit()
    
    return {"message": "2FA disabled successfully"}


@router.get("/blocked-ips")
async def get_blocked_ips(
    current_user: User = Depends(deps.get_current_admin_user)
):
    """Get list of blocked IPs (admin only)"""
    blocked_ips = await redis_client.smembers("security:blocked_ips")
    return {"blocked_ips": list(blocked_ips)}


@router.delete("/blocked-ips/{ip}")
async def unblock_ip(
    ip: str,
    current_user: User = Depends(deps.get_current_admin_user)
):
    """Unblock an IP address (admin only)"""
    await redis_client.srem("security:blocked_ips", ip)
    security_audit.blocked_ips.discard(ip)
    
    logger.info(f"IP {ip} unblocked by admin {current_user.email}")
    
    return {"message": f"IP {ip} unblocked successfully"}


@router.get("/encryption-health")
async def check_encryption_health(
    current_user: User = Depends(deps.get_current_admin_user)
):
    """Check encryption service health (admin only)"""
    return encryption_service.check_encryption_health()


def check_password_strength(password: str) -> dict:
    """Check password strength and return score"""
    score = 0
    feedback = []
    
    # Length check
    if len(password) >= 8:
        score += 1
    else:
        feedback.append("Password should be at least 8 characters long")
    
    if len(password) >= 12:
        score += 1
    
    # Complexity checks
    if any(c.isupper() for c in password):
        score += 1
    else:
        feedback.append("Include at least one uppercase letter")
    
    if any(c.islower() for c in password):
        score += 1
    else:
        feedback.append("Include at least one lowercase letter")
    
    if any(c.isdigit() for c in password):
        score += 1
    else:
        feedback.append("Include at least one number")
    
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if any(c in special_chars for c in password):
        score += 1
    else:
        feedback.append("Include at least one special character")
    
    # Common patterns check
    common_patterns = ["123", "abc", "password", "qwerty", "admin"]
    if any(pattern in password.lower() for pattern in common_patterns):
        score -= 1
        feedback.append("Avoid common patterns")
    
    # Calculate strength
    if score >= 5:
        strength = "strong"
    elif score >= 3:
        strength = "medium"
    else:
        strength = "weak"
    
    return {
        "score": max(0, score),
        "strength": strength,
        "feedback": feedback
    }


def generate_security_recommendations(report: dict) -> List[str]:
    """Generate security recommendations based on report"""
    recommendations = []
    
    # Check blocked requests
    if report.get("blocked_requests", 0) > report.get("total_requests", 1) * 0.1:
        recommendations.append("High number of blocked requests detected. Review security rules.")
    
    # Check auth failures
    if report.get("auth_failures", 0) > 100:
        recommendations.append("High authentication failure rate. Consider implementing CAPTCHA.")
    
    # Check unique IPs
    if report.get("unique_ips", 0) > 1000:
        recommendations.append("High number of unique IPs. Monitor for potential DDoS.")
    
    # Check threat types
    threats = report.get("threats_detected", {})
    if threats.get("sql_injection", 0) > 0:
        recommendations.append("SQL injection attempts detected. Review input validation.")
    
    if threats.get("xss", 0) > 0:
        recommendations.append("XSS attempts detected. Enhance output encoding.")
    
    if not recommendations:
        recommendations.append("No significant security issues detected.")
    
    return recommendations


# Import required modules
import json
import secrets
from app.core.redis_client import redis_client