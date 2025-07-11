"""
Metrics Collection and Alerting System
Comprehensive metrics collection with intelligent alerting
"""

import asyncio
import time
import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict, field
from collections import defaultdict, deque
from enum import Enum
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

from app.core.logger import get_logger
from app.core.redis_client import redis_client
from app.core.config import settings
from app.core.distributed_tracing import distributed_tracer, trace_operation

logger = get_logger(__name__)

class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"          # Monotonically increasing value
    GAUGE = "gauge"             # Current value that can go up/down
    HISTOGRAM = "histogram"     # Distribution of values
    TIMER = "timer"            # Duration measurements
    RATE = "rate"              # Events per time unit

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class AlertState(Enum):
    """Alert states"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"
    SUPPRESSED = "suppressed"

@dataclass
class MetricPoint:
    """Individual metric data point"""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Metric:
    """Metric definition and data"""
    name: str
    type: MetricType
    description: str
    unit: str
    labels: Dict[str, str] = field(default_factory=dict)
    data_points: deque = field(default_factory=lambda: deque(maxlen=10000))
    aggregations: Dict[str, float] = field(default_factory=dict)
    last_updated: Optional[datetime] = None

@dataclass
class AlertRule:
    """Alert rule definition"""
    id: str
    name: str
    metric_name: str
    condition: str  # e.g., "> 0.8", "< 100", "== 0"
    threshold: float
    severity: AlertSeverity
    duration_seconds: int = 60  # How long condition must be true
    cooldown_seconds: int = 300  # Minimum time between alerts
    description: str = ""
    enabled: bool = True
    labels: Dict[str, str] = field(default_factory=dict)
    notification_channels: List[str] = field(default_factory=list)

@dataclass
class Alert:
    """Active alert"""
    id: str
    rule_id: str
    metric_name: str
    message: str
    severity: AlertSeverity
    state: AlertState
    value: float
    threshold: float
    fired_at: datetime
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)

class MetricsCollector:
    """Advanced metrics collection system"""
    
    def __init__(self):
        self.metrics: Dict[str, Metric] = {}
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=10000)
        
        # Collection settings
        self.collection_interval = 10  # seconds
        self.retention_days = 30
        
        # Background tasks
        self._collection_task = None
        self._alert_evaluation_task = None
        self._cleanup_task = None
        
        # Notification system
        self.notification_handlers: Dict[str, Callable] = {}
        
        # Built-in metrics
        self._register_builtin_metrics()
        self._register_builtin_alert_rules()
        
        # Start background tasks
        self._start_background_tasks()
    
    def _start_background_tasks(self):
        """Start background collection and evaluation tasks"""
        if self._collection_task is None:
            self._collection_task = asyncio.create_task(self._collection_loop())
        
        if self._alert_evaluation_task is None:
            self._alert_evaluation_task = asyncio.create_task(self._alert_evaluation_loop())
        
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    def _register_builtin_metrics(self):
        """Register built-in system metrics"""
        self.register_metric("http_requests_total", MetricType.COUNTER, 
                           "Total HTTP requests", "requests")
        self.register_metric("http_request_duration", MetricType.HISTOGRAM,
                           "HTTP request duration", "seconds")
        self.register_metric("system_cpu_usage", MetricType.GAUGE,
                           "System CPU usage", "percent")
        self.register_metric("system_memory_usage", MetricType.GAUGE,
                           "System memory usage", "percent")
        self.register_metric("database_connections", MetricType.GAUGE,
                           "Active database connections", "connections")
        self.register_metric("cache_hit_rate", MetricType.GAUGE,
                           "Cache hit rate", "percent")
        self.register_metric("error_rate", MetricType.GAUGE,
                           "Application error rate", "percent")
        self.register_metric("response_time_p95", MetricType.GAUGE,
                           "95th percentile response time", "seconds")
    
    def _register_builtin_alert_rules(self):
        """Register built-in alert rules"""
        # High CPU usage
        self.add_alert_rule(AlertRule(
            id="high_cpu_usage",
            name="High CPU Usage",
            metric_name="system_cpu_usage",
            condition=">",
            threshold=80.0,
            severity=AlertSeverity.WARNING,
            duration_seconds=120,
            description="System CPU usage is above 80%",
            notification_channels=["email", "webhook"]
        ))
        
        # Critical CPU usage
        self.add_alert_rule(AlertRule(
            id="critical_cpu_usage",
            name="Critical CPU Usage",
            metric_name="system_cpu_usage",
            condition=">",
            threshold=95.0,
            severity=AlertSeverity.CRITICAL,
            duration_seconds=60,
            description="System CPU usage is above 95%",
            notification_channels=["email", "slack", "webhook"]
        ))
        
        # High memory usage
        self.add_alert_rule(AlertRule(
            id="high_memory_usage",
            name="High Memory Usage",
            metric_name="system_memory_usage",
            condition=">",
            threshold=85.0,
            severity=AlertSeverity.WARNING,
            duration_seconds=300,
            description="System memory usage is above 85%",
            notification_channels=["email"]
        ))
        
        # High error rate
        self.add_alert_rule(AlertRule(
            id="high_error_rate",
            name="High Error Rate",
            metric_name="error_rate",
            condition=">",
            threshold=5.0,
            severity=AlertSeverity.CRITICAL,
            duration_seconds=60,
            description="Application error rate is above 5%",
            notification_channels=["email", "slack"]
        ))
        
        # Slow response time
        self.add_alert_rule(AlertRule(
            id="slow_response_time",
            name="Slow Response Time",
            metric_name="response_time_p95",
            condition=">",
            threshold=2.0,
            severity=AlertSeverity.WARNING,
            duration_seconds=180,
            description="95th percentile response time is above 2 seconds",
            notification_channels=["email"]
        ))
    
    def register_metric(self, name: str, metric_type: MetricType, 
                       description: str, unit: str, 
                       labels: Dict[str, str] = None) -> bool:
        """Register a new metric"""
        try:
            if name in self.metrics:
                logger.warning(f"Metric {name} already exists")
                return False
            
            metric = Metric(
                name=name,
                type=metric_type,
                description=description,
                unit=unit,
                labels=labels or {}
            )
            
            self.metrics[name] = metric
            logger.info(f"Registered metric: {name} ({metric_type.value})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register metric {name}: {e}")
            return False
    
    async def record_metric(self, name: str, value: float, 
                          labels: Dict[str, str] = None,
                          timestamp: datetime = None) -> bool:
        """Record a metric value"""
        try:
            if name not in self.metrics:
                logger.warning(f"Metric {name} not registered")
                return False
            
            metric = self.metrics[name]
            
            # Create data point
            data_point = MetricPoint(
                timestamp=timestamp or datetime.utcnow(),
                value=value,
                labels=labels or {}
            )
            
            metric.data_points.append(data_point)
            metric.last_updated = data_point.timestamp
            
            # Update aggregations
            await self._update_aggregations(metric)
            
            # Store in Redis for persistence
            await self._store_metric_point(name, data_point)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to record metric {name}: {e}")
            return False
    
    async def _update_aggregations(self, metric: Metric):
        """Update metric aggregations"""
        try:
            if not metric.data_points:
                return
            
            values = [dp.value for dp in metric.data_points]
            
            # Basic aggregations
            metric.aggregations.update({
                "count": len(values),
                "sum": sum(values),
                "avg": statistics.mean(values),
                "min": min(values),
                "max": max(values)
            })
            
            # Advanced aggregations for sufficient data
            if len(values) >= 2:
                metric.aggregations.update({
                    "stddev": statistics.stdev(values),
                    "median": statistics.median(values)
                })
            
            # Percentiles for sufficient data
            if len(values) >= 10:
                sorted_values = sorted(values)
                metric.aggregations.update({
                    "p50": sorted_values[int(len(values) * 0.5)],
                    "p90": sorted_values[int(len(values) * 0.9)],
                    "p95": sorted_values[int(len(values) * 0.95)],
                    "p99": sorted_values[int(len(values) * 0.99)]
                })
            
            # Rate calculation for counters
            if metric.type == MetricType.COUNTER and len(values) >= 2:
                recent_points = list(metric.data_points)[-10:]  # Last 10 points
                if len(recent_points) >= 2:
                    time_diff = (recent_points[-1].timestamp - recent_points[0].timestamp).total_seconds()
                    value_diff = recent_points[-1].value - recent_points[0].value
                    if time_diff > 0:
                        metric.aggregations["rate_per_second"] = value_diff / time_diff
            
        except Exception as e:
            logger.error(f"Failed to update aggregations for {metric.name}: {e}")
    
    async def _store_metric_point(self, metric_name: str, data_point: MetricPoint):
        """Store metric data point in Redis"""
        try:
            # Store individual data point
            key = f"metric:{metric_name}:{data_point.timestamp.strftime('%Y%m%d_%H')}"
            
            point_data = {
                "timestamp": data_point.timestamp.isoformat(),
                "value": data_point.value,
                "labels": data_point.labels,
                "metadata": data_point.metadata
            }
            
            await redis_client.lpush(key, json.dumps(point_data))
            await redis_client.expire(key, 86400 * self.retention_days)
            
            # Store aggregated hourly data
            await self._store_hourly_aggregation(metric_name, data_point)
            
        except Exception as e:
            logger.error(f"Failed to store metric point: {e}")
    
    async def _store_hourly_aggregation(self, metric_name: str, data_point: MetricPoint):
        """Store hourly aggregated metric data"""
        try:
            hour_key = f"metric_hourly:{metric_name}:{data_point.timestamp.strftime('%Y%m%d_%H')}"
            
            # Get existing aggregation
            existing_data = await redis_client.get(hour_key)
            if existing_data:
                hourly_data = json.loads(existing_data)
            else:
                hourly_data = {
                    "count": 0,
                    "sum": 0,
                    "min": float('inf'),
                    "max": float('-inf'),
                    "values": []
                }
            
            # Update aggregation
            hourly_data["count"] += 1
            hourly_data["sum"] += data_point.value
            hourly_data["min"] = min(hourly_data["min"], data_point.value)
            hourly_data["max"] = max(hourly_data["max"], data_point.value)
            hourly_data["values"].append(data_point.value)
            
            # Keep only recent values for percentile calculation
            if len(hourly_data["values"]) > 1000:
                hourly_data["values"] = hourly_data["values"][-1000:]
            
            # Calculate derived metrics
            hourly_data["avg"] = hourly_data["sum"] / hourly_data["count"]
            
            await redis_client.setex(hour_key, 86400 * self.retention_days, json.dumps(hourly_data))
            
        except Exception as e:
            logger.error(f"Failed to store hourly aggregation: {e}")
    
    def add_alert_rule(self, rule: AlertRule) -> bool:
        """Add alert rule"""
        try:
            self.alert_rules[rule.id] = rule
            logger.info(f"Added alert rule: {rule.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to add alert rule: {e}")
            return False
    
    def remove_alert_rule(self, rule_id: str) -> bool:
        """Remove alert rule"""
        try:
            if rule_id in self.alert_rules:
                del self.alert_rules[rule_id]
                logger.info(f"Removed alert rule: {rule_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove alert rule: {e}")
            return False
    
    async def _collection_loop(self):
        """Background metrics collection loop"""
        while True:
            try:
                await asyncio.sleep(self.collection_interval)
                await self._collect_system_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
    
    async def _collect_system_metrics(self):
        """Collect system metrics"""
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            await self.record_metric("system_cpu_usage", cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            await self.record_metric("system_memory_usage", memory.percent)
            
            # Get application-specific metrics from APM
            try:
                from app.core.apm import apm_collector
                
                if apm_collector.app_metrics:
                    latest_app_metrics = apm_collector.app_metrics[-1]
                    
                    await self.record_metric("error_rate", latest_app_metrics.error_rate)
                    await self.record_metric("response_time_p95", latest_app_metrics.average_response_time)
                    await self.record_metric("cache_hit_rate", latest_app_metrics.cache_hit_rate)
                    
            except ImportError:
                pass
            
        except Exception as e:
            logger.error(f"System metrics collection failed: {e}")
    
    async def _alert_evaluation_loop(self):
        """Background alert evaluation loop"""
        while True:
            try:
                await asyncio.sleep(30)  # Evaluate every 30 seconds
                await self._evaluate_alert_rules()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Alert evaluation error: {e}")
    
    async def _evaluate_alert_rules(self):
        """Evaluate all alert rules"""
        for rule_id, rule in self.alert_rules.items():
            if not rule.enabled:
                continue
            
            try:
                await self._evaluate_single_rule(rule)
            except Exception as e:
                logger.error(f"Failed to evaluate rule {rule_id}: {e}")
    
    async def _evaluate_single_rule(self, rule: AlertRule):
        """Evaluate a single alert rule"""
        try:
            # Get metric
            if rule.metric_name not in self.metrics:
                return
            
            metric = self.metrics[rule.metric_name]
            
            # Check if we have recent data
            if not metric.data_points:
                return
            
            latest_point = metric.data_points[-1]
            
            # Check if data is recent enough
            if (datetime.utcnow() - latest_point.timestamp).total_seconds() > 300:  # 5 minutes
                return
            
            # Evaluate condition
            current_value = latest_point.value
            condition_met = self._evaluate_condition(current_value, rule.condition, rule.threshold)
            
            alert_id = f"{rule.id}_{rule.metric_name}"
            
            if condition_met:
                # Check if alert already exists
                if alert_id not in self.active_alerts:
                    # Create new alert
                    alert = Alert(
                        id=alert_id,
                        rule_id=rule.id,
                        metric_name=rule.metric_name,
                        message=f"{rule.name}: {rule.metric_name} is {current_value} {rule.condition} {rule.threshold}",
                        severity=rule.severity,
                        state=AlertState.ACTIVE,
                        value=current_value,
                        threshold=rule.threshold,
                        fired_at=datetime.utcnow(),
                        labels=rule.labels,
                        annotations={"description": rule.description}
                    )
                    
                    self.active_alerts[alert_id] = alert
                    self.alert_history.append(alert)
                    
                    # Send notifications
                    await self._send_alert_notifications(alert, rule)
                    
                    logger.warning(f"Alert fired: {alert.message}")
            else:
                # Check if alert should be resolved
                if alert_id in self.active_alerts:
                    alert = self.active_alerts[alert_id]
                    alert.state = AlertState.RESOLVED
                    alert.resolved_at = datetime.utcnow()
                    
                    # Send resolution notification
                    await self._send_resolution_notifications(alert, rule)
                    
                    # Move to history
                    del self.active_alerts[alert_id]
                    
                    logger.info(f"Alert resolved: {alert.message}")
            
        except Exception as e:
            logger.error(f"Failed to evaluate rule {rule.id}: {e}")
    
    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """Evaluate alert condition"""
        if condition == ">":
            return value > threshold
        elif condition == ">=":
            return value >= threshold
        elif condition == "<":
            return value < threshold
        elif condition == "<=":
            return value <= threshold
        elif condition == "==":
            return abs(value - threshold) < 0.001  # Float comparison
        elif condition == "!=":
            return abs(value - threshold) >= 0.001
        else:
            logger.error(f"Unknown condition: {condition}")
            return False
    
    async def _send_alert_notifications(self, alert: Alert, rule: AlertRule):
        """Send alert notifications"""
        for channel in rule.notification_channels:
            try:
                if channel in self.notification_handlers:
                    await self.notification_handlers[channel](alert, "fired")
                else:
                    logger.warning(f"No handler for notification channel: {channel}")
            except Exception as e:
                logger.error(f"Failed to send notification via {channel}: {e}")
    
    async def _send_resolution_notifications(self, alert: Alert, rule: AlertRule):
        """Send alert resolution notifications"""
        for channel in rule.notification_channels:
            try:
                if channel in self.notification_handlers:
                    await self.notification_handlers[channel](alert, "resolved")
            except Exception as e:
                logger.error(f"Failed to send resolution notification via {channel}: {e}")
    
    def register_notification_handler(self, channel: str, handler: Callable):
        """Register notification handler"""
        self.notification_handlers[channel] = handler
        logger.info(f"Registered notification handler for channel: {channel}")
    
    async def _cleanup_loop(self):
        """Background cleanup loop"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                await self._cleanup_old_data()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    async def _cleanup_old_data(self):
        """Clean up old metric data"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
            
            # Clean up in-memory data
            for metric in self.metrics.values():
                # Remove old data points
                while (metric.data_points and 
                       metric.data_points[0].timestamp < cutoff_date):
                    metric.data_points.popleft()
            
            # Clean up old alerts from history
            while (self.alert_history and 
                   self.alert_history[0].fired_at < cutoff_date):
                self.alert_history.popleft()
            
            logger.info("Completed metrics cleanup")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    
    def get_metric_summary(self, metric_name: str) -> Optional[Dict[str, Any]]:
        """Get metric summary"""
        try:
            if metric_name not in self.metrics:
                return None
            
            metric = self.metrics[metric_name]
            
            return {
                "name": metric.name,
                "type": metric.type.value,
                "description": metric.description,
                "unit": metric.unit,
                "labels": metric.labels,
                "data_points_count": len(metric.data_points),
                "last_updated": metric.last_updated.isoformat() if metric.last_updated else None,
                "aggregations": metric.aggregations
            }
            
        except Exception as e:
            logger.error(f"Failed to get metric summary: {e}")
            return None
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        try:
            return {
                "total_metrics": len(self.metrics),
                "total_alert_rules": len(self.alert_rules),
                "active_alerts": len(self.active_alerts),
                "metrics": {
                    name: self.get_metric_summary(name)
                    for name in self.metrics.keys()
                }
            }
        except Exception as e:
            logger.error(f"Failed to get metrics summary: {e}")
            return {"error": str(e)}

# Built-in notification handlers
async def email_notification_handler(alert: Alert, action: str):
    """Email notification handler"""
    try:
        # This would integrate with your email service
        logger.info(f"Email notification: {action} - {alert.message}")
    except Exception as e:
        logger.error(f"Email notification failed: {e}")

async def webhook_notification_handler(alert: Alert, action: str):
    """Webhook notification handler"""
    try:
        # This would send HTTP webhook
        logger.info(f"Webhook notification: {action} - {alert.message}")
    except Exception as e:
        logger.error(f"Webhook notification failed: {e}")

async def slack_notification_handler(alert: Alert, action: str):
    """Slack notification handler"""
    try:
        # This would integrate with Slack API
        logger.info(f"Slack notification: {action} - {alert.message}")
    except Exception as e:
        logger.error(f"Slack notification failed: {e}")

# Global metrics collector instance
metrics_collector = MetricsCollector()

# Register built-in notification handlers
metrics_collector.register_notification_handler("email", email_notification_handler)
metrics_collector.register_notification_handler("webhook", webhook_notification_handler)
metrics_collector.register_notification_handler("slack", slack_notification_handler)

# Utility functions
async def record_metric(name: str, value: float, labels: Dict[str, str] = None):
    """Record a metric value"""
    return await metrics_collector.record_metric(name, value, labels)

async def increment_counter(name: str, value: float = 1.0, labels: Dict[str, str] = None):
    """Increment a counter metric"""
    return await metrics_collector.record_metric(name, value, labels)

async def set_gauge(name: str, value: float, labels: Dict[str, str] = None):
    """Set a gauge metric value"""
    return await metrics_collector.record_metric(name, value, labels)

async def time_operation(name: str, labels: Dict[str, str] = None):
    """Context manager for timing operations"""
    from contextlib import asynccontextmanager
    
    @asynccontextmanager
    async def timer():
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            await metrics_collector.record_metric(name, duration, labels)
    
    return timer()