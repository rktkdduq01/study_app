"""
User Experience Monitoring System
Comprehensive monitoring of user interactions, performance, and satisfaction
"""

import asyncio
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict, field
from collections import defaultdict, deque, Counter
from enum import Enum
import statistics

from app.core.logger import get_logger
from app.core.redis_client import redis_client
from app.core.config import settings
from app.core.distributed_tracing import distributed_tracer, trace_operation
from app.core.metrics_collector import record_metric

logger = get_logger(__name__)

class InteractionType(Enum):
    """Types of user interactions"""
    PAGE_VIEW = "page_view"
    CLICK = "click"
    FORM_SUBMIT = "form_submit"
    SEARCH = "search"
    DOWNLOAD = "download"
    UPLOAD = "upload"
    LOGIN = "login"
    LOGOUT = "logout"
    ERROR = "error"
    CUSTOM = "custom"

class DeviceType(Enum):
    """Device types"""
    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"
    UNKNOWN = "unknown"

class BrowserType(Enum):
    """Browser types"""
    CHROME = "chrome"
    FIREFOX = "firefox"
    SAFARI = "safari"
    EDGE = "edge"
    OTHER = "other"

@dataclass
class UserSession:
    """User session data"""
    session_id: str
    user_id: Optional[str]
    start_time: datetime
    end_time: Optional[datetime] = None
    device_type: DeviceType = DeviceType.UNKNOWN
    browser_type: BrowserType = BrowserType.OTHER
    user_agent: str = ""
    ip_address: str = ""
    country: str = ""
    page_views: int = 0
    interactions: int = 0
    errors: int = 0
    total_time: float = 0.0  # seconds
    bounce: bool = False
    conversion: bool = False
    revenue: float = 0.0

@dataclass
class UserInteraction:
    """Individual user interaction"""
    interaction_id: str
    session_id: str
    user_id: Optional[str]
    timestamp: datetime
    interaction_type: InteractionType
    page_url: str
    element_id: Optional[str] = None
    element_text: Optional[str] = None
    coordinates: Optional[Dict[str, int]] = None
    duration: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PerformanceMetrics:
    """Web performance metrics"""
    session_id: str
    page_url: str
    timestamp: datetime
    dns_lookup_time: Optional[float] = None
    tcp_connect_time: Optional[float] = None
    request_time: Optional[float] = None
    response_time: Optional[float] = None
    dom_ready_time: Optional[float] = None
    page_load_time: Optional[float] = None
    first_contentful_paint: Optional[float] = None
    largest_contentful_paint: Optional[float] = None
    cumulative_layout_shift: Optional[float] = None
    first_input_delay: Optional[float] = None
    time_to_interactive: Optional[float] = None

@dataclass
class UserJourney:
    """User journey through the application"""
    journey_id: str
    user_id: Optional[str]
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    path: List[str] = field(default_factory=list)
    interactions: List[str] = field(default_factory=list)
    conversion_funnel: List[str] = field(default_factory=list)
    dropped_at: Optional[str] = None
    completed: bool = False
    goal_achieved: bool = False

@dataclass
class UXScorecard:
    """User experience scorecard"""
    period: str
    total_sessions: int
    unique_users: int
    avg_session_duration: float
    bounce_rate: float
    conversion_rate: float
    error_rate: float
    page_load_performance: Dict[str, float]
    satisfaction_score: float
    nps_score: Optional[float] = None
    user_segments: Dict[str, Dict[str, Any]] = field(default_factory=dict)

class UserExperienceMonitor:
    """Comprehensive user experience monitoring system"""
    
    def __init__(self):
        self.active_sessions: Dict[str, UserSession] = {}
        self.interaction_buffer: deque = deque(maxlen=50000)
        self.performance_buffer: deque = deque(maxlen=10000)
        self.user_journeys: Dict[str, UserJourney] = {}
        
        # Analytics settings
        self.session_timeout = 1800  # 30 minutes
        self.bounce_threshold = 30  # seconds
        self.slow_page_threshold = 3.0  # seconds
        
        # Conversion funnels
        self.conversion_funnels = {
            "signup": ["landing_page", "signup_form", "email_verification", "profile_setup"],
            "purchase": ["product_page", "add_to_cart", "checkout", "payment", "confirmation"],
            "engagement": ["home_page", "content_view", "interaction", "return_visit"]
        }
        
        # Background tasks
        self._processing_task = None
        self._analysis_task = None
        self._cleanup_task = None
        
        # Real-time analytics
        self.real_time_metrics = {
            "active_users": 0,
            "page_views_per_minute": 0,
            "errors_per_minute": 0,
            "avg_page_load_time": 0.0
        }
        
        self._start_background_tasks()
    
    def _start_background_tasks(self):
        """Start background processing tasks"""
        if self._processing_task is None:
            self._processing_task = asyncio.create_task(self._processing_loop())
        
        if self._analysis_task is None:
            self._analysis_task = asyncio.create_task(self._analysis_loop())
        
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def start_session(self, session_id: str, user_id: Optional[str] = None,
                          user_agent: str = "", ip_address: str = "") -> bool:
        """Start a new user session"""
        try:
            session = UserSession(
                session_id=session_id,
                user_id=user_id,
                start_time=datetime.utcnow(),
                device_type=self._detect_device_type(user_agent),
                browser_type=self._detect_browser_type(user_agent),
                user_agent=user_agent,
                ip_address=ip_address,
                country=self._get_country_from_ip(ip_address)
            )
            
            self.active_sessions[session_id] = session
            
            # Record metrics
            await record_metric("ux_sessions_started", 1.0, {
                "device_type": session.device_type.value,
                "browser_type": session.browser_type.value
            })
            
            logger.info(f"Started UX session: {session_id} for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start session: {e}")
            return False
    
    async def end_session(self, session_id: str) -> bool:
        """End a user session"""
        try:
            if session_id not in self.active_sessions:
                return False
            
            session = self.active_sessions[session_id]
            session.end_time = datetime.utcnow()
            session.total_time = (session.end_time - session.start_time).total_seconds()
            
            # Determine if session was a bounce
            session.bounce = (
                session.total_time < self.bounce_threshold and 
                session.page_views <= 1
            )
            
            # Store session data
            await self._store_session_data(session)
            
            # Record metrics
            await record_metric("ux_sessions_ended", 1.0, {
                "device_type": session.device_type.value,
                "bounce": str(session.bounce)
            })
            
            await record_metric("ux_session_duration", session.total_time, {
                "device_type": session.device_type.value
            })
            
            # Remove from active sessions
            del self.active_sessions[session_id]
            
            logger.info(f"Ended UX session: {session_id}, duration: {session.total_time:.2f}s")
            return True
            
        except Exception as e:
            logger.error(f"Failed to end session: {e}")
            return False
    
    async def track_interaction(self, interaction: UserInteraction) -> bool:
        """Track user interaction"""
        try:
            # Add to buffer
            self.interaction_buffer.append(interaction)
            
            # Update session if exists
            if interaction.session_id in self.active_sessions:
                session = self.active_sessions[interaction.session_id]
                session.interactions += 1
                
                if interaction.interaction_type == InteractionType.PAGE_VIEW:
                    session.page_views += 1
                
                if not interaction.success:
                    session.errors += 1
            
            # Update user journey
            await self._update_user_journey(interaction)
            
            # Record metrics
            await record_metric("ux_interactions_total", 1.0, {
                "type": interaction.interaction_type.value,
                "success": str(interaction.success)
            })
            
            if interaction.duration:
                await record_metric("ux_interaction_duration", interaction.duration, {
                    "type": interaction.interaction_type.value
                })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to track interaction: {e}")
            return False
    
    async def track_performance(self, performance: PerformanceMetrics) -> bool:
        """Track web performance metrics"""
        try:
            # Add to buffer
            self.performance_buffer.append(performance)
            
            # Record key performance metrics
            if performance.page_load_time:
                await record_metric("ux_page_load_time", performance.page_load_time, {
                    "page": self._normalize_url(performance.page_url)
                })
            
            if performance.first_contentful_paint:
                await record_metric("ux_first_contentful_paint", performance.first_contentful_paint, {
                    "page": self._normalize_url(performance.page_url)
                })
            
            if performance.largest_contentful_paint:
                await record_metric("ux_largest_contentful_paint", performance.largest_contentful_paint, {
                    "page": self._normalize_url(performance.page_url)
                })
            
            if performance.cumulative_layout_shift:
                await record_metric("ux_cumulative_layout_shift", performance.cumulative_layout_shift, {
                    "page": self._normalize_url(performance.page_url)
                })
            
            if performance.first_input_delay:
                await record_metric("ux_first_input_delay", performance.first_input_delay, {
                    "page": self._normalize_url(performance.page_url)
                })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to track performance: {e}")
            return False
    
    async def track_conversion(self, session_id: str, funnel_name: str, 
                             step: str, value: float = 0.0) -> bool:
        """Track conversion funnel progress"""
        try:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                
                # Check if this completes a conversion
                if funnel_name in self.conversion_funnels:
                    funnel_steps = self.conversion_funnels[funnel_name]
                    if step == funnel_steps[-1]:  # Last step in funnel
                        session.conversion = True
                        session.revenue += value
                        
                        await record_metric("ux_conversions_total", 1.0, {
                            "funnel": funnel_name,
                            "device_type": session.device_type.value
                        })
                        
                        if value > 0:
                            await record_metric("ux_conversion_value", value, {
                                "funnel": funnel_name
                            })
            
            # Update user journey
            journey_id = f"{session_id}_{funnel_name}"
            if journey_id not in self.user_journeys:
                self.user_journeys[journey_id] = UserJourney(
                    journey_id=journey_id,
                    user_id=self.active_sessions.get(session_id, {}).user_id,
                    session_id=session_id,
                    start_time=datetime.utcnow(),
                    conversion_funnel=self.conversion_funnels.get(funnel_name, [])
                )
            
            journey = self.user_journeys[journey_id]
            if step not in journey.path:
                journey.path.append(step)
            
            # Check if funnel is completed
            if funnel_name in self.conversion_funnels:
                required_steps = self.conversion_funnels[funnel_name]
                if all(req_step in journey.path for req_step in required_steps):
                    journey.completed = True
                    journey.goal_achieved = True
                    journey.end_time = datetime.utcnow()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to track conversion: {e}")
            return False
    
    async def _update_user_journey(self, interaction: UserInteraction):
        """Update user journey based on interaction"""
        try:
            journey_id = f"{interaction.session_id}_main"
            
            if journey_id not in self.user_journeys:
                self.user_journeys[journey_id] = UserJourney(
                    journey_id=journey_id,
                    user_id=interaction.user_id,
                    session_id=interaction.session_id,
                    start_time=interaction.timestamp
                )
            
            journey = self.user_journeys[journey_id]
            
            # Add page to path
            if interaction.interaction_type == InteractionType.PAGE_VIEW:
                page = self._normalize_url(interaction.page_url)
                if not journey.path or journey.path[-1] != page:
                    journey.path.append(page)
            
            # Add interaction
            journey.interactions.append(interaction.interaction_type.value)
            
            # Check for dropoff
            if interaction.interaction_type == InteractionType.ERROR:
                journey.dropped_at = self._normalize_url(interaction.page_url)
            
        except Exception as e:
            logger.error(f"Failed to update user journey: {e}")
    
    def _detect_device_type(self, user_agent: str) -> DeviceType:
        """Detect device type from user agent"""
        user_agent_lower = user_agent.lower()
        
        if any(mobile in user_agent_lower for mobile in ['mobile', 'android', 'iphone']):
            return DeviceType.MOBILE
        elif any(tablet in user_agent_lower for tablet in ['tablet', 'ipad']):
            return DeviceType.TABLET
        elif any(desktop in user_agent_lower for desktop in ['windows', 'macintosh', 'linux']):
            return DeviceType.DESKTOP
        else:
            return DeviceType.UNKNOWN
    
    def _detect_browser_type(self, user_agent: str) -> BrowserType:
        """Detect browser type from user agent"""
        user_agent_lower = user_agent.lower()
        
        if 'chrome' in user_agent_lower:
            return BrowserType.CHROME
        elif 'firefox' in user_agent_lower:
            return BrowserType.FIREFOX
        elif 'safari' in user_agent_lower:
            return BrowserType.SAFARI
        elif 'edge' in user_agent_lower:
            return BrowserType.EDGE
        else:
            return BrowserType.OTHER
    
    def _get_country_from_ip(self, ip_address: str) -> str:
        """Get country from IP address (simplified)"""
        # This would integrate with a GeoIP service
        return "Unknown"
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL for analytics"""
        # Remove query parameters and fragments
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        return f"{parsed.path}" if parsed.path else "/"
    
    async def _store_session_data(self, session: UserSession):
        """Store session data in Redis"""
        try:
            session_data = {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "start_time": session.start_time.isoformat(),
                "end_time": session.end_time.isoformat() if session.end_time else None,
                "device_type": session.device_type.value,
                "browser_type": session.browser_type.value,
                "country": session.country,
                "page_views": session.page_views,
                "interactions": session.interactions,
                "errors": session.errors,
                "total_time": session.total_time,
                "bounce": session.bounce,
                "conversion": session.conversion,
                "revenue": session.revenue
            }
            
            # Store in daily bucket
            date_key = session.start_time.strftime('%Y%m%d')
            key = f"ux_sessions:{date_key}"
            
            await redis_client.lpush(key, json.dumps(session_data))
            await redis_client.expire(key, 86400 * 90)  # Keep for 90 days
            
        except Exception as e:
            logger.error(f"Failed to store session data: {e}")
    
    async def _processing_loop(self):
        """Background processing loop"""
        while True:
            try:
                await asyncio.sleep(60)  # Process every minute
                await self._process_interactions()
                await self._process_performance_data()
                await self._update_real_time_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"UX processing error: {e}")
    
    async def _process_interactions(self):
        """Process interaction buffer"""
        try:
            if not self.interaction_buffer:
                return
            
            # Get batch of interactions
            batch = []
            for _ in range(min(1000, len(self.interaction_buffer))):
                if self.interaction_buffer:
                    batch.append(self.interaction_buffer.popleft())
            
            if not batch:
                return
            
            # Store in Redis
            for interaction in batch:
                interaction_data = {
                    "interaction_id": interaction.interaction_id,
                    "session_id": interaction.session_id,
                    "user_id": interaction.user_id,
                    "timestamp": interaction.timestamp.isoformat(),
                    "type": interaction.interaction_type.value,
                    "page_url": interaction.page_url,
                    "element_id": interaction.element_id,
                    "element_text": interaction.element_text,
                    "coordinates": interaction.coordinates,
                    "duration": interaction.duration,
                    "success": interaction.success,
                    "error_message": interaction.error_message,
                    "metadata": interaction.metadata
                }
                
                # Store in hourly bucket
                hour_key = interaction.timestamp.strftime('%Y%m%d_%H')
                key = f"ux_interactions:{hour_key}"
                
                await redis_client.lpush(key, json.dumps(interaction_data))
                await redis_client.expire(key, 86400 * 30)  # Keep for 30 days
            
            logger.debug(f"Processed {len(batch)} interactions")
            
        except Exception as e:
            logger.error(f"Failed to process interactions: {e}")
    
    async def _process_performance_data(self):
        """Process performance data buffer"""
        try:
            if not self.performance_buffer:
                return
            
            # Get batch of performance data
            batch = []
            for _ in range(min(500, len(self.performance_buffer))):
                if self.performance_buffer:
                    batch.append(self.performance_buffer.popleft())
            
            if not batch:
                return
            
            # Store in Redis
            for performance in batch:
                perf_data = {
                    "session_id": performance.session_id,
                    "page_url": performance.page_url,
                    "timestamp": performance.timestamp.isoformat(),
                    "dns_lookup_time": performance.dns_lookup_time,
                    "tcp_connect_time": performance.tcp_connect_time,
                    "request_time": performance.request_time,
                    "response_time": performance.response_time,
                    "dom_ready_time": performance.dom_ready_time,
                    "page_load_time": performance.page_load_time,
                    "first_contentful_paint": performance.first_contentful_paint,
                    "largest_contentful_paint": performance.largest_contentful_paint,
                    "cumulative_layout_shift": performance.cumulative_layout_shift,
                    "first_input_delay": performance.first_input_delay,
                    "time_to_interactive": performance.time_to_interactive
                }
                
                # Store in hourly bucket
                hour_key = performance.timestamp.strftime('%Y%m%d_%H')
                key = f"ux_performance:{hour_key}"
                
                await redis_client.lpush(key, json.dumps(perf_data))
                await redis_client.expire(key, 86400 * 30)  # Keep for 30 days
            
            logger.debug(f"Processed {len(batch)} performance records")
            
        except Exception as e:
            logger.error(f"Failed to process performance data: {e}")
    
    async def _update_real_time_metrics(self):
        """Update real-time metrics"""
        try:
            # Active users
            self.real_time_metrics["active_users"] = len(self.active_sessions)
            
            # Page views per minute (from last minute's interactions)
            current_minute = datetime.utcnow().replace(second=0, microsecond=0)
            minute_interactions = [
                i for i in self.interaction_buffer
                if (i.timestamp >= current_minute and 
                    i.interaction_type == InteractionType.PAGE_VIEW)
            ]
            self.real_time_metrics["page_views_per_minute"] = len(minute_interactions)
            
            # Errors per minute
            minute_errors = [
                i for i in self.interaction_buffer
                if (i.timestamp >= current_minute and not i.success)
            ]
            self.real_time_metrics["errors_per_minute"] = len(minute_errors)
            
            # Average page load time (from last 10 minutes)
            ten_minutes_ago = datetime.utcnow() - timedelta(minutes=10)
            recent_performance = [
                p for p in self.performance_buffer
                if (p.timestamp >= ten_minutes_ago and p.page_load_time)
            ]
            
            if recent_performance:
                avg_load_time = statistics.mean(p.page_load_time for p in recent_performance)
                self.real_time_metrics["avg_page_load_time"] = avg_load_time
            
            # Record real-time metrics
            await record_metric("ux_active_users", self.real_time_metrics["active_users"])
            await record_metric("ux_page_views_per_minute", self.real_time_metrics["page_views_per_minute"])
            await record_metric("ux_errors_per_minute", self.real_time_metrics["errors_per_minute"])
            await record_metric("ux_avg_page_load_time", self.real_time_metrics["avg_page_load_time"])
            
        except Exception as e:
            logger.error(f"Failed to update real-time metrics: {e}")
    
    async def _analysis_loop(self):
        """Background analysis loop"""
        while True:
            try:
                await asyncio.sleep(3600)  # Analyze every hour
                await self._perform_ux_analysis()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"UX analysis error: {e}")
    
    async def _perform_ux_analysis(self):
        """Perform UX analysis"""
        try:
            # Generate scorecards for different periods
            periods = ["1h", "24h", "7d"]
            
            for period in periods:
                scorecard = await self._generate_ux_scorecard(period)
                
                # Store scorecard
                key = f"ux_scorecard:{period}:{datetime.utcnow().strftime('%Y%m%d_%H')}"
                await redis_client.setex(key, 86400, json.dumps(asdict(scorecard)))
                
        except Exception as e:
            logger.error(f"UX analysis failed: {e}")
    
    async def _generate_ux_scorecard(self, period: str) -> UXScorecard:
        """Generate UX scorecard for period"""
        try:
            # Calculate time range
            if period == "1h":
                time_delta = timedelta(hours=1)
            elif period == "24h":
                time_delta = timedelta(hours=24)
            elif period == "7d":
                time_delta = timedelta(days=7)
            else:
                time_delta = timedelta(hours=24)
            
            end_time = datetime.utcnow()
            start_time = end_time - time_delta
            
            # Collect session data
            sessions = await self._get_sessions_in_range(start_time, end_time)
            
            if not sessions:
                return UXScorecard(
                    period=period,
                    total_sessions=0,
                    unique_users=0,
                    avg_session_duration=0,
                    bounce_rate=0,
                    conversion_rate=0,
                    error_rate=0,
                    page_load_performance={},
                    satisfaction_score=0
                )
            
            # Calculate metrics
            total_sessions = len(sessions)
            unique_users = len(set(s.get("user_id") for s in sessions if s.get("user_id")))
            
            durations = [s.get("total_time", 0) for s in sessions]
            avg_session_duration = statistics.mean(durations) if durations else 0
            
            bounces = sum(1 for s in sessions if s.get("bounce", False))
            bounce_rate = (bounces / total_sessions) * 100 if total_sessions > 0 else 0
            
            conversions = sum(1 for s in sessions if s.get("conversion", False))
            conversion_rate = (conversions / total_sessions) * 100 if total_sessions > 0 else 0
            
            total_interactions = sum(s.get("interactions", 0) for s in sessions)
            total_errors = sum(s.get("errors", 0) for s in sessions)
            error_rate = (total_errors / total_interactions) * 100 if total_interactions > 0 else 0
            
            # Get performance data
            performance_data = await self._get_performance_in_range(start_time, end_time)
            page_load_performance = self._calculate_performance_metrics(performance_data)
            
            # Calculate satisfaction score (0-100)
            satisfaction_score = self._calculate_satisfaction_score(
                bounce_rate, conversion_rate, error_rate, 
                page_load_performance.get("avg_page_load_time", 0)
            )
            
            # Segment users
            user_segments = self._segment_users(sessions)
            
            return UXScorecard(
                period=period,
                total_sessions=total_sessions,
                unique_users=unique_users,
                avg_session_duration=avg_session_duration,
                bounce_rate=bounce_rate,
                conversion_rate=conversion_rate,
                error_rate=error_rate,
                page_load_performance=page_load_performance,
                satisfaction_score=satisfaction_score,
                user_segments=user_segments
            )
            
        except Exception as e:
            logger.error(f"Failed to generate UX scorecard: {e}")
            return UXScorecard(
                period=period, total_sessions=0, unique_users=0,
                avg_session_duration=0, bounce_rate=0, conversion_rate=0,
                error_rate=0, page_load_performance={}, satisfaction_score=0
            )
    
    async def _get_sessions_in_range(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Get sessions in time range"""
        try:
            sessions = []
            current_date = start_time.date()
            end_date = end_time.date()
            
            while current_date <= end_date:
                date_key = current_date.strftime('%Y%m%d')
                key = f"ux_sessions:{date_key}"
                
                session_data = await redis_client.lrange(key, 0, -1)
                
                for data in session_data:
                    try:
                        session = json.loads(data)
                        session_time = datetime.fromisoformat(session["start_time"])
                        
                        if start_time <= session_time <= end_time:
                            sessions.append(session)
                    except (json.JSONDecodeError, ValueError):
                        continue
                
                current_date += timedelta(days=1)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to get sessions: {e}")
            return []
    
    async def _get_performance_in_range(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Get performance data in time range"""
        try:
            performance_data = []
            current_time = start_time
            
            while current_time <= end_time:
                hour_key = current_time.strftime('%Y%m%d_%H')
                key = f"ux_performance:{hour_key}"
                
                perf_data = await redis_client.lrange(key, 0, -1)
                
                for data in perf_data:
                    try:
                        perf = json.loads(data)
                        perf_time = datetime.fromisoformat(perf["timestamp"])
                        
                        if start_time <= perf_time <= end_time:
                            performance_data.append(perf)
                    except (json.JSONDecodeError, ValueError):
                        continue
                
                current_time += timedelta(hours=1)
            
            return performance_data
            
        except Exception as e:
            logger.error(f"Failed to get performance data: {e}")
            return []
    
    def _calculate_performance_metrics(self, performance_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate aggregated performance metrics"""
        try:
            if not performance_data:
                return {}
            
            metrics = {}
            
            # Page load times
            load_times = [p.get("page_load_time") for p in performance_data if p.get("page_load_time")]
            if load_times:
                metrics["avg_page_load_time"] = statistics.mean(load_times)
                metrics["p95_page_load_time"] = sorted(load_times)[int(len(load_times) * 0.95)]
            
            # First Contentful Paint
            fcp_times = [p.get("first_contentful_paint") for p in performance_data if p.get("first_contentful_paint")]
            if fcp_times:
                metrics["avg_first_contentful_paint"] = statistics.mean(fcp_times)
            
            # Largest Contentful Paint
            lcp_times = [p.get("largest_contentful_paint") for p in performance_data if p.get("largest_contentful_paint")]
            if lcp_times:
                metrics["avg_largest_contentful_paint"] = statistics.mean(lcp_times)
            
            # Cumulative Layout Shift
            cls_values = [p.get("cumulative_layout_shift") for p in performance_data if p.get("cumulative_layout_shift")]
            if cls_values:
                metrics["avg_cumulative_layout_shift"] = statistics.mean(cls_values)
            
            # First Input Delay
            fid_times = [p.get("first_input_delay") for p in performance_data if p.get("first_input_delay")]
            if fid_times:
                metrics["avg_first_input_delay"] = statistics.mean(fid_times)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to calculate performance metrics: {e}")
            return {}
    
    def _calculate_satisfaction_score(self, bounce_rate: float, conversion_rate: float,
                                    error_rate: float, avg_page_load_time: float) -> float:
        """Calculate overall satisfaction score (0-100)"""
        try:
            # Start with 100 and deduct points for poor metrics
            score = 100.0
            
            # Deduct for high bounce rate
            if bounce_rate > 70:
                score -= 30
            elif bounce_rate > 50:
                score -= 20
            elif bounce_rate > 30:
                score -= 10
            
            # Deduct for low conversion rate
            if conversion_rate < 1:
                score -= 20
            elif conversion_rate < 3:
                score -= 10
            elif conversion_rate < 5:
                score -= 5
            
            # Deduct for high error rate
            if error_rate > 5:
                score -= 25
            elif error_rate > 2:
                score -= 15
            elif error_rate > 1:
                score -= 10
            
            # Deduct for slow page load times
            if avg_page_load_time > 5:
                score -= 25
            elif avg_page_load_time > 3:
                score -= 15
            elif avg_page_load_time > 2:
                score -= 10
            
            return max(0, score)
            
        except Exception as e:
            logger.error(f"Failed to calculate satisfaction score: {e}")
            return 0.0
    
    def _segment_users(self, sessions: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Segment users based on behavior"""
        try:
            segments = {
                "new_users": {"count": 0, "sessions": []},
                "returning_users": {"count": 0, "sessions": []},
                "power_users": {"count": 0, "sessions": []},
                "mobile_users": {"count": 0, "sessions": []},
                "converters": {"count": 0, "sessions": []},
                "bouncers": {"count": 0, "sessions": []}
            }
            
            user_session_counts = Counter(s.get("user_id") for s in sessions if s.get("user_id"))
            
            for session in sessions:
                user_id = session.get("user_id")
                device_type = session.get("device_type")
                bounce = session.get("bounce", False)
                conversion = session.get("conversion", False)
                
                # Segment by user type
                if user_id and user_session_counts[user_id] == 1:
                    segments["new_users"]["count"] += 1
                    segments["new_users"]["sessions"].append(session)
                elif user_id and user_session_counts[user_id] > 1:
                    segments["returning_users"]["count"] += 1
                    segments["returning_users"]["sessions"].append(session)
                
                # Power users (multiple sessions)
                if user_id and user_session_counts[user_id] > 5:
                    segments["power_users"]["count"] += 1
                    segments["power_users"]["sessions"].append(session)
                
                # Mobile users
                if device_type == "mobile":
                    segments["mobile_users"]["count"] += 1
                    segments["mobile_users"]["sessions"].append(session)
                
                # Converters
                if conversion:
                    segments["converters"]["count"] += 1
                    segments["converters"]["sessions"].append(session)
                
                # Bouncers
                if bounce:
                    segments["bouncers"]["count"] += 1
                    segments["bouncers"]["sessions"].append(session)
            
            # Calculate segment statistics
            for segment_name, segment_data in segments.items():
                segment_sessions = segment_data["sessions"]
                if segment_sessions:
                    avg_duration = statistics.mean(s.get("total_time", 0) for s in segment_sessions)
                    avg_page_views = statistics.mean(s.get("page_views", 0) for s in segment_sessions)
                    
                    segment_data["avg_duration"] = avg_duration
                    segment_data["avg_page_views"] = avg_page_views
                    
                    # Remove sessions to reduce payload size
                    del segment_data["sessions"]
            
            return segments
            
        except Exception as e:
            logger.error(f"Failed to segment users: {e}")
            return {}
    
    async def _cleanup_loop(self):
        """Background cleanup loop"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                await self._cleanup_old_data()
                await self._cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"UX cleanup error: {e}")
    
    async def _cleanup_old_data(self):
        """Clean up old UX data"""
        try:
            # This would clean up old Redis keys beyond retention period
            logger.info("Completed UX data cleanup")
        except Exception as e:
            logger.error(f"UX cleanup failed: {e}")
    
    async def _cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        try:
            current_time = datetime.utcnow()
            expired_sessions = []
            
            for session_id, session in self.active_sessions.items():
                # Check if session has been inactive for too long
                time_since_start = (current_time - session.start_time).total_seconds()
                if time_since_start > self.session_timeout:
                    expired_sessions.append(session_id)
            
            # End expired sessions
            for session_id in expired_sessions:
                await self.end_session(session_id)
            
            if expired_sessions:
                logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
                
        except Exception as e:
            logger.error(f"Session cleanup failed: {e}")
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time UX metrics"""
        return self.real_time_metrics.copy()
    
    def get_active_sessions_count(self) -> int:
        """Get count of active sessions"""
        return len(self.active_sessions)
    
    async def get_ux_scorecard(self, period: str = "24h") -> Optional[UXScorecard]:
        """Get UX scorecard for period"""
        try:
            key = f"ux_scorecard:{period}:{datetime.utcnow().strftime('%Y%m%d_%H')}"
            data = await redis_client.get(key)
            
            if data:
                scorecard_data = json.loads(data)
                return UXScorecard(**scorecard_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get UX scorecard: {e}")
            return None

# Global UX monitor instance
ux_monitor = UserExperienceMonitor()

# Utility functions
async def start_user_session(session_id: str, user_id: Optional[str] = None,
                           user_agent: str = "", ip_address: str = "") -> bool:
    """Start user session"""
    return await ux_monitor.start_session(session_id, user_id, user_agent, ip_address)

async def end_user_session(session_id: str) -> bool:
    """End user session"""
    return await ux_monitor.end_session(session_id)

async def track_user_interaction(interaction: UserInteraction) -> bool:
    """Track user interaction"""
    return await ux_monitor.track_interaction(interaction)

async def track_web_performance(performance: PerformanceMetrics) -> bool:
    """Track web performance"""
    return await ux_monitor.track_performance(performance)

async def track_user_conversion(session_id: str, funnel_name: str, 
                              step: str, value: float = 0.0) -> bool:
    """Track conversion"""
    return await ux_monitor.track_conversion(session_id, funnel_name, step, value)