#!/usr/bin/env python3

"""
Security Integration Manager for Agentic Research Engine
Comprehensive security integration validation and dependency management
"""

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import asyncio
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('security-integration.log')
    ]
)

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Data class for individual validation results"""
    name: str
    status: str  # pass, fail, partial
    score: int
    message: str
    timestamp: str


@dataclass
class CategoryResult:
    """Data class for validation category results"""
    status: str
    score: int
    checks: List[ValidationResult]


@dataclass
class SecurityIntegrationReport:
    """Comprehensive security integration validation report"""
    timestamp: str
    repository: str
    validation_version: str
    overall_status: str
    categories: Dict[str, CategoryResult]
    recommendations: List[str]
    dependency_prs: List[Dict]
    total_score: int
    grade: str


class SecurityIntegrationManager:
    """
    Comprehensive security integration manager for dependency security,
    vulnerability management, and incident response capabilities
    """
    
    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.timestamp = datetime.now().isoformat()
        
        # Initialize validation results
        self.categories = {
            'workflow_validation': CategoryResult('unknown', 0, []),
            'security_tools': CategoryResult('unknown', 0, []),
            'dependency_management': CategoryResult('unknown', 0, []),
            'monitoring_systems': CategoryResult('unknown', 0, []),
            'incident_response': CategoryResult('unknown', 0, [])
        }
        
        self.recommendations = []
        self.dependency_prs = []
        
        # Ensure reports directory exists
        self.reports_dir = self.project_root / 'security-reports'
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Security Integration Manager initialized for {self.project_root}")
    
    async def run_comprehensive_validation(self) -> SecurityIntegrationReport:
        """Run comprehensive security integration validation"""
        logger.info("🔍 Starting comprehensive security integration validation...")
        
        try:
            # Run validation categories
            await self._validate_workflows()
            await self._validate_security_tools()
            await self._validate_dependency_management()
            await self._validate_monitoring_systems()
            await self._validate_incident_response()
            
            # Analyze dependency PRs
            await self._analyze_dependency_prs()
            
            # Generate recommendations
            await self._generate_recommendations()
            
            # Calculate final scores
            report = await self._generate_final_report()
            
            # Save validation results
            await self._save_results(report)
            
            logger.info("✅ Security integration validation completed")
            return report
            
        except Exception as error:
            logger.error(f"❌ Security integration validation failed: {error}")
            raise
    
    async def _validate_workflows(self) -> None:
        """Validate GitHub Actions security workflows"""
        logger.info("🔧 Validating security workflows...")
        
        workflow_dir = self.project_root / '.github' / 'workflows'
        required_workflows = [
            'comprehensive-security-integration.yml',
            'dependency-security-scan.yml'  # May not exist yet
        ]
        
        total_checks = 0
        passed_checks = 0
        
        for workflow in required_workflows:
            total_checks += 1
            workflow_path = workflow_dir / workflow
            
            if workflow_path.exists():
                logger.info(f"✅ Workflow found: {workflow}")
                
                # Validate workflow content
                try:
                    content = workflow_path.read_text()
                    if 'security' in content.lower() and 'vulnerability' in content.lower():
                        logger.info(f"✅ Security workflow content validated: {workflow}")
                        passed_checks += 1
                        self._add_validation_result(
                            'workflow_validation', f'workflow_{workflow}', 'pass', 10,
                            f"Security workflow {workflow} exists and contains security content"
                        )
                    else:
                        logger.warning(f"⚠️ Workflow lacks security content: {workflow}")
                        self._add_validation_result(
                            'workflow_validation', f'workflow_{workflow}', 'partial', 5,
                            f"Workflow {workflow} exists but may lack comprehensive security content"
                        )
                except Exception as e:
                    logger.error(f"❌ Error reading workflow {workflow}: {e}")
                    self._add_validation_result(
                        'workflow_validation', f'workflow_{workflow}', 'fail', 0,
                        f"Error reading workflow {workflow}: {str(e)}"
                    )
            else:
                logger.warning(f"⚠️ Required workflow missing: {workflow}")
                self._add_validation_result(
                    'workflow_validation', f'workflow_{workflow}', 'fail', 0,
                    f"Required workflow {workflow} is missing"
                )
        
        # Check for scheduled security scans
        security_workflow = workflow_dir / 'comprehensive-security-integration.yml'
        if security_workflow.exists():
            total_checks += 1
            content = security_workflow.read_text()
            if 'schedule:' in content and 'cron:' in content:
                logger.info("✅ Scheduled security scans configured")
                passed_checks += 1
                self._add_validation_result(
                    'workflow_validation', 'scheduled_scans', 'pass', 10,
                    "Scheduled security scans are configured"
                )
            else:
                logger.warning("⚠️ Scheduled security scans not configured")
                self._add_validation_result(
                    'workflow_validation', 'scheduled_scans', 'fail', 0,
                    "Scheduled security scans are not configured"
                )
        
        # Update category score
        self._update_category_score('workflow_validation', passed_checks, total_checks)
        logger.info(f"Workflow validation: {passed_checks}/{total_checks} checks passed")
    
    async def _validate_security_tools(self) -> None:
        """Validate security tools and configurations"""
        logger.info("🛠️ Validating security tools...")
        
        total_checks = 0
        passed_checks = 0
        
        # Check for Python security monitor
        total_checks += 1
        security_monitor = self.project_root / 'security' / 'python_security_monitor.py'
        if security_monitor.exists():
            logger.info("✅ Python security monitor found")
            
            # Validate script syntax
            result = subprocess.run(
                [sys.executable, '-m', 'py_compile', str(security_monitor)],
                capture_output=True
            )
            
            if result.returncode == 0:
                logger.info("✅ Security monitor syntax valid")
                passed_checks += 1
                self._add_validation_result(
                    'security_tools', 'security_monitor', 'pass', 15,
                    "Python security monitor exists and has valid syntax"
                )
            else:
                logger.error("❌ Security monitor syntax invalid")
                self._add_validation_result(
                    'security_tools', 'security_monitor', 'fail', 5,
                    "Security monitor exists but has syntax errors"
                )
        else:
            logger.error("❌ Python security monitor missing")
            self._add_validation_result(
                'security_tools', 'security_monitor', 'fail', 0,
                "Python security monitor script not found"
            )
        
        # Check for security tools availability
        security_tools = ['safety', 'bandit', 'pip-audit']
        for tool in security_tools:
            total_checks += 1
            result = subprocess.run(['which', tool], capture_output=True)
            
            if result.returncode == 0:
                logger.info(f"✅ Security tool available: {tool}")
                passed_checks += 1
                self._add_validation_result(
                    'security_tools', f'tool_{tool}', 'pass', 8,
                    f"Security tool {tool} is available"
                )
            else:
                logger.warning(f"⚠️ Security tool not available: {tool}")
                self._add_validation_result(
                    'security_tools', f'tool_{tool}', 'fail', 0,
                    f"Security tool {tool} is not installed or not in PATH"
                )
        
        # Check requirements.txt for security tools
        total_checks += 1
        requirements_file = self.project_root / 'requirements.txt'
        if requirements_file.exists():
            content = requirements_file.read_text()
            security_packages = ['safety', 'bandit', 'pip-audit']
            found_tools = [tool for tool in security_packages if tool in content]
            
            if found_tools:
                logger.info(f"✅ Security tools in requirements: {found_tools}")
                passed_checks += 1
                self._add_validation_result(
                    'security_tools', 'requirements_security_tools', 'pass', 10,
                    f"Security tools found in requirements.txt: {', '.join(found_tools)}"
                )
            else:
                logger.warning("⚠️ No security tools in requirements.txt")
                self._add_validation_result(
                    'security_tools', 'requirements_security_tools', 'partial', 3,
                    "No security tools explicitly listed in requirements.txt"
                )
        else:
            logger.warning("⚠️ requirements.txt not found")
            self._add_validation_result(
                'security_tools', 'requirements_security_tools', 'fail', 0,
                "requirements.txt file not found"
            )
        
        # Update category score
        self._update_category_score('security_tools', passed_checks, total_checks)
        logger.info(f"Security tools validation: {passed_checks}/{total_checks} checks passed")
    
    async def _validate_dependency_management(self) -> None:
        """Validate dependency management and security"""
        logger.info("📦 Validating dependency management...")
        
        total_checks = 0
        passed_checks = 0
        
        # Check for requirements files
        total_checks += 1
        requirements_file = self.project_root / 'requirements.txt'
        if requirements_file.exists():
            logger.info("✅ requirements.txt found")
            passed_checks += 1
            self._add_validation_result(
                'dependency_management', 'requirements_file', 'pass', 10,
                "requirements.txt file exists"
            )
        else:
            logger.error("❌ requirements.txt not found")
            self._add_validation_result(
                'dependency_management', 'requirements_file', 'fail', 0,
                "requirements.txt file not found"
            )
        
        # Check for security-related packages with version pinning
        total_checks += 1
        if requirements_file.exists():
            content = requirements_file.read_text()
            lines = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
            
            # Count pinned versions
            pinned_versions = sum(1 for line in lines if '==' in line or '>=' in line)
            total_packages = len(lines)
            
            if total_packages > 0:
                pin_percentage = (pinned_versions / total_packages) * 100
                if pin_percentage >= 80:
                    logger.info(f"✅ Good version pinning: {pin_percentage:.1f}% of packages pinned")
                    passed_checks += 1
                    self._add_validation_result(
                        'dependency_management', 'version_pinning', 'pass', 10,
                        f"Good version pinning: {pin_percentage:.1f}% of packages have pinned versions"
                    )
                else:
                    logger.warning(f"⚠️ Low version pinning: {pin_percentage:.1f}% of packages pinned")
                    self._add_validation_result(
                        'dependency_management', 'version_pinning', 'partial', 5,
                        f"Low version pinning: only {pin_percentage:.1f}% of packages have pinned versions"
                    )
            else:
                logger.warning("⚠️ No packages found in requirements.txt")
                self._add_validation_result(
                    'dependency_management', 'version_pinning', 'fail', 0,
                    "No packages found in requirements.txt"
                )
        
        # Check for security scan scripts or configurations
        total_checks += 1
        security_configs = [
            self.project_root / 'security_config.json',
            self.project_root / '.safety',
            self.project_root / 'bandit.yaml',
            self.project_root / 'pyproject.toml'
        ]
        
        found_configs = [config for config in security_configs if config.exists()]
        if found_configs:
            logger.info(f"✅ Security configurations found: {[c.name for c in found_configs]}")
            passed_checks += 1
            self._add_validation_result(
                'dependency_management', 'security_configs', 'pass', 8,
                f"Security configuration files found: {', '.join([c.name for c in found_configs])}"
            )
        else:
            logger.warning("⚠️ No security configuration files found")
            self._add_validation_result(
                'dependency_management', 'security_configs', 'partial', 3,
                "No security configuration files found"
            )
        
        # Update category score
        self._update_category_score('dependency_management', passed_checks, total_checks)
        logger.info(f"Dependency management validation: {passed_checks}/{total_checks} checks passed")
    
    async def _validate_monitoring_systems(self) -> None:
        """Validate monitoring and alerting systems"""
        logger.info("📊 Validating monitoring systems...")
        
        total_checks = 0
        passed_checks = 0
        
        # Check for security reports directory
        total_checks += 1
        if self.reports_dir.exists() and self.reports_dir.is_dir():
            logger.info("✅ Security reports directory exists")
            passed_checks += 1
            self._add_validation_result(
                'monitoring_systems', 'reports_directory', 'pass', 5,
                "Security reports directory exists and is accessible"
            )
        else:
            logger.error("❌ Security reports directory not accessible")
            self._add_validation_result(
                'monitoring_systems', 'reports_directory', 'fail', 0,
                "Security reports directory not accessible"
            )
        
        # Check for existing security reports
        total_checks += 1
        security_report_files = list(self.reports_dir.glob('security-report-*.json'))
        if security_report_files:
            logger.info(f"✅ Found {len(security_report_files)} existing security reports")
            passed_checks += 1
            self._add_validation_result(
                'monitoring_systems', 'existing_reports', 'pass', 8,
                f"Found {len(security_report_files)} existing security reports"
            )
        else:
            logger.info("ℹ️ No existing security reports (expected for new setup)")
            self._add_validation_result(
                'monitoring_systems', 'existing_reports', 'partial', 5,
                "No existing security reports found (expected for new setup)"
            )
        
        # Test logging capabilities
        total_checks += 1
        try:
            test_log_file = self.project_root / 'test-security-integration.log'
            test_log_file.write_text(f"Security integration test - {self.timestamp}\n")
            test_log_file.unlink()  # Clean up
            
            logger.info("✅ Logging system functional")
            passed_checks += 1
            self._add_validation_result(
                'monitoring_systems', 'logging_system', 'pass', 10,
                "Logging system is functional"
            )
        except Exception as e:
            logger.error(f"❌ Logging system issues: {e}")
            self._add_validation_result(
                'monitoring_systems', 'logging_system', 'fail', 0,
                f"Logging system issues: {str(e)}"
            )
        
        # Update category score
        self._update_category_score('monitoring_systems', passed_checks, total_checks)
        logger.info(f"Monitoring systems validation: {passed_checks}/{total_checks} checks passed")
    
    async def _validate_incident_response(self) -> None:
        """Validate incident response capabilities"""
        logger.info("🚨 Validating incident response capabilities...")
        
        total_checks = 0
        passed_checks = 0
        
        # Check for incident response documentation or workflows
        total_checks += 1
        incident_docs = [
            self.project_root / 'SECURITY.md',
            self.project_root / 'INCIDENT_RESPONSE.md',
            self.project_root / '.github' / 'SECURITY.md'
        ]
        
        found_docs = [doc for doc in incident_docs if doc.exists()]
        if found_docs:
            logger.info(f"✅ Security documentation found: {[d.name for d in found_docs]}")
            passed_checks += 1
            self._add_validation_result(
                'incident_response', 'security_documentation', 'pass', 10,
                f"Security documentation found: {', '.join([d.name for d in found_docs])}"
            )
        else:
            logger.warning("⚠️ No security documentation found")
            self._add_validation_result(
                'incident_response', 'security_documentation', 'fail', 0,
                "No security documentation or incident response procedures found"
            )
        
        # Check for security workflow with incident response capabilities
        total_checks += 1
        security_workflow = self.project_root / '.github' / 'workflows' / 'comprehensive-security-integration.yml'
        if security_workflow.exists():
            content = security_workflow.read_text()
            if 'workflow_dispatch' in content:
                logger.info("✅ Manual security workflow trigger available")
                passed_checks += 1
                self._add_validation_result(
                    'incident_response', 'manual_triggers', 'pass', 15,
                    "Manual security workflow triggers available for incident response"
                )
            else:
                logger.warning("⚠️ No manual workflow triggers found")
                self._add_validation_result(
                    'incident_response', 'manual_triggers', 'partial', 5,
                    "Security workflow exists but no manual triggers for incident response"
                )
        else:
            logger.error("❌ Security workflow not found")
            self._add_validation_result(
                'incident_response', 'manual_triggers', 'fail', 0,
                "Security workflow not found - no incident response automation"
            )
        
        # Check for notification configurations
        total_checks += 1
        if security_workflow.exists():
            content = security_workflow.read_text()
            if 'slack' in content.lower() or 'notification' in content.lower() or 'alert' in content.lower():
                logger.info("✅ Notification systems configured in security workflow")
                passed_checks += 1
                self._add_validation_result(
                    'incident_response', 'notifications', 'pass', 10,
                    "Notification systems configured in security workflows"
                )
            else:
                logger.warning("⚠️ No notification systems found in security workflow")
                self._add_validation_result(
                    'incident_response', 'notifications', 'partial', 3,
                    "Security workflow exists but no notification systems configured"
                )
        
        # Update category score
        self._update_category_score('incident_response', passed_checks, total_checks)
        logger.info(f"Incident response validation: {passed_checks}/{total_checks} checks passed")
    
    async def _analyze_dependency_prs(self) -> None:
        """Analyze open dependency PRs for security review"""
        logger.info("📋 Analyzing dependency PRs...")
        
        try:
            # Use GitHub CLI to get PR information
            result = subprocess.run(
                ['gh', 'pr', 'list', '--state=open', '--json', 'number,title,headRefName,createdAt,body'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                prs = json.loads(result.stdout) if result.stdout else []
                
                # Filter dependency PRs
                dependency_prs = [
                    pr for pr in prs 
                    if pr['headRefName'].startswith('dependabot/') or 'bump' in pr['title'].lower()
                ]
                
                self.dependency_prs = dependency_prs
                logger.info(f"✅ Found {len(dependency_prs)} dependency PRs")
                
                # Analyze security-related PRs
                security_prs = [
                    pr for pr in dependency_prs
                    if any(keyword in pr['title'].lower() or keyword in pr.get('body', '').lower() 
                          for keyword in ['security', 'vulnerability', 'cve'])
                ]
                
                if security_prs:
                    logger.warning(f"⚠️ Found {len(security_prs)} security-related dependency PRs requiring attention")
                    self.recommendations.append(
                        f"🔒 Review and merge {len(security_prs)} security-related dependency PRs immediately"
                    )
                
            else:
                logger.warning("⚠️ Unable to fetch PR information (GitHub CLI may not be configured)")
                
        except subprocess.TimeoutExpired:
            logger.warning("⚠️ GitHub CLI request timed out")
        except Exception as e:
            logger.warning(f"⚠️ Error analyzing dependency PRs: {e}")
    
    async def _generate_recommendations(self) -> None:
        """Generate security recommendations based on validation results"""
        logger.info("💡 Generating security recommendations...")
        
        # Calculate category scores
        category_scores = {
            name: category.score 
            for name, category in self.categories.items()
        }
        
        # Generate recommendations based on scores
        if category_scores.get('workflow_validation', 0) < 80:
            self.recommendations.append(
                "🔧 Improve security workflow configuration - ensure comprehensive security scanning workflows are properly set up"
            )
        
        if category_scores.get('security_tools', 0) < 80:
            self.recommendations.append(
                "🛠️ Install and configure security tools - ensure Safety, Bandit, and pip-audit are available"
            )
        
        if category_scores.get('dependency_management', 0) < 80:
            self.recommendations.append(
                "📦 Improve dependency management - pin package versions and configure security scanning"
            )
        
        if category_scores.get('monitoring_systems', 0) < 80:
            self.recommendations.append(
                "📊 Enhance monitoring and reporting systems - ensure security reports and logging are functional"
            )
        
        if category_scores.get('incident_response', 0) < 80:
            self.recommendations.append(
                "🚨 Strengthen incident response capabilities - create security documentation and configure alerts"
            )
        
        # Add dependency PR recommendations
        if len(self.dependency_prs) > 10:
            self.recommendations.append(
                f"📋 Address {len(self.dependency_prs)} open dependency PRs - review and merge security updates"
            )
        
        # General recommendations
        self.recommendations.extend([
            "🔄 Schedule regular security scans - automate weekly dependency vulnerability checks",
            "📚 Security training - ensure team understands security workflows and incident response",
            "🧪 Test security tools - regularly validate that security monitoring and alerting work correctly"
        ])
        
        logger.info(f"Generated {len(self.recommendations)} security recommendations")
    
    async def _generate_final_report(self) -> SecurityIntegrationReport:
        """Generate final security integration report"""
        logger.info("📄 Generating final security integration report...")
        
        # Calculate total score (weighted average)
        weights = {
            'workflow_validation': 25,
            'security_tools': 20,
            'dependency_management': 20,
            'monitoring_systems': 15,
            'incident_response': 20
        }
        
        total_weighted_score = sum(
            self.categories[category].score * weight / 100
            for category, weight in weights.items()
        )
        
        # Determine grade and overall status
        if total_weighted_score >= 90:
            grade = 'A'
            overall_status = 'excellent'
        elif total_weighted_score >= 80:
            grade = 'B'
            overall_status = 'good'
        elif total_weighted_score >= 70:
            grade = 'C'
            overall_status = 'acceptable'
        elif total_weighted_score >= 60:
            grade = 'D'
            overall_status = 'needs_improvement'
        else:
            grade = 'F'
            overall_status = 'critical'
        
        return SecurityIntegrationReport(
            timestamp=self.timestamp,
            repository='agentic-research-engine',
            validation_version='1.0.0',
            overall_status=overall_status,
            categories=self.categories,
            recommendations=self.recommendations,
            dependency_prs=self.dependency_prs,
            total_score=int(total_weighted_score),
            grade=grade
        )
    
    async def _save_results(self, report: SecurityIntegrationReport) -> None:
        """Save validation results to files"""
        logger.info("💾 Saving validation results...")
        
        # Save JSON report
        json_report_path = self.reports_dir / f'security-integration-report-{int(time.time())}.json'
        with open(json_report_path, 'w') as f:
            json.dump(asdict(report), f, indent=2, default=str)
        
        # Generate and save markdown report
        markdown_report = self._generate_markdown_report(report)
        md_report_path = self.project_root / 'security-integration-report.md'
        with open(md_report_path, 'w') as f:
            f.write(markdown_report)
        
        logger.info(f"Reports saved:")
        logger.info(f"  JSON: {json_report_path}")
        logger.info(f"  Markdown: {md_report_path}")
    
    def _generate_markdown_report(self, report: SecurityIntegrationReport) -> str:
        """Generate human-readable markdown report"""
        return f"""# Security Integration Validation Report

**Generated:** {datetime.fromisoformat(report.timestamp).strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Repository:** {report.repository}  
**Validation Version:** {report.validation_version}

## Overall Assessment

- **Total Score:** {report.total_score}/100
- **Grade:** {report.grade}
- **Status:** {report.overall_status}

## Category Breakdown

### Workflow Validation
- **Score:** {report.categories['workflow_validation'].score}/100
- **Status:** {report.categories['workflow_validation'].status}

### Security Tools
- **Score:** {report.categories['security_tools'].score}/100
- **Status:** {report.categories['security_tools'].status}

### Dependency Management
- **Score:** {report.categories['dependency_management'].score}/100
- **Status:** {report.categories['dependency_management'].status}

### Monitoring Systems
- **Score:** {report.categories['monitoring_systems'].score}/100
- **Status:** {report.categories['monitoring_systems'].status}

### Incident Response
- **Score:** {report.categories['incident_response'].score}/100
- **Status:** {report.categories['incident_response'].status}

## Dependency Management

- **Open Dependency PRs:** {len(report.dependency_prs)}
- **Security-related PRs:** {len([pr for pr in report.dependency_prs if any(keyword in pr['title'].lower() for keyword in ['security', 'vulnerability', 'cve'])])}

## Recommendations

{chr(10).join(f'- {rec}' for rec in report.recommendations)}

## Summary

{self._get_status_description(report.overall_status)}

---
*Generated by Security Integration Manager for Agentic Research Engine*
"""
    
    def _get_status_description(self, status: str) -> str:
        """Get description for overall status"""
        descriptions = {
            'excellent': '✅ **Excellent** - Security integration is comprehensive and well-configured.',
            'good': '✅ **Good** - Security integration is solid with minor areas for improvement.',
            'acceptable': '⚠️ **Acceptable** - Security integration meets basic requirements but has room for improvement.',
            'needs_improvement': '🔶 **Needs Improvement** - Security integration has significant gaps that should be addressed.',
            'critical': '🚨 **Critical** - Security integration has major deficiencies requiring immediate attention.'
        }
        return descriptions.get(status, 'Unknown status')
    
    def _add_validation_result(self, category: str, name: str, status: str, score: int, message: str) -> None:
        """Add a validation result to a category"""
        result = ValidationResult(
            name=name,
            status=status,
            score=score,
            message=message,
            timestamp=datetime.now().isoformat()
        )
        
        if category in self.categories:
            self.categories[category].checks.append(result)
    
    def _update_category_score(self, category: str, passed_checks: int, total_checks: int) -> None:
        """Update category score based on passed/total checks"""
        if total_checks > 0:
            score = int((passed_checks / total_checks) * 100)
            
            if score >= 80:
                status = 'pass'
            elif score >= 60:
                status = 'partial'
            else:
                status = 'fail'
            
            self.categories[category].score = score
            self.categories[category].status = status


async def main():
    """Main execution function"""
    manager = SecurityIntegrationManager()
    
    try:
        logger.info("🔍 Starting Security Integration Validation for Agentic Research Engine")
        report = await manager.run_comprehensive_validation()
        
        # Print summary
        print("\n" + "="*60)
        print("SECURITY INTEGRATION VALIDATION SUMMARY")
        print("="*60)
        print(f"Overall Score: {report.total_score}/100")
        print(f"Grade: {report.grade}")
        print(f"Status: {report.overall_status}")
        print(f"Open Dependency PRs: {len(report.dependency_prs)}")
        print(f"Recommendations: {len(report.recommendations)}")
        print("="*60)
        
        # Exit with appropriate code
        if report.total_score >= 80:
            logger.info("✅ Security integration validation PASSED")
            sys.exit(0)
        elif report.total_score >= 60:
            logger.warning("⚠️ Security integration validation PARTIALLY PASSED")
            sys.exit(1)
        else:
            logger.error("❌ Security integration validation FAILED")
            sys.exit(2)
            
    except Exception as error:
        logger.error(f"❌ Security integration validation failed: {error}")
        sys.exit(3)


if __name__ == '__main__':
    asyncio.run(main())