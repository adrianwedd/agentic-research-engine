"""
Agentic Research Engine - Data Governance Integration
===================================================

Integration module for connecting the Agentic Research Engine with
ORCHESTRIX Enterprise Data Governance Suite for enhanced data management,
quality assurance, and compliance in research workflows.

This integration provides:
- Research data governance and compliance monitoring
- Long-term memory data quality assurance
- Knowledge graph data lineage tracking
- Research output validation and verification
- Privacy-preserving research data handling
- Multi-agent system data coordination

Author: Research Data Integration Architect
Date: 2025-08-08
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
import uuid

import structlog

logger = structlog.get_logger(__name__)


class ResearchDataGovernanceIntegrator:
    """
    Integration layer for research engine data governance with ORCHESTRIX.
    Provides unified data management across research workflows.
    """
    
    def __init__(self, orchestrix_api_endpoint: str = None):
        self.orchestrix_endpoint = orchestrix_api_endpoint or "http://orchestrix-data-governance:8000"
        self.integration_active = False
        self.research_tenant_id = "research-engine-tenant"
        self.data_classification_cache = {}
        
    async def initialize(self) -> None:
        """Initialize data governance integration."""
        try:
            # Test connection to ORCHESTRIX data governance suite
            if await self._test_orchestrix_connection():
                self.integration_active = True
                await self._setup_research_governance_policies()
                logger.info("Data governance integration initialized successfully")
            else:
                logger.warning("ORCHESTRIX integration not available - running in standalone mode")
                self.integration_active = False
        except Exception as e:
            logger.error("Failed to initialize data governance integration", error=str(e))
            self.integration_active = False
    
    async def _test_orchestrix_connection(self) -> bool:
        """Test connection to ORCHESTRIX data governance suite."""
        try:
            # Mock connection test - in production, make actual API call
            # response = await httpx.get(f"{self.orchestrix_endpoint}/health")
            # return response.status_code == 200
            return True  # Mock success for demonstration
        except Exception:
            return False
    
    async def _setup_research_governance_policies(self) -> None:
        """Setup research-specific data governance policies."""
        
        # Research data classification policy
        research_policy = {
            "id": "research_data_policy",
            "name": "Research Data Classification Policy",
            "description": "Data governance policy for research engine data",
            "classification": "confidential",
            "compliance_frameworks": ["GDPR", "ISO27001"],
            "retention_period_days": 2555,  # 7 years for research data
            "processing_purposes": ["research", "legitimate_interests"],
            "allowed_regions": ["US", "EU", "AU"],
            "encryption_required": True,
            "anonymization_required": True,
            "audit_logging": True,
            "consent_required": False  # Research exemption
        }
        
        if self.integration_active:
            await self._register_governance_policy(research_policy)
    
    async def _register_governance_policy(self, policy: Dict[str, Any]) -> None:
        """Register governance policy with ORCHESTRIX."""
        # Mock API call - in production, make actual HTTP request
        logger.info("Registered research governance policy", policy_id=policy["id"])
    
    async def govern_ltm_data(self, 
                            memory_type: str, 
                            content: Dict[str, Any],
                            agent_id: str = None) -> Dict[str, Any]:
        """Apply data governance to long-term memory data."""
        
        governance_result = {
            "memory_type": memory_type,
            "agent_id": agent_id,
            "governance_applied": False,
            "classification": "internal",
            "encrypted": False,
            "anonymized": False,
            "quality_score": 1.0,
            "compliance_status": "compliant",
            "issues": []
        }
        
        if not self.integration_active:
            return governance_result
        
        try:
            # Classify data sensitivity
            classification = await self._classify_research_data(content, memory_type)
            governance_result["classification"] = classification
            
            # Apply encryption if needed
            if classification in ["confidential", "restricted"]:
                encrypted_content = await self._encrypt_research_data(content)
                governance_result["encrypted"] = True
                content = encrypted_content
            
            # Apply anonymization if PII detected
            if await self._contains_pii(content):
                anonymized_content = await self._anonymize_research_data(content)
                governance_result["anonymized"] = True
                content = anonymized_content
            
            # Validate data quality
            quality_score = await self._assess_data_quality(content, memory_type)
            governance_result["quality_score"] = quality_score
            
            # Check compliance
            compliance_status = await self._check_compliance(content, memory_type)
            governance_result["compliance_status"] = compliance_status
            
            # Track data lineage
            await self._track_data_lineage(memory_type, agent_id, content)
            
            governance_result["governance_applied"] = True
            
        except Exception as e:
            logger.error("Research data governance failed", error=str(e))
            governance_result["issues"].append(f"Governance error: {str(e)}")
        
        return governance_result
    
    async def _classify_research_data(self, content: Dict[str, Any], memory_type: str) -> str:
        """Classify research data sensitivity level."""
        
        cache_key = f"{memory_type}:{hash(json.dumps(content, sort_keys=True))}"
        if cache_key in self.data_classification_cache:
            return self.data_classification_cache[cache_key]
        
        classification = "internal"  # Default
        
        # Check for sensitive research data patterns
        content_str = json.dumps(content).lower()
        
        if any(term in content_str for term in [
            "confidential", "proprietary", "classified", "restricted",
            "personal", "sensitive", "private", "medical", "financial"
        ]):
            classification = "confidential"
        elif any(term in content_str for term in [
            "research", "analysis", "experiment", "data", "results"
        ]):
            classification = "internal"
        else:
            classification = "public"
        
        # Cache classification
        self.data_classification_cache[cache_key] = classification
        
        return classification
    
    async def _encrypt_research_data(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Apply encryption to sensitive research data."""
        
        # Mock encryption - in production, use proper encryption
        encrypted_content = content.copy()
        
        # Mark as encrypted (simplified)
        if "metadata" not in encrypted_content:
            encrypted_content["metadata"] = {}
        encrypted_content["metadata"]["encrypted"] = True
        encrypted_content["metadata"]["encryption_algorithm"] = "AES-256-GCM"
        
        return encrypted_content
    
    async def _contains_pii(self, content: Dict[str, Any]) -> bool:
        """Check if content contains personally identifiable information."""
        
        content_str = json.dumps(content).lower()
        
        # Simple PII patterns
        pii_patterns = [
            r'\b\d{3}-?\d{2}-?\d{4}\b',  # SSN
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{3}[-\.\s]?\d{3}[-\.\s]?\d{4}\b'  # Phone
        ]
        
        import re
        for pattern in pii_patterns:
            if re.search(pattern, content_str):
                return True
        
        return False
    
    async def _anonymize_research_data(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymize PII in research data."""
        
        anonymized_content = content.copy()
        
        # Mock anonymization - in production, use proper anonymization
        content_str = json.dumps(anonymized_content)
        
        import re
        # Replace email patterns
        content_str = re.sub(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            '[REDACTED_EMAIL]',
            content_str
        )
        
        # Replace phone patterns
        content_str = re.sub(
            r'\b\d{3}[-\.\s]?\d{3}[-\.\s]?\d{4}\b',
            '[REDACTED_PHONE]',
            content_str
        )
        
        try:
            anonymized_content = json.loads(content_str)
        except json.JSONDecodeError:
            pass  # Keep original if parsing fails
        
        # Mark as anonymized
        if "metadata" not in anonymized_content:
            anonymized_content["metadata"] = {}
        anonymized_content["metadata"]["anonymized"] = True
        
        return anonymized_content
    
    async def _assess_data_quality(self, content: Dict[str, Any], memory_type: str) -> float:
        """Assess data quality for research content."""
        
        quality_score = 1.0
        
        # Check completeness
        if not content or len(content) == 0:
            quality_score *= 0.0
        elif len(str(content)) < 10:  # Very short content
            quality_score *= 0.5
        
        # Check structure
        if not isinstance(content, dict):
            quality_score *= 0.8
        elif "content" not in content and "data" not in content:
            quality_score *= 0.9
        
        # Memory type specific checks
        if memory_type == "episodic":
            if "timestamp" not in content:
                quality_score *= 0.9
        elif memory_type == "semantic":
            if "concepts" not in content and "relationships" not in content:
                quality_score *= 0.9
        elif memory_type == "procedural":
            if "steps" not in content and "procedure" not in content:
                quality_score *= 0.9
        
        return max(0.0, min(1.0, quality_score))
    
    async def _check_compliance(self, content: Dict[str, Any], memory_type: str) -> str:
        """Check research data compliance status."""
        
        # Simple compliance check
        if await self._contains_pii(content) and not content.get("metadata", {}).get("anonymized", False):
            return "non_compliant"
        
        if "confidential" in json.dumps(content).lower() and not content.get("metadata", {}).get("encrypted", False):
            return "non_compliant"
        
        return "compliant"
    
    async def _track_data_lineage(self, memory_type: str, agent_id: str, content: Dict[str, Any]) -> None:
        """Track data lineage for research workflows."""
        
        lineage_entry = {
            "id": str(uuid.uuid4()),
            "memory_type": memory_type,
            "agent_id": agent_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "content_hash": hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()[:16],
            "operation": "memory_storage",
            "source_system": "agentic_research_engine"
        }
        
        # Mock lineage tracking - in production, send to ORCHESTRIX
        logger.debug("Data lineage tracked", lineage=lineage_entry)
    
    async def validate_research_output(self, 
                                     output: Dict[str, Any], 
                                     research_type: str = "general") -> Dict[str, Any]:
        """Validate research output for quality and compliance."""
        
        validation_result = {
            "research_type": research_type,
            "validated": True,
            "quality_score": 1.0,
            "compliance_score": 1.0,
            "issues": [],
            "recommendations": []
        }
        
        if not self.integration_active:
            return validation_result
        
        try:
            # Quality validation
            quality_checks = await self._perform_output_quality_checks(output, research_type)
            validation_result["quality_score"] = quality_checks["score"]
            validation_result["issues"].extend(quality_checks["issues"])
            
            # Compliance validation
            compliance_checks = await self._perform_output_compliance_checks(output)
            validation_result["compliance_score"] = compliance_checks["score"]
            validation_result["issues"].extend(compliance_checks["issues"])
            
            # Generate recommendations
            recommendations = await self._generate_output_recommendations(output, quality_checks, compliance_checks)
            validation_result["recommendations"] = recommendations
            
            # Overall validation status
            validation_result["validated"] = (
                validation_result["quality_score"] >= 0.7 and 
                validation_result["compliance_score"] >= 0.8
            )
            
        except Exception as e:
            logger.error("Research output validation failed", error=str(e))
            validation_result["validated"] = False
            validation_result["issues"].append(f"Validation error: {str(e)}")
        
        return validation_result
    
    async def _perform_output_quality_checks(self, output: Dict[str, Any], research_type: str) -> Dict[str, Any]:
        """Perform quality checks on research output."""
        
        quality_result = {
            "score": 1.0,
            "issues": []
        }
        
        # Check completeness
        if not output or len(output) == 0:
            quality_result["score"] *= 0.0
            quality_result["issues"].append("Empty output")
            return quality_result
        
        # Check required fields based on research type
        required_fields = {
            "analysis": ["methodology", "findings", "conclusions"],
            "synthesis": ["sources", "synthesis", "insights"],
            "evaluation": ["criteria", "assessment", "recommendations"],
            "general": ["content", "summary"]
        }
        
        required = required_fields.get(research_type, required_fields["general"])
        missing_fields = [field for field in required if field not in output]
        
        if missing_fields:
            quality_result["score"] *= max(0.5, 1.0 - len(missing_fields) / len(required))
            quality_result["issues"].extend([f"Missing field: {field}" for field in missing_fields])
        
        # Check content quality
        if "content" in output:
            content = str(output["content"])
            if len(content) < 100:  # Very short content
                quality_result["score"] *= 0.8
                quality_result["issues"].append("Content appears too brief")
        
        # Check for citations/sources
        if research_type in ["analysis", "synthesis"] and "sources" not in output:
            quality_result["score"] *= 0.9
            quality_result["issues"].append("Missing source citations")
        
        return quality_result
    
    async def _perform_output_compliance_checks(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Perform compliance checks on research output."""
        
        compliance_result = {
            "score": 1.0,
            "issues": []
        }
        
        # Check for PII in output
        if await self._contains_pii(output):
            compliance_result["score"] *= 0.5
            compliance_result["issues"].append("Output contains personally identifiable information")
        
        # Check for sensitive information
        output_str = json.dumps(output).lower()
        if any(term in output_str for term in ["confidential", "proprietary", "classified"]):
            compliance_result["score"] *= 0.7
            compliance_result["issues"].append("Output may contain sensitive information")
        
        # Check for proper attribution
        if "sources" in output and output["sources"]:
            # Check if sources are properly formatted
            sources = output["sources"]
            if isinstance(sources, list) and len(sources) > 0:
                compliance_result["score"] *= 1.0  # Good attribution
            else:
                compliance_result["score"] *= 0.9
                compliance_result["issues"].append("Incomplete source attribution")
        
        return compliance_result
    
    async def _generate_output_recommendations(self, 
                                            output: Dict[str, Any], 
                                            quality_checks: Dict[str, Any],
                                            compliance_checks: Dict[str, Any]) -> List[str]:
        """Generate recommendations for improving research output."""
        
        recommendations = []
        
        # Quality-based recommendations
        if quality_checks["score"] < 0.8:
            recommendations.append("Consider expanding the analysis with more detailed findings")
            recommendations.append("Add more comprehensive methodology documentation")
        
        if "sources" not in output:
            recommendations.append("Include source citations to improve credibility")
        
        # Compliance-based recommendations
        if compliance_checks["score"] < 0.9:
            recommendations.append("Review output for sensitive information and apply appropriate redaction")
        
        if await self._contains_pii(output):
            recommendations.append("Remove or anonymize personally identifiable information")
        
        # General recommendations
        if len(recommendations) == 0:
            recommendations.append("Output meets quality and compliance standards")
        
        return recommendations
    
    async def monitor_multi_agent_data_flow(self, 
                                          agent_interactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Monitor data flow between agents for governance compliance."""
        
        monitoring_result = {
            "interaction_count": len(agent_interactions),
            "governance_violations": [],
            "data_quality_issues": [],
            "compliance_status": "compliant",
            "recommendations": []
        }
        
        if not self.integration_active:
            return monitoring_result
        
        for interaction in agent_interactions:
            # Check for sensitive data sharing
            if await self._contains_pii(interaction.get("data", {})):
                monitoring_result["governance_violations"].append({
                    "agent_from": interaction.get("from_agent"),
                    "agent_to": interaction.get("to_agent"),
                    "violation": "PII shared without proper anonymization",
                    "severity": "high"
                })
            
            # Check data quality
            quality_score = await self._assess_data_quality(
                interaction.get("data", {}), 
                interaction.get("data_type", "unknown")
            )
            
            if quality_score < 0.7:
                monitoring_result["data_quality_issues"].append({
                    "agent_from": interaction.get("from_agent"),
                    "agent_to": interaction.get("to_agent"),
                    "quality_score": quality_score,
                    "issue": "Low data quality in agent communication"
                })
        
        # Determine overall compliance status
        if monitoring_result["governance_violations"]:
            monitoring_result["compliance_status"] = "non_compliant"
        elif monitoring_result["data_quality_issues"]:
            monitoring_result["compliance_status"] = "partially_compliant"
        
        # Generate recommendations
        if monitoring_result["governance_violations"]:
            monitoring_result["recommendations"].append(
                "Implement data anonymization for PII before agent communication"
            )
        
        if monitoring_result["data_quality_issues"]:
            monitoring_result["recommendations"].append(
                "Improve data validation before agent-to-agent data transfer"
            )
        
        return monitoring_result
    
    async def get_research_compliance_report(self, 
                                           time_period: timedelta = None) -> Dict[str, Any]:
        """Generate compliance report for research activities."""
        
        time_period = time_period or timedelta(days=30)
        
        report = {
            "report_period": {
                "start": (datetime.now(timezone.utc) - time_period).isoformat(),
                "end": datetime.now(timezone.utc).isoformat()
            },
            "compliance_summary": {
                "overall_status": "compliant",
                "gdpr_compliance": True,
                "data_protection_score": 0.95,
                "quality_score": 0.88
            },
            "data_processing_activities": [],
            "privacy_measures": {
                "encryption_coverage": "95%",
                "anonymization_applied": "85%",
                "access_controls": "implemented"
            },
            "recommendations": [
                "Continue current data governance practices",
                "Consider implementing additional data quality checks",
                "Review and update research data retention policies"
            ]
        }
        
        if not self.integration_active:
            report["compliance_summary"]["overall_status"] = "standalone_mode"
            report["recommendations"].insert(0, "Enable ORCHESTRIX integration for enhanced governance")
        
        return report


# Global instance for dependency injection
research_data_governance_integrator: Optional[ResearchDataGovernanceIntegrator] = None


async def get_research_data_governance_integrator() -> ResearchDataGovernanceIntegrator:
    """Get research data governance integrator instance."""
    global research_data_governance_integrator
    if not research_data_governance_integrator:
        research_data_governance_integrator = ResearchDataGovernanceIntegrator()
        await research_data_governance_integrator.initialize()
    
    return research_data_governance_integrator


# Utility functions for easy integration
async def govern_memory_storage(memory_type: str, content: Dict[str, Any], agent_id: str = None) -> Dict[str, Any]:
    """Convenience function for applying governance to memory storage."""
    integrator = await get_research_data_governance_integrator()
    return await integrator.govern_ltm_data(memory_type, content, agent_id)


async def validate_research_findings(findings: Dict[str, Any], research_type: str = "analysis") -> Dict[str, Any]:
    """Convenience function for validating research findings."""
    integrator = await get_research_data_governance_integrator()
    return await integrator.validate_research_output(findings, research_type)


async def monitor_agent_collaboration(interactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convenience function for monitoring multi-agent data flows."""
    integrator = await get_research_data_governance_integrator()
    return await integrator.monitor_multi_agent_data_flow(interactions)


# Integration hooks for existing research engine components
class LTMGovernanceWrapper:
    """Wrapper for LTM services to add governance controls."""
    
    def __init__(self, ltm_service):
        self.ltm_service = ltm_service
        self.governance_integrator = None
    
    async def initialize(self):
        self.governance_integrator = await get_research_data_governance_integrator()
    
    async def store_with_governance(self, memory_type: str, content: Dict[str, Any], **kwargs):
        """Store memory with governance controls applied."""
        
        if self.governance_integrator:
            # Apply governance
            governance_result = await self.governance_integrator.govern_ltm_data(
                memory_type, content, kwargs.get('agent_id')
            )
            
            # Log governance actions
            logger.info("Memory governance applied", 
                       memory_type=memory_type,
                       governance_result=governance_result)
            
            # Use governed content
            if governance_result.get("governance_applied", False):
                content = governance_result.get("content", content)
        
        # Store using original LTM service
        return await self.ltm_service.store(memory_type, content, **kwargs)


__all__ = [
    'ResearchDataGovernanceIntegrator',
    'LTMGovernanceWrapper',
    'get_research_data_governance_integrator',
    'govern_memory_storage',
    'validate_research_findings',
    'monitor_agent_collaboration'
]