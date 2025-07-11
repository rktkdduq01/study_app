from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from pydantic import BaseModel

from ...database import get_db
from ...core.auth import get_current_user
from ...models.user import User
from ...services.analytics_service import analytics_service

router = APIRouter()

class TrackEventRequest(BaseModel):
    event_name: str
    event_category: str
    session_id: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None

class ActivityTrackRequest(BaseModel):
    activity_type: str
    activity_data: Optional[Dict[str, Any]] = None
    duration_seconds: Optional[int] = 0

class LearningProgressRequest(BaseModel):
    subject_id: int
    content_id: Optional[int] = None
    quest_id: Optional[int] = None
    progress_percentage: float
    time_spent: int
    score: Optional[float] = None
    completed: bool = False

class DateRangeQuery(BaseModel):
    start_date: datetime
    end_date: datetime

@router.post("/track/event")
async def track_event(
    request: TrackEventRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Track a custom analytics event"""
    event = await analytics_service.track_event(
        event_name=request.event_name,
        event_category=request.event_category,
        user_id=current_user.id,
        session_id=request.session_id,
        properties=request.properties,
        db=db
    )
    
    # Calculate metrics in background
    background_tasks.add_task(
        analytics_service.calculate_performance_metrics,
        current_user.id,
        "daily",
        db
    )
    
    return {
        "status": "success",
        "event_id": event.id,
        "message": "Event tracked successfully"
    }

@router.post("/track/activity")
async def track_activity(
    request: ActivityTrackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Track user activity"""
    activity = await analytics_service.track_user_activity(
        user_id=current_user.id,
        activity_type=request.activity_type,
        activity_data=request.activity_data,
        duration_seconds=request.duration_seconds,
        db=db
    )
    
    return {
        "status": "success",
        "activity_id": activity.id,
        "message": "Activity tracked successfully"
    }

@router.post("/track/progress")
async def track_learning_progress(
    request: LearningProgressRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Track learning progress"""
    progress = await analytics_service.update_learning_progress(
        user_id=current_user.id,
        subject_id=request.subject_id,
        content_id=request.content_id,
        quest_id=request.quest_id,
        progress_percentage=request.progress_percentage,
        time_spent=request.time_spent,
        score=request.score,
        completed=request.completed,
        db=db
    )
    
    return {
        "status": "success",
        "progress_id": progress.id,
        "message": "Progress tracked successfully"
    }

@router.get("/user/me")
async def get_my_analytics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's analytics"""
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()
    
    analytics = await analytics_service.get_user_analytics(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        db=db
    )
    
    return analytics

@router.get("/user/{user_id}")
async def get_user_analytics(
    user_id: int,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get analytics for a specific user (admin/teacher only)"""
    # Check permissions
    if current_user.role not in ["admin", "teacher"]:
        if current_user.id != user_id:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to view this user's analytics"
            )
    
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()
    
    analytics = await analytics_service.get_user_analytics(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        db=db
    )
    
    return analytics

@router.get("/content/{content_id}/effectiveness")
async def get_content_effectiveness(
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get content effectiveness metrics"""
    effectiveness = await analytics_service.get_content_effectiveness(
        content_id=content_id,
        db=db
    )
    
    return effectiveness

@router.get("/global")
async def get_global_analytics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get platform-wide analytics (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()
    
    analytics = await analytics_service.get_global_analytics(
        start_date=start_date,
        end_date=end_date,
        db=db
    )
    
    return analytics

@router.get("/real-time")
async def get_real_time_analytics(
    current_user: User = Depends(get_current_user)
):
    """Get real-time analytics data"""
    if current_user.role not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=403,
            detail="Admin or teacher access required"
        )
    
    metrics = await analytics_service.get_real_time_metrics()
    return metrics

@router.post("/report/generate")
async def generate_report(
    report_type: str = Query(..., description="Type of report: user, global, content"),
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    filters: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate analytics report"""
    if current_user.role not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=403,
            detail="Admin or teacher access required"
        )
    
    report = await analytics_service.generate_report(
        report_type=report_type,
        start_date=start_date,
        end_date=end_date,
        filters=filters,
        db=db
    )
    
    return report

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard summary data"""
    # Different data based on role
    if current_user.role == "admin":
        # Admin sees global metrics
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # Get various time ranges
        today_analytics = await analytics_service.get_global_analytics(
            today, datetime.utcnow(), db
        )
        week_analytics = await analytics_service.get_global_analytics(
            week_ago, datetime.utcnow(), db
        )
        month_analytics = await analytics_service.get_global_analytics(
            month_ago, datetime.utcnow(), db
        )
        
        return {
            "role": "admin",
            "today": today_analytics,
            "week": week_analytics,
            "month": month_analytics,
            "real_time": await analytics_service.get_real_time_metrics()
        }
        
    elif current_user.role == "teacher":
        # Teacher sees their students' metrics
        # TODO: Implement teacher-specific analytics
        return {
            "role": "teacher",
            "message": "Teacher analytics coming soon"
        }
        
    else:
        # Students see their own metrics
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = today - timedelta(days=7)
        
        user_analytics = await analytics_service.get_user_analytics(
            current_user.id, week_ago, datetime.utcnow(), db
        )
        
        return {
            "role": "student",
            "analytics": user_analytics
        }

@router.get("/leaderboard")
async def get_leaderboard(
    metric: str = Query("xp", description="Metric to rank by: xp, quests, achievements"),
    period: str = Query("all", description="Time period: today, week, month, all"),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get leaderboard rankings"""
    # Determine date range
    end_date = datetime.utcnow()
    if period == "today":
        start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start_date = end_date - timedelta(days=7)
    elif period == "month":
        start_date = end_date - timedelta(days=30)
    else:
        start_date = datetime(2000, 1, 1)  # All time
    
    # Query based on metric
    # This is a simplified example - in production, you'd want to optimize these queries
    from ...models.character import Character
    from sqlalchemy import desc
    
    if metric == "xp":
        rankings = db.query(
            Character.user_id,
            Character.level,
            Character.experience,
            User.username
        ).join(
            User, User.id == Character.user_id
        ).order_by(
            desc(Character.level),
            desc(Character.experience)
        ).limit(limit).all()
        
        leaderboard = [
            {
                "rank": idx + 1,
                "user_id": r.user_id,
                "username": r.username,
                "level": r.level,
                "experience": r.experience,
                "is_current_user": r.user_id == current_user.id
            }
            for idx, r in enumerate(rankings)
        ]
    else:
        # Placeholder for other metrics
        leaderboard = []
    
    # Find current user's rank
    user_rank = None
    if current_user.id not in [entry["user_id"] for entry in leaderboard]:
        # Calculate user's rank if not in top N
        character = db.query(Character).filter(
            Character.user_id == current_user.id
        ).first()
        
        if character:
            higher_ranked = db.query(Character).filter(
                (Character.level > character.level) |
                ((Character.level == character.level) & 
                 (Character.experience > character.experience))
            ).count()
            
            user_rank = {
                "rank": higher_ranked + 1,
                "user_id": current_user.id,
                "username": current_user.username,
                "level": character.level,
                "experience": character.experience,
                "is_current_user": True
            }
    
    return {
        "metric": metric,
        "period": period,
        "leaderboard": leaderboard,
        "current_user_rank": user_rank
    }

@router.get("/export")
async def export_analytics(
    format: str = Query("csv", description="Export format: csv, excel, json"),
    report_type: str = Query(...),
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export analytics data"""
    if current_user.role not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=403,
            detail="Admin or teacher access required"
        )
    
    # Generate report
    report = await analytics_service.generate_report(
        report_type=report_type,
        start_date=start_date,
        end_date=end_date,
        filters={"user_id": current_user.id} if report_type == "user" else None,
        db=db
    )
    
    # Format based on requested type
    if format == "json":
        return report
    elif format == "csv":
        # Convert to CSV format
        # This is a simplified example
        import csv
        import io
        from fastapi.responses import StreamingResponse
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers and data based on report type
        if report_type == "user" and "learning_progress" in report.get("data", {}):
            writer.writerow(["Date", "Subject", "Progress", "Score", "Time Spent"])
            # Add data rows...
        
        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=analytics_{report_type}_{datetime.utcnow().date()}.csv"}
        )
    
    return {"error": "Unsupported format"}