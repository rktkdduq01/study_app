"""
User Experience Monitoring API Endpoints
REST API for user experience tracking, analytics, and insights
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query, HTTPException, Depends, Body
from pydantic import BaseModel, Field

from app.core.logger import get_logger
from app.core.user_experience_monitor import (
    ux_monitor, InteractionType, DeviceType, BrowserType,
    UserInteraction, PerformanceMetrics, UXScorecard,
    start_user_session, end_user_session, track_user_interaction,
    track_web_performance, track_user_conversion
)

logger = get_logger(__name__)

# Pydantic models
class SessionStartRequest(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    user_agent: str = ""
    ip_address: str = ""

class InteractionRequest(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    interaction_type: str = Field(..., regex="^(page_view|click|form_submit|search|download|upload|login|logout|error|custom)$")
    page_url: str
    element_id: Optional[str] = None
    element_text: Optional[str] = None
    coordinates: Optional[Dict[str, int]] = None
    duration: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class PerformanceRequest(BaseModel):
    session_id: str
    page_url: str
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

class ConversionRequest(BaseModel):
    session_id: str
    funnel_name: str
    step: str
    value: float = 0.0

# Create router
router = APIRouter(prefix="/ux", tags=["User Experience"])

@router.post("/session/start")
async def start_session(request: SessionStartRequest):
    """Start a new user session"""
    try:
        success = await start_user_session(
            session_id=request.session_id,
            user_id=request.user_id,
            user_agent=request.user_agent,
            ip_address=request.ip_address
        )
        
        if success:
            return {
                "status": "success",
                "message": "Session started",
                "session_id": request.session_id
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to start session")
            
    except Exception as e:
        logger.error(f"Failed to start session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/session/end")
async def end_session(session_id: str = Body(..., embed=True)):
    """End a user session"""
    try:
        success = await end_user_session(session_id)
        
        if success:
            return {
                "status": "success",
                "message": "Session ended",
                "session_id": session_id
            }
        else:
            raise HTTPException(status_code=404, detail="Session not found")
            
    except Exception as e:
        logger.error(f"Failed to end session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/interaction")
async def track_interaction(request: InteractionRequest):
    """Track user interaction"""
    try:
        interaction = UserInteraction(
            interaction_id=f"{request.session_id}_{int(datetime.utcnow().timestamp() * 1000)}",
            session_id=request.session_id,
            user_id=request.user_id,
            timestamp=datetime.utcnow(),
            interaction_type=InteractionType(request.interaction_type),
            page_url=request.page_url,
            element_id=request.element_id,
            element_text=request.element_text,
            coordinates=request.coordinates,
            duration=request.duration,
            success=request.success,
            error_message=request.error_message,
            metadata=request.metadata or {}
        )
        
        success = await track_user_interaction(interaction)
        
        if success:
            return {
                "status": "success",
                "message": "Interaction tracked",
                "interaction_id": interaction.interaction_id
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to track interaction")
            
    except Exception as e:
        logger.error(f"Failed to track interaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/performance")
async def track_performance(request: PerformanceRequest):
    """Track web performance metrics"""
    try:
        performance = PerformanceMetrics(
            session_id=request.session_id,
            page_url=request.page_url,
            timestamp=datetime.utcnow(),
            dns_lookup_time=request.dns_lookup_time,
            tcp_connect_time=request.tcp_connect_time,
            request_time=request.request_time,
            response_time=request.response_time,
            dom_ready_time=request.dom_ready_time,
            page_load_time=request.page_load_time,
            first_contentful_paint=request.first_contentful_paint,
            largest_contentful_paint=request.largest_contentful_paint,
            cumulative_layout_shift=request.cumulative_layout_shift,
            first_input_delay=request.first_input_delay,
            time_to_interactive=request.time_to_interactive
        )
        
        success = await track_web_performance(performance)
        
        if success:
            return {
                "status": "success",
                "message": "Performance metrics tracked"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to track performance")
            
    except Exception as e:
        logger.error(f"Failed to track performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/conversion")
async def track_conversion(request: ConversionRequest):
    """Track conversion funnel progress"""
    try:
        success = await track_user_conversion(
            session_id=request.session_id,
            funnel_name=request.funnel_name,
            step=request.step,
            value=request.value
        )
        
        if success:
            return {
                "status": "success",
                "message": "Conversion tracked",
                "funnel": request.funnel_name,
                "step": request.step
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to track conversion")
            
    except Exception as e:
        logger.error(f"Failed to track conversion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard")
async def get_ux_dashboard():
    """Get comprehensive UX dashboard data"""
    try:
        # Get real-time metrics
        real_time_metrics = ux_monitor.get_real_time_metrics()
        
        # Get scorecards for different periods
        scorecard_1h = await ux_monitor.get_ux_scorecard("1h")
        scorecard_24h = await ux_monitor.get_ux_scorecard("24h")
        scorecard_7d = await ux_monitor.get_ux_scorecard("7d")
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "real_time": real_time_metrics,
            "scorecards": {
                "1h": scorecard_1h.__dict__ if scorecard_1h else None,
                "24h": scorecard_24h.__dict__ if scorecard_24h else None,
                "7d": scorecard_7d.__dict__ if scorecard_7d else None
            },
            "active_sessions": ux_monitor.get_active_sessions_count()
        }
        
    except Exception as e:
        logger.error(f"Failed to get UX dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scorecard/{period}")
async def get_scorecard(
    period: str = Query(..., regex="^(1h|24h|7d)$")
):
    """Get UX scorecard for specific period"""
    try:
        scorecard = await ux_monitor.get_ux_scorecard(period)
        
        if not scorecard:
            raise HTTPException(status_code=404, detail=f"Scorecard not available for period: {period}")
        
        return {
            "status": "success",
            "period": period,
            "scorecard": scorecard.__dict__
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get scorecard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/real-time")
async def get_real_time_metrics():
    """Get real-time UX metrics"""
    try:
        metrics = ux_monitor.get_real_time_metrics()
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"Failed to get real-time metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/active")
async def get_active_sessions():
    """Get information about active sessions"""
    try:
        active_count = ux_monitor.get_active_sessions_count()
        
        # Get sample of active sessions (without sensitive data)
        sample_sessions = []
        for session_id, session in list(ux_monitor.active_sessions.items())[:10]:
            sample_sessions.append({
                "session_id": session_id[:8] + "...",  # Truncate for privacy
                "device_type": session.device_type.value,
                "browser_type": session.browser_type.value,
                "start_time": session.start_time.isoformat(),
                "page_views": session.page_views,
                "interactions": session.interactions,
                "country": session.country
            })
        
        return {
            "status": "success",
            "active_sessions_count": active_count,
            "sample_sessions": sample_sessions
        }
        
    except Exception as e:
        logger.error(f"Failed to get active sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/funnel/{funnel_name}")
async def get_funnel_analytics(
    funnel_name: str,
    hours: int = Query(default=24, ge=1, le=168)
):
    """Get conversion funnel analytics"""
    try:
        # This would analyze conversion funnel data
        # For now, return mock data structure
        
        funnel_steps = ux_monitor.conversion_funnels.get(funnel_name, [])
        
        if not funnel_steps:
            raise HTTPException(status_code=404, detail=f"Funnel '{funnel_name}' not found")
        
        # Mock funnel analytics
        analytics = {
            "funnel_name": funnel_name,
            "time_period_hours": hours,
            "steps": [],
            "overall_conversion_rate": 15.5,
            "drop_off_points": []
        }
        
        # Add step analytics
        for i, step in enumerate(funnel_steps):
            step_analytics = {
                "step": step,
                "step_number": i + 1,
                "visitors": 1000 - (i * 200),  # Mock decreasing visitors
                "conversion_rate": 100 - (i * 15),  # Mock decreasing conversion
                "avg_time_on_step": 45 + (i * 20),  # Mock increasing time
                "drop_off_rate": i * 15
            }
            analytics["steps"].append(step_analytics)
        
        return {
            "status": "success",
            "analytics": analytics
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get funnel analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/pages")
async def get_page_analytics(
    hours: int = Query(default=24, ge=1, le=168),
    limit: int = Query(default=20, ge=1, le=100)
):
    """Get page-level analytics"""
    try:
        # This would analyze page performance and interaction data
        # For now, return mock data
        
        pages = [
            {
                "page_url": "/home",
                "page_views": 5432,
                "unique_visitors": 3876,
                "avg_time_on_page": 125.3,
                "bounce_rate": 35.2,
                "avg_load_time": 1.8,
                "interactions": 8765,
                "conversion_rate": 12.4
            },
            {
                "page_url": "/products",
                "page_views": 3210,
                "unique_visitors": 2543,
                "avg_time_on_page": 89.7,
                "bounce_rate": 42.1,
                "avg_load_time": 2.1,
                "interactions": 5432,
                "conversion_rate": 8.9
            },
            {
                "page_url": "/checkout",
                "page_views": 876,
                "unique_visitors": 654,
                "avg_time_on_page": 234.5,
                "bounce_rate": 28.7,
                "avg_load_time": 3.2,
                "interactions": 2109,
                "conversion_rate": 45.6
            }
        ]
        
        return {
            "status": "success",
            "time_period_hours": hours,
            "total_pages": len(pages),
            "pages": pages[:limit]
        }
        
    except Exception as e:
        logger.error(f"Failed to get page analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/devices")
async def get_device_analytics(
    hours: int = Query(default=24, ge=1, le=168)
):
    """Get device and browser analytics"""
    try:
        # This would analyze device/browser distribution from sessions
        # For now, return mock data
        
        device_analytics = {
            "device_distribution": {
                "desktop": {"count": 3456, "percentage": 52.3},
                "mobile": {"count": 2890, "percentage": 43.7},
                "tablet": {"count": 265, "percentage": 4.0}
            },
            "browser_distribution": {
                "chrome": {"count": 4123, "percentage": 62.4},
                "firefox": {"count": 1234, "percentage": 18.7},
                "safari": {"count": 876, "percentage": 13.3},
                "edge": {"count": 432, "percentage": 6.5},
                "other": {"count": 345, "percentage": 5.2}
            },
            "performance_by_device": {
                "desktop": {"avg_load_time": 1.8, "conversion_rate": 15.2},
                "mobile": {"avg_load_time": 3.2, "conversion_rate": 8.9},
                "tablet": {"avg_load_time": 2.5, "conversion_rate": 11.3}
            }
        }
        
        return {
            "status": "success",
            "time_period_hours": hours,
            "analytics": device_analytics
        }
        
    except Exception as e:
        logger.error(f"Failed to get device analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/user-journeys")
async def get_user_journey_analytics(
    hours: int = Query(default=24, ge=1, le=168),
    limit: int = Query(default=50, ge=1, le=200)
):
    """Get user journey analytics"""
    try:
        # Get sample of user journeys (anonymized)
        journeys = []
        
        for journey_id, journey in list(ux_monitor.user_journeys.items())[:limit]:
            journey_data = {
                "journey_id": journey_id[:12] + "...",  # Truncate for privacy
                "path": journey.path,
                "interactions": len(journey.interactions),
                "duration": (
                    (journey.end_time - journey.start_time).total_seconds()
                    if journey.end_time else None
                ),
                "completed": journey.completed,
                "goal_achieved": journey.goal_achieved,
                "dropped_at": journey.dropped_at
            }
            journeys.append(journey_data)
        
        # Calculate common paths
        all_paths = [journey.path for journey in ux_monitor.user_journeys.values() if journey.path]
        common_paths = []
        
        # Simple path analysis (in real implementation, would be more sophisticated)
        if all_paths:
            # Get most common starting pages
            start_pages = [path[0] for path in all_paths if path]
            start_page_counts = {}
            for page in start_pages:
                start_page_counts[page] = start_page_counts.get(page, 0) + 1
            
            common_paths = [
                {"path": [page], "count": count}
                for page, count in sorted(start_page_counts.items(), 
                                        key=lambda x: x[1], reverse=True)[:10]
            ]
        
        return {
            "status": "success",
            "time_period_hours": hours,
            "total_journeys": len(ux_monitor.user_journeys),
            "sample_journeys": journeys,
            "common_paths": common_paths
        }
        
    except Exception as e:
        logger.error(f"Failed to get user journey analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def ux_health_check():
    """Health check for UX monitoring system"""
    try:
        stats = {
            "active_sessions": ux_monitor.get_active_sessions_count(),
            "interaction_buffer_size": len(ux_monitor.interaction_buffer),
            "performance_buffer_size": len(ux_monitor.performance_buffer),
            "user_journeys": len(ux_monitor.user_journeys),
            "background_tasks_running": (
                ux_monitor._processing_task is not None and 
                not ux_monitor._processing_task.done()
            )
        }
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"UX health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }