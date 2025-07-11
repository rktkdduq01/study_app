# Security Configuration Guide

## 🔐 Environment Variables

### Backend Security Keys

The application requires several security keys to be configured properly. Here's how to generate them:

#### 1. SECRET_KEY (JWT Access Token Signing)
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### 2. REFRESH_SECRET_KEY (JWT Refresh Token Signing)
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### 3. ENCRYPTION_KEY (Data Encryption)
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

#### 4. INTERNAL_API_KEY (Internal API Authentication)
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 🛡️ Security Features

### 1. Authentication & Authorization
- **JWT Tokens**: Short-lived access tokens (30 min) with refresh tokens (7 days)
- **Role-Based Access Control (RBAC)**: Child, Parent, Teacher, Admin roles
- **Permission System**: Fine-grained permissions for each role
- **Token Blacklisting**: Revoked tokens are blacklisted in Redis

### 2. Password Security
- **Requirements**:
  - Minimum 8 characters
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one digit
  - At least one special character
- **Bcrypt Hashing**: Passwords are hashed using bcrypt

### 3. API Security
- **Rate Limiting**: 
  - 60 requests per minute (unauthenticated)
  - 120 requests per minute (authenticated)
  - 1000/2000 requests per hour
- **CORS**: Configured for specific origins only
- **Security Headers**: CSP, HSTS, X-Frame-Options, etc.

### 4. Data Protection
- **Encryption**: Sensitive data encrypted using Fernet (AES)
- **SQL Injection Protection**: Input validation and parameterized queries
- **XSS Protection**: Input sanitization and CSP headers

### 5. Security Middleware Stack
1. Rate Limiting
2. SQL Injection Protection
3. XSS Protection
4. Request Validation
5. Security Headers
6. CORS

## 📋 Security Checklist

### Development
- [ ] Use `.env` file for secrets (never commit!)
- [ ] Generate new keys for each environment
- [ ] Enable HTTPS in production
- [ ] Use parameterized database queries
- [ ] Validate all user inputs

### Production Deployment
- [ ] Set `DEBUG=False`
- [ ] Use strong, unique keys for all secrets
- [ ] Enable Redis for token blacklisting
- [ ] Configure proper CORS origins
- [ ] Set up SSL/TLS certificates
- [ ] Enable security headers
- [ ] Configure firewall rules
- [ ] Regular security audits

## 🚨 Security Best Practices

### 1. Token Management
```python
# Frontend - Store tokens securely
localStorage.setItem('access_token', token);  // OK for development
// Consider using httpOnly cookies in production

# Backend - Always validate tokens
@router.get("/protected")
def protected_route(current_user: User = Depends(get_current_active_user)):
    return {"user": current_user}
```

### 2. Permission Checking
```python
# Use permission decorators
@router.post("/admin-only")
def admin_route(user: User = Depends(RequireAdmin)):
    return {"message": "Admin access granted"}

# Or check permissions manually
if not has_permission(user, Permission.CONTENT_CREATE):
    raise HTTPException(status_code=403, detail="Permission denied")
```

### 3. Data Encryption
```python
# Encrypt sensitive data before storing
from app.utils.encryption import encrypt_data, decrypt_data

encrypted = encrypt_data("sensitive information")
decrypted = decrypt_data(encrypted)
```

### 4. Logging Security Events
```python
from app.utils.security_logger import security_logger

# Log security-relevant events
security_logger.log_login_attempt(email, ip_address, success=True)
security_logger.log_unauthorized_access(ip_address, path, method)
```

## 🔍 Security Monitoring

### Log Files
- **Security Events**: `logs/security.log`
- **Application Logs**: Standard output/error
- **Access Logs**: Web server logs

### What to Monitor
1. Failed login attempts
2. Unauthorized access attempts
3. Rate limit violations
4. Suspicious patterns
5. Token refresh patterns

## 🆘 Incident Response

### If a Security Breach Occurs:
1. **Immediate Actions**:
   - Revoke all tokens
   - Change all secret keys
   - Review access logs
   
2. **Investigation**:
   - Check security logs
   - Identify affected users
   - Determine breach scope
   
3. **Recovery**:
   - Reset affected passwords
   - Notify affected users
   - Implement additional security measures

## 📚 Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [Python Security](https://python.readthedocs.io/en/latest/library/security_warnings.html)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)