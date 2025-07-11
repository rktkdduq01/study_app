"""
Database query optimization utilities
"""
from typing import List, Dict, Any, Optional, Type, TypeVar
from sqlalchemy import event, text
from sqlalchemy.orm import Session, Query, joinedload, selectinload, contains_eager
from sqlalchemy.engine import Engine
from sqlalchemy.sql import Select
from functools import wraps
import time
import logging

from app.core.config import settings
from app.utils.logger import performance_logger

T = TypeVar('T')


class QueryOptimizer:
    """
    Query optimization utilities for SQLAlchemy.
    
    Features:
    - N+1 query prevention
    - Query result caching
    - Batch loading
    - Query plan analysis
    - Index usage verification
    """
    
    @staticmethod
    def optimize_relationship_loading(
        query: Query,
        relationships: List[str],
        strategy: str = 'selectin'
    ) -> Query:
        """
        Optimize relationship loading to prevent N+1 queries.
        
        Strategies:
        - 'selectin': Uses IN loading (good for <1000 items)
        - 'joined': Uses JOIN (good for 1-to-1 or small 1-to-many)
        - 'subquery': Uses subquery (good for large 1-to-many)
        
        Example:
            users = QueryOptimizer.optimize_relationship_loading(
                db.query(User),
                ['character', 'quests.progress'],
                strategy='selectin'
            ).all()
        """
        for relationship in relationships:
            if '.' in relationship:
                # Handle nested relationships
                parts = relationship.split('.')
                if strategy == 'selectin':
                    query = query.options(selectinload(parts[0]))
                    current = selectinload(parts[0])
                    for part in parts[1:]:
                        current = current.selectinload(part)
                    query = query.options(current)
                elif strategy == 'joined':
                    query = query.options(joinedload(parts[0]))
                    current = joinedload(parts[0])
                    for part in parts[1:]:
                        current = current.joinedload(part)
                    query = query.options(current)
            else:
                # Simple relationship
                if strategy == 'selectin':
                    query = query.options(selectinload(relationship))
                elif strategy == 'joined':
                    query = query.options(joinedload(relationship))
        
        return query
    
    @staticmethod
    def batch_load(
        db: Session,
        model: Type[T],
        ids: List[int],
        batch_size: int = 1000
    ) -> List[T]:
        """
        Load entities in batches to avoid query size limits.
        
        Example:
            users = QueryOptimizer.batch_load(db, User, user_ids, batch_size=500)
        """
        results = []
        
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i + batch_size]
            batch_results = db.query(model).filter(
                model.id.in_(batch_ids)
            ).all()
            results.extend(batch_results)
        
        return results
    
    @staticmethod
    def paginate_large_dataset(
        query: Query,
        page_size: int = 1000,
        order_by: Any = None
    ):
        """
        Generator for efficiently paginating large datasets.
        
        Example:
            for batch in QueryOptimizer.paginate_large_dataset(
                db.query(Quest),
                page_size=500,
                order_by=Quest.id
            ):
                process_quests(batch)
        """
        if order_by is not None:
            query = query.order_by(order_by)
        
        offset = 0
        while True:
            batch = query.limit(page_size).offset(offset).all()
            if not batch:
                break
            yield batch
            offset += page_size
    
    @staticmethod
    def analyze_query_plan(db: Session, query: Query) -> Dict[str, Any]:
        """
        Analyze query execution plan for optimization opportunities.
        
        Returns information about:
        - Estimated cost
        - Index usage
        - Join types
        - Potential issues
        """
        # Convert SQLAlchemy query to SQL
        compiled = query.statement.compile(
            compile_kwargs={"literal_binds": True}
        )
        sql = str(compiled)
        
        # Get query plan
        result = db.execute(text(f"EXPLAIN ANALYZE {sql}"))
        plan_lines = [row[0] for row in result]
        
        # Analyze plan
        analysis = {
            'sql': sql,
            'plan': plan_lines,
            'uses_index': any('Index' in line for line in plan_lines),
            'has_sequential_scan': any('Seq Scan' in line for line in plan_lines),
            'has_nested_loop': any('Nested Loop' in line for line in plan_lines),
            'estimated_cost': None,
            'actual_time': None,
            'warnings': []
        }
        
        # Extract metrics
        for line in plan_lines:
            if 'cost=' in line:
                cost_match = line.split('cost=')[1].split(' ')[0]
                analysis['estimated_cost'] = float(cost_match.split('..')[1])
            
            if 'actual time=' in line:
                time_match = line.split('actual time=')[1].split(' ')[0]
                analysis['actual_time'] = float(time_match.split('..')[1])
        
        # Generate warnings
        if analysis['has_sequential_scan']:
            analysis['warnings'].append(
                "Query uses sequential scan. Consider adding an index."
            )
        
        if analysis['has_nested_loop'] and analysis.get('actual_time', 0) > 100:
            analysis['warnings'].append(
                "Slow nested loop detected. Consider query restructuring."
            )
        
        return analysis


class QueryCache:
    """
    Simple query result caching mechanism.
    
    Usage:
        @QueryCache.cache("user_profile", ttl=300)
        def get_user_profile(user_id: int):
            return db.query(User).filter(User.id == user_id).first()
    """
    
    _cache: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    def cache(cls, cache_key_prefix: str, ttl: int = 300):
        """
        Decorator for caching query results.
        
        Args:
            cache_key_prefix: Prefix for cache keys
            ttl: Time to live in seconds
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = f"{cache_key_prefix}:{args}:{kwargs}"
                
                # Check cache
                if cache_key in cls._cache:
                    cached = cls._cache[cache_key]
                    if time.time() - cached['timestamp'] < ttl:
                        performance_logger.debug(
                            "Cache hit",
                            cache_key=cache_key
                        )
                        return cached['result']
                
                # Execute query
                result = func(*args, **kwargs)
                
                # Store in cache
                cls._cache[cache_key] = {
                    'result': result,
                    'timestamp': time.time()
                }
                
                return result
            
            return wrapper
        return decorator
    
    @classmethod
    def invalidate(cls, pattern: Optional[str] = None):
        """Invalidate cache entries matching pattern"""
        if pattern is None:
            cls._cache.clear()
        else:
            keys_to_remove = [
                key for key in cls._cache.keys()
                if pattern in key
            ]
            for key in keys_to_remove:
                del cls._cache[key]


def setup_query_logging(engine: Engine):
    """
    Setup query logging for performance monitoring.
    
    Logs:
    - Slow queries (> threshold)
    - Query execution time
    - Query frequency
    """
    slow_query_threshold = settings.SLOW_QUERY_THRESHOLD_MS / 1000  # Convert to seconds
    
    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        conn.info.setdefault('query_start_time', []).append(time.time())
        conn.info.setdefault('query_statement', []).append(statement)
    
    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        total_time = time.time() - conn.info['query_start_time'].pop(-1)
        
        # Log slow queries
        if total_time > slow_query_threshold:
            performance_logger.warning(
                "Slow query detected",
                duration=total_time,
                statement=statement[:200],  # Truncate long queries
                parameters=parameters
            )
        
        # Always log in debug mode
        performance_logger.debug(
            "Query executed",
            duration=total_time,
            statement=statement[:100]
        )


# Query optimization helpers
def optimize_user_query(query: Query) -> Query:
    """Optimize user queries with common relationships"""
    return QueryOptimizer.optimize_relationship_loading(
        query,
        ['character', 'character.stats', 'quest_progress'],
        strategy='selectin'
    )


def optimize_quest_query(query: Query) -> Query:
    """Optimize quest queries with progress tracking"""
    return QueryOptimizer.optimize_relationship_loading(
        query,
        ['progress', 'requirements', 'rewards'],
        strategy='selectin'
    )


def optimize_multiplayer_query(query: Query) -> Query:
    """Optimize multiplayer session queries"""
    return QueryOptimizer.optimize_relationship_loading(
        query,
        ['participants', 'participants.user', 'chat_room'],
        strategy='selectin'
    )


# Index recommendations
INDEX_RECOMMENDATIONS = {
    'users': [
        'CREATE INDEX idx_users_email ON users(email);',
        'CREATE INDEX idx_users_username ON users(username);',
        'CREATE INDEX idx_users_created_at ON users(created_at DESC);'
    ],
    'quests': [
        'CREATE INDEX idx_quests_type_difficulty ON quests(quest_type, difficulty);',
        'CREATE INDEX idx_quests_subject_level ON quests(subject, min_level);',
        'CREATE INDEX idx_quests_is_active ON quests(is_active) WHERE is_active = true;'
    ],
    'quest_progress': [
        'CREATE INDEX idx_quest_progress_user_status ON quest_progress(user_id, status);',
        'CREATE INDEX idx_quest_progress_quest_id ON quest_progress(quest_id);',
        'CREATE INDEX idx_quest_progress_completed_at ON quest_progress(completed_at DESC);'
    ],
    'learning_sessions': [
        'CREATE INDEX idx_learning_sessions_user_subject ON learning_sessions(user_id, subject);',
        'CREATE INDEX idx_learning_sessions_start_time ON learning_sessions(start_time DESC);'
    ],
    'multiplayer_sessions': [
        'CREATE INDEX idx_multiplayer_sessions_code ON multiplayer_sessions(session_code);',
        'CREATE INDEX idx_multiplayer_sessions_status ON multiplayer_sessions(status);',
        'CREATE INDEX idx_multiplayer_sessions_type_public ON multiplayer_sessions(type, is_public);'
    ]
}


def generate_index_creation_script() -> str:
    """Generate SQL script for creating recommended indexes"""
    script = "-- Performance optimization indexes\n\n"
    
    for table, indexes in INDEX_RECOMMENDATIONS.items():
        script += f"-- Indexes for {table}\n"
        for index in indexes:
            script += f"{index}\n"
        script += "\n"
    
    return script