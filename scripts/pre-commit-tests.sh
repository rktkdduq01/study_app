#!/bin/bash

# Pre-commit Test Hook
# This script runs essential tests before allowing commits
# Usage: ./scripts/pre-commit-tests.sh

set -e

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Running pre-commit tests...${NC}"

# Track test results
TOTAL_CHECKS=0
FAILED_CHECKS=0

# Check function
check() {
    local name="$1"
    local command="$2"
    local directory="$3"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    echo -e "\n${BLUE}🔄 $name${NC}"
    
    if [ -n "$directory" ]; then
        cd "$PROJECT_ROOT/$directory"
    fi
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $name passed${NC}"
    else
        echo -e "${RED}❌ $name failed${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        
        # Show actual error for failed checks
        echo -e "${YELLOW}Error details:${NC}"
        eval "$command" || true
    fi
    
    if [ -n "$directory" ]; then
        cd "$PROJECT_ROOT"
    fi
}

# Get list of changed files
CHANGED_FILES=$(git diff --cached --name-only)

if [ -z "$CHANGED_FILES" ]; then
    echo -e "${YELLOW}⚠️  No staged changes found${NC}"
    exit 0
fi

echo -e "${BLUE}📁 Changed files:${NC}"
echo "$CHANGED_FILES" | sed 's/^/  /'

# Backend checks (if backend files changed)
if echo "$CHANGED_FILES" | grep -q "^backend/"; then
    echo -e "\n${BLUE}🐍 Backend Checks${NC}"
    
    # Check if virtual environment exists
    if [ -d "$PROJECT_ROOT/backend/venv" ]; then
        source "$PROJECT_ROOT/backend/venv/bin/activate"
    elif [ -d "$PROJECT_ROOT/backend/venv_backend" ]; then
        source "$PROJECT_ROOT/backend/venv_backend/bin/activate"
    fi
    
    # Only check changed Python files
    CHANGED_PY_FILES=$(echo "$CHANGED_FILES" | grep "^backend/.*\.py$" || true)
    
    if [ -n "$CHANGED_PY_FILES" ]; then
        # Syntax check
        for file in $CHANGED_PY_FILES; do
            check "Python syntax check ($file)" "python -m py_compile $file" ""
        done
        
        # Linting (only changed files)
        if command -v ruff &> /dev/null; then
            for file in $CHANGED_PY_FILES; do
                check "Ruff linting ($file)" "ruff check $file" ""
            done
        fi
        
        # Code formatting check
        if command -v black &> /dev/null; then
            for file in $CHANGED_PY_FILES; do
                check "Black formatting ($file)" "black --check $file" ""
            done
        fi
    fi
    
    # Quick security check for common issues
    if echo "$CHANGED_FILES" | grep -q "^backend/"; then
        check "No hardcoded passwords" "! grep -r 'password.*=' backend/ --include='*.py'" ""
        check "No print statements" "! grep -r 'print(' backend/app/ --include='*.py'" ""
        check "No console.log statements" "! grep -r 'console\.log' backend/ --include='*.py'" ""
    fi
fi

# Frontend checks (if frontend files changed)
if echo "$CHANGED_FILES" | grep -q "^frontend/"; then
    echo -e "\n${BLUE}⚛️  Frontend Checks${NC}"
    
    # Check if node_modules exists
    if [ ! -d "$PROJECT_ROOT/frontend/node_modules" ]; then
        echo -e "${YELLOW}⚠️  Frontend dependencies not installed, skipping frontend checks${NC}"
    else
        # TypeScript compilation check
        check "TypeScript compilation" "npx tsc --noEmit" "frontend"
        
        # Linting (if available)
        if [ -f "$PROJECT_ROOT/frontend/package.json" ] && grep -q "lint" "$PROJECT_ROOT/frontend/package.json"; then
            check "ESLint check" "npm run lint" "frontend"
        fi
        
        # Check for console.log statements
        CHANGED_TS_FILES=$(echo "$CHANGED_FILES" | grep "^frontend/.*\.(ts|tsx|js|jsx)$" || true)
        if [ -n "$CHANGED_TS_FILES" ]; then
            for file in $CHANGED_TS_FILES; do
                if grep -q "console\.log" "$PROJECT_ROOT/$file"; then
                    echo -e "${RED}❌ Console.log found in $file${NC}"
                    FAILED_CHECKS=$((FAILED_CHECKS + 1))
                    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
                fi
            done
        fi
    fi
fi

# Mobile checks (if mobile files changed)
if echo "$CHANGED_FILES" | grep -q "^mobile/"; then
    echo -e "\n${BLUE}📱 Mobile Checks${NC}"
    
    if [ -d "$PROJECT_ROOT/mobile/node_modules" ]; then
        # TypeScript compilation check
        check "Mobile TypeScript compilation" "npx tsc --noEmit" "mobile"
    else
        echo -e "${YELLOW}⚠️  Mobile dependencies not installed, skipping mobile checks${NC}"
    fi
fi

# Configuration checks
if echo "$CHANGED_FILES" | grep -q -E "\.(yml|yaml|json|env)$"; then
    echo -e "\n${BLUE}⚙️  Configuration Checks${NC}"
    
    # YAML syntax check
    CHANGED_YAML_FILES=$(echo "$CHANGED_FILES" | grep -E "\.(yml|yaml)$" || true)
    if [ -n "$CHANGED_YAML_FILES" ] && command -v yamllint &> /dev/null; then
        for file in $CHANGED_YAML_FILES; do
            check "YAML syntax ($file)" "yamllint $file" ""
        done
    fi
    
    # JSON syntax check
    CHANGED_JSON_FILES=$(echo "$CHANGED_FILES" | grep "\.json$" || true)
    if [ -n "$CHANGED_JSON_FILES" ]; then
        for file in $CHANGED_JSON_FILES; do
            check "JSON syntax ($file)" "python -m json.tool $file > /dev/null" ""
        done
    fi
    
    # Environment file checks
    CHANGED_ENV_FILES=$(echo "$CHANGED_FILES" | grep "\.env" || true)
    if [ -n "$CHANGED_ENV_FILES" ]; then
        for file in $CHANGED_ENV_FILES; do
            # Check for secrets in env files (except .env.example)
            if [[ "$file" != *".example"* ]]; then
                if grep -q "password\|secret\|key" "$PROJECT_ROOT/$file"; then
                    echo -e "${YELLOW}⚠️  WARNING: Potential secrets found in $file${NC}"
                    echo -e "${YELLOW}Make sure this file is in .gitignore${NC}"
                fi
            fi
        done
    fi
fi

# Docker checks
if echo "$CHANGED_FILES" | grep -q -E "(Dockerfile|docker-compose)"; then
    echo -e "\n${BLUE}🐳 Docker Checks${NC}"
    
    # Docker syntax check
    CHANGED_DOCKERFILES=$(echo "$CHANGED_FILES" | grep "Dockerfile" || true)
    if [ -n "$CHANGED_DOCKERFILES" ] && command -v docker &> /dev/null; then
        for file in $CHANGED_DOCKERFILES; do
            # Basic Dockerfile syntax check
            check "Dockerfile syntax ($file)" "docker build --dry-run -f $file ." ""
        done
    fi
    
    # Docker Compose syntax check
    if echo "$CHANGED_FILES" | grep -q "docker-compose" && command -v docker-compose &> /dev/null; then
        check "Docker Compose syntax" "docker-compose config > /dev/null" ""
    fi
fi

# Git checks
echo -e "\n${BLUE}📝 Git Checks${NC}"

# Check commit message (if available)
if [ -f ".git/COMMIT_EDITMSG" ]; then
    COMMIT_MSG=$(cat .git/COMMIT_EDITMSG)
    if [ ${#COMMIT_MSG} -lt 10 ]; then
        echo -e "${RED}❌ Commit message too short (minimum 10 characters)${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    else
        echo -e "${GREEN}✅ Commit message length OK${NC}"
    fi
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
fi

# Check for large files
LARGE_FILES=$(git diff --cached --name-only | xargs -I {} find "$PROJECT_ROOT/{}" -size +10M 2>/dev/null || true)
if [ -n "$LARGE_FILES" ]; then
    echo -e "${RED}❌ Large files detected (>10MB):${NC}"
    echo "$LARGE_FILES" | sed 's/^/  /'
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
fi

# Check for merge conflict markers
if git diff --cached | grep -q -E "^(\+.*)?(<<<<<<<|=======|>>>>>>>)"; then
    echo -e "${RED}❌ Merge conflict markers found in staged changes${NC}"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
fi

# Summary
echo -e "\n${BLUE}📊 Pre-commit Check Summary${NC}"
echo -e "Total checks: $TOTAL_CHECKS"
echo -e "${GREEN}Passed: $((TOTAL_CHECKS - FAILED_CHECKS))${NC}"
echo -e "${RED}Failed: $FAILED_CHECKS${NC}"

if [ $FAILED_CHECKS -eq 0 ]; then
    echo -e "\n${GREEN}✅ All pre-commit checks passed!${NC}"
    echo -e "${GREEN}Commit can proceed.${NC}"
    exit 0
else
    echo -e "\n${RED}❌ $FAILED_CHECKS check(s) failed${NC}"
    echo -e "${RED}Please fix the issues before committing${NC}"
    echo -e "\n${YELLOW}💡 Tip: You can auto-fix some issues with:${NC}"
    echo -e "${YELLOW}  - Backend: black . && ruff --fix .${NC}"
    echo -e "${YELLOW}  - Frontend: npm run lint --fix${NC}"
    exit 1
fi