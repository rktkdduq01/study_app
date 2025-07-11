"""
APM Dashboard Utilities
Real-time dashboard and visualization utilities for APM data
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import asdict

from app.core.logger import get_logger
from app.core.apm import apm_collector
from app.core.redis_client import redis_client
from app.core.websocket_manager import websocket_manager

logger = get_logger(__name__)

class APMDashboard:
    """Real-time APM dashboard manager"""
    
    def __init__(self):
        self.subscribers: Dict[str, Any] = {}
        self.update_interval = 5  # seconds
        self._update_task = None
        
    async def start_real_time_updates(self):
        """Start real-time dashboard updates"""
        if self._update_task is None:
            self._update_task = asyncio.create_task(self._real_time_update_loop())
            logger.info("APM dashboard real-time updates started")
    
    async def stop_real_time_updates(self):
        """Stop real-time dashboard updates"""
        if self._update_task:
            self._update_task.cancel()
            self._update_task = None
            logger.info("APM dashboard real-time updates stopped")
    
    async def _real_time_update_loop(self):
        """Real-time update loop for dashboard"""
        while True:
            try:
                await asyncio.sleep(self.update_interval)
                await self._broadcast_dashboard_update()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Dashboard update error: {e}")
    
    async def _broadcast_dashboard_update(self):
        """Broadcast dashboard update to all subscribers"""
        try:
            # Get current dashboard data
            dashboard_data = await self._get_real_time_dashboard_data()
            
            # Broadcast to WebSocket subscribers
            await websocket_manager.broadcast_to_group(
                "apm_dashboard",
                {
                    "type": "dashboard_update",
                    "data": dashboard_data,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Store in Redis for caching
            await redis_client.setex(
                "apm_dashboard_cache",
                60,  # 1 minute cache
                json.dumps(dashboard_data)
            )
            
        except Exception as e:
            logger.error(f"Failed to broadcast dashboard update: {e}")
    
    async def _get_real_time_dashboard_data(self) -> Dict[str, Any]:
        """Get real-time dashboard data"""
        try:
            # Get performance summary
            performance_summary = apm_collector.get_performance_summary()
            
            # Get latest metrics
            latest_system = None
            latest_app = None
            
            if apm_collector.system_metrics:
                latest_system = asdict(apm_collector.system_metrics[-1])
                latest_system['timestamp'] = latest_system['timestamp'].isoformat()
            
            if apm_collector.app_metrics:
                latest_app = asdict(apm_collector.app_metrics[-1])
                latest_app['timestamp'] = latest_app['timestamp'].isoformat()
            
            # Get recent trends
            system_trend = await self._calculate_system_trend()
            app_trend = await self._calculate_app_trend()
            
            # Get active alerts
            recent_alerts = list(apm_collector.alerts)[-10:]  # Last 10 alerts
            
            # Get top slow endpoints
            slow_endpoints = sorted(
                apm_collector.profiler.endpoint_metrics.values(),
                key=lambda x: x.average_response_time,
                reverse=True
            )[:5]
            
            return {
                "performance_summary": performance_summary,
                "latest_metrics": {
                    "system": latest_system,
                    "application": latest_app
                },
                "trends": {
                    "system": system_trend,
                    "application": app_trend
                },
                "alerts": recent_alerts,
                "slow_endpoints": [
                    {
                        "endpoint": ep.endpoint,
                        "method": ep.method,
                        "avg_response_time": ep.average_response_time,
                        "request_count": ep.request_count,
                        "error_rate": ep.error_rate
                    }
                    for ep in slow_endpoints
                ],
                "system_health": await self._get_system_health(),
                "real_time_stats": await self._get_real_time_stats()
            }
            
        except Exception as e:
            logger.error(f"Failed to get real-time dashboard data: {e}")
            return {"error": str(e)}
    
    async def _calculate_system_trend(self) -> Dict[str, Any]:
        """Calculate system metrics trend"""
        try:
            if len(apm_collector.system_metrics) < 2:
                return {"status": "insufficient_data"}
            
            recent_metrics = list(apm_collector.system_metrics)[-10:]  # Last 10 data points
            
            # Calculate trends
            cpu_values = [m.cpu_percent for m in recent_metrics]
            memory_values = [m.memory_percent for m in recent_metrics]
            
            cpu_trend = self._calculate_trend(cpu_values)
            memory_trend = self._calculate_trend(memory_values)
            
            return {
                "cpu": {
                    "current": cpu_values[-1],
                    "trend": cpu_trend,
                    "values": cpu_values
                },
                "memory": {
                    "current": memory_values[-1],
                    "trend": memory_trend,
                    "values": memory_values
                },
                "status": "ok"
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate system trend: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _calculate_app_trend(self) -> Dict[str, Any]:
        """Calculate application metrics trend"""
        try:
            if len(apm_collector.app_metrics) < 2:
                return {"status": "insufficient_data"}
            
            recent_metrics = list(apm_collector.app_metrics)[-10:]  # Last 10 data points
            
            # Calculate trends
            response_time_values = [m.average_response_time for m in recent_metrics]
            error_rate_values = [m.error_rate for m in recent_metrics]
            rps_values = [m.requests_per_second for m in recent_metrics]
            
            response_time_trend = self._calculate_trend(response_time_values)
            error_rate_trend = self._calculate_trend(error_rate_values)
            rps_trend = self._calculate_trend(rps_values)
            
            return {
                "response_time": {
                    "current": response_time_values[-1],
                    "trend": response_time_trend,
                    "values": response_time_values
                },
                "error_rate": {
                    "current": error_rate_values[-1],
                    "trend": error_rate_trend,
                    "values": error_rate_values
                },
                "requests_per_second": {
                    "current": rps_values[-1],
                    "trend": rps_trend,
                    "values": rps_values
                },
                "status": "ok"
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate app trend: {e}")
            return {"status": "error", "error": str(e)}
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from values"""
        if len(values) < 2:
            return "stable"
        
        # Simple trend calculation
        recent_avg = sum(values[-3:]) / min(len(values), 3)
        older_avg = sum(values[:-3]) / max(len(values) - 3, 1) if len(values) > 3 else recent_avg
        
        if recent_avg > older_avg * 1.1:
            return "increasing"
        elif recent_avg < older_avg * 0.9:
            return "decreasing"
        else:
            return "stable"
    
    async def _get_system_health(self) -> Dict[str, Any]:
        """Get system health status"""
        try:
            if not apm_collector.system_metrics:
                return {"status": "unknown"}
            
            latest = apm_collector.system_metrics[-1]
            
            health_score = 100
            issues = []
            
            # Check CPU
            if latest.cpu_percent > 90:
                health_score -= 30
                issues.append({"type": "cpu", "severity": "critical", "value": latest.cpu_percent})
            elif latest.cpu_percent > 70:
                health_score -= 15
                issues.append({"type": "cpu", "severity": "warning", "value": latest.cpu_percent})
            
            # Check Memory
            if latest.memory_percent > 90:
                health_score -= 30
                issues.append({"type": "memory", "severity": "critical", "value": latest.memory_percent})
            elif latest.memory_percent > 70:
                health_score -= 15
                issues.append({"type": "memory", "severity": "warning", "value": latest.memory_percent})
            
            # Check Disk
            if latest.disk_usage_percent > 90:
                health_score -= 20
                issues.append({"type": "disk", "severity": "critical", "value": latest.disk_usage_percent})
            elif latest.disk_usage_percent > 80:
                health_score -= 10
                issues.append({"type": "disk", "severity": "warning", "value": latest.disk_usage_percent})
            
            # Determine status
            if health_score >= 90:
                status = "excellent"
            elif health_score >= 70:
                status = "good"
            elif health_score >= 50:
                status = "fair"
            else:
                status = "poor"
            
            return {
                "status": status,
                "score": max(0, health_score),
                "issues": issues
            }
            
        except Exception as e:
            logger.error(f"Failed to get system health: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _get_real_time_stats(self) -> Dict[str, Any]:
        """Get real-time statistics"""
        try:
            # Get function call statistics
            function_stats = {}
            for func_name, metrics in apm_collector.profiler.function_metrics.items():
                if metrics:
                    recent_metrics = list(metrics)[-10:]  # Last 10 calls
                    function_stats[func_name] = {
                        "total_calls": len(metrics),
                        "recent_calls": len(recent_metrics),
                        "avg_execution_time": sum(m.get("execution_time", 0) for m in recent_metrics) / len(recent_metrics),
                        "recent_errors": sum(1 for m in recent_metrics if m.get("status") == "error")
                    }
            
            # Get endpoint statistics
            endpoint_stats = {}
            for ep in apm_collector.profiler.endpoint_metrics.values():
                endpoint_stats[f"{ep.method} {ep.endpoint}"] = {
                    "request_count": ep.request_count,
                    "avg_response_time": ep.average_response_time,
                    "error_rate": ep.error_rate,
                    "last_accessed": ep.last_accessed.isoformat()
                }
            
            return {
                "functions": function_stats,
                "endpoints": endpoint_stats,
                "active_alerts": len([a for a in apm_collector.alerts if a.get("severity") == "critical"]),
                "memory_leaks": len(apm_collector.profiler.memory_leaks),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get real-time stats: {e}")
            return {"error": str(e)}
    
    async def export_dashboard_data(self, format: str = "json", 
                                  time_range_hours: int = 24) -> Dict[str, Any]:
        """Export dashboard data for analysis"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=time_range_hours)
            
            # Collect historical data
            historical_data = {
                "export_info": {
                    "format": format,
                    "time_range": {
                        "start": start_time.isoformat(),
                        "end": end_time.isoformat(),
                        "hours": time_range_hours
                    },
                    "exported_at": datetime.utcnow().isoformat()
                },
                "performance_summary": apm_collector.get_performance_summary(),
                "system_metrics": [
                    {**asdict(m), "timestamp": m.timestamp.isoformat()}
                    for m in apm_collector.system_metrics
                    if start_time <= m.timestamp <= end_time
                ],
                "application_metrics": [
                    {**asdict(m), "timestamp": m.timestamp.isoformat()}
                    for m in apm_collector.app_metrics
                    if start_time <= m.timestamp <= end_time
                ],
                "alerts": [
                    alert for alert in apm_collector.alerts
                    if start_time <= datetime.fromisoformat(alert.get("timestamp", "1970-01-01")) <= end_time
                ],
                "endpoint_metrics": [
                    {
                        "endpoint": ep.endpoint,
                        "method": ep.method,
                        "request_count": ep.request_count,
                        "average_response_time": ep.average_response_time,
                        "min_response_time": ep.min_response_time,
                        "max_response_time": ep.max_response_time,
                        "error_count": ep.error_count,
                        "error_rate": ep.error_rate,
                        "last_accessed": ep.last_accessed.isoformat()
                    }
                    for ep in apm_collector.profiler.endpoint_metrics.values()
                ],
                "memory_leaks": apm_collector.profiler.memory_leaks
            }
            
            if format == "csv":
                # Convert to CSV format (simplified)
                return {"message": "CSV export not implemented yet", "data": historical_data}
            
            return historical_data
            
        except Exception as e:
            logger.error(f"Failed to export dashboard data: {e}")
            return {"error": str(e)}

# Global dashboard instance
apm_dashboard = APMDashboard()

# Utility functions
async def get_dashboard_cache() -> Optional[Dict[str, Any]]:
    """Get cached dashboard data"""
    try:
        cached_data = await redis_client.get("apm_dashboard_cache")
        if cached_data:
            return json.loads(cached_data)
        return None
    except Exception as e:
        logger.error(f"Failed to get dashboard cache: {e}")
        return None

async def generate_performance_alert(alert_type: str, message: str, 
                                   severity: str, value: float) -> bool:
    """Generate and broadcast performance alert"""
    try:
        alert = {
            "type": alert_type,
            "message": message,
            "severity": severity,
            "value": value,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add to collector
        apm_collector.alerts.append(alert)
        
        # Broadcast to dashboard subscribers
        await websocket_manager.broadcast_to_group(
            "apm_dashboard",
            {
                "type": "alert",
                "alert": alert
            }
        )
        
        # Store in Redis
        await redis_client.lpush("apm_alerts", json.dumps(alert))
        
        logger.warning(f"Performance alert generated: {message}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to generate performance alert: {e}")
        return False

async def start_dashboard():
    """Start APM dashboard"""
    await apm_dashboard.start_real_time_updates()

async def stop_dashboard():
    """Stop APM dashboard"""
    await apm_dashboard.stop_real_time_updates()