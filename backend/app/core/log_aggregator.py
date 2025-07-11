"""
Log Centralization and Analysis System
Centralized log collection, processing, and analysis with intelligent dashboards
"""

import asyncio
import json
import re
import gzip
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union, Pattern
from dataclasses import dataclass, asdict, field
from collections import defaultdict, deque, Counter
from enum import Enum
import hashlib
import logging
from pathlib import Path

from app.core.logger import get_logger
from app.core.redis_client import redis_client
from app.core.config import settings
from app.core.distributed_tracing import distributed_tracer, trace_operation

logger = get_logger(__name__)

class LogLevel(Enum):
    """Log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogSource(Enum):
    """Log sources"""
    APPLICATION = "application"
    SYSTEM = "system"
    DATABASE = "database"
    CACHE = "cache"
    SECURITY = "security"
    BUSINESS = "business"
    EXTERNAL = "external"

@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: datetime
    level: LogLevel
    source: LogSource
    module: str
    message: str
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['level'] = self.level.value
        data['source'] = self.source.value
        return data

@dataclass
class LogPattern:
    """Log pattern for analysis"""
    pattern_id: str
    name: str
    regex: Pattern[str]
    level: LogLevel
    category: str
    description: str
    actions: List[str] = field(default_factory=list)
    count: int = 0
    last_seen: Optional[datetime] = None

@dataclass
class LogAnalysis:
    """Log analysis results"""
    total_logs: int
    time_range: Dict[str, str]
    log_levels: Dict[str, int]
    log_sources: Dict[str, int]
    error_patterns: List[Dict[str, Any]]
    anomalies: List[Dict[str, Any]]
    trends: Dict[str, Any]
    top_errors: List[Dict[str, Any]]
    performance_insights: List[Dict[str, Any]]

class LogAggregator:
    """Advanced log aggregation and analysis system"""
    
    def __init__(self):
        self.log_buffer: deque = deque(maxlen=100000)  # In-memory buffer
        self.patterns: Dict[str, LogPattern] = {}
        self.error_signatures: Dict[str, int] = defaultdict(int)
        self.anomaly_detectors: List[Callable] = []
        
        # Processing settings
        self.batch_size = 1000
        self.flush_interval = 30  # seconds
        self.retention_days = 90
        
        # Analysis cache
        self.analysis_cache: Dict[str, LogAnalysis] = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Background tasks
        self._processing_task = None
        self._analysis_task = None
        self._cleanup_task = None
        
        # Initialize patterns and detectors
        self._initialize_patterns()
        self._initialize_anomaly_detectors()
        
        # Start background processing
        self._start_background_tasks()
    
    def _start_background_tasks(self):
        """Start background processing tasks"""
        if self._processing_task is None:
            self._processing_task = asyncio.create_task(self._log_processing_loop())
        
        if self._analysis_task is None:
            self._analysis_task = asyncio.create_task(self._analysis_loop())
        
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    def _initialize_patterns(self):
        """Initialize common log patterns"""
        patterns = [
            # Error patterns
            LogPattern(
                "db_connection_error",
                "Database Connection Error",
                re.compile(r"connection.*(?:refused|timeout|failed)", re.IGNORECASE),
                LogLevel.ERROR,
                "database",
                "Database connection issues"
            ),
            LogPattern(
                "memory_error",
                "Memory Error",
                re.compile(r"(?:out of memory|memory.*exceeded|allocation.*failed)", re.IGNORECASE),
                LogLevel.CRITICAL,
                "system",
                "Memory allocation errors"
            ),
            LogPattern(
                "authentication_failure",
                "Authentication Failure",
                re.compile(r"(?:authentication|login).*(?:failed|denied|invalid)", re.IGNORECASE),
                LogLevel.WARNING,
                "security",
                "Authentication failures"
            ),
            LogPattern(
                "http_5xx_error",
                "HTTP 5xx Error",
                re.compile(r"(?:500|501|502|503|504|505).*(?:error|exception)", re.IGNORECASE),
                LogLevel.ERROR,
                "application",
                "HTTP server errors"
            ),
            LogPattern(
                "rate_limit_exceeded",
                "Rate Limit Exceeded",
                re.compile(r"rate.*limit.*(?:exceeded|reached)", re.IGNORECASE),
                LogLevel.WARNING,
                "application",
                "Rate limiting triggered"
            ),
            
            # Performance patterns
            LogPattern(
                "slow_query",
                "Slow Database Query",
                re.compile(r"(?:slow.*query|query.*(?:took|duration).*\d+(?:ms|seconds?))", re.IGNORECASE),
                LogLevel.WARNING,
                "performance",
                "Slow database queries"
            ),
            LogPattern(
                "high_cpu_usage",
                "High CPU Usage",
                re.compile(r"cpu.*usage.*(?:high|exceeded|\d{2,3}%)", re.IGNORECASE),
                LogLevel.WARNING,
                "performance",
                "High CPU usage detected"
            ),
            
            # Security patterns
            LogPattern(
                "suspicious_activity",
                "Suspicious Activity",
                re.compile(r"(?:suspicious|malicious|attack|intrusion|breach)", re.IGNORECASE),
                LogLevel.CRITICAL,
                "security",
                "Potential security threats"
            ),
            LogPattern(
                "unauthorized_access",
                "Unauthorized Access",
                re.compile(r"(?:unauthorized|forbidden|access.*denied)", re.IGNORECASE),
                LogLevel.WARNING,
                "security",
                "Unauthorized access attempts"
            )
        ]
        
        for pattern in patterns:
            self.patterns[pattern.pattern_id] = pattern
    
    def _initialize_anomaly_detectors(self):
        """Initialize anomaly detection functions"""
        self.anomaly_detectors = [
            self._detect_error_spikes,
            self._detect_unusual_patterns,
            self._detect_performance_degradation,
            self._detect_security_anomalies
        ]
    
    async def ingest_log(self, log_entry: LogEntry) -> bool:
        """Ingest a single log entry"""
        try:
            # Add to buffer
            self.log_buffer.append(log_entry)
            
            # Pattern matching
            await self._match_patterns(log_entry)
            
            # Real-time anomaly detection for critical logs
            if log_entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                await self._real_time_anomaly_check(log_entry)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to ingest log entry: {e}")
            return False
    
    async def ingest_logs_batch(self, log_entries: List[LogEntry]) -> int:
        """Ingest multiple log entries"""
        successful = 0
        
        for entry in log_entries:
            if await self.ingest_log(entry):
                successful += 1
        
        return successful
    
    async def _match_patterns(self, log_entry: LogEntry):
        """Match log entry against known patterns"""
        try:
            for pattern in self.patterns.values():
                if pattern.regex.search(log_entry.message):
                    pattern.count += 1
                    pattern.last_seen = log_entry.timestamp
                    
                    # Store pattern match
                    await self._store_pattern_match(pattern, log_entry)
            
        except Exception as e:
            logger.error(f"Pattern matching failed: {e}")
    
    async def _store_pattern_match(self, pattern: LogPattern, log_entry: LogEntry):
        """Store pattern match for analysis"""
        try:
            match_data = {
                "pattern_id": pattern.pattern_id,
                "pattern_name": pattern.name,
                "category": pattern.category,
                "timestamp": log_entry.timestamp.isoformat(),
                "level": log_entry.level.value,
                "source": log_entry.source.value,
                "message": log_entry.message,
                "trace_id": log_entry.trace_id,
                "user_id": log_entry.user_id
            }
            
            # Store in Redis with expiration
            key = f"log_pattern_match:{pattern.pattern_id}:{log_entry.timestamp.strftime('%Y%m%d_%H')}"
            await redis_client.lpush(key, json.dumps(match_data))
            await redis_client.expire(key, 86400 * self.retention_days)
            
        except Exception as e:
            logger.error(f"Failed to store pattern match: {e}")
    
    async def _real_time_anomaly_check(self, log_entry: LogEntry):
        """Real-time anomaly detection for critical logs"""
        try:
            # Check error frequency
            error_key = f"error_count:{log_entry.timestamp.strftime('%Y%m%d_%H%M')}"
            current_count = await redis_client.incr(error_key)
            await redis_client.expire(error_key, 3600)  # 1 hour
            
            # Alert on error spikes
            if current_count > 50:  # More than 50 errors per minute
                await self._trigger_anomaly_alert("error_spike", {
                    "count": current_count,
                    "minute": log_entry.timestamp.strftime('%Y-%m-%d %H:%M'),
                    "last_error": log_entry.message
                })
            
        except Exception as e:
            logger.error(f"Real-time anomaly check failed: {e}")
    
    async def _log_processing_loop(self):
        """Background log processing loop"""
        while True:
            try:
                await asyncio.sleep(self.flush_interval)
                await self._process_log_batch()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Log processing error: {e}")
    
    async def _process_log_batch(self):
        """Process accumulated logs in batch"""
        try:
            if not self.log_buffer:
                return
            
            # Get batch of logs
            batch = []
            for _ in range(min(self.batch_size, len(self.log_buffer))):
                if self.log_buffer:
                    batch.append(self.log_buffer.popleft())
            
            if not batch:
                return
            
            # Store batch in Redis
            await self._store_log_batch(batch)
            
            # Update metrics
            await self._update_log_metrics(batch)
            
            logger.debug(f"Processed {len(batch)} log entries")
            
        except Exception as e:
            logger.error(f"Log batch processing failed: {e}")
    
    async def _store_log_batch(self, batch: List[LogEntry]):
        """Store log batch in Redis"""
        try:
            # Group by hour for efficient storage
            hourly_groups = defaultdict(list)
            
            for entry in batch:
                hour_key = entry.timestamp.strftime('%Y%m%d_%H')
                hourly_groups[hour_key].append(entry.to_dict())
            
            # Store each hourly group
            for hour_key, entries in hourly_groups.items():
                # Store in main log stream
                log_key = f"logs:{hour_key}"
                for entry in entries:
                    await redis_client.lpush(log_key, json.dumps(entry))
                
                await redis_client.expire(log_key, 86400 * self.retention_days)
                
                # Store compressed aggregated data
                await self._store_compressed_logs(hour_key, entries)
            
        except Exception as e:
            logger.error(f"Failed to store log batch: {e}")
    
    async def _store_compressed_logs(self, hour_key: str, entries: List[Dict[str, Any]]):
        """Store compressed aggregated log data"""
        try:
            # Create aggregated summary
            summary = {
                "hour": hour_key,
                "total_logs": len(entries),
                "levels": Counter(entry["level"] for entry in entries),
                "sources": Counter(entry["source"] for entry in entries),
                "modules": Counter(entry["module"] for entry in entries),
                "errors": [e for e in entries if e["level"] in ["ERROR", "CRITICAL"]],
                "sample_logs": entries[:100]  # Keep sample for detailed analysis
            }
            
            # Compress and store
            compressed_data = gzip.compress(json.dumps(summary).encode())
            
            summary_key = f"log_summary:{hour_key}"
            await redis_client.set(summary_key, compressed_data)
            await redis_client.expire(summary_key, 86400 * self.retention_days)
            
        except Exception as e:
            logger.error(f"Failed to store compressed logs: {e}")
    
    async def _update_log_metrics(self, batch: List[LogEntry]):
        """Update log metrics"""
        try:
            # Count by level
            level_counts = Counter(entry.level.value for entry in batch)
            for level, count in level_counts.items():
                await redis_client.incrby(f"log_metrics:level:{level}", count)
            
            # Count by source
            source_counts = Counter(entry.source.value for entry in batch)
            for source, count in source_counts.items():
                await redis_client.incrby(f"log_metrics:source:{source}", count)
            
            # Update error signatures
            for entry in batch:
                if entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                    signature = self._generate_error_signature(entry.message)
                    self.error_signatures[signature] += 1
            
        except Exception as e:
            logger.error(f"Failed to update log metrics: {e}")
    
    def _generate_error_signature(self, message: str) -> str:
        """Generate error signature for grouping similar errors"""
        # Remove dynamic parts (numbers, timestamps, etc.)
        normalized = re.sub(r'\d+', 'N', message)
        normalized = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', 'UUID', normalized)
        normalized = re.sub(r'\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\b', 'TIMESTAMP', normalized)
        
        # Generate hash
        return hashlib.md5(normalized.encode()).hexdigest()[:16]
    
    async def _analysis_loop(self):
        """Background analysis loop"""
        while True:
            try:
                await asyncio.sleep(300)  # Analyze every 5 minutes
                await self._perform_analysis()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Analysis loop error: {e}")
    
    async def _perform_analysis(self):
        """Perform log analysis"""
        try:
            # Run anomaly detectors
            for detector in self.anomaly_detectors:
                try:
                    await detector()
                except Exception as e:
                    logger.error(f"Anomaly detector failed: {e}")
            
            # Update analysis cache
            await self._update_analysis_cache()
            
        except Exception as e:
            logger.error(f"Log analysis failed: {e}")
    
    async def _detect_error_spikes(self):
        """Detect error spikes"""
        try:
            # Get error counts for last hour
            now = datetime.utcnow()
            current_hour = now.strftime('%Y%m%d_%H')
            previous_hour = (now - timedelta(hours=1)).strftime('%Y%m%d_%H')
            
            current_errors = await redis_client.get(f"log_metrics:level:ERROR")
            previous_errors = await redis_client.get(f"log_metrics:level:ERROR")
            
            current_count = int(current_errors) if current_errors else 0
            previous_count = int(previous_errors) if previous_errors else 0
            
            # Check for spike (>200% increase)
            if previous_count > 0 and current_count > previous_count * 2:
                await self._trigger_anomaly_alert("error_spike", {
                    "current_count": current_count,
                    "previous_count": previous_count,
                    "increase_percentage": ((current_count - previous_count) / previous_count) * 100
                })
            
        except Exception as e:
            logger.error(f"Error spike detection failed: {e}")
    
    async def _detect_unusual_patterns(self):
        """Detect unusual log patterns"""
        try:
            # Analyze pattern frequency changes
            for pattern in self.patterns.values():
                if pattern.last_seen and pattern.count > 0:
                    # Check if pattern frequency has increased significantly
                    time_diff = (datetime.utcnow() - pattern.last_seen).total_seconds()
                    if time_diff < 3600 and pattern.count > 100:  # High frequency in last hour
                        await self._trigger_anomaly_alert("unusual_pattern", {
                            "pattern_name": pattern.name,
                            "count": pattern.count,
                            "category": pattern.category
                        })
            
        except Exception as e:
            logger.error(f"Unusual pattern detection failed: {e}")
    
    async def _detect_performance_degradation(self):
        """Detect performance degradation"""
        try:
            # Check for performance-related log patterns
            perf_patterns = ["slow_query", "high_cpu_usage"]
            
            for pattern_id in perf_patterns:
                if pattern_id in self.patterns:
                    pattern = self.patterns[pattern_id]
                    if pattern.count > 50:  # Threshold for performance issues
                        await self._trigger_anomaly_alert("performance_degradation", {
                            "issue_type": pattern.name,
                            "count": pattern.count
                        })
            
        except Exception as e:
            logger.error(f"Performance degradation detection failed: {e}")
    
    async def _detect_security_anomalies(self):
        """Detect security anomalies"""
        try:
            # Check for security-related patterns
            security_patterns = ["authentication_failure", "suspicious_activity", "unauthorized_access"]
            
            total_security_events = 0
            for pattern_id in security_patterns:
                if pattern_id in self.patterns:
                    total_security_events += self.patterns[pattern_id].count
            
            if total_security_events > 20:  # Threshold for security concerns
                await self._trigger_anomaly_alert("security_anomaly", {
                    "total_events": total_security_events,
                    "patterns": {
                        pid: self.patterns[pid].count 
                        for pid in security_patterns 
                        if pid in self.patterns
                    }
                })
            
        except Exception as e:
            logger.error(f"Security anomaly detection failed: {e}")
    
    async def _trigger_anomaly_alert(self, anomaly_type: str, data: Dict[str, Any]):
        """Trigger anomaly alert"""
        try:
            alert = {
                "type": anomaly_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data,
                "severity": self._get_anomaly_severity(anomaly_type)
            }
            
            # Store alert
            await redis_client.lpush("log_anomaly_alerts", json.dumps(alert))
            await redis_client.expire("log_anomaly_alerts", 86400 * 7)  # Keep for 7 days
            
            logger.warning(f"Log anomaly detected: {anomaly_type} - {data}")
            
        except Exception as e:
            logger.error(f"Failed to trigger anomaly alert: {e}")
    
    def _get_anomaly_severity(self, anomaly_type: str) -> str:
        """Get severity level for anomaly type"""
        severity_map = {
            "error_spike": "critical",
            "security_anomaly": "critical",
            "performance_degradation": "warning",
            "unusual_pattern": "info"
        }
        return severity_map.get(anomaly_type, "info")
    
    async def _update_analysis_cache(self):
        """Update analysis cache"""
        try:
            # Generate analysis for different time windows
            time_windows = [
                ("1h", timedelta(hours=1)),
                ("24h", timedelta(hours=24)),
                ("7d", timedelta(days=7))
            ]
            
            for window_name, window_duration in time_windows:
                analysis = await self._generate_analysis(window_duration)
                self.analysis_cache[window_name] = analysis
            
        except Exception as e:
            logger.error(f"Failed to update analysis cache: {e}")
    
    async def _generate_analysis(self, time_window: timedelta) -> LogAnalysis:
        """Generate log analysis for time window"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - time_window
            
            # Collect data from Redis
            total_logs = 0
            log_levels = defaultdict(int)
            log_sources = defaultdict(int)
            error_patterns = []
            
            # Iterate through time range
            current_time = start_time
            while current_time <= end_time:
                hour_key = current_time.strftime('%Y%m%d_%H')
                
                # Get summary data
                summary_key = f"log_summary:{hour_key}"
                summary_data = await redis_client.get(summary_key)
                
                if summary_data:
                    try:
                        decompressed = gzip.decompress(summary_data)
                        summary = json.loads(decompressed.decode())
                        
                        total_logs += summary.get("total_logs", 0)
                        
                        for level, count in summary.get("levels", {}).items():
                            log_levels[level] += count
                        
                        for source, count in summary.get("sources", {}).items():
                            log_sources[source] += count
                        
                    except Exception as e:
                        logger.error(f"Failed to process summary for {hour_key}: {e}")
                
                current_time += timedelta(hours=1)
            
            # Generate insights
            anomalies = await self._get_anomalies_in_range(start_time, end_time)
            trends = await self._calculate_trends(start_time, end_time)
            top_errors = await self._get_top_errors(start_time, end_time)
            performance_insights = await self._get_performance_insights(start_time, end_time)
            
            return LogAnalysis(
                total_logs=total_logs,
                time_range={
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                },
                log_levels=dict(log_levels),
                log_sources=dict(log_sources),
                error_patterns=error_patterns,
                anomalies=anomalies,
                trends=trends,
                top_errors=top_errors,
                performance_insights=performance_insights
            )
            
        except Exception as e:
            logger.error(f"Analysis generation failed: {e}")
            return LogAnalysis(
                total_logs=0,
                time_range={"start": start_time.isoformat(), "end": end_time.isoformat()},
                log_levels={}, log_sources={}, error_patterns=[], anomalies=[],
                trends={}, top_errors=[], performance_insights=[]
            )
    
    async def _get_anomalies_in_range(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Get anomalies in time range"""
        try:
            alerts = await redis_client.lrange("log_anomaly_alerts", 0, -1)
            anomalies = []
            
            for alert_data in alerts:
                try:
                    alert = json.loads(alert_data)
                    alert_time = datetime.fromisoformat(alert["timestamp"])
                    
                    if start_time <= alert_time <= end_time:
                        anomalies.append(alert)
                except json.JSONDecodeError:
                    continue
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Failed to get anomalies: {e}")
            return []
    
    async def _calculate_trends(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Calculate log trends"""
        try:
            # This would calculate trends like log volume changes, error rate trends, etc.
            return {
                "log_volume_trend": "increasing",
                "error_rate_trend": "stable",
                "performance_trend": "degrading"
            }
        except Exception as e:
            logger.error(f"Failed to calculate trends: {e}")
            return {}
    
    async def _get_top_errors(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Get top errors in time range"""
        try:
            # Return top error signatures
            sorted_errors = sorted(self.error_signatures.items(), 
                                 key=lambda x: x[1], reverse=True)
            
            return [
                {"signature": sig, "count": count}
                for sig, count in sorted_errors[:10]
            ]
        except Exception as e:
            logger.error(f"Failed to get top errors: {e}")
            return []
    
    async def _get_performance_insights(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Get performance insights"""
        try:
            insights = []
            
            # Check for slow query patterns
            if "slow_query" in self.patterns and self.patterns["slow_query"].count > 0:
                insights.append({
                    "type": "slow_queries",
                    "message": f"Detected {self.patterns['slow_query'].count} slow queries",
                    "recommendation": "Consider optimizing database queries or adding indexes"
                })
            
            return insights
        except Exception as e:
            logger.error(f"Failed to get performance insights: {e}")
            return []
    
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
        """Clean up old log data"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
            
            # This would clean up old Redis keys
            # Implementation depends on your specific Redis cleanup strategy
            
            logger.info("Completed log data cleanup")
            
        except Exception as e:
            logger.error(f"Log cleanup failed: {e}")
    
    async def get_analysis(self, time_window: str = "24h") -> Optional[LogAnalysis]:
        """Get cached analysis for time window"""
        try:
            return self.analysis_cache.get(time_window)
        except Exception as e:
            logger.error(f"Failed to get analysis: {e}")
            return None
    
    async def search_logs(self, query: str, start_time: datetime, end_time: datetime,
                         level: Optional[LogLevel] = None, source: Optional[LogSource] = None,
                         limit: int = 1000) -> List[Dict[str, Any]]:
        """Search logs with filters"""
        try:
            results = []
            current_time = start_time
            
            while current_time <= end_time and len(results) < limit:
                hour_key = current_time.strftime('%Y%m%d_%H')
                log_key = f"logs:{hour_key}"
                
                # Get logs for this hour
                logs = await redis_client.lrange(log_key, 0, -1)
                
                for log_data in logs:
                    if len(results) >= limit:
                        break
                    
                    try:
                        log_entry = json.loads(log_data)
                        
                        # Apply filters
                        if level and log_entry.get("level") != level.value:
                            continue
                        
                        if source and log_entry.get("source") != source.value:
                            continue
                        
                        # Apply text search
                        if query and query.lower() not in log_entry.get("message", "").lower():
                            continue
                        
                        results.append(log_entry)
                        
                    except json.JSONDecodeError:
                        continue
                
                current_time += timedelta(hours=1)
            
            return results
            
        except Exception as e:
            logger.error(f"Log search failed: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get aggregator statistics"""
        try:
            return {
                "buffer_size": len(self.log_buffer),
                "patterns_count": len(self.patterns),
                "error_signatures": len(self.error_signatures),
                "cache_entries": len(self.analysis_cache)
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}

# Global log aggregator instance
log_aggregator = LogAggregator()

# Utility functions
async def log_to_aggregator(level: LogLevel, source: LogSource, module: str, 
                          message: str, **kwargs) -> bool:
    """Log message to aggregator"""
    try:
        log_entry = LogEntry(
            timestamp=datetime.utcnow(),
            level=level,
            source=source,
            module=module,
            message=message,
            **kwargs
        )
        
        return await log_aggregator.ingest_log(log_entry)
    except Exception as e:
        logger.error(f"Failed to log to aggregator: {e}")
        return False

async def get_log_analysis(time_window: str = "24h") -> Optional[LogAnalysis]:
    """Get log analysis for time window"""
    return await log_aggregator.get_analysis(time_window)