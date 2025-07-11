"""
Family API Endpoints
API endpoints for parent-child monitoring, quest management, and reporting
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.logger import get_logger
from app.core.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.family import (
    Family, FamilyMember, ParentQuest, FamilyReport,
    FamilyRole, RelationshipStatus, NotificationPreference
)
from app.schemas.family import (
    FamilyCreate, FamilyResponse, FamilyMemberInvite,
    ParentQuestCreate, ParentQuestUpdate, ParentQuestResponse,
    ReportGenerationRequest, FamilyReportResponse,
    MonitoringDashboardResponse, ActivityUpdate
)
from app.services.parent_quest_service import ParentQuestService
from app.services.family_report_service import FamilyReportService
from app.core.family_monitoring import get_monitoring_service

logger = get_logger(__name__)

router = APIRouter(prefix="/api/family", tags=["Family"])

# Family Management Endpoints

@router.post("/create", response_model=FamilyResponse)
async def create_family(
    family_data: FamilyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new family group"""
    try:
        # Create family
        family = Family(name=family_data.name, settings=family_data.settings or {})
        db.add(family)
        db.flush()
        
        # Add creator as parent
        member = FamilyMember(
            family_id=family.id,
            user_id=current_user.id,
            role=FamilyRole.PARENT,
            status=RelationshipStatus.ACTIVE,
            can_view_progress=True,
            can_create_quests=True,
            can_set_goals=True,
            can_manage_rewards=True
        )
        db.add(member)
        db.commit()
        
        return FamilyResponse.from_orm(family)
        
    except Exception as e:
        logger.error(f"Failed to create family: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{family_id}/invite")
async def invite_family_member(
    family_id: int,
    invite_data: FamilyMemberInvite,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Invite a user to join the family"""
    try:
        # Verify current user is parent in this family
        parent_member = db.query(FamilyMember).filter(
            FamilyMember.family_id == family_id,
            FamilyMember.user_id == current_user.id,
            FamilyMember.role.in_([FamilyRole.PARENT, FamilyRole.GUARDIAN])
        ).first()
        
        if not parent_member:
            raise HTTPException(status_code=403, detail="Not authorized to invite members")
        
        # Find invited user
        invited_user = db.query(User).filter(User.email == invite_data.email).first()
        if not invited_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if already member
        existing_member = db.query(FamilyMember).filter(
            FamilyMember.family_id == family_id,
            FamilyMember.user_id == invited_user.id
        ).first()
        
        if existing_member:
            raise HTTPException(status_code=400, detail="User is already a family member")
        
        # Create family member
        member = FamilyMember(
            family_id=family_id,
            user_id=invited_user.id,
            role=invite_data.role,
            status=RelationshipStatus.PENDING,
            can_view_progress=invite_data.role == FamilyRole.PARENT,
            can_create_quests=invite_data.role == FamilyRole.PARENT and invite_data.can_create_quests,
            can_set_goals=invite_data.role == FamilyRole.PARENT and invite_data.can_set_goals,
            notification_preference=invite_data.notification_preference
        )
        db.add(member)
        db.commit()
        
        # TODO: Send invitation notification
        
        return {"message": "Invitation sent successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to invite family member: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/my-families", response_model=List[FamilyResponse])
async def get_my_families(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all families the current user belongs to"""
    memberships = db.query(FamilyMember).filter(
        FamilyMember.user_id == current_user.id,
        FamilyMember.status == RelationshipStatus.ACTIVE
    ).all()
    
    families = []
    for membership in memberships:
        family_data = {
            "id": membership.family.id,
            "name": membership.family.name,
            "role": membership.role,
            "member_count": db.query(FamilyMember).filter(
                FamilyMember.family_id == membership.family_id,
                FamilyMember.status == RelationshipStatus.ACTIVE
            ).count()
        }
        families.append(family_data)
    
    return families

# Parent Quest Management

@router.post("/quests/create", response_model=ParentQuestResponse)
async def create_parent_quest(
    quest_data: ParentQuestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a custom quest for a child"""
    try:
        quest_service = ParentQuestService(db)
        quest = quest_service.create_parent_quest(current_user.id, quest_data)
        
        return ParentQuestResponse.from_orm(quest)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create parent quest: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/quests/{quest_id}")
async def update_parent_quest(
    quest_id: int,
    update_data: ParentQuestUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a parent quest"""
    try:
        quest_service = ParentQuestService(db)
        quest = quest_service.update_parent_quest(current_user.id, quest_id, update_data)
        
        return ParentQuestResponse.from_orm(quest)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update parent quest: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/quests/{quest_id}")
async def cancel_parent_quest(
    quest_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a parent quest"""
    try:
        quest_service = ParentQuestService(db)
        success = quest_service.cancel_parent_quest(current_user.id, quest_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Quest not found")
            
        return {"message": "Quest cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel parent quest: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/quests/created", response_model=List[ParentQuestResponse])
async def get_created_quests(
    child_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get quests created by the parent"""
    quest_service = ParentQuestService(db)
    quests = quest_service.get_parent_created_quests(current_user.id, child_id)
    
    if status:
        quests = [q for q in quests if q.status == status]
    
    return [ParentQuestResponse.from_orm(q) for q in quests]

@router.get("/quests/assigned", response_model=List[ParentQuestResponse])
async def get_assigned_quests(
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get quests assigned to the current user (child)"""
    quest_service = ParentQuestService(db)
    quests = quest_service.get_child_quests(current_user.id, status)
    
    return [ParentQuestResponse.from_orm(q) for q in quests]

@router.post("/quests/{quest_id}/progress")
async def record_quest_progress(
    quest_id: int,
    progress_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record progress on a parent quest"""
    try:
        quest_service = ParentQuestService(db)
        success = quest_service.record_quest_progress(
            current_user.id, quest_id, progress_data
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to record progress")
            
        return {"message": "Progress recorded successfully"}
        
    except Exception as e:
        logger.error(f"Failed to record quest progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Real-time Monitoring

@router.get("/monitoring/dashboard", response_model=MonitoringDashboardResponse)
async def get_monitoring_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get real-time monitoring dashboard for parent"""
    try:
        monitoring_service = get_monitoring_service(db)
        dashboard_data = await monitoring_service.get_monitoring_dashboard(current_user.id)
        
        return MonitoringDashboardResponse(**dashboard_data)
        
    except Exception as e:
        logger.error(f"Failed to get monitoring dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/monitoring/ws")
async def monitoring_websocket(
    websocket: WebSocket,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time monitoring"""
    try:
        # Authenticate user from token
        from app.core.auth import verify_token
        payload = verify_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            await websocket.close(code=4001, reason="Invalid token")
            return
        
        # Get monitored children
        family_members = db.query(FamilyMember).filter(
            FamilyMember.user_id == user_id,
            FamilyMember.role.in_([FamilyRole.PARENT, FamilyRole.GUARDIAN])
        ).all()
        
        child_ids = []
        for member in family_members:
            children = db.query(FamilyMember).filter(
                FamilyMember.family_id == member.family_id,
                FamilyMember.role == FamilyRole.CHILD,
                FamilyMember.status == RelationshipStatus.ACTIVE
            ).all()
            child_ids.extend([c.user_id for c in children])
        
        # Accept connection
        await websocket.accept()
        
        # Register for monitoring
        monitoring_service = get_monitoring_service(db)
        await monitoring_service.register_parent_monitoring(user_id, child_ids)
        
        # Add to WebSocket group
        from app.core.websocket_manager import websocket_manager
        connection_id = await websocket_manager.connect(
            websocket, 
            group=f"parent_monitoring_{user_id}",
            metadata={"user_id": user_id, "role": "parent"}
        )
        
        try:
            # Keep connection alive
            while True:
                data = await websocket.receive_text()
                # Handle incoming messages if needed
                
        except WebSocketDisconnect:
            logger.info(f"Parent {user_id} disconnected from monitoring")
        finally:
            await monitoring_service.unregister_parent_monitoring(user_id)
            await websocket_manager.disconnect(connection_id)
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=4000, reason=str(e))

@router.post("/monitoring/activity")
async def record_child_activity(
    activity_data: ActivityUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record child activity (called by child's client)"""
    try:
        monitoring_service = get_monitoring_service(db)
        await monitoring_service.record_child_activity(
            current_user.id,
            activity_data.dict()
        )
        
        return {"message": "Activity recorded successfully"}
        
    except Exception as e:
        logger.error(f"Failed to record activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Report Generation

@router.post("/reports/generate", response_model=FamilyReportResponse)
async def generate_report(
    report_request: ReportGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a learning report for a child"""
    try:
        report_service = FamilyReportService(db)
        report = await report_service.generate_report(
            current_user.id,
            report_request.child_id,
            report_request.report_type
        )
        
        return FamilyReportResponse.from_orm(report)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports", response_model=List[FamilyReportResponse])
async def get_reports(
    child_id: Optional[int] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get family reports"""
    report_service = FamilyReportService(db)
    reports = report_service.get_family_reports(current_user.id, child_id, limit)
    
    return [FamilyReportResponse.from_orm(r) for r in reports]

@router.get("/reports/{report_id}")
async def get_report_details(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed report data"""
    report = db.query(FamilyReport).filter(FamilyReport.id == report_id).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Verify access
    family_member = db.query(FamilyMember).filter(
        FamilyMember.family_id == report.family_id,
        FamilyMember.user_id == current_user.id,
        FamilyMember.role.in_([FamilyRole.PARENT, FamilyRole.GUARDIAN])
    ).first()
    
    if not family_member:
        raise HTTPException(status_code=403, detail="Not authorized to view this report")
    
    # Mark as viewed
    report_service = FamilyReportService(db)
    report_service.mark_report_viewed(report_id, current_user.id)
    
    return {
        "report": FamilyReportResponse.from_orm(report),
        "details": {
            "daily_breakdown": report.daily_breakdown,
            "subject_performance": report.subject_performance,
            "ai_insights": report.ai_insights,
            "recommendations": report.recommendations
        }
    }

@router.post("/reports/{report_id}/share")
async def share_report(
    report_id: int,
    share_with: List[str] = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Share report with email addresses"""
    try:
        report_service = FamilyReportService(db)
        success = await report_service.share_report(
            report_id, current_user.id, share_with
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to share report")
            
        return {"message": f"Report shared with {len(share_with)} recipients"}
        
    except Exception as e:
        logger.error(f"Failed to share report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Notifications

@router.get("/notifications")
async def get_parent_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get parent notifications"""
    from app.models.family import ParentNotification
    
    query = db.query(ParentNotification).filter(
        ParentNotification.parent_id == current_user.id
    )
    
    if unread_only:
        query = query.filter(ParentNotification.is_read == False)
    
    notifications = query.order_by(
        ParentNotification.created_at.desc()
    ).limit(limit).all()
    
    return [
        {
            "id": n.id,
            "type": n.notification_type,
            "title": n.title,
            "message": n.message,
            "severity": n.severity,
            "child_id": n.child_id,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat()
        }
        for n in notifications
    ]

@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark notification as read"""
    from app.models.family import ParentNotification
    
    notification = db.query(ParentNotification).filter(
        ParentNotification.id == notification_id,
        ParentNotification.parent_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = True
    notification.read_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Notification marked as read"}