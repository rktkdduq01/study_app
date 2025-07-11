#!/bin/bash

# Environment Configuration Validation Script
# Usage: ./scripts/validate-env.sh [environment]
# Example: ./scripts/validate-env.sh production

set -e

# Default environment
ENV=${1:-development}

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Environment files
ENV_DIR="$PROJECT_ROOT/config/environments"
ENV_FILE="$ENV_DIR/$ENV.env"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Validating environment configuration for: ${ENV}${NC}"

# Check if environment file exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ Error: Environment file not found: $ENV_FILE${NC}"
    echo "Available environments:"
    ls -1 "$ENV_DIR"/*.env 2>/dev/null | xargs -n 1 basename -s .env || echo "No environment files found"
    exit 1
fi

# Load environment variables
source "$ENV_FILE"

# Validation counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

# Validation function
validate_var() {
    local var_name="$1"
    local var_value="${!var_name}"
    local is_required="$2"
    local description="$3"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if [ -z "$var_value" ]; then
        if [ "$is_required" = "true" ]; then
            echo -e "${RED}❌ MISSING: $var_name - $description${NC}"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
        else
            echo -e "${YELLOW}⚠️  OPTIONAL: $var_name - $description${NC}"
            WARNING_CHECKS=$((WARNING_CHECKS + 1))
        fi
    else
        echo -e "${GREEN}✅ OK: $var_name${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    fi
}

# Validation function for patterns
validate_pattern() {
    local var_name="$1"
    local var_value="${!var_name}"
    local pattern="$2"
    local description="$3"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if [ -z "$var_value" ]; then
        echo -e "${RED}❌ MISSING: $var_name - $description${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    elif [[ "$var_value" =~ $pattern ]]; then
        echo -e "${GREEN}✅ OK: $var_name${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        echo -e "${RED}❌ INVALID: $var_name - $description${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
}

echo -e "\n${BLUE}📋 Basic Configuration${NC}"
validate_var "ENVIRONMENT" true "Environment name"
validate_var "DEBUG" true "Debug mode flag"

echo -e "\n${BLUE}🗄️  Database Configuration${NC}"
validate_var "POSTGRES_HOST" true "PostgreSQL host"
validate_var "POSTGRES_PORT" true "PostgreSQL port"
validate_var "POSTGRES_DB" true "PostgreSQL database name"
validate_var "POSTGRES_USER" true "PostgreSQL username"

echo -e "\n${BLUE}🔄 Redis Configuration${NC}"
validate_var "REDIS_HOST" true "Redis host"
validate_var "REDIS_PORT" true "Redis port"

echo -e "\n${BLUE}🔐 Security Configuration${NC}"
validate_var "SECRET_KEY" true "Application secret key"
validate_var "JWT_SECRET" true "JWT secret key"
validate_var "JWT_EXPIRATION_DELTA" true "JWT expiration time"

echo -e "\n${BLUE}🌐 Frontend URLs${NC}"
validate_pattern "FRONTEND_URL" "^https?://" "Frontend URL (should start with http/https)"
validate_pattern "VITE_API_URL" "^https?://" "API URL (should start with http/https)"
validate_pattern "VITE_WEBSOCKET_URL" "^wss?://" "WebSocket URL (should start with ws/wss)"

echo -e "\n${BLUE}📧 Email Configuration${NC}"
validate_var "SMTP_HOST" true "SMTP server host"
validate_var "SMTP_PORT" true "SMTP server port"
validate_var "SMTP_FROM_EMAIL" true "Email sender address"

echo -e "\n${BLUE}📊 Logging Configuration${NC}"
validate_var "LOG_LEVEL" true "Log level"
validate_var "LOG_FORMAT" true "Log format"

# Environment-specific validations
if [ "$ENV" = "production" ]; then
    echo -e "\n${BLUE}🚀 Production-Specific Validation${NC}"
    
    # Security checks for production
    if [ "$DEBUG" = "true" ]; then
        echo -e "${RED}❌ SECURITY: DEBUG should be false in production${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    else
        echo -e "${GREEN}✅ OK: DEBUG is disabled${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    fi
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    # Check for development secrets
    if [ "$SECRET_KEY" = "dev-secret-key-not-for-production" ]; then
        echo -e "${RED}❌ SECURITY: Using development SECRET_KEY in production${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    else
        echo -e "${GREEN}✅ OK: SECRET_KEY is not development default${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    fi
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if [ "$JWT_SECRET" = "dev-jwt-secret-not-for-production" ]; then
        echo -e "${RED}❌ SECURITY: Using development JWT_SECRET in production${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    else
        echo -e "${GREEN}✅ OK: JWT_SECRET is not development default${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    fi
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    # SSL/HTTPS checks
    if [[ "$FRONTEND_URL" != https://* ]]; then
        echo -e "${RED}❌ SECURITY: FRONTEND_URL should use HTTPS in production${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    else
        echo -e "${GREEN}✅ OK: FRONTEND_URL uses HTTPS${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    fi
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if [[ "$VITE_API_URL" != https://* ]]; then
        echo -e "${RED}❌ SECURITY: VITE_API_URL should use HTTPS in production${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    else
        echo -e "${GREEN}✅ OK: VITE_API_URL uses HTTPS${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    fi
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if [[ "$VITE_WEBSOCKET_URL" != wss://* ]]; then
        echo -e "${RED}❌ SECURITY: VITE_WEBSOCKET_URL should use WSS in production${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    else
        echo -e "${GREEN}✅ OK: VITE_WEBSOCKET_URL uses WSS${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    fi
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    # Production-specific configurations
    echo -e "\n${BLUE}☁️  AWS Configuration${NC}"
    validate_var "AWS_REGION" true "AWS region"
    validate_var "S3_BUCKET_NAME" true "S3 bucket for uploads"
    
    echo -e "\n${BLUE}📈 Monitoring Configuration${NC}"
    validate_var "ENABLE_METRICS" true "Metrics collection"
    validate_var "SENTRY_DSN" false "Sentry DSN for error tracking"
    
    echo -e "\n${BLUE}🔧 Performance Configuration${NC}"
    validate_var "RATE_LIMIT_ENABLED" true "Rate limiting"
    validate_var "CACHE_TTL_DEFAULT" true "Default cache TTL"
    
elif [ "$ENV" = "staging" ]; then
    echo -e "\n${BLUE}🧪 Staging-Specific Validation${NC}"
    
    # Staging should be production-like but allow some relaxed settings
    if [ "$DEBUG" = "true" ]; then
        echo -e "${YELLOW}⚠️  WARNING: DEBUG is enabled in staging (consider disabling)${NC}"
        WARNING_CHECKS=$((WARNING_CHECKS + 1))
    else
        echo -e "${GREEN}✅ OK: DEBUG is disabled${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    fi
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
elif [ "$ENV" = "development" ]; then
    echo -e "\n${BLUE}🛠️  Development-Specific Validation${NC}"
    
    # Development can be more relaxed
    if [ "$DEBUG" != "true" ]; then
        echo -e "${YELLOW}⚠️  WARNING: DEBUG is disabled in development (consider enabling)${NC}"
        WARNING_CHECKS=$((WARNING_CHECKS + 1))
    else
        echo -e "${GREEN}✅ OK: DEBUG is enabled${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    fi
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    # Check localhost configurations
    if [[ "$POSTGRES_HOST" != "localhost" ]]; then
        echo -e "${YELLOW}⚠️  INFO: POSTGRES_HOST is not localhost (${POSTGRES_HOST})${NC}"
        WARNING_CHECKS=$((WARNING_CHECKS + 1))
    else
        echo -e "${GREEN}✅ OK: Using localhost for PostgreSQL${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    fi
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
fi

# Summary
echo -e "\n${BLUE}📊 Validation Summary${NC}"
echo -e "Total checks: ${TOTAL_CHECKS}"
echo -e "${GREEN}Passed: ${PASSED_CHECKS}${NC}"
echo -e "${RED}Failed: ${FAILED_CHECKS}${NC}"
echo -e "${YELLOW}Warnings: ${WARNING_CHECKS}${NC}"

# Calculate success percentage
if [ $TOTAL_CHECKS -gt 0 ]; then
    SUCCESS_PERCENT=$(( (PASSED_CHECKS * 100) / TOTAL_CHECKS ))
    echo -e "Success rate: ${SUCCESS_PERCENT}%"
fi

# Exit with appropriate code
if [ $FAILED_CHECKS -gt 0 ]; then
    echo -e "\n${RED}❌ Validation failed with ${FAILED_CHECKS} errors${NC}"
    echo -e "${RED}Please fix the errors before proceeding with deployment${NC}"
    exit 1
elif [ $WARNING_CHECKS -gt 0 ]; then
    echo -e "\n${YELLOW}⚠️  Validation completed with ${WARNING_CHECKS} warnings${NC}"
    echo -e "${YELLOW}Review warnings for potential improvements${NC}"
    exit 0
else
    echo -e "\n${GREEN}✅ All validations passed successfully!${NC}"
    echo -e "${GREEN}Environment is ready for deployment${NC}"
    exit 0
fi