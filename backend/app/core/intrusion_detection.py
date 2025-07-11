"""
Intrusion Detection System (IDS)
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import asyncio
import re
import json
from ipaddress import ip_address, ip_network

from app.core.logger import get_logger
from app.core.redis_client import redis_client
from app.core.config import settings

logger = get_logger(__name__)


class IntrusionDetectionSystem:
    """Real-time intrusion detection and prevention"""
    
    def __init__(self):
        self.attack_patterns = self._load_attack_patterns()
        self.behavior_baselines = defaultdict(lambda: {"requests": deque(maxlen=1000)})
        self.alert_thresholds = {
            "port_scan": 10,
            "brute_force": 5,
            "dos_attack": 100,
            "sql_injection": 1,
            "xss_attempt": 1,
            "path_traversal": 1
        }
        self.detection_rules = self._initialize_rules()
        
    def _load_attack_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Load attack signature patterns"""
        return {
            "sql_injection": [
                re.compile(r"(union.*select|select.*from|insert.*into|delete.*from)", re.I),
                re.compile(r"(drop\s+table|alter\s+table|create\s+table)", re.I),
                re.compile(r"(exec\s*\(|execute\s*\(|xp_cmdshell)", re.I),
                re.compile(r"(waitfor\s+delay|benchmark\s*\(|sleep\s*\()", re.I)
            ],
            "xss": [
                re.compile(r"<script[^>]*>.*?</script>", re.I | re.S),
                re.compile(r"(javascript|vbscript|onload|onerror|onclick)\s*:", re.I),
                re.compile(r"<iframe[^>]*>|<object[^>]*>|<embed[^>]*>", re.I)
            ],
            "command_injection": [
                re.compile(r"[;&|]\s*(ls|cat|rm|wget|curl|nc|bash|sh)\s", re.I),
                re.compile(r"\$\(.*\)|\`.*\`", re.I),
                re.compile(r"(system|eval|exec|passthru|shell_exec)\s*\(", re.I)
            ],
            "path_traversal": [
                re.compile(r"\.\.[\\/]|\.\.%2[fF]|\.\.%5[cC]"),
                re.compile(r"(etc/passwd|win\.ini|boot\.ini)", re.I)
            ],
            "ldap_injection": [
                re.compile(r"[*()\\|&=]"),
                re.compile(r"(\(|\))\s*(\||&)", re.I)
            ]
        }
    
    def _initialize_rules(self) -> List[Dict[str, Any]]:
        """Initialize detection rules"""
        return [
            {
                "name": "rapid_requests",
                "description": "Detect rapid requests from single IP",
                "check": self._check_rapid_requests,
                "threshold": 100,
                "window": 60  # seconds
            },
            {
                "name": "failed_auth_attempts",
                "description": "Multiple failed authentication attempts",
                "check": self._check_failed_auth,
                "threshold": 5,
                "window": 300  # 5 minutes
            },
            {
                "name": "port_scanning",
                "description": "Detect port scanning behavior",
                "check": self._check_port_scan,
                "threshold": 10,
                "window": 60
            },
            {
                "name": "unusual_user_agent",
                "description": "Detect suspicious user agents",
                "check": self._check_user_agent,
                "threshold": 1,
                "window": 0
            },
            {
                "name": "geographic_anomaly",
                "description": "Detect geographic anomalies",
                "check": self._check_geographic_anomaly,
                "threshold": 1,
                "window": 3600
            }
        ]
    
    async def analyze_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze request for intrusion attempts"""
        analysis = {
            "timestamp": datetime.utcnow(),
            "ip": request_data.get("ip"),
            "threats_detected": [],
            "risk_score": 0,
            "action": "allow"
        }
        
        # Check attack patterns
        pattern_threats = self._check_attack_patterns(request_data)
        analysis["threats_detected"].extend(pattern_threats)
        
        # Check behavioral anomalies
        behavioral_threats = await self._check_behavioral_anomalies(request_data)
        analysis["threats_detected"].extend(behavioral_threats)
        
        # Calculate risk score
        analysis["risk_score"] = self._calculate_risk_score(analysis["threats_detected"])
        
        # Determine action
        if analysis["risk_score"] >= 80:
            analysis["action"] = "block"
            await self._block_attacker(request_data["ip"])
        elif analysis["risk_score"] >= 50:
            analysis["action"] = "challenge"  # e.g., CAPTCHA
        
        # Log high-risk attempts
        if analysis["risk_score"] >= 50:
            await self._log_intrusion_attempt(analysis)
        
        # Update behavioral baseline
        await self._update_baseline(request_data)
        
        return analysis
    
    def _check_attack_patterns(self, request_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check request against known attack patterns"""
        threats = []
        
        # Check URL and parameters
        url = request_data.get("url", "")
        params = request_data.get("params", "")
        body = request_data.get("body", "")
        headers = request_data.get("headers", {})
        
        # Combine all input for checking
        combined_input = f"{url} {params} {body} {' '.join(headers.values())}"
        
        for attack_type, patterns in self.attack_patterns.items():
            for pattern in patterns:
                if pattern.search(combined_input):
                    threats.append({
                        "type": attack_type,
                        "severity": "high",
                        "pattern": pattern.pattern,
                        "confidence": 0.9
                    })
                    break
        
        return threats
    
    async def _check_behavioral_anomalies(self, request_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for behavioral anomalies"""
        threats = []
        
        for rule in self.detection_rules:
            result = await rule["check"](request_data, rule)
            if result:
                threats.append(result)
        
        return threats
    
    async def _check_rapid_requests(self, request_data: Dict[str, Any], rule: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check for rapid request patterns"""
        ip = request_data["ip"]
        key = f"ids:requests:{ip}"
        
        # Increment counter
        count = await redis_client.incr(key)
        if count == 1:
            await redis_client.expire(key, rule["window"])
        
        if count > rule["threshold"]:
            return {
                "type": "dos_attack",
                "severity": "high",
                "description": f"Rapid requests detected: {count} in {rule['window']}s",
                "confidence": 0.8
            }
        
        return None
    
    async def _check_failed_auth(self, request_data: Dict[str, Any], rule: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check for brute force attacks"""
        if request_data.get("endpoint") not in ["/auth/login", "/api/v1/auth/login"]:
            return None
        
        if request_data.get("status_code") != 401:
            return None
        
        ip = request_data["ip"]
        key = f"ids:failed_auth:{ip}"
        
        count = await redis_client.incr(key)
        if count == 1:
            await redis_client.expire(key, rule["window"])
        
        if count > rule["threshold"]:
            return {
                "type": "brute_force",
                "severity": "high",
                "description": f"Multiple failed auth attempts: {count}",
                "confidence": 0.9
            }
        
        return None
    
    async def _check_port_scan(self, request_data: Dict[str, Any], rule: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detect port scanning behavior"""
        ip = request_data["ip"]
        endpoint = request_data.get("endpoint", "")
        
        # Track unique endpoints accessed
        key = f"ids:endpoints:{ip}"
        await redis_client.sadd(key, endpoint)
        await redis_client.expire(key, rule["window"])
        
        # Get count of unique endpoints
        count = await redis_client.scard(key)
        
        if count > rule["threshold"]:
            endpoints = await redis_client.smembers(key)
            
            # Check if endpoints look like port scanning
            if self._looks_like_port_scan(list(endpoints)):
                return {
                    "type": "port_scan",
                    "severity": "medium",
                    "description": f"Port scanning detected: {count} endpoints",
                    "confidence": 0.7
                }
        
        return None
    
    def _looks_like_port_scan(self, endpoints: List[str]) -> bool:
        """Check if endpoint pattern looks like port scanning"""
        # Common scanning patterns
        scan_patterns = [
            r"/admin", r"/phpmyadmin", r"/wp-admin",
            r"/.git", r"/.env", r"/config",
            r"/backup", r"/sql", r"/database"
        ]
        
        matches = 0
        for endpoint in endpoints:
            for pattern in scan_patterns:
                if re.search(pattern, endpoint, re.I):
                    matches += 1
                    break
        
        return matches >= 3
    
    async def _check_user_agent(self, request_data: Dict[str, Any], rule: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check for suspicious user agents"""
        user_agent = request_data.get("user_agent", "").lower()
        
        # Known malicious tools
        suspicious_agents = [
            "sqlmap", "nikto", "nmap", "masscan",
            "metasploit", "burpsuite", "owasp",
            "havij", "acunetix", "nessus"
        ]
        
        for agent in suspicious_agents:
            if agent in user_agent:
                return {
                    "type": "malicious_scanner",
                    "severity": "high",
                    "description": f"Malicious tool detected: {agent}",
                    "confidence": 0.95
                }
        
        # Check for missing or suspicious user agent
        if not user_agent or user_agent in ["", "-", "null"]:
            return {
                "type": "suspicious_agent",
                "severity": "low",
                "description": "Missing or invalid user agent",
                "confidence": 0.5
            }
        
        return None
    
    async def _check_geographic_anomaly(self, request_data: Dict[str, Any], rule: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detect geographic anomalies in user behavior"""
        ip = request_data["ip"]
        user_id = request_data.get("user_id")
        
        if not user_id:
            return None
        
        # Get user's location history
        key = f"ids:user_locations:{user_id}"
        
        # This is a simplified check - in production, use GeoIP database
        await redis_client.sadd(key, ip)
        await redis_client.expire(key, 86400)  # 24 hours
        
        locations = await redis_client.smembers(key)
        
        # If user has IPs from very different locations in short time
        if len(locations) > 3:
            return {
                "type": "geographic_anomaly",
                "severity": "medium",
                "description": f"User accessing from {len(locations)} different IPs",
                "confidence": 0.6
            }
        
        return None
    
    def _calculate_risk_score(self, threats: List[Dict[str, Any]]) -> int:
        """Calculate overall risk score"""
        if not threats:
            return 0
        
        severity_scores = {
            "low": 20,
            "medium": 50,
            "high": 80,
            "critical": 100
        }
        
        total_score = 0
        for threat in threats:
            severity = threat.get("severity", "low")
            confidence = threat.get("confidence", 0.5)
            score = severity_scores.get(severity, 20) * confidence
            total_score += score
        
        # Normalize to 0-100
        return min(100, int(total_score))
    
    async def _block_attacker(self, ip: str):
        """Block detected attacker"""
        # Add to blocked IPs
        await redis_client.sadd("security:blocked_ips", ip)
        
        # Set expiration for temporary block (24 hours)
        block_key = f"ids:blocked:{ip}"
        await redis_client.setex(block_key, 86400, "blocked")
        
        logger.warning(f"IDS blocked IP {ip} due to intrusion attempt")
    
    async def _log_intrusion_attempt(self, analysis: Dict[str, Any]):
        """Log intrusion attempt for analysis"""
        log_key = f"ids:intrusions:{datetime.utcnow().strftime('%Y%m%d')}"
        await redis_client.lpush(log_key, json.dumps(analysis, default=str))
        await redis_client.expire(log_key, 86400 * 30)  # Keep for 30 days
        
        # Send alert for high-risk intrusions
        if analysis["risk_score"] >= 80:
            await self._send_intrusion_alert(analysis)
    
    async def _send_intrusion_alert(self, analysis: Dict[str, Any]):
        """Send alert for high-risk intrusions"""
        alert = {
            "type": "intrusion_detected",
            "severity": "critical",
            "timestamp": datetime.utcnow().isoformat(),
            "details": analysis
        }
        
        # Send to monitoring system
        await redis_client.lpush("security:alerts", json.dumps(alert))
        
        logger.critical(f"High-risk intrusion detected: {analysis}")
    
    async def _update_baseline(self, request_data: Dict[str, Any]):
        """Update behavioral baseline for anomaly detection"""
        ip = request_data["ip"]
        
        # Update request patterns
        baseline = self.behavior_baselines[ip]
        baseline["requests"].append({
            "timestamp": datetime.utcnow(),
            "endpoint": request_data.get("endpoint"),
            "method": request_data.get("method"),
            "size": request_data.get("size", 0)
        })
    
    async def get_threat_intelligence(self) -> Dict[str, Any]:
        """Get current threat intelligence summary"""
        # Get recent intrusions
        today = datetime.utcnow().strftime('%Y%m%d')
        intrusions = await redis_client.lrange(f"ids:intrusions:{today}", 0, -1)
        
        # Parse and analyze
        threat_types = defaultdict(int)
        blocked_ips = await redis_client.scard("security:blocked_ips")
        
        for intrusion_str in intrusions:
            try:
                intrusion = json.loads(intrusion_str)
                for threat in intrusion.get("threats_detected", []):
                    threat_types[threat["type"]] += 1
            except:
                continue
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_intrusions_today": len(intrusions),
            "blocked_ips": blocked_ips,
            "threat_distribution": dict(threat_types),
            "top_threats": sorted(threat_types.items(), key=lambda x: x[1], reverse=True)[:5]
        }


# Global IDS instance
ids = IntrusionDetectionSystem()