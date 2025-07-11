from typing import Dict, Any
from datetime import datetime
from ..websocket.manager import websocket_manager

class WebSocketEvents:
    @staticmethod
    async def emit_learning_progress(user_id: str, progress_data: Dict[str, Any]):
        event_data = {
            "user_id": user_id,
            "progress": progress_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await websocket_manager.sio.emit("learning_progress", event_data, room=f"user_{user_id}")
        
        parent_ids = websocket_manager._get_parent_ids(user_id)
        for parent_id in parent_ids:
            await websocket_manager.sio.emit("child_progress_update", event_data, room=f"user_{parent_id}")
    
    @staticmethod
    async def emit_quest_completion(user_id: str, quest_data: Dict[str, Any]):
        event_data = {
            "user_id": user_id,
            "quest": quest_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await websocket_manager.sio.emit("quest_completion", event_data, room=f"user_{user_id}")
        
        parent_ids = websocket_manager._get_parent_ids(user_id)
        for parent_id in parent_ids:
            notification = {
                "type": "quest_completed",
                "title": "퀘스트 완료",
                "message": f"자녀가 '{quest_data.get('title', '퀘스트')}'를 완료했습니다!",
                "child_id": user_id,
                "quest_data": quest_data,
                "timestamp": event_data["timestamp"]
            }
            await websocket_manager.sio.emit("parent_notification", notification, room=f"user_{parent_id}")
    
    @staticmethod
    async def emit_achievement_unlock(user_id: str, achievement_data: Dict[str, Any]):
        event_data = {
            "user_id": user_id,
            "achievement": achievement_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await websocket_manager.sio.emit("achievement_notification", event_data, room=f"user_{user_id}")
        
        await websocket_manager.sio.emit("achievement_broadcast", event_data, room="students")
        
        parent_ids = websocket_manager._get_parent_ids(user_id)
        for parent_id in parent_ids:
            notification = {
                "type": "achievement_unlocked",
                "title": "새로운 업적 달성!",
                "message": f"자녀가 '{achievement_data.get('title', '업적')}'을 달성했습니다!",
                "child_id": user_id,
                "achievement_data": achievement_data,
                "timestamp": event_data["timestamp"]
            }
            await websocket_manager.sio.emit("parent_notification", notification, room=f"user_{parent_id}")
    
    @staticmethod
    async def emit_level_up(user_id: str, level_data: Dict[str, Any]):
        event_data = {
            "user_id": user_id,
            "level": level_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await websocket_manager.sio.emit("level_up", event_data, room=f"user_{user_id}")
        
        await websocket_manager.sio.emit("level_up_broadcast", event_data, room="students")
        
        parent_ids = websocket_manager._get_parent_ids(user_id)
        for parent_id in parent_ids:
            notification = {
                "type": "level_up",
                "title": "레벨 업!",
                "message": f"자녀가 레벨 {level_data.get('new_level', 0)}에 도달했습니다!",
                "child_id": user_id,
                "level_data": level_data,
                "timestamp": event_data["timestamp"]
            }
            await websocket_manager.sio.emit("parent_notification", notification, room=f"user_{parent_id}")
    
    @staticmethod
    async def emit_friend_request(from_user_id: str, to_user_id: str, request_data: Dict[str, Any]):
        event_data = {
            "from_user_id": from_user_id,
            "request_data": request_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await websocket_manager.sio.emit("friend_request", event_data, room=f"user_{to_user_id}")
    
    @staticmethod
    async def emit_multiplayer_update(room_id: str, update_data: Dict[str, Any]):
        event_data = {
            "room_id": room_id,
            "update": update_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await websocket_manager.sio.emit("multiplayer_update", event_data, room=f"multiplayer_{room_id}")
    
    @staticmethod
    async def emit_system_announcement(announcement: str, target: str = "all"):
        event_data = {
            "type": "system_announcement",
            "message": announcement,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if target == "all":
            await websocket_manager.sio.emit("system_announcement", event_data)
        elif target == "students":
            await websocket_manager.broadcast_to_students("system_announcement", event_data)
        elif target == "parents":
            await websocket_manager.broadcast_to_parents("system_announcement", event_data)