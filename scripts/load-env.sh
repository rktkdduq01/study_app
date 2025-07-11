#!/bin/bash

# Environment Configuration Loader Script
# Usage: source scripts/load-env.sh [environment]
# Example: source scripts/load-env.sh production

set -e

# Default environment
ENV=${1:-development}

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Environment files
ENV_DIR="$PROJECT_ROOT/config/environments"
ENV_FILE="$ENV_DIR/$ENV.env"
COMMON_ENV_FILE="$PROJECT_ROOT/.env"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Loading environment configuration for: ${ENV}${NC}"

# Check if environment file exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: Environment file not found: $ENV_FILE${NC}"
    echo "Available environments:"
    ls -1 "$ENV_DIR"/*.env 2>/dev/null | xargs -n 1 basename -s .env || echo "No environment files found"
    return 1 2>/dev/null || exit 1
fi

# Load common environment variables first
if [ -f "$COMMON_ENV_FILE" ]; then
    echo -e "${YELLOW}Loading common environment variables...${NC}"
    set -a
    source "$COMMON_ENV_FILE"
    set +a
fi

# Load environment-specific variables
echo -e "${YELLOW}Loading $ENV environment variables...${NC}"
set -a
source "$ENV_FILE"
set +a

# Validate required variables for production
if [ "$ENV" = "production" ]; then
    echo -e "${YELLOW}Validating production environment variables...${NC}"
    
    REQUIRED_VARS=(
        "POSTGRES_HOST"
        "POSTGRES_DB"
        "POSTGRES_USER"
        "REDIS_HOST"
        "FRONTEND_URL"
        "VITE_API_URL"
        "SMTP_HOST"
        "AWS_REGION"
        "S3_BUCKET_NAME"
    )
    
    MISSING_VARS=()
    for var in "${REQUIRED_VARS[@]}"; do
        if [ -z "${!var}" ]; then
            MISSING_VARS+=("$var")
        fi
    done
    
    if [ ${#MISSING_VARS[@]} -ne 0 ]; then
        echo -e "${RED}Error: Missing required production variables:${NC}"
        printf "${RED}  - %s${NC}\n" "${MISSING_VARS[@]}"
        return 1 2>/dev/null || exit 1
    fi
    
    # Check for insecure defaults in production
    INSECURE_VARS=()
    if [ "$DEBUG" = "true" ]; then
        INSECURE_VARS+=("DEBUG=true")
    fi
    if [ "$SECRET_KEY" = "dev-secret-key-not-for-production" ]; then
        INSECURE_VARS+=("SECRET_KEY using development value")
    fi
    if [ "$JWT_SECRET" = "dev-jwt-secret-not-for-production" ]; then
        INSECURE_VARS+=("JWT_SECRET using development value")
    fi
    
    if [ ${#INSECURE_VARS[@]} -ne 0 ]; then
        echo -e "${RED}Error: Insecure configuration detected in production:${NC}"
        printf "${RED}  - %s${NC}\n" "${INSECURE_VARS[@]}"
        return 1 2>/dev/null || exit 1
    fi
fi

# Create .env file for Docker Compose
echo -e "${YELLOW}Creating .env file for Docker Compose...${NC}"
cp "$ENV_FILE" "$PROJECT_ROOT/.env"

# Export environment name
export ENVIRONMENT="$ENV"

echo -e "${GREEN}✓ Environment configuration loaded successfully${NC}"
echo -e "${GREEN}✓ Environment: $ENVIRONMENT${NC}"
echo -e "${GREEN}✓ Debug mode: ${DEBUG:-false}${NC}"
echo -e "${GREEN}✓ Database: ${POSTGRES_HOST:-localhost}:${POSTGRES_PORT:-5432}/${POSTGRES_DB:-quest_edu}${NC}"
echo -e "${GREEN}✓ Redis: ${REDIS_HOST:-localhost}:${REDIS_PORT:-6379}${NC}"
echo -e "${GREEN}✓ Frontend URL: ${FRONTEND_URL:-http://localhost:3000}${NC}"

# Additional validation for staging/production
if [ "$ENV" != "development" ]; then
    echo -e "${YELLOW}Running additional checks for $ENV environment...${NC}"
    
    # Check if secrets are properly configured
    if [ -z "$SECRET_KEY" ] || [ -z "$JWT_SECRET" ]; then
        echo -e "${YELLOW}Warning: SECRET_KEY or JWT_SECRET not set. Make sure they are configured in your secrets manager.${NC}"
    fi
    
    # Check SSL configuration
    if [[ "$FRONTEND_URL" != https://* ]]; then
        echo -e "${YELLOW}Warning: FRONTEND_URL should use HTTPS in $ENV environment${NC}"
    fi
    
    # Check database SSL
    if [ "$ENV" = "production" ] && [[ "$DATABASE_URL" != *"sslmode=require"* ]]; then
        echo -e "${YELLOW}Warning: Database connection should use SSL in production${NC}"
    fi
fi

echo -e "${GREEN}Environment configuration completed!${NC}"