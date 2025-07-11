from typing import Dict, List, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import json
import asyncio
from collections import defaultdict

from app.utils.logger import service_logger

class ConnectionManager:
    def __init__(self):
        # user_id -> WebSocket connections
        self.active_connections: Dict[int, List[WebSocket]] = defaultdict(list)
        # websocket -> user_id mapping
        self.connection_to_user: Dict[WebSocket, int] = {}
        # user_id -> current room/session
        self.user_rooms: Dict[int, List[int]] = defaultdict(list)
        # room_id -> list of user_ids
        self.room_users: Dict[int, List[int]] = defaultdict(list)
        
    async def connect(self, websocket: WebSocket, user_id: int):
        """Connect a new WebSocket"""
        await websocket.accept()
        self.active_connections[user_id].append(websocket)
        self.connection_to_user[websocket] = user_id
        
        # Send connection confirmation
        await self.send_personal_message(
            websocket,
            {
                "type": "connection_established",
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Notify friends that user is online
        await self.broadcast_user_status(user_id, "online")
        
    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket"""
        user_id = self.connection_to_user.get(websocket)
        if user_id:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                # No more connections for this user
                del self.active_connections[user_id]
                # Remove from all rooms
                for room_id in list(self.user_rooms[user_id]):
                    self.leave_room(user_id, room_id)
                del self.user_rooms[user_id]
                
                # Notify friends that user is offline
                asyncio.create_task(self.broadcast_user_status(user_id, "offline"))
            
            del self.connection_to_user[websocket]
    
    def join_room(self, user_id: int, room_id: int):
        """Add user to a room"""
        if room_id not in self.user_rooms[user_id]:
            self.user_rooms[user_id].append(room_id)
            self.room_users[room_id].append(user_id)
    
    def leave_room(self, user_id: int, room_id: int):
        """Remove user from a room"""
        if room_id in self.user_rooms[user_id]:
            self.user_rooms[user_id].remove(room_id)
            self.room_users[room_id].remove(user_id)
            if not self.room_users[room_id]:
                del self.room_users[room_id]
    
    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """Send message to specific WebSocket"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            service_logger.error("Error sending WebSocket message", error=e, user_id=user_id)
    
    async def send_user_message(self, user_id: int, message: dict):
        """Send message to all connections of a user"""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                await self.send_personal_message(connection, message)
    
    async def broadcast_to_room(self, room_id: int, message: dict, exclude_user: Optional[int] = None):
        """Broadcast message to all users in a room"""
        if room_id in self.room_users:
            for user_id in self.room_users[room_id]:
                if user_id != exclude_user:
                    await self.send_user_message(user_id, message)
    
    async def broadcast_to_users(self, user_ids: List[int], message: dict):
        """Broadcast message to specific users"""
        for user_id in user_ids:
            await self.send_user_message(user_id, message)
    
    async def broadcast_user_status(self, user_id: int, status: str):
        """Broadcast user online/offline status to friends"""
        # This would need to query friends from database
        # For now, just a placeholder
        message = {
            "type": "user_status_update",
            "user_id": user_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        # Would broadcast to friends here
    
    def is_user_online(self, user_id: int) -> bool:
        """Check if user is online"""
        return user_id in self.active_connections
    
    def get_online_users(self) -> List[int]:
        """Get list of online users"""
        return list(self.active_connections.keys())
    
    def get_room_users(self, room_id: int) -> List[int]:
        """Get users in a specific room"""
        return self.room_users.get(room_id, [])
    
    # Specific message types
    
    async def send_notification(self, user_id: int, notification: dict):
        """Send notification to user"""
        message = {
            "type": "notification",
            "data": notification,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.send_user_message(user_id, message)
    
    async def send_chat_message(self, user_id: int, message: dict):
        """Send chat message to user"""
        wrapped_message = {
            "type": "chat_message",
            "data": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.send_user_message(user_id, wrapped_message)
    
    async def send_chat_update(self, user_id: int, update: dict):
        """Send chat update (edit, delete, reaction)"""
        message = {
            "type": "chat_update",
            "data": update,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.send_user_message(user_id, message)
    
    async def send_multiplayer_update(self, user_id: int, update: dict):
        """Send multiplayer session update"""
        message = {
            "type": "multiplayer_update",
            "data": update,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.send_user_message(user_id, message)
    
    async def send_game_update(self, user_id: int, update: dict):
        """Send game state update"""
        message = {
            "type": "game_update",
            "data": update,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.send_user_message(user_id, message)
    
    async def send_achievement_unlock(self, user_id: int, achievement: dict):
        """Send achievement unlock notification"""
        message = {
            "type": "achievement_unlocked",
            "data": achievement,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.send_user_message(user_id, message)
    
    async def handle_message(self, websocket: WebSocket, user_id: int, data: dict):
        """Handle incoming WebSocket message"""
        message_type = data.get("type")
        
        if message_type == "ping":
            # Respond to ping
            await self.send_personal_message(websocket, {"type": "pong"})
            
        elif message_type == "join_room":
            room_id = data.get("room_id")
            if room_id:
                self.join_room(user_id, room_id)
                await self.send_personal_message(
                    websocket,
                    {
                        "type": "room_joined",
                        "room_id": room_id
                    }
                )
                
        elif message_type == "leave_room":
            room_id = data.get("room_id")
            if room_id:
                self.leave_room(user_id, room_id)
                await self.send_personal_message(
                    websocket,
                    {
                        "type": "room_left",
                        "room_id": room_id
                    }
                )
                
        elif message_type == "typing":
            # Broadcast typing indicator
            room_id = data.get("room_id")
            if room_id:
                await self.broadcast_to_room(
                    room_id,
                    {
                        "type": "user_typing",
                        "user_id": user_id,
                        "room_id": room_id
                    },
                    exclude_user=user_id
                )
                
        elif message_type == "stop_typing":
            # Broadcast stop typing
            room_id = data.get("room_id")
            if room_id:
                await self.broadcast_to_room(
                    room_id,
                    {
                        "type": "user_stop_typing",
                        "user_id": user_id,
                        "room_id": room_id
                    },
                    exclude_user=user_id
                )
        
        # Add more message handlers as needed

# Create global instance
manager = ConnectionManager()