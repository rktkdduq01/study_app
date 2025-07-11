#!/bin/bash

# Security Dashboard and Monitoring Script
# Usage: ./scripts/security-dashboard.sh [command] [options]
# Example: ./scripts/security-dashboard.sh analyze --last-24h
# Example: ./scripts/security-dashboard.sh report --output-html

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
LOG_DIR="$PROJECT_ROOT/logs/security"
DASHBOARD_OUTPUT="$LOG_DIR/dashboard"
mkdir -p "$DASHBOARD_OUTPUT"

# Command and options
COMMAND=${1:-dashboard}
TIME_RANGE=${2:-"--last-24h"}
OUTPUT_FORMAT=${3:-"--output-console"}

log() {
    echo -e "$1"
}

# Load environment
if [ -f "$PROJECT_ROOT/scripts/load-env.sh" ]; then
    source "$PROJECT_ROOT/scripts/load-env.sh" "${ENVIRONMENT:-development}"
fi

# Generate real-time security dashboard
generate_dashboard() {
    local time_range="$1"
    local output_format="$2"
    
    log "${BLUE}${BOLD}🔒 Security Dashboard${NC}"
    log "${BLUE}========================${NC}"
    log "${CYAN}Environment: ${ENVIRONMENT:-development}${NC}"
    log "${CYAN}Time Range: $time_range${NC}"
    log "${CYAN}Generated: $(date)${NC}"
    log ""
    
    # Security events summary
    log "${YELLOW}${BOLD}📊 Security Events Summary${NC}"
    log "${YELLOW}═══════════════════════════${NC}"
    
    cd "$PROJECT_ROOT/backend"
    
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    elif [ -d "venv_backend" ]; then
        source venv_backend/bin/activate
    fi
    
    # Generate dashboard data
    python << EOF
import sys
import os
import json
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import glob

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.getcwd()))

try:
    from app.core.security_audit import SecurityEventType, SeverityLevel
    
    def parse_time_range(time_range):
        """Parse time range argument"""
        if time_range == "--last-24h":
            return datetime.now() - timedelta(hours=24)
        elif time_range == "--last-week":
            return datetime.now() - timedelta(days=7)
        elif time_range == "--last-month":
            return datetime.now() - timedelta(days=30)
        else:
            return datetime.now() - timedelta(hours=24)
    
    def analyze_security_logs(start_time):
        """Analyze security logs for dashboard"""
        log_dir = "../logs/security"
        
        # Statistics
        stats = {
            "total_events": 0,
            "events_by_type": defaultdict(int),
            "events_by_severity": defaultdict(int),
            "events_by_hour": defaultdict(int),
            "top_ips": Counter(),
            "top_paths": Counter(),
            "blocked_ips": set(),
            "high_risk_events": 0,
            "unique_sessions": set(),
            "failed_auth_attempts": 0,
            "successful_auth": 0,
            "admin_actions": 0,
            "suspicious_requests": 0
        }
        
        # Find relevant log files
        current = start_time.date()
        end_date = datetime.now().date()
        
        while current <= end_date:
            log_file = f"{log_dir}/security_events_{current.strftime('%Y%m%d')}.jsonl"
            
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    for line in f:
                        try:
                            event = json.loads(line)
                            event_time = datetime.fromisoformat(event['timestamp'])
                            
                            # Skip events outside time range
                            if event_time < start_time:
                                continue
                            
                            stats["total_events"] += 1
                            
                            # Categorize events
                            event_type = event.get('event_type', 'unknown')
                            severity = event.get('severity', 'info')
                            risk_score = event.get('risk_score', 0)
                            ip_address = event.get('ip_address', 'unknown')
                            path = event.get('request_path', 'unknown')
                            session_id = event.get('session_id')
                            
                            stats["events_by_type"][event_type] += 1
                            stats["events_by_severity"][severity] += 1
                            stats["events_by_hour"][event_time.hour] += 1
                            stats["top_ips"][ip_address] += 1
                            stats["top_paths"][path] += 1
                            
                            if session_id:
                                stats["unique_sessions"].add(session_id)
                            
                            if risk_score >= 7:
                                stats["high_risk_events"] += 1
                            
                            if event_type == "auth_failure":
                                stats["failed_auth_attempts"] += 1
                            elif event_type == "auth_success":
                                stats["successful_auth"] += 1
                            elif event_type == "admin_action":
                                stats["admin_actions"] += 1
                            elif "suspicious" in event_type or "injection" in event_type or "xss" in event_type:
                                stats["suspicious_requests"] += 1
                            
                            # Check for blocked IPs
                            if risk_score >= 8:
                                stats["blocked_ips"].add(ip_address)
                                
                        except (json.JSONDecodeError, ValueError, KeyError):
                            continue
            
            current += timedelta(days=1)
        
        # Convert sets to counts
        stats["unique_sessions"] = len(stats["unique_sessions"])
        stats["blocked_ips_count"] = len(stats["blocked_ips"])
        
        return stats
    
    def print_dashboard(stats):
        """Print dashboard to console"""
        print(f"Total Security Events: {stats['total_events']}")
        print(f"High Risk Events: {stats['high_risk_events']}")
        print(f"Unique Sessions: {stats['unique_sessions']}")
        print(f"Blocked IPs: {stats['blocked_ips_count']}")
        print()
        
        print("📈 Event Breakdown:")
        print(f"  ✅ Successful Authentications: {stats['successful_auth']}")
        print(f"  ❌ Failed Authentications: {stats['failed_auth_attempts']}")
        print(f"  🔧 Admin Actions: {stats['admin_actions']}")
        print(f"  ⚠️  Suspicious Requests: {stats['suspicious_requests']}")
        print()
        
        print("🚨 Events by Severity:")
        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            count = stats['events_by_severity'].get(severity, 0)
            icon = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🔵', 'info': '⚪'}.get(severity, '⚪')
            print(f"  {icon} {severity.capitalize()}: {count}")
        print()
        
        print("🕒 Events by Hour:")
        for hour in range(24):
            count = stats['events_by_hour'].get(hour, 0)
            bar = '█' * min(count // 10, 20) if count > 0 else ''
            print(f"  {hour:2d}:00 │{bar:<20}│ {count}")
        print()
        
        print("🌐 Top Source IPs:")
        for ip, count in stats['top_ips'].most_common(10):
            blocked_indicator = " 🚫" if ip in stats['blocked_ips'] else ""
            print(f"  {ip:<15} │ {count:>5} events{blocked_indicator}")
        print()
        
        print("📡 Top Request Paths:")
        for path, count in stats['top_paths'].most_common(10):
            print(f"  {path:<30} │ {count:>5} requests")
        print()
        
        print("🎯 Event Types:")
        for event_type, count in sorted(stats['events_by_type'].items(), key=lambda x: x[1], reverse=True):
            icon = {
                'auth_success': '✅',
                'auth_failure': '❌',
                'admin_action': '🔧',
                'suspicious_request': '⚠️',
                'sql_injection_attempt': '💉',
                'xss_attempt': '🕷️',
                'brute_force_attempt': '🔨',
                'rate_limit_exceeded': '⏱️'
            }.get(event_type, '📝')
            print(f"  {icon} {event_type:<25} │ {count:>5}")
    
    def generate_html_report(stats):
        """Generate HTML dashboard report"""
        html_content = f'''
<!DOCTYPE html>
<html>
<head>
    <title>Security Dashboard - {datetime.now().strftime("%Y-%m-%d %H:%M")}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .stat-card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .stat-number {{ font-size: 2.5em; font-weight: bold; color: #333; }}
        .stat-label {{ color: #666; font-size: 0.9em; }}
        .chart-container {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .severity-bar {{ display: flex; height: 30px; border-radius: 15px; overflow: hidden; margin: 10px 0; }}
        .severity-critical {{ background: #e74c3c; }}
        .severity-high {{ background: #f39c12; }}
        .severity-medium {{ background: #f1c40f; }}
        .severity-low {{ background: #3498db; }}
        .severity-info {{ background: #95a5a6; }}
        .hour-chart {{ display: grid; grid-template-columns: repeat(24, 1fr); gap: 2px; margin: 20px 0; }}
        .hour-bar {{ background: #3498db; min-height: 5px; border-radius: 2px; }}
        .table {{ width: 100%; border-collapse: collapse; }}
        .table th, .table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        .table th {{ background: #f8f9fa; font-weight: 600; }}
        .blocked {{ color: #e74c3c; font-weight: bold; }}
        .timestamp {{ color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔒 Security Dashboard</h1>
            <p>Real-time security monitoring and threat analysis</p>
            <p class="timestamp">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{stats['total_events']}</div>
                <div class="stat-label">Total Security Events</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color: #e74c3c;">{stats['high_risk_events']}</div>
                <div class="stat-label">High Risk Events</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['unique_sessions']}</div>
                <div class="stat-label">Unique Sessions</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color: #f39c12;">{stats['blocked_ips_count']}</div>
                <div class="stat-label">Blocked IP Addresses</div>
            </div>
        </div>
        
        <div class="chart-container">
            <h3>📊 Events by Severity</h3>
            <div class="severity-bar">
                <div class="severity-critical" style="width: {(stats['events_by_severity'].get('critical', 0) / max(stats['total_events'], 1)) * 100}%" title="Critical: {stats['events_by_severity'].get('critical', 0)}"></div>
                <div class="severity-high" style="width: {(stats['events_by_severity'].get('high', 0) / max(stats['total_events'], 1)) * 100}%" title="High: {stats['events_by_severity'].get('high', 0)}"></div>
                <div class="severity-medium" style="width: {(stats['events_by_severity'].get('medium', 0) / max(stats['total_events'], 1)) * 100}%" title="Medium: {stats['events_by_severity'].get('medium', 0)}"></div>
                <div class="severity-low" style="width: {(stats['events_by_severity'].get('low', 0) / max(stats['total_events'], 1)) * 100}%" title="Low: {stats['events_by_severity'].get('low', 0)}"></div>
                <div class="severity-info" style="width: {(stats['events_by_severity'].get('info', 0) / max(stats['total_events'], 1)) * 100}%" title="Info: {stats['events_by_severity'].get('info', 0)}"></div>
            </div>
        </div>
        
        <div class="chart-container">
            <h3>🕒 Events by Hour</h3>
            <div class="hour-chart">
'''
        
        max_hourly = max(stats['events_by_hour'].values()) if stats['events_by_hour'] else 1
        for hour in range(24):
            count = stats['events_by_hour'].get(hour, 0)
            height = int((count / max_hourly) * 100) if max_hourly > 0 else 0
            html_content += f'<div class="hour-bar" style="height: {height}px;" title="{hour}:00 - {count} events"></div>'
        
        html_content += '''
            </div>
        </div>
        
        <div class="chart-container">
            <h3>🌐 Top Source IP Addresses</h3>
            <table class="table">
                <thead>
                    <tr>
                        <th>IP Address</th>
                        <th>Event Count</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
'''
        
        for ip, count in stats['top_ips'].most_common(10):
            status = "🚫 Blocked" if ip in stats['blocked_ips'] else "✅ Active"
            status_class = "blocked" if ip in stats['blocked_ips'] else ""
            html_content += f'''
                    <tr>
                        <td>{ip}</td>
                        <td>{count}</td>
                        <td class="{status_class}">{status}</td>
                    </tr>
'''
        
        html_content += '''
                </tbody>
            </table>
        </div>
        
        <div class="chart-container">
            <h3>🎯 Event Types Distribution</h3>
            <table class="table">
                <thead>
                    <tr>
                        <th>Event Type</th>
                        <th>Count</th>
                        <th>Percentage</th>
                    </tr>
                </thead>
                <tbody>
'''
        
        for event_type, count in sorted(stats['events_by_type'].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / max(stats['total_events'], 1)) * 100
            icon = {
                'auth_success': '✅',
                'auth_failure': '❌',
                'admin_action': '🔧',
                'suspicious_request': '⚠️',
                'sql_injection_attempt': '💉',
                'xss_attempt': '🕷️',
                'brute_force_attempt': '🔨'
            }.get(event_type, '📝')
            html_content += f'''
                    <tr>
                        <td>{icon} {event_type.replace('_', ' ').title()}</td>
                        <td>{count}</td>
                        <td>{percentage:.1f}%</td>
                    </tr>
'''
        
        html_content += '''
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
'''
        
        # Save HTML report
        html_file = f"../logs/security/dashboard/security_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(html_file, 'w') as f:
            f.write(html_content)
        
        print(f"📄 HTML report generated: {html_file}")
        return html_file
    
    # Main execution
    start_time = parse_time_range("$time_range")
    stats = analyze_security_logs(start_time)
    
    if "$output_format" == "--output-html":
        html_file = generate_html_report(stats)
    else:
        print_dashboard(stats)

except ImportError as e:
    print(f"❌ Failed to import security modules: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Dashboard generation failed: {e}")
    sys.exit(1)
EOF
}

# Analyze security threats
analyze_threats() {
    log "${YELLOW}${BOLD}🔍 Threat Analysis${NC}"
    log "${YELLOW}═════════════════${NC}"
    
    cd "$PROJECT_ROOT/backend"
    
    python << EOF
import sys
import os
import json
from datetime import datetime, timedelta
from collections import Counter, defaultdict

sys.path.insert(0, os.path.join(os.getcwd()))

try:
    def analyze_threats():
        """Analyze security threats and patterns"""
        log_dir = "../logs/security"
        
        # Threat analysis
        threats = {
            "brute_force_attempts": [],
            "injection_attempts": [],
            "suspicious_ips": Counter(),
            "anomalous_patterns": [],
            "geographic_anomalies": [],
            "time_based_anomalies": []
        }
        
        # Look at last 24 hours
        start_time = datetime.now() - timedelta(hours=24)
        
        # Analyze recent logs
        current = start_time.date()
        end_date = datetime.now().date()
        
        while current <= end_date:
            log_file = f"{log_dir}/security_events_{current.strftime('%Y%m%d')}.jsonl"
            
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    for line in f:
                        try:
                            event = json.loads(line)
                            event_time = datetime.fromisoformat(event['timestamp'])
                            
                            if event_time < start_time:
                                continue
                            
                            event_type = event.get('event_type', '')
                            ip_address = event.get('ip_address', 'unknown')
                            risk_score = event.get('risk_score', 0)
                            
                            # Detect brute force
                            if event_type == 'auth_failure':
                                threats["brute_force_attempts"].append({
                                    'ip': ip_address,
                                    'time': event_time.isoformat(),
                                    'path': event.get('request_path', '')
                                })
                            
                            # Detect injection attempts
                            if 'injection' in event_type or 'xss' in event_type:
                                threats["injection_attempts"].append({
                                    'type': event_type,
                                    'ip': ip_address,
                                    'time': event_time.isoformat(),
                                    'details': event.get('details', {})
                                })
                            
                            # Track suspicious IPs
                            if risk_score >= 5:
                                threats["suspicious_ips"][ip_address] += 1
                            
                            # Detect time-based anomalies (outside business hours)
                            hour = event_time.hour
                            if hour < 6 or hour > 22:  # Outside 6 AM - 10 PM
                                threats["time_based_anomalies"].append({
                                    'ip': ip_address,
                                    'time': event_time.isoformat(),
                                    'hour': hour,
                                    'event_type': event_type
                                })
                            
                        except (json.JSONDecodeError, ValueError, KeyError):
                            continue
            
            current += timedelta(days=1)
        
        return threats
    
    def print_threat_analysis(threats):
        """Print threat analysis results"""
        print("🚨 Active Threats Detected:")
        print()
        
        # Brute force analysis
        brute_force_by_ip = defaultdict(list)
        for attempt in threats["brute_force_attempts"]:
            brute_force_by_ip[attempt['ip']].append(attempt)
        
        if brute_force_by_ip:
            print("🔨 Brute Force Attempts:")
            for ip, attempts in brute_force_by_ip.items():
                if len(attempts) >= 5:  # 5+ failed attempts
                    print(f"  🚨 {ip}: {len(attempts)} failed login attempts")
                    for attempt in attempts[-3:]:  # Show last 3
                        time_str = datetime.fromisoformat(attempt['time']).strftime('%H:%M:%S')
                        print(f"    └─ {time_str} → {attempt['path']}")
            print()
        
        # Injection attempts
        if threats["injection_attempts"]:
            print("💉 Injection Attempts:")
            for attempt in threats["injection_attempts"][-10:]:  # Show last 10
                time_str = datetime.fromisoformat(attempt['time']).strftime('%H:%M:%S')
                print(f"  ⚠️  {attempt['type']} from {attempt['ip']} at {time_str}")
            print()
        
        # Top suspicious IPs
        if threats["suspicious_ips"]:
            print("🕵️  Most Suspicious IP Addresses:")
            for ip, count in threats["suspicious_ips"].most_common(10):
                print(f"  🔴 {ip}: {count} suspicious events")
            print()
        
        # Time-based anomalies
        if threats["time_based_anomalies"]:
            print("🌙 After-Hours Activity:")
            recent_anomalies = threats["time_based_anomalies"][-10:]
            for anomaly in recent_anomalies:
                time_str = datetime.fromisoformat(anomaly['time']).strftime('%H:%M:%S')
                print(f"  🕐 {anomaly['ip']} at {time_str} ({anomaly['hour']}:00) - {anomaly['event_type']}")
            print()
        
        # Summary
        total_threats = (len(brute_force_by_ip) + 
                        len(threats["injection_attempts"]) + 
                        len(threats["suspicious_ips"]) + 
                        len(threats["time_based_anomalies"]))
        
        if total_threats == 0:
            print("✅ No active threats detected in the last 24 hours")
        else:
            print(f"⚠️  {total_threats} potential threats require attention")
    
    # Execute analysis
    threats = analyze_threats()
    print_threat_analysis(threats)

except Exception as e:
    print(f"❌ Threat analysis failed: {e}")
    sys.exit(1)
EOF
}

# Generate security metrics
generate_metrics() {
    log "${GREEN}${BOLD}📈 Security Metrics${NC}"
    log "${GREEN}══════════════════${NC}"
    
    # System security health check
    log "🏥 System Security Health:"
    
    # Check log file sizes
    if [ -d "$LOG_DIR" ]; then
        total_logs=$(find "$LOG_DIR" -name "*.log" -o -name "*.jsonl" | wc -l)
        log "  📁 Security log files: $total_logs"
        
        latest_log=$(find "$LOG_DIR" -name "security_events_*.jsonl" -exec ls -t {} + | head -1)
        if [ -n "$latest_log" ]; then
            events_today=$(wc -l < "$latest_log" 2>/dev/null || echo "0")
            log "  📝 Events logged today: $events_today"
        fi
    fi
    
    # Check disk space for logs
    log_disk_usage=$(du -sh "$LOG_DIR" 2>/dev/null | cut -f1 || echo "0B")
    log "  💾 Log storage usage: $log_disk_usage"
    
    # Check if security services are running
    log ""
    log "🔧 Security Services Status:"
    
    # Check Redis connection
    if command -v redis-cli &> /dev/null; then
        if redis-cli ping >/dev/null 2>&1; then
            log "  ✅ Redis (session storage): Connected"
        else
            log "  ❌ Redis (session storage): Disconnected"
        fi
    else
        log "  ⚠️  Redis: Not installed"
    fi
    
    # Check log rotation
    log ""
    log "🔄 Log Management:"
    old_logs=$(find "$LOG_DIR" -name "*.log" -mtime +7 | wc -l)
    log "  📅 Log files older than 7 days: $old_logs"
    
    if [ "$old_logs" -gt 10 ]; then
        log "  ⚠️  Consider implementing log rotation"
    fi
}

# Real-time monitoring mode
real_time_monitor() {
    log "${CYAN}${BOLD}📡 Real-time Security Monitor${NC}"
    log "${CYAN}════════════════════════════${NC}"
    log "Press Ctrl+C to stop monitoring"
    log ""
    
    # Monitor security events in real-time
    if [ -d "$LOG_DIR" ]; then
        # Find today's log file
        today_log="$LOG_DIR/security_events_$(date +%Y%m%d).jsonl"
        
        if [ -f "$today_log" ]; then
            log "👀 Monitoring: $today_log"
            log ""
            
            # Use tail to follow the log file
            tail -f "$today_log" | while read -r line; do
                if [ -n "$line" ]; then
                    # Parse and display security events
                    echo "$line" | python3 -c "
import json
import sys
from datetime import datetime

try:
    event = json.loads(input())
    timestamp = datetime.fromisoformat(event['timestamp']).strftime('%H:%M:%S')
    event_type = event.get('event_type', 'unknown')
    severity = event.get('severity', 'info')
    ip = event.get('ip_address', 'unknown')
    risk_score = event.get('risk_score', 0)
    
    # Color coding
    colors = {
        'critical': '\033[0;31m',  # Red
        'high': '\033[0;33m',      # Yellow
        'medium': '\033[0;36m',    # Cyan
        'low': '\033[0;32m',       # Green
        'info': '\033[0;37m'       # White
    }
    
    icons = {
        'auth_success': '✅',
        'auth_failure': '❌',
        'admin_action': '🔧',
        'suspicious_request': '⚠️',
        'sql_injection_attempt': '💉',
        'xss_attempt': '🕷️',
        'brute_force_attempt': '🔨'
    }
    
    color = colors.get(severity, '\033[0;37m')
    icon = icons.get(event_type, '📝')
    reset = '\033[0m'
    
    print(f'{color}[{timestamp}] {icon} {event_type} | {ip} | Risk: {risk_score}/10 | {severity.upper()}{reset}')
    
except (json.JSONDecodeError, KeyError):
    pass
"
                fi
            done
        else
            log "⚠️  No security events logged today yet"
            log "Creating log file: $today_log"
            touch "$today_log"
            tail -f "$today_log"
        fi
    else
        log "❌ Security log directory not found: $LOG_DIR"
        exit 1
    fi
}

# Generate alert summary
generate_alerts() {
    log "${RED}${BOLD}🚨 Security Alerts${NC}"
    log "${RED}══════════════════${NC}"
    
    cd "$PROJECT_ROOT/backend"
    
    python << EOF
import sys
import os
import json
from datetime import datetime, timedelta
from collections import defaultdict

sys.path.insert(0, os.path.join(os.getcwd()))

def check_alerts():
    """Check for active security alerts"""
    log_dir = "../logs/security"
    alerts = []
    
    # Check last 4 hours for critical events
    start_time = datetime.now() - timedelta(hours=4)
    
    current = start_time.date()
    end_date = datetime.now().date()
    
    while current <= end_date:
        log_file = f"{log_dir}/security_events_{current.strftime('%Y%m%d')}.jsonl"
        
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        event = json.loads(line)
                        event_time = datetime.fromisoformat(event['timestamp'])
                        
                        if event_time < start_time:
                            continue
                        
                        severity = event.get('severity', 'info')
                        risk_score = event.get('risk_score', 0)
                        event_type = event.get('event_type', '')
                        
                        # Critical alerts
                        if severity == 'critical' or risk_score >= 8:
                            alerts.append({
                                'time': event_time.strftime('%H:%M:%S'),
                                'type': event_type,
                                'severity': severity,
                                'risk_score': risk_score,
                                'ip': event.get('ip_address', 'unknown'),
                                'details': event.get('details', {})
                            })
                        
                    except (json.JSONDecodeError, ValueError, KeyError):
                        continue
        
        current += timedelta(days=1)
    
    return alerts

# Check for alerts
alerts = check_alerts()

if alerts:
    print(f"🚨 {len(alerts)} CRITICAL SECURITY ALERTS in the last 4 hours:")
    print()
    
    for alert in alerts[-10:]:  # Show last 10 alerts
        print(f"  🔴 [{alert['time']}] {alert['type']}")
        print(f"      IP: {alert['ip']} | Risk: {alert['risk_score']}/10 | Severity: {alert['severity'].upper()}")
        if alert['details']:
            details_str = str(alert['details'])[:100]
            print(f"      Details: {details_str}...")
        print()
    
    if len(alerts) > 10:
        print(f"  ... and {len(alerts) - 10} more alerts")
else:
    print("✅ No critical security alerts in the last 4 hours")
EOF
}

# Main execution
case $COMMAND in
    "dashboard")
        generate_dashboard "$TIME_RANGE" "$OUTPUT_FORMAT"
        ;;
        
    "analyze")
        analyze_threats
        ;;
        
    "metrics")
        generate_metrics
        ;;
        
    "monitor")
        real_time_monitor
        ;;
        
    "alerts")
        generate_alerts
        ;;
        
    "report")
        log "${BLUE}${BOLD}📄 Generating Comprehensive Security Report${NC}"
        generate_dashboard "$TIME_RANGE" "$OUTPUT_FORMAT"
        echo ""
        analyze_threats
        echo ""
        generate_metrics
        echo ""
        generate_alerts
        ;;
        
    "help"|"-h"|"--help")
        cat << EOF

Security Dashboard and Monitoring Script

Usage: $0 [command] [time-range] [output-format]

Commands:
  dashboard          Show security dashboard (default)
  analyze            Analyze security threats and patterns
  metrics            Show security system metrics
  monitor            Real-time security event monitoring
  alerts             Show active security alerts
  report             Generate comprehensive security report
  help               Show this help message

Time Ranges:
  --last-24h         Last 24 hours (default)
  --last-week        Last 7 days
  --last-month       Last 30 days

Output Formats:
  --output-console   Console output (default)
  --output-html      Generate HTML report

Examples:
  $0 dashboard --last-24h --output-console
  $0 analyze --last-week
  $0 monitor
  $0 report --last-24h --output-html
  $0 alerts

Real-time Monitoring:
  $0 monitor         Start real-time event monitoring

EOF
        ;;
        
    *)
        log "${RED}❌ Unknown command: $COMMAND${NC}"
        log "Use '$0 help' for usage information"
        exit 1
        ;;
esac

exit 0