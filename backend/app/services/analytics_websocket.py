from typing import Dict, Set, Optional
import asyncio
import json
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
import logging

from ..core.redis_client import redis_client
from ..database import SessionLocal

logger = logging.getLogger(__name__)

class AnalyticsWebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "global": set(),  # Admin users watching global metrics
            "content": set(),  # Content analytics subscribers
            "user": {}  # User-specific analytics: {user_id: set of websockets}
        }
        self.redis_client = redis_client
        self._running = False
        self._tasks = []
    
    async def connect(self, websocket: WebSocket, channel: str, user_id: Optional[int] = None):
        """Connect a client to analytics updates"""
        await websocket.accept()
        
        if channel == "user" and user_id:
            if user_id not in self.active_connections["user"]:
                self.active_connections["user"][user_id] = set()
            self.active_connections["user"][user_id].add(websocket)
            logger.info(f"User {user_id} connected to personal analytics")
        else:
            self.active_connections[channel].add(websocket)
            logger.info(f"Client connected to {channel} analytics")
        
        # Send initial data
        await self._send_initial_data(websocket, channel, user_id)
    
    def disconnect(self, websocket: WebSocket, channel: str, user_id: Optional[int] = None):
        """Disconnect a client"""
        if channel == "user" and user_id:
            if user_id in self.active_connections["user"]:
                self.active_connections["user"][user_id].discard(websocket)
                if not self.active_connections["user"][user_id]:
                    del self.active_connections["user"][user_id]
        else:
            self.active_connections[channel].discard(websocket)
        
        logger.info(f"Client disconnected from {channel} analytics")
    
    async def _send_initial_data(self, websocket: WebSocket, channel: str, user_id: Optional[int] = None):
        """Send initial analytics data to newly connected client"""
        try:
            initial_data = {
                "type": "initial",
                "channel": channel,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if channel == "global":
                # Send current global metrics
                global_metrics = await self.redis_client.hgetall("analytics:global:today")
                initial_data["data"] = {
                    "global_activity": {k.decode(): int(v) for k, v in global_metrics.items()},
                    "active_users": await self.redis_client.scard("analytics:active_users:today")
                }
            elif channel == "user" and user_id:
                # Send user-specific metrics
                user_metrics = await self.redis_client.hgetall(f"analytics:user:{user_id}:today")
                initial_data["data"] = {
                    "user_activity": {k.decode(): int(v) for k, v in user_metrics.items()}
                }
            
            await websocket.send_json(initial_data)
        except Exception as e:
            logger.error(f"Error sending initial data: {str(e)}")
    
    async def broadcast_to_channel(self, channel: str, message: dict):
        """Broadcast message to all connections in a channel"""
        if channel not in self.active_connections:
            return
        
        connections = self.active_connections[channel].copy()
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to channel {channel}: {str(e)}")
                self.disconnect(connection, channel)
    
    async def broadcast_to_user(self, user_id: int, message: dict):
        """Broadcast message to specific user's connections"""
        if user_id not in self.active_connections["user"]:
            return
        
        connections = self.active_connections["user"][user_id].copy()
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to user {user_id}: {str(e)}")
                self.disconnect(connection, "user", user_id)
    
    async def start_analytics_stream(self):
        """Start streaming analytics updates"""
        if self._running:
            return
        
        self._running = True
        
        # Start Redis pubsub listener
        self._tasks.append(asyncio.create_task(self._redis_listener()))
        
        # Start periodic metrics broadcaster
        self._tasks.append(asyncio.create_task(self._periodic_metrics_broadcaster()))
        
        logger.info("Analytics WebSocket streaming started")
    
    async def stop_analytics_stream(self):
        """Stop analytics streaming"""
        self._running = False
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        
        logger.info("Analytics WebSocket streaming stopped")
    
    async def _redis_listener(self):
        """Listen for analytics events from Redis"""
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe("analytics:events", "analytics:updates")
        
        try:
            while self._running:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                
                if message and message['type'] == 'message':
                    try:
                        data = json.loads(message['data'])
                        await self._process_analytics_event(data)
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON in Redis message: {message['data']}")
                
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass
        finally:
            await pubsub.unsubscribe()
            await pubsub.close()
    
    async def _process_analytics_event(self, event: dict):
        """Process and broadcast analytics event"""
        event_type = event.get("type")
        
        if event_type == "user_activity":
            # Broadcast to global channel
            await self.broadcast_to_channel("global", {
                "type": "activity_update",
                "data": event,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Broadcast to specific user if applicable
            user_id = event.get("user_id")
            if user_id:
                await self.broadcast_to_user(user_id, {
                    "type": "personal_activity",
                    "data": event,
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        elif event_type == "content_update":
            # Broadcast to content channel
            await self.broadcast_to_channel("content", {
                "type": "content_metrics",
                "data": event,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def _periodic_metrics_broadcaster(self):
        """Periodically broadcast metrics updates"""
        try:
            while self._running:
                # Every 5 seconds, send updated metrics
                await asyncio.sleep(5)
                
                # Global metrics
                if self.active_connections["global"]:
                    global_metrics = await self._get_current_global_metrics()
                    await self.broadcast_to_channel("global", {
                        "type": "metrics_update",
                        "data": global_metrics,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                # User-specific metrics
                for user_id, connections in self.active_connections["user"].items():
                    if connections:
                        user_metrics = await self._get_current_user_metrics(user_id)
                        await self.broadcast_to_user(user_id, {
                            "type": "personal_metrics_update",
                            "data": user_metrics,
                            "timestamp": datetime.utcnow().isoformat()
                        })
        
        except asyncio.CancelledError:
            pass
    
    async def _get_current_global_metrics(self) -> dict:
        """Get current global metrics from Redis"""
        try:
            # Get various metrics
            global_activity = await self.redis_client.hgetall("analytics:global:today")
            active_users = await self.redis_client.scard("analytics:active_users:today")
            
            # Get recent events
            recent_events = await self.redis_client.lrange("analytics:events", 0, 4)
            events = []
            for event_data in recent_events:
                try:
                    events.append(json.loads(event_data))
                except:
                    pass
            
            return {
                "global_activity": {k.decode(): int(v) for k, v in global_activity.items()},
                "active_users": active_users,
                "recent_events": events,
                "server_time": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting global metrics: {str(e)}")
            return {}
    
    async def _get_current_user_metrics(self, user_id: int) -> dict:
        """Get current metrics for a specific user"""
        try:
            user_activity = await self.redis_client.hgetall(f"analytics:user:{user_id}:today")
            
            # Get user's recent achievements
            recent_achievements = await self.redis_client.lrange(
                f"analytics:user:{user_id}:achievements", 0, 4
            )
            
            return {
                "user_activity": {k.decode(): int(v) for k, v in user_activity.items()},
                "recent_achievements": [json.loads(a) for a in recent_achievements if a],
                "daily_streak": await self.redis_client.get(f"analytics:user:{user_id}:streak") or 0
            }
        except Exception as e:
            logger.error(f"Error getting user metrics: {str(e)}")
            return {}
    
    async def handle_analytics_websocket(
        self,
        websocket: WebSocket,
        channel: str,
        user_id: Optional[int] = None
    ):
        """Handle WebSocket connection for analytics"""
        await self.connect(websocket, channel, user_id)
        
        try:
            while True:
                # Keep connection alive and handle any client messages
                data = await websocket.receive_text()
                
                # Handle client commands (e.g., subscribe to specific metrics)
                try:
                    command = json.loads(data)
                    await self._handle_client_command(websocket, command)
                except json.JSONDecodeError:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Invalid JSON"
                    })
        except WebSocketDisconnect:
            self.disconnect(websocket, channel, user_id)
    
    async def _handle_client_command(self, websocket: WebSocket, command: dict):
        """Handle commands from client"""
        cmd_type = command.get("type")
        
        if cmd_type == "ping":
            await websocket.send_json({
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat()
            })
        elif cmd_type == "subscribe":
            # Handle subscription to specific metrics
            metric_type = command.get("metric")
            await websocket.send_json({
                "type": "subscribed",
                "metric": metric_type,
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            await websocket.send_json({
                "type": "error",
                "message": f"Unknown command: {cmd_type}"
            })

# Singleton instance
analytics_websocket_manager = AnalyticsWebSocketManager()