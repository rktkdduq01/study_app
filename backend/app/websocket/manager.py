import socketio
from typing import Dict, Set, Optional
import json
from datetime import datetime

from app.utils.logger import service_logger

class WebSocketManager:
    def __init__(self):
        self.sio = socketio.AsyncServer(
            async_mode='asgi',
            cors_allowed_origins="*",
            logger=True,
            engineio_logger=False
        )
        self.active_connections: Dict[str, str] = {}
        self.user_rooms: Dict[str, Set[str]] = {}
        self.parent_child_map: Dict[str, Set[str]] = {}
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        @self.sio.event
        async def connect(sid, environ):
            service_logger.info("WebSocket client connected", sid=sid)
            return True
        
        @self.sio.event
        async def disconnect(sid):
            service_logger.info("WebSocket client disconnected", sid=sid)
            await self._handle_disconnect(sid)
        
        @self.sio.event
        async def authenticate(sid, data):
            user_id = data.get("user_id")
            user_type = data.get("user_type")
            
            if user_id:
                self.active_connections[sid] = user_id
                
                if user_id not in self.user_rooms:
                    self.user_rooms[user_id] = set()
                self.user_rooms[user_id].add(sid)
                
                await self.sio.enter_room(sid, f"user_{user_id}")
                
                if user_type == "student":
                    await self.sio.enter_room(sid, "students")
                elif user_type == "parent":
                    await self.sio.enter_room(sid, "parents")
                
                await self.sio.emit("authenticated", {"status": "success"}, room=sid)
                service_logger.info("User authenticated via WebSocket", user_id=user_id, sid=sid, user_type=user_type)
        
        @self.sio.event
        async def join_room(sid, data):
            room_name = data.get("room")
            if room_name:
                await self.sio.enter_room(sid, room_name)
                await self.sio.emit("joined_room", {"room": room_name}, room=sid)
        
        @self.sio.event
        async def leave_room(sid, data):
            room_name = data.get("room")
            if room_name:
                await self.sio.leave_room(sid, room_name)
                await self.sio.emit("left_room", {"room": room_name}, room=sid)
        
        @self.sio.event
        async def learning_progress_update(sid, data):
            user_id = self.active_connections.get(sid)
            if user_id:
                data["timestamp"] = datetime.utcnow().isoformat()
                data["user_id"] = user_id
                
                await self.sio.emit("learning_progress", data, room=f"user_{user_id}")
                
                parent_ids = self._get_parent_ids(user_id)
                for parent_id in parent_ids:
                    await self.sio.emit("child_progress_update", data, room=f"user_{parent_id}")
        
        @self.sio.event
        async def quest_completed(sid, data):
            user_id = self.active_connections.get(sid)
            if user_id:
                data["timestamp"] = datetime.utcnow().isoformat()
                data["user_id"] = user_id
                
                await self.sio.emit("quest_completion", data, room=f"user_{user_id}")
                
                parent_ids = self._get_parent_ids(user_id)
                for parent_id in parent_ids:
                    notification = {
                        "type": "quest_completed",
                        "title": "퀘스트 완료",
                        "message": f"자녀가 '{data.get('quest_title', '퀘스트')}'를 완료했습니다!",
                        "child_id": user_id,
                        "timestamp": data["timestamp"]
                    }
                    await self.sio.emit("parent_notification", notification, room=f"user_{parent_id}")
        
        @self.sio.event
        async def achievement_unlocked(sid, data):
            user_id = self.active_connections.get(sid)
            if user_id:
                data["timestamp"] = datetime.utcnow().isoformat()
                data["user_id"] = user_id
                
                await self.sio.emit("achievement_notification", data, room=f"user_{user_id}")
                
                await self.sio.emit("achievement_broadcast", data, room="students")
                
                parent_ids = self._get_parent_ids(user_id)
                for parent_id in parent_ids:
                    notification = {
                        "type": "achievement_unlocked",
                        "title": "새로운 업적 달성!",
                        "message": f"자녀가 '{data.get('achievement_title', '업적')}'을 달성했습니다!",
                        "child_id": user_id,
                        "timestamp": data["timestamp"]
                    }
                    await self.sio.emit("parent_notification", notification, room=f"user_{parent_id}")
        
        @self.sio.event
        async def multiplayer_invite(sid, data):
            inviter_id = self.active_connections.get(sid)
            invitee_id = data.get("invitee_id")
            
            if inviter_id and invitee_id:
                invitation = {
                    "inviter_id": inviter_id,
                    "inviter_name": data.get("inviter_name", "Unknown"),
                    "game_type": data.get("game_type", "quest"),
                    "room_id": data.get("room_id"),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await self.sio.emit("multiplayer_invitation", invitation, room=f"user_{invitee_id}")
        
        @self.sio.event
        async def multiplayer_join(sid, data):
            user_id = self.active_connections.get(sid)
            room_id = data.get("room_id")
            
            if user_id and room_id:
                await self.sio.enter_room(sid, f"multiplayer_{room_id}")
                
                join_data = {
                    "user_id": user_id,
                    "user_name": data.get("user_name", "Unknown"),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await self.sio.emit("player_joined", join_data, room=f"multiplayer_{room_id}")
        
        @self.sio.event
        async def multiplayer_action(sid, data):
            room_id = data.get("room_id")
            if room_id:
                data["timestamp"] = datetime.utcnow().isoformat()
                await self.sio.emit("multiplayer_update", data, room=f"multiplayer_{room_id}", skip_sid=sid)
    
    async def _handle_disconnect(self, sid):
        user_id = self.active_connections.pop(sid, None)
        
        if user_id and user_id in self.user_rooms:
            self.user_rooms[user_id].discard(sid)
            if not self.user_rooms[user_id]:
                del self.user_rooms[user_id]
    
    def _get_parent_ids(self, child_id: str) -> Set[str]:
        return self.parent_child_map.get(child_id, set())
    
    def set_parent_child_relationship(self, parent_id: str, child_id: str):
        if child_id not in self.parent_child_map:
            self.parent_child_map[child_id] = set()
        self.parent_child_map[child_id].add(parent_id)
    
    async def send_notification(self, user_id: str, notification: dict):
        notification["timestamp"] = datetime.utcnow().isoformat()
        await self.sio.emit("notification", notification, room=f"user_{user_id}")
    
    async def broadcast_to_students(self, event: str, data: dict):
        data["timestamp"] = datetime.utcnow().isoformat()
        await self.sio.emit(event, data, room="students")
    
    async def broadcast_to_parents(self, event: str, data: dict):
        data["timestamp"] = datetime.utcnow().isoformat()
        await self.sio.emit(event, data, room="parents")
    
    def get_app(self):
        return socketio.ASGIApp(self.sio)

websocket_manager = WebSocketManager()