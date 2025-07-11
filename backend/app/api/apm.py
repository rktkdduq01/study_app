"""
APM API Endpoints
REST API endpoints for Application Performance Monitoring data
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel

from app.core.logger import get_logger
from app.core.apm import (
    apm_collector, get_apm_dashboard_data, get_performance_alerts,
    trigger_memory_leak_detection, set_performance_threshold
)
from app.core.redis_client import redis_client
import json

logger = get_logger(__name__)

# Pydantic models for API responses
class APMSummaryResponse(BaseModel):
    overall_score: float
    performance_level: str
    system_metrics: Dict[str, Any]
    application_metrics: Dict[str, Any]
    endpoint_performance: List[Dict[str, Any]]
    recent_alerts: List[Dict[str, Any]]
    memory_leaks: int
    timestamp: str

class AlertResponse(BaseModel):
    type: str
    message: str
    severity: str
    value: float
    timestamp: str

class EndpointMetricsResponse(BaseModel):
    endpoint: str
    method: str
    request_count: int
    average_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    error_count: int
    error_rate: float
    last_accessed: str

class SystemMetricsResponse(BaseModel):
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    load_average: List[float]
    process_count: int
    thread_count: int
    timestamp: str

class ThresholdUpdateRequest(BaseModel):
    metric: str
    value: float

# Create router
router = APIRouter(prefix="/apm", tags=["APM"])

@router.get("/dashboard", response_model=Dict[str, Any])
async def get_apm_dashboard():
    """Get comprehensive APM dashboard data"""
    try:
        dashboard_data = await get_apm_dashboard_data()
        return {
            "status": "success",
            "data": dashboard_data
        }
    except Exception as e:
        logger.error(f"Failed to get APM dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary", response_model=APMSummaryResponse)
async def get_performance_summary():
    """Get performance summary with overall health score"""
    try:
        summary = apm_collector.get_performance_summary()
        
        if summary.get("status") == "no_data":
            raise HTTPException(status_code=404, detail="No performance data available")
        
        if summary.get("status") == "error":
            raise HTTPException(status_code=500, detail=summary.get("error"))
        
        return summary
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get performance summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(
    limit: int = Query(default=50, ge=1, le=1000),
    severity: Optional[str] = Query(default=None, regex="^(critical|warning|info)$")
):
    """Get performance alerts with optional filtering"""
    try:
        alerts = await get_performance_alerts(limit)
        
        # Filter by severity if specified
        if severity:
            alerts = [alert for alert in alerts if alert.get("severity") == severity]
        
        return alerts
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/endpoints", response_model=List[EndpointMetricsResponse])
async def get_endpoint_metrics(
    limit: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="request_count", regex="^(request_count|average_response_time|error_rate)$")
):
    """Get endpoint performance metrics"""
    try:
        endpoints = list(apm_collector.profiler.endpoint_metrics.values())
        
        # Sort by specified field
        if sort_by == "request_count":
            endpoints.sort(key=lambda x: x.request_count, reverse=True)
        elif sort_by == "average_response_time":
            endpoints.sort(key=lambda x: x.average_response_time, reverse=True)
        elif sort_by == "error_rate":
            endpoints.sort(key=lambda x: x.error_rate, reverse=True)
        
        # Convert to response format
        result = []
        for ep in endpoints[:limit]:
            result.append({
                "endpoint": ep.endpoint,
                "method": ep.method,
                "request_count": ep.request_count,
                "average_response_time": ep.average_response_time,
                "min_response_time": ep.min_response_time,
                "max_response_time": ep.max_response_time,
                "p95_response_time": ep.p95_response_time,
                "error_count": ep.error_count,
                "error_rate": ep.error_rate,
                "last_accessed": ep.last_accessed.isoformat()
            })
        
        return result
    except Exception as e:
        logger.error(f"Failed to get endpoint metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system-metrics", response_model=List[SystemMetricsResponse])
async def get_system_metrics(
    hours: int = Query(default=1, ge=1, le=24),
    interval_minutes: int = Query(default=5, ge=1, le=60)
):
    """Get historical system metrics"""
    try:
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # Get metrics from Redis
        metrics = []
        current_time = start_time
        
        while current_time <= end_time:
            key = f"apm_metrics:system:{current_time.strftime('%Y%m%d_%H%M')}"
            data = await redis_client.get(key)
            
            if data:
                try:
                    metric = json.loads(data)
                    metrics.append(metric)
                except json.JSONDecodeError:
                    pass
            
            current_time += timedelta(minutes=interval_minutes)
        
        return metrics
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/application-metrics")
async def get_application_metrics(
    hours: int = Query(default=1, ge=1, le=24),
    interval_minutes: int = Query(default=5, ge=1, le=60)
):
    """Get historical application metrics"""
    try:
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # Get metrics from Redis
        metrics = []
        current_time = start_time
        
        while current_time <= end_time:
            key = f"apm_metrics:application:{current_time.strftime('%Y%m%d_%H%M')}"
            data = await redis_client.get(key)
            
            if data:
                try:
                    metric = json.loads(data)
                    metrics.append(metric)
                except json.JSONDecodeError:
                    pass
            
            current_time += timedelta(minutes=interval_minutes)
        
        return {
            "status": "success",
            "data": metrics,
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Failed to get application metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/function-metrics")
async def get_function_metrics(
    function_name: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000)
):
    """Get function performance metrics"""
    try:
        if function_name:
            # Get metrics for specific function
            if function_name in apm_collector.profiler.function_metrics:
                metrics = list(apm_collector.profiler.function_metrics[function_name])
                return {
                    "status": "success",
                    "function": function_name,
                    "metrics": metrics[-limit:]
                }
            else:
                raise HTTPException(status_code=404, detail=f"Function '{function_name}' not found")
        else:
            # Get all function metrics
            all_metrics = {}
            for func_name, metrics in apm_collector.profiler.function_metrics.items():
                all_metrics[func_name] = {
                    "total_calls": len(metrics),
                    "average_execution_time": sum(m.get("execution_time", 0) for m in metrics) / len(metrics),
                    "total_memory_delta": sum(m.get("memory_delta", 0) for m in metrics),
                    "recent_metrics": list(metrics)[-10:]  # Last 10 calls
                }
            
            return {
                "status": "success",
                "functions": all_metrics
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get function metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memory-leaks")
async def get_memory_leak_info():
    """Get memory leak detection information"""
    try:
        memory_leaks = apm_collector.profiler.memory_leaks
        
        return {
            "status": "success",
            "total_leaks_detected": len(memory_leaks),
            "leaks": memory_leaks
        }
    except Exception as e:
        logger.error(f"Failed to get memory leak info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/memory-leak-detection")
async def trigger_memory_leak_check():
    """Manually trigger memory leak detection"""
    try:
        await trigger_memory_leak_detection()
        return {
            "status": "success",
            "message": "Memory leak detection triggered"
        }
    except Exception as e:
        logger.error(f"Failed to trigger memory leak detection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/thresholds")
async def get_performance_thresholds():
    """Get current performance thresholds"""
    try:
        return {
            "status": "success",
            "thresholds": apm_collector.thresholds
        }
    except Exception as e:
        logger.error(f"Failed to get thresholds: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/thresholds")
async def update_performance_threshold(request: ThresholdUpdateRequest):
    """Update performance threshold"""
    try:
        set_performance_threshold(request.metric, request.value)
        
        return {
            "status": "success",
            "message": f"Updated {request.metric} threshold to {request.value}"
        }
    except Exception as e:
        logger.error(f"Failed to update threshold: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health-check")
async def apm_health_check():
    """Health check for APM system"""
    try:
        # Check if APM collector is running
        is_running = (
            apm_collector._collection_task is not None and
            not apm_collector._collection_task.done()
        )
        
        # Get basic stats
        stats = {
            "apm_collector_running": is_running,
            "system_metrics_count": len(apm_collector.system_metrics),
            "app_metrics_count": len(apm_collector.app_metrics),
            "function_metrics_count": len(apm_collector.profiler.function_metrics),
            "endpoint_metrics_count": len(apm_collector.profiler.endpoint_metrics),
            "alerts_count": len(apm_collector.alerts),
            "memory_leaks_count": len(apm_collector.profiler.memory_leaks)
        }
        
        return {
            "status": "healthy" if is_running else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "stats": stats
        }
    except Exception as e:
        logger.error(f"APM health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/report")
async def generate_performance_report(
    hours: int = Query(default=24, ge=1, le=168)  # Max 1 week
):
    """Generate comprehensive performance report"""
    try:
        # Get current performance summary
        current_summary = apm_collector.get_performance_summary()
        
        # Get historical data
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # Calculate key metrics over time period
        report = {
            "report_period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "duration_hours": hours
            },
            "current_status": current_summary,
            "summary": {
                "total_requests": sum(ep.request_count for ep in apm_collector.profiler.endpoint_metrics.values()),
                "total_errors": sum(ep.error_count for ep in apm_collector.profiler.endpoint_metrics.values()),
                "total_alerts": len(apm_collector.alerts),
                "memory_leaks_detected": len(apm_collector.profiler.memory_leaks)
            },
            "top_endpoints": [
                {
                    "endpoint": ep.endpoint,
                    "method": ep.method,
                    "request_count": ep.request_count,
                    "avg_response_time": ep.average_response_time,
                    "error_rate": ep.error_rate
                }
                for ep in sorted(
                    apm_collector.profiler.endpoint_metrics.values(),
                    key=lambda x: x.request_count,
                    reverse=True
                )[:10]
            ],
            "performance_issues": [],
            "recommendations": []
        }
        
        # Analyze performance issues
        for ep in apm_collector.profiler.endpoint_metrics.values():
            if ep.average_response_time > 2.0:
                report["performance_issues"].append({
                    "type": "slow_endpoint",
                    "endpoint": f"{ep.method} {ep.endpoint}",
                    "avg_response_time": ep.average_response_time,
                    "severity": "high" if ep.average_response_time > 5.0 else "medium"
                })
            
            if ep.error_rate > 5.0:
                report["performance_issues"].append({
                    "type": "high_error_rate",
                    "endpoint": f"{ep.method} {ep.endpoint}",
                    "error_rate": ep.error_rate,
                    "severity": "high" if ep.error_rate > 15.0 else "medium"
                })
        
        # Generate recommendations
        if current_summary.get("system_metrics", {}).get("cpu_percent", 0) > 80:
            report["recommendations"].append({
                "type": "resource_optimization",
                "message": "High CPU usage detected. Consider scaling horizontally or optimizing code.",
                "priority": "high"
            })
        
        if current_summary.get("system_metrics", {}).get("memory_percent", 0) > 80:
            report["recommendations"].append({
                "type": "memory_optimization",
                "message": "High memory usage detected. Check for memory leaks and optimize memory usage.",
                "priority": "high"
            })
        
        slow_endpoints = [ep for ep in apm_collector.profiler.endpoint_metrics.values() if ep.average_response_time > 1.0]
        if slow_endpoints:
            report["recommendations"].append({
                "type": "performance_optimization",
                "message": f"Found {len(slow_endpoints)} slow endpoints. Consider optimization or caching.",
                "priority": "medium"
            })
        
        return {
            "status": "success",
            "report": report
        }
        
    except Exception as e:
        logger.error(f"Failed to generate performance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))