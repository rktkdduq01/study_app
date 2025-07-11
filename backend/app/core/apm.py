"""
Application Performance Monitoring (APM) System
Comprehensive performance monitoring and profiling for applications
"""

import asyncio
import time
import psutil
import resource
import gc
import sys
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, NamedTuple
from dataclasses import dataclass, asdict, field
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from functools import wraps
import json
import traceback
import inspect

from app.core.logger import get_logger
from app.core.redis_client import redis_client
from app.core.config import settings
from app.core.distributed_tracing import distributed_tracer, trace_operation

logger = get_logger(__name__)

class PerformanceLevel(str):
    """Performance level indicators"""
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"
    CRITICAL = "critical"

@dataclass
class PerformanceMetric:
    """Performance metric data"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    category: str
    level: PerformanceLevel
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SystemMetrics:
    """System-level metrics"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    load_average: List[float]
    process_count: int
    thread_count: int
    timestamp: datetime

@dataclass
class ApplicationMetrics:
    """Application-level metrics"""
    request_count: int
    requests_per_second: float
    average_response_time: float
    error_rate: float
    active_connections: int
    database_connections: int
    cache_hit_rate: float
    memory_usage_mb: float
    gc_count: int
    exception_count: int
    timestamp: datetime

@dataclass
class EndpointMetrics:
    """API endpoint metrics"""
    endpoint: str
    method: str
    request_count: int
    average_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    error_count: int
    error_rate: float
    last_accessed: datetime

class PerformanceProfiler:
    """Performance profiler for detailed analysis"""
    
    def __init__(self):
        self.function_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.endpoint_metrics: Dict[str, EndpointMetrics] = {}
        self.slow_queries: deque = deque(maxlen=100)
        self.memory_leaks: List[Dict[str, Any]] = []
        
    def profile_function(self, func_name: str, execution_time: float, 
                        memory_delta: float, **kwargs):
        """Record function execution metrics"""
        metric = {
            "function": func_name,
            "execution_time": execution_time,
            "memory_delta": memory_delta,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        
        self.function_metrics[func_name].append(metric)
        
        # Detect slow functions
        if execution_time > 1.0:  # > 1 second
            logger.warning(f"Slow function detected: {func_name} took {execution_time:.3f}s")
    
    def profile_endpoint(self, endpoint: str, method: str, response_time: float, 
                        status_code: int):
        """Record endpoint performance metrics"""
        key = f"{method}:{endpoint}"
        
        if key not in self.endpoint_metrics:
            self.endpoint_metrics[key] = EndpointMetrics(
                endpoint=endpoint,
                method=method,
                request_count=0,
                average_response_time=0.0,
                min_response_time=float('inf'),
                max_response_time=0.0,
                p95_response_time=0.0,
                error_count=0,
                error_rate=0.0,
                last_accessed=datetime.utcnow()
            )
        
        metrics = self.endpoint_metrics[key]
        metrics.request_count += 1
        metrics.last_accessed = datetime.utcnow()
        
        # Update response time statistics
        metrics.average_response_time = (
            (metrics.average_response_time * (metrics.request_count - 1) + response_time) /
            metrics.request_count
        )
        metrics.min_response_time = min(metrics.min_response_time, response_time)
        metrics.max_response_time = max(metrics.max_response_time, response_time)
        
        # Track errors
        if status_code >= 400:
            metrics.error_count += 1
            metrics.error_rate = metrics.error_count / metrics.request_count * 100
    
    def detect_memory_leak(self, threshold_mb: float = 100):
        """Detect potential memory leaks"""
        current_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        # Simple leak detection based on memory growth
        if hasattr(self, '_last_memory_check'):
            growth = current_memory - self._last_memory_check
            if growth > threshold_mb:
                leak_info = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "memory_growth_mb": growth,
                    "current_memory_mb": current_memory,
                    "gc_stats": {
                        "gen0": gc.get_count()[0],
                        "gen1": gc.get_count()[1],
                        "gen2": gc.get_count()[2]
                    }
                }
                
                self.memory_leaks.append(leak_info)
                logger.warning(f"Potential memory leak detected: {growth:.2f}MB growth")
        
        self._last_memory_check = current_memory

class APMCollector:
    """Advanced APM metrics collector"""
    
    def __init__(self):
        self.profiler = PerformanceProfiler()
        self.system_metrics: deque = deque(maxlen=1440)  # 24 hours at 1-minute intervals
        self.app_metrics: deque = deque(maxlen=1440)
        self.alerts: deque = deque(maxlen=1000)
        
        # Performance thresholds
        self.thresholds = {
            "cpu_critical": 90.0,
            "memory_critical": 85.0,
            "response_time_critical": 5.0,
            "error_rate_critical": 10.0,
            "disk_critical": 90.0
        }
        
        # Background collection task
        self._collection_task = None
        self._start_collection()
    
    def _start_collection(self):
        """Start background metrics collection"""
        if self._collection_task is None:
            self._collection_task = asyncio.create_task(self._collect_metrics_loop())
    
    async def _collect_metrics_loop(self):
        """Background metrics collection loop"""
        while True:
            try:
                await asyncio.sleep(60)  # Collect every minute
                await self._collect_system_metrics()
                await self._collect_application_metrics()
                await self._analyze_performance()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
    
    async def _collect_system_metrics(self):
        """Collect system-level metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            # Network metrics
            network = psutil.net_io_counters()
            
            # System load
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            
            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / 1024 / 1024,
                memory_available_mb=memory.available / 1024 / 1024,
                disk_usage_percent=disk.percent,
                disk_io_read_mb=disk_io.read_bytes / 1024 / 1024 if disk_io else 0,
                disk_io_write_mb=disk_io.write_bytes / 1024 / 1024 if disk_io else 0,
                network_sent_mb=network.bytes_sent / 1024 / 1024 if network else 0,
                network_recv_mb=network.bytes_recv / 1024 / 1024 if network else 0,
                load_average=list(load_avg),
                process_count=len(psutil.pids()),
                thread_count=threading.active_count(),
                timestamp=datetime.utcnow()
            )
            
            self.system_metrics.append(metrics)
            
            # Store in Redis for persistence
            await self._store_metrics("system", asdict(metrics))
            
        except Exception as e:
            logger.error(f"System metrics collection failed: {e}")
    
    async def _collect_application_metrics(self):
        """Collect application-level metrics"""
        try:
            # Get process info
            process = psutil.Process()
            
            # Memory info
            memory_info = process.memory_info()
            
            # GC info
            gc_stats = gc.get_stats()
            gc_count = sum(stat['collections'] for stat in gc_stats)
            
            # Calculate derived metrics
            total_requests = sum(
                ep.request_count for ep in self.profiler.endpoint_metrics.values()
            )
            
            total_errors = sum(
                ep.error_count for ep in self.profiler.endpoint_metrics.values()
            )
            
            avg_response_time = (
                sum(ep.average_response_time * ep.request_count 
                    for ep in self.profiler.endpoint_metrics.values()) / 
                max(total_requests, 1)
            )
            
            error_rate = (total_errors / max(total_requests, 1)) * 100
            
            metrics = ApplicationMetrics(
                request_count=total_requests,
                requests_per_second=self._calculate_rps(),
                average_response_time=avg_response_time,
                error_rate=error_rate,
                active_connections=self._get_active_connections(),
                database_connections=self._get_db_connections(),
                cache_hit_rate=self._get_cache_hit_rate(),
                memory_usage_mb=memory_info.rss / 1024 / 1024,
                gc_count=gc_count,
                exception_count=len(self.profiler.memory_leaks),
                timestamp=datetime.utcnow()
            )
            
            self.app_metrics.append(metrics)
            
            # Store in Redis
            await self._store_metrics("application", asdict(metrics))
            
        except Exception as e:
            logger.error(f"Application metrics collection failed: {e}")
    
    def _calculate_rps(self) -> float:
        """Calculate requests per second"""
        if len(self.app_metrics) < 2:
            return 0.0
        
        current = self.app_metrics[-1]
        previous = self.app_metrics[-2]
        
        time_diff = (current.timestamp - previous.timestamp).total_seconds()
        request_diff = current.request_count - previous.request_count
        
        return request_diff / max(time_diff, 1)
    
    def _get_active_connections(self) -> int:
        """Get active connection count"""
        try:
            connections = psutil.net_connections(kind='inet')
            return len([c for c in connections if c.status == 'ESTABLISHED'])
        except:
            return 0
    
    def _get_db_connections(self) -> int:
        """Get database connection count"""
        # This would integrate with your database connection pool
        return 0
    
    def _get_cache_hit_rate(self) -> float:
        """Get cache hit rate"""
        # This would integrate with your cache system
        return 95.0
    
    async def _store_metrics(self, category: str, metrics: Dict[str, Any]):
        """Store metrics in Redis"""
        try:
            # Convert datetime objects to ISO strings
            for key, value in metrics.items():
                if isinstance(value, datetime):
                    metrics[key] = value.isoformat()
            
            key = f"apm_metrics:{category}:{datetime.utcnow().strftime('%Y%m%d_%H%M')}"
            await redis_client.setex(key, 3600 * 24, json.dumps(metrics))  # Keep for 24 hours
            
        except Exception as e:
            logger.error(f"Failed to store {category} metrics: {e}")
    
    async def _analyze_performance(self):
        """Analyze performance and generate alerts"""
        try:
            if not self.system_metrics or not self.app_metrics:
                return
            
            latest_system = self.system_metrics[-1]
            latest_app = self.app_metrics[-1]
            
            alerts = []
            
            # System-level alerts
            if latest_system.cpu_percent > self.thresholds["cpu_critical"]:
                alerts.append({
                    "type": "cpu_critical",
                    "message": f"High CPU usage: {latest_system.cpu_percent:.1f}%",
                    "severity": "critical",
                    "value": latest_system.cpu_percent
                })
            
            if latest_system.memory_percent > self.thresholds["memory_critical"]:
                alerts.append({
                    "type": "memory_critical",
                    "message": f"High memory usage: {latest_system.memory_percent:.1f}%",
                    "severity": "critical",
                    "value": latest_system.memory_percent
                })
            
            if latest_system.disk_usage_percent > self.thresholds["disk_critical"]:
                alerts.append({
                    "type": "disk_critical",
                    "message": f"High disk usage: {latest_system.disk_usage_percent:.1f}%",
                    "severity": "critical",
                    "value": latest_system.disk_usage_percent
                })
            
            # Application-level alerts
            if latest_app.average_response_time > self.thresholds["response_time_critical"]:
                alerts.append({
                    "type": "response_time_critical",
                    "message": f"High response time: {latest_app.average_response_time:.3f}s",
                    "severity": "warning",
                    "value": latest_app.average_response_time
                })
            
            if latest_app.error_rate > self.thresholds["error_rate_critical"]:
                alerts.append({
                    "type": "error_rate_critical",
                    "message": f"High error rate: {latest_app.error_rate:.1f}%",
                    "severity": "critical",
                    "value": latest_app.error_rate
                })
            
            # Store alerts
            for alert in alerts:
                alert["timestamp"] = datetime.utcnow().isoformat()
                self.alerts.append(alert)
                logger.warning(f"APM Alert: {alert['message']}")
                
                # Store in Redis for alert management
                await redis_client.lpush("apm_alerts", json.dumps(alert))
                await redis_client.expire("apm_alerts", 86400 * 7)  # Keep for 7 days
            
        except Exception as e:
            logger.error(f"Performance analysis failed: {e}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        try:
            if not self.system_metrics or not self.app_metrics:
                return {"status": "no_data"}
            
            latest_system = self.system_metrics[-1]
            latest_app = self.app_metrics[-1]
            
            # Calculate performance level
            performance_scores = []
            
            # CPU score
            cpu_score = max(0, 100 - latest_system.cpu_percent)
            performance_scores.append(cpu_score)
            
            # Memory score
            memory_score = max(0, 100 - latest_system.memory_percent)
            performance_scores.append(memory_score)
            
            # Response time score
            response_time_score = max(0, 100 - (latest_app.average_response_time * 20))
            performance_scores.append(response_time_score)
            
            # Error rate score
            error_rate_score = max(0, 100 - (latest_app.error_rate * 10))
            performance_scores.append(error_rate_score)
            
            overall_score = sum(performance_scores) / len(performance_scores)
            
            # Determine performance level
            if overall_score >= 90:
                performance_level = PerformanceLevel.EXCELLENT
            elif overall_score >= 75:
                performance_level = PerformanceLevel.GOOD
            elif overall_score >= 60:
                performance_level = PerformanceLevel.AVERAGE
            elif overall_score >= 40:
                performance_level = PerformanceLevel.POOR
            else:
                performance_level = PerformanceLevel.CRITICAL
            
            return {
                "overall_score": round(overall_score, 1),
                "performance_level": performance_level,
                "system_metrics": {
                    "cpu_percent": latest_system.cpu_percent,
                    "memory_percent": latest_system.memory_percent,
                    "disk_usage_percent": latest_system.disk_usage_percent,
                    "load_average": latest_system.load_average
                },
                "application_metrics": {
                    "requests_per_second": latest_app.requests_per_second,
                    "average_response_time": latest_app.average_response_time,
                    "error_rate": latest_app.error_rate,
                    "memory_usage_mb": latest_app.memory_usage_mb
                },
                "endpoint_performance": [
                    {
                        "endpoint": ep.endpoint,
                        "method": ep.method,
                        "avg_response_time": ep.average_response_time,
                        "request_count": ep.request_count,
                        "error_rate": ep.error_rate
                    }
                    for ep in sorted(
                        self.profiler.endpoint_metrics.values(),
                        key=lambda x: x.request_count,
                        reverse=True
                    )[:10]  # Top 10 endpoints
                ],
                "recent_alerts": [
                    alert for alert in list(self.alerts)[-5:]  # Last 5 alerts
                ],
                "memory_leaks": len(self.profiler.memory_leaks),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance summary: {e}")
            return {"status": "error", "error": str(e)}

# Decorators for automatic performance monitoring
def monitor_performance(func_name: str = None):
    """Decorator to monitor function performance"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            name = func_name or f"{func.__module__}.{func.__name__}"
            
            # Memory before
            memory_before = psutil.Process().memory_info().rss / 1024 / 1024
            start_time = time.time()
            
            try:
                # Use distributed tracing context
                async with trace_operation(f"apm.{name}") as span:
                    span.set_attribute("function.name", name)
                    span.set_attribute("function.type", "async")
                    
                    result = await func(*args, **kwargs)
                    
                    # Record success metrics
                    execution_time = time.time() - start_time
                    memory_after = psutil.Process().memory_info().rss / 1024 / 1024
                    memory_delta = memory_after - memory_before
                    
                    apm_collector.profiler.profile_function(
                        name, execution_time, memory_delta, status="success"
                    )
                    
                    span.set_attribute("performance.execution_time", execution_time)
                    span.set_attribute("performance.memory_delta", memory_delta)
                    
                    return result
                    
            except Exception as e:
                execution_time = time.time() - start_time
                memory_after = psutil.Process().memory_info().rss / 1024 / 1024
                memory_delta = memory_after - memory_before
                
                apm_collector.profiler.profile_function(
                    name, execution_time, memory_delta, 
                    status="error", error=str(e)
                )
                
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            name = func_name or f"{func.__module__}.{func.__name__}"
            
            memory_before = psutil.Process().memory_info().rss / 1024 / 1024
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                execution_time = time.time() - start_time
                memory_after = psutil.Process().memory_info().rss / 1024 / 1024
                memory_delta = memory_after - memory_before
                
                apm_collector.profiler.profile_function(
                    name, execution_time, memory_delta, status="success"
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                memory_after = psutil.Process().memory_info().rss / 1024 / 1024
                memory_delta = memory_after - memory_before
                
                apm_collector.profiler.profile_function(
                    name, execution_time, memory_delta,
                    status="error", error=str(e)
                )
                
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

@asynccontextmanager
async def performance_context(operation_name: str):
    """Context manager for performance monitoring"""
    start_time = time.time()
    memory_before = psutil.Process().memory_info().rss / 1024 / 1024
    
    try:
        async with trace_operation(f"apm.{operation_name}") as span:
            span.set_attribute("apm.operation", operation_name)
            yield span
            
    finally:
        execution_time = time.time() - start_time
        memory_after = psutil.Process().memory_info().rss / 1024 / 1024
        memory_delta = memory_after - memory_before
        
        apm_collector.profiler.profile_function(
            operation_name, execution_time, memory_delta
        )

# Global APM collector instance
apm_collector = APMCollector()

# Utility functions
async def record_endpoint_performance(endpoint: str, method: str, 
                                    response_time: float, status_code: int):
    """Record endpoint performance metrics"""
    apm_collector.profiler.profile_endpoint(endpoint, method, response_time, status_code)

async def get_apm_dashboard_data() -> Dict[str, Any]:
    """Get APM dashboard data"""
    return apm_collector.get_performance_summary()

async def get_performance_alerts(limit: int = 50) -> List[Dict[str, Any]]:
    """Get recent performance alerts"""
    return list(apm_collector.alerts)[-limit:]

async def trigger_memory_leak_detection():
    """Manually trigger memory leak detection"""
    apm_collector.profiler.detect_memory_leak()

def set_performance_threshold(metric: str, value: float):
    """Set performance threshold for alerts"""
    if metric in apm_collector.thresholds:
        apm_collector.thresholds[metric] = value
        logger.info(f"Updated {metric} threshold to {value}")