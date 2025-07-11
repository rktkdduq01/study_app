"""
Distributed Tracing System
OpenTelemetry-based distributed tracing for microservices observability
"""

import asyncio
import time
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, asdict, field
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from contextvars import ContextVar
import functools

from opentelemetry import trace, baggage, context
from opentelemetry.trace import Status, StatusCode, SpanKind
from opentelemetry.sdk.trace import TracerProvider, Span
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.propagate import inject, extract
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from app.core.logger import get_logger
from app.core.config import settings
from app.core.redis_client import redis_client

logger = get_logger(__name__)

# Context variables for trace correlation
current_trace_id: ContextVar[str] = ContextVar('current_trace_id', default=None)
current_span_id: ContextVar[str] = ContextVar('current_span_id', default=None)
current_user_id: ContextVar[str] = ContextVar('current_user_id', default=None)

@dataclass
class SpanMetadata:
    """Span metadata for enrichment"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    service_name: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_ms: Optional[float]
    status: str
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    baggage: Dict[str, str] = field(default_factory=dict)

@dataclass
class TraceConfiguration:
    """Distributed tracing configuration"""
    service_name: str = "quest-edu-backend"
    service_version: str = "1.0.0"
    environment: str = "development"
    
    # Exporters
    enable_jaeger: bool = True
    jaeger_endpoint: str = "http://localhost:14268/api/traces"
    enable_zipkin: bool = False
    zipkin_endpoint: str = "http://localhost:9411/api/v2/spans"
    enable_console: bool = False
    
    # Sampling
    sampling_rate: float = 1.0  # 100% sampling in development
    
    # Custom attributes
    enable_custom_attributes: bool = True
    enable_db_query_tracing: bool = True
    enable_redis_tracing: bool = True
    enable_http_tracing: bool = True
    
    # Performance
    max_spans_per_trace: int = 1000
    max_trace_duration_seconds: int = 300  # 5 minutes

class DistributedTracer:
    """Enhanced distributed tracing system"""
    
    def __init__(self, config: TraceConfiguration = None):
        self.config = config or TraceConfiguration()
        self.tracer_provider = None
        self.tracer = None
        self.active_spans: Dict[str, SpanMetadata] = {}
        
        # Trace correlation
        self.trace_correlations: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
        # Metrics
        self.span_metrics: deque = deque(maxlen=10000)
        self.trace_stats = {
            "total_traces": 0,
            "total_spans": 0,
            "error_spans": 0,
            "slow_spans": 0
        }
        
        # Initialize tracing
        self._initialize_tracing()
    
    def _initialize_tracing(self):
        """Initialize OpenTelemetry tracing"""
        try:
            # Create resource
            resource = Resource.create({
                SERVICE_NAME: self.config.service_name,
                "service.version": self.config.service_version,
                "deployment.environment": self.config.environment
            })
            
            # Create tracer provider
            self.tracer_provider = TracerProvider(resource=resource)
            trace.set_tracer_provider(self.tracer_provider)
            
            # Add exporters
            self._setup_exporters()
            
            # Get tracer
            self.tracer = trace.get_tracer(__name__)
            
            # Instrument libraries
            self._instrument_libraries()
            
            logger.info(f"Distributed tracing initialized for {self.config.service_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize distributed tracing: {e}")
            raise
    
    def _setup_exporters(self):
        """Setup trace exporters"""
        try:
            # Jaeger exporter
            if self.config.enable_jaeger:
                jaeger_exporter = JaegerExporter(
                    endpoint=self.config.jaeger_endpoint
                )
                self.tracer_provider.add_span_processor(
                    BatchSpanProcessor(jaeger_exporter)
                )
                logger.info(f"Jaeger exporter configured: {self.config.jaeger_endpoint}")
            
            # Zipkin exporter
            if self.config.enable_zipkin:
                zipkin_exporter = ZipkinExporter(
                    endpoint=self.config.zipkin_endpoint
                )
                self.tracer_provider.add_span_processor(
                    BatchSpanProcessor(zipkin_exporter)
                )
                logger.info(f"Zipkin exporter configured: {self.config.zipkin_endpoint}")
            
            # Console exporter (for development)
            if self.config.enable_console:
                console_exporter = ConsoleSpanExporter()
                self.tracer_provider.add_span_processor(
                    BatchSpanProcessor(console_exporter)
                )
                logger.info("Console exporter configured")
                
        except Exception as e:
            logger.error(f"Failed to setup exporters: {e}")
    
    def _instrument_libraries(self):
        """Automatically instrument libraries"""
        try:
            # FastAPI instrumentation
            FastAPIInstrumentor().instrument()
            
            # Database instrumentation
            if self.config.enable_db_query_tracing:
                SQLAlchemyInstrumentor().instrument()
                Psycopg2Instrumentor().instrument()
            
            # Redis instrumentation
            if self.config.enable_redis_tracing:
                RedisInstrumentor().instrument()
            
            # HTTP client instrumentation
            if self.config.enable_http_tracing:
                HTTPXClientInstrumentor().instrument()
            
            logger.info("Library instrumentation completed")
            
        except Exception as e:
            logger.error(f"Failed to instrument libraries: {e}")
    
    @asynccontextmanager
    async def trace_context(self, operation_name: str, **attributes):
        """Context manager for creating traced operations"""
        span = self.tracer.start_span(operation_name)
        
        try:
            # Set span attributes
            for key, value in attributes.items():
                span.set_attribute(key, str(value))
            
            # Set context variables
            trace_id = format(span.get_span_context().trace_id, '032x')
            span_id = format(span.get_span_context().span_id, '016x')
            
            current_trace_id.set(trace_id)
            current_span_id.set(span_id)
            
            # Create span metadata
            span_metadata = SpanMetadata(
                trace_id=trace_id,
                span_id=span_id,
                parent_span_id=None,  # Will be set if parent exists
                operation_name=operation_name,
                service_name=self.config.service_name,
                start_time=datetime.utcnow(),
                end_time=None,
                duration_ms=None,
                status="active",
                tags=attributes
            )
            
            self.active_spans[span_id] = span_metadata
            
            yield span
            
        except Exception as e:
            # Record exception
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span_metadata.status = "error"
            self.trace_stats["error_spans"] += 1
            raise
            
        finally:
            # End span
            span.end()
            
            # Update metadata
            if span_id in self.active_spans:
                span_metadata = self.active_spans[span_id]
                span_metadata.end_time = datetime.utcnow()
                span_metadata.duration_ms = (
                    (span_metadata.end_time - span_metadata.start_time).total_seconds() * 1000
                )
                
                if span_metadata.status != "error":
                    span_metadata.status = "completed"
                
                # Check if slow span
                if span_metadata.duration_ms > 1000:  # > 1 second
                    self.trace_stats["slow_spans"] += 1
                
                # Store span metrics
                self.span_metrics.append(span_metadata)
                
                # Remove from active spans
                del self.active_spans[span_id]
            
            self.trace_stats["total_spans"] += 1
    
    def start_span(self, operation_name: str, **attributes) -> Any:
        """Start a new span"""
        span = self.tracer.start_span(operation_name)
        
        # Set attributes
        for key, value in attributes.items():
            span.set_attribute(key, str(value))
        
        return span
    
    def get_current_trace_id(self) -> Optional[str]:
        """Get current trace ID"""
        return current_trace_id.get(None)
    
    def get_current_span_id(self) -> Optional[str]:
        """Get current span ID"""
        return current_span_id.get(None)
    
    def add_span_attribute(self, span: Any, key: str, value: Any):
        """Add attribute to span"""
        if span and span.is_recording():
            span.set_attribute(key, str(value))
    
    def add_span_event(self, span: Any, event_name: str, **attributes):
        """Add event to span"""
        if span and span.is_recording():
            span.add_event(event_name, attributes)
    
    def record_exception(self, span: Any, exception: Exception):
        """Record exception in span"""
        if span and span.is_recording():
            span.record_exception(exception)
            span.set_status(Status(StatusCode.ERROR, str(exception)))
    
    def inject_trace_context(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Inject trace context into headers for propagation"""
        propagator = TraceContextTextMapPropagator()
        propagator.inject(headers)
        return headers
    
    def extract_trace_context(self, headers: Dict[str, str]) -> Any:
        """Extract trace context from headers"""
        propagator = TraceContextTextMapPropagator()
        return propagator.extract(headers)
    
    async def correlate_user_trace(self, user_id: str, additional_context: Dict[str, Any] = None):
        """Correlate trace with user for better observability"""
        try:
            trace_id = self.get_current_trace_id()
            if not trace_id:
                return
            
            current_user_id.set(user_id)
            
            # Store correlation
            correlation_data = {
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "service": self.config.service_name,
                **(additional_context or {})
            }
            
            self.trace_correlations[trace_id].update(correlation_data)
            
            # Store in Redis for persistence
            await redis_client.setex(
                f"trace_correlation:{trace_id}",
                3600,  # 1 hour
                json.dumps(correlation_data)
            )
            
        except Exception as e:
            logger.error(f"Failed to correlate user trace: {e}")
    
    def create_child_span(self, parent_span: Any, operation_name: str, **attributes) -> Any:
        """Create child span"""
        if not parent_span:
            return self.start_span(operation_name, **attributes)
        
        with trace.use_span(parent_span):
            child_span = self.tracer.start_span(operation_name)
            
            # Set attributes
            for key, value in attributes.items():
                child_span.set_attribute(key, str(value))
            
            return child_span
    
    async def trace_database_query(self, query: str, parameters: Any = None):
        """Trace database query execution"""
        async with self.trace_context("db.query") as span:
            span.set_attribute("db.statement", query[:1000])  # Limit query length
            span.set_attribute("db.type", "postgresql")
            
            if parameters:
                span.set_attribute("db.parameters", str(parameters)[:500])
            
            yield span
    
    async def trace_redis_operation(self, operation: str, key: str = None):
        """Trace Redis operation"""
        async with self.trace_context("redis.operation") as span:
            span.set_attribute("redis.operation", operation)
            if key:
                span.set_attribute("redis.key", key)
            
            yield span
    
    async def trace_http_request(self, method: str, url: str, **attributes):
        """Trace HTTP request"""
        async with self.trace_context("http.request") as span:
            span.set_attribute("http.method", method)
            span.set_attribute("http.url", url)
            span.set_attribute("http.scheme", "https")
            
            for key, value in attributes.items():
                span.set_attribute(f"http.{key}", str(value))
            
            yield span
    
    def get_trace_statistics(self) -> Dict[str, Any]:
        """Get tracing statistics"""
        active_traces = len(set(span.trace_id for span in self.active_spans.values()))
        
        # Calculate average span duration
        recent_spans = [s for s in self.span_metrics if s.duration_ms is not None]
        avg_duration = sum(s.duration_ms for s in recent_spans) / len(recent_spans) if recent_spans else 0
        
        return {
            "total_traces": self.trace_stats["total_traces"],
            "total_spans": self.trace_stats["total_spans"],
            "active_traces": active_traces,
            "active_spans": len(self.active_spans),
            "error_spans": self.trace_stats["error_spans"],
            "slow_spans": self.trace_stats["slow_spans"],
            "average_span_duration_ms": round(avg_duration, 2),
            "error_rate": (
                self.trace_stats["error_spans"] / self.trace_stats["total_spans"] * 100
                if self.trace_stats["total_spans"] > 0 else 0
            ),
            "service_name": self.config.service_name,
            "environment": self.config.environment
        }
    
    async def get_trace_details(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific trace"""
        try:
            # Get correlation data
            correlation_data = await redis_client.get(f"trace_correlation:{trace_id}")
            if correlation_data:
                correlation = json.loads(correlation_data)
            else:
                correlation = self.trace_correlations.get(trace_id, {})
            
            # Get spans for this trace
            trace_spans = [s for s in self.span_metrics if s.trace_id == trace_id]
            
            if not trace_spans:
                return None
            
            return {
                "trace_id": trace_id,
                "correlation": correlation,
                "span_count": len(trace_spans),
                "total_duration_ms": sum(s.duration_ms or 0 for s in trace_spans),
                "spans": [asdict(span) for span in trace_spans],
                "service_name": self.config.service_name
            }
            
        except Exception as e:
            logger.error(f"Failed to get trace details: {e}")
            return None

# Decorators for automatic tracing
def trace_function(operation_name: str = None, **span_attributes):
    """Decorator to automatically trace function execution"""
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            async with distributed_tracer.trace_context(op_name, **span_attributes) as span:
                # Add function details
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                result = await func(*args, **kwargs)
                
                # Add result info if it's serializable
                try:
                    if hasattr(result, '__dict__'):
                        span.set_attribute("function.result.type", type(result).__name__)
                except:
                    pass
                
                return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            with distributed_tracer.tracer.start_as_current_span(op_name) as span:
                # Add function details
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                for key, value in span_attributes.items():
                    span.set_attribute(key, str(value))
                
                try:
                    result = func(*args, **kwargs)
                    
                    # Add result info
                    if hasattr(result, '__dict__'):
                        span.set_attribute("function.result.type", type(result).__name__)
                    
                    return result
                    
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

def trace_class(class_name: str = None):
    """Decorator to automatically trace all methods in a class"""
    def decorator(cls):
        if class_name:
            cls._trace_name = class_name
        else:
            cls._trace_name = cls.__name__
        
        # Wrap all public methods
        for attr_name in dir(cls):
            if not attr_name.startswith('_'):
                attr = getattr(cls, attr_name)
                if callable(attr):
                    setattr(cls, attr_name, trace_function(f"{cls._trace_name}.{attr_name}")(attr))
        
        return cls
    return decorator

# Configuration based on environment
def get_trace_config() -> TraceConfiguration:
    """Get tracing configuration based on environment"""
    environment = getattr(settings, 'ENVIRONMENT', 'development')
    
    if environment == 'production':
        return TraceConfiguration(
            service_name="quest-edu-backend",
            service_version=getattr(settings, 'VERSION', '1.0.0'),
            environment=environment,
            enable_jaeger=True,
            jaeger_endpoint=getattr(settings, 'JAEGER_ENDPOINT', 'http://jaeger:14268/api/traces'),
            enable_console=False,
            sampling_rate=0.1,  # 10% sampling in production
            enable_custom_attributes=True,
            enable_db_query_tracing=True,
            enable_redis_tracing=True,
            enable_http_tracing=True
        )
    elif environment == 'staging':
        return TraceConfiguration(
            service_name="quest-edu-backend-staging",
            environment=environment,
            enable_jaeger=True,
            jaeger_endpoint=getattr(settings, 'JAEGER_ENDPOINT', 'http://jaeger:14268/api/traces'),
            enable_console=True,
            sampling_rate=0.5,  # 50% sampling in staging
            enable_custom_attributes=True
        )
    else:
        return TraceConfiguration(
            service_name="quest-edu-backend-dev",
            environment=environment,
            enable_jaeger=True,
            jaeger_endpoint=getattr(settings, 'JAEGER_ENDPOINT', 'http://localhost:14268/api/traces'),
            enable_console=True,
            sampling_rate=1.0,  # 100% sampling in development
            enable_custom_attributes=True
        )

# Global distributed tracer instance
trace_config = get_trace_config()
distributed_tracer = DistributedTracer(trace_config)

# Utility functions
async def start_trace(operation_name: str, **attributes) -> Any:
    """Start a new trace"""
    return distributed_tracer.start_span(operation_name, **attributes)

def get_trace_id() -> Optional[str]:
    """Get current trace ID"""
    return distributed_tracer.get_current_trace_id()

def get_span_id() -> Optional[str]:
    """Get current span ID"""
    return distributed_tracer.get_current_span_id()

async def correlate_user(user_id: str, **context):
    """Correlate current trace with user"""
    await distributed_tracer.correlate_user_trace(user_id, context)

@asynccontextmanager
async def trace_operation(operation_name: str, **attributes):
    """Context manager for tracing operations"""
    async with distributed_tracer.trace_context(operation_name, **attributes) as span:
        yield span