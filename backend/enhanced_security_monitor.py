"""
Enhanced Security Monitoring System
Real-time threat detection and security monitoring
"""

import asyncio
import json
import time
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import psutil
import requests
from sqlalchemy.orm import Session
from sqlalchemy import text, func

from database import get_db, SecurityEvent, UserActivityLog, ApiRateLimits
from enhanced_security_config import security_config, THREAT_DETECTION_CONFIG
from backend.encryption_manager import encryption_manager

# Configure logging
monitor_logger = logging.getLogger("security_monitor")
monitor_logger.setLevel(logging.INFO)

class ThreatLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityAlert:
    """Security alert data structure"""
    alert_id: str
    threat_level: ThreatLevel
    alert_type: str
    description: str
    source_ip: str
    user_id: Optional[str]
    timestamp: datetime
    details: Dict[str, Any]
    resolved: bool = False
    resolution_time: Optional[datetime] = None

class EnhancedSecurityMonitor:
    """Enhanced security monitoring system"""
    
    def __init__(self):
        self.alerts: List[SecurityAlert] = []
        self.threat_patterns: Dict[str, List[str]] = {}
        self.system_metrics: Dict[str, Any] = {}
        self.last_scan_time = datetime.now(timezone.utc)
        self.monitoring_active = True
        
        # Initialize threat patterns
        self._initialize_threat_patterns()
    
    def _initialize_threat_patterns(self):
        """Initialize threat detection patterns"""
        self.threat_patterns = {
            "brute_force": [
                "multiple_failed_logins",
                "rapid_login_attempts",
                "account_lockout"
            ],
            "sql_injection": [
                "sql_pattern_detected",
                "database_error_exposure",
                "suspicious_query"
            ],
            "xss": [
                "script_tag_detected",
                "javascript_injection",
                "dom_manipulation"
            ],
            "ddos": [
                "high_request_rate",
                "resource_exhaustion",
                "service_unavailable"
            ],
            "data_exfiltration": [
                "bulk_data_access",
                "unauthorized_export",
                "sensitive_data_access"
            ],
            "privilege_escalation": [
                "admin_access_attempt",
                "role_modification",
                "permission_change"
            ]
        }
    
    async def start_monitoring(self):
        """Start the security monitoring system"""
        monitor_logger.info("Starting enhanced security monitoring system")
        
        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self.monitor_security_events()),
            asyncio.create_task(self.monitor_system_metrics()),
            asyncio.create_task(self.monitor_network_activity()),
            asyncio.create_task(self.monitor_database_activity()),
            asyncio.create_task(self.monitor_user_activity()),
            asyncio.create_task(self.analyze_threat_patterns()),
            asyncio.create_task(self.generate_security_reports())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            monitor_logger.error(f"Security monitoring error: {str(e)}")
    
    async def monitor_security_events(self):
        """Monitor security events in real-time"""
        while self.monitoring_active:
            try:
                # Get recent security events
                recent_events = await self.get_recent_security_events()
                
                # Analyze events for threats
                for event in recent_events:
                    threat_level = self.analyze_event_threat_level(event)
                    
                    if threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                        await self.create_security_alert(event, threat_level)
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                monitor_logger.error(f"Security event monitoring error: {str(e)}")
                await asyncio.sleep(60)
    
    async def monitor_system_metrics(self):
        """Monitor system performance and resource usage"""
        while self.monitoring_active:
            try:
                # Collect system metrics
                metrics = {
                    "cpu_percent": psutil.cpu_percent(interval=1),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_percent": psutil.disk_usage('/').percent,
                    "network_connections": len(psutil.net_connections()),
                    "load_average": psutil.getloadavg(),
                    "timestamp": datetime.now(timezone.utc)
                }
                
                self.system_metrics = metrics
                
                # Check for resource exhaustion
                if metrics["cpu_percent"] > 90:
                    await self.create_system_alert("high_cpu_usage", ThreatLevel.HIGH, metrics)
                
                if metrics["memory_percent"] > 85:
                    await self.create_system_alert("high_memory_usage", ThreatLevel.HIGH, metrics)
                
                if metrics["disk_percent"] > 80:
                    await self.create_system_alert("high_disk_usage", ThreatLevel.MEDIUM, metrics)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                monitor_logger.error(f"System metrics monitoring error: {str(e)}")
                await asyncio.sleep(120)
    
    async def monitor_network_activity(self):
        """Monitor network connections and traffic"""
        while self.monitoring_active:
            try:
                # Get network connections
                connections = psutil.net_connections()
                
                # Analyze connections for suspicious activity
                suspicious_connections = []
                
                for conn in connections:
                    if conn.status == 'ESTABLISHED':
                        # Check for suspicious ports
                        if conn.raddr and conn.raddr.port in [22, 23, 3389, 5900]:
                            suspicious_connections.append(conn)
                        
                        # Check for multiple connections to same IP
                        if conn.raddr:
                            same_ip_connections = [
                                c for c in connections 
                                if c.raddr and c.raddr.ip == conn.raddr.ip
                            ]
                            if len(same_ip_connections) > 10:
                                suspicious_connections.append(conn)
                
                if suspicious_connections:
                    await self.create_network_alert("suspicious_connections", ThreatLevel.MEDIUM, {
                        "connections": len(suspicious_connections),
                        "details": [str(c) for c in suspicious_connections[:5]]
                    })
                
                await asyncio.sleep(120)  # Check every 2 minutes
                
            except Exception as e:
                monitor_logger.error(f"Network monitoring error: {str(e)}")
                await asyncio.sleep(300)
    
    async def monitor_database_activity(self):
        """Monitor database activity for suspicious patterns"""
        while self.monitoring_active:
            try:
                # Get database session
                db = next(get_db())
                
                # Check for unusual query patterns
                recent_queries = db.execute(text("""
                    SELECT query, calls, total_time, mean_time
                    FROM pg_stat_statements
                    WHERE query_time > NOW() - INTERVAL '1 hour'
                    ORDER BY total_time DESC
                    LIMIT 10
                """)).fetchall()
                
                # Analyze query patterns
                for query in recent_queries:
                    if self.is_suspicious_query(query[0]):
                        await self.create_database_alert("suspicious_query", ThreatLevel.HIGH, {
                            "query": query[0],
                            "calls": query[1],
                            "total_time": query[2]
                        })
                
                # Check for failed connections
                failed_connections = db.execute(text("""
                    SELECT COUNT(*) as failed_count
                    FROM pg_stat_activity
                    WHERE state = 'idle in transaction (aborted)'
                """)).fetchone()
                
                if failed_connections[0] > 10:
                    await self.create_database_alert("high_failed_connections", ThreatLevel.MEDIUM, {
                        "failed_count": failed_connections[0]
                    })
                
                db.close()
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                monitor_logger.error(f"Database monitoring error: {str(e)}")
                await asyncio.sleep(600)
    
    async def monitor_user_activity(self):
        """Monitor user activity for suspicious behavior"""
        while self.monitoring_active:
            try:
                # Get database session
                db = next(get_db())
                
                # Check for unusual user activity
                recent_activity = db.query(UserActivityLog).filter(
                    UserActivityLog.timestamp > datetime.now(timezone.utc) - timedelta(hours=1)
                ).all()
                
                # Group by user and analyze patterns
                user_activity = {}
                for activity in recent_activity:
                    user_id = activity.user_id
                    if user_id not in user_activity:
                        user_activity[user_id] = []
                    user_activity[user_id].append(activity)
                
                # Check for suspicious patterns
                for user_id, activities in user_activity.items():
                    if len(activities) > 100:  # Too many activities
                        await self.create_user_alert("excessive_activity", ThreatLevel.HIGH, {
                            "user_id": user_id,
                            "activity_count": len(activities)
                        })
                    
                    # Check for rapid successive actions
                    timestamps = [a.timestamp for a in activities]
                    for i in range(len(timestamps) - 1):
                        time_diff = (timestamps[i+1] - timestamps[i]).total_seconds()
                        if time_diff < 1:  # Less than 1 second between actions
                            await self.create_user_alert("rapid_actions", ThreatLevel.MEDIUM, {
                                "user_id": user_id,
                                "time_diff": time_diff
                            })
                
                db.close()
                await asyncio.sleep(180)  # Check every 3 minutes
                
            except Exception as e:
                monitor_logger.error(f"User activity monitoring error: {str(e)}")
                await asyncio.sleep(600)
    
    async def analyze_threat_patterns(self):
        """Analyze threat patterns and correlations"""
        while self.monitoring_active:
            try:
                # Get recent security events
                recent_events = await self.get_recent_security_events()
                
                # Analyze patterns
                patterns = self.detect_threat_patterns(recent_events)
                
                for pattern_type, events in patterns.items():
                    if len(events) >= THREAT_DETECTION_CONFIG["detection_rules"][pattern_type]["threshold"]:
                        await self.create_pattern_alert(pattern_type, ThreatLevel.HIGH, {
                            "pattern_type": pattern_type,
                            "event_count": len(events),
                            "events": events[:5]  # First 5 events
                        })
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                monitor_logger.error(f"Threat pattern analysis error: {str(e)}")
                await asyncio.sleep(600)
    
    async def generate_security_reports(self):
        """Generate periodic security reports"""
        while self.monitoring_active:
            try:
                # Generate daily report
                if datetime.now(timezone.utc).hour == 0 and datetime.now(timezone.utc).minute < 5:
                    await self.generate_daily_report()
                
                # Generate weekly report
                if datetime.now(timezone.utc).weekday() == 0 and datetime.now(timezone.utc).hour == 1:
                    await self.generate_weekly_report()
                
                await asyncio.sleep(3600)  # Check every hour
                
            except Exception as e:
                monitor_logger.error(f"Report generation error: {str(e)}")
                await asyncio.sleep(7200)
    
    async def get_recent_security_events(self) -> List[Dict]:
        """Get recent security events from database"""
        try:
            db = next(get_db())
            events = db.query(SecurityEvent).filter(
                SecurityEvent.timestamp > datetime.now(timezone.utc) - timedelta(hours=1)
            ).all()
            
            return [
                {
                    "id": event.id,
                    "event_type": event.event_type,
                    "user_id": event.user_id,
                    "ip_address": event.ip_address,
                    "details": event.details,
                    "timestamp": event.timestamp,
                    "severity": event.severity
                }
                for event in events
            ]
        except Exception as e:
            monitor_logger.error(f"Error getting security events: {str(e)}")
            return []
    
    def analyze_event_threat_level(self, event: Dict) -> ThreatLevel:
        """Analyze threat level of a security event"""
        # Base threat levels
        threat_levels = {
            "login_failed": ThreatLevel.LOW,
            "login_success": ThreatLevel.LOW,
            "threat_detected": ThreatLevel.HIGH,
            "sql_injection": ThreatLevel.CRITICAL,
            "xss_detected": ThreatLevel.HIGH,
            "ddos_attack": ThreatLevel.CRITICAL,
            "data_breach": ThreatLevel.CRITICAL,
            "privilege_escalation": ThreatLevel.HIGH
        }
        
        base_level = threat_levels.get(event["event_type"], ThreatLevel.LOW)
        
        # Adjust based on frequency
        if event.get("frequency", 1) > 10:
            if base_level == ThreatLevel.LOW:
                base_level = ThreatLevel.MEDIUM
            elif base_level == ThreatLevel.MEDIUM:
                base_level = ThreatLevel.HIGH
        
        return base_level
    
    def is_suspicious_query(self, query: str) -> bool:
        """Check if a database query is suspicious"""
        suspicious_patterns = [
            "union select",
            "drop table",
            "delete from",
            "update set",
            "insert into",
            "create table",
            "alter table",
            "exec ",
            "execute ",
            "xp_",
            "sp_"
        ]
        
        query_lower = query.lower()
        return any(pattern in query_lower for pattern in suspicious_patterns)
    
    def detect_threat_patterns(self, events: List[Dict]) -> Dict[str, List[Dict]]:
        """Detect threat patterns in security events"""
        patterns = {}
        
        for event in events:
            for pattern_type, pattern_indicators in self.threat_patterns.items():
                if any(indicator in event["event_type"].lower() for indicator in pattern_indicators):
                    if pattern_type not in patterns:
                        patterns[pattern_type] = []
                    patterns[pattern_type].append(event)
        
        return patterns
    
    async def create_security_alert(self, event: Dict, threat_level: ThreatLevel):
        """Create a security alert"""
        alert = SecurityAlert(
            alert_id=encryption_manager.generate_secure_id(),
            threat_level=threat_level,
            alert_type="security_event",
            description=f"Security event detected: {event['event_type']}",
            source_ip=event.get("ip_address", "unknown"),
            user_id=event.get("user_id"),
            timestamp=datetime.now(timezone.utc),
            details=event
        )
        
        self.alerts.append(alert)
        await self.notify_security_alert(alert)
    
    async def create_system_alert(self, alert_type: str, threat_level: ThreatLevel, details: Dict):
        """Create a system alert"""
        alert = SecurityAlert(
            alert_id=encryption_manager.generate_secure_id(),
            threat_level=threat_level,
            alert_type=alert_type,
            description=f"System alert: {alert_type}",
            source_ip="system",
            user_id=None,
            timestamp=datetime.now(timezone.utc),
            details=details
        )
        
        self.alerts.append(alert)
        await self.notify_security_alert(alert)
    
    async def create_network_alert(self, alert_type: str, threat_level: ThreatLevel, details: Dict):
        """Create a network alert"""
        alert = SecurityAlert(
            alert_id=encryption_manager.generate_secure_id(),
            threat_level=threat_level,
            alert_type=alert_type,
            description=f"Network alert: {alert_type}",
            source_ip="network",
            user_id=None,
            timestamp=datetime.now(timezone.utc),
            details=details
        )
        
        self.alerts.append(alert)
        await self.notify_security_alert(alert)
    
    async def create_database_alert(self, alert_type: str, threat_level: ThreatLevel, details: Dict):
        """Create a database alert"""
        alert = SecurityAlert(
            alert_id=encryption_manager.generate_secure_id(),
            threat_level=threat_level,
            alert_type=alert_type,
            description=f"Database alert: {alert_type}",
            source_ip="database",
            user_id=None,
            timestamp=datetime.now(timezone.utc),
            details=details
        )
        
        self.alerts.append(alert)
        await self.notify_security_alert(alert)
    
    async def create_user_alert(self, alert_type: str, threat_level: ThreatLevel, details: Dict):
        """Create a user activity alert"""
        alert = SecurityAlert(
            alert_id=encryption_manager.generate_secure_id(),
            threat_level=threat_level,
            alert_type=alert_type,
            description=f"User activity alert: {alert_type}",
            source_ip="user_activity",
            user_id=details.get("user_id"),
            timestamp=datetime.now(timezone.utc),
            details=details
        )
        
        self.alerts.append(alert)
        await self.notify_security_alert(alert)
    
    async def create_pattern_alert(self, pattern_type: str, threat_level: ThreatLevel, details: Dict):
        """Create a threat pattern alert"""
        alert = SecurityAlert(
            alert_id=encryption_manager.generate_secure_id(),
            threat_level=threat_level,
            alert_type=f"threat_pattern_{pattern_type}",
            description=f"Threat pattern detected: {pattern_type}",
            source_ip="pattern_analysis",
            user_id=None,
            timestamp=datetime.now(timezone.utc),
            details=details
        )
        
        self.alerts.append(alert)
        await self.notify_security_alert(alert)
    
    async def notify_security_alert(self, alert: SecurityAlert):
        """Notify about security alert"""
        # Log the alert
        monitor_logger.warning(f"SECURITY ALERT: {alert.threat_level.value.upper()} - {alert.description}")
        
        # For critical alerts, send immediate notification
        if alert.threat_level == ThreatLevel.CRITICAL:
            await self.send_emergency_notification(alert)
        
        # Store alert in database
        await self.store_alert_in_database(alert)
    
    async def send_emergency_notification(self, alert: SecurityAlert):
        """Send emergency notification for critical alerts"""
        # This would integrate with notification systems
        # For now, just log
        monitor_logger.critical(f"EMERGENCY NOTIFICATION: {alert.description}")
    
    async def store_alert_in_database(self, alert: SecurityAlert):
        """Store alert in database"""
        try:
            db = next(get_db())
            security_event = SecurityEvent(
                event_type=f"alert_{alert.alert_type}",
                user_id=alert.user_id,
                details=json.dumps(alert.details),
                severity=alert.threat_level.value,
                ip_address=alert.source_ip,
                timestamp=alert.timestamp
            )
            db.add(security_event)
            db.commit()
            db.close()
        except Exception as e:
            monitor_logger.error(f"Error storing alert in database: {str(e)}")
    
    async def generate_daily_report(self):
        """Generate daily security report"""
        try:
            # Get daily statistics
            db = next(get_db())
            
            # Security events count
            events_count = db.query(SecurityEvent).filter(
                SecurityEvent.timestamp > datetime.now(timezone.utc) - timedelta(days=1)
            ).count()
            
            # Alerts by severity
            alerts_by_severity = db.query(
                SecurityEvent.severity,
                func.count(SecurityEvent.id)
            ).filter(
                SecurityEvent.timestamp > datetime.now(timezone.utc) - timedelta(days=1)
            ).group_by(SecurityEvent.severity).all()
            
            # System metrics
            system_metrics = self.system_metrics
            
            # Generate report
            report = {
                "date": datetime.now(timezone.utc).date().isoformat(),
                "total_events": events_count,
                "alerts_by_severity": dict(alerts_by_severity),
                "system_metrics": system_metrics,
                "active_alerts": len([a for a in self.alerts if not a.resolved]),
                "threat_level": self.get_overall_threat_level()
            }
            
            # Store report
            await self.store_security_report("daily", report)
            
            db.close()
            monitor_logger.info("Daily security report generated")
            
        except Exception as e:
            monitor_logger.error(f"Error generating daily report: {str(e)}")
    
    async def generate_weekly_report(self):
        """Generate weekly security report"""
        try:
            # Similar to daily report but for weekly data
            report = {
                "week": datetime.now(timezone.utc).isocalendar()[1],
                "year": datetime.now(timezone.utc).year,
                "summary": "Weekly security summary"
            }
            
            await self.store_security_report("weekly", report)
            monitor_logger.info("Weekly security report generated")
            
        except Exception as e:
            monitor_logger.error(f"Error generating weekly report: {str(e)}")
    
    async def store_security_report(self, report_type: str, report_data: Dict):
        """Store security report"""
        try:
            # This would store reports in database or file system
            # For now, just log
            monitor_logger.info(f"Security report stored: {report_type}")
        except Exception as e:
            monitor_logger.error(f"Error storing security report: {str(e)}")
    
    def get_overall_threat_level(self) -> ThreatLevel:
        """Get overall system threat level"""
        if not self.alerts:
            return ThreatLevel.LOW
        
        # Get unresolved alerts
        unresolved_alerts = [a for a in self.alerts if not a.resolved]
        
        if not unresolved_alerts:
            return ThreatLevel.LOW
        
        # Check for critical alerts
        if any(a.threat_level == ThreatLevel.CRITICAL for a in unresolved_alerts):
            return ThreatLevel.CRITICAL
        
        # Check for high alerts
        if any(a.threat_level == ThreatLevel.HIGH for a in unresolved_alerts):
            return ThreatLevel.HIGH
        
        # Check for medium alerts
        if any(a.threat_level == ThreatLevel.MEDIUM for a in unresolved_alerts):
            return ThreatLevel.MEDIUM
        
        return ThreatLevel.LOW
    
    def stop_monitoring(self):
        """Stop the security monitoring system"""
        self.monitoring_active = False
        monitor_logger.info("Security monitoring system stopped")

# Initialize global security monitor
security_monitor = EnhancedSecurityMonitor()

# Utility functions
async def start_security_monitoring():
    """Start the security monitoring system"""
    await security_monitor.start_monitoring()

def get_security_status() -> Dict[str, Any]:
    """Get current security status"""
    return {
        "monitoring_active": security_monitor.monitoring_active,
        "active_alerts": len([a for a in security_monitor.alerts if not a.resolved]),
        "overall_threat_level": security_monitor.get_overall_threat_level().value,
        "system_metrics": security_monitor.system_metrics,
        "last_scan_time": security_monitor.last_scan_time.isoformat()
    }

def get_recent_alerts(limit: int = 10) -> List[Dict]:
    """Get recent security alerts"""
    recent_alerts = sorted(
        [a for a in security_monitor.alerts if not a.resolved],
        key=lambda x: x.timestamp,
        reverse=True
    )[:limit]
    
    return [
        {
            "alert_id": alert.alert_id,
            "threat_level": alert.threat_level.value,
            "alert_type": alert.alert_type,
            "description": alert.description,
            "source_ip": alert.source_ip,
            "timestamp": alert.timestamp.isoformat(),
            "details": alert.details
        }
        for alert in recent_alerts
    ] 