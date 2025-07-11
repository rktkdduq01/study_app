"""
Intelligent Cache Invalidation System
Smart cache invalidation with dependency tracking and event-driven updates
"""

import asyncio
import json
import time
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Callable, Union
from dataclasses import dataclass, asdict, field
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from enum import Enum
import hashlib

from app.core.logger import get_logger
from app.core.redis_client import redis_client
from app.core.advanced_cache import multi_layer_cache

logger = get_logger(__name__)

class InvalidationType(Enum):
    """Cache invalidation types"""
    MANUAL = "manual"
    TIME_BASED = "time_based"
    EVENT_DRIVEN = "event_driven"
    DEPENDENCY_BASED = "dependency_based"
    PATTERN_BASED = "pattern_based"

class CacheTag(Enum):
    """Cache tags for categorization"""
    USER_DATA = "user_data"
    CONTENT = "content"
    SETTINGS = "settings"
    ANALYTICS = "analytics"
    SESSION = "session"
    API_RESPONSE = "api_response"

@dataclass
class CacheDependency:
    """Cache dependency definition"""
    cache_key: str
    depends_on: List[str]
    tags: List[str]
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    invalidation_count: int = 0

@dataclass
class InvalidationEvent:
    """Cache invalidation event"""
    event_id: str
    invalidation_type: InvalidationType
    affected_keys: List[str]
    trigger: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

class SmartCacheInvalidator:
    """Smart cache invalidation system with dependency tracking"""
    
    def __init__(self):
        self.dependencies: Dict[str, CacheDependency] = {}
        self.tag_mappings: Dict[str, Set[str]] = defaultdict(set)
        self.pattern_mappings: Dict[str, Set[str]] = defaultdict(set)
        self.invalidation_history: deque = deque(maxlen=1000)
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        
        # Background task for periodic cleanup
        self._cleanup_task = None
        self._start_background_tasks()
        
        # Statistics
        self.stats = {
            "total_invalidations": 0,
            "dependency_invalidations": 0,
            "pattern_invalidations": 0,
            "tag_invalidations": 0,
            "cache_hits_prevented": 0
        }
    
    def _start_background_tasks(self):
        """Start background tasks"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of old dependencies and history"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                await self._cleanup_old_dependencies()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cache invalidation cleanup error: {e}")
    
    async def _cleanup_old_dependencies(self):
        """Clean up old dependencies"""
        cutoff_time = datetime.utcnow() - timedelta(days=7)
        
        keys_to_remove = []
        for key, dependency in self.dependencies.items():
            if dependency.last_accessed < cutoff_time and dependency.access_count < 5:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            await self.remove_dependency(key)
        
        if keys_to_remove:
            logger.info(f"Cleaned up {len(keys_to_remove)} old cache dependencies")
    
    async def register_dependency(self, cache_key: str, depends_on: List[str], 
                                tags: List[str] = None, patterns: List[str] = None) -> bool:
        """Register cache dependency"""
        try:
            tags = tags or []
            patterns = patterns or []
            
            # Create dependency
            dependency = CacheDependency(
                cache_key=cache_key,
                depends_on=depends_on,
                tags=tags,
                created_at=datetime.utcnow(),
                last_accessed=datetime.utcnow()
            )
            
            # Store dependency
            self.dependencies[cache_key] = dependency
            
            # Update tag mappings
            for tag in tags:
                self.tag_mappings[tag].add(cache_key)
            
            # Update pattern mappings
            for pattern in patterns:
                self.pattern_mappings[pattern].add(cache_key)
            
            # Store in Redis for persistence
            await self._store_dependency_in_redis(dependency)
            
            logger.debug(f"Registered cache dependency for {cache_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register dependency for {cache_key}: {e}")
            return False
    
    async def _store_dependency_in_redis(self, dependency: CacheDependency):
        """Store dependency in Redis"""
        try:
            key = f"cache_dependency:{dependency.cache_key}"
            data = asdict(dependency)
            data['created_at'] = dependency.created_at.isoformat()
            data['last_accessed'] = dependency.last_accessed.isoformat()
            
            await redis_client.setex(key, 86400 * 7, json.dumps(data))  # 7 days TTL
            
        except Exception as e:
            logger.error(f"Failed to store dependency in Redis: {e}")
    
    async def remove_dependency(self, cache_key: str) -> bool:
        """Remove cache dependency"""
        try:
            if cache_key not in self.dependencies:
                return False
            
            dependency = self.dependencies[cache_key]
            
            # Remove from tag mappings
            for tag in dependency.tags:
                self.tag_mappings[tag].discard(cache_key)
            
            # Remove from pattern mappings
            for pattern_key, keys in self.pattern_mappings.items():
                keys.discard(cache_key)
            
            # Remove dependency
            del self.dependencies[cache_key]
            
            # Remove from Redis
            await redis_client.delete(f"cache_dependency:{cache_key}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove dependency for {cache_key}: {e}")
            return False
    
    async def invalidate_by_key(self, cache_key: str, cascade: bool = True) -> List[str]:
        """Invalidate cache by specific key"""
        invalidated_keys = []
        
        try:
            # Direct invalidation
            await multi_layer_cache.delete(cache_key)
            invalidated_keys.append(cache_key)
            
            # Cascade invalidation if enabled
            if cascade:
                dependent_keys = await self._find_dependent_keys(cache_key)
                for dependent_key in dependent_keys:
                    await multi_layer_cache.delete(dependent_key)
                    invalidated_keys.append(dependent_key)
            
            # Record invalidation event
            await self._record_invalidation_event(
                InvalidationType.MANUAL, 
                invalidated_keys, 
                f"key:{cache_key}"
            )
            
            self.stats["total_invalidations"] += len(invalidated_keys)
            
            return invalidated_keys
            
        except Exception as e:
            logger.error(f"Failed to invalidate cache key {cache_key}: {e}")
            return []
    
    async def _find_dependent_keys(self, trigger_key: str) -> List[str]:
        """Find keys that depend on the trigger key"""
        dependent_keys = []
        
        for cache_key, dependency in self.dependencies.items():
            if trigger_key in dependency.depends_on:
                dependent_keys.append(cache_key)
                # Update access stats
                dependency.last_accessed = datetime.utcnow()
                dependency.invalidation_count += 1
        
        return dependent_keys
    
    async def invalidate_by_tag(self, tag: str) -> List[str]:
        """Invalidate cache by tag"""
        try:
            cache_keys = list(self.tag_mappings.get(tag, set()))
            invalidated_keys = []
            
            for cache_key in cache_keys:
                await multi_layer_cache.delete(cache_key)
                invalidated_keys.append(cache_key)
            
            # Record invalidation event
            await self._record_invalidation_event(
                InvalidationType.EVENT_DRIVEN,
                invalidated_keys,
                f"tag:{tag}"
            )
            
            self.stats["tag_invalidations"] += len(invalidated_keys)
            self.stats["total_invalidations"] += len(invalidated_keys)
            
            logger.info(f"Invalidated {len(invalidated_keys)} cache entries by tag: {tag}")
            return invalidated_keys
            
        except Exception as e:
            logger.error(f"Failed to invalidate cache by tag {tag}: {e}")
            return []
    
    async def invalidate_by_pattern(self, pattern: str) -> List[str]:
        """Invalidate cache by pattern"""
        try:
            # Get keys matching pattern from cache
            cache_keys = await multi_layer_cache.invalidate_pattern(pattern)
            
            # Also check registered pattern mappings
            pattern_keys = []
            for registered_pattern, keys in self.pattern_mappings.items():
                if self._pattern_matches(pattern, registered_pattern):
                    pattern_keys.extend(list(keys))
            
            # Combine and deduplicate
            all_keys = list(set(pattern_keys))
            
            # Invalidate from cache
            for cache_key in all_keys:
                await multi_layer_cache.delete(cache_key)
            
            total_invalidated = cache_keys + len(all_keys)
            
            # Record invalidation event
            await self._record_invalidation_event(
                InvalidationType.PATTERN_BASED,
                all_keys,
                f"pattern:{pattern}"
            )
            
            self.stats["pattern_invalidations"] += total_invalidated
            self.stats["total_invalidations"] += total_invalidated
            
            logger.info(f"Invalidated {total_invalidated} cache entries by pattern: {pattern}")
            return all_keys
            
        except Exception as e:
            logger.error(f"Failed to invalidate cache by pattern {pattern}: {e}")
            return []
    
    def _pattern_matches(self, pattern: str, registered_pattern: str) -> bool:
        """Check if pattern matches registered pattern"""
        # Convert glob-style pattern to regex
        regex_pattern = pattern.replace('*', '.*').replace('?', '.')
        return bool(re.match(regex_pattern, registered_pattern))
    
    async def invalidate_by_event(self, event_name: str, event_data: Dict[str, Any] = None) -> List[str]:
        """Invalidate cache based on application event"""
        try:
            event_data = event_data or {}
            invalidated_keys = []
            
            # Execute registered event handlers
            if event_name in self.event_handlers:
                for handler in self.event_handlers[event_name]:
                    try:
                        handler_keys = await handler(event_data)
                        if handler_keys:
                            invalidated_keys.extend(handler_keys)
                    except Exception as e:
                        logger.error(f"Event handler error for {event_name}: {e}")
            
            # Record invalidation event
            if invalidated_keys:
                await self._record_invalidation_event(
                    InvalidationType.EVENT_DRIVEN,
                    invalidated_keys,
                    f"event:{event_name}",
                    event_data
                )
            
            self.stats["total_invalidations"] += len(invalidated_keys)
            
            return invalidated_keys
            
        except Exception as e:
            logger.error(f"Failed to invalidate cache by event {event_name}: {e}")
            return []
    
    def register_event_handler(self, event_name: str, handler: Callable):
        """Register event handler for cache invalidation"""
        self.event_handlers[event_name].append(handler)
        logger.info(f"Registered cache invalidation handler for event: {event_name}")
    
    async def _record_invalidation_event(self, invalidation_type: InvalidationType,
                                       affected_keys: List[str], trigger: str,
                                       metadata: Dict[str, Any] = None):
        """Record cache invalidation event"""
        try:
            event = InvalidationEvent(
                event_id=hashlib.md5(f"{trigger}:{time.time()}".encode()).hexdigest(),
                invalidation_type=invalidation_type,
                affected_keys=affected_keys,
                trigger=trigger,
                timestamp=datetime.utcnow(),
                metadata=metadata or {}
            )
            
            self.invalidation_history.append(event)
            
            # Store in Redis for analysis
            event_key = f"cache_invalidation_event:{event.event_id}"
            event_data = asdict(event)
            event_data['timestamp'] = event.timestamp.isoformat()
            event_data['invalidation_type'] = event.invalidation_type.value
            
            await redis_client.setex(event_key, 86400, json.dumps(event_data))
            
        except Exception as e:
            logger.error(f"Failed to record invalidation event: {e}")
    
    async def bulk_invalidate(self, operations: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Perform bulk cache invalidation operations"""
        results = {}
        
        for operation in operations:
            op_type = operation.get('type')
            op_value = operation.get('value')
            
            try:
                if op_type == 'key':
                    results[f"key:{op_value}"] = await self.invalidate_by_key(op_value)
                elif op_type == 'tag':
                    results[f"tag:{op_value}"] = await self.invalidate_by_tag(op_value)
                elif op_type == 'pattern':
                    results[f"pattern:{op_value}"] = await self.invalidate_by_pattern(op_value)
                elif op_type == 'event':
                    event_data = operation.get('data', {})
                    results[f"event:{op_value}"] = await self.invalidate_by_event(op_value, event_data)
                    
            except Exception as e:
                logger.error(f"Bulk invalidation operation failed: {operation} - {e}")
                results[f"{op_type}:{op_value}"] = []
        
        return results
    
    async def schedule_invalidation(self, cache_key: str, delay_seconds: int):
        """Schedule cache invalidation after delay"""
        async def delayed_invalidation():
            await asyncio.sleep(delay_seconds)
            await self.invalidate_by_key(cache_key)
        
        asyncio.create_task(delayed_invalidation())
        logger.info(f"Scheduled invalidation of {cache_key} in {delay_seconds} seconds")
    
    def get_dependency_graph(self) -> Dict[str, Any]:
        """Get cache dependency graph"""
        graph = {
            "nodes": [],
            "edges": []
        }
        
        # Add nodes
        for cache_key, dependency in self.dependencies.items():
            graph["nodes"].append({
                "id": cache_key,
                "tags": dependency.tags,
                "access_count": dependency.access_count,
                "invalidation_count": dependency.invalidation_count,
                "last_accessed": dependency.last_accessed.isoformat()
            })
        
        # Add edges (dependencies)
        for cache_key, dependency in self.dependencies.items():
            for dep_key in dependency.depends_on:
                graph["edges"].append({
                    "from": dep_key,
                    "to": cache_key
                })
        
        return graph
    
    def get_invalidation_stats(self) -> Dict[str, Any]:
        """Get cache invalidation statistics"""
        recent_events = [
            event for event in self.invalidation_history
            if event.timestamp > datetime.utcnow() - timedelta(hours=1)
        ]
        
        event_types = defaultdict(int)
        for event in recent_events:
            event_types[event.invalidation_type.value] += 1
        
        return {
            "total_stats": self.stats.copy(),
            "recent_events": len(recent_events),
            "event_types": dict(event_types),
            "active_dependencies": len(self.dependencies),
            "tag_mappings": {tag: len(keys) for tag, keys in self.tag_mappings.items()},
            "pattern_mappings": {pattern: len(keys) for pattern, keys in self.pattern_mappings.items()}
        }
    
    async def analyze_cache_efficiency(self) -> Dict[str, Any]:
        """Analyze cache efficiency and suggest optimizations"""
        analysis = {
            "frequently_invalidated": [],
            "unused_dependencies": [],
            "optimization_suggestions": []
        }
        
        # Find frequently invalidated keys
        frequent_threshold = 10
        for dependency in self.dependencies.values():
            if dependency.invalidation_count > frequent_threshold:
                analysis["frequently_invalidated"].append({
                    "cache_key": dependency.cache_key,
                    "invalidation_count": dependency.invalidation_count,
                    "access_count": dependency.access_count
                })
        
        # Find unused dependencies
        cutoff_time = datetime.utcnow() - timedelta(days=3)
        for dependency in self.dependencies.values():
            if (dependency.last_accessed < cutoff_time and 
                dependency.access_count < 5):
                analysis["unused_dependencies"].append(dependency.cache_key)
        
        # Generate optimization suggestions
        if analysis["frequently_invalidated"]:
            analysis["optimization_suggestions"].append(
                "Consider using more specific cache keys or shorter TTL for frequently invalidated data"
            )
        
        if analysis["unused_dependencies"]:
            analysis["optimization_suggestions"].append(
                f"Remove {len(analysis['unused_dependencies'])} unused cache dependencies"
            )
        
        return analysis

# Global cache invalidator instance
cache_invalidator = SmartCacheInvalidator()

# Predefined event handlers
async def user_data_changed_handler(event_data: Dict[str, Any]) -> List[str]:
    """Handle user data change events"""
    user_id = event_data.get('user_id')
    if not user_id:
        return []
    
    # Invalidate user-related cache keys
    invalidated_keys = []
    patterns = [
        f"user:{user_id}:*",
        f"profile:{user_id}",
        f"settings:{user_id}:*"
    ]
    
    for pattern in patterns:
        keys = await cache_invalidator.invalidate_by_pattern(pattern)
        invalidated_keys.extend(keys)
    
    return invalidated_keys

async def content_updated_handler(event_data: Dict[str, Any]) -> List[str]:
    """Handle content update events"""
    content_id = event_data.get('content_id')
    content_type = event_data.get('content_type', 'general')
    
    if not content_id:
        return []
    
    # Invalidate content-related cache
    invalidated_keys = []
    patterns = [
        f"content:{content_id}:*",
        f"list:{content_type}:*",
        "homepage:*"  # Homepage might show this content
    ]
    
    for pattern in patterns:
        keys = await cache_invalidator.invalidate_by_pattern(pattern)
        invalidated_keys.extend(keys)
    
    return invalidated_keys

# Register default event handlers
cache_invalidator.register_event_handler("user_data_changed", user_data_changed_handler)
cache_invalidator.register_event_handler("content_updated", content_updated_handler)

# Context manager for cache invalidation
@asynccontextmanager
async def invalidation_context():
    """Context manager for cache invalidation operations"""
    try:
        yield cache_invalidator
    except Exception as e:
        logger.error(f"Cache invalidation context error: {e}")
        raise

# Utility functions
async def invalidate_user_cache(user_id: str) -> List[str]:
    """Invalidate all cache related to a user"""
    return await cache_invalidator.invalidate_by_tag(f"user:{user_id}")

async def invalidate_content_cache(content_type: str = None) -> List[str]:
    """Invalidate content cache"""
    if content_type:
        return await cache_invalidator.invalidate_by_tag(f"content:{content_type}")
    else:
        return await cache_invalidator.invalidate_by_tag("content")

async def trigger_cache_event(event_name: str, event_data: Dict[str, Any] = None) -> List[str]:
    """Trigger cache invalidation event"""
    return await cache_invalidator.invalidate_by_event(event_name, event_data)