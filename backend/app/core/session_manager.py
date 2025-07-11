"""
Advanced Session Management System
High-performance session handling with Redis backend and security features
"""

import json
import time
import uuid
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Set
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager
from enum import Enum
import asyncio

from app.core.logger import get_logger
from app.core.redis_client import redis_client
from app.core.config import settings

logger = get_logger(__name__)

class SessionState(Enum):
    """Session states"""
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    SUSPICIOUS = "suspicious"

@dataclass
class SessionData:
    """Session data structure"""
    session_id: str
    user_id: Optional[str]
    user_agent: str
    ip_address: str
    created_at: datetime
    last_accessed: datetime
    expires_at: datetime
    state: SessionState
    data: Dict[str, Any]
    csrf_token: str
    device_fingerprint: Optional[str] = None
    location: Optional[Dict[str, str]] = None
    security_flags: Dict[str, bool] = None

    def __post_init__(self):
        if self.security_flags is None:
            self.security_flags = {
                "is_secure": False,
                "http_only": True,
                "same_site": True
            }

@dataclass
class SessionMetrics:
    """Session metrics"""
    operation: str
    session_id: str
    execution_time: float
    success: bool
    timestamp: datetime

class SessionConfig:
    """Session configuration"""
    
    def __init__(self):
        self.default_ttl = getattr(settings, 'SESSION_TTL', 3600)  # 1 hour
        self.max_ttl = getattr(settings, 'SESSION_MAX_TTL', 86400 * 7)  # 7 days
        self.cleanup_interval = getattr(settings, 'SESSION_CLEANUP_INTERVAL', 300)  # 5 minutes
        self.max_sessions_per_user = getattr(settings, 'MAX_SESSIONS_PER_USER', 5)
        self.session_key_prefix = "session:"
        self.user_sessions_key_prefix = "user_sessions:"
        self.active_sessions_key = "active_sessions"
        self.suspicious_threshold = 10  # Suspicious activity threshold

class AdvancedSessionManager:
    """Advanced session management with Redis backend"""
    
    def __init__(self, config: SessionConfig = None):
        self.config = config or SessionConfig()
        self.metrics: List[SessionMetrics] = []
        
        # Session tracking
        self.session_stats = {
            "total_sessions": 0,
            "active_sessions": 0,
            "expired_sessions": 0,
            "terminated_sessions": 0,
            "suspicious_sessions": 0
        }
        
        # Background cleanup task
        self._cleanup_task = None
        self._start_background_cleanup()
    
    def _start_background_cleanup(self):
        """Start background cleanup task"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of expired sessions"""
        while True:
            try:
                await asyncio.sleep(self.config.cleanup_interval)
                await self.cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Session cleanup error: {e}")
    
    def _generate_session_id(self) -> str:
        """Generate cryptographically secure session ID"""
        return secrets.token_urlsafe(32)
    
    def _generate_csrf_token(self) -> str:
        """Generate CSRF token"""
        return secrets.token_urlsafe(32)
    
    def _generate_device_fingerprint(self, user_agent: str, ip_address: str, 
                                   additional_data: Optional[Dict] = None) -> str:
        """Generate device fingerprint"""
        fingerprint_data = f"{user_agent}:{ip_address}"
        
        if additional_data:
            fingerprint_data += ":" + json.dumps(additional_data, sort_keys=True)
        
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()
    
    async def _record_metric(self, operation: str, session_id: str, 
                           execution_time: float, success: bool):
        """Record session operation metrics"""
        metric = SessionMetrics(
            operation=operation,
            session_id=session_id,
            execution_time=execution_time,
            success=success,
            timestamp=datetime.utcnow()
        )
        
        self.metrics.append(metric)
        
        # Keep only recent metrics
        if len(self.metrics) > 1000:
            self.metrics = self.metrics[-500:]
    
    async def create_session(self, user_id: Optional[str] = None, 
                           user_agent: str = "", ip_address: str = "",
                           ttl: Optional[int] = None,
                           additional_data: Optional[Dict] = None) -> SessionData:
        """Create new session"""
        start_time = time.time()
        success = False
        session_id = self._generate_session_id()
        
        try:
            ttl = ttl or self.config.default_ttl
            now = datetime.utcnow()
            
            # Check session limits for user
            if user_id:
                await self._enforce_session_limits(user_id)
            
            # Create session data
            session_data = SessionData(
                session_id=session_id,
                user_id=user_id,
                user_agent=user_agent,
                ip_address=ip_address,
                created_at=now,
                last_accessed=now,
                expires_at=now + timedelta(seconds=ttl),
                state=SessionState.ACTIVE,
                data=additional_data or {},
                csrf_token=self._generate_csrf_token(),
                device_fingerprint=self._generate_device_fingerprint(user_agent, ip_address)
            )
            
            # Store session in Redis
            session_key = f"{self.config.session_key_prefix}{session_id}"
            session_dict = asdict(session_data)
            
            # Convert datetime objects to ISO format
            session_dict['created_at'] = session_data.created_at.isoformat()
            session_dict['last_accessed'] = session_data.last_accessed.isoformat()
            session_dict['expires_at'] = session_data.expires_at.isoformat()
            session_dict['state'] = session_data.state.value
            
            # Store with pipeline for atomicity
            async with redis_client.pipeline() as pipe:
                pipe.hset(session_key, mapping=session_dict)
                pipe.expire(session_key, ttl)
                
                # Add to active sessions set
                pipe.sadd(self.config.active_sessions_key, session_id)
                
                # Track user sessions
                if user_id:
                    user_sessions_key = f"{self.config.user_sessions_key_prefix}{user_id}"
                    pipe.sadd(user_sessions_key, session_id)
                    pipe.expire(user_sessions_key, self.config.max_ttl)
                
                await pipe.execute()
            
            # Update stats
            self.session_stats["total_sessions"] += 1
            self.session_stats["active_sessions"] += 1
            
            success = True
            logger.info(f"Created session {session_id} for user {user_id}")
            
            return session_data
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise
        finally:
            await self._record_metric("create", session_id, 
                                     time.time() - start_time, success)
    
    async def _enforce_session_limits(self, user_id: str):
        """Enforce maximum sessions per user"""
        user_sessions_key = f"{self.config.user_sessions_key_prefix}{user_id}"
        user_sessions = await redis_client.smembers(user_sessions_key)
        
        if len(user_sessions) >= self.config.max_sessions_per_user:
            # Remove oldest session
            oldest_session = None
            oldest_time = None
            
            for session_id in user_sessions:
                session_key = f"{self.config.session_key_prefix}{session_id.decode()}"
                session_data = await redis_client.hgetall(session_key)
                
                if session_data:
                    created_at = datetime.fromisoformat(session_data[b'created_at'].decode())
                    if oldest_time is None or created_at < oldest_time:
                        oldest_time = created_at
                        oldest_session = session_id.decode()
            
            if oldest_session:
                await self.terminate_session(oldest_session, reason="session_limit_exceeded")
    
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get session by ID"""
        start_time = time.time()
        success = False
        
        try:
            session_key = f"{self.config.session_key_prefix}{session_id}"
            session_dict = await redis_client.hgetall(session_key)
            
            if not session_dict:
                return None
            
            # Convert bytes to strings and parse
            session_data = {}
            for key, value in session_dict.items():
                key_str = key.decode() if isinstance(key, bytes) else key
                value_str = value.decode() if isinstance(value, bytes) else value
                
                if key_str in ['created_at', 'last_accessed', 'expires_at']:
                    session_data[key_str] = datetime.fromisoformat(value_str)
                elif key_str == 'state':
                    session_data[key_str] = SessionState(value_str)
                elif key_str in ['data', 'security_flags']:
                    session_data[key_str] = json.loads(value_str) if value_str else {}
                else:
                    session_data[key_str] = value_str
            
            # Check if session is expired
            if session_data['expires_at'] < datetime.utcnow():
                await self._mark_session_expired(session_id)
                return None
            
            # Update last accessed time
            await self._update_last_accessed(session_id)
            
            success = True
            return SessionData(**session_data)
            
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None
        finally:
            await self._record_metric("get", session_id, 
                                     time.time() - start_time, success)
    
    async def _update_last_accessed(self, session_id: str):
        """Update session last accessed time"""
        session_key = f"{self.config.session_key_prefix}{session_id}"
        await redis_client.hset(session_key, "last_accessed", datetime.utcnow().isoformat())
    
    async def update_session_data(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Update session data"""
        start_time = time.time()
        success = False
        
        try:
            session_key = f"{self.config.session_key_prefix}{session_id}"
            
            # Check if session exists
            exists = await redis_client.exists(session_key)
            if not exists:
                return False
            
            # Update data
            await redis_client.hset(session_key, "data", json.dumps(data))
            await self._update_last_accessed(session_id)
            
            success = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {e}")
            return False
        finally:
            await self._record_metric("update", session_id, 
                                     time.time() - start_time, success)
    
    async def extend_session(self, session_id: str, ttl: Optional[int] = None) -> bool:
        """Extend session TTL"""
        start_time = time.time()
        success = False
        
        try:
            ttl = ttl or self.config.default_ttl
            session_key = f"{self.config.session_key_prefix}{session_id}"
            
            # Update expires_at and Redis TTL
            new_expires_at = datetime.utcnow() + timedelta(seconds=ttl)
            
            async with redis_client.pipeline() as pipe:
                pipe.hset(session_key, "expires_at", new_expires_at.isoformat())
                pipe.expire(session_key, ttl)
                await pipe.execute()
            
            await self._update_last_accessed(session_id)
            
            success = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to extend session {session_id}: {e}")
            return False
        finally:
            await self._record_metric("extend", session_id, 
                                     time.time() - start_time, success)
    
    async def terminate_session(self, session_id: str, reason: str = "user_logout") -> bool:
        """Terminate session"""
        start_time = time.time()
        success = False
        
        try:
            session_key = f"{self.config.session_key_prefix}{session_id}"
            
            # Get session data to find user_id
            session_data = await redis_client.hgetall(session_key)
            user_id = session_data.get(b'user_id')
            
            # Remove session
            async with redis_client.pipeline() as pipe:
                pipe.delete(session_key)
                pipe.srem(self.config.active_sessions_key, session_id)
                
                # Remove from user sessions
                if user_id:
                    user_sessions_key = f"{self.config.user_sessions_key_prefix}{user_id.decode()}"
                    pipe.srem(user_sessions_key, session_id)
                
                await pipe.execute()
            
            # Update stats
            self.session_stats["active_sessions"] = max(0, self.session_stats["active_sessions"] - 1)
            self.session_stats["terminated_sessions"] += 1
            
            success = True
            logger.info(f"Terminated session {session_id} - reason: {reason}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to terminate session {session_id}: {e}")
            return False
        finally:
            await self._record_metric("terminate", session_id, 
                                     time.time() - start_time, success)
    
    async def _mark_session_expired(self, session_id: str):
        """Mark session as expired"""
        session_key = f"{self.config.session_key_prefix}{session_id}"
        await redis_client.hset(session_key, "state", SessionState.EXPIRED.value)
        await redis_client.srem(self.config.active_sessions_key, session_id)
        
        # Update stats
        self.session_stats["active_sessions"] = max(0, self.session_stats["active_sessions"] - 1)
        self.session_stats["expired_sessions"] += 1
    
    async def terminate_user_sessions(self, user_id: str, 
                                    exclude_session: Optional[str] = None) -> int:
        """Terminate all sessions for a user"""
        user_sessions_key = f"{self.config.user_sessions_key_prefix}{user_id}"
        user_sessions = await redis_client.smembers(user_sessions_key)
        
        terminated_count = 0
        for session_id in user_sessions:
            session_id_str = session_id.decode() if isinstance(session_id, bytes) else session_id
            
            if exclude_session and session_id_str == exclude_session:
                continue
            
            if await self.terminate_session(session_id_str, "user_sessions_terminated"):
                terminated_count += 1
        
        return terminated_count
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        start_time = time.time()
        cleaned_count = 0
        
        try:
            # Get all active session IDs
            active_sessions = await redis_client.smembers(self.config.active_sessions_key)
            
            for session_id in active_sessions:
                session_id_str = session_id.decode() if isinstance(session_id, bytes) else session_id
                session_key = f"{self.config.session_key_prefix}{session_id_str}"
                
                # Check if session exists and is expired
                session_data = await redis_client.hgetall(session_key)
                if not session_data:
                    # Session doesn't exist, remove from active set
                    await redis_client.srem(self.config.active_sessions_key, session_id_str)
                    cleaned_count += 1
                    continue
                
                expires_at_str = session_data.get(b'expires_at')
                if expires_at_str:
                    expires_at = datetime.fromisoformat(expires_at_str.decode())
                    if expires_at < datetime.utcnow():
                        await self._mark_session_expired(session_id_str)
                        cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} expired sessions")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Session cleanup failed: {e}")
            return 0
    
    async def get_user_sessions(self, user_id: str) -> List[SessionData]:
        """Get all active sessions for a user"""
        user_sessions_key = f"{self.config.user_sessions_key_prefix}{user_id}"
        session_ids = await redis_client.smembers(user_sessions_key)
        
        sessions = []
        for session_id in session_ids:
            session_id_str = session_id.decode() if isinstance(session_id, bytes) else session_id
            session = await self.get_session(session_id_str)
            if session and session.state == SessionState.ACTIVE:
                sessions.append(session)
        
        return sessions
    
    async def detect_suspicious_activity(self, session_id: str, 
                                       activity_data: Dict[str, Any]) -> bool:
        """Detect suspicious session activity"""
        try:
            session = await self.get_session(session_id)
            if not session:
                return False
            
            suspicious_indicators = 0
            
            # Check for IP address changes
            if 'ip_address' in activity_data:
                if activity_data['ip_address'] != session.ip_address:
                    suspicious_indicators += 3
                    logger.warning(f"IP address change detected for session {session_id}")
            
            # Check for user agent changes
            if 'user_agent' in activity_data:
                if activity_data['user_agent'] != session.user_agent:
                    suspicious_indicators += 2
                    logger.warning(f"User agent change detected for session {session_id}")
            
            # Check for unusual access patterns
            if 'access_frequency' in activity_data:
                if activity_data['access_frequency'] > 100:  # More than 100 requests per minute
                    suspicious_indicators += 2
            
            # Mark as suspicious if threshold exceeded
            if suspicious_indicators >= self.config.suspicious_threshold:
                await self._mark_session_suspicious(session_id)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Suspicious activity detection failed for session {session_id}: {e}")
            return False
    
    async def _mark_session_suspicious(self, session_id: str):
        """Mark session as suspicious"""
        session_key = f"{self.config.session_key_prefix}{session_id}"
        await redis_client.hset(session_key, "state", SessionState.SUSPICIOUS.value)
        
        # Update stats
        self.session_stats["suspicious_sessions"] += 1
        
        logger.warning(f"Session {session_id} marked as suspicious")
    
    async def validate_csrf_token(self, session_id: str, provided_token: str) -> bool:
        """Validate CSRF token"""
        try:
            session = await self.get_session(session_id)
            if not session:
                return False
            
            return session.csrf_token == provided_token
            
        except Exception as e:
            logger.error(f"CSRF token validation failed: {e}")
            return False
    
    async def rotate_csrf_token(self, session_id: str) -> Optional[str]:
        """Rotate CSRF token for session"""
        try:
            new_token = self._generate_csrf_token()
            session_key = f"{self.config.session_key_prefix}{session_id}"
            
            await redis_client.hset(session_key, "csrf_token", new_token)
            await self._update_last_accessed(session_id)
            
            return new_token
            
        except Exception as e:
            logger.error(f"CSRF token rotation failed for session {session_id}: {e}")
            return None
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        # Calculate metrics from recent operations
        recent_metrics = [m for m in self.metrics 
                         if m.timestamp > datetime.utcnow() - timedelta(minutes=5)]
        
        metrics_summary = {}
        if recent_metrics:
            total_time = sum(m.execution_time for m in recent_metrics)
            successful_ops = sum(1 for m in recent_metrics if m.success)
            
            metrics_summary = {
                "recent_operations": len(recent_metrics),
                "success_rate": round(successful_ops / len(recent_metrics) * 100, 2),
                "avg_response_time_ms": round(total_time / len(recent_metrics) * 1000, 2)
            }
        
        return {
            "session_counts": self.session_stats.copy(),
            "metrics": metrics_summary,
            "config": {
                "default_ttl": self.config.default_ttl,
                "max_sessions_per_user": self.config.max_sessions_per_user,
                "cleanup_interval": self.config.cleanup_interval
            }
        }

# Global session manager instance
session_config = SessionConfig()
session_manager = AdvancedSessionManager(session_config)

# Context manager for session operations
@asynccontextmanager
async def session_context():
    """Context manager for session operations"""
    try:
        yield session_manager
    except Exception as e:
        logger.error(f"Session context error: {e}")
        raise

# Utility functions
async def create_user_session(user_id: str, user_agent: str = "", 
                            ip_address: str = "", ttl: Optional[int] = None) -> SessionData:
    """Create session for authenticated user"""
    return await session_manager.create_session(
        user_id=user_id,
        user_agent=user_agent,
        ip_address=ip_address,
        ttl=ttl
    )

async def get_current_session(session_id: str) -> Optional[SessionData]:
    """Get current session"""
    return await session_manager.get_session(session_id)

async def logout_user(session_id: str) -> bool:
    """Logout user by terminating session"""
    return await session_manager.terminate_session(session_id, "user_logout")

async def logout_all_user_sessions(user_id: str, current_session_id: Optional[str] = None) -> int:
    """Logout all user sessions except current one"""
    return await session_manager.terminate_user_sessions(user_id, current_session_id)