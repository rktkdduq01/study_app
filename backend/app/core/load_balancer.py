"""
Load Balancing and Horizontal Scaling System
Advanced load balancing with health checks and auto-scaling capabilities
"""

import asyncio
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict, field
from collections import defaultdict, deque
from enum import Enum
import hashlib
import json

from app.core.logger import get_logger
from app.core.redis_client import redis_client
from app.core.config import settings

logger = get_logger(__name__)

class LoadBalancingStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    LEAST_RESPONSE_TIME = "least_response_time"
    IP_HASH = "ip_hash"
    RESOURCE_BASED = "resource_based"

class ServerStatus(Enum):
    """Server health status"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    MAINTENANCE = "maintenance"
    WARMING_UP = "warming_up"

@dataclass
class ServerNode:
    """Backend server node"""
    id: str
    host: str
    port: int
    weight: float = 1.0
    status: ServerStatus = ServerStatus.HEALTHY
    current_connections: int = 0
    max_connections: int = 1000
    response_time: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    last_health_check: Optional[datetime] = None
    consecutive_failures: int = 0
    region: str = "default"
    zone: str = "default"
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass 
class LoadBalancerConfig:
    """Load balancer configuration"""
    strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEAST_CONNECTIONS
    health_check_interval: int = 30  # seconds
    health_check_timeout: int = 5    # seconds
    max_failures: int = 3
    recovery_time: int = 60          # seconds
    sticky_sessions: bool = False
    session_affinity_ttl: int = 3600 # 1 hour
    enable_auto_scaling: bool = True
    min_instances: int = 2
    max_instances: int = 10
    scale_up_threshold: float = 0.8  # CPU/Memory threshold
    scale_down_threshold: float = 0.3

class AdvancedLoadBalancer:
    """Advanced load balancer with health checks and auto-scaling"""
    
    def __init__(self, config: LoadBalancerConfig = None):
        self.config = config or LoadBalancerConfig()
        self.servers: Dict[str, ServerNode] = {}
        self.round_robin_index = 0
        
        # Session affinity tracking
        self.session_affinity: Dict[str, str] = {}  # session_id -> server_id
        
        # Performance tracking
        self.request_metrics: deque = deque(maxlen=10000)
        self.server_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Health checking
        self._health_check_task = None
        self._auto_scaling_task = None
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_response_time": 0.0,
            "servers_added": 0,
            "servers_removed": 0
        }
        
        self._start_background_tasks()
    
    def _start_background_tasks(self):
        """Start background health check and auto-scaling tasks"""
        if self._health_check_task is None:
            self._health_check_task = asyncio.create_task(self._periodic_health_check())
        
        if self.config.enable_auto_scaling and self._auto_scaling_task is None:
            self._auto_scaling_task = asyncio.create_task(self._auto_scaling_monitor())
    
    async def add_server(self, server: ServerNode) -> bool:
        """Add server to the pool"""
        try:
            self.servers[server.id] = server
            await self._store_server_config(server)
            
            logger.info(f"Added server {server.id} ({server.host}:{server.port})")
            self.stats["servers_added"] += 1
            
            return True
        except Exception as e:
            logger.error(f"Failed to add server {server.id}: {e}")
            return False
    
    async def remove_server(self, server_id: str) -> bool:
        """Remove server from the pool"""
        try:
            if server_id in self.servers:
                server = self.servers[server_id]
                
                # Gracefully drain connections
                await self._drain_server(server_id)
                
                del self.servers[server_id]
                await redis_client.delete(f"lb_server:{server_id}")
                
                logger.info(f"Removed server {server_id}")
                self.stats["servers_removed"] += 1
                
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove server {server_id}: {e}")
            return False
    
    async def _drain_server(self, server_id: str, timeout: int = 30):
        """Gracefully drain server connections"""
        logger.info(f"Draining server {server_id}...")
        
        # Mark server as draining
        if server_id in self.servers:
            self.servers[server_id].status = ServerStatus.MAINTENANCE
        
        # Wait for connections to finish naturally
        start_time = time.time()
        while time.time() - start_time < timeout:
            if server_id in self.servers:
                if self.servers[server_id].current_connections == 0:
                    break
            await asyncio.sleep(1)
        
        logger.info(f"Server {server_id} drained")
    
    async def get_server(self, client_ip: Optional[str] = None, 
                        session_id: Optional[str] = None,
                        request_path: Optional[str] = None) -> Optional[ServerNode]:
        """Get server based on load balancing strategy"""
        try:
            # Check session affinity first
            if (self.config.sticky_sessions and session_id and 
                session_id in self.session_affinity):
                
                server_id = self.session_affinity[session_id]
                if (server_id in self.servers and 
                    self.servers[server_id].status == ServerStatus.HEALTHY):
                    return self.servers[server_id]
                else:
                    # Remove stale affinity
                    del self.session_affinity[session_id]
            
            # Get healthy servers
            healthy_servers = [
                server for server in self.servers.values()
                if server.status == ServerStatus.HEALTHY
            ]
            
            if not healthy_servers:
                logger.error("No healthy servers available")
                return None
            
            # Apply load balancing strategy
            selected_server = await self._apply_strategy(
                healthy_servers, client_ip, request_path
            )
            
            # Set session affinity if enabled
            if self.config.sticky_sessions and session_id and selected_server:
                self.session_affinity[session_id] = selected_server.id
                
                # Set TTL for session affinity
                await redis_client.setex(
                    f"session_affinity:{session_id}",
                    self.config.session_affinity_ttl,
                    selected_server.id
                )
            
            return selected_server
            
        except Exception as e:
            logger.error(f"Server selection failed: {e}")
            return None
    
    async def _apply_strategy(self, healthy_servers: List[ServerNode],
                            client_ip: Optional[str] = None,
                            request_path: Optional[str] = None) -> Optional[ServerNode]:
        """Apply load balancing strategy"""
        
        if self.config.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin_select(healthy_servers)
        
        elif self.config.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin_select(healthy_servers)
        
        elif self.config.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return self._least_connections_select(healthy_servers)
        
        elif self.config.strategy == LoadBalancingStrategy.LEAST_RESPONSE_TIME:
            return self._least_response_time_select(healthy_servers)
        
        elif self.config.strategy == LoadBalancingStrategy.IP_HASH:
            return self._ip_hash_select(healthy_servers, client_ip)
        
        elif self.config.strategy == LoadBalancingStrategy.RESOURCE_BASED:
            return self._resource_based_select(healthy_servers)
        
        else:
            return self._round_robin_select(healthy_servers)
    
    def _round_robin_select(self, servers: List[ServerNode]) -> ServerNode:
        """Round-robin server selection"""
        server = servers[self.round_robin_index % len(servers)]
        self.round_robin_index += 1
        return server
    
    def _weighted_round_robin_select(self, servers: List[ServerNode]) -> ServerNode:
        """Weighted round-robin selection"""
        total_weight = sum(server.weight for server in servers)
        if total_weight == 0:
            return self._round_robin_select(servers)
        
        # Create weighted list
        weighted_servers = []
        for server in servers:
            weight_count = max(1, int(server.weight * 10))  # Scale weights
            weighted_servers.extend([server] * weight_count)
        
        selected = weighted_servers[self.round_robin_index % len(weighted_servers)]
        self.round_robin_index += 1
        return selected
    
    def _least_connections_select(self, servers: List[ServerNode]) -> ServerNode:
        """Select server with least connections"""
        return min(servers, key=lambda s: s.current_connections)
    
    def _least_response_time_select(self, servers: List[ServerNode]) -> ServerNode:
        """Select server with least response time"""
        return min(servers, key=lambda s: s.response_time)
    
    def _ip_hash_select(self, servers: List[ServerNode], 
                       client_ip: Optional[str]) -> ServerNode:
        """IP hash-based selection for session persistence"""
        if not client_ip:
            return self._round_robin_select(servers)
        
        hash_value = int(hashlib.md5(client_ip.encode()).hexdigest(), 16)
        return servers[hash_value % len(servers)]
    
    def _resource_based_select(self, servers: List[ServerNode]) -> ServerNode:
        """Resource-based selection (CPU + Memory)"""
        def server_load(server):
            return (server.cpu_usage + server.memory_usage) / 2
        
        return min(servers, key=server_load)
    
    async def _periodic_health_check(self):
        """Periodic health check for all servers"""
        while True:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                await self._check_all_servers_health()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
    
    async def _check_all_servers_health(self):
        """Check health of all servers"""
        health_check_tasks = []
        
        for server_id, server in self.servers.items():
            task = asyncio.create_task(self._check_server_health(server))
            health_check_tasks.append(task)
        
        if health_check_tasks:
            await asyncio.gather(*health_check_tasks, return_exceptions=True)
    
    async def _check_server_health(self, server: ServerNode):
        """Check individual server health"""
        try:
            # Simulate health check (replace with actual HTTP health check)
            start_time = time.time()
            
            # This would be an actual HTTP request to server health endpoint
            # For now, simulate with basic connectivity check
            await asyncio.sleep(0.01)  # Simulate network delay
            
            response_time = time.time() - start_time
            
            # Update server metrics
            server.response_time = response_time
            server.last_health_check = datetime.utcnow()
            server.consecutive_failures = 0
            
            # Update status
            if server.status == ServerStatus.UNHEALTHY:
                logger.info(f"Server {server.id} recovered")
                server.status = ServerStatus.HEALTHY
            
            # Store health metrics
            await self._store_health_metrics(server, True, response_time)
            
        except Exception as e:
            logger.warning(f"Health check failed for server {server.id}: {e}")
            
            server.consecutive_failures += 1
            server.last_health_check = datetime.utcnow()
            
            # Mark as unhealthy if too many failures
            if server.consecutive_failures >= self.config.max_failures:
                if server.status == ServerStatus.HEALTHY:
                    logger.error(f"Server {server.id} marked as unhealthy")
                    server.status = ServerStatus.UNHEALTHY
            
            await self._store_health_metrics(server, False, 0)
    
    async def _store_health_metrics(self, server: ServerNode, 
                                  healthy: bool, response_time: float):
        """Store health metrics in Redis"""
        try:
            metric = {
                "server_id": server.id,
                "timestamp": datetime.utcnow().isoformat(),
                "healthy": healthy,
                "response_time": response_time,
                "cpu_usage": server.cpu_usage,
                "memory_usage": server.memory_usage,
                "connections": server.current_connections
            }
            
            key = f"health_metrics:{server.id}:{datetime.utcnow().strftime('%Y%m%d')}"
            await redis_client.lpush(key, json.dumps(metric))
            await redis_client.expire(key, 86400 * 7)  # Keep for 7 days
            
        except Exception as e:
            logger.error(f"Failed to store health metrics: {e}")
    
    async def _store_server_config(self, server: ServerNode):
        """Store server configuration in Redis"""
        try:
            server_data = asdict(server)
            server_data['last_health_check'] = (
                server.last_health_check.isoformat() 
                if server.last_health_check else None
            )
            server_data['status'] = server.status.value
            
            await redis_client.setex(
                f"lb_server:{server.id}",
                3600,  # 1 hour TTL
                json.dumps(server_data)
            )
            
        except Exception as e:
            logger.error(f"Failed to store server config: {e}")
    
    async def _auto_scaling_monitor(self):
        """Monitor system load and trigger auto-scaling"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self._evaluate_scaling_needs()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Auto-scaling monitor error: {e}")
    
    async def _evaluate_scaling_needs(self):
        """Evaluate if scaling up or down is needed"""
        try:
            healthy_servers = [
                s for s in self.servers.values() 
                if s.status == ServerStatus.HEALTHY
            ]
            
            if not healthy_servers:
                return
            
            # Calculate average resource usage
            avg_cpu = sum(s.cpu_usage for s in healthy_servers) / len(healthy_servers)
            avg_memory = sum(s.memory_usage for s in healthy_servers) / len(healthy_servers)
            avg_load = (avg_cpu + avg_memory) / 2
            
            current_count = len(healthy_servers)
            
            # Scale up if load is high and we can add more servers
            if (avg_load > self.config.scale_up_threshold and 
                current_count < self.config.max_instances):
                
                logger.info(f"Triggering scale-up: load={avg_load:.2%}, servers={current_count}")
                await self._trigger_scale_up()
            
            # Scale down if load is low and we have more than minimum servers
            elif (avg_load < self.config.scale_down_threshold and 
                  current_count > self.config.min_instances):
                
                logger.info(f"Triggering scale-down: load={avg_load:.2%}, servers={current_count}")
                await self._trigger_scale_down()
            
        except Exception as e:
            logger.error(f"Scaling evaluation failed: {e}")
    
    async def _trigger_scale_up(self):
        """Trigger scale-up by adding a new server"""
        try:
            # This would integrate with cloud provider APIs or container orchestration
            # For now, simulate adding a new server
            
            new_server_id = f"auto-{int(time.time())}"
            new_server = ServerNode(
                id=new_server_id,
                host=f"app-{new_server_id}",
                port=8000,
                weight=1.0,
                status=ServerStatus.WARMING_UP,
                tags={"auto_scaled": "true"}
            )
            
            await self.add_server(new_server)
            
            # Simulate server warming up
            asyncio.create_task(self._warm_up_server(new_server_id))
            
            logger.info(f"Auto-scaled up: added server {new_server_id}")
            
        except Exception as e:
            logger.error(f"Scale-up failed: {e}")
    
    async def _trigger_scale_down(self):
        """Trigger scale-down by removing a server"""
        try:
            # Find auto-scaled servers to remove
            auto_scaled_servers = [
                s for s in self.servers.values()
                if s.tags.get("auto_scaled") == "true" and s.status == ServerStatus.HEALTHY
            ]
            
            if auto_scaled_servers:
                # Remove server with least connections
                server_to_remove = min(auto_scaled_servers, 
                                     key=lambda s: s.current_connections)
                
                await self.remove_server(server_to_remove.id)
                logger.info(f"Auto-scaled down: removed server {server_to_remove.id}")
            
        except Exception as e:
            logger.error(f"Scale-down failed: {e}")
    
    async def _warm_up_server(self, server_id: str):
        """Warm up newly added server"""
        try:
            # Wait for server to be ready
            await asyncio.sleep(30)  # Simulate warm-up time
            
            if server_id in self.servers:
                self.servers[server_id].status = ServerStatus.HEALTHY
                logger.info(f"Server {server_id} warmed up and ready")
            
        except Exception as e:
            logger.error(f"Server warm-up failed for {server_id}: {e}")
    
    async def record_request(self, server_id: str, response_time: float, 
                           success: bool):
        """Record request metrics"""
        try:
            self.stats["total_requests"] += 1
            if success:
                self.stats["successful_requests"] += 1
            else:
                self.stats["failed_requests"] += 1
            
            self.stats["total_response_time"] += response_time
            
            # Update server metrics
            if server_id in self.servers:
                server = self.servers[server_id]
                server.response_time = response_time
                
                # Update connection count (simplified)
                if success:
                    server.current_connections = max(0, server.current_connections)
            
            # Store request metrics
            metric = {
                "server_id": server_id,
                "timestamp": datetime.utcnow().isoformat(),
                "response_time": response_time,
                "success": success
            }
            
            self.request_metrics.append(metric)
            
        except Exception as e:
            logger.error(f"Failed to record request metrics: {e}")
    
    def get_load_balancer_stats(self) -> Dict[str, Any]:
        """Get load balancer statistics"""
        healthy_servers = [
            s for s in self.servers.values() 
            if s.status == ServerStatus.HEALTHY
        ]
        
        total_requests = self.stats["total_requests"]
        avg_response_time = (
            self.stats["total_response_time"] / total_requests 
            if total_requests > 0 else 0
        )
        
        return {
            "strategy": self.config.strategy.value,
            "total_servers": len(self.servers),
            "healthy_servers": len(healthy_servers),
            "unhealthy_servers": len([
                s for s in self.servers.values() 
                if s.status == ServerStatus.UNHEALTHY
            ]),
            "total_requests": total_requests,
            "success_rate": (
                self.stats["successful_requests"] / total_requests * 100
                if total_requests > 0 else 0
            ),
            "average_response_time": avg_response_time,
            "servers_added": self.stats["servers_added"],
            "servers_removed": self.stats["servers_removed"],
            "session_affinities": len(self.session_affinity),
            "auto_scaling_enabled": self.config.enable_auto_scaling,
            "servers": [
                {
                    "id": s.id,
                    "host": s.host,
                    "port": s.port,
                    "status": s.status.value,
                    "connections": s.current_connections,
                    "response_time": s.response_time,
                    "cpu_usage": s.cpu_usage,
                    "memory_usage": s.memory_usage,
                    "weight": s.weight
                }
                for s in self.servers.values()
            ]
        }

# Global load balancer instance
load_balancer_config = LoadBalancerConfig(
    strategy=LoadBalancingStrategy(getattr(settings, 'LB_STRATEGY', 'least_connections')),
    health_check_interval=getattr(settings, 'LB_HEALTH_CHECK_INTERVAL', 30),
    sticky_sessions=getattr(settings, 'LB_STICKY_SESSIONS', False),
    enable_auto_scaling=getattr(settings, 'LB_AUTO_SCALING', True),
    min_instances=getattr(settings, 'LB_MIN_INSTANCES', 2),
    max_instances=getattr(settings, 'LB_MAX_INSTANCES', 10)
)

load_balancer = AdvancedLoadBalancer(load_balancer_config)

# Utility functions
async def register_server(host: str, port: int, weight: float = 1.0, 
                         region: str = "default", **kwargs) -> bool:
    """Register a new server with the load balancer"""
    server_id = f"{host}:{port}"
    server = ServerNode(
        id=server_id,
        host=host,
        port=port,
        weight=weight,
        region=region,
        **kwargs
    )
    
    return await load_balancer.add_server(server)

async def unregister_server(host: str, port: int) -> bool:
    """Unregister server from the load balancer"""
    server_id = f"{host}:{port}"
    return await load_balancer.remove_server(server_id)

async def get_backend_server(client_ip: str = None, session_id: str = None,
                           request_path: str = None) -> Optional[ServerNode]:
    """Get backend server for request"""
    return await load_balancer.get_server(client_ip, session_id, request_path)

async def record_backend_request(server_id: str, response_time: float, 
                                success: bool):
    """Record backend request metrics"""
    await load_balancer.record_request(server_id, response_time, success)