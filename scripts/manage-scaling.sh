#!/bin/bash

# Horizontal Scaling Management Script
# Usage: ./scripts/manage-scaling.sh [command] [options]
# Example: ./scripts/manage-scaling.sh scale-up --instances 3

set -e

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
BACKEND_DIR="$PROJECT_ROOT/backend"
LOG_DIR="$PROJECT_ROOT/logs/scaling"
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"

# Command and options
COMMAND=${1:-status}
INSTANCES=${2:-1}
FORCE=${3:-false}

# Logging
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/scaling-$(date +%Y%m%d_%H%M%S).log"

log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

log "${BLUE}${BOLD}🚀 Horizontal Scaling Manager${NC}"
log "${BLUE}Command: $COMMAND${NC}"
log "${BLUE}Log File: $LOG_FILE${NC}"
log ""

# Load environment
load_environment() {
    if [ -f "$PROJECT_ROOT/scripts/load-env.sh" ]; then
        source "$PROJECT_ROOT/scripts/load-env.sh" "${ENVIRONMENT:-development}"
    fi
    
    # Set scaling configuration based on environment
    case ${ENVIRONMENT:-development} in
        "production")
            MIN_INSTANCES=3
            MAX_INSTANCES=20
            SCALE_THRESHOLD=80
            ;;
        "staging")
            MIN_INSTANCES=2
            MAX_INSTANCES=10
            SCALE_THRESHOLD=70
            ;;
        "development")
            MIN_INSTANCES=1
            MAX_INSTANCES=5
            SCALE_THRESHOLD=90
            ;;
    esac
}

# Get current scaling status
get_scaling_status() {
    log "${YELLOW}📊 Getting Scaling Status${NC}"
    
    # Check Docker containers
    if command -v docker &> /dev/null; then
        local running_containers
        running_containers=$(docker ps --filter "name=backend" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "")
        
        if [ -n "$running_containers" ]; then
            log "🐳 Docker Containers:"
            echo "$running_containers" | tee -a "$LOG_FILE"
            
            local container_count
            container_count=$(docker ps --filter "name=backend" --quiet | wc -l)
            log "Total Backend Instances: $container_count"
        else
            log "No Docker containers found"
        fi
    fi
    
    # Check if using Kubernetes
    if command -v kubectl &> /dev/null; then
        local k8s_pods
        k8s_pods=$(kubectl get pods -l app=quest-edu-backend 2>/dev/null || echo "")
        
        if [ -n "$k8s_pods" ]; then
            log "☸️  Kubernetes Pods:"
            echo "$k8s_pods" | tee -a "$LOG_FILE"
            
            local pod_count
            pod_count=$(kubectl get pods -l app=quest-edu-backend --no-headers 2>/dev/null | wc -l)
            log "Total Kubernetes Pods: $pod_count"
        fi
    fi
    
    # Get load balancer status
    get_load_balancer_status
}

# Get load balancer status
get_load_balancer_status() {
    log "${YELLOW}⚖️  Load Balancer Status${NC}"
    
    cd "$BACKEND_DIR"
    
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    elif [ -d "venv_backend" ]; then
        source venv_backend/bin/activate
    fi
    
    python << EOF
import sys
import os
import asyncio
import json

# Add the backend directory to Python path
sys.path.insert(0, os.getcwd())

try:
    from app.core.load_balancer import load_balancer
    
    async def get_lb_status():
        stats = load_balancer.get_load_balancer_stats()
        
        print(f"Load Balancing Strategy: {stats['strategy']}")
        print(f"Total Servers: {stats['total_servers']}")
        print(f"Healthy Servers: {stats['healthy_servers']}")
        print(f"Unhealthy Servers: {stats['unhealthy_servers']}")
        print(f"Total Requests: {stats['total_requests']}")
        print(f"Success Rate: {stats['success_rate']:.2f}%")
        print(f"Average Response Time: {stats['average_response_time']:.3f}s")
        
        if stats['servers']:
            print("\nServer Details:")
            for server in stats['servers']:
                status_icon = "✅" if server['status'] == 'healthy' else "❌"
                print(f"  {status_icon} {server['id']} - {server['host']}:{server['port']}")
                print(f"    Status: {server['status']}")
                print(f"    Connections: {server['connections']}")
                print(f"    Response Time: {server['response_time']:.3f}s")
                print(f"    CPU: {server['cpu_usage']:.1%}, Memory: {server['memory_usage']:.1%}")
                print()
        
        return True
    
    success = asyncio.run(get_lb_status())
    sys.exit(0 if success else 1)

except ImportError as e:
    print(f"❌ Failed to import load balancer: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Load balancer status check failed: {e}")
    sys.exit(1)
EOF

    cd "$PROJECT_ROOT"
}

# Scale up instances
scale_up() {
    log "${GREEN}📈 Scaling Up${NC}"
    
    local target_instances=${INSTANCES:-1}
    
    if [ "$target_instances" -lt 1 ]; then
        log "${RED}❌ Invalid number of instances: $target_instances${NC}"
        return 1
    fi
    
    if [ "$target_instances" -gt "$MAX_INSTANCES" ]; then
        log "${RED}❌ Target instances ($target_instances) exceeds maximum ($MAX_INSTANCES)${NC}"
        return 1
    fi
    
    log "Target instances: $target_instances"
    
    # Scale using Docker Compose
    if [ -f "$DOCKER_COMPOSE_FILE" ]; then
        scale_with_docker_compose "$target_instances"
    elif command -v kubectl &> /dev/null; then
        scale_with_kubernetes "$target_instances"
    else
        scale_manually "$target_instances"
    fi
}

# Scale down instances
scale_down() {
    log "${YELLOW}📉 Scaling Down${NC}"
    
    local target_instances=${INSTANCES:-1}
    
    if [ "$target_instances" -lt "$MIN_INSTANCES" ]; then
        log "${RED}❌ Target instances ($target_instances) below minimum ($MIN_INSTANCES)${NC}"
        return 1
    fi
    
    log "Target instances: $target_instances"
    
    # Scale using Docker Compose
    if [ -f "$DOCKER_COMPOSE_FILE" ]; then
        scale_with_docker_compose "$target_instances"
    elif command -v kubectl &> /dev/null; then
        scale_with_kubernetes "$target_instances"
    else
        log "${YELLOW}⚠️  Manual scaling down not implemented${NC}"
        return 1
    fi
}

# Scale with Docker Compose
scale_with_docker_compose() {
    local instances="$1"
    
    log "${BLUE}🐳 Scaling with Docker Compose${NC}"
    
    if ! command -v docker-compose &> /dev/null && ! command -v docker &> /dev/null; then
        log "${RED}❌ Docker Compose not found${NC}"
        return 1
    fi
    
    # Use docker-compose or docker compose
    local compose_cmd="docker-compose"
    if ! command -v docker-compose &> /dev/null; then
        compose_cmd="docker compose"
    fi
    
    # Scale the backend service
    if $compose_cmd -f "$DOCKER_COMPOSE_FILE" up -d --scale backend="$instances" >> "$LOG_FILE" 2>&1; then
        log "${GREEN}✅ Scaled backend to $instances instances${NC}"
        
        # Wait for containers to be ready
        log "Waiting for containers to be ready..."
        sleep 10
        
        # Verify scaling
        local running_count
        running_count=$(docker ps --filter "name=backend" --quiet | wc -l)
        log "Running instances: $running_count"
        
        # Register new instances with load balancer
        register_instances_with_lb
        
    else
        log "${RED}❌ Failed to scale with Docker Compose${NC}"
        return 1
    fi
}

# Scale with Kubernetes
scale_with_kubernetes() {
    local instances="$1"
    
    log "${BLUE}☸️  Scaling with Kubernetes${NC}"
    
    if ! command -v kubectl &> /dev/null; then
        log "${RED}❌ kubectl not found${NC}"
        return 1
    fi
    
    # Scale the deployment
    if kubectl scale deployment quest-edu-backend --replicas="$instances" >> "$LOG_FILE" 2>&1; then
        log "${GREEN}✅ Scaled Kubernetes deployment to $instances replicas${NC}"
        
        # Wait for rollout to complete
        log "Waiting for rollout to complete..."
        kubectl rollout status deployment/quest-edu-backend --timeout=300s >> "$LOG_FILE" 2>&1
        
        # Verify scaling
        local ready_pods
        ready_pods=$(kubectl get pods -l app=quest-edu-backend --field-selector=status.phase=Running --no-headers | wc -l)
        log "Ready pods: $ready_pods"
        
    else
        log "${RED}❌ Failed to scale Kubernetes deployment${NC}"
        return 1
    fi
}

# Manual scaling (for development)
scale_manually() {
    local instances="$1"
    
    log "${BLUE}🔧 Manual Scaling${NC}"
    log "Starting $instances backend instances manually..."
    
    # This would implement manual instance management
    # For now, just log the action
    for ((i=1; i<=instances; i++)); do
        local port=$((8000 + i))
        log "Would start instance $i on port $port"
        
        # In a real implementation, this would:
        # 1. Start new Python process on different port
        # 2. Register with load balancer
        # 3. Wait for health checks to pass
    done
    
    log "${GREEN}✅ Manual scaling simulation completed${NC}"
}

# Register instances with load balancer
register_instances_with_lb() {
    log "${YELLOW}🔗 Registering instances with load balancer${NC}"
    
    cd "$BACKEND_DIR"
    
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    elif [ -d "venv_backend" ]; then
        source venv_backend/bin/activate
    fi
    
    python << EOF
import sys
import os
import asyncio
import docker

# Add the backend directory to Python path
sys.path.insert(0, os.getcwd())

try:
    from app.core.load_balancer import load_balancer, register_server
    
    async def register_containers():
        # Get Docker client
        client = docker.from_env()
        
        # Find backend containers
        containers = client.containers.list(filters={"name": "backend"})
        
        registered_count = 0
        for container in containers:
            try:
                # Get container info
                container_name = container.name
                container_ip = container.attrs['NetworkSettings']['IPAddress']
                
                # Default port (could be extracted from container config)
                port = 8000
                
                # Register with load balancer
                success = await register_server(
                    host=container_ip,
                    port=port,
                    weight=1.0,
                    region="docker",
                    tags={"container_id": container.id[:12], "container_name": container_name}
                )
                
                if success:
                    print(f"✅ Registered {container_name} ({container_ip}:{port})")
                    registered_count += 1
                else:
                    print(f"❌ Failed to register {container_name}")
                    
            except Exception as e:
                print(f"❌ Error registering container {container.name}: {e}")
        
        print(f"Registered {registered_count} instances with load balancer")
        return registered_count > 0
    
    success = asyncio.run(register_containers())
    sys.exit(0 if success else 1)

except ImportError as e:
    print(f"⚠️  Load balancer registration skipped: {e}")
    sys.exit(0)
except Exception as e:
    print(f"❌ Registration failed: {e}")
    sys.exit(1)
EOF

    cd "$PROJECT_ROOT"
}

# Auto-scale based on metrics
auto_scale() {
    log "${CYAN}🤖 Auto-scaling Analysis${NC}"
    
    cd "$BACKEND_DIR"
    
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    elif [ -d "venv_backend" ]; then
        source venv_backend/bin/activate
    fi
    
    python << EOF
import sys
import os
import asyncio
import time

# Add the backend directory to Python path
sys.path.insert(0, os.getcwd())

try:
    from app.core.load_balancer import load_balancer
    from app.core.api_optimizer import api_optimizer
    
    async def analyze_and_scale():
        print("🔍 Analyzing system metrics...")
        
        # Get current metrics
        lb_stats = load_balancer.get_load_balancer_stats()
        api_stats = api_optimizer.get_performance_stats()
        
        healthy_servers = lb_stats['healthy_servers']
        avg_response_time = api_stats.get('avg_response_time_ms', 0)
        error_rate = api_stats.get('error_rate', 0)
        recent_requests = api_stats.get('recent_requests', 0)
        
        print(f"Current healthy servers: {healthy_servers}")
        print(f"Average response time: {avg_response_time:.2f}ms")
        print(f"Error rate: {error_rate:.2f}%")
        print(f"Recent requests (5min): {recent_requests}")
        
        # Scaling decision logic
        scale_up_needed = False
        scale_down_needed = False
        
        # Scale up conditions
        if avg_response_time > 1000:  # > 1 second
            print("⚠️  High response time detected")
            scale_up_needed = True
        
        if error_rate > 5:  # > 5% error rate
            print("⚠️  High error rate detected")
            scale_up_needed = True
        
        if recent_requests > 100 and healthy_servers < 3:
            print("⚠️  High traffic with few servers")
            scale_up_needed = True
        
        # Scale down conditions
        if (avg_response_time < 200 and error_rate < 1 and 
            recent_requests < 20 and healthy_servers > 2):
            print("ℹ️  Low utilization detected")
            scale_down_needed = True
        
        # Make scaling recommendation
        if scale_up_needed and not scale_down_needed:
            recommended_instances = min(healthy_servers + 1, int(os.getenv('MAX_INSTANCES', '10')))
            print(f"🔥 RECOMMENDATION: Scale UP to {recommended_instances} instances")
            print("   Reasons: High load detected")
            return "scale_up", recommended_instances
            
        elif scale_down_needed and not scale_up_needed:
            recommended_instances = max(healthy_servers - 1, int(os.getenv('MIN_INSTANCES', '2')))
            print(f"🔥 RECOMMENDATION: Scale DOWN to {recommended_instances} instances")
            print("   Reasons: Low utilization")
            return "scale_down", recommended_instances
            
        else:
            print("✅ RECOMMENDATION: No scaling needed")
            print("   Current configuration is optimal")
            return "no_action", healthy_servers
    
    try:
        action, instances = asyncio.run(analyze_and_scale())
        
        # Output recommendation in a format the shell script can parse
        print(f"SCALING_ACTION={action}")
        print(f"RECOMMENDED_INSTANCES={instances}")
        
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ Auto-scaling analysis failed: {e}")
        sys.exit(1)

except ImportError as e:
    print(f"❌ Failed to import required modules: {e}")
    sys.exit(1)
EOF

    # Parse Python output
    local python_output
    python_output=$(python << 'EOF'
import sys
import os
import asyncio

sys.path.insert(0, os.getcwd())

try:
    from app.core.load_balancer import load_balancer
    from app.core.api_optimizer import api_optimizer
    
    async def analyze():
        lb_stats = load_balancer.get_load_balancer_stats()
        api_stats = api_optimizer.get_performance_stats()
        
        healthy_servers = lb_stats['healthy_servers']
        avg_response_time = api_stats.get('avg_response_time_ms', 0)
        error_rate = api_stats.get('error_rate', 0)
        
        if avg_response_time > 1000 or error_rate > 5:
            action = "scale_up"
            instances = min(healthy_servers + 1, 10)
        elif avg_response_time < 200 and error_rate < 1 and healthy_servers > 2:
            action = "scale_down" 
            instances = max(healthy_servers - 1, 2)
        else:
            action = "no_action"
            instances = healthy_servers
            
        print(f"{action}:{instances}")
        return True
    
    asyncio.run(analyze())
except:
    print("no_action:2")
EOF
)
    
    IFS=':' read -r scaling_action recommended_instances <<< "$python_output"
    
    if [ "$scaling_action" = "scale_up" ]; then
        log "${GREEN}🚀 Auto-scaling recommendation: Scale UP to $recommended_instances instances${NC}"
        if [ "$FORCE" = "--force" ]; then
            INSTANCES="$recommended_instances"
            scale_up
        else
            log "Run with --force to execute auto-scaling"
        fi
    elif [ "$scaling_action" = "scale_down" ]; then
        log "${YELLOW}📉 Auto-scaling recommendation: Scale DOWN to $recommended_instances instances${NC}"
        if [ "$FORCE" = "--force" ]; then
            INSTANCES="$recommended_instances"
            scale_down
        else
            log "Run with --force to execute auto-scaling"
        fi
    else
        log "${GREEN}✅ No scaling action needed${NC}"
    fi
    
    cd "$PROJECT_ROOT"
}

# Monitor scaling metrics
monitor_scaling() {
    log "${CYAN}📊 Monitoring Scaling Metrics${NC}"
    log "Press Ctrl+C to stop monitoring"
    log ""
    
    while true; do
        clear
        echo -e "${CYAN}${BOLD}📊 Scaling Metrics Dashboard - $(date)${NC}"
        echo -e "${CYAN}════════════════════════════════════════════${NC}"
        echo ""
        
        # Get current status
        get_scaling_status 2>/dev/null
        
        echo ""
        echo -e "${YELLOW}Refreshing in 30 seconds... (Ctrl+C to stop)${NC}"
        sleep 30
    done
}

# Health check for scaled instances
health_check() {
    log "${YELLOW}🏥 Health Check for Scaled Instances${NC}"
    
    # Check Docker containers
    if command -v docker &> /dev/null; then
        local containers
        containers=$(docker ps --filter "name=backend" --format "{{.Names}}" 2>/dev/null || echo "")
        
        if [ -n "$containers" ]; then
            echo "$containers" | while read -r container; do
                if [ -n "$container" ]; then
                    local container_ip
                    container_ip=$(docker inspect "$container" --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' 2>/dev/null || echo "unknown")
                    
                    local health_url="http://${container_ip}:8000/health"
                    
                    if curl -s --max-time 5 "$health_url" > /dev/null 2>&1; then
                        log "${GREEN}✅ $container ($container_ip) - Healthy${NC}"
                    else
                        log "${RED}❌ $container ($container_ip) - Unhealthy${NC}"
                    fi
                fi
            done
        else
            log "No backend containers found"
        fi
    fi
}

# Main execution
main() {
    load_environment
    
    case $COMMAND in
        "status")
            get_scaling_status
            ;;
            
        "scale-up")
            scale_up
            ;;
            
        "scale-down")
            scale_down
            ;;
            
        "auto-scale")
            auto_scale
            ;;
            
        "monitor")
            monitor_scaling
            ;;
            
        "health-check")
            health_check
            ;;
            
        "help"|"-h"|"--help")
            cat << EOF

Horizontal Scaling Management Script

Usage: $0 [command] [instances] [options]

Commands:
  status          Show current scaling status (default)
  scale-up        Scale up to specified number of instances  
  scale-down      Scale down to specified number of instances
  auto-scale      Analyze metrics and recommend scaling
  monitor         Monitor scaling metrics in real-time
  health-check    Check health of all scaled instances
  help            Show this help message

Options:
  --force         Execute auto-scaling recommendations without prompt

Examples:
  $0 status
  $0 scale-up 5
  $0 scale-down 2
  $0 auto-scale --force
  $0 monitor
  $0 health-check

Environment Variables:
  MIN_INSTANCES     Minimum number of instances (default: varies by env)
  MAX_INSTANCES     Maximum number of instances (default: varies by env)
  SCALE_THRESHOLD   CPU/Memory threshold for scaling (default: varies by env)

Scaling Targets:
  Development: 1-5 instances (90% threshold)
  Staging:     2-10 instances (70% threshold)  
  Production:  3-20 instances (80% threshold)

EOF
            ;;
            
        *)
            log "${RED}❌ Unknown command: $COMMAND${NC}"
            log "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Execute main function
if main; then
    if [ "$COMMAND" != "monitor" ]; then
        log ""
        log "${GREEN}✅ Scaling management completed${NC}"
        log "${BLUE}📄 Log file: $LOG_FILE${NC}"
    fi
    exit 0
else
    log ""
    log "${RED}❌ Scaling management failed${NC}"
    log "${BLUE}📄 Check log file: $LOG_FILE${NC}"
    exit 1
fi