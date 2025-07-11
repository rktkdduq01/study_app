#!/bin/bash

# Automated Test Pipeline Runner
# Usage: ./scripts/test-runner.sh [environment] [test-type]
# Example: ./scripts/test-runner.sh development all
# Example: ./scripts/test-runner.sh staging backend

set -e

# Parameters
ENV=${1:-development}
TEST_TYPE=${2:-all}

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Logging
LOG_DIR="$PROJECT_ROOT/logs/tests"
mkdir -p "$LOG_DIR"
TEST_LOG="$LOG_DIR/test-run-$(date +%Y%m%d_%H%M%S).log"

log() {
    echo -e "$1" | tee -a "$TEST_LOG"
}

log "${BLUE}🧪 Starting automated test pipeline${NC}"
log "${BLUE}Environment: $ENV${NC}"
log "${BLUE}Test Type: $TEST_TYPE${NC}"
log "${BLUE}Log File: $TEST_LOG${NC}"

# Load environment configuration
if [ -f "$PROJECT_ROOT/scripts/load-env.sh" ]; then
    log "${YELLOW}Loading environment configuration...${NC}"
    source "$PROJECT_ROOT/scripts/load-env.sh" "$ENV"
else
    log "${RED}❌ Environment loader not found${NC}"
    exit 1
fi

# Validate environment
if [ -f "$PROJECT_ROOT/scripts/validate-env.sh" ]; then
    log "${YELLOW}Validating environment configuration...${NC}"
    if ! bash "$PROJECT_ROOT/scripts/validate-env.sh" "$ENV"; then
        log "${RED}❌ Environment validation failed${NC}"
        exit 1
    fi
else
    log "${YELLOW}⚠️  Environment validator not found, skipping validation${NC}"
fi

# Test execution function
run_test() {
    local test_name="$1"
    local test_command="$2"
    local test_dir="$3"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    log "\n${BLUE}🔄 Running $test_name...${NC}"
    
    if [ -n "$test_dir" ]; then
        cd "$PROJECT_ROOT/$test_dir"
    fi
    
    if eval "$test_command" >> "$TEST_LOG" 2>&1; then
        log "${GREEN}✅ $test_name PASSED${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        log "${RED}❌ $test_name FAILED${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        
        # Show last few lines of output for failed tests
        log "${RED}Last 10 lines of output:${NC}"
        tail -10 "$TEST_LOG" | sed 's/^/  /' | tee -a "$TEST_LOG"
    fi
    
    cd "$PROJECT_ROOT"
}

# Backend tests
run_backend_tests() {
    log "\n${BLUE}🐍 Backend Test Suite${NC}"
    
    if [ ! -d "$PROJECT_ROOT/backend" ]; then
        log "${YELLOW}⚠️  Backend directory not found, skipping backend tests${NC}"
        return
    fi
    
    # Check if virtual environment exists
    if [ ! -d "$PROJECT_ROOT/backend/venv" ] && [ ! -d "$PROJECT_ROOT/backend/venv_backend" ]; then
        log "${YELLOW}Creating Python virtual environment...${NC}"
        cd "$PROJECT_ROOT/backend"
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        if [ -f "requirements-dev.txt" ]; then
            pip install -r requirements-dev.txt
        fi
        cd "$PROJECT_ROOT"
    fi
    
    # Activate virtual environment
    if [ -d "$PROJECT_ROOT/backend/venv" ]; then
        source "$PROJECT_ROOT/backend/venv/bin/activate"
    elif [ -d "$PROJECT_ROOT/backend/venv_backend" ]; then
        source "$PROJECT_ROOT/backend/venv_backend/bin/activate"
    fi
    
    # Code quality checks
    run_test "Backend Linting (Ruff)" "ruff check ." "backend"
    run_test "Backend Code Formatting (Black)" "black --check ." "backend"
    
    # Security checks
    if command -v safety &> /dev/null; then
        run_test "Backend Security Check (Safety)" "safety check" "backend"
    fi
    
    if command -v bandit &> /dev/null; then
        run_test "Backend Security Analysis (Bandit)" "bandit -r app/ -ll" "backend"
    fi
    
    # Unit tests
    run_test "Backend Unit Tests" "python -m pytest tests/ -v --tb=short" "backend"
    
    # Integration tests
    if [ -f "$PROJECT_ROOT/backend/tests/test_integration.py" ]; then
        run_test "Backend Integration Tests" "python -m pytest tests/test_integration*.py -v" "backend"
    fi
    
    # API tests
    if [ -f "$PROJECT_ROOT/backend/test_api.py" ]; then
        run_test "Backend API Tests" "python test_api.py" "backend"
    fi
}

# Frontend tests
run_frontend_tests() {
    log "\n${BLUE}⚛️  Frontend Test Suite${NC}"
    
    if [ ! -d "$PROJECT_ROOT/frontend" ]; then
        log "${YELLOW}⚠️  Frontend directory not found, skipping frontend tests${NC}"
        return
    fi
    
    # Install dependencies if node_modules doesn't exist
    if [ ! -d "$PROJECT_ROOT/frontend/node_modules" ]; then
        log "${YELLOW}Installing frontend dependencies...${NC}"
        run_test "Frontend Dependency Installation" "npm ci" "frontend"
    fi
    
    # Code quality checks
    run_test "Frontend Linting" "npm run lint" "frontend"
    
    # Type checking
    run_test "Frontend Type Check" "npm run type-check || npx tsc --noEmit" "frontend"
    
    # Unit tests
    run_test "Frontend Unit Tests" "npm test -- --coverage --watchAll=false" "frontend"
    
    # Build test
    run_test "Frontend Build" "npm run build" "frontend"
}

# E2E tests
run_e2e_tests() {
    log "\n${BLUE}🎭 End-to-End Test Suite${NC}"
    
    if [ ! -d "$PROJECT_ROOT/e2e" ]; then
        log "${YELLOW}⚠️  E2E directory not found, skipping E2E tests${NC}"
        return
    fi
    
    # Install Playwright if not already installed
    if ! command -v npx playwright &> /dev/null; then
        log "${YELLOW}Installing Playwright...${NC}"
        cd "$PROJECT_ROOT"
        npm install -D @playwright/test
        npx playwright install
    fi
    
    # Start services for E2E tests (if in development)
    if [ "$ENV" = "development" ]; then
        log "${YELLOW}Starting services for E2E tests...${NC}"
        
        # Start backend in background
        cd "$PROJECT_ROOT/backend"
        if [ -d "venv" ]; then
            source venv/bin/activate
        elif [ -d "venv_backend" ]; then
            source venv_backend/bin/activate
        fi
        
        python main.py &
        BACKEND_PID=$!
        
        # Wait for backend to start
        sleep 5
        
        # Start frontend in background
        cd "$PROJECT_ROOT/frontend"
        npm run dev &
        FRONTEND_PID=$!
        
        # Wait for frontend to start
        sleep 10
        
        cd "$PROJECT_ROOT"
    fi
    
    # Run E2E tests
    run_test "E2E Smoke Tests" "npx playwright test e2e/smoke.spec.ts" ""
    run_test "E2E Auth Flow Tests" "npx playwright test e2e/auth.spec.ts" ""
    run_test "E2E Learning Flow Tests" "npx playwright test e2e/learning-flow.spec.ts" ""
    
    # Stop services if we started them
    if [ "$ENV" = "development" ] && [ -n "$BACKEND_PID" ] && [ -n "$FRONTEND_PID" ]; then
        log "${YELLOW}Stopping test services...${NC}"
        kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    fi
}

# Mobile tests
run_mobile_tests() {
    log "\n${BLUE}📱 Mobile Test Suite${NC}"
    
    if [ ! -d "$PROJECT_ROOT/mobile" ]; then
        log "${YELLOW}⚠️  Mobile directory not found, skipping mobile tests${NC}"
        return
    fi
    
    # Install dependencies if node_modules doesn't exist
    if [ ! -d "$PROJECT_ROOT/mobile/node_modules" ]; then
        log "${YELLOW}Installing mobile dependencies...${NC}"
        run_test "Mobile Dependency Installation" "npm ci" "mobile"
    fi
    
    # Type checking
    run_test "Mobile Type Check" "npx tsc --noEmit" "mobile"
    
    # Linting
    if [ -f "$PROJECT_ROOT/mobile/package.json" ] && grep -q "lint" "$PROJECT_ROOT/mobile/package.json"; then
        run_test "Mobile Linting" "npm run lint" "mobile"
    fi
    
    # Unit tests
    if [ -f "$PROJECT_ROOT/mobile/package.json" ] && grep -q "test" "$PROJECT_ROOT/mobile/package.json"; then
        run_test "Mobile Unit Tests" "npm test" "mobile"
    fi
}

# Docker tests
run_docker_tests() {
    log "\n${BLUE}🐳 Docker Test Suite${NC}"
    
    # Test Docker builds
    if [ -f "$PROJECT_ROOT/backend/Dockerfile" ]; then
        run_test "Backend Docker Build" "docker build -t quest-backend-test ./backend" ""
    fi
    
    if [ -f "$PROJECT_ROOT/frontend/Dockerfile" ]; then
        run_test "Frontend Docker Build" "docker build -t quest-frontend-test ./frontend" ""
    fi
    
    # Test docker-compose
    if [ -f "$PROJECT_ROOT/docker-compose.yml" ]; then
        run_test "Docker Compose Validation" "docker-compose config" ""
    fi
    
    # Clean up test images
    log "${YELLOW}Cleaning up test Docker images...${NC}"
    docker rmi quest-backend-test quest-frontend-test 2>/dev/null || true
}

# Security tests
run_security_tests() {
    log "\n${BLUE}🔒 Security Test Suite${NC}"
    
    # Run security scanning script if it exists
    if [ -f "$PROJECT_ROOT/scripts/security-scan.sh" ]; then
        run_test "Security Scan" "bash scripts/security-scan.sh" ""
    fi
    
    # Check for sensitive files
    run_test "Sensitive Files Check" "! find . -name '*.env' -not -path './config/environments/*' -not -name '.env.example'" ""
    
    # Check for hardcoded secrets (basic check)
    run_test "Hardcoded Secrets Check" "! grep -r 'password.*=' --include='*.py' --include='*.js' --include='*.ts' --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=.git ." ""
}

# Performance tests
run_performance_tests() {
    log "\n${BLUE}⚡ Performance Test Suite${NC}"
    
    # Check bundle sizes if they exist
    if [ -f "$PROJECT_ROOT/frontend/dist/index.html" ]; then
        run_test "Frontend Bundle Size Check" "test $(du -s frontend/dist | cut -f1) -lt 10000" ""  # Less than 10MB
    fi
    
    # Database query performance (if we have test data)
    if [ "$ENV" = "development" ] && [ -f "$PROJECT_ROOT/backend/test_performance.py" ]; then
        run_test "Database Performance Tests" "python test_performance.py" "backend"
    fi
}

# Main test execution
log "\n${BLUE}📋 Test Execution Plan${NC}"
case $TEST_TYPE in
    "all")
        log "Running all test suites..."
        run_backend_tests
        run_frontend_tests
        run_mobile_tests
        run_e2e_tests
        run_docker_tests
        run_security_tests
        run_performance_tests
        ;;
    "backend")
        log "Running backend tests only..."
        run_backend_tests
        ;;
    "frontend")
        log "Running frontend tests only..."
        run_frontend_tests
        ;;
    "mobile")
        log "Running mobile tests only..."
        run_mobile_tests
        ;;
    "e2e")
        log "Running E2E tests only..."
        run_e2e_tests
        ;;
    "docker")
        log "Running Docker tests only..."
        run_docker_tests
        ;;
    "security")
        log "Running security tests only..."
        run_security_tests
        ;;
    "performance")
        log "Running performance tests only..."
        run_performance_tests
        ;;
    *)
        log "${RED}❌ Invalid test type: $TEST_TYPE${NC}"
        log "Valid options: all, backend, frontend, mobile, e2e, docker, security, performance"
        exit 1
        ;;
esac

# Test summary
log "\n${BLUE}📊 Test Summary${NC}"
log "Total tests: $TOTAL_TESTS"
log "${GREEN}Passed: $PASSED_TESTS${NC}"
log "${RED}Failed: $FAILED_TESTS${NC}"

if [ $TOTAL_TESTS -gt 0 ]; then
    SUCCESS_RATE=$(( (PASSED_TESTS * 100) / TOTAL_TESTS ))
    log "Success rate: $SUCCESS_RATE%"
fi

# Generate test report
REPORT_FILE="$LOG_DIR/test-report-$(date +%Y%m%d_%H%M%S).html"
cat > "$REPORT_FILE" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Test Report - $ENV</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background: #f5f5f5; padding: 20px; border-radius: 5px; }
        .summary { margin: 20px 0; }
        .passed { color: green; }
        .failed { color: red; }
        .log { background: #f9f9f9; padding: 15px; border-radius: 5px; font-family: monospace; white-space: pre-wrap; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Test Report</h1>
        <p><strong>Environment:</strong> $ENV</p>
        <p><strong>Test Type:</strong> $TEST_TYPE</p>
        <p><strong>Date:</strong> $(date)</p>
    </div>
    
    <div class="summary">
        <h2>Summary</h2>
        <p>Total Tests: $TOTAL_TESTS</p>
        <p class="passed">Passed: $PASSED_TESTS</p>
        <p class="failed">Failed: $FAILED_TESTS</p>
        <p>Success Rate: $SUCCESS_RATE%</p>
    </div>
    
    <div class="log">
        <h2>Detailed Log</h2>
$(cat "$TEST_LOG" | sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g')
    </div>
</body>
</html>
EOF

log "\n${BLUE}📄 Test report generated: $REPORT_FILE${NC}"

# Exit with appropriate code
if [ $FAILED_TESTS -gt 0 ]; then
    log "\n${RED}❌ Test pipeline failed with $FAILED_TESTS failures${NC}"
    exit 1
else
    log "\n${GREEN}✅ All tests passed successfully!${NC}"
    exit 0
fi