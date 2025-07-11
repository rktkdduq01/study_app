"""
Advanced Redis Caching System
High-performance caching with multiple strategies and optimization features
"""

import json
import time
import asyncio
import hashlib
import pickle
import zlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from enum import Enum
import functools

from app.core.logger import get_logger
from app.core.config import settings
from app.core.redis_client import redis_client

logger = get_logger(__name__)

class CacheStrategy(Enum):
    """Cache eviction strategies"""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    FIFO = "fifo"  # First In First Out

class CacheLayer(Enum):
    """Cache layer types"""
    L1_MEMORY = "l1_memory"  # In-memory cache
    L2_REDIS = "l2_redis"    # Redis cache
    L3_PERSISTENT = "l3_persistent"  # Persistent cache

@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    key: str
    layer: str
    operation: str  # get, set, delete, hit, miss
    execution_time: float
    data_size: int
    timestamp: datetime
    ttl: Optional[int] = None

@dataclass
class CacheConfiguration:
    """Cache configuration for different data types"""
    default_ttl: int = 300  # 5 minutes
    max_memory_size: int = 100 * 1024 * 1024  # 100MB
    compression_threshold: int = 1024  # Compress data larger than 1KB
    serialization_method: str = "json"  # json, pickle, msgpack
    enable_compression: bool = True
    enable_versioning: bool = True
    max_versions: int = 3

class MultiLayerCache:
    """Multi-layer caching system with L1 (memory) and L2 (Redis) layers"""
    
    def __init__(self, config: CacheConfiguration = None):
        self.config = config or CacheConfiguration()
        
        # L1 Cache (In-memory)
        self.l1_cache: Dict[str, Any] = {}
        self.l1_access_times: Dict[str, float] = {}
        self.l1_access_counts: Dict[str, int] = defaultdict(int)
        self.l1_current_size = 0
        
        # Cache metrics
        self.metrics: deque = deque(maxlen=10000)
        self.stats = {
            "l1_hits": 0,
            "l1_misses": 0,
            "l2_hits": 0,
            "l2_misses": 0,
            "total_sets": 0,
            "total_deletes": 0,
            "compression_saves": 0
        }
        
        # Background cleanup task
        self._cleanup_task = None
        self._start_background_cleanup()
    
    def _start_background_cleanup(self):
        """Start background cleanup task"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of expired L1 cache entries"""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                await self._cleanup_l1_cache()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
    
    async def _cleanup_l1_cache(self):
        """Clean up expired L1 cache entries"""
        current_time = time.time()
        expired_keys = []
        
        for key, access_time in self.l1_access_times.items():
            if current_time - access_time > self.config.default_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            if key in self.l1_cache:
                data_size = len(str(self.l1_cache[key]))
                del self.l1_cache[key]
                del self.l1_access_times[key]
                if key in self.l1_access_counts:
                    del self.l1_access_counts[key]
                self.l1_current_size -= data_size
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired L1 cache entries")
    
    def _evict_l1_if_needed(self):
        """Evict L1 cache entries if memory limit is exceeded"""
        while self.l1_current_size > self.config.max_memory_size:
            # Use LRU eviction by default
            if not self.l1_access_times:
                break
            
            oldest_key = min(self.l1_access_times.keys(), 
                           key=lambda k: self.l1_access_times[k])
            
            if oldest_key in self.l1_cache:
                data_size = len(str(self.l1_cache[oldest_key]))
                del self.l1_cache[oldest_key]
                del self.l1_access_times[oldest_key]
                if oldest_key in self.l1_access_counts:
                    del self.l1_access_counts[oldest_key]
                self.l1_current_size -= data_size
    
    def _serialize_data(self, data: Any) -> Tuple[bytes, str]:
        """Serialize data based on configuration"""
        if self.config.serialization_method == "pickle":
            serialized = pickle.dumps(data)
            method = "pickle"
        elif self.config.serialization_method == "msgpack":
            try:
                import msgpack
                serialized = msgpack.packb(data)
                method = "msgpack"
            except ImportError:
                serialized = json.dumps(data, default=str).encode()
                method = "json"
        else:
            serialized = json.dumps(data, default=str).encode()
            method = "json"
        
        # Compress if enabled and data is large enough
        if (self.config.enable_compression and 
            len(serialized) > self.config.compression_threshold):
            serialized = zlib.compress(serialized)
            method += "_compressed"
            self.stats["compression_saves"] += 1
        
        return serialized, method
    
    def _deserialize_data(self, data: bytes, method: str) -> Any:
        """Deserialize data based on method"""
        # Decompress if needed
        if method.endswith("_compressed"):
            data = zlib.decompress(data)
            method = method[:-11]  # Remove "_compressed"
        
        if method == "pickle":
            return pickle.loads(data)
        elif method == "msgpack":
            try:
                import msgpack
                return msgpack.unpackb(data)
            except ImportError:
                return json.loads(data.decode())
        else:
            return json.loads(data.decode())
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache with multi-layer fallback"""
        start_time = time.time()
        
        # Try L1 cache first
        if key in self.l1_cache:
            self.l1_access_times[key] = time.time()
            self.l1_access_counts[key] += 1
            self.stats["l1_hits"] += 1
            
            self._record_metric(key, CacheLayer.L1_MEMORY.value, "hit", 
                              time.time() - start_time, len(str(self.l1_cache[key])))
            return self.l1_cache[key]
        
        self.stats["l1_misses"] += 1
        
        # Try L2 cache (Redis)
        try:
            redis_data = await redis_client.hgetall(f"cache:{key}")
            if redis_data and b"data" in redis_data:
                data = redis_data[b"data"]
                method = redis_data.get(b"method", b"json").decode()
                
                # Deserialize
                result = self._deserialize_data(data, method)
                
                # Store in L1 cache
                self._store_in_l1(key, result)
                
                self.stats["l2_hits"] += 1
                self._record_metric(key, CacheLayer.L2_REDIS.value, "hit",
                                  time.time() - start_time, len(data))
                return result
                
        except Exception as e:
            logger.error(f"Redis cache get error for key {key}: {e}")
        
        self.stats["l2_misses"] += 1
        self._record_metric(key, CacheLayer.L2_REDIS.value, "miss",
                          time.time() - start_time, 0)
        return default
    
    def _store_in_l1(self, key: str, value: Any):
        """Store value in L1 cache"""
        data_size = len(str(value))
        
        # Check if we need to evict
        if self.l1_current_size + data_size > self.config.max_memory_size:
            self._evict_l1_if_needed()
        
        self.l1_cache[key] = value
        self.l1_access_times[key] = time.time()
        self.l1_access_counts[key] = 1
        self.l1_current_size += data_size
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None, 
                 store_in_l1: bool = True) -> bool:
        """Set value in cache with multi-layer storage"""
        start_time = time.time()
        ttl = ttl or self.config.default_ttl
        
        try:
            # Serialize data
            serialized_data, method = self._serialize_data(value)
            data_size = len(serialized_data)
            
            # Store in L2 (Redis) with metadata
            cache_data = {
                "data": serialized_data,
                "method": method,
                "created_at": datetime.utcnow().isoformat(),
                "size": data_size
            }
            
            # Use Redis hash for metadata and pipeline for atomic operation
            async with redis_client.pipeline() as pipe:
                pipe.hset(f"cache:{key}", mapping=cache_data)
                pipe.expire(f"cache:{key}", ttl)
                await pipe.execute()
            
            # Store in L1 if requested and not too large
            if store_in_l1 and data_size < self.config.max_memory_size // 10:
                self._store_in_l1(key, value)
            
            self.stats["total_sets"] += 1
            self._record_metric(key, CacheLayer.L2_REDIS.value, "set",
                              time.time() - start_time, data_size, ttl)
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from all cache layers"""
        start_time = time.time()
        
        # Delete from L1
        if key in self.l1_cache:
            data_size = len(str(self.l1_cache[key]))
            del self.l1_cache[key]
            del self.l1_access_times[key]
            if key in self.l1_access_counts:
                del self.l1_access_counts[key]
            self.l1_current_size -= data_size
        
        # Delete from L2 (Redis)
        try:
            result = await redis_client.delete(f"cache:{key}")
            self.stats["total_deletes"] += 1
            self._record_metric(key, "all_layers", "delete",
                              time.time() - start_time, 0)
            return result > 0
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache keys matching pattern"""
        try:
            # Invalidate L1 cache
            l1_deleted = 0
            keys_to_delete = [k for k in self.l1_cache.keys() if pattern in k]
            for key in keys_to_delete:
                await self.delete(key)
                l1_deleted += 1
            
            # Invalidate L2 cache
            redis_keys = await redis_client.keys(f"cache:*{pattern}*")
            if redis_keys:
                l2_deleted = await redis_client.delete(*redis_keys)
            else:
                l2_deleted = 0
            
            logger.info(f"Invalidated {l1_deleted} L1 and {l2_deleted} L2 cache entries for pattern: {pattern}")
            return l1_deleted + l2_deleted
            
        except Exception as e:
            logger.error(f"Cache pattern invalidation error: {e}")
            return 0
    
    def _record_metric(self, key: str, layer: str, operation: str, 
                      execution_time: float, data_size: int, ttl: Optional[int] = None):
        """Record cache operation metrics"""
        metric = CacheMetrics(
            key=key,
            layer=layer,
            operation=operation,
            execution_time=execution_time,
            data_size=data_size,
            timestamp=datetime.utcnow(),
            ttl=ttl
        )
        self.metrics.append(metric)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        total_l1_requests = self.stats["l1_hits"] + self.stats["l1_misses"]
        total_l2_requests = self.stats["l2_hits"] + self.stats["l2_misses"]
        
        l1_hit_rate = (self.stats["l1_hits"] / total_l1_requests * 100) if total_l1_requests > 0 else 0
        l2_hit_rate = (self.stats["l2_hits"] / total_l2_requests * 100) if total_l2_requests > 0 else 0
        
        return {
            "l1_cache": {
                "entries": len(self.l1_cache),
                "size_bytes": self.l1_current_size,
                "hit_rate": round(l1_hit_rate, 2),
                "hits": self.stats["l1_hits"],
                "misses": self.stats["l1_misses"]
            },
            "l2_cache": {
                "hit_rate": round(l2_hit_rate, 2),
                "hits": self.stats["l2_hits"],
                "misses": self.stats["l2_misses"]
            },
            "operations": {
                "total_sets": self.stats["total_sets"],
                "total_deletes": self.stats["total_deletes"],
                "compression_saves": self.stats["compression_saves"]
            },
            "performance": {
                "avg_get_time": self._calculate_avg_operation_time("get"),
                "avg_set_time": self._calculate_avg_operation_time("set")
            }
        }
    
    def _calculate_avg_operation_time(self, operation: str) -> float:
        """Calculate average operation time from metrics"""
        operation_metrics = [m for m in self.metrics if m.operation == operation]
        if not operation_metrics:
            return 0.0
        
        total_time = sum(m.execution_time for m in operation_metrics)
        return round(total_time / len(operation_metrics) * 1000, 2)  # ms

class SmartCache:
    """Smart caching system with adaptive strategies"""
    
    def __init__(self, multi_layer_cache: MultiLayerCache):
        self.cache = multi_layer_cache
        self.access_patterns: Dict[str, List[float]] = defaultdict(list)
        self.key_weights: Dict[str, float] = defaultdict(float)
    
    def _calculate_key_weight(self, key: str) -> float:
        """Calculate cache key weight based on access patterns"""
        if key not in self.access_patterns:
            return 1.0
        
        accesses = self.access_patterns[key]
        if not accesses:
            return 1.0
        
        # Calculate frequency and recency
        now = time.time()
        recent_accesses = [a for a in accesses if now - a < 3600]  # Last hour
        
        frequency_score = len(recent_accesses) / 10  # Normalize frequency
        recency_score = 1.0 / (now - max(accesses) + 1) if accesses else 0
        
        return min(frequency_score + recency_score, 5.0)  # Cap at 5.0
    
    async def smart_get(self, key: str, default: Any = None) -> Any:
        """Smart get with access pattern tracking"""
        # Record access
        self.access_patterns[key].append(time.time())
        
        # Limit access history
        if len(self.access_patterns[key]) > 100:
            self.access_patterns[key] = self.access_patterns[key][-50:]
        
        # Update key weight
        self.key_weights[key] = self._calculate_key_weight(key)
        
        return await self.cache.get(key, default)
    
    async def smart_set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Smart set with adaptive TTL"""
        # Calculate adaptive TTL based on access patterns
        if ttl is None:
            weight = self.key_weights.get(key, 1.0)
            base_ttl = self.cache.config.default_ttl
            adaptive_ttl = int(base_ttl * weight)
            ttl = max(adaptive_ttl, 60)  # Minimum 1 minute
        
        return await self.cache.set(key, value, ttl)

class CacheWarmer:
    """Cache warming system for preloading frequently accessed data"""
    
    def __init__(self, cache: MultiLayerCache):
        self.cache = cache
        self.warming_strategies: List[Callable] = []
    
    def register_warming_strategy(self, strategy: Callable):
        """Register a cache warming strategy"""
        self.warming_strategies.append(strategy)
    
    async def warm_cache(self, strategy_name: Optional[str] = None):
        """Execute cache warming strategies"""
        strategies_to_run = self.warming_strategies
        
        if strategy_name:
            strategies_to_run = [s for s in self.warming_strategies 
                               if s.__name__ == strategy_name]
        
        for strategy in strategies_to_run:
            try:
                await strategy(self.cache)
                logger.info(f"Cache warming strategy '{strategy.__name__}' completed")
            except Exception as e:
                logger.error(f"Cache warming strategy '{strategy.__name__}' failed: {e}")

class CacheDecorator:
    """Decorator for automatic function result caching"""
    
    def __init__(self, cache: MultiLayerCache, ttl: Optional[int] = None, 
                 key_prefix: str = "", invalidate_on: Optional[List[str]] = None):
        self.cache = cache
        self.ttl = ttl
        self.key_prefix = key_prefix
        self.invalidate_on = invalidate_on or []
    
    def __call__(self, func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [self.key_prefix, func.__name__]
            
            # Add args to key
            if args:
                key_parts.extend([str(arg) for arg in args])
            
            # Add kwargs to key
            if kwargs:
                key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
            
            cache_key = ":".join(key_parts)
            cache_key = hashlib.md5(cache_key.encode()).hexdigest()
            
            # Try to get from cache
            result = await self.cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await self.cache.set(cache_key, result, self.ttl)
            
            return result
        
        return wrapper

# Global cache instances
cache_config = CacheConfiguration(
    default_ttl=getattr(settings, 'CACHE_DEFAULT_TTL', 300),
    max_memory_size=getattr(settings, 'CACHE_MAX_MEMORY', 100 * 1024 * 1024),
    compression_threshold=getattr(settings, 'CACHE_COMPRESSION_THRESHOLD', 1024),
    enable_compression=getattr(settings, 'CACHE_ENABLE_COMPRESSION', True)
)

multi_layer_cache = MultiLayerCache(cache_config)
smart_cache = SmartCache(multi_layer_cache)
cache_warmer = CacheWarmer(multi_layer_cache)

# Convenience decorator
def cached(ttl: Optional[int] = None, key_prefix: str = "func_cache"):
    """Decorator for caching function results"""
    return CacheDecorator(multi_layer_cache, ttl, key_prefix)

# Context manager for cache operations
@asynccontextmanager
async def cache_context():
    """Context manager for cache operations"""
    try:
        yield {
            "multi_layer": multi_layer_cache,
            "smart": smart_cache,
            "warmer": cache_warmer
        }
    except Exception as e:
        logger.error(f"Cache context error: {e}")
        raise

# Cache warming strategies
async def warm_user_data(cache: MultiLayerCache):
    """Warm cache with frequently accessed user data"""
    # This would be implemented based on your specific data access patterns
    logger.info("Warming user data cache...")

async def warm_content_data(cache: MultiLayerCache):
    """Warm cache with content data"""
    # This would be implemented based on your specific content patterns
    logger.info("Warming content data cache...")

# Register warming strategies
cache_warmer.register_warming_strategy(warm_user_data)
cache_warmer.register_warming_strategy(warm_content_data)