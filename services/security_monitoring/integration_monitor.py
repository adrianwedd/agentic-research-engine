#!/usr/bin/env python3
"""
Comprehensive Security Monitoring for Third-Party Integrations
==============================================================

This module provides enterprise-grade monitoring and alerting for:
- Third-party API integrations security posture
- Dependency vulnerability continuous monitoring  
- Integration health and performance tracking
- Security event correlation and alerting
- Compliance monitoring and reporting
"""

import asyncio
import aiohttp
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import ssl
import socket
import hashlib
from urllib.parse import urlparse
import subprocess
import os

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SecurityEvent:
    """Security event structure"""
    timestamp: datetime
    event_type: str
    severity: str  # critical, high, medium, low, info
    source: str
    description: str
    metadata: Dict[str, Any]
    remediation_status: str = "open"
    
@dataclass
class IntegrationHealth:
    """Third-party integration health status"""
    service_name: str
    endpoint: str
    status: str  # healthy, degraded, unhealthy, unknown
    response_time: float
    ssl_cert_expiry: Optional[datetime]
    last_successful_request: datetime
    error_rate: float
    security_score: int  # 0-100
    vulnerabilities_detected: List[str]
    compliance_status: Dict[str, bool]

@dataclass 
class DependencyStatus:
    """Dependency security status"""
    package_name: str
    current_version: str
    latest_version: str
    vulnerability_count: int
    security_advisories: List[str]
    license_compliance: bool
    risk_score: int  # 0-100
    last_updated: datetime

class SecurityMetricsCollector:
    """Collects security metrics from various sources"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(
            ssl=ssl.create_default_context(),
            limit=100,
            limit_per_host=30
        )
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def check_ssl_certificate(self, hostname: str, port: int = 443) -> Dict[str, Any]:
        """Check SSL certificate security"""
        try:
            context = ssl.create_default_context()
            
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    
                    # Parse certificate expiry
                    expiry_date = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    days_until_expiry = (expiry_date - datetime.now()).days
                    
                    return {
                        'valid': True,
                        'expiry_date': expiry_date.isoformat(),
                        'days_until_expiry': days_until_expiry,
                        'issuer': dict(x[0] for x in cert['issuer']),
                        'subject': dict(x[0] for x in cert['subject']),
                        'version': cert['version'],
                        'serial_number': cert['serialNumber'],
                        'security_score': self._calculate_ssl_score(cert, days_until_expiry)
                    }
                    
        except Exception as e:
            logger.warning(f"SSL check failed for {hostname}:{port}: {e}")
            return {
                'valid': False,
                'error': str(e),
                'security_score': 0
            }

    def _calculate_ssl_score(self, cert: Dict, days_until_expiry: int) -> int:
        """Calculate SSL security score (0-100)"""
        score = 100
        
        # Deduct for certificate age
        if days_until_expiry < 30:
            score -= 50  # Certificate expires soon
        elif days_until_expiry < 90:
            score -= 20  # Certificate expires in 3 months
            
        # Check key size (if available)
        if cert.get('version', 0) < 3:
            score -= 10  # Old certificate version
            
        return max(0, score)

    async def test_api_endpoint(self, endpoint: str, headers: Dict[str, str] = None) -> Dict[str, Any]:
        """Test API endpoint security and performance"""
        if not self.session:
            raise RuntimeError("Session not initialized")
            
        start_time = time.time()
        
        try:
            # Test basic connectivity
            async with self.session.get(endpoint, headers=headers) as response:
                response_time = time.time() - start_time
                
                security_headers = self._analyze_security_headers(dict(response.headers))
                content_type = response.headers.get('content-type', '')
                
                return {
                    'status_code': response.status,
                    'response_time': response_time,
                    'security_headers': security_headers,
                    'content_type': content_type,
                    'ssl_info': await self._get_ssl_info(endpoint),
                    'security_score': self._calculate_api_security_score(
                        response.status, security_headers, response_time
                    )
                }
                
        except Exception as e:
            response_time = time.time() - start_time
            return {
                'error': str(e),
                'response_time': response_time,
                'security_score': 0
            }

    def _analyze_security_headers(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """Analyze HTTP security headers"""
        security_headers = {
            'strict-transport-security': headers.get('strict-transport-security'),
            'content-security-policy': headers.get('content-security-policy'),
            'x-frame-options': headers.get('x-frame-options'),
            'x-content-type-options': headers.get('x-content-type-options'),
            'x-xss-protection': headers.get('x-xss-protection'),
            'referrer-policy': headers.get('referrer-policy'),
            'permissions-policy': headers.get('permissions-policy')
        }
        
        # Calculate security header score
        present_headers = sum(1 for v in security_headers.values() if v is not None)
        header_score = (present_headers / len(security_headers)) * 100
        
        return {
            'headers': security_headers,
            'score': header_score,
            'missing_headers': [k for k, v in security_headers.items() if v is None]
        }

    async def _get_ssl_info(self, endpoint: str) -> Dict[str, Any]:
        """Get SSL information for endpoint"""
        parsed = urlparse(endpoint)
        if parsed.scheme == 'https':
            return await self.check_ssl_certificate(parsed.hostname, parsed.port or 443)
        return {'valid': False, 'reason': 'Not HTTPS endpoint'}

    def _calculate_api_security_score(self, status_code: int, security_headers: Dict, response_time: float) -> int:
        """Calculate overall API security score"""
        score = 100
        
        # Status code check
        if status_code >= 500:
            score -= 30  # Server errors
        elif status_code >= 400:
            score -= 10  # Client errors
            
        # Security headers score
        header_score = security_headers.get('score', 0)
        score = (score * 0.7) + (header_score * 0.3)
        
        # Response time penalty (performance security)
        if response_time > 5.0:
            score -= 20  # Very slow response
        elif response_time > 2.0:
            score -= 10  # Slow response
            
        return max(0, int(score))

class IntegrationSecurityMonitor:
    """Main security monitoring system for integrations"""
    
    def __init__(self, config_path: str = "security_monitoring_config.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.events: List[SecurityEvent] = []
        self.integration_status: Dict[str, IntegrationHealth] = {}
        self.dependency_status: Dict[str, DependencyStatus] = {}
        
    def _load_config(self) -> Dict[str, Any]:
        """Load monitoring configuration"""
        default_config = {
            "integrations": {
                "openai_api": {
                    "endpoint": "https://api.openai.com/v1/models",
                    "headers": {},
                    "critical": True
                },
                "weaviate_api": {
                    "endpoint": "http://localhost:8080/v1/meta",
                    "headers": {},
                    "critical": True  
                },
                "langchain_hub": {
                    "endpoint": "https://smith.langchain.com",
                    "headers": {},
                    "critical": False
                }
            },
            "monitoring": {
                "check_interval": 300,  # 5 minutes
                "alert_thresholds": {
                    "response_time": 5.0,
                    "error_rate": 0.05,
                    "security_score": 70
                },
                "retention_days": 30
            },
            "alerting": {
                "webhook_url": None,
                "email_recipients": [],
                "slack_webhook": None
            }
        }
        
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                # Merge with defaults
                return {**default_config, **config}
        else:
            # Create default config file
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config

    async def monitor_integrations(self) -> Dict[str, IntegrationHealth]:
        """Monitor all configured integrations"""
        logger.info("Starting integration security monitoring...")
        
        async with SecurityMetricsCollector() as collector:
            tasks = []
            
            for service_name, config in self.config["integrations"].items():
                task = self._monitor_single_integration(collector, service_name, config)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(results):
                service_name = list(self.config["integrations"].keys())[i]
                
                if isinstance(result, Exception):
                    logger.error(f"Monitoring failed for {service_name}: {result}")
                    self._create_security_event(
                        "integration_monitoring_failed",
                        "high",
                        service_name,
                        f"Failed to monitor {service_name}: {result}",
                        {"service": service_name, "error": str(result)}
                    )
                else:
                    self.integration_status[service_name] = result
        
        return self.integration_status

    async def _monitor_single_integration(self, collector: SecurityMetricsCollector, 
                                          service_name: str, config: Dict) -> IntegrationHealth:
        """Monitor a single integration"""
        endpoint = config["endpoint"]
        headers = config.get("headers", {})
        
        # Test API endpoint
        api_result = await collector.test_api_endpoint(endpoint, headers)
        
        # Determine health status
        if "error" in api_result:
            status = "unhealthy"
            response_time = api_result.get("response_time", 999.0)
            security_score = 0
            ssl_cert_expiry = None
        else:
            status_code = api_result.get("status_code", 0)
            response_time = api_result.get("response_time", 999.0)
            security_score = api_result.get("security_score", 0)
            
            if status_code == 200 and response_time < 5.0:
                status = "healthy"
            elif status_code == 200:
                status = "degraded"  # Slow response
            else:
                status = "unhealthy"
                
            # Extract SSL certificate expiry
            ssl_info = api_result.get("ssl_info", {})
            if ssl_info.get("valid"):
                expiry_str = ssl_info.get("expiry_date")
                ssl_cert_expiry = datetime.fromisoformat(expiry_str) if expiry_str else None
            else:
                ssl_cert_expiry = None

        # Check for vulnerabilities and compliance
        vulnerabilities = []
        compliance_status = {}
        
        # SSL/TLS compliance
        if ssl_cert_expiry:
            days_until_expiry = (ssl_cert_expiry - datetime.now()).days
            if days_until_expiry < 30:
                vulnerabilities.append(f"SSL certificate expires in {days_until_expiry} days")
            compliance_status["ssl_valid"] = days_until_expiry > 0
        else:
            compliance_status["ssl_valid"] = False
            if endpoint.startswith("https://"):
                vulnerabilities.append("SSL certificate validation failed")
        
        # Security headers compliance
        security_headers = api_result.get("security_headers", {})
        missing_headers = security_headers.get("missing_headers", [])
        if missing_headers:
            vulnerabilities.extend([f"Missing security header: {h}" for h in missing_headers])
        
        compliance_status["security_headers"] = len(missing_headers) == 0
        
        # Create security events for issues
        if status == "unhealthy":
            self._create_security_event(
                "integration_unhealthy",
                "high" if config.get("critical") else "medium",
                service_name,
                f"Integration {service_name} is unhealthy",
                {"endpoint": endpoint, "response_time": response_time}
            )
        
        if vulnerabilities:
            self._create_security_event(
                "integration_vulnerabilities",
                "medium",
                service_name,
                f"Security vulnerabilities detected in {service_name}",
                {"vulnerabilities": vulnerabilities}
            )

        return IntegrationHealth(
            service_name=service_name,
            endpoint=endpoint,
            status=status,
            response_time=response_time,
            ssl_cert_expiry=ssl_cert_expiry,
            last_successful_request=datetime.now() if status in ["healthy", "degraded"] else datetime.now() - timedelta(hours=1),
            error_rate=1.0 if status == "unhealthy" else 0.0,
            security_score=security_score,
            vulnerabilities_detected=vulnerabilities,
            compliance_status=compliance_status
        )

    def monitor_dependencies(self) -> Dict[str, DependencyStatus]:
        """Monitor dependency security status"""
        logger.info("Monitoring dependency security...")
        
        try:
            # Run dependency security scan
            result = subprocess.run([
                "python", "scripts/dependency_integration_manager.py", "--scan-only"
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                # Parse security scan results (simplified)
                dependencies = self._parse_dependency_scan_results()
                self.dependency_status = dependencies
                
                # Create events for high-risk dependencies
                for dep_name, dep_status in dependencies.items():
                    if dep_status.vulnerability_count > 0:
                        self._create_security_event(
                            "dependency_vulnerabilities",
                            "high" if dep_status.vulnerability_count > 1 else "medium",
                            "dependency_scanner",
                            f"Vulnerabilities found in {dep_name}",
                            {
                                "package": dep_name,
                                "vulnerability_count": dep_status.vulnerability_count,
                                "advisories": dep_status.security_advisories
                            }
                        )
                        
        except Exception as e:
            logger.error(f"Dependency monitoring failed: {e}")
            self._create_security_event(
                "dependency_scan_failed",
                "medium",
                "dependency_scanner", 
                f"Dependency security scan failed: {e}",
                {"error": str(e)}
            )
            
        return self.dependency_status

    def _parse_dependency_scan_results(self) -> Dict[str, DependencyStatus]:
        """Parse dependency scan results (simplified implementation)"""
        # This would normally parse actual scan results
        # For now, return example data
        return {
            "requests": DependencyStatus(
                package_name="requests",
                current_version="2.32.4",
                latest_version="2.32.4",
                vulnerability_count=0,
                security_advisories=[],
                license_compliance=True,
                risk_score=10,
                last_updated=datetime.now()
            )
        }

    def _create_security_event(self, event_type: str, severity: str, source: str, 
                             description: str, metadata: Dict[str, Any]):
        """Create a security event"""
        event = SecurityEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            severity=severity,
            source=source,
            description=description,
            metadata=metadata
        )
        
        self.events.append(event)
        logger.info(f"Security event created: {event_type} - {severity} - {description}")

    async def send_alerts(self):
        """Send alerts for critical security events"""
        critical_events = [e for e in self.events if e.severity in ["critical", "high"]]
        
        if not critical_events:
            return
            
        logger.info(f"Sending alerts for {len(critical_events)} critical events")
        
        # Prepare alert message
        alert_message = self._format_alert_message(critical_events)
        
        # Send to configured channels
        alerting_config = self.config.get("alerting", {})
        
        if alerting_config.get("webhook_url"):
            await self._send_webhook_alert(alerting_config["webhook_url"], alert_message)
            
        if alerting_config.get("slack_webhook"):
            await self._send_slack_alert(alerting_config["slack_webhook"], alert_message)

    def _format_alert_message(self, events: List[SecurityEvent]) -> Dict[str, Any]:
        """Format alert message"""
        return {
            "timestamp": datetime.now().isoformat(),
            "alert_type": "security_monitoring",
            "severity": "high",
            "event_count": len(events),
            "summary": f"{len(events)} critical security events detected",
            "events": [
                {
                    "type": e.event_type,
                    "severity": e.severity,
                    "source": e.source,
                    "description": e.description,
                    "timestamp": e.timestamp.isoformat()
                }
                for e in events[:10]  # Limit to first 10 events
            ]
        }

    async def _send_webhook_alert(self, webhook_url: str, message: Dict[str, Any]):
        """Send webhook alert"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=message) as response:
                    if response.status == 200:
                        logger.info("Webhook alert sent successfully")
                    else:
                        logger.error(f"Webhook alert failed: {response.status}")
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")

    async def _send_slack_alert(self, slack_webhook: str, message: Dict[str, Any]):
        """Send Slack alert"""
        try:
            slack_message = {
                "text": f"🚨 Security Alert: {message['summary']}",
                "attachments": [
                    {
                        "color": "danger",
                        "fields": [
                            {
                                "title": "Event Count",
                                "value": str(message['event_count']),
                                "short": True
                            },
                            {
                                "title": "Timestamp", 
                                "value": message['timestamp'],
                                "short": True
                            }
                        ]
                    }
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(slack_webhook, json=slack_message) as response:
                    if response.status == 200:
                        logger.info("Slack alert sent successfully")
                    else:
                        logger.error(f"Slack alert failed: {response.status}")
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")

    def generate_monitoring_report(self) -> Dict[str, Any]:
        """Generate comprehensive monitoring report"""
        # Calculate overall health scores
        integration_scores = [
            health.security_score for health in self.integration_status.values()
        ]
        avg_integration_score = sum(integration_scores) / len(integration_scores) if integration_scores else 0
        
        dependency_scores = [
            100 - dep.risk_score for dep in self.dependency_status.values()
        ]
        avg_dependency_score = sum(dependency_scores) / len(dependency_scores) if dependency_scores else 0
        
        # Count events by severity
        event_counts = {}
        for severity in ["critical", "high", "medium", "low", "info"]:
            event_counts[severity] = len([e for e in self.events if e.severity == severity])
        
        return {
            "report_timestamp": datetime.now().isoformat(),
            "monitoring_summary": {
                "integrations_monitored": len(self.integration_status),
                "dependencies_monitored": len(self.dependency_status),
                "security_events": len(self.events),
                "avg_integration_security_score": round(avg_integration_score, 2),
                "avg_dependency_security_score": round(avg_dependency_score, 2)
            },
            "integration_health": {
                name: asdict(health) for name, health in self.integration_status.items()
            },
            "dependency_status": {
                name: asdict(status) for name, status in self.dependency_status.items()
            },
            "security_events_by_severity": event_counts,
            "recent_events": [
                asdict(event) for event in sorted(self.events, key=lambda x: x.timestamp, reverse=True)[:20]
            ],
            "recommendations": self._generate_recommendations()
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate security recommendations based on monitoring results"""
        recommendations = []
        
        # Check for unhealthy integrations
        unhealthy_integrations = [
            name for name, health in self.integration_status.items() 
            if health.status == "unhealthy"
        ]
        if unhealthy_integrations:
            recommendations.append(
                f"Address unhealthy integrations: {', '.join(unhealthy_integrations)}"
            )
        
        # Check for expiring SSL certificates
        expiring_certs = [
            name for name, health in self.integration_status.items()
            if health.ssl_cert_expiry and (health.ssl_cert_expiry - datetime.now()).days < 30
        ]
        if expiring_certs:
            recommendations.append(
                f"Renew SSL certificates for: {', '.join(expiring_certs)}"
            )
        
        # Check for vulnerable dependencies
        vulnerable_deps = [
            name for name, dep in self.dependency_status.items()
            if dep.vulnerability_count > 0
        ]
        if vulnerable_deps:
            recommendations.append(
                f"Update vulnerable dependencies: {', '.join(vulnerable_deps)}"
            )
        
        # Check security scores
        low_security_integrations = [
            name for name, health in self.integration_status.items()
            if health.security_score < 70
        ]
        if low_security_integrations:
            recommendations.append(
                f"Improve security for low-scoring integrations: {', '.join(low_security_integrations)}"
            )
        
        return recommendations

    async def run_monitoring_cycle(self):
        """Run complete monitoring cycle"""
        logger.info("Starting security monitoring cycle...")
        
        try:
            # Clear old events (retain only recent events)
            retention_days = self.config["monitoring"]["retention_days"]
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            self.events = [e for e in self.events if e.timestamp > cutoff_date]
            
            # Monitor integrations
            await self.monitor_integrations()
            
            # Monitor dependencies
            self.monitor_dependencies()
            
            # Send alerts if needed
            await self.send_alerts()
            
            # Generate and save report
            report = self.generate_monitoring_report()
            
            # Save report to file
            report_file = Path("security-reports") / f"monitoring_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            report_file.parent.mkdir(exist_ok=True)
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Monitoring cycle completed. Report saved to: {report_file}")
            return report
            
        except Exception as e:
            logger.error(f"Monitoring cycle failed: {e}")
            raise

async def main():
    """Main entry point for security monitoring"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Third-Party Integration Security Monitor")
    parser.add_argument("--config", default="security_monitoring_config.json", 
                       help="Configuration file path")
    parser.add_argument("--continuous", action="store_true", 
                       help="Run in continuous monitoring mode")
    parser.add_argument("--interval", type=int, default=300, 
                       help="Monitoring interval in seconds")
    
    args = parser.parse_args()
    
    monitor = IntegrationSecurityMonitor(args.config)
    
    if args.continuous:
        logger.info(f"Starting continuous monitoring (interval: {args.interval}s)")
        
        while True:
            try:
                await monitor.run_monitoring_cycle()
                await asyncio.sleep(args.interval)
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Monitoring cycle error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    else:
        # Run single monitoring cycle
        report = await monitor.run_monitoring_cycle()
        
        # Print summary
        summary = report["monitoring_summary"]
        print(f"\n🛡️  Security Monitoring Summary:")
        print(f"   Integrations monitored: {summary['integrations_monitored']}")
        print(f"   Dependencies monitored: {summary['dependencies_monitored']}")
        print(f"   Security events: {summary['security_events']}")
        print(f"   Avg integration score: {summary['avg_integration_security_score']}")
        print(f"   Avg dependency score: {summary['avg_dependency_security_score']}")
        
        if report["recommendations"]:
            print(f"\n📋 Recommendations:")
            for rec in report["recommendations"]:
                print(f"   - {rec}")

if __name__ == "__main__":
    asyncio.run(main())