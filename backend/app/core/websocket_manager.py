"""
WebSocket Manager
Centralized WebSocket connection management for real-time features
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict

from fastapi import WebSocket, WebSocketDisconnect
from app.core.logger import get_logger

logger = get_logger(__name__)

class WebSocketConnection:
    """Individual WebSocket connection wrapper"""
    
    def __init__(self, websocket: WebSocket, connection_id: str):
        self.websocket = websocket
        self.connection_id = connection_id
        self.connected_at = datetime.utcnow()
        self.groups: Set[str] = set()
        self.metadata: Dict[str, Any] = {}
        self.last_ping = datetime.utcnow()
    
    async def send_message(self, message: Dict[str, Any]):
        """Send message to this connection"""
        try:
            await self.websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send message to {self.connection_id}: {e}")
            raise
    
    async def ping(self):
        """Send ping to connection"""
        try:
            await self.send_message({"type": "ping", "timestamp": datetime.utcnow().isoformat()})
            self.last_ping = datetime.utcnow()
        except Exception as e:
            logger.error(f"Failed to ping connection {self.connection_id}: {e}")
            raise

class WebSocketManager:
    """Centralized WebSocket connection manager"""
    
    def __init__(self):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.groups: Dict[str, Set[str]] = defaultdict(set)  # group_name -> connection_ids
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Health monitoring
        self._health_check_task = None
        self._start_health_monitoring()
    
    def _start_health_monitoring(self):
        """Start health monitoring for connections"""
        if self._health_check_task is None:
            self._health_check_task = asyncio.create_task(self._health_check_loop())
    
    async def _health_check_loop(self):
        """Health check loop for WebSocket connections"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                await self._check_connection_health()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"WebSocket health check error: {e}")
    
    async def _check_connection_health(self):
        """Check health of all connections"""
        dead_connections = []
        
        for connection_id, connection in self.connections.items():
            try:
                # Check if connection is stale
                time_since_ping = (datetime.utcnow() - connection.last_ping).total_seconds()
                
                if time_since_ping > 300:  # 5 minutes
                    dead_connections.append(connection_id)
                elif time_since_ping > 60:  # 1 minute, send ping
                    await connection.ping()
                    
            except Exception as e:
                logger.warning(f"Connection {connection_id} health check failed: {e}")
                dead_connections.append(connection_id)
        
        # Remove dead connections
        for connection_id in dead_connections:
            await self.disconnect(connection_id)
    
    async def connect(self, websocket: WebSocket, group: str = None, 
                     metadata: Dict[str, Any] = None) -> str:
        """Accept new WebSocket connection"""
        try:
            await websocket.accept()
            
            connection_id = str(uuid.uuid4())
            connection = WebSocketConnection(websocket, connection_id)
            
            if metadata:
                connection.metadata = metadata
            
            self.connections[connection_id] = connection
            
            # Add to group if specified
            if group:
                await self.add_to_group(connection_id, group)
            
            logger.info(f"WebSocket connected: {connection_id} (group: {group})")
            
            # Send welcome message
            await connection.send_message({
                "type": "welcome",
                "connection_id": connection_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return connection_id
            
        except Exception as e:
            logger.error(f"Failed to connect WebSocket: {e}")
            raise
    
    async def disconnect(self, connection_id: str):
        """Disconnect WebSocket connection"""
        try:
            if connection_id in self.connections:
                connection = self.connections[connection_id]
                
                # Remove from all groups
                for group in list(connection.groups):
                    await self.remove_from_group(connection_id, group)
                
                # Close WebSocket if still connected
                try:
                    await connection.websocket.close()
                except:
                    pass
                
                # Remove from connections
                del self.connections[connection_id]
                
                logger.info(f"WebSocket disconnected: {connection_id}")
                
        except Exception as e:
            logger.error(f"Failed to disconnect WebSocket {connection_id}: {e}")
    
    async def add_to_group(self, connection_id: str, group: str):
        """Add connection to a group"""
        try:
            if connection_id in self.connections:
                self.groups[group].add(connection_id)
                self.connections[connection_id].groups.add(group)
                
                logger.debug(f"Added connection {connection_id} to group {group}")
                
        except Exception as e:
            logger.error(f"Failed to add connection to group: {e}")
    
    async def remove_from_group(self, connection_id: str, group: str):
        """Remove connection from a group"""
        try:
            if group in self.groups:
                self.groups[group].discard(connection_id)
                if not self.groups[group]:  # Remove empty group
                    del self.groups[group]
            
            if connection_id in self.connections:
                self.connections[connection_id].groups.discard(group)
                
            logger.debug(f"Removed connection {connection_id} from group {group}")
            
        except Exception as e:
            logger.error(f"Failed to remove connection from group: {e}")
    
    async def send_to_connection(self, connection_id: str, message: Dict[str, Any]) -> bool:
        """Send message to specific connection"""
        try:
            if connection_id in self.connections:
                await self.connections[connection_id].send_message(message)
                return True
            else:
                logger.warning(f"Connection {connection_id} not found")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send message to connection {connection_id}: {e}")
            # Remove dead connection
            await self.disconnect(connection_id)
            return False
    
    async def broadcast_to_group(self, group: str, message: Dict[str, Any]) -> int:
        """Broadcast message to all connections in a group"""
        try:
            if group not in self.groups:
                logger.debug(f"Group {group} not found")
                return 0
            
            connection_ids = list(self.groups[group])
            sent_count = 0
            failed_connections = []
            
            for connection_id in connection_ids:
                try:
                    if await self.send_to_connection(connection_id, message):
                        sent_count += 1
                    else:
                        failed_connections.append(connection_id)
                except Exception as e:
                    logger.error(f"Failed to send to connection {connection_id}: {e}")
                    failed_connections.append(connection_id)
            
            # Clean up failed connections
            for connection_id in failed_connections:
                await self.disconnect(connection_id)
            
            logger.debug(f"Broadcasted to group {group}: {sent_count} connections")
            return sent_count
            
        except Exception as e:
            logger.error(f"Failed to broadcast to group {group}: {e}")
            return 0
    
    async def broadcast_to_all(self, message: Dict[str, Any]) -> int:
        """Broadcast message to all connections"""
        try:
            connection_ids = list(self.connections.keys())
            sent_count = 0
            
            for connection_id in connection_ids:
                try:
                    if await self.send_to_connection(connection_id, message):
                        sent_count += 1
                except Exception as e:
                    logger.error(f"Failed to broadcast to connection {connection_id}: {e}")
            
            logger.debug(f"Broadcasted to all connections: {sent_count}")
            return sent_count
            
        except Exception as e:
            logger.error(f"Failed to broadcast to all: {e}")
            return 0
    
    def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get connection information"""
        try:
            if connection_id in self.connections:
                connection = self.connections[connection_id]
                return {
                    "connection_id": connection_id,
                    "connected_at": connection.connected_at.isoformat(),
                    "groups": list(connection.groups),
                    "metadata": connection.metadata,
                    "last_ping": connection.last_ping.isoformat()
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get connection info: {e}")
            return None
    
    def get_group_info(self, group: str) -> Dict[str, Any]:
        """Get group information"""
        try:
            if group in self.groups:
                return {
                    "group": group,
                    "connection_count": len(self.groups[group]),
                    "connections": [
                        self.get_connection_info(conn_id)
                        for conn_id in self.groups[group]
                        if conn_id in self.connections
                    ]
                }
            return {"group": group, "connection_count": 0, "connections": []}
        except Exception as e:
            logger.error(f"Failed to get group info: {e}")
            return {"error": str(e)}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket manager statistics"""
        try:
            return {
                "total_connections": len(self.connections),
                "total_groups": len(self.groups),
                "groups": {
                    group: len(connections) 
                    for group, connections in self.groups.items()
                },
                "health_check_running": (
                    self._health_check_task is not None and 
                    not self._health_check_task.done()
                )
            }
        except Exception as e:
            logger.error(f"Failed to get WebSocket stats: {e}")
            return {"error": str(e)}
    
    async def handle_connection(self, websocket: WebSocket, group: str = None,
                              metadata: Dict[str, Any] = None):
        """Handle WebSocket connection lifecycle"""
        connection_id = None
        try:
            connection_id = await self.connect(websocket, group, metadata)
            
            # Keep connection alive and handle messages
            while True:
                try:
                    # Wait for message or connection close
                    data = await websocket.receive_text()
                    
                    # Parse and handle message
                    try:
                        message = json.loads(data)
                        await self._handle_message(connection_id, message)
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON from connection {connection_id}: {data}")
                        
                except WebSocketDisconnect:
                    logger.info(f"WebSocket disconnected normally: {connection_id}")
                    break
                except Exception as e:
                    logger.error(f"WebSocket error for {connection_id}: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
        finally:
            if connection_id:
                await self.disconnect(connection_id)
    
    async def _handle_message(self, connection_id: str, message: Dict[str, Any]):
        """Handle incoming WebSocket message"""
        try:
            message_type = message.get("type")
            
            if message_type == "ping":
                # Respond with pong
                await self.send_to_connection(connection_id, {
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Update last ping time
                if connection_id in self.connections:
                    self.connections[connection_id].last_ping = datetime.utcnow()
            
            elif message_type == "join_group":
                group = message.get("group")
                if group:
                    await self.add_to_group(connection_id, group)
                    await self.send_to_connection(connection_id, {
                        "type": "group_joined",
                        "group": group,
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            elif message_type == "leave_group":
                group = message.get("group")
                if group:
                    await self.remove_from_group(connection_id, group)
                    await self.send_to_connection(connection_id, {
                        "type": "group_left",
                        "group": group,
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            else:
                logger.debug(f"Unknown message type from {connection_id}: {message_type}")
                
        except Exception as e:
            logger.error(f"Failed to handle message from {connection_id}: {e}")

# Global WebSocket manager instance
websocket_manager = WebSocketManager()