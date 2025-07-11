"""
Log Analysis API Endpoints
REST API for log centralization, search, and analysis dashboard
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query, HTTPException, Depends, Body
from pydantic import BaseModel, Field

from app.core.logger import get_logger
from app.core.log_aggregator import (
    log_aggregator, LogLevel, LogSource, LogEntry, LogAnalysis,
    log_to_aggregator, get_log_analysis
)

logger = get_logger(__name__)

# Pydantic models
class LogSearchRequest(BaseModel):
    query: Optional[str] = None
    start_time: datetime
    end_time: datetime
    level: Optional[str] = Field(None, regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    source: Optional[str] = Field(None, regex="^(application|system|database|cache|security|business|external)$")
    module: Optional[str] = None
    limit: int = Field(default=1000, ge=1, le=10000)

class LogIngestRequest(BaseModel):
    level: str = Field(..., regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    source: str = Field(..., regex="^(application|system|database|cache|security|business|external)$")
    module: str
    message: str
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None

class LogAnalysisResponse(BaseModel):
    total_logs: int
    time_range: Dict[str, str]
    log_levels: Dict[str, int]
    log_sources: Dict[str, int]
    error_patterns: List[Dict[str, Any]]
    anomalies: List[Dict[str, Any]]
    trends: Dict[str, Any]
    top_errors: List[Dict[str, Any]]
    performance_insights: List[Dict[str, Any]]

# Create router
router = APIRouter(prefix="/logs", tags=["Logs"])

@router.post("/ingest")
async def ingest_log(log_request: LogIngestRequest):
    """Ingest a single log entry"""
    try:
        success = await log_to_aggregator(
            level=LogLevel(log_request.level),
            source=LogSource(log_request.source),
            module=log_request.module,
            message=log_request.message,
            trace_id=log_request.trace_id,
            span_id=log_request.span_id,
            user_id=log_request.user_id,
            session_id=log_request.session_id,
            request_id=log_request.request_id,
            metadata=log_request.metadata or {},
            tags=log_request.tags or []
        )
        
        if success:
            return {"status": "success", "message": "Log entry ingested"}
        else:
            raise HTTPException(status_code=400, detail="Failed to ingest log entry")
            
    except Exception as e:
        logger.error(f"Failed to ingest log: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ingest/batch")
async def ingest_logs_batch(log_requests: List[LogIngestRequest]):
    """Ingest multiple log entries"""
    try:
        log_entries = []
        
        for log_request in log_requests:
            log_entry = LogEntry(
                timestamp=datetime.utcnow(),
                level=LogLevel(log_request.level),
                source=LogSource(log_request.source),
                module=log_request.module,
                message=log_request.message,
                trace_id=log_request.trace_id,
                span_id=log_request.span_id,
                user_id=log_request.user_id,
                session_id=log_request.session_id,
                request_id=log_request.request_id,
                metadata=log_request.metadata or {},
                tags=log_request.tags or []
            )
            log_entries.append(log_entry)
        
        successful = await log_aggregator.ingest_logs_batch(log_entries)
        
        return {
            "status": "success",
            "total": len(log_requests),
            "successful": successful,
            "failed": len(log_requests) - successful
        }
        
    except Exception as e:
        logger.error(f"Failed to ingest log batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search")
async def search_logs(search_request: LogSearchRequest):
    """Search logs with filters"""
    try:
        # Convert string enums to enum objects
        level = LogLevel(search_request.level) if search_request.level else None
        source = LogSource(search_request.source) if search_request.source else None
        
        results = await log_aggregator.search_logs(
            query=search_request.query,
            start_time=search_request.start_time,
            end_time=search_request.end_time,
            level=level,
            source=source,
            limit=search_request.limit
        )
        
        return {
            "status": "success",
            "query": search_request.query,
            "filters": {
                "start_time": search_request.start_time.isoformat(),
                "end_time": search_request.end_time.isoformat(),
                "level": search_request.level,
                "source": search_request.source,
                "module": search_request.module
            },
            "total_results": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Log search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/{time_window}")
async def get_log_analysis_endpoint(
    time_window: str = Query(..., regex="^(1h|24h|7d)$")
):
    """Get log analysis for time window"""
    try:
        analysis = await get_log_analysis(time_window)
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not available for this time window")
        
        return {
            "status": "success",
            "time_window": time_window,
            "analysis": {
                "total_logs": analysis.total_logs,
                "time_range": analysis.time_range,
                "log_levels": analysis.log_levels,
                "log_sources": analysis.log_sources,
                "error_patterns": analysis.error_patterns,
                "anomalies": analysis.anomalies,
                "trends": analysis.trends,
                "top_errors": analysis.top_errors,
                "performance_insights": analysis.performance_insights
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get log analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard")
async def get_log_dashboard():
    """Get comprehensive log dashboard data"""
    try:
        # Get analysis for different time windows
        analysis_1h = await get_log_analysis("1h")
        analysis_24h = await get_log_analysis("24h")
        analysis_7d = await get_log_analysis("7d")
        
        # Get aggregator stats
        stats = log_aggregator.get_stats()
        
        # Get recent anomalies
        recent_anomalies = []
        if analysis_24h and analysis_24h.anomalies:
            recent_anomalies = analysis_24h.anomalies[-10:]  # Last 10 anomalies
        
        # Calculate key metrics
        current_error_rate = 0
        if analysis_1h and analysis_1h.total_logs > 0:
            error_count = analysis_1h.log_levels.get("ERROR", 0) + analysis_1h.log_levels.get("CRITICAL", 0)
            current_error_rate = (error_count / analysis_1h.total_logs) * 100
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "overview": {
                "current_error_rate": round(current_error_rate, 2),
                "total_logs_24h": analysis_24h.total_logs if analysis_24h else 0,
                "active_anomalies": len(recent_anomalies),
                "buffer_size": stats.get("buffer_size", 0)
            },
            "time_windows": {
                "1h": {
                    "total_logs": analysis_1h.total_logs if analysis_1h else 0,
                    "log_levels": analysis_1h.log_levels if analysis_1h else {},
                    "log_sources": analysis_1h.log_sources if analysis_1h else {}
                },
                "24h": {
                    "total_logs": analysis_24h.total_logs if analysis_24h else 0,
                    "log_levels": analysis_24h.log_levels if analysis_24h else {},
                    "log_sources": analysis_24h.log_sources if analysis_24h else {},
                    "anomalies": analysis_24h.anomalies if analysis_24h else []
                },
                "7d": {
                    "total_logs": analysis_7d.total_logs if analysis_7d else 0,
                    "trends": analysis_7d.trends if analysis_7d else {}
                }
            },
            "recent_anomalies": recent_anomalies,
            "top_errors": analysis_24h.top_errors if analysis_24h else [],
            "performance_insights": analysis_24h.performance_insights if analysis_24h else [],
            "system_stats": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get log dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/patterns")
async def get_log_patterns():
    """Get log patterns and their statistics"""
    try:
        patterns = []
        
        for pattern_id, pattern in log_aggregator.patterns.items():
            patterns.append({
                "id": pattern.pattern_id,
                "name": pattern.name,
                "category": pattern.category,
                "description": pattern.description,
                "level": pattern.level.value,
                "count": pattern.count,
                "last_seen": pattern.last_seen.isoformat() if pattern.last_seen else None
            })
        
        # Sort by count descending
        patterns.sort(key=lambda x: x["count"], reverse=True)
        
        return {
            "status": "success",
            "total_patterns": len(patterns),
            "patterns": patterns
        }
        
    except Exception as e:
        logger.error(f"Failed to get log patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/anomalies")
async def get_log_anomalies(
    hours: int = Query(default=24, ge=1, le=168),
    severity: Optional[str] = Query(None, regex="^(info|warning|critical)$")
):
    """Get log anomalies"""
    try:
        from app.core.redis_client import redis_client
        import json
        
        # Get anomalies from Redis
        alerts = await redis_client.lrange("log_anomaly_alerts", 0, -1)
        anomalies = []
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        for alert_data in alerts:
            try:
                alert = json.loads(alert_data)
                alert_time = datetime.fromisoformat(alert["timestamp"])
                
                # Filter by time range
                if alert_time < start_time or alert_time > end_time:
                    continue
                
                # Filter by severity if specified
                if severity and alert.get("severity") != severity:
                    continue
                
                anomalies.append(alert)
                
            except (json.JSONDecodeError, ValueError):
                continue
        
        # Sort by timestamp descending
        anomalies.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {
            "status": "success",
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "hours": hours
            },
            "total_anomalies": len(anomalies),
            "anomalies": anomalies
        }
        
    except Exception as e:
        logger.error(f"Failed to get log anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/levels/distribution")
async def get_log_level_distribution(
    hours: int = Query(default=24, ge=1, le=168)
):
    """Get log level distribution over time"""
    try:
        from app.core.redis_client import redis_client
        
        distribution = {}
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # Get hourly distribution
        current_time = start_time
        while current_time <= end_time:
            hour_key = current_time.strftime('%Y%m%d_%H')
            hour_label = current_time.strftime('%Y-%m-%d %H:00')
            
            # Get log summary for this hour
            summary_key = f"log_summary:{hour_key}"
            summary_data = await redis_client.get(summary_key)
            
            hour_distribution = {"DEBUG": 0, "INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0}
            
            if summary_data:
                try:
                    import gzip
                    decompressed = gzip.decompress(summary_data)
                    summary = json.loads(decompressed.decode())
                    
                    levels = summary.get("levels", {})
                    for level, count in levels.items():
                        if level in hour_distribution:
                            hour_distribution[level] = count
                            
                except Exception as e:
                    logger.error(f"Failed to process summary for {hour_key}: {e}")
            
            distribution[hour_label] = hour_distribution
            current_time += timedelta(hours=1)
        
        return {
            "status": "success",
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "hours": hours
            },
            "distribution": distribution
        }
        
    except Exception as e:
        logger.error(f"Failed to get log level distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sources/distribution")
async def get_log_source_distribution(
    hours: int = Query(default=24, ge=1, le=168)
):
    """Get log source distribution over time"""
    try:
        from app.core.redis_client import redis_client
        import json
        import gzip
        
        distribution = {}
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # Get hourly distribution
        current_time = start_time
        while current_time <= end_time:
            hour_key = current_time.strftime('%Y%m%d_%H')
            hour_label = current_time.strftime('%Y-%m-%d %H:00')
            
            # Get log summary for this hour
            summary_key = f"log_summary:{hour_key}"
            summary_data = await redis_client.get(summary_key)
            
            hour_distribution = {
                "application": 0, "system": 0, "database": 0, 
                "cache": 0, "security": 0, "business": 0, "external": 0
            }
            
            if summary_data:
                try:
                    decompressed = gzip.decompress(summary_data)
                    summary = json.loads(decompressed.decode())
                    
                    sources = summary.get("sources", {})
                    for source, count in sources.items():
                        if source in hour_distribution:
                            hour_distribution[source] = count
                            
                except Exception as e:
                    logger.error(f"Failed to process summary for {hour_key}: {e}")
            
            distribution[hour_label] = hour_distribution
            current_time += timedelta(hours=1)
        
        return {
            "status": "success",
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "hours": hours
            },
            "distribution": distribution
        }
        
    except Exception as e:
        logger.error(f"Failed to get log source distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_log_stats():
    """Get log aggregator statistics"""
    try:
        stats = log_aggregator.get_stats()
        
        # Add additional statistics
        pattern_stats = []
        for pattern in log_aggregator.patterns.values():
            pattern_stats.append({
                "name": pattern.name,
                "count": pattern.count,
                "category": pattern.category
            })
        
        pattern_stats.sort(key=lambda x: x["count"], reverse=True)
        
        return {
            "status": "success",
            "system_stats": stats,
            "top_patterns": pattern_stats[:10],
            "error_signatures": len(log_aggregator.error_signatures)
        }
        
    except Exception as e:
        logger.error(f"Failed to get log stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export")
async def export_logs(
    start_time: datetime = Query(...),
    end_time: datetime = Query(...),
    format: str = Query("json", regex="^(json|csv)$"),
    level: Optional[str] = Query(None, regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"),
    source: Optional[str] = Query(None, regex="^(application|system|database|cache|security|business|external)$"),
    limit: int = Query(default=10000, ge=1, le=50000)
):
    """Export logs in specified format"""
    try:
        # Convert string enums to enum objects
        level_enum = LogLevel(level) if level else None
        source_enum = LogSource(source) if source else None
        
        # Search logs
        results = await log_aggregator.search_logs(
            query=None,
            start_time=start_time,
            end_time=end_time,
            level=level_enum,
            source=source_enum,
            limit=limit
        )
        
        if format == "csv":
            # Convert to CSV format
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=[
                'timestamp', 'level', 'source', 'module', 'message',
                'trace_id', 'user_id', 'request_id'
            ])
            
            writer.writeheader()
            for result in results:
                writer.writerow({
                    'timestamp': result.get('timestamp', ''),
                    'level': result.get('level', ''),
                    'source': result.get('source', ''),
                    'module': result.get('module', ''),
                    'message': result.get('message', ''),
                    'trace_id': result.get('trace_id', ''),
                    'user_id': result.get('user_id', ''),
                    'request_id': result.get('request_id', '')
                })
            
            return {
                "status": "success",
                "format": "csv",
                "data": output.getvalue(),
                "total_records": len(results)
            }
        else:
            # JSON format
            return {
                "status": "success",
                "format": "json",
                "export_info": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "filters": {
                        "level": level,
                        "source": source
                    },
                    "total_records": len(results),
                    "exported_at": datetime.utcnow().isoformat()
                },
                "data": results
            }
        
    except Exception as e:
        logger.error(f"Log export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))