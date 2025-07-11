"""
Parent Dashboard API endpoints
"""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_active_user, get_current_parent_user
from app.models.user import User
from app.models.family import Family, FamilyMember, FamilyRole
from app.services.parent_quest_service import ParentQuestService
from app.services.family_report_service import FamilyReportService
from app.core.family_monitoring import FamilyMonitoringService
from app.schemas.family import (
    FamilyCreate,
    FamilyUpdate,
    FamilyResponse,
    FamilyMemberCreate,
    FamilyMemberResponse,
    ParentQuestCreate,
    ParentQuestUpdate,
    ParentQuestResponse,
    DashboardData,
    FamilyReportCreate,
    FamilyReportResponse,
    ParentNotificationResponse,
    FamilySettings,
    FamilySettingsUpdate,
    NotificationPreferences,
    ActivityMonitoringResponse
)
from app.core.exceptions import NotFoundException, BadRequestException, ForbiddenException
from app.websocket.manager import WebSocketManager

router = APIRouter()
ws_manager = WebSocketManager()


# Family Management Endpoints
@router.post("/families", response_model=FamilyResponse)
async def create_family(
    family_data: FamilyCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new family group"""
    # Check if user already belongs to a family as parent
    existing_member = db.query(FamilyMember).filter(
        FamilyMember.user_id == current_user.id,
        FamilyMember.role == FamilyRole.PARENT,
        FamilyMember.is_active == True
    ).first()
    
    if existing_member:
        raise BadRequestException("You already belong to a family as a parent")
    
    # Create family
    family = Family(
        name=family_data.name,
        description=family_data.description,
        created_by=current_user.id
    )
    db.add(family)
    db.commit()
    db.refresh(family)
    
    # Add creator as parent
    family_member = FamilyMember(
        family_id=family.id,
        user_id=current_user.id,
        role=FamilyRole.PARENT
    )
    db.add(family_member)
    db.commit()
    
    family.member_count = 1
    return family


@router.get("/families/my", response_model=FamilyResponse)
async def get_my_family(
    current_user: User = Depends(get_current_parent_user),
    db: Session = Depends(get_db)
):
    """Get current user's family"""
    family_member = db.query(FamilyMember).filter(
        FamilyMember.user_id == current_user.id,
        FamilyMember.is_active == True
    ).first()
    
    if not family_member:
        raise NotFoundException("You don't belong to any family")
    
    family = db.query(Family).filter(
        Family.id == family_member.family_id,
        Family.is_active == True
    ).first()
    
    if not family:
        raise NotFoundException("Family not found")
    
    # Get member count
    member_count = db.query(FamilyMember).filter(
        FamilyMember.family_id == family.id,
        FamilyMember.is_active == True
    ).count()
    
    family.member_count = member_count
    return family


@router.get("/families/{family_id}/members", response_model=List[FamilyMemberResponse])
async def get_family_members(
    family_id: int,
    current_user: User = Depends(get_current_parent_user),
    db: Session = Depends(get_db)
):
    """Get all family members"""
    # Verify user is parent in this family
    parent_member = db.query(FamilyMember).filter(
        FamilyMember.family_id == family_id,
        FamilyMember.user_id == current_user.id,
        FamilyMember.role == FamilyRole.PARENT,
        FamilyMember.is_active == True
    ).first()
    
    if not parent_member:
        raise ForbiddenException("You don't have permission to view this family")
    
    members = db.query(FamilyMember).filter(
        FamilyMember.family_id == family_id,
        FamilyMember.is_active == True
    ).all()
    
    # Enhance with user info
    for member in members:
        user = db.query(User).filter(User.id == member.user_id).first()
        if user:
            member.user_name = user.username
            member.user_email = user.email
            member.user_avatar = user.avatar_url
    
    return members


@router.post("/families/{family_id}/invite", response_model=dict)
async def invite_family_member(
    family_id: int,
    member_data: FamilyMemberCreate,
    current_user: User = Depends(get_current_parent_user),
    db: Session = Depends(get_db)
):
    """Invite a user to join the family"""
    # Verify user is parent in this family
    parent_member = db.query(FamilyMember).filter(
        FamilyMember.family_id == family_id,
        FamilyMember.user_id == current_user.id,
        FamilyMember.role == FamilyRole.PARENT,
        FamilyMember.is_active == True
    ).first()
    
    if not parent_member:
        raise ForbiddenException("You don't have permission to invite to this family")
    
    # Check if user exists
    invited_user = db.query(User).filter(User.id == member_data.user_id).first()
    if not invited_user:
        raise NotFoundException("User not found")
    
    # Check if already a member
    existing = db.query(FamilyMember).filter(
        FamilyMember.family_id == family_id,
        FamilyMember.user_id == member_data.user_id,
        FamilyMember.is_active == True
    ).first()
    
    if existing:
        raise BadRequestException("User is already a family member")
    
    # Create family member
    new_member = FamilyMember(
        family_id=family_id,
        user_id=member_data.user_id,
        role=member_data.role
    )
    db.add(new_member)
    db.commit()
    
    # TODO: Send invitation notification
    
    return {
        "message": f"Successfully invited {invited_user.username} to the family",
        "member_id": new_member.id
    }


# Dashboard Endpoints
@router.get("/dashboard", response_model=DashboardData)
async def get_parent_dashboard(
    current_user: User = Depends(get_current_parent_user),
    db: Session = Depends(get_db)
):
    """Get parent dashboard data"""
    # Get user's family
    family_member = db.query(FamilyMember).filter(
        FamilyMember.user_id == current_user.id,
        FamilyMember.role == FamilyRole.PARENT,
        FamilyMember.is_active == True
    ).first()
    
    if not family_member:
        raise NotFoundException("You don't belong to any family as a parent")
    
    family = db.query(Family).filter(
        Family.id == family_member.family_id,
        Family.is_active == True
    ).first()
    
    if not family:
        raise NotFoundException("Family not found")
    
    # Get dashboard data from monitoring service
    monitoring_service = FamilyMonitoringService(db)
    dashboard_data = monitoring_service.get_dashboard_data(family.id, current_user.id)
    
    return dashboard_data


@router.get("/dashboard/activities", response_model=List[ActivityMonitoringResponse])
async def get_recent_activities(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    child_id: Optional[int] = Query(None, description="Filter by child ID"),
    current_user: User = Depends(get_current_parent_user),
    db: Session = Depends(get_db)
):
    """Get recent activities for all children"""
    # Get user's family
    family_member = db.query(FamilyMember).filter(
        FamilyMember.user_id == current_user.id,
        FamilyMember.role == FamilyRole.PARENT,
        FamilyMember.is_active == True
    ).first()
    
    if not family_member:
        raise NotFoundException("You don't belong to any family as a parent")
    
    monitoring_service = FamilyMonitoringService(db)
    
    # If child_id provided, verify they belong to the family
    if child_id:
        child_member = db.query(FamilyMember).filter(
            FamilyMember.family_id == family_member.family_id,
            FamilyMember.user_id == child_id,
            FamilyMember.role == FamilyRole.CHILD,
            FamilyMember.is_active == True
        ).first()
        
        if not child_member:
            raise ForbiddenException("Child not found in your family")
    
    activities = monitoring_service.get_recent_activities(
        family_id=family_member.family_id,
        hours=hours,
        child_id=child_id
    )
    
    return activities


# Quest Management Endpoints
@router.post("/quests", response_model=ParentQuestResponse)
async def create_parent_quest(
    quest_data: ParentQuestCreate,
    current_user: User = Depends(get_current_parent_user),
    db: Session = Depends(get_db)
):
    """Create a custom quest for a child"""
    # Verify child belongs to parent's family
    family_member = db.query(FamilyMember).filter(
        FamilyMember.user_id == current_user.id,
        FamilyMember.role == FamilyRole.PARENT,
        FamilyMember.is_active == True
    ).first()
    
    if not family_member:
        raise NotFoundException("You don't belong to any family as a parent")
    
    # Verify child is in the same family
    child_member = db.query(FamilyMember).filter(
        FamilyMember.family_id == family_member.family_id,
        FamilyMember.user_id == quest_data.child_id,
        FamilyMember.role == FamilyRole.CHILD,
        FamilyMember.is_active == True
    ).first()
    
    if not child_member:
        raise ForbiddenException("Child not found in your family")
    
    quest_service = ParentQuestService(db)
    quest = quest_service.create_quest(
        parent_id=current_user.id,
        family_id=family_member.family_id,
        quest_data=quest_data
    )
    
    return quest


@router.get("/quests", response_model=List[ParentQuestResponse])
async def get_parent_quests(
    child_id: Optional[int] = Query(None, description="Filter by child ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_completed: Optional[bool] = Query(None, description="Filter by completion status"),
    current_user: User = Depends(get_current_parent_user),
    db: Session = Depends(get_db)
):
    """Get all parent-created quests"""
    # Get user's family
    family_member = db.query(FamilyMember).filter(
        FamilyMember.user_id == current_user.id,
        FamilyMember.role == FamilyRole.PARENT,
        FamilyMember.is_active == True
    ).first()
    
    if not family_member:
        raise NotFoundException("You don't belong to any family as a parent")
    
    quest_service = ParentQuestService(db)
    quests = quest_service.get_family_quests(
        family_id=family_member.family_id,
        child_id=child_id,
        is_active=is_active,
        is_completed=is_completed
    )
    
    return quests


@router.put("/quests/{quest_id}", response_model=ParentQuestResponse)
async def update_parent_quest(
    quest_id: int,
    quest_update: ParentQuestUpdate,
    current_user: User = Depends(get_current_parent_user),
    db: Session = Depends(get_db)
):
    """Update a parent quest"""
    quest_service = ParentQuestService(db)
    
    # Verify quest belongs to parent
    quest = quest_service.get_quest(quest_id)
    if quest.created_by != current_user.id:
        raise ForbiddenException("You don't have permission to update this quest")
    
    updated_quest = quest_service.update_quest(quest_id, quest_update)
    return updated_quest


@router.delete("/quests/{quest_id}")
async def cancel_parent_quest(
    quest_id: int,
    current_user: User = Depends(get_current_parent_user),
    db: Session = Depends(get_db)
):
    """Cancel a parent quest"""
    quest_service = ParentQuestService(db)
    
    # Verify quest belongs to parent
    quest = quest_service.get_quest(quest_id)
    if quest.created_by != current_user.id:
        raise ForbiddenException("You don't have permission to cancel this quest")
    
    quest_service.cancel_quest(quest_id)
    
    return {"message": "Quest cancelled successfully"}


# Report Generation Endpoints
@router.post("/reports", response_model=FamilyReportResponse)
async def generate_family_report(
    report_data: FamilyReportCreate,
    current_user: User = Depends(get_current_parent_user),
    db: Session = Depends(get_db)
):
    """Generate a family report"""
    # Get user's family
    family_member = db.query(FamilyMember).filter(
        FamilyMember.user_id == current_user.id,
        FamilyMember.role == FamilyRole.PARENT,
        FamilyMember.is_active == True
    ).first()
    
    if not family_member:
        raise NotFoundException("You don't belong to any family as a parent")
    
    # If child_id provided, verify they belong to the family
    if report_data.child_id:
        child_member = db.query(FamilyMember).filter(
            FamilyMember.family_id == family_member.family_id,
            FamilyMember.user_id == report_data.child_id,
            FamilyMember.role == FamilyRole.CHILD,
            FamilyMember.is_active == True
        ).first()
        
        if not child_member:
            raise ForbiddenException("Child not found in your family")
    
    report_service = FamilyReportService(db)
    report = await report_service.generate_report(
        family_id=family_member.family_id,
        parent_id=current_user.id,
        report_data=report_data
    )
    
    return report


@router.get("/reports", response_model=List[FamilyReportResponse])
async def get_family_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_parent_user),
    db: Session = Depends(get_db)
):
    """Get all family reports"""
    # Get user's family
    family_member = db.query(FamilyMember).filter(
        FamilyMember.user_id == current_user.id,
        FamilyMember.role == FamilyRole.PARENT,
        FamilyMember.is_active == True
    ).first()
    
    if not family_member:
        raise NotFoundException("You don't belong to any family as a parent")
    
    report_service = FamilyReportService(db)
    reports = report_service.get_reports(
        family_id=family_member.family_id,
        skip=skip,
        limit=limit
    )
    
    return reports


@router.get("/reports/{report_id}/download")
async def download_report(
    report_id: int,
    current_user: User = Depends(get_current_parent_user),
    db: Session = Depends(get_db)
):
    """Download a report as PDF"""
    report_service = FamilyReportService(db)
    report = report_service.get_report(report_id)
    
    # Verify report belongs to user's family
    family_member = db.query(FamilyMember).filter(
        FamilyMember.user_id == current_user.id,
        FamilyMember.role == FamilyRole.PARENT,
        FamilyMember.is_active == True
    ).first()
    
    if not family_member or report.family_id != family_member.family_id:
        raise ForbiddenException("You don't have permission to download this report")
    
    # Generate PDF if not already generated
    if not report.file_url:
        file_url = await report_service.generate_pdf(report_id)
        return {"download_url": file_url}
    
    return {"download_url": report.file_url}


# Notification Endpoints
@router.get("/notifications", response_model=List[ParentNotificationResponse])
async def get_parent_notifications(
    unread_only: bool = Query(False, description="Show only unread notifications"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_parent_user),
    db: Session = Depends(get_db)
):
    """Get parent notifications"""
    # Get user's family
    family_member = db.query(FamilyMember).filter(
        FamilyMember.user_id == current_user.id,
        FamilyMember.role == FamilyRole.PARENT,
        FamilyMember.is_active == True
    ).first()
    
    if not family_member:
        raise NotFoundException("You don't belong to any family as a parent")
    
    monitoring_service = FamilyMonitoringService(db)
    notifications = monitoring_service.get_parent_notifications(
        parent_id=current_user.id,
        family_id=family_member.family_id,
        unread_only=unread_only,
        skip=skip,
        limit=limit
    )
    
    return notifications


@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_parent_user),
    db: Session = Depends(get_db)
):
    """Mark a notification as read"""
    monitoring_service = FamilyMonitoringService(db)
    
    # Verify notification belongs to user
    notification = monitoring_service.get_notification(notification_id)
    if notification.parent_id != current_user.id:
        raise ForbiddenException("You don't have permission to update this notification")
    
    monitoring_service.mark_notification_read(notification_id)
    
    return {"message": "Notification marked as read"}


# Settings Endpoints
@router.get("/settings", response_model=FamilySettings)
async def get_family_settings(
    current_user: User = Depends(get_current_parent_user),
    db: Session = Depends(get_db)
):
    """Get family settings"""
    # Get user's family
    family_member = db.query(FamilyMember).filter(
        FamilyMember.user_id == current_user.id,
        FamilyMember.role == FamilyRole.PARENT,
        FamilyMember.is_active == True
    ).first()
    
    if not family_member:
        raise NotFoundException("You don't belong to any family as a parent")
    
    monitoring_service = FamilyMonitoringService(db)
    settings = monitoring_service.get_family_settings(
        family_id=family_member.family_id,
        parent_id=current_user.id
    )
    
    return settings


@router.put("/settings", response_model=FamilySettings)
async def update_family_settings(
    settings_update: FamilySettingsUpdate,
    current_user: User = Depends(get_current_parent_user),
    db: Session = Depends(get_db)
):
    """Update family settings"""
    # Get user's family
    family_member = db.query(FamilyMember).filter(
        FamilyMember.user_id == current_user.id,
        FamilyMember.role == FamilyRole.PARENT,
        FamilyMember.is_active == True
    ).first()
    
    if not family_member:
        raise NotFoundException("You don't belong to any family as a parent")
    
    monitoring_service = FamilyMonitoringService(db)
    updated_settings = monitoring_service.update_family_settings(
        family_id=family_member.family_id,
        parent_id=current_user.id,
        settings_update=settings_update
    )
    
    return updated_settings


# WebSocket Endpoint for Real-time Monitoring
@router.websocket("/ws/{family_id}")
async def websocket_monitoring(
    websocket: WebSocket,
    family_id: int,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time family monitoring"""
    await ws_manager.connect(websocket)
    
    try:
        # TODO: Verify authentication from WebSocket
        # TODO: Verify user is parent in this family
        
        # Join family room
        await ws_manager.join_room(websocket, f"family_{family_id}")
        
        # Send initial connection success
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "family_id": family_id
        })
        
        # Keep connection alive and handle messages
        while True:
            data = await websocket.receive_json()
            
            # Handle different message types
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif data.get("type") == "refresh_dashboard":
                # Send updated dashboard data
                monitoring_service = FamilyMonitoringService(db)
                dashboard_data = monitoring_service.get_dashboard_data(
                    family_id=family_id,
                    parent_id=data.get("parent_id")
                )
                await websocket.send_json({
                    "type": "dashboard_update",
                    "data": dashboard_data.dict()
                })
                
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        await ws_manager.leave_room(websocket, f"family_{family_id}")