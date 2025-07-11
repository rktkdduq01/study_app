#!/bin/bash

# Production deployment script
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
ENVIRONMENT="production"
AWS_REGION="us-west-2"
ECR_REGISTRY="your-account-id.dkr.ecr.us-west-2.amazonaws.com"
ECS_CLUSTER="educational-rpg-cluster"
BACKEND_SERVICE="educational-rpg-backend-production"
FRONTEND_SERVICE="educational-rpg-frontend-production"

echo -e "${BLUE}🚀 Educational RPG Platform - Production Deployment${NC}"
echo -e "${BLUE}================================================${NC}\n"

# Check prerequisites
check_prerequisites() {
    echo -e "${GREEN}Checking prerequisites...${NC}"
    
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}Error: AWS CLI is not installed${NC}"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker is not installed${NC}"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        echo -e "${RED}Error: AWS credentials not configured${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ All prerequisites satisfied${NC}\n"
}

# Build and push Docker images
build_and_push_images() {
    echo -e "${GREEN}Building and pushing Docker images...${NC}"
    
    # Login to ECR
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY
    
    # Get git commit hash for tagging
    GIT_COMMIT=$(git rev-parse --short HEAD)
    TIMESTAMP=$(date +%Y%m%d%H%M%S)
    TAG="${TIMESTAMP}-${GIT_COMMIT}"
    
    # Build backend
    echo -e "${YELLOW}Building backend image...${NC}"
    docker build -t $ECR_REGISTRY/educational-rpg-backend:$TAG \
                 -t $ECR_REGISTRY/educational-rpg-backend:latest \
                 -f backend/Dockerfile \
                 backend/
    
    # Build frontend
    echo -e "${YELLOW}Building frontend image...${NC}"
    docker build -t $ECR_REGISTRY/educational-rpg-frontend:$TAG \
                 -t $ECR_REGISTRY/educational-rpg-frontend:latest \
                 -f frontend/Dockerfile \
                 --build-arg VITE_API_URL=https://api.educational-rpg.com/api/v1 \
                 --build-arg VITE_WEBSOCKET_URL=wss://api.educational-rpg.com/ws \
                 frontend/
    
    # Push images
    echo -e "${YELLOW}Pushing images to ECR...${NC}"
    docker push $ECR_REGISTRY/educational-rpg-backend:$TAG
    docker push $ECR_REGISTRY/educational-rpg-backend:latest
    docker push $ECR_REGISTRY/educational-rpg-frontend:$TAG
    docker push $ECR_REGISTRY/educational-rpg-frontend:latest
    
    echo -e "${GREEN}✓ Images built and pushed successfully${NC}\n"
}

# Run database migrations
run_migrations() {
    echo -e "${GREEN}Running database migrations...${NC}"
    
    # Get database URL from SSM Parameter Store
    DB_URL=$(aws ssm get-parameter --name "/educational-rpg/production/database-url" --with-decryption --query 'Parameter.Value' --output text)
    
    # Run migrations using Docker
    docker run --rm \
        -e DATABASE_URL="$DB_URL" \
        $ECR_REGISTRY/educational-rpg-backend:latest \
        alembic upgrade head
    
    echo -e "${GREEN}✓ Migrations completed${NC}\n"
}

# Deploy to ECS
deploy_to_ecs() {
    echo -e "${GREEN}Deploying to ECS...${NC}"
    
    # Update backend service
    echo -e "${YELLOW}Updating backend service...${NC}"
    aws ecs update-service \
        --cluster $ECS_CLUSTER \
        --service $BACKEND_SERVICE \
        --force-new-deployment \
        --region $AWS_REGION
    
    # Update frontend service
    echo -e "${YELLOW}Updating frontend service...${NC}"
    aws ecs update-service \
        --cluster $ECS_CLUSTER \
        --service $FRONTEND_SERVICE \
        --force-new-deployment \
        --region $AWS_REGION
    
    echo -e "${GREEN}✓ ECS services updated${NC}\n"
}

# Wait for deployment
wait_for_deployment() {
    echo -e "${GREEN}Waiting for deployment to stabilize...${NC}"
    
    # Wait for backend
    echo -e "${YELLOW}Waiting for backend...${NC}"
    aws ecs wait services-stable \
        --cluster $ECS_CLUSTER \
        --services $BACKEND_SERVICE \
        --region $AWS_REGION
    
    # Wait for frontend
    echo -e "${YELLOW}Waiting for frontend...${NC}"
    aws ecs wait services-stable \
        --cluster $ECS_CLUSTER \
        --services $FRONTEND_SERVICE \
        --region $AWS_REGION
    
    echo -e "${GREEN}✓ Services are stable${NC}\n"
}

# Run smoke tests
run_smoke_tests() {
    echo -e "${GREEN}Running smoke tests...${NC}"
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        npm install
    fi
    
    # Run smoke tests
    PLAYWRIGHT_BASE_URL=https://educational-rpg.com npm run test:e2e -- --grep "@smoke"
    
    echo -e "${GREEN}✓ Smoke tests passed${NC}\n"
}

# Invalidate CloudFront cache
invalidate_cache() {
    echo -e "${GREEN}Invalidating CloudFront cache...${NC}"
    
    DISTRIBUTION_ID=$(aws ssm get-parameter --name "/educational-rpg/production/cloudfront-distribution-id" --query 'Parameter.Value' --output text)
    
    aws cloudfront create-invalidation \
        --distribution-id $DISTRIBUTION_ID \
        --paths "/*"
    
    echo -e "${GREEN}✓ Cache invalidation started${NC}\n"
}

# Send deployment notification
send_notification() {
    echo -e "${GREEN}Sending deployment notification...${NC}"
    
    # Get Slack webhook from SSM
    SLACK_WEBHOOK=$(aws ssm get-parameter --name "/educational-rpg/production/slack-webhook" --with-decryption --query 'Parameter.Value' --output text)
    
    # Send notification
    curl -X POST $SLACK_WEBHOOK \
        -H 'Content-type: application/json' \
        -d "{
            \"text\": \"🚀 Production Deployment Completed\",
            \"attachments\": [{
                \"color\": \"good\",
                \"fields\": [
                    {\"title\": \"Environment\", \"value\": \"Production\", \"short\": true},
                    {\"title\": \"Version\", \"value\": \"${TAG}\", \"short\": true},
                    {\"title\": \"Status\", \"value\": \"Success\", \"short\": true},
                    {\"title\": \"Deployed By\", \"value\": \"${USER}\", \"short\": true}
                ]
            }]
        }"
    
    echo -e "${GREEN}✓ Notification sent${NC}\n"
}

# Main deployment flow
main() {
    echo -e "${YELLOW}Starting production deployment...${NC}\n"
    
    # Confirmation
    echo -e "${RED}⚠️  WARNING: You are about to deploy to PRODUCTION!${NC}"
    read -p "Are you sure you want to continue? (yes/no): " -r
    echo
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo -e "${YELLOW}Deployment cancelled.${NC}"
        exit 0
    fi
    
    # Run deployment steps
    check_prerequisites
    build_and_push_images
    run_migrations
    deploy_to_ecs
    wait_for_deployment
    run_smoke_tests
    invalidate_cache
    send_notification
    
    echo -e "${GREEN}🎉 Production deployment completed successfully!${NC}"
    echo -e "Application URL: https://educational-rpg.com"
    echo -e "API URL: https://api.educational-rpg.com"
}

# Run main function
main "$@"