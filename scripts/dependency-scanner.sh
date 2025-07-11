#!/bin/bash

# Dependency Vulnerability Scanner
# Usage: ./scripts/dependency-scanner.sh [environment]
# Example: ./scripts/dependency-scanner.sh production

set -e

# Parameters
ENV=${1:-development}

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
LOG_DIR="$PROJECT_ROOT/logs/security"
mkdir -p "$LOG_DIR"
SCAN_LOG="$LOG_DIR/dependency-scan-$(date +%Y%m%d_%H%M%S).log"

# Vulnerability counters
TOTAL_VULNERABILITIES=0
HIGH_VULNS=0
MEDIUM_VULNS=0
LOW_VULNS=0

log() {
    echo -e "$1" | tee -a "$SCAN_LOG"
}

log "${BLUE}🔍 Starting dependency vulnerability scan${NC}"
log "${BLUE}Environment: $ENV${NC}"

# Python dependencies scan
scan_python_dependencies() {
    log "\n${BLUE}🐍 Scanning Python dependencies${NC}"
    
    if [ ! -d "$PROJECT_ROOT/backend" ]; then
        log "${YELLOW}⚠️  Backend directory not found, skipping Python scan${NC}"
        return
    fi
    
    cd "$PROJECT_ROOT/backend"
    
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
        log "${GREEN}✅ Activated Python virtual environment${NC}"
    elif [ -d "venv_backend" ]; then
        source venv_backend/bin/activate
        log "${GREEN}✅ Activated Python virtual environment${NC}"
    fi
    
    # Install/upgrade security tools
    log "${YELLOW}Installing security scanning tools...${NC}"
    pip install --upgrade safety pip-audit bandit >/dev/null 2>&1
    
    # Safety scan
    log "${BLUE}Running Safety scan...${NC}"
    local safety_output="/tmp/safety-scan-$$"
    if safety check --json > "$safety_output" 2>&1; then
        log "${GREEN}✅ Safety scan completed - no vulnerabilities found${NC}"
    else
        local vuln_count=$(jq length "$safety_output" 2>/dev/null || echo "0")
        log "${RED}❌ Safety found $vuln_count vulnerabilities${NC}"
        
        # Parse safety results
        if [ -f "$safety_output" ] && [ "$vuln_count" -gt 0 ]; then
            jq -r '.[] | "  - \(.package_name) \(.installed_version): \(.vulnerability_id) (\(.more_info_url))"' "$safety_output" 2>/dev/null | head -10 | while read -r line; do
                log "${RED}$line${NC}"
            done
            
            TOTAL_VULNERABILITIES=$((TOTAL_VULNERABILITIES + vuln_count))
            HIGH_VULNS=$((HIGH_VULNS + vuln_count))  # Safety reports are generally high severity
        fi
    fi
    rm -f "$safety_output"
    
    # pip-audit scan
    log "${BLUE}Running pip-audit scan...${NC}"
    local audit_output="/tmp/pip-audit-$$"
    if pip-audit --format=json > "$audit_output" 2>&1; then
        log "${GREEN}✅ pip-audit completed - no vulnerabilities found${NC}"
    else
        local audit_vulns=$(jq '.vulnerabilities | length' "$audit_output" 2>/dev/null || echo "0")
        if [ "$audit_vulns" -gt 0 ]; then
            log "${RED}❌ pip-audit found $audit_vulns vulnerabilities${NC}"
            
            # Show sample vulnerabilities
            jq -r '.vulnerabilities[] | "  - \(.package) \(.installed_version): \(.id) - \(.description[0:100])..."' "$audit_output" 2>/dev/null | head -5 | while read -r line; do
                log "${RED}$line${NC}"
            done
            
            TOTAL_VULNERABILITIES=$((TOTAL_VULNERABILITIES + audit_vulns))
            MEDIUM_VULNS=$((MEDIUM_VULNS + audit_vulns))
        fi
    fi
    rm -f "$audit_output"
    
    # Bandit security linting
    log "${BLUE}Running Bandit security linting...${NC}"
    local bandit_output="/tmp/bandit-$$"
    if bandit -r app/ -f json -o "$bandit_output" >/dev/null 2>&1; then
        local bandit_issues=$(jq '.results | length' "$bandit_output" 2>/dev/null || echo "0")
        if [ "$bandit_issues" -eq 0 ]; then
            log "${GREEN}✅ Bandit found no security issues${NC}"
        else
            log "${YELLOW}⚠️  Bandit found $bandit_issues potential security issues${NC}"
            
            # Count by severity
            local high_issues=$(jq '.results[] | select(.issue_severity == "HIGH") | .test_id' "$bandit_output" 2>/dev/null | wc -l || echo "0")
            local medium_issues=$(jq '.results[] | select(.issue_severity == "MEDIUM") | .test_id' "$bandit_output" 2>/dev/null | wc -l || echo "0")
            local low_issues=$(jq '.results[] | select(.issue_severity == "LOW") | .test_id' "$bandit_output" 2>/dev/null | wc -l || echo "0")
            
            HIGH_VULNS=$((HIGH_VULNS + high_issues))
            MEDIUM_VULNS=$((MEDIUM_VULNS + medium_issues))
            LOW_VULNS=$((LOW_VULNS + low_issues))
            TOTAL_VULNERABILITIES=$((TOTAL_VULNERABILITIES + bandit_issues))
            
            # Show sample issues
            if [ "$high_issues" -gt 0 ]; then
                log "${RED}  High severity: $high_issues${NC}"
                jq -r '.results[] | select(.issue_severity == "HIGH") | "    - \(.filename):\(.line_number) - \(.test_name)"' "$bandit_output" 2>/dev/null | head -3 | while read -r line; do
                    log "${RED}$line${NC}"
                done
            fi
        fi
    else
        log "${YELLOW}⚠️  Bandit scan failed${NC}"
    fi
    rm -f "$bandit_output"
    
    cd "$PROJECT_ROOT"
}

# Node.js dependencies scan
scan_nodejs_dependencies() {
    log "\n${BLUE}📦 Scanning Node.js dependencies${NC}"
    
    # Frontend scan
    if [ -d "$PROJECT_ROOT/frontend" ] && [ -f "$PROJECT_ROOT/frontend/package.json" ]; then
        log "${BLUE}Scanning frontend dependencies...${NC}"
        cd "$PROJECT_ROOT/frontend"
        
        # npm audit
        local npm_audit_output="/tmp/npm-audit-$$"
        if npm audit --audit-level moderate --json > "$npm_audit_output" 2>&1; then
            log "${GREEN}✅ Frontend npm audit - no vulnerabilities found${NC}"
        else
            local npm_vulns=$(jq '.metadata.vulnerabilities.total' "$npm_audit_output" 2>/dev/null || echo "0")
            if [ "$npm_vulns" -gt 0 ]; then
                log "${RED}❌ Frontend npm audit found $npm_vulns vulnerabilities${NC}"
                
                # Count by severity
                local high_npm=$(jq '.metadata.vulnerabilities.high // 0' "$npm_audit_output" 2>/dev/null || echo "0")
                local moderate_npm=$(jq '.metadata.vulnerabilities.moderate // 0' "$npm_audit_output" 2>/dev/null || echo "0")
                local low_npm=$(jq '.metadata.vulnerabilities.low // 0' "$npm_audit_output" 2>/dev/null || echo "0")
                
                HIGH_VULNS=$((HIGH_VULNS + high_npm))
                MEDIUM_VULNS=$((MEDIUM_VULNS + moderate_npm))
                LOW_VULNS=$((LOW_VULNS + low_npm))
                TOTAL_VULNERABILITIES=$((TOTAL_VULNERABILITIES + npm_vulns))
                
                log "${RED}  High: $high_npm, Moderate: $moderate_npm, Low: $low_npm${NC}"
                
                # Show top vulnerabilities
                jq -r '.vulnerabilities | to_entries[] | select(.value.severity == "high" or .value.severity == "critical") | "  - \(.key): \(.value.title)"' "$npm_audit_output" 2>/dev/null | head -5 | while read -r line; do
                    log "${RED}$line${NC}"
                done
            fi
        fi
        rm -f "$npm_audit_output"
        
        # Retire.js scan (if available)
        if command -v retire &> /dev/null; then
            log "${BLUE}Running Retire.js scan...${NC}"
            local retire_output="/tmp/retire-$$"
            if retire --js --outputformat json --outputpath "$retire_output" >/dev/null 2>&1; then
                if [ -s "$retire_output" ]; then
                    local retire_count=$(jq '. | length' "$retire_output" 2>/dev/null || echo "0")
                    if [ "$retire_count" -gt 0 ]; then
                        log "${YELLOW}⚠️  Retire.js found $retire_count outdated libraries${NC}"
                        MEDIUM_VULNS=$((MEDIUM_VULNS + retire_count))
                        TOTAL_VULNERABILITIES=$((TOTAL_VULNERABILITIES + retire_count))
                    fi
                fi
            fi
            rm -f "$retire_output"
        fi
    fi
    
    # Mobile dependencies scan
    if [ -d "$PROJECT_ROOT/mobile" ] && [ -f "$PROJECT_ROOT/mobile/package.json" ]; then
        log "${BLUE}Scanning mobile dependencies...${NC}"
        cd "$PROJECT_ROOT/mobile"
        
        local mobile_audit_output="/tmp/mobile-audit-$$"
        if npm audit --audit-level moderate --json > "$mobile_audit_output" 2>&1; then
            log "${GREEN}✅ Mobile npm audit - no vulnerabilities found${NC}"
        else
            local mobile_vulns=$(jq '.metadata.vulnerabilities.total' "$mobile_audit_output" 2>/dev/null || echo "0")
            if [ "$mobile_vulns" -gt 0 ]; then
                log "${RED}❌ Mobile npm audit found $mobile_vulns vulnerabilities${NC}"
                
                local high_mobile=$(jq '.metadata.vulnerabilities.high // 0' "$mobile_audit_output" 2>/dev/null || echo "0")
                local moderate_mobile=$(jq '.metadata.vulnerabilities.moderate // 0' "$mobile_audit_output" 2>/dev/null || echo "0")
                local low_mobile=$(jq '.metadata.vulnerabilities.low // 0' "$mobile_audit_output" 2>/dev/null || echo "0")
                
                HIGH_VULNS=$((HIGH_VULNS + high_mobile))
                MEDIUM_VULNS=$((MEDIUM_VULNS + moderate_mobile))
                LOW_VULNS=$((LOW_VULNS + low_mobile))
                TOTAL_VULNERABILITIES=$((TOTAL_VULNERABILITIES + mobile_vulns))
                
                log "${RED}  High: $high_mobile, Moderate: $moderate_mobile, Low: $low_mobile${NC}"
            fi
        fi
        rm -f "$mobile_audit_output"
    fi
    
    cd "$PROJECT_ROOT"
}

# Generate dependency vulnerability report
generate_report() {
    log "\n${BLUE}📊 Generating vulnerability report${NC}"
    
    local report_file="$LOG_DIR/dependency-vulnerability-report-$(date +%Y%m%d_%H%M%S).json"
    
    cat > "$report_file" << EOF
{
  "scan_timestamp": "$(date -Iseconds)",
  "environment": "$ENV",
  "summary": {
    "total_vulnerabilities": $TOTAL_VULNERABILITIES,
    "high_severity": $HIGH_VULNS,
    "medium_severity": $MEDIUM_VULNS,
    "low_severity": $LOW_VULNS
  },
  "risk_assessment": {
    "level": "$([ $HIGH_VULNS -gt 0 ] && echo "HIGH" || [ $MEDIUM_VULNS -gt 5 ] && echo "MEDIUM" || [ $TOTAL_VULNERABILITIES -gt 10 ] && echo "LOW" || echo "MINIMAL")",
    "score": $(( HIGH_VULNS * 10 + MEDIUM_VULNS * 5 + LOW_VULNS * 1 ))
  },
  "recommendations": [
    $([ $HIGH_VULNS -gt 0 ] && echo '"Immediately update packages with high severity vulnerabilities",' || echo "")
    $([ $MEDIUM_VULNS -gt 0 ] && echo '"Schedule updates for medium severity vulnerabilities",' || echo "")
    $([ $LOW_VULNS -gt 0 ] && echo '"Plan updates for low severity vulnerabilities",' || echo "")
    "Set up automated dependency scanning in CI/CD pipeline",
    "Enable Dependabot or similar automated dependency updates",
    "Regularly review and update dependencies"
  ]
}
EOF
    
    # Generate HTML report
    local html_report="$LOG_DIR/dependency-vulnerability-report-$(date +%Y%m%d_%H%M%S).html"
    cat > "$html_report" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Dependency Vulnerability Report - $ENV</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { background: #e74c3c; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 20px; margin: 20px 0; }
        .metric { background: #ecf0f1; padding: 15px; border-radius: 5px; text-align: center; }
        .high { color: #e74c3c; font-weight: bold; font-size: 2em; }
        .medium { color: #f39c12; font-weight: bold; font-size: 2em; }
        .low { color: #3498db; font-size: 2em; }
        .total { color: #2c3e50; font-size: 2em; font-weight: bold; }
        .recommendations { background: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107; }
        .risk-high { background: #e74c3c; color: white; }
        .risk-medium { background: #f39c12; color: white; }
        .risk-low { background: #3498db; color: white; }
        .risk-minimal { background: #27ae60; color: white; }
        .risk-badge { padding: 10px 20px; border-radius: 20px; display: inline-block; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Dependency Vulnerability Report</h1>
            <p><strong>Environment:</strong> $ENV</p>
            <p><strong>Scan Date:</strong> $(date)</p>
        </div>
        
        <div class="summary">
            <div class="metric">
                <h3>Total Vulnerabilities</h3>
                <div class="total">$TOTAL_VULNERABILITIES</div>
            </div>
            <div class="metric">
                <h3>High Severity</h3>
                <div class="high">$HIGH_VULNS</div>
            </div>
            <div class="metric">
                <h3>Medium Severity</h3>
                <div class="medium">$MEDIUM_VULNS</div>
            </div>
            <div class="metric">
                <h3>Low Severity</h3>
                <div class="low">$LOW_VULNS</div>
            </div>
        </div>
        
        <div style="text-align: center;">
            <span class="risk-badge risk-$([ $HIGH_VULNS -gt 0 ] && echo "high" || [ $MEDIUM_VULNS -gt 5 ] && echo "medium" || [ $TOTAL_VULNERABILITIES -gt 10 ] && echo "low" || echo "minimal")">
                Risk Level: $([ $HIGH_VULNS -gt 0 ] && echo "HIGH" || [ $MEDIUM_VULNS -gt 5 ] && echo "MEDIUM" || [ $TOTAL_VULNERABILITIES -gt 10 ] && echo "LOW" || echo "MINIMAL")
            </span>
        </div>
        
        <div class="recommendations">
            <h2>📋 Recommendations</h2>
            <ul>
$([ $HIGH_VULNS -gt 0 ] && echo "                <li style=\"color: #e74c3c;\">🚨 <strong>URGENT:</strong> Update packages with $HIGH_VULNS high severity vulnerabilities immediately</li>")
$([ $MEDIUM_VULNS -gt 0 ] && echo "                <li style=\"color: #f39c12;\">⚠️ Schedule updates for $MEDIUM_VULNS medium severity vulnerabilities</li>")
$([ $LOW_VULNS -gt 0 ] && echo "                <li style=\"color: #3498db;\">ℹ️ Plan updates for $LOW_VULNS low severity vulnerabilities</li>")
                <li>Set up automated dependency scanning in CI/CD pipeline</li>
                <li>Enable Dependabot or similar automated dependency updates</li>
                <li>Regularly review and update dependencies</li>
                <li>Implement security policies for dependency management</li>
            </ul>
        </div>
    </div>
</body>
</html>
EOF
    
    log "${GREEN}✅ Reports generated:${NC}"
    log "  JSON: $report_file"
    log "  HTML: $html_report"
    log "  Log: $SCAN_LOG"
}

# Install required tools if not present
install_tools() {
    log "${BLUE}🔧 Checking and installing security tools${NC}"
    
    # Check for jq
    if ! command -v jq &> /dev/null; then
        log "${YELLOW}Installing jq...${NC}"
        if command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y jq
        elif command -v yum &> /dev/null; then
            sudo yum install -y jq
        elif command -v brew &> /dev/null; then
            brew install jq
        fi
    fi
    
    # Check for retire.js
    if ! command -v retire &> /dev/null; then
        log "${YELLOW}Installing retire.js...${NC}"
        npm install -g retire
    fi
}

# Main execution
install_tools
scan_python_dependencies
scan_nodejs_dependencies

# Summary
log "\n${BLUE}📊 Dependency Vulnerability Scan Summary${NC}"
log "Environment: $ENV"
log "Total vulnerabilities found: $TOTAL_VULNERABILITIES"
log "${RED}High severity: $HIGH_VULNS${NC}"
log "${YELLOW}Medium severity: $MEDIUM_VULNS${NC}"
log "${BLUE}Low severity: $LOW_VULNS${NC}"

# Risk assessment
if [ $HIGH_VULNS -gt 0 ]; then
    RISK_LEVEL="HIGH"
    RISK_COLOR="$RED"
    log "\n${RED}🚨 HIGH RISK: Immediate action required${NC}"
elif [ $MEDIUM_VULNS -gt 5 ]; then
    RISK_LEVEL="MEDIUM"
    RISK_COLOR="$YELLOW"
    log "\n${YELLOW}⚠️  MEDIUM RISK: Schedule updates soon${NC}"
elif [ $TOTAL_VULNERABILITIES -gt 10 ]; then
    RISK_LEVEL="LOW"
    RISK_COLOR="$BLUE"
    log "\n${BLUE}ℹ️  LOW RISK: Plan regular updates${NC}"
else
    RISK_LEVEL="MINIMAL"
    RISK_COLOR="$GREEN"
    log "\n${GREEN}✅ MINIMAL RISK: Good security posture${NC}"
fi

generate_report

# Exit with appropriate code
if [ $HIGH_VULNS -gt 0 ]; then
    log "\n${RED}❌ High severity vulnerabilities found - immediate attention required${NC}"
    exit 1
elif [ $TOTAL_VULNERABILITIES -gt 0 ]; then
    log "\n${YELLOW}⚠️  Vulnerabilities found - review and update recommended${NC}"
    exit 2
else
    log "\n${GREEN}✅ No vulnerabilities found${NC}"
    exit 0
fi