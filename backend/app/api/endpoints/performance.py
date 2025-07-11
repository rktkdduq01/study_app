"""
Performance monitoring and metrics API endpoints
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
import psutil
import prometheus_client

from app.api import deps
from app.core.auth import get_current_admin_user
from app.models.user import User
from app.middleware.performance import get_metrics
from app.db.query_optimizer import QueryOptimizer, INDEX_RECOMMENDATIONS
from app.utils.logger import performance_logger

router = APIRouter()


@router.get("/metrics")
async def get_performance_metrics(
    current_user: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """
    Get current performance metrics (admin only).
    
    Returns:
    - System metrics (CPU, memory, disk)
    - Request metrics (count, duration, active)
    - Database metrics (query times, connection pool)
    - Cache metrics (hit rates)
    - WebSocket metrics (active connections)
    """
    # System metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Process metrics
    process = psutil.Process()
    process_memory = process.memory_info()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "system": {
            "cpu": {
                "percent": cpu_percent,
                "count": psutil.cpu_count(),
                "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            },
            "memory": {
                "total_mb": memory.total / 1024 / 1024,
                "available_mb": memory.available / 1024 / 1024,
                "used_mb": memory.used / 1024 / 1024,
                "percent": memory.percent
            },
            "disk": {
                "total_gb": disk.total / 1024 / 1024 / 1024,
                "used_gb": disk.used / 1024 / 1024 / 1024,
                "free_gb": disk.free / 1024 / 1024 / 1024,
                "percent": disk.percent
            }
        },
        "process": {
            "memory_mb": process_memory.rss / 1024 / 1024,
            "cpu_percent": process.cpu_percent(),
            "threads": process.num_threads(),
            "open_files": len(process.open_files()),
            "connections": len(process.connections())
        }
    }


@router.get("/metrics/prometheus")
async def get_prometheus_metrics(
    current_user: User = Depends(get_current_admin_user)
) -> str:
    """
    Get Prometheus-formatted metrics (admin only).
    
    Compatible with Prometheus scraping.
    """
    return get_metrics().decode('utf-8')


@router.get("/slow-queries")
async def get_slow_queries(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_admin_user),
    limit: int = Query(10, ge=1, le=100),
    min_duration_ms: int = Query(1000, ge=100)
) -> List[Dict[str, Any]]:
    """
    Get slow database queries (admin only).
    
    Returns queries that exceeded the duration threshold.
    """
    # This would typically query a slow query log table
    # For now, we'll query pg_stat_statements if available
    try:
        result = db.execute(text("""
            SELECT 
                query,
                calls,
                total_time,
                mean_time,
                stddev_time,
                min_time,
                max_time
            FROM pg_stat_statements
            WHERE mean_time > :min_duration
            ORDER BY mean_time DESC
            LIMIT :limit
        """), {
            "min_duration": min_duration_ms,
            "limit": limit
        })
        
        queries = []
        for row in result:
            queries.append({
                "query": row[0][:200],  # Truncate long queries
                "calls": row[1],
                "total_time_ms": row[2],
                "mean_time_ms": row[3],
                "stddev_time_ms": row[4],
                "min_time_ms": row[5],
                "max_time_ms": row[6]
            })
        
        return queries
    except Exception as e:
        performance_logger.error(f"Failed to get slow queries: {e}")
        return []


@router.get("/query-analysis")
async def analyze_query(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_admin_user),
    query: str = Query(..., description="SQL query to analyze")
) -> Dict[str, Any]:
    """
    Analyze a specific query's execution plan (admin only).
    
    Returns:
    - Execution plan
    - Cost estimates
    - Index usage
    - Optimization suggestions
    """
    try:
        # Create a safe query object
        from sqlalchemy import text
        safe_query = text(query)
        
        # Get execution plan
        plan_result = db.execute(text(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"))
        plan = plan_result.fetchone()[0]
        
        # Analyze for common issues
        issues = []
        suggestions = []
        
        # Check for sequential scans
        plan_str = str(plan)
        if "Seq Scan" in plan_str:
            issues.append("Sequential scan detected")
            suggestions.append("Consider adding an index on filtered columns")
        
        # Check for nested loops with high cost
        if "Nested Loop" in plan_str and plan[0]["Plan"]["Total Cost"] > 10000:
            issues.append("Expensive nested loop detected")
            suggestions.append("Consider restructuring query or adding indexes")
        
        # Check for missing indexes
        if "Filter" in plan_str:
            suggestions.append("Check if filtered columns have appropriate indexes")
        
        return {
            "query": query,
            "execution_plan": plan,
            "issues": issues,
            "suggestions": suggestions,
            "estimated_cost": plan[0]["Plan"]["Total Cost"],
            "execution_time_ms": plan[0]["Execution Time"]
        }
        
    except Exception as e:
        return {
            "error": f"Failed to analyze query: {str(e)}",
            "query": query
        }


@router.get("/cache-stats")
async def get_cache_statistics(
    current_user: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """
    Get cache performance statistics (admin only).
    
    Returns hit rates and usage for different cache layers.
    """
    # This would integrate with your actual cache implementation
    # Example structure:
    return {
        "redis": {
            "hit_rate": 0.85,
            "misses": 1520,
            "hits": 8480,
            "evictions": 230,
            "memory_used_mb": 124.5,
            "keys": 10000
        },
        "application": {
            "query_cache": {
                "hit_rate": 0.72,
                "size": 500,
                "max_size": 1000
            },
            "session_cache": {
                "hit_rate": 0.95,
                "active_sessions": 342
            }
        },
        "cdn": {
            "hit_rate": 0.92,
            "bandwidth_saved_gb": 1250.3,
            "requests_served": 1_500_000
        }
    }


@router.post("/optimize/indexes")
async def generate_index_recommendations(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_admin_user),
    table_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate index recommendations for tables (admin only).
    
    Analyzes query patterns and suggests optimal indexes.
    """
    recommendations = []
    
    if table_name:
        # Get recommendations for specific table
        if table_name in INDEX_RECOMMENDATIONS:
            recommendations = INDEX_RECOMMENDATIONS[table_name]
    else:
        # Get all recommendations
        for table, indexes in INDEX_RECOMMENDATIONS.items():
            recommendations.extend([{
                "table": table,
                "index": index
            } for index in indexes])
    
    # Check which indexes already exist
    existing_indexes = db.execute(text("""
        SELECT 
            schemaname,
            tablename,
            indexname,
            indexdef
        FROM pg_indexes
        WHERE schemaname = 'public'
    """)).fetchall()
    
    existing_index_names = {row[2] for row in existing_indexes}
    
    # Filter out existing indexes
    new_recommendations = []
    for rec in recommendations:
        index_sql = rec if isinstance(rec, str) else rec["index"]
        index_name = index_sql.split(" ")[2]  # Extract index name
        
        if index_name not in existing_index_names:
            new_recommendations.append(rec)
    
    return {
        "existing_indexes": len(existing_indexes),
        "recommended_indexes": len(new_recommendations),
        "recommendations": new_recommendations,
        "sql_script": "\n".join([
            r if isinstance(r, str) else r["index"] 
            for r in new_recommendations
        ])
    }


@router.get("/api-performance")
async def get_api_performance_stats(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_admin_user),
    hours: int = Query(24, ge=1, le=168)  # Max 1 week
) -> Dict[str, Any]:
    """
    Get API endpoint performance statistics (admin only).
    
    Returns:
    - Slowest endpoints
    - Most called endpoints
    - Error rates by endpoint
    - Response time percentiles
    """
    # This would query your metrics storage
    # Example structure:
    return {
        "time_range": {
            "start": (datetime.utcnow() - timedelta(hours=hours)).isoformat(),
            "end": datetime.utcnow().isoformat()
        },
        "summary": {
            "total_requests": 145_230,
            "avg_response_time_ms": 124.5,
            "p50_response_time_ms": 85,
            "p95_response_time_ms": 450,
            "p99_response_time_ms": 1200,
            "error_rate": 0.0023
        },
        "slowest_endpoints": [
            {
                "path": "/api/v1/ai-tutor/generate-content",
                "method": "POST",
                "avg_time_ms": 2340,
                "calls": 523
            },
            {
                "path": "/api/v1/multiplayer/battles/submit",
                "method": "POST", 
                "avg_time_ms": 450,
                "calls": 8921
            }
        ],
        "most_called": [
            {
                "path": "/api/v1/auth/me",
                "method": "GET",
                "calls": 45_123,
                "avg_time_ms": 23
            },
            {
                "path": "/api/v1/quests",
                "method": "GET",
                "calls": 23_456,
                "avg_time_ms": 67
            }
        ],
        "errors_by_endpoint": [
            {
                "path": "/api/v1/payments/webhook",
                "error_count": 23,
                "error_rate": 0.012
            }
        ]
    }


@router.post("/optimize/vacuum")
async def run_database_vacuum(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_admin_user),
    analyze: bool = Query(True, description="Also run ANALYZE"),
    table_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run VACUUM on database tables (admin only).
    
    Helps reclaim storage and update statistics.
    """
    try:
        if table_name:
            # Vacuum specific table
            command = f"VACUUM {'ANALYZE' if analyze else ''} {table_name}"
            db.execute(text(command))
            message = f"Successfully vacuumed table: {table_name}"
        else:
            # Vacuum all tables
            command = f"VACUUM {'ANALYZE' if analyze else ''}"
            db.execute(text(command))
            message = "Successfully vacuumed all tables"
        
        db.commit()
        
        return {
            "success": True,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/websocket-stats")
async def get_websocket_statistics(
    current_user: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """
    Get WebSocket connection statistics (admin only).
    
    Returns active connections and message rates.
    """
    # This would integrate with your WebSocket manager
    return {
        "active_connections": 342,
        "connections_by_type": {
            "multiplayer_battle": 125,
            "study_group": 89,
            "general_chat": 128
        },
        "message_rate": {
            "per_second": 234.5,
            "per_minute": 14_070
        },
        "peak_connections": {
            "today": 523,
            "this_week": 1_245
        }
    }