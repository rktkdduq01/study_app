#!/bin/bash

# API Performance Monitoring Script
# Usage: ./scripts/monitor-performance.sh [command] [options]
# Example: ./scripts/monitor-performance.sh dashboard --real-time

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
BACKEND_DIR="$PROJECT_ROOT/backend"
LOG_DIR="$PROJECT_ROOT/logs/performance"
REPORTS_DIR="$PROJECT_ROOT/reports/performance"

# Command and options
COMMAND=${1:-dashboard}
REAL_TIME=${2:-false}
DURATION=${3:-60}

# Logging
mkdir -p "$LOG_DIR" "$REPORTS_DIR"
LOG_FILE="$LOG_DIR/performance-monitor-$(date +%Y%m%d_%H%M%S).log"

log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

log "${BLUE}${BOLD}🚀 API Performance Monitor${NC}"
log "${BLUE}Command: $COMMAND${NC}"
log "${BLUE}Log File: $LOG_FILE${NC}"
log ""

# Load environment
load_environment() {
    if [ -f "$PROJECT_ROOT/scripts/load-env.sh" ]; then
        source "$PROJECT_ROOT/scripts/load-env.sh" "${ENVIRONMENT:-development}"
    fi
}

# Check if backend is running
check_backend_status() {
    log "${YELLOW}🔍 Checking Backend Status${NC}"
    
    local backend_url="${BACKEND_URL:-http://localhost:8000}"
    local health_endpoint="$backend_url/health"
    
    if curl -s "$health_endpoint" > /dev/null 2>&1; then
        log "${GREEN}✅ Backend is running at $backend_url${NC}"
        return 0
    else
        log "${RED}❌ Backend is not accessible at $backend_url${NC}"
        return 1
    fi
}

# Real-time performance dashboard
real_time_dashboard() {
    log "${CYAN}${BOLD}📊 Real-time Performance Dashboard${NC}"
    log "${CYAN}════════════════════════════════════${NC}"
    log "Press Ctrl+C to stop monitoring"
    log ""
    
    local backend_url="${BACKEND_URL:-http://localhost:8000}"
    local stats_endpoint="$backend_url/api/v1/admin/performance/stats"
    
    while true; do
        clear
        echo -e "${CYAN}${BOLD}📊 API Performance Dashboard - $(date)${NC}"
        echo -e "${CYAN}════════════════════════════════════════════════${NC}"
        echo ""
        
        # Get performance stats
        local stats_response
        if stats_response=$(curl -s "$stats_endpoint" 2>/dev/null); then
            echo "$stats_response" | python3 -c "
import json
import sys
from datetime import datetime

try:
    data = json.loads(input())
    
    print('🔥 System Performance:')
    print(f'  Active Requests: {data.get(\"queue_performance\", {}).get(\"active_requests\", 0)}')
    print(f'  Queued Requests: {data.get(\"queue_performance\", {}).get(\"total_queued\", 0)}')
    print(f'  System Load: {data.get(\"system_load\", 0):.2%}')
    print()
    
    if 'recent_requests' in data:
        print('📈 Recent Activity:')
        print(f'  Requests (5min): {data.get(\"recent_requests\", 0)}')
        print(f'  Avg Response Time: {data.get(\"avg_processing_time_ms\", 0):.2f}ms')
        print(f'  Avg Queue Time: {data.get(\"avg_queue_time_ms\", 0):.2f}ms')
        print()
    
    if 'status_code_distribution' in data:
        print('📊 Status Codes:')
        for status, count in data.get('status_code_distribution', {}).items():
            emoji = '✅' if status.startswith('2') else '⚠️' if status.startswith('4') else '❌'
            print(f'  {emoji} {status}: {count}')
        print()
    
    if 'deduplication_active' in data:
        print('⚡ Optimizations:')
        print(f'  Request Deduplication: {data.get(\"deduplication_active\", 0)} active')
        print(f'  Rate Limited Users: {data.get(\"rate_limiter_active_users\", 0)}')
        print()
        
except (json.JSONDecodeError, KeyError) as e:
    print(f'❌ Error parsing stats: {e}')
except Exception as e:
    print(f'❌ Unexpected error: {e}')
"
        else
            echo "❌ Failed to fetch performance stats"
        fi
        
        echo ""
        echo -e "${YELLOW}Refreshing in 5 seconds... (Ctrl+C to stop)${NC}"
        sleep 5
    done
}

# Generate performance report
generate_performance_report() {
    log "${YELLOW}📋 Generating Performance Report${NC}"
    
    cd "$BACKEND_DIR"
    
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    elif [ -d "venv_backend" ]; then
        source venv_backend/bin/activate
    fi
    
    # Generate comprehensive report
    python << EOF
import sys
import os
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, os.getcwd())

try:
    from app.core.redis_client import redis_client
    from app.core.api_optimizer import api_optimizer
    from app.db.query_optimizer import db_optimizer
    from app.core.advanced_cache import multi_layer_cache
    
    async def generate_report():
        print("🔍 Analyzing API Performance...")
        
        # Initialize Redis connection
        if not redis_client._initialized:
            await redis_client.initialize()
        
        # Collect performance data
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "period": "last_24_hours",
            "summary": {},
            "api_performance": {},
            "database_performance": {},
            "cache_performance": {},
            "optimization_recommendations": []
        }
        
        # API Performance Stats
        try:
            api_stats = api_optimizer.get_performance_stats()
            report["api_performance"] = api_stats
            print(f"✅ API Stats: {api_stats.get('total_requests', 0)} requests analyzed")
        except Exception as e:
            print(f"⚠️  API stats collection failed: {e}")
            report["api_performance"] = {"error": str(e)}
        
        # Database Performance Stats
        try:
            db_stats = db_optimizer.get_performance_report()
            report["database_performance"] = db_stats
            print(f"✅ Database Stats: {db_stats.get('total_queries', 0)} queries analyzed")
        except Exception as e:
            print(f"⚠️  Database stats collection failed: {e}")
            report["database_performance"] = {"error": str(e)}
        
        # Cache Performance Stats
        try:
            cache_stats = multi_layer_cache.get_cache_stats()
            report["cache_performance"] = cache_stats
            print(f"✅ Cache Stats: L1 hit rate {cache_stats.get('l1_cache', {}).get('hit_rate', 0)}%")
        except Exception as e:
            print(f"⚠️  Cache stats collection failed: {e}")
            report["cache_performance"] = {"error": str(e)}
        
        # Generate Summary
        try:
            total_requests = api_stats.get("total_requests", 0)
            avg_response_time = api_stats.get("avg_response_time_ms", 0)
            cache_hit_rate = api_stats.get("cache_hit_rate", 0)
            error_rate = api_stats.get("error_rate", 0)
            
            report["summary"] = {
                "total_api_requests": total_requests,
                "average_response_time_ms": avg_response_time,
                "cache_hit_rate_percent": cache_hit_rate,
                "error_rate_percent": error_rate,
                "performance_grade": "A" if avg_response_time < 100 and error_rate < 1 else 
                                   "B" if avg_response_time < 500 and error_rate < 5 else "C"
            }
        except Exception as e:
            print(f"⚠️  Summary generation failed: {e}")
        
        # Generate Optimization Recommendations
        recommendations = []
        
        if avg_response_time > 500:
            recommendations.append({
                "type": "performance",
                "priority": "high",
                "title": "High API Response Time",
                "description": f"Average response time is {avg_response_time:.2f}ms, consider optimizing slow endpoints",
                "action": "Review slow endpoints and implement caching"
            })
        
        if cache_hit_rate < 50:
            recommendations.append({
                "type": "caching",
                "priority": "medium", 
                "title": "Low Cache Hit Rate",
                "description": f"Cache hit rate is {cache_hit_rate:.1f}%, increase caching coverage",
                "action": "Add caching to frequently accessed endpoints"
            })
        
        if error_rate > 5:
            recommendations.append({
                "type": "reliability",
                "priority": "high",
                "title": "High Error Rate",
                "description": f"Error rate is {error_rate:.1f}%, investigate failing endpoints",
                "action": "Review error logs and fix failing endpoints"
            })
        
        # Database optimization recommendations
        try:
            slow_queries = db_stats.get("slow_queries_count", 0)
            if slow_queries > 10:
                recommendations.append({
                    "type": "database",
                    "priority": "high", 
                    "title": "Slow Database Queries",
                    "description": f"{slow_queries} slow queries detected",
                    "action": "Optimize slow queries and add database indexes"
                })
        except:
            pass
        
        report["optimization_recommendations"] = recommendations
        
        # Save report to file
        report_file = f"../reports/performance/performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        Path(report_file).parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Report saved to: {report_file}")
        
        # Generate HTML report
        await generate_html_report(report, report_file.replace('.json', '.html'))
        
        return report
    
    async def generate_html_report(report_data, html_file):
        """Generate HTML performance report"""
        html_content = f'''
<!DOCTYPE html>
<html>
<head>
    <title>API Performance Report - {report_data["timestamp"][:10]}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .stat-card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .stat-number {{ font-size: 2.5em; font-weight: bold; color: #333; }}
        .stat-label {{ color: #666; font-size: 0.9em; }}
        .grade-a {{ color: #27ae60; }}
        .grade-b {{ color: #f39c12; }}
        .grade-c {{ color: #e74c3c; }}
        .chart-container {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .recommendation {{ background: white; border-left: 4px solid #3498db; padding: 15px; margin: 10px 0; border-radius: 0 5px 5px 0; }}
        .recommendation.high {{ border-left-color: #e74c3c; }}
        .recommendation.medium {{ border-left-color: #f39c12; }}
        .recommendation.low {{ border-left-color: #27ae60; }}
        .timestamp {{ color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 API Performance Report</h1>
            <p>Comprehensive performance analysis and optimization recommendations</p>
            <p class="timestamp">Generated: {report_data["timestamp"]}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{report_data.get("summary", {}).get("total_api_requests", 0)}</div>
                <div class="stat-label">Total API Requests</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{report_data.get("summary", {}).get("average_response_time_ms", 0):.1f}ms</div>
                <div class="stat-label">Average Response Time</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{report_data.get("summary", {}).get("cache_hit_rate_percent", 0):.1f}%</div>
                <div class="stat-label">Cache Hit Rate</div>
            </div>
            <div class="stat-card">
                <div class="stat-number grade-{report_data.get("summary", {}).get("performance_grade", "c").lower()}">{report_data.get("summary", {}).get("performance_grade", "N/A")}</div>
                <div class="stat-label">Performance Grade</div>
            </div>
        </div>
        
        <div class="chart-container">
            <h3>📊 Optimization Recommendations</h3>
'''
        
        recommendations = report_data.get("optimization_recommendations", [])
        if recommendations:
            for rec in recommendations:
                html_content += f'''
            <div class="recommendation {rec.get("priority", "low")}">
                <h4>{rec.get("title", "")}</h4>
                <p>{rec.get("description", "")}</p>
                <strong>Action:</strong> {rec.get("action", "")}
            </div>
'''
        else:
            html_content += '<p>✅ No optimization recommendations at this time.</p>'
        
        html_content += '''
        </div>
    </div>
</body>
</html>'''
        
        with open(html_file, 'w') as f:
            f.write(html_content)
        
        print(f"📄 HTML report saved to: {html_file}")
    
    # Run the report generation
    try:
        report = asyncio.run(generate_report())
        print("✅ Performance report generated successfully")
        return True
    except Exception as e:
        print(f"❌ Report generation failed: {e}")
        return False

except ImportError as e:
    print(f"❌ Failed to import required modules: {e}")
    sys.exit(1)
EOF

    if [ $? -eq 0 ]; then
        log "${GREEN}✅ Performance report generated${NC}"
    else
        log "${RED}❌ Performance report generation failed${NC}"
        return 1
    fi
    
    cd "$PROJECT_ROOT"
}

# Load testing simulation
run_load_test() {
    log "${YELLOW}🔥 Running Load Test${NC}"
    
    local backend_url="${BACKEND_URL:-http://localhost:8000}"
    local concurrent_users=${CONCURRENT_USERS:-10}
    local test_duration=${DURATION:-60}
    
    if ! command -v ab &> /dev/null; then
        log "${RED}❌ Apache Bench (ab) not found. Install apache2-utils${NC}"
        return 1
    fi
    
    log "Target: $backend_url"
    log "Concurrent Users: $concurrent_users"
    log "Duration: ${test_duration}s"
    log ""
    
    # Test different endpoints
    declare -a endpoints=(
        "/health"
        "/api/v1/content"
        "/api/v1/users/profile"
    )
    
    for endpoint in "${endpoints[@]}"; do
        log "${CYAN}Testing endpoint: $endpoint${NC}"
        
        local full_url="$backend_url$endpoint"
        local output_file="$REPORTS_DIR/load_test_$(echo $endpoint | tr '/' '_')_$(date +%Y%m%d_%H%M%S).txt"
        
        # Run Apache Bench test
        ab -n 1000 -c "$concurrent_users" -t "$test_duration" -g "$output_file.gnuplot" "$full_url" > "$output_file" 2>&1
        
        if [ $? -eq 0 ]; then
            log "${GREEN}✅ Test completed for $endpoint${NC}"
            
            # Extract key metrics
            echo "📊 Results for $endpoint:"
            grep "Requests per second" "$output_file" || echo "  No RPS data"
            grep "Time per request" "$output_file" | head -1 || echo "  No latency data"
            grep "Transfer rate" "$output_file" || echo "  No transfer rate data"
            echo ""
        else
            log "${RED}❌ Test failed for $endpoint${NC}"
        fi
    done
    
    log "${GREEN}✅ Load testing completed${NC}"
    log "Reports saved to: $REPORTS_DIR"
}

# Monitor API endpoints
monitor_endpoints() {
    log "${YELLOW}🔍 Monitoring API Endpoints${NC}"
    
    local backend_url="${BACKEND_URL:-http://localhost:8000}"
    local check_interval=30
    
    # Define critical endpoints to monitor
    declare -a critical_endpoints=(
        "/health:Health Check"
        "/api/v1/auth/login:Authentication"
        "/api/v1/content:Content API"
        "/api/v1/users/profile:User Profile"
    )
    
    log "Monitoring ${#critical_endpoints[@]} endpoints every ${check_interval}s"
    log ""
    
    while true; do
        local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        echo "[$timestamp] Endpoint Health Check:"
        
        for endpoint_info in "${critical_endpoints[@]}"; do
            IFS=':' read -r endpoint description <<< "$endpoint_info"
            local full_url="$backend_url$endpoint"
            
            # Measure response time
            local start_time=$(date +%s.%N)
            local http_code
            http_code=$(curl -s -o /dev/null -w "%{http_code}" "$full_url" --max-time 10)
            local end_time=$(date +%s.%N)
            local response_time=$(echo "$end_time - $start_time" | bc)
            local response_time_ms=$(echo "$response_time * 1000" | bc | cut -d. -f1)
            
            # Status indicator
            local status_icon="❌"
            local status_color="$RED"
            
            if [[ "$http_code" =~ ^2[0-9][0-9]$ ]]; then
                if [ "$response_time_ms" -lt 500 ]; then
                    status_icon="✅"
                    status_color="$GREEN"
                else
                    status_icon="⚠️"
                    status_color="$YELLOW"
                fi
            elif [[ "$http_code" =~ ^[45][0-9][0-9]$ ]]; then
                status_icon="❌"
                status_color="$RED"
            fi
            
            echo -e "  $status_icon ${status_color}$description${NC}: $http_code (${response_time_ms}ms)"
        done
        
        echo ""
        sleep "$check_interval"
    done
}

# Performance optimization suggestions
suggest_optimizations() {
    log "${YELLOW}💡 Performance Optimization Suggestions${NC}"
    
    cd "$BACKEND_DIR"
    
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    elif [ -d "venv_backend" ]; then
        source venv_backend/bin/activate
    fi
    
    python << EOF
import sys
import os
import asyncio
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.getcwd())

try:
    from app.core.api_optimizer import api_optimizer
    from app.db.query_optimizer import db_optimizer
    from app.core.advanced_cache import multi_layer_cache
    
    async def analyze_and_suggest():
        print("🔍 Analyzing System Performance...")
        print()
        
        # API Performance Analysis
        try:
            api_stats = api_optimizer.get_performance_stats()
            
            print("📊 API Performance Analysis:")
            print(f"  Total Requests: {api_stats.get('total_requests', 0)}")
            print(f"  Average Response Time: {api_stats.get('avg_response_time_ms', 0):.2f}ms")
            print(f"  Error Rate: {api_stats.get('error_rate', 0):.2f}%")
            print(f"  Cache Hit Rate: {api_stats.get('cache_hit_rate', 0):.2f}%")
            print()
            
            # Suggestions based on API stats
            if api_stats.get('avg_response_time_ms', 0) > 500:
                print("⚠️  HIGH RESPONSE TIME DETECTED")
                print("   Suggestions:")
                print("   - Enable response compression")
                print("   - Implement request caching")
                print("   - Optimize database queries")
                print("   - Consider adding more server instances")
                print()
            
            if api_stats.get('cache_hit_rate', 0) < 50:
                print("⚠️  LOW CACHE HIT RATE DETECTED")
                print("   Suggestions:")
                print("   - Increase cache TTL for stable data")
                print("   - Add caching to frequently accessed endpoints")
                print("   - Implement cache warming strategies")
                print()
            
            if api_stats.get('error_rate', 0) > 5:
                print("⚠️  HIGH ERROR RATE DETECTED")
                print("   Suggestions:")
                print("   - Review error logs for patterns")
                print("   - Implement better error handling")
                print("   - Add health checks and circuit breakers")
                print()
                
        except Exception as e:
            print(f"⚠️  API analysis failed: {e}")
        
        # Database Performance Analysis
        try:
            db_report = db_optimizer.get_performance_report()
            
            print("🗄️  Database Performance Analysis:")
            print(f"  Total Queries: {db_report.get('performance_stats', {}).get('total_queries', 0)}")
            print(f"  Slow Queries: {db_report.get('slow_queries_count', 0)}")
            print(f"  Average Query Time: {db_report.get('performance_stats', {}).get('avg_execution_time', 0):.3f}s")
            print()
            
            slow_queries = db_report.get('slow_queries_count', 0)
            if slow_queries > 10:
                print("⚠️  SLOW QUERIES DETECTED")
                print("   Suggestions:")
                print("   - Add database indexes for frequent queries")
                print("   - Optimize JOIN operations")
                print("   - Consider query result caching")
                print("   - Review and optimize WHERE clauses")
                print()
                
        except Exception as e:
            print(f"⚠️  Database analysis failed: {e}")
        
        # Cache Performance Analysis
        try:
            cache_stats = multi_layer_cache.get_cache_stats()
            
            print("💾 Cache Performance Analysis:")
            l1_stats = cache_stats.get('l1_cache', {})
            l2_stats = cache_stats.get('l2_cache', {})
            
            print(f"  L1 Cache Hit Rate: {l1_stats.get('hit_rate', 0):.2f}%")
            print(f"  L2 Cache Hit Rate: {l2_stats.get('hit_rate', 0):.2f}%")
            print(f"  L1 Cache Entries: {l1_stats.get('entries', 0)}")
            print()
            
            if l1_stats.get('hit_rate', 0) < 70:
                print("⚠️  LOW L1 CACHE EFFICIENCY")
                print("   Suggestions:")
                print("   - Increase L1 cache size")
                print("   - Optimize cache key strategies")
                print("   - Implement smarter cache eviction")
                print()
                
        except Exception as e:
            print(f"⚠️  Cache analysis failed: {e}")
        
        # General optimization suggestions
        print("🚀 General Performance Optimization Tips:")
        print("   1. Enable Brotli/Gzip compression for all text responses")
        print("   2. Implement CDN for static assets")
        print("   3. Use connection pooling for database connections")
        print("   4. Add monitoring and alerting for key metrics")
        print("   5. Implement graceful degradation for external services")
        print("   6. Use async/await for I/O operations")
        print("   7. Consider implementing read replicas for heavy read workloads")
        print("   8. Set up proper logging and distributed tracing")
        print()
        
        return True
    
    # Run the analysis
    try:
        success = asyncio.run(analyze_and_suggest())
        if success:
            print("✅ Performance analysis completed")
        return success
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False

except ImportError as e:
    print(f"❌ Failed to import required modules: {e}")
    sys.exit(1)
EOF
}

# Main execution
main() {
    load_environment
    
    case $COMMAND in
        "dashboard")
            check_backend_status || exit 1
            if [ "$REAL_TIME" = "--real-time" ] || [ "$REAL_TIME" = "-r" ]; then
                real_time_dashboard
            else
                generate_performance_report
            fi
            ;;
            
        "report")
            generate_performance_report
            ;;
            
        "load-test")
            check_backend_status || exit 1
            run_load_test
            ;;
            
        "monitor")
            check_backend_status || exit 1
            monitor_endpoints
            ;;
            
        "analyze")
            suggest_optimizations
            ;;
            
        "help"|"-h"|"--help")
            cat << EOF

API Performance Monitoring Script

Usage: $0 [command] [options]

Commands:
  dashboard        Show performance dashboard (default)
  report          Generate detailed performance report
  load-test       Run load testing simulation
  monitor         Monitor API endpoints continuously
  analyze         Analyze performance and suggest optimizations
  help            Show this help message

Options:
  --real-time     Show real-time dashboard (for dashboard command)
  -r              Short form of --real-time
  
Examples:
  $0 dashboard --real-time
  $0 report
  $0 load-test
  $0 monitor
  $0 analyze

Environment Variables:
  BACKEND_URL           Backend URL (default: http://localhost:8000)
  CONCURRENT_USERS      Concurrent users for load testing (default: 10)
  DURATION             Test duration in seconds (default: 60)

Requirements:
  - Backend server running
  - Apache Bench (ab) for load testing
  - Python with required modules

EOF
            ;;
            
        *)
            log "${RED}❌ Unknown command: $COMMAND${NC}"
            log "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Execute main function
if main; then
    if [ "$COMMAND" != "dashboard" ] && [ "$COMMAND" != "monitor" ]; then
        log ""
        log "${GREEN}✅ Performance monitoring completed${NC}"
        log "${BLUE}📄 Log file: $LOG_FILE${NC}"
    fi
    exit 0
else
    log ""
    log "${RED}❌ Performance monitoring failed${NC}"
    log "${BLUE}📄 Check log file: $LOG_FILE${NC}"
    exit 1
fi