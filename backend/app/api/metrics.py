"""
Metrics and Alerting API Endpoints
REST API for metrics collection and alert management
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query, HTTPException, Depends, Body
from pydantic import BaseModel, Field

from app.core.logger import get_logger
from app.core.metrics_collector import (
    metrics_collector, MetricType, AlertSeverity, AlertState, 
    AlertRule, Alert, record_metric
)
from app.core.redis_client import redis_client
import json

logger = get_logger(__name__)

# Pydantic models
class MetricRequest(BaseModel):
    name: str
    value: float
    labels: Optional[Dict[str, str]] = None
    timestamp: Optional[datetime] = None

class MetricRegistration(BaseModel):
    name: str
    type: str = Field(..., regex="^(counter|gauge|histogram|timer|rate)$")
    description: str
    unit: str
    labels: Optional[Dict[str, str]] = None

class AlertRuleRequest(BaseModel):
    name: str
    metric_name: str
    condition: str = Field(..., regex="^(>|>=|<|<=|==|!=)$")
    threshold: float
    severity: str = Field(..., regex="^(info|warning|critical)$")
    duration_seconds: int = Field(default=60, ge=1, le=3600)
    cooldown_seconds: int = Field(default=300, ge=60, le=7200)
    description: Optional[str] = ""
    enabled: bool = True
    labels: Optional[Dict[str, str]] = None
    notification_channels: Optional[List[str]] = None

class AlertRuleUpdate(BaseModel):
    name: Optional[str] = None
    condition: Optional[str] = None
    threshold: Optional[float] = None
    severity: Optional[str] = None
    duration_seconds: Optional[int] = None
    cooldown_seconds: Optional[int] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    labels: Optional[Dict[str, str]] = None
    notification_channels: Optional[List[str]] = None

class AlertResponse(BaseModel):
    id: str
    rule_id: str
    metric_name: str
    message: str
    severity: str
    state: str
    value: float
    threshold: float
    fired_at: str
    resolved_at: Optional[str] = None
    acknowledged_at: Optional[str] = None
    labels: Dict[str, str]
    annotations: Dict[str, str]

# Create router
router = APIRouter(prefix="/metrics", tags=["Metrics"])

@router.post("/record")
async def record_metric_endpoint(metric: MetricRequest):
    """Record a single metric value"""
    try:
        success = await record_metric(
            metric.name, 
            metric.value, 
            metric.labels
        )
        
        if success:
            return {"status": "success", "message": "Metric recorded"}
        else:
            raise HTTPException(status_code=400, detail="Failed to record metric")
            
    except Exception as e:
        logger.error(f"Failed to record metric: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/record/batch")
async def record_metrics_batch(metrics: List[MetricRequest]):
    """Record multiple metric values"""
    try:
        results = []
        for metric in metrics:
            success = await record_metric(
                metric.name,
                metric.value,
                metric.labels
            )
            results.append({
                "metric": metric.name,
                "success": success
            })
        
        successful = sum(1 for r in results if r["success"])
        
        return {
            "status": "success",
            "total": len(metrics),
            "successful": successful,
            "failed": len(metrics) - successful,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Failed to record metrics batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/register")
async def register_metric_endpoint(metric_def: MetricRegistration):
    """Register a new metric"""
    try:
        metric_type = MetricType(metric_def.type)
        
        success = metrics_collector.register_metric(
            metric_def.name,
            metric_type,
            metric_def.description,
            metric_def.unit,
            metric_def.labels
        )
        
        if success:
            return {"status": "success", "message": f"Metric {metric_def.name} registered"}
        else:
            raise HTTPException(status_code=400, detail="Failed to register metric")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid metric type: {metric_def.type}")
    except Exception as e:
        logger.error(f"Failed to register metric: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_metrics():
    """List all registered metrics"""
    try:
        summary = metrics_collector.get_metrics_summary()
        return {
            "status": "success",
            "data": summary
        }
    except Exception as e:
        logger.error(f"Failed to list metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{metric_name}")
async def get_metric_details(
    metric_name: str,
    hours: int = Query(default=1, ge=1, le=168)  # Max 1 week
):
    """Get detailed metric information"""
    try:
        # Get metric summary
        summary = metrics_collector.get_metric_summary(metric_name)
        if not summary:
            raise HTTPException(status_code=404, detail=f"Metric {metric_name} not found")
        
        # Get historical data from Redis
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        historical_data = []
        current_time = start_time
        
        while current_time <= end_time:
            key = f"metric:{metric_name}:{current_time.strftime('%Y%m%d_%H')}"
            data = await redis_client.lrange(key, 0, -1)
            
            for item in data:
                try:
                    point = json.loads(item)
                    point_time = datetime.fromisoformat(point["timestamp"])
                    if start_time <= point_time <= end_time:
                        historical_data.append(point)
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue
            
            current_time += timedelta(hours=1)
        
        # Sort by timestamp
        historical_data.sort(key=lambda x: x["timestamp"])
        
        return {
            "status": "success",
            "metric": summary,
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "hours": hours
            },
            "data_points": len(historical_data),
            "historical_data": historical_data[-1000:]  # Limit to last 1000 points
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metric details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{metric_name}/aggregated")
async def get_metric_aggregated(
    metric_name: str,
    hours: int = Query(default=24, ge=1, le=168),
    aggregation: str = Query(default="avg", regex="^(avg|sum|min|max|count)$")
):
    """Get aggregated metric data"""
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        aggregated_data = []
        current_time = start_time
        
        while current_time <= end_time:
            key = f"metric_hourly:{metric_name}:{current_time.strftime('%Y%m%d_%H')}"
            data = await redis_client.get(key)
            
            if data:
                try:
                    hourly_data = json.loads(data)
                    
                    if aggregation in hourly_data:
                        aggregated_data.append({
                            "timestamp": current_time.isoformat(),
                            "value": hourly_data[aggregation]
                        })
                except json.JSONDecodeError:
                    pass
            
            current_time += timedelta(hours=1)
        
        return {
            "status": "success",
            "metric_name": metric_name,
            "aggregation": aggregation,
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "hours": hours
            },
            "data": aggregated_data
        }
        
    except Exception as e:
        logger.error(f"Failed to get aggregated metric data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Alert management endpoints
@router.post("/alerts/rules")
async def create_alert_rule(rule_request: AlertRuleRequest):
    """Create a new alert rule"""
    try:
        rule_id = f"rule_{int(datetime.utcnow().timestamp())}"
        
        rule = AlertRule(
            id=rule_id,
            name=rule_request.name,
            metric_name=rule_request.metric_name,
            condition=rule_request.condition,
            threshold=rule_request.threshold,
            severity=AlertSeverity(rule_request.severity),
            duration_seconds=rule_request.duration_seconds,
            cooldown_seconds=rule_request.cooldown_seconds,
            description=rule_request.description or "",
            enabled=rule_request.enabled,
            labels=rule_request.labels or {},
            notification_channels=rule_request.notification_channels or []
        )
        
        success = metrics_collector.add_alert_rule(rule)
        
        if success:
            return {
                "status": "success", 
                "message": "Alert rule created",
                "rule_id": rule_id
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to create alert rule")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create alert rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts/rules")
async def list_alert_rules():
    """List all alert rules"""
    try:
        rules = []
        for rule_id, rule in metrics_collector.alert_rules.items():
            rules.append({
                "id": rule.id,
                "name": rule.name,
                "metric_name": rule.metric_name,
                "condition": rule.condition,
                "threshold": rule.threshold,
                "severity": rule.severity.value,
                "duration_seconds": rule.duration_seconds,
                "cooldown_seconds": rule.cooldown_seconds,
                "description": rule.description,
                "enabled": rule.enabled,
                "labels": rule.labels,
                "notification_channels": rule.notification_channels
            })
        
        return {
            "status": "success",
            "total_rules": len(rules),
            "rules": rules
        }
        
    except Exception as e:
        logger.error(f"Failed to list alert rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts/rules/{rule_id}")
async def get_alert_rule(rule_id: str):
    """Get specific alert rule"""
    try:
        if rule_id not in metrics_collector.alert_rules:
            raise HTTPException(status_code=404, detail=f"Alert rule {rule_id} not found")
        
        rule = metrics_collector.alert_rules[rule_id]
        
        return {
            "status": "success",
            "rule": {
                "id": rule.id,
                "name": rule.name,
                "metric_name": rule.metric_name,
                "condition": rule.condition,
                "threshold": rule.threshold,
                "severity": rule.severity.value,
                "duration_seconds": rule.duration_seconds,
                "cooldown_seconds": rule.cooldown_seconds,
                "description": rule.description,
                "enabled": rule.enabled,
                "labels": rule.labels,
                "notification_channels": rule.notification_channels
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get alert rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/alerts/rules/{rule_id}")
async def update_alert_rule(rule_id: str, update_request: AlertRuleUpdate):
    """Update an alert rule"""
    try:
        if rule_id not in metrics_collector.alert_rules:
            raise HTTPException(status_code=404, detail=f"Alert rule {rule_id} not found")
        
        rule = metrics_collector.alert_rules[rule_id]
        
        # Update fields if provided
        if update_request.name is not None:
            rule.name = update_request.name
        if update_request.condition is not None:
            rule.condition = update_request.condition
        if update_request.threshold is not None:
            rule.threshold = update_request.threshold
        if update_request.severity is not None:
            rule.severity = AlertSeverity(update_request.severity)
        if update_request.duration_seconds is not None:
            rule.duration_seconds = update_request.duration_seconds
        if update_request.cooldown_seconds is not None:
            rule.cooldown_seconds = update_request.cooldown_seconds
        if update_request.description is not None:
            rule.description = update_request.description
        if update_request.enabled is not None:
            rule.enabled = update_request.enabled
        if update_request.labels is not None:
            rule.labels = update_request.labels
        if update_request.notification_channels is not None:
            rule.notification_channels = update_request.notification_channels
        
        return {
            "status": "success",
            "message": f"Alert rule {rule_id} updated"
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update alert rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/alerts/rules/{rule_id}")
async def delete_alert_rule(rule_id: str):
    """Delete an alert rule"""
    try:
        success = metrics_collector.remove_alert_rule(rule_id)
        
        if success:
            return {
                "status": "success",
                "message": f"Alert rule {rule_id} deleted"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Alert rule {rule_id} not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete alert rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts/active", response_model=List[AlertResponse])
async def get_active_alerts(
    severity: Optional[str] = Query(None, regex="^(info|warning|critical)$")
):
    """Get active alerts"""
    try:
        alerts = []
        
        for alert in metrics_collector.active_alerts.values():
            # Filter by severity if specified
            if severity and alert.severity.value != severity:
                continue
            
            alerts.append(AlertResponse(
                id=alert.id,
                rule_id=alert.rule_id,
                metric_name=alert.metric_name,
                message=alert.message,
                severity=alert.severity.value,
                state=alert.state.value,
                value=alert.value,
                threshold=alert.threshold,
                fired_at=alert.fired_at.isoformat(),
                resolved_at=alert.resolved_at.isoformat() if alert.resolved_at else None,
                acknowledged_at=alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                labels=alert.labels,
                annotations=alert.annotations
            ))
        
        return alerts
        
    except Exception as e:
        logger.error(f"Failed to get active alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts/history")
async def get_alert_history(
    hours: int = Query(default=24, ge=1, le=168),
    severity: Optional[str] = Query(None, regex="^(info|warning|critical)$"),
    limit: int = Query(default=100, ge=1, le=1000)
):
    """Get alert history"""
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        alerts = []
        
        for alert in metrics_collector.alert_history:
            # Filter by time range
            if alert.fired_at < start_time or alert.fired_at > end_time:
                continue
            
            # Filter by severity if specified
            if severity and alert.severity.value != severity:
                continue
            
            alerts.append({
                "id": alert.id,
                "rule_id": alert.rule_id,
                "metric_name": alert.metric_name,
                "message": alert.message,
                "severity": alert.severity.value,
                "state": alert.state.value,
                "value": alert.value,
                "threshold": alert.threshold,
                "fired_at": alert.fired_at.isoformat(),
                "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
                "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                "labels": alert.labels,
                "annotations": alert.annotations
            })
        
        # Sort by fired_at descending and limit
        alerts.sort(key=lambda x: x["fired_at"], reverse=True)
        
        return {
            "status": "success",
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "hours": hours
            },
            "total_alerts": len(alerts),
            "alerts": alerts[:limit]
        }
        
    except Exception as e:
        logger.error(f"Failed to get alert history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Acknowledge an active alert"""
    try:
        if alert_id not in metrics_collector.active_alerts:
            raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
        
        alert = metrics_collector.active_alerts[alert_id]
        alert.state = AlertState.ACKNOWLEDGED
        alert.acknowledged_at = datetime.utcnow()
        
        return {
            "status": "success",
            "message": f"Alert {alert_id} acknowledged"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to acknowledge alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard")
async def get_metrics_dashboard():
    """Get metrics dashboard data"""
    try:
        # Get summary statistics
        summary = metrics_collector.get_metrics_summary()
        
        # Get active alerts by severity
        alerts_by_severity = {"info": 0, "warning": 0, "critical": 0}
        for alert in metrics_collector.active_alerts.values():
            alerts_by_severity[alert.severity.value] += 1
        
        # Get top metrics by activity
        top_metrics = []
        for name, metric in metrics_collector.metrics.items():
            if metric.data_points:
                top_metrics.append({
                    "name": name,
                    "type": metric.type.value,
                    "data_points": len(metric.data_points),
                    "last_value": metric.data_points[-1].value if metric.data_points else None,
                    "last_updated": metric.last_updated.isoformat() if metric.last_updated else None
                })
        
        # Sort by data points (activity)
        top_metrics.sort(key=lambda x: x["data_points"], reverse=True)
        
        return {
            "status": "success",
            "summary": summary,
            "alerts_by_severity": alerts_by_severity,
            "top_metrics": top_metrics[:20],  # Top 20 most active metrics
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get metrics dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))