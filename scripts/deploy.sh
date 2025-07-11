#!/bin/bash

# Deploy script for Educational RPG Platform
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-staging}
VERSION=${2:-latest}

echo -e "${GREEN}🚀 Deploying Educational RPG Platform${NC}"
echo -e "Environment: ${YELLOW}$ENVIRONMENT${NC}"
echo -e "Version: ${YELLOW}$VERSION${NC}"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "\n${GREEN}Checking prerequisites...${NC}"

if ! command_exists docker; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

if ! command_exists docker-compose; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    exit 1
fi

# Load environment variables
if [ -f .env.$ENVIRONMENT ]; then
    echo -e "${GREEN}Loading environment variables from .env.$ENVIRONMENT${NC}"
    export $(cat .env.$ENVIRONMENT | grep -v '^#' | xargs)
else
    echo -e "${YELLOW}Warning: .env.$ENVIRONMENT file not found${NC}"
fi

# Pull latest changes
echo -e "\n${GREEN}Pulling latest changes...${NC}"
git pull origin main

# Build Docker images
echo -e "\n${GREEN}Building Docker images...${NC}"
docker-compose build --parallel

# Run database migrations
echo -e "\n${GREEN}Running database migrations...${NC}"
docker-compose run --rm backend alembic upgrade head

# Start services
echo -e "\n${GREEN}Starting services...${NC}"
if [ "$ENVIRONMENT" = "production" ]; then
    docker-compose --profile production up -d
else
    docker-compose up -d
fi

# Wait for services to be healthy
echo -e "\n${GREEN}Waiting for services to be healthy...${NC}"
sleep 10

# Health check
echo -e "\n${GREEN}Running health checks...${NC}"
if curl -f http://localhost:8000/health >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend is healthy${NC}"
else
    echo -e "${RED}✗ Backend health check failed${NC}"
    exit 1
fi

if curl -f http://localhost:3000 >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend is healthy${NC}"
else
    echo -e "${RED}✗ Frontend health check failed${NC}"
    exit 1
fi

# Run smoke tests
if [ "$ENVIRONMENT" = "production" ]; then
    echo -e "\n${GREEN}Running smoke tests...${NC}"
    npm run test:e2e -- --grep "@smoke"
fi

echo -e "\n${GREEN}🎉 Deployment completed successfully!${NC}"
echo -e "Frontend: http://localhost:3000"
echo -e "Backend API: http://localhost:8000"
echo -e "API Docs: http://localhost:8000/docs"

if [ "$ENVIRONMENT" = "development" ]; then
    echo -e "pgAdmin: http://localhost:5050"
    echo -e "Redis Commander: http://localhost:8081"
fi