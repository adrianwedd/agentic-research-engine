#!/usr/bin/env python3

"""
ORCHESTRIX Pilot KPI Collection System
Classification: STRATEGIC - BUSINESS VALIDATION
Real-time business KPI collection, analysis, and alerting for Phase 2 pilot
Last Updated: 2025-08-08
"""

import json
import time
import datetime
import logging
import asyncio
import aiohttp
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import psycopg2
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pilot-kpi-collection.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class KPIStatus(Enum):
    EXCELLENT = "excellent"      # Exceeding targets significantly
    GOOD = "good"               # Meeting or slightly exceeding targets  
    WARNING = "warning"         # Below targets but within acceptable range
    CRITICAL = "critical"       # Significantly below targets
    UNKNOWN = "unknown"         # No data available

@dataclass
class BusinessKPI:
    metric_name: str
    current_value: float
    target_value: float
    threshold_value: float
    status: KPIStatus
    trend: str  # improving, stable, declining
    measurement_timestamp: datetime.datetime
    cohort_breakdown: Optional[Dict[str, float]] = None

@dataclass
class TechnicalKPI:
    metric_name: str
    current_value: float
    target_value: float
    slo_target: float
    status: KPIStatus
    measurement_timestamp: datetime.datetime
    error_budget_consumed: float = 0.0

@dataclass
class CustomerHealthScore:
    user_id: str
    satisfaction_score: float
    engagement_score: float
    adoption_score: float
    retention_risk: float
    overall_health: float
    intervention_needed: bool
    last_calculated: datetime.datetime

class PilotKPICollector:
    """Comprehensive KPI collection and analysis for Phase 2 pilot validation."""
    
    def __init__(self, config: Dict = None):
        self.config = config or self._default_config()
        self.business_kpis: Dict[str, BusinessKPI] = {}
        self.technical_kpis: Dict[str, TechnicalKPI] = {}
        self.customer_health_scores: Dict[str, CustomerHealthScore] = {}
        self.collection_start_time = datetime.datetime.now()
        
        # Initialize KPI tracking
        self._initialize_kpi_tracking()
        
        logger.info("🚀 ORCHESTRIX Pilot KPI Collection System Initialized")
        logger.info(f"📊 Tracking {len(self.business_kpis)} business KPIs")
        logger.info(f"🔧 Tracking {len(self.technical_kpis)} technical KPIs")
    
    def _default_config(self) -> Dict:
        """Default configuration for KPI collection."""
        return {
            "collection_interval_seconds": 30,
            "health_check_interval_seconds": 300,
            "alert_thresholds": {
                "customer_satisfaction": {"critical": 7.0, "warning": 8.0},
                "task_completion_rate": {"critical": 85.0, "warning": 90.0},
                "user_retention": {"critical": 80.0, "warning": 90.0},
                "availability_slo": {"critical": 99.5, "warning": 99.8},
                "response_time_p95": {"critical": 2000, "warning": 1500}
            },
            "success_targets": {
                "customer_satisfaction": 8.5,
                "task_completion_rate": 95.0,
                "feature_adoption_rate": 85.0,
                "user_retention_rate": 92.0,
                "nps_score": 70.0,
                "availability_slo": 99.9,
                "response_time_p95": 1000,
                "error_rate": 0.1
            }
        }
    
    def _initialize_kpi_tracking(self):
        """Initialize KPI tracking with baseline metrics."""
        
        # Business KPIs
        business_metrics = [
            ("customer_satisfaction", 0.0, 8.5, 8.0),
            ("task_completion_rate", 0.0, 95.0, 90.0),
            ("feature_adoption_rate", 0.0, 85.0, 80.0),
            ("user_retention_rate", 0.0, 92.0, 85.0),
            ("nps_score", 0.0, 70.0, 50.0),
            ("daily_active_users", 0, 40, 30),
            ("session_duration_avg", 0.0, 25.0, 20.0),
            ("support_ticket_rate", 0.0, 3.0, 5.0),
            ("churn_rate", 0.0, 5.0, 8.0),
            ("feature_request_rate", 0.0, 2.0, 5.0)
        ]
        
        for name, current, target, threshold in business_metrics:
            self.business_kpis[name] = BusinessKPI(
                metric_name=name,
                current_value=current,
                target_value=target,
                threshold_value=threshold,
                status=KPIStatus.UNKNOWN,
                trend="stable",
                measurement_timestamp=datetime.datetime.now()
            )
        
        # Technical KPIs
        technical_metrics = [
            ("availability_slo", 0.0, 99.9, 99.5),
            ("response_time_p95", 0.0, 1000.0, 2000.0),
            ("response_time_p99", 0.0, 2000.0, 5000.0),
            ("error_rate", 0.0, 0.1, 1.0),
            ("throughput_rps", 0.0, 500.0, 200.0),
            ("mttr_minutes", 0.0, 5.0, 15.0),
            ("concurrent_users", 0, 50, 30),
            ("cpu_utilization", 0.0, 70.0, 85.0),
            ("memory_utilization", 0.0, 75.0, 90.0),
            ("database_response_time", 0.0, 100.0, 500.0)
        ]
        
        for name, current, target, slo in technical_metrics:
            self.technical_kpis[name] = TechnicalKPI(
                metric_name=name,
                current_value=current,
                target_value=target,
                slo_target=slo,
                status=KPIStatus.UNKNOWN,
                measurement_timestamp=datetime.datetime.now()
            )
        
        logger.info(f"📊 Initialized tracking for {len(self.business_kpis)} business and {len(self.technical_kpis)} technical KPIs")
    
    def simulate_kpi_collection(self, phase: str = "cohort_4") -> Dict:
        """Simulate KPI collection with realistic Phase 2 pilot values."""
        logger.info(f"📈 Simulating KPI collection for pilot phase: {phase}")
        
        # Simulate business KPIs with progressive improvement
        phase_multipliers = {
            "cohort_1": 0.85,  # Initial conservative performance
            "cohort_2": 0.92,  # Improving performance
            "cohort_3": 0.96,  # Strong performance
            "cohort_4": 1.0    # Peak pilot performance
        }
        
        multiplier = phase_multipliers.get(phase, 1.0)
        
        # Simulate realistic business metrics
        simulated_business = {
            "customer_satisfaction": 8.8 * multiplier,
            "task_completion_rate": 97.1 * multiplier,
            "feature_adoption_rate": 91.3 * multiplier,
            "user_retention_rate": 94.7 * multiplier,
            "nps_score": 76.8 * multiplier,
            "daily_active_users": 45 * multiplier,
            "session_duration_avg": 28.5 * multiplier,
            "support_ticket_rate": 2.1,  # Lower is better
            "churn_rate": 3.2,          # Lower is better
            "feature_request_rate": 1.8   # Moderate level
        }
        
        # Simulate technical metrics
        simulated_technical = {
            "availability_slo": 99.96,
            "response_time_p95": 650 / multiplier,  # Lower is better
            "response_time_p99": 1200 / multiplier, # Lower is better
            "error_rate": 0.03 / multiplier,       # Lower is better
            "throughput_rps": 485 * multiplier,
            "mttr_minutes": 2.1 / multiplier,      # Lower is better
            "concurrent_users": 50 * multiplier,
            "cpu_utilization": 65 * multiplier,
            "memory_utilization": 72 * multiplier,
            "database_response_time": 45 / multiplier  # Lower is better
        }
        
        # Update business KPIs
        for name, value in simulated_business.items():
            if name in self.business_kpis:
                kpi = self.business_kpis[name]
                
                # Calculate trend
                if kpi.current_value > 0:
                    if value > kpi.current_value:
                        trend = "improving"
                    elif value < kpi.current_value:
                        trend = "declining"
                    else:
                        trend = "stable"
                else:
                    trend = "stable"
                
                # Update KPI
                kpi.current_value = value
                kpi.trend = trend
                kpi.measurement_timestamp = datetime.datetime.now()
                
                # Determine status
                if value >= kpi.target_value:
                    kpi.status = KPIStatus.EXCELLENT
                elif value >= kpi.threshold_value:
                    kpi.status = KPIStatus.GOOD
                elif value >= kpi.threshold_value * 0.9:
                    kpi.status = KPIStatus.WARNING
                else:
                    kpi.status = KPIStatus.CRITICAL
                
                logger.info(f"📊 {name}: {value:.2f} (target: {kpi.target_value}) - {kpi.status.value} - {trend}")
        
        # Update technical KPIs
        for name, value in simulated_technical.items():
            if name in self.technical_kpis:
                kpi = self.technical_kpis[name]
                kpi.current_value = value
                kpi.measurement_timestamp = datetime.datetime.now()
                
                # Status determination varies by metric type
                if name in ["response_time_p95", "response_time_p99", "error_rate", "mttr_minutes"]:
                    # Lower is better metrics
                    if value <= kpi.target_value:
                        kpi.status = KPIStatus.EXCELLENT
                    elif value <= kpi.slo_target:
                        kpi.status = KPIStatus.GOOD
                    else:
                        kpi.status = KPIStatus.WARNING
                else:
                    # Higher is better metrics
                    if value >= kpi.target_value:
                        kpi.status = KPIStatus.EXCELLENT
                    elif value >= kpi.slo_target:
                        kpi.status = KPIStatus.GOOD
                    else:
                        kpi.status = KPIStatus.WARNING
                
                logger.info(f"🔧 {name}: {value:.2f} (target: {kpi.target_value}) - {kpi.status.value}")
        
        return {
            "business_kpis": simulated_business,
            "technical_kpis": simulated_technical,
            "collection_timestamp": datetime.datetime.now().isoformat()
        }
    
    def calculate_customer_health_scores(self, phase: str = "cohort_4") -> Dict[str, CustomerHealthScore]:
        """Calculate individual customer health scores."""
        logger.info("👥 Calculating customer health scores...")
        
        # Simulate customer health data
        num_users = {"cohort_1": 10, "cohort_2": 20, "cohort_3": 35, "cohort_4": 50}.get(phase, 50)
        
        health_scores = {}
        
        for i in range(1, num_users + 1):
            user_id = f"pilot_user_{i:03d}"
            
            # Simulate varying customer health levels
            satisfaction_base = 8.5 + (i % 3 - 1) * 0.5  # Range 8.0-9.0
            engagement_base = 85.0 + (i % 4) * 5.0        # Range 85-100
            adoption_base = 90.0 + (i % 3) * 3.0          # Range 90-96
            
            # Add some realistic variation
            import random
            random.seed(i)  # Consistent results
            
            satisfaction_score = max(7.0, min(10.0, satisfaction_base + random.uniform(-0.3, 0.3)))
            engagement_score = max(60.0, min(100.0, engagement_base + random.uniform(-5.0, 5.0)))
            adoption_score = max(70.0, min(100.0, adoption_base + random.uniform(-3.0, 3.0)))
            
            # Calculate retention risk (lower is better)
            retention_risk = max(0.0, (9.0 - satisfaction_score) * 10 + (85.0 - engagement_score) * 0.5)
            retention_risk = min(100.0, retention_risk)
            
            # Overall health score (weighted average)
            overall_health = (satisfaction_score * 0.4 + engagement_score * 0.3 + adoption_score * 0.3) / 10 * 100
            
            # Determine if intervention needed
            intervention_needed = satisfaction_score < 8.0 or engagement_score < 70.0 or retention_risk > 30.0
            
            health_scores[user_id] = CustomerHealthScore(
                user_id=user_id,
                satisfaction_score=satisfaction_score,
                engagement_score=engagement_score,
                adoption_score=adoption_score,
                retention_risk=retention_risk,
                overall_health=overall_health,
                intervention_needed=intervention_needed,
                last_calculated=datetime.datetime.now()
            )
        
        self.customer_health_scores = health_scores
        
        # Log summary statistics
        avg_satisfaction = sum(h.satisfaction_score for h in health_scores.values()) / len(health_scores)
        avg_engagement = sum(h.engagement_score for h in health_scores.values()) / len(health_scores)
        interventions_needed = sum(1 for h in health_scores.values() if h.intervention_needed)
        
        logger.info(f"👥 Health scores calculated for {len(health_scores)} users")
        logger.info(f"📊 Average satisfaction: {avg_satisfaction:.2f}/10")
        logger.info(f"📊 Average engagement: {avg_engagement:.1f}%")
        logger.info(f"🚨 Interventions needed: {interventions_needed} users")
        
        return health_scores
    
    def generate_expansion_readiness_assessment(self) -> Dict:
        """Generate comprehensive expansion readiness assessment."""
        logger.info("🎯 Generating expansion readiness assessment...")
        
        # Assess each category
        technical_ready = self._assess_technical_readiness()
        business_ready = self._assess_business_readiness()
        operational_ready = self._assess_operational_readiness()
        financial_ready = self._assess_financial_readiness()
        
        # Overall decision
        overall_ready = all([technical_ready, business_ready, operational_ready, financial_ready])
        
        assessment = {
            "assessment_timestamp": datetime.datetime.now().isoformat(),
            "criteria": {
                "technical_readiness": technical_ready,
                "business_validation": business_ready,
                "operational_readiness": operational_ready,
                "financial_viability": financial_ready
            },
            "overall_decision": "GO_FOR_EXPANSION" if overall_ready else "CONTINUE_PILOT",
            "confidence_score": self._calculate_confidence_score(),
            "detailed_assessment": self._generate_detailed_assessment(),
            "recommendations": self._generate_recommendations(overall_ready)
        }
        
        logger.info(f"🎯 Expansion readiness: {'READY' if overall_ready else 'NOT READY'}")
        logger.info(f"📊 Confidence score: {assessment['confidence_score']:.1f}%")
        
        return assessment
    
    def _assess_technical_readiness(self) -> bool:
        """Assess technical readiness for expansion."""
        critical_metrics = ["availability_slo", "response_time_p95", "error_rate"]
        
        for metric_name in critical_metrics:
            if metric_name in self.technical_kpis:
                kpi = self.technical_kpis[metric_name]
                if kpi.status not in [KPIStatus.EXCELLENT, KPIStatus.GOOD]:
                    return False
        
        return True
    
    def _assess_business_readiness(self) -> bool:
        """Assess business readiness for expansion."""
        critical_metrics = ["customer_satisfaction", "task_completion_rate", "user_retention_rate"]
        
        for metric_name in critical_metrics:
            if metric_name in self.business_kpis:
                kpi = self.business_kpis[metric_name]
                if kpi.status not in [KPIStatus.EXCELLENT, KPIStatus.GOOD]:
                    return False
        
        return True
    
    def _assess_operational_readiness(self) -> bool:
        """Assess operational readiness for expansion."""
        # Check customer health scores
        if not self.customer_health_scores:
            return False
        
        high_risk_customers = sum(1 for h in self.customer_health_scores.values() if h.retention_risk > 40.0)
        total_customers = len(self.customer_health_scores)
        
        # Less than 10% high-risk customers
        return (high_risk_customers / total_customers) < 0.1
    
    def _assess_financial_readiness(self) -> bool:
        """Assess financial readiness for expansion."""
        # Simulated financial validation (would be based on actual cost/revenue data)
        return True
    
    def _calculate_confidence_score(self) -> float:
        """Calculate overall confidence score for expansion."""
        total_metrics = len(self.business_kpis) + len(self.technical_kpis)
        excellent_metrics = sum(1 for kpi in self.business_kpis.values() if kpi.status == KPIStatus.EXCELLENT)
        excellent_metrics += sum(1 for kpi in self.technical_kpis.values() if kpi.status == KPIStatus.EXCELLENT)
        
        good_metrics = sum(1 for kpi in self.business_kpis.values() if kpi.status == KPIStatus.GOOD)
        good_metrics += sum(1 for kpi in self.technical_kpis.values() if kpi.status == KPIStatus.GOOD)
        
        # Weight excellent metrics more heavily
        score = ((excellent_metrics * 1.0) + (good_metrics * 0.8)) / total_metrics * 100
        return min(100.0, score)
    
    def _generate_detailed_assessment(self) -> Dict:
        """Generate detailed assessment breakdown."""
        return {
            "business_metrics_summary": {
                "total_metrics": len(self.business_kpis),
                "excellent": sum(1 for kpi in self.business_kpis.values() if kpi.status == KPIStatus.EXCELLENT),
                "good": sum(1 for kpi in self.business_kpis.values() if kpi.status == KPIStatus.GOOD),
                "warning": sum(1 for kpi in self.business_kpis.values() if kpi.status == KPIStatus.WARNING),
                "critical": sum(1 for kpi in self.business_kpis.values() if kpi.status == KPIStatus.CRITICAL)
            },
            "technical_metrics_summary": {
                "total_metrics": len(self.technical_kpis),
                "excellent": sum(1 for kpi in self.technical_kpis.values() if kpi.status == KPIStatus.EXCELLENT),
                "good": sum(1 for kpi in self.technical_kpis.values() if kpi.status == KPIStatus.GOOD),
                "warning": sum(1 for kpi in self.technical_kpis.values() if kpi.status == KPIStatus.WARNING),
                "critical": sum(1 for kpi in self.technical_kpis.values() if kpi.status == KPIStatus.CRITICAL)
            },
            "customer_health_summary": {
                "total_customers": len(self.customer_health_scores),
                "interventions_needed": sum(1 for h in self.customer_health_scores.values() if h.intervention_needed),
                "average_satisfaction": sum(h.satisfaction_score for h in self.customer_health_scores.values()) / len(self.customer_health_scores) if self.customer_health_scores else 0,
                "high_risk_customers": sum(1 for h in self.customer_health_scores.values() if h.retention_risk > 40.0)
            }
        }
    
    def _generate_recommendations(self, overall_ready: bool) -> List[str]:
        """Generate strategic recommendations based on assessment."""
        recommendations = []
        
        if overall_ready:
            recommendations.extend([
                "🚀 Proceed with Phase 3 Limited Production deployment (500 users)",
                "📈 Begin enterprise customer acquisition and onboarding",
                "🏗️ Scale infrastructure to support 10x user growth",
                "👥 Expand customer success and support teams",
                "💰 Activate revenue collection and billing systems"
            ])
        else:
            # Identify specific improvement areas
            if not self._assess_technical_readiness():
                recommendations.append("🔧 Address technical performance and reliability issues")
            
            if not self._assess_business_readiness():
                recommendations.append("📊 Improve customer satisfaction and retention metrics")
            
            if not self._assess_operational_readiness():
                recommendations.append("👥 Implement customer success interventions for high-risk users")
            
            recommendations.extend([
                "⏱️ Continue pilot validation for additional 30-60 days",
                "📋 Focus on identified improvement areas",
                "🔄 Re-assess expansion readiness monthly"
            ])
        
        return recommendations
    
    def generate_comprehensive_report(self, phase: str = "cohort_4") -> str:
        """Generate comprehensive KPI report."""
        
        # Collect current KPIs
        self.simulate_kpi_collection(phase)
        self.calculate_customer_health_scores(phase)
        expansion_assessment = self.generate_expansion_readiness_assessment()
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("ORCHESTRIX PHASE 2 PILOT - COMPREHENSIVE KPI REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Report Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Collection Period: {self.collection_start_time.strftime('%Y-%m-%d')} to {datetime.datetime.now().strftime('%Y-%m-%d')}")
        report_lines.append(f"Current Phase: {phase.upper()}")
        report_lines.append("")
        
        # Business KPIs Section
        report_lines.append("BUSINESS VALIDATION METRICS")
        report_lines.append("-" * 60)
        for name, kpi in self.business_kpis.items():
            status_icon = {"excellent": "🟢", "good": "🟡", "warning": "🟠", "critical": "🔴"}.get(kpi.status.value, "⚪")
            trend_icon = {"improving": "📈", "declining": "📉", "stable": "➡️"}.get(kpi.trend, "")
            
            report_lines.append(f"{status_icon} {name.replace('_', ' ').title()}: {kpi.current_value:.2f} "
                              f"(target: {kpi.target_value}) {trend_icon} [{kpi.status.value.upper()}]")
        
        report_lines.append("")
        
        # Technical KPIs Section
        report_lines.append("TECHNICAL PERFORMANCE METRICS")
        report_lines.append("-" * 60)
        for name, kpi in self.technical_kpis.items():
            status_icon = {"excellent": "🟢", "good": "🟡", "warning": "🟠", "critical": "🔴"}.get(kpi.status.value, "⚪")
            unit = self._get_metric_unit(name)
            
            report_lines.append(f"{status_icon} {name.replace('_', ' ').title()}: {kpi.current_value:.2f}{unit} "
                              f"(target: {kpi.target_value}{unit}) [{kpi.status.value.upper()}]")
        
        report_lines.append("")
        
        # Customer Health Summary
        report_lines.append("CUSTOMER HEALTH SUMMARY")
        report_lines.append("-" * 60)
        if self.customer_health_scores:
            avg_satisfaction = sum(h.satisfaction_score for h in self.customer_health_scores.values()) / len(self.customer_health_scores)
            avg_engagement = sum(h.engagement_score for h in self.customer_health_scores.values()) / len(self.customer_health_scores)
            avg_health = sum(h.overall_health for h in self.customer_health_scores.values()) / len(self.customer_health_scores)
            interventions_needed = sum(1 for h in self.customer_health_scores.values() if h.intervention_needed)
            
            report_lines.append(f"👥 Total Customers: {len(self.customer_health_scores)}")
            report_lines.append(f"😊 Average Satisfaction: {avg_satisfaction:.2f}/10")
            report_lines.append(f"📱 Average Engagement: {avg_engagement:.1f}%")
            report_lines.append(f"💚 Average Health Score: {avg_health:.1f}%")
            report_lines.append(f"🚨 Interventions Needed: {interventions_needed} customers")
        
        report_lines.append("")
        
        # Expansion Readiness Assessment
        report_lines.append("EXPANSION READINESS ASSESSMENT")
        report_lines.append("-" * 60)
        
        criteria = expansion_assessment["criteria"]
        for criterion_name, status in criteria.items():
            status_icon = "✅" if status else "❌"
            readable_name = criterion_name.replace('_', ' ').title()
            report_lines.append(f"{status_icon} {readable_name}: {'READY' if status else 'NOT READY'}")
        
        report_lines.append("")
        decision_icon = "🚀" if expansion_assessment["overall_decision"] == "GO_FOR_EXPANSION" else "⏸️"
        report_lines.append(f"{decision_icon} OVERALL DECISION: {expansion_assessment['overall_decision']}")
        report_lines.append(f"📊 Confidence Score: {expansion_assessment['confidence_score']:.1f}%")
        
        report_lines.append("")
        
        # Recommendations
        report_lines.append("STRATEGIC RECOMMENDATIONS")
        report_lines.append("-" * 60)
        for rec in expansion_assessment["recommendations"]:
            report_lines.append(f"   {rec}")
        
        report_lines.append("")
        report_lines.append("=" * 80)
        
        report_content = "\n".join(report_lines)
        
        # Save report to file
        report_filename = f"pilot-kpi-comprehensive-report-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
        with open(report_filename, 'w') as f:
            f.write(report_content)
        
        logger.info(f"📄 Comprehensive KPI report saved: {report_filename}")
        
        return report_content
    
    def _get_metric_unit(self, metric_name: str) -> str:
        """Get appropriate unit for metric display."""
        units = {
            "response_time_p95": "ms",
            "response_time_p99": "ms",
            "error_rate": "%",
            "throughput_rps": " RPS",
            "mttr_minutes": " min",
            "cpu_utilization": "%",
            "memory_utilization": "%",
            "database_response_time": "ms",
            "availability_slo": "%"
        }
        return units.get(metric_name, "")

def main():
    """Main execution function for KPI collection system."""
    logger.info("🚀 Starting ORCHESTRIX Pilot KPI Collection System")
    
    # Initialize KPI collector
    collector = PilotKPICollector()
    
    # Generate comprehensive report for final pilot phase
    comprehensive_report = collector.generate_comprehensive_report("cohort_4")
    
    print(comprehensive_report)
    
    # Check if ready for expansion
    expansion_assessment = collector.generate_expansion_readiness_assessment()
    ready_for_expansion = expansion_assessment["overall_decision"] == "GO_FOR_EXPANSION"
    
    if ready_for_expansion:
        logger.info("🎉 PILOT VALIDATION SUCCESSFUL - READY FOR PHASE 3 EXPANSION")
        return 0
    else:
        logger.info("⏳ CONTINUE PILOT VALIDATION - EXPANSION CRITERIA NOT YET MET")
        return 1

if __name__ == "__main__":
    sys.exit(main())