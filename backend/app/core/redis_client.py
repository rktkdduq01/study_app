"""
Enhanced Redis Client with Connection Pooling and Health Monitoring
High-performance Redis operations with automatic failover and monitoring
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager
import logging

try:
    import redis.asyncio as redis
    from redis.asyncio import ConnectionPool, Redis
    from redis.exceptions import (
        ConnectionError, TimeoutError, RedisError,
        DataError, ResponseError
    )
except ImportError:
    # Fallback for older redis-py versions
    import aioredis as redis
    from aioredis import ConnectionPool, Redis
    from aioredis.exceptions import (
        ConnectionError, TimeoutError, RedisError,
        DataError, ResponseError
    )

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

@dataclass
class RedisMetrics:
    """Redis operation metrics"""
    operation: str
    execution_time: float
    success: bool
    error_type: Optional[str]
    data_size: int
    timestamp: datetime

@dataclass
class ConnectionHealth:
    """Redis connection health status"""
    is_connected: bool
    latency_ms: float
    memory_usage: Optional[Dict[str, Any]]
    uptime_seconds: Optional[int]
    connected_clients: Optional[int]
    last_check: datetime

class EnhancedRedisClient:
    """Enhanced Redis client with advanced features"""
    
    def __init__(self, url: Optional[str] = None, **kwargs):
        self.url = url or getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
        self.connection_pool = None
        self.client: Optional[Redis] = None
        
        # Configuration
        self.max_connections = kwargs.get('max_connections', 20)
        self.socket_keepalive = kwargs.get('socket_keepalive', True)
        self.socket_keepalive_options = kwargs.get('socket_keepalive_options', {})
        self.retry_on_timeout = kwargs.get('retry_on_timeout', True)
        self.health_check_interval = kwargs.get('health_check_interval', 30)
        
        # Metrics and monitoring
        self.metrics: List[RedisMetrics] = []
        self.connection_health = ConnectionHealth(
            is_connected=False,
            latency_ms=0.0,
            memory_usage=None,
            uptime_seconds=None,
            connected_clients=None,
            last_check=datetime.utcnow()
        )
        
        # Circuit breaker pattern
        self.failure_count = 0
        self.failure_threshold = 5
        self.recovery_timeout = 60
        self.last_failure_time = None
        self.is_circuit_open = False
        
        # Background tasks
        self._health_check_task = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize Redis connection and start background tasks"""
        if self._initialized:
            return
        
        try:
            # Create connection pool
            self.connection_pool = ConnectionPool.from_url(
                self.url,
                max_connections=self.max_connections,
                socket_keepalive=self.socket_keepalive,
                socket_keepalive_options=self.socket_keepalive_options,
                retry_on_timeout=self.retry_on_timeout
            )
            
            # Create Redis client
            self.client = Redis(connection_pool=self.connection_pool)
            
            # Test connection
            await self.ping()
            
            # Start health monitoring
            self._health_check_task = asyncio.create_task(self._periodic_health_check())
            
            self._initialized = True
            logger.info("Redis client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")
            raise
    
    async def close(self):
        """Close Redis connection and cleanup"""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        if self.client:
            await self.client.close()
        
        if self.connection_pool:
            await self.connection_pool.disconnect()
        
        self._initialized = False
        logger.info("Redis client closed")
    
    async def _periodic_health_check(self):
        """Periodic health check task"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._perform_health_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
    
    async def _perform_health_check(self):
        """Perform comprehensive health check"""
        try:
            start_time = time.time()
            
            # Test ping
            await self.client.ping()
            latency = (time.time() - start_time) * 1000
            
            # Get server info
            info = await self.client.info()
            
            # Update health status
            self.connection_health = ConnectionHealth(
                is_connected=True,
                latency_ms=round(latency, 2),
                memory_usage={
                    'used_memory': info.get('used_memory', 0),
                    'used_memory_human': info.get('used_memory_human', '0B'),
                    'maxmemory': info.get('maxmemory', 0)
                },
                uptime_seconds=info.get('uptime_in_seconds', 0),
                connected_clients=info.get('connected_clients', 0),
                last_check=datetime.utcnow()
            )
            
            # Reset circuit breaker on successful health check
            if self.is_circuit_open:
                self._reset_circuit_breaker()
            
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            self.connection_health.is_connected = False
            self.connection_health.last_check = datetime.utcnow()
            self._handle_failure()
    
    def _handle_failure(self):
        """Handle Redis operation failure"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.is_circuit_open = True
            logger.error(f"Circuit breaker opened after {self.failure_count} failures")
    
    def _reset_circuit_breaker(self):
        """Reset circuit breaker after successful operation"""
        if self.is_circuit_open:
            self.is_circuit_open = False
            self.failure_count = 0
            self.last_failure_time = None
            logger.info("Circuit breaker reset - Redis connection recovered")
    
    def _check_circuit_breaker(self):
        """Check if circuit breaker allows operation"""
        if not self.is_circuit_open:
            return True
        
        # Check if recovery timeout has passed
        if (self.last_failure_time and 
            time.time() - self.last_failure_time > self.recovery_timeout):
            logger.info("Circuit breaker recovery timeout reached, attempting operation")
            return True
        
        raise ConnectionError("Circuit breaker is open - Redis operations disabled")
    
    async def _execute_with_metrics(self, operation: str, func, *args, **kwargs):
        """Execute Redis operation with metrics collection"""
        if not self._initialized:
            await self.initialize()
        
        self._check_circuit_breaker()
        
        start_time = time.time()
        success = False
        error_type = None
        data_size = 0
        
        try:
            result = await func(*args, **kwargs)
            success = True
            
            # Estimate data size
            if isinstance(result, (str, bytes)):
                data_size = len(result)
            elif isinstance(result, (list, tuple)):
                data_size = sum(len(str(item)) for item in result)
            
            # Reset failure count on success
            if self.failure_count > 0:
                self.failure_count = max(0, self.failure_count - 1)
            
            return result
            
        except Exception as e:
            error_type = type(e).__name__
            self._handle_failure()
            raise
            
        finally:
            execution_time = time.time() - start_time
            
            # Record metrics
            metric = RedisMetrics(
                operation=operation,
                execution_time=execution_time,
                success=success,
                error_type=error_type,
                data_size=data_size,
                timestamp=datetime.utcnow()
            )
            
            self.metrics.append(metric)
            
            # Keep only recent metrics
            if len(self.metrics) > 1000:
                self.metrics = self.metrics[-500:]
    
    # Basic Redis operations with metrics
    async def ping(self) -> bool:
        """Ping Redis server"""
        result = await self._execute_with_metrics("ping", self.client.ping)
        return result
    
    async def get(self, key: str) -> Optional[bytes]:
        """Get value by key"""
        return await self._execute_with_metrics("get", self.client.get, key)
    
    async def set(self, key: str, value: Union[str, bytes], ex: Optional[int] = None) -> bool:
        """Set key-value pair"""
        return await self._execute_with_metrics("set", self.client.set, key, value, ex=ex)
    
    async def setex(self, key: str, time: int, value: Union[str, bytes]) -> bool:
        """Set key-value pair with expiration"""
        return await self._execute_with_metrics("setex", self.client.setex, key, time, value)
    
    async def delete(self, *keys) -> int:
        """Delete keys"""
        return await self._execute_with_metrics("delete", self.client.delete, *keys)
    
    async def exists(self, *keys) -> int:
        """Check if keys exist"""
        return await self._execute_with_metrics("exists", self.client.exists, *keys)
    
    async def expire(self, key: str, time: int) -> bool:
        """Set key expiration"""
        return await self._execute_with_metrics("expire", self.client.expire, key, time)
    
    async def ttl(self, key: str) -> int:
        """Get key time to live"""
        return await self._execute_with_metrics("ttl", self.client.ttl, key)
    
    async def keys(self, pattern: str = "*") -> List[bytes]:
        """Get keys matching pattern"""
        return await self._execute_with_metrics("keys", self.client.keys, pattern)
    
    # Hash operations
    async def hget(self, name: str, key: str) -> Optional[bytes]:
        """Get hash field value"""
        return await self._execute_with_metrics("hget", self.client.hget, name, key)
    
    async def hset(self, name: str, key: Optional[str] = None, value: Optional[str] = None, 
                  mapping: Optional[Dict] = None) -> int:
        """Set hash field"""
        return await self._execute_with_metrics("hset", self.client.hset, name, key, value, mapping=mapping)
    
    async def hgetall(self, name: str) -> Dict[bytes, bytes]:
        """Get all hash fields"""
        return await self._execute_with_metrics("hgetall", self.client.hgetall, name)
    
    async def hdel(self, name: str, *keys) -> int:
        """Delete hash fields"""
        return await self._execute_with_metrics("hdel", self.client.hdel, name, *keys)
    
    async def hincrby(self, name: str, key: str, amount: int = 1) -> int:
        """Increment hash field by amount"""
        return await self._execute_with_metrics("hincrby", self.client.hincrby, name, key, amount)
    
    async def hincrbyfloat(self, name: str, key: str, amount: float = 1.0) -> float:
        """Increment hash field by float amount"""
        return await self._execute_with_metrics("hincrbyfloat", self.client.hincrbyfloat, name, key, amount)
    
    # List operations
    async def lpush(self, name: str, *values) -> int:
        """Left push to list"""
        return await self._execute_with_metrics("lpush", self.client.lpush, name, *values)
    
    async def rpush(self, name: str, *values) -> int:
        """Right push to list"""
        return await self._execute_with_metrics("rpush", self.client.rpush, name, *values)
    
    async def lpop(self, name: str, count: Optional[int] = None) -> Union[bytes, List[bytes], None]:
        """Left pop from list"""
        return await self._execute_with_metrics("lpop", self.client.lpop, name, count)
    
    async def rpop(self, name: str, count: Optional[int] = None) -> Union[bytes, List[bytes], None]:
        """Right pop from list"""
        return await self._execute_with_metrics("rpop", self.client.rpop, name, count)
    
    async def lrange(self, name: str, start: int, end: int) -> List[bytes]:
        """Get list range"""
        return await self._execute_with_metrics("lrange", self.client.lrange, name, start, end)
    
    async def llen(self, name: str) -> int:
        """Get list length"""
        return await self._execute_with_metrics("llen", self.client.llen, name)
    
    # Set operations
    async def sadd(self, name: str, *values) -> int:
        """Add to set"""
        return await self._execute_with_metrics("sadd", self.client.sadd, name, *values)
    
    async def srem(self, name: str, *values) -> int:
        """Remove from set"""
        return await self._execute_with_metrics("srem", self.client.srem, name, *values)
    
    async def smembers(self, name: str) -> set:
        """Get set members"""
        return await self._execute_with_metrics("smembers", self.client.smembers, name)
    
    async def sismember(self, name: str, value: str) -> bool:
        """Check if value is in set"""
        return await self._execute_with_metrics("sismember", self.client.sismember, name, value)
    
    # Sorted set operations
    async def zadd(self, name: str, mapping: Dict[str, float], **kwargs) -> int:
        """Add to sorted set"""
        return await self._execute_with_metrics("zadd", self.client.zadd, name, mapping, **kwargs)
    
    async def zrange(self, name: str, start: int, end: int, **kwargs) -> List[bytes]:
        """Get sorted set range"""
        return await self._execute_with_metrics("zrange", self.client.zrange, name, start, end, **kwargs)
    
    async def zrem(self, name: str, *values) -> int:
        """Remove from sorted set"""
        return await self._execute_with_metrics("zrem", self.client.zrem, name, *values)
    
    # Pipeline operations
    def pipeline(self, transaction: bool = True) -> redis.client.Pipeline:
        """Create pipeline"""
        return self.client.pipeline(transaction=transaction)
    
    async def incr(self, name: str, amount: int = 1) -> int:
        """Increment key"""
        return await self._execute_with_metrics("incr", self.client.incr, name, amount)
    
    async def decr(self, name: str, amount: int = 1) -> int:
        """Decrement key"""
        return await self._execute_with_metrics("decr", self.client.decr, name, amount)
    
    # Advanced operations
    async def eval(self, script: str, numkeys: int, *keys_and_args) -> Any:
        """Execute Lua script"""
        return await self._execute_with_metrics("eval", self.client.eval, script, numkeys, *keys_and_args)
    
    async def info(self, section: Optional[str] = None) -> Dict[str, Any]:
        """Get server info"""
        return await self._execute_with_metrics("info", self.client.info, section)
    
    async def flushdb(self, asynchronous: bool = False) -> bool:
        """Flush current database"""
        return await self._execute_with_metrics("flushdb", self.client.flushdb, asynchronous=asynchronous)
    
    # Utility methods
    def get_health_status(self) -> Dict[str, Any]:
        """Get connection health status"""
        return {
            "connection_health": asdict(self.connection_health),
            "circuit_breaker": {
                "is_open": self.is_circuit_open,
                "failure_count": self.failure_count,
                "last_failure": self.last_failure_time
            },
            "metrics_summary": self._get_metrics_summary()
        }
    
    def _get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        if not self.metrics:
            return {"total_operations": 0}
        
        recent_metrics = [m for m in self.metrics 
                         if m.timestamp > datetime.utcnow() - timedelta(minutes=5)]
        
        if not recent_metrics:
            return {"total_operations": len(self.metrics)}
        
        total_time = sum(m.execution_time for m in recent_metrics)
        successful_ops = sum(1 for m in recent_metrics if m.success)
        
        return {
            "total_operations": len(self.metrics),
            "recent_operations": len(recent_metrics),
            "success_rate": round(successful_ops / len(recent_metrics) * 100, 2),
            "avg_response_time_ms": round(total_time / len(recent_metrics) * 1000, 2),
            "operations_per_minute": len(recent_metrics) * 12  # Scale to per minute
        }

# Global Redis client instance
redis_client = EnhancedRedisClient()

# Context manager for Redis operations
@asynccontextmanager
async def redis_context():
    """Context manager for Redis operations"""
    if not redis_client._initialized:
        await redis_client.initialize()
    
    try:
        yield redis_client
    except Exception as e:
        logger.error(f"Redis context error: {e}")
        raise

# Utility functions
async def ensure_redis_connection():
    """Ensure Redis connection is established"""
    if not redis_client._initialized:
        await redis_client.initialize()
    return redis_client

async def get_redis_stats() -> Dict[str, Any]:
    """Get comprehensive Redis statistics"""
    await ensure_redis_connection()
    return redis_client.get_health_status()