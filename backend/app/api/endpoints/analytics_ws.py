from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional
import logging

from ...core.auth import get_current_user_ws
from ...services.analytics_websocket import analytics_websocket_manager

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/ws/analytics/global")
async def analytics_global_websocket(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """WebSocket endpoint for global analytics (admin only)"""
    try:
        # Authenticate user
        user = await get_current_user_ws(websocket, token)
        if not user or user.role != "admin":
            await websocket.close(code=4003, reason="Unauthorized")
            return
        
        # Handle WebSocket connection
        await analytics_websocket_manager.handle_analytics_websocket(
            websocket, "global"
        )
    except Exception as e:
        logger.error(f"Error in global analytics WebSocket: {str(e)}")
        await websocket.close(code=4000, reason="Internal error")

@router.websocket("/ws/analytics/user")
async def analytics_user_websocket(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """WebSocket endpoint for user-specific analytics"""
    try:
        # Authenticate user
        user = await get_current_user_ws(websocket, token)
        if not user:
            await websocket.close(code=4003, reason="Unauthorized")
            return
        
        # Handle WebSocket connection
        await analytics_websocket_manager.handle_analytics_websocket(
            websocket, "user", user.id
        )
    except Exception as e:
        logger.error(f"Error in user analytics WebSocket: {str(e)}")
        await websocket.close(code=4000, reason="Internal error")

@router.websocket("/ws/analytics/content")
async def analytics_content_websocket(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """WebSocket endpoint for content analytics (admin/teacher only)"""
    try:
        # Authenticate user
        user = await get_current_user_ws(websocket, token)
        if not user or user.role not in ["admin", "teacher"]:
            await websocket.close(code=4003, reason="Unauthorized")
            return
        
        # Handle WebSocket connection
        await analytics_websocket_manager.handle_analytics_websocket(
            websocket, "content"
        )
    except Exception as e:
        logger.error(f"Error in content analytics WebSocket: {str(e)}")
        await websocket.close(code=4000, reason="Internal error")