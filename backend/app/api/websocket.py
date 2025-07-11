"""
WebSocket API Endpoints
WebSocket endpoints for real-time communication
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional

from app.core.logger import get_logger
from app.core.websocket_manager import websocket_manager

logger = get_logger(__name__)

# Create router
router = APIRouter()

@router.websocket("/ws/apm")
async def apm_websocket(
    websocket: WebSocket,
    client_id: Optional[str] = Query(None)
):
    """WebSocket endpoint for APM real-time updates"""
    metadata = {
        "client_id": client_id,
        "endpoint": "apm"
    }
    
    await websocket_manager.handle_connection(
        websocket, 
        group="apm_dashboard", 
        metadata=metadata
    )

@router.websocket("/ws/general")
async def general_websocket(
    websocket: WebSocket,
    group: Optional[str] = Query(None),
    client_id: Optional[str] = Query(None)
):
    """General WebSocket endpoint"""
    metadata = {
        "client_id": client_id,
        "endpoint": "general"
    }
    
    await websocket_manager.handle_connection(
        websocket,
        group=group,
        metadata=metadata
    )