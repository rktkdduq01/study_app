#!/bin/bash

# Security Vulnerability Scanner for Quest Education Platform
# Usage: ./scripts/security-scan.sh [scan-type] [environment]
# Example: ./scripts/security-scan.sh all production
# Example: ./scripts/security-scan.sh dependencies staging

set -e

# Parameters
SCAN_TYPE=${1:-all}
ENV=${2:-development}

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Scan results
TOTAL_SCANS=0
PASSED_SCANS=0
FAILED_SCANS=0
HIGH_SEVERITY_ISSUES=0
MEDIUM_SEVERITY_ISSUES=0
LOW_SEVERITY_ISSUES=0

# Logging
LOG_DIR="$PROJECT_ROOT/logs/security"
mkdir -p "$LOG_DIR"
SCAN_LOG="$LOG_DIR/security-scan-$(date +%Y%m%d_%H%M%S).log"
REPORT_FILE="$LOG_DIR/security-report-$(date +%Y%m%d_%H%M%S).json"

log() {
    echo -e "$1" | tee -a "$SCAN_LOG"
}

log "${BLUE}🔒 Starting security vulnerability scan${NC}"
log "${BLUE}Scan Type: $SCAN_TYPE${NC}"
log "${BLUE}Environment: $ENV${NC}"
log "${BLUE}Log File: $SCAN_LOG${NC}"

# Initialize report
cat > "$REPORT_FILE" << EOF
{
  "scan_timestamp": "$(date -Iseconds)",
  "environment": "$ENV",
  "scan_type": "$SCAN_TYPE",
  "results": {
    "dependency_scans": [],
    "code_scans": [],
    "container_scans": [],
    "infrastructure_scans": []
  },
  "summary": {
    "total_scans": 0,
    "passed_scans": 0,
    "failed_scans": 0,
    "high_severity": 0,
    "medium_severity": 0,
    "low_severity": 0
  }
}
EOF

# 1. Dependency vulnerability scan
echo -e "${YELLOW}1. Scanning Python dependencies...${NC}"
pip install safety
safety check --json > "$RESULTS_DIR/python-vulns-$TIMESTAMP.json" || true
safety check || echo -e "${YELLOW}Some vulnerabilities found in Python dependencies${NC}"

# 2. Code security scan with Bandit
echo -e "\n${YELLOW}2. Running Bandit security scan...${NC}"
pip install bandit
bandit -r backend/ -f json -o "$RESULTS_DIR/bandit-$TIMESTAMP.json" || true
bandit -r backend/ -ll || echo -e "${YELLOW}Some security issues found by Bandit${NC}"

# 3. Secret detection
echo -e "\n${YELLOW}3. Scanning for secrets...${NC}"
# Using detect-secrets
pip install detect-secrets
detect-secrets scan --all-files > "$RESULTS_DIR/secrets-baseline-$TIMESTAMP.json"
detect-secrets audit "$RESULTS_DIR/secrets-baseline-$TIMESTAMP.json" || true

# 4. OWASP dependency check
echo -e "\n${YELLOW}4. Running OWASP dependency check...${NC}"
if command -v dependency-check &> /dev/null; then
    dependency-check --project "Educational RPG" \
        --scan . \
        --format JSON \
        --out "$RESULTS_DIR/owasp-dc-$TIMESTAMP.json" \
        --suppression dependency-check-suppression.xml || true
else
    echo -e "${YELLOW}OWASP Dependency Check not installed. Skipping...${NC}"
fi

# 5. Docker security scan (if Docker is used)
echo -e "\n${YELLOW}5. Scanning Docker images...${NC}"
if [ -f "docker-compose.yml" ]; then
    # Scan with Trivy
    if command -v trivy &> /dev/null; then
        trivy image educational-rpg-backend:latest > "$RESULTS_DIR/trivy-backend-$TIMESTAMP.txt" || true
        trivy image educational-rpg-frontend:latest > "$RESULTS_DIR/trivy-frontend-$TIMESTAMP.txt" || true
    else
        echo -e "${YELLOW}Trivy not installed. Skipping Docker scan...${NC}"
    fi
fi

# 6. Infrastructure as Code scan
echo -e "\n${YELLOW}6. Scanning Infrastructure as Code...${NC}"
if [ -d "infrastructure/terraform" ]; then
    # Using tfsec
    if command -v tfsec &> /dev/null; then
        tfsec infrastructure/terraform --format json > "$RESULTS_DIR/tfsec-$TIMESTAMP.json" || true
        tfsec infrastructure/terraform || echo -e "${YELLOW}Some security issues found in Terraform${NC}"
    else
        echo -e "${YELLOW}tfsec not installed. Skipping IaC scan...${NC}"
    fi
fi

# 7. SSL/TLS configuration check
echo -e "\n${YELLOW}7. Checking SSL/TLS configuration...${NC}"
if [ -f "nginx/nginx-production.conf" ]; then
    # Check for weak ciphers
    grep -E "(SSLv2|SSLv3|TLSv1\.0|TLSv1\.1)" nginx/*.conf && \
        echo -e "${RED}Weak SSL/TLS versions found!${NC}" || \
        echo -e "${GREEN}No weak SSL/TLS versions found${NC}"
    
    # Check for security headers
    echo -e "\nChecking security headers..."
    headers=("X-Frame-Options" "X-Content-Type-Options" "Strict-Transport-Security" "Content-Security-Policy")
    for header in "${headers[@]}"; do
        grep -q "$header" nginx/*.conf && \
            echo -e "${GREEN}✓ $header configured${NC}" || \
            echo -e "${RED}✗ $header not found${NC}"
    done
fi

# 8. API security check
echo -e "\n${YELLOW}8. Checking API security...${NC}"
# Check for rate limiting
grep -r "RateLimitMiddleware\|rate_limit" backend/ > /dev/null && \
    echo -e "${GREEN}✓ Rate limiting implemented${NC}" || \
    echo -e "${RED}✗ Rate limiting not found${NC}"

# Check for authentication
grep -r "get_current_user\|@requires_auth" backend/ > /dev/null && \
    echo -e "${GREEN}✓ Authentication middleware found${NC}" || \
    echo -e "${RED}✗ Authentication middleware not found${NC}"

# Check for input validation
grep -r "pydantic\|validate" backend/ > /dev/null && \
    echo -e "${GREEN}✓ Input validation found${NC}" || \
    echo -e "${RED}✗ Input validation not found${NC}"

# 9. Frontend security check
echo -e "\n${YELLOW}9. Checking frontend security...${NC}"
if [ -d "frontend" ]; then
    # Check for dangerous functions
    echo "Checking for dangerous JavaScript patterns..."
    grep -r "eval(\|innerHTML\|document.write" frontend/src --include="*.js" --include="*.jsx" --include="*.ts" --include="*.tsx" && \
        echo -e "${YELLOW}Potentially dangerous JavaScript patterns found${NC}" || \
        echo -e "${GREEN}No dangerous JavaScript patterns found${NC}"
fi

# 10. Generate security report
echo -e "\n${YELLOW}10. Generating security report...${NC}"
cat > "$RESULTS_DIR/security-report-$TIMESTAMP.md" <<EOF
# Security Scan Report
Generated: $(date)

## Summary
This report contains the results of automated security scans for the Educational RPG Platform.

## Scan Results

### 1. Dependency Vulnerabilities
See: python-vulns-$TIMESTAMP.json

### 2. Code Security (Bandit)
See: bandit-$TIMESTAMP.json

### 3. Secret Detection
See: secrets-baseline-$TIMESTAMP.json

### 4. OWASP Dependency Check
See: owasp-dc-$TIMESTAMP.json

### 5. Docker Security (Trivy)
See: trivy-*-$TIMESTAMP.txt

### 6. Infrastructure as Code (tfsec)
See: tfsec-$TIMESTAMP.json

## Recommendations
1. Review and fix all HIGH and CRITICAL vulnerabilities
2. Update dependencies with known vulnerabilities
3. Remove or encrypt any detected secrets
4. Implement missing security headers
5. Enable all security middleware

## Next Steps
1. Review each finding in detail
2. Create tickets for remediation
3. Re-run scans after fixes
4. Schedule regular security scans
EOF

echo -e "\n${GREEN}✅ Security scan complete!${NC}"
echo -e "Results saved in: ${BLUE}$RESULTS_DIR/${NC}"
echo -e "Report: ${BLUE}$RESULTS_DIR/security-report-$TIMESTAMP.md${NC}"

# Count vulnerabilities
if [ -f "$RESULTS_DIR/python-vulns-$TIMESTAMP.json" ]; then
    VULN_COUNT=$(python -c "import json; data=json.load(open('$RESULTS_DIR/python-vulns-$TIMESTAMP.json')); print(len(data))" 2>/dev/null || echo "0")
    if [ "$VULN_COUNT" -gt 0 ]; then
        echo -e "\n${RED}⚠️  Found $VULN_COUNT dependency vulnerabilities${NC}"
    fi
fi

# Exit with error if critical issues found
if grep -q "severity.*high\|severity.*critical" "$RESULTS_DIR"/*-$TIMESTAMP.* 2>/dev/null; then
    echo -e "\n${RED}❌ Critical security issues found! Please review and fix.${NC}"
    exit 1
else
    echo -e "\n${GREEN}✅ No critical security issues found.${NC}"
fi