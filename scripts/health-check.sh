#!/bin/bash

# Health Check Script for Quest Education Platform
# Usage: ./scripts/health-check.sh [environment] [timeout]
# Example: ./scripts/health-check.sh production 30

set -e

# Parameters
ENV=${1:-development}
TIMEOUT=${2:-30}

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🏥 Starting health check for environment: $ENV${NC}"

# Load environment configuration
if [ -f "$PROJECT_ROOT/scripts/load-env.sh" ]; then
    source "$PROJECT_ROOT/scripts/load-env.sh" "$ENV"
else
    echo -e "${RED}❌ Environment loader not found${NC}"
    exit 1
fi

# Health check counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# Health check function
health_check() {
    local service_name="$1"
    local check_url="$2"
    local expected_status="$3"
    local description="$4"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    echo -e "\n${BLUE}🔍 Checking $service_name: $description${NC}"
    
    # Perform health check with timeout
    if timeout "$TIMEOUT" curl -sSf "$check_url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $service_name is healthy${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        echo -e "${RED}❌ $service_name health check failed${NC}"
        echo -e "${RED}   URL: $check_url${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        
        # Try to get more details
        echo -e "${YELLOW}   Attempting detailed check...${NC}"
        HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$check_url" || echo "000")
        echo -e "${YELLOW}   HTTP Status: $HTTP_STATUS${NC}"
    fi
}

# Database health check
db_health_check() {
    local service_name="$1"
    local host="$2"
    local port="$3"
    local user="$4"
    local database="$5"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    echo -e "\n${BLUE}🔍 Checking $service_name database connection${NC}"
    
    # Check if we can connect to the database
    if timeout "$TIMEOUT" pg_isready -h "$host" -p "$port" -U "$user" -d "$database" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $service_name database is accessible${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        echo -e "${RED}❌ $service_name database connection failed${NC}"
        echo -e "${RED}   Host: $host:$port${NC}"
        echo -e "${RED}   Database: $database${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
}

# Redis health check
redis_health_check() {
    local service_name="$1"
    local host="$2"
    local port="$3"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    echo -e "\n${BLUE}🔍 Checking $service_name Redis connection${NC}"
    
    # Check if we can ping Redis
    if timeout "$TIMEOUT" redis-cli -h "$host" -p "$port" ping > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $service_name Redis is accessible${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        echo -e "${RED}❌ $service_name Redis connection failed${NC}"
        echo -e "${RED}   Host: $host:$port${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
}

# Service availability check
service_check() {
    local service_name="$1"
    local host="$2"
    local port="$3"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    echo -e "\n${BLUE}🔍 Checking $service_name service availability${NC}"
    
    # Check if port is open
    if timeout "$TIMEOUT" nc -z "$host" "$port" 2>/dev/null; then
        echo -e "${GREEN}✅ $service_name is listening on $host:$port${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        echo -e "${RED}❌ $service_name is not accessible on $host:$port${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
}

# Docker service health check
docker_health_check() {
    local service_name="$1"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    echo -e "\n${BLUE}🔍 Checking Docker service: $service_name${NC}"
    
    # Check if Docker service is running and healthy
    if docker-compose ps "$service_name" | grep -q "Up (healthy)"; then
        echo -e "${GREEN}✅ Docker service $service_name is healthy${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    elif docker-compose ps "$service_name" | grep -q "Up"; then
        echo -e "${YELLOW}⚠️  Docker service $service_name is running but health check not configured${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        echo -e "${RED}❌ Docker service $service_name is not running properly${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        
        # Show service logs
        echo -e "${YELLOW}   Last 10 lines of logs:${NC}"
        docker-compose logs --tail=10 "$service_name" 2>/dev/null || echo "   No logs available"
    fi
}

# Start health checks
echo -e "${BLUE}🏁 Starting comprehensive health checks...${NC}"

# API Health Checks
if [ -n "$VITE_API_URL" ]; then
    health_check "Backend API" "$VITE_API_URL/health" "200" "API health endpoint"
    health_check "Backend API Docs" "$VITE_API_URL/docs" "200" "API documentation"
fi

# Frontend Health Checks
if [ -n "$FRONTEND_URL" ]; then
    health_check "Frontend" "$FRONTEND_URL" "200" "Frontend application"
fi

# Database Health Checks
if [ -n "$POSTGRES_HOST" ] && [ -n "$POSTGRES_PORT" ]; then
    # Check if pg_isready is available
    if command -v pg_isready &> /dev/null; then
        db_health_check "PostgreSQL" "$POSTGRES_HOST" "$POSTGRES_PORT" "${POSTGRES_USER:-postgres}" "${POSTGRES_DB:-quest_edu}"
    else
        service_check "PostgreSQL" "$POSTGRES_HOST" "$POSTGRES_PORT"
    fi
fi

# Redis Health Checks
if [ -n "$REDIS_HOST" ] && [ -n "$REDIS_PORT" ]; then
    # Check if redis-cli is available
    if command -v redis-cli &> /dev/null; then
        redis_health_check "Redis" "$REDIS_HOST" "$REDIS_PORT"
    else
        service_check "Redis" "$REDIS_HOST" "$REDIS_PORT"
    fi
fi

# WebSocket Health Check
if [ -n "$VITE_WEBSOCKET_URL" ]; then
    # Convert WebSocket URL to HTTP for health check
    WS_HTTP_URL=$(echo "$VITE_WEBSOCKET_URL" | sed 's/wss:/https:/' | sed 's/ws:/http:/')
    health_check "WebSocket" "$WS_HTTP_URL/health" "200" "WebSocket service"
fi

# Docker Services Health Check (if using Docker)
if command -v docker-compose &> /dev/null && [ -f "$PROJECT_ROOT/docker-compose.yml" ]; then
    echo -e "\n${BLUE}🐳 Checking Docker services...${NC}"
    
    # Get list of services from docker-compose
    SERVICES=$(docker-compose config --services 2>/dev/null || true)
    
    if [ -n "$SERVICES" ]; then
        for service in $SERVICES; do
            docker_health_check "$service"
        done
    else
        echo -e "${YELLOW}⚠️  No Docker services found or docker-compose not available${NC}"
    fi
fi

# Environment-specific checks
case $ENV in
    "production")
        echo -e "\n${BLUE}🚀 Production-specific health checks${NC}"
        
        # SSL certificate check
        if [ -n "$FRONTEND_URL" ] && [[ "$FRONTEND_URL" == https://* ]]; then
            DOMAIN=$(echo "$FRONTEND_URL" | sed 's|https://||' | sed 's|/.*||')
            
            TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
            echo -e "\n${BLUE}🔍 Checking SSL certificate for $DOMAIN${NC}"
            
            # Check SSL certificate expiry
            SSL_EXPIRY=$(echo | openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
            
            if [ -n "$SSL_EXPIRY" ]; then
                SSL_EXPIRY_EPOCH=$(date -d "$SSL_EXPIRY" +%s 2>/dev/null || date -j -f "%b %d %H:%M:%S %Y %Z" "$SSL_EXPIRY" +%s 2>/dev/null)
                CURRENT_EPOCH=$(date +%s)
                DAYS_UNTIL_EXPIRY=$(( (SSL_EXPIRY_EPOCH - CURRENT_EPOCH) / 86400 ))
                
                if [ $DAYS_UNTIL_EXPIRY -gt 30 ]; then
                    echo -e "${GREEN}✅ SSL certificate is valid (expires in $DAYS_UNTIL_EXPIRY days)${NC}"
                    PASSED_CHECKS=$((PASSED_CHECKS + 1))
                elif [ $DAYS_UNTIL_EXPIRY -gt 0 ]; then
                    echo -e "${YELLOW}⚠️  SSL certificate expires soon ($DAYS_UNTIL_EXPIRY days)${NC}"
                    PASSED_CHECKS=$((PASSED_CHECKS + 1))
                else
                    echo -e "${RED}❌ SSL certificate has expired${NC}"
                    FAILED_CHECKS=$((FAILED_CHECKS + 1))
                fi
            else
                echo -e "${RED}❌ Could not retrieve SSL certificate information${NC}"
                FAILED_CHECKS=$((FAILED_CHECKS + 1))
            fi
        fi
        
        # Monitoring services check
        if [ -n "$ENABLE_METRICS" ] && [ "$ENABLE_METRICS" = "true" ]; then
            health_check "Prometheus" "http://localhost:9090/-/healthy" "200" "Metrics collection"
            health_check "Grafana" "http://localhost:3001/api/health" "200" "Monitoring dashboard"
        fi
        ;;
        
    "staging")
        echo -e "\n${BLUE}🧪 Staging-specific health checks${NC}"
        
        # Check if staging database is isolated from production
        if [ -n "$POSTGRES_DB" ] && [[ "$POSTGRES_DB" == *"staging"* ]]; then
            echo -e "${GREEN}✅ Using staging database${NC}"
        else
            echo -e "${YELLOW}⚠️  Database name doesn't indicate staging environment${NC}"
        fi
        ;;
        
    "development")
        echo -e "\n${BLUE}🛠️  Development-specific health checks${NC}"
        
        # Check for development tools
        if [ "$DEBUG" = "true" ]; then
            echo -e "${GREEN}✅ Debug mode is enabled${NC}"
        else
            echo -e "${YELLOW}⚠️  Debug mode is disabled in development${NC}"
        fi
        ;;
esac

# Check external dependencies
echo -e "\n${BLUE}🌐 External Dependencies Health Check${NC}"

# OpenAI API (if configured)
if [ -n "$OPENAI_API_KEY" ]; then
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    echo -e "\n${BLUE}🔍 Checking OpenAI API connection${NC}"
    
    if timeout "$TIMEOUT" curl -s -H "Authorization: Bearer $OPENAI_API_KEY" "https://api.openai.com/v1/models" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ OpenAI API is accessible${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        echo -e "${RED}❌ OpenAI API connection failed${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
fi

# Email service (SMTP)
if [ -n "$SMTP_HOST" ] && [ -n "$SMTP_PORT" ]; then
    service_check "SMTP Server" "$SMTP_HOST" "$SMTP_PORT"
fi

# Summary
echo -e "\n${BLUE}📊 Health Check Summary${NC}"
echo -e "Environment: $ENV"
echo -e "Total checks: $TOTAL_CHECKS"
echo -e "${GREEN}Healthy: $PASSED_CHECKS${NC}"
echo -e "${RED}Unhealthy: $FAILED_CHECKS${NC}"

if [ $TOTAL_CHECKS -gt 0 ]; then
    HEALTH_PERCENTAGE=$(( (PASSED_CHECKS * 100) / TOTAL_CHECKS ))
    echo -e "Health score: $HEALTH_PERCENTAGE%"
    
    if [ $HEALTH_PERCENTAGE -ge 90 ]; then
        echo -e "${GREEN}🎉 System is in excellent health!${NC}"
    elif [ $HEALTH_PERCENTAGE -ge 75 ]; then
        echo -e "${YELLOW}⚠️  System health is acceptable but could be improved${NC}"
    else
        echo -e "${RED}🚨 System health is poor - immediate attention required${NC}"
    fi
fi

# Create health report
REPORT_FILE="$PROJECT_ROOT/logs/health-check-$(date +%Y%m%d_%H%M%S).json"
mkdir -p "$(dirname "$REPORT_FILE")"

cat > "$REPORT_FILE" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "environment": "$ENV",
  "health_score": $HEALTH_PERCENTAGE,
  "total_checks": $TOTAL_CHECKS,
  "passed_checks": $PASSED_CHECKS,
  "failed_checks": $FAILED_CHECKS,
  "status": $([ $FAILED_CHECKS -eq 0 ] && echo '"healthy"' || echo '"unhealthy"')
}
EOF

echo -e "\n${BLUE}📄 Health report saved to: $REPORT_FILE${NC}"

# Exit with appropriate code
if [ $FAILED_CHECKS -eq 0 ]; then
    echo -e "\n${GREEN}✅ All health checks passed!${NC}"
    exit 0
else
    echo -e "\n${RED}❌ $FAILED_CHECKS health check(s) failed${NC}"
    exit 1
fi