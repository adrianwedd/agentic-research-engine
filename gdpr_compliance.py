#!/usr/bin/env python3
"""
GDPR Compliance Framework for Agentic Research Engine
Comprehensive data protection and privacy controls
"""

import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import secrets
from pathlib import Path

logger = logging.getLogger(__name__)

class LawfulBasis(Enum):
    """GDPR Article 6 - Lawful basis for processing"""
    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTERESTS = "vital_interests"
    PUBLIC_TASK = "public_task"
    LEGITIMATE_INTERESTS = "legitimate_interests"

class DataCategory(Enum):
    """Categories of personal data"""
    BASIC_IDENTITY = "basic_identity"
    CONTACT_INFO = "contact_info"
    TECHNICAL_DATA = "technical_data"
    USAGE_DATA = "usage_data"
    LOCATION_DATA = "location_data"
    SPECIAL_CATEGORY = "special_category"  # Article 9 data

class ProcessingPurpose(Enum):
    """Purposes for data processing"""
    SERVICE_PROVISION = "service_provision"
    ANALYTICS = "analytics"
    MARKETING = "marketing"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    RESEARCH = "research"

@dataclass
class DataSubject:
    """Data subject information"""
    subject_id: str
    email: str
    created_at: datetime
    consent_records: List['ConsentRecord'] = field(default_factory=list)
    data_requests: List['DataRequest'] = field(default_factory=list)
    
class RequestType(Enum):
    """GDPR data subject request types"""
    ACCESS = "access"  # Article 15
    RECTIFICATION = "rectification"  # Article 16
    ERASURE = "erasure"  # Article 17 (Right to be forgotten)
    RESTRICT_PROCESSING = "restrict_processing"  # Article 18
    DATA_PORTABILITY = "data_portability"  # Article 20
    OBJECT = "object"  # Article 21

@dataclass
class ConsentRecord:
    """Consent record for GDPR compliance"""
    consent_id: str
    subject_id: str
    purpose: ProcessingPurpose
    lawful_basis: LawfulBasis
    granted_at: datetime
    withdrawn_at: Optional[datetime] = None
    consent_text: str = ""
    version: str = "1.0"
    
    def is_active(self) -> bool:
        """Check if consent is currently active"""
        return self.withdrawn_at is None
    
    def withdraw(self) -> None:
        """Withdraw consent"""
        self.withdrawn_at = datetime.utcnow()

@dataclass
class DataRequest:
    """GDPR data subject request"""
    request_id: str
    subject_id: str
    request_type: RequestType
    requested_at: datetime
    completed_at: Optional[datetime] = None
    status: str = "pending"
    notes: str = ""
    
    def complete(self, notes: str = "") -> None:
        """Mark request as completed"""
        self.completed_at = datetime.utcnow()
        self.status = "completed"
        self.notes = notes

@dataclass
class DataProcessingRecord:
    """Record of Processing Activities (ROPA) - Article 30"""
    activity_id: str
    controller_name: str
    controller_contact: str
    purpose: ProcessingPurpose
    lawful_basis: LawfulBasis
    data_categories: List[DataCategory]
    recipients: List[str]
    third_country_transfers: List[str]
    retention_period: str
    security_measures: List[str]
    created_at: datetime

class DataMinimization:
    """Data minimization principles implementation"""
    
    @staticmethod
    def pseudonymize_data(data: Dict[str, Any], fields_to_pseudonymize: List[str]) -> Dict[str, Any]:
        """Pseudonymize specified fields"""
        pseudonymized = data.copy()
        
        for field in fields_to_pseudonymize:
            if field in pseudonymized:
                original_value = str(pseudonymized[field])
                pseudonymized[field] = hashlib.sha256(
                    (original_value + "salt").encode()
                ).hexdigest()[:16]
        
        return pseudonymized
    
    @staticmethod
    def anonymize_data(data: Dict[str, Any], fields_to_remove: List[str]) -> Dict[str, Any]:
        """Anonymize data by removing identifying fields"""
        anonymized = data.copy()
        
        for field in fields_to_remove:
            if field in anonymized:
                del anonymized[field]
        
        return anonymized

class RetentionManager:
    """Data retention policy management"""
    
    def __init__(self):
        self.retention_policies = {
            DataCategory.BASIC_IDENTITY: timedelta(days=365*7),  # 7 years
            DataCategory.CONTACT_INFO: timedelta(days=365*3),   # 3 years
            DataCategory.TECHNICAL_DATA: timedelta(days=365*2), # 2 years
            DataCategory.USAGE_DATA: timedelta(days=365),       # 1 year
            DataCategory.LOCATION_DATA: timedelta(days=90),     # 90 days
            DataCategory.SPECIAL_CATEGORY: timedelta(days=365*10), # 10 years
        }
    
    def should_delete(self, data_category: DataCategory, created_at: datetime) -> bool:
        """Check if data should be deleted based on retention policy"""
        retention_period = self.retention_policies.get(data_category, timedelta(days=365))
        return datetime.utcnow() - created_at > retention_period
    
    def get_retention_period(self, data_category: DataCategory) -> timedelta:
        """Get retention period for data category"""
        return self.retention_policies.get(data_category, timedelta(days=365))

class CrossBorderTransferManager:
    """Cross-border data transfer compliance"""
    
    ADEQUATE_COUNTRIES = [
        "AD", "AR", "CA", "FO", "GG", "IL", "IM", "IS", "JE", "JP", 
        "NZ", "CH", "UY", "GB", "KR", "AU", "DK", "AT", "BE", "BG", 
        "HR", "CY", "CZ", "EE", "FI", "FR", "DE", "GR", "HU", "IE", 
        "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", 
        "SI", "ES", "SE"
    ]
    
    @classmethod
    def is_adequate_country(cls, country_code: str) -> bool:
        """Check if country has adequacy decision"""
        return country_code.upper() in cls.ADEQUATE_COUNTRIES
    
    @classmethod
    def requires_safeguards(cls, country_code: str) -> bool:
        """Check if transfer requires additional safeguards"""
        return not cls.is_adequate_country(country_code)

class GDPRCompliance:
    """Main GDPR compliance manager"""
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("gdpr_data")
        self.storage_path.mkdir(exist_ok=True)
        
        self.consent_manager = ConsentManager(self.storage_path / "consents.json")
        self.request_manager = RequestManager(self.storage_path / "requests.json")
        self.retention_manager = RetentionManager()
        self.processing_records: List[DataProcessingRecord] = []
        
        # Load existing data
        self._load_processing_records()
    
    def record_processing_activity(
        self,
        activity_id: str,
        controller_name: str,
        controller_contact: str,
        purpose: ProcessingPurpose,
        lawful_basis: LawfulBasis,
        data_categories: List[DataCategory],
        recipients: List[str] = None,
        third_country_transfers: List[str] = None,
        retention_period: str = "As per retention policy",
        security_measures: List[str] = None
    ) -> DataProcessingRecord:
        """Record processing activity (Article 30 compliance)"""
        
        record = DataProcessingRecord(
            activity_id=activity_id,
            controller_name=controller_name,
            controller_contact=controller_contact,
            purpose=purpose,
            lawful_basis=lawful_basis,
            data_categories=data_categories,
            recipients=recipients or [],
            third_country_transfers=third_country_transfers or [],
            retention_period=retention_period,
            security_measures=security_measures or [
                "Encryption at rest and in transit",
                "Access controls and authentication",
                "Regular security assessments",
                "Data breach monitoring"
            ],
            created_at=datetime.utcnow()
        )
        
        self.processing_records.append(record)
        self._save_processing_records()
        
        logger.info(f"Recorded processing activity: {activity_id}")
        return record
    
    def handle_data_subject_request(
        self,
        subject_id: str,
        request_type: RequestType,
        notes: str = ""
    ) -> DataRequest:
        """Handle data subject request"""
        return self.request_manager.create_request(subject_id, request_type, notes)
    
    def grant_consent(
        self,
        subject_id: str,
        purpose: ProcessingPurpose,
        lawful_basis: LawfulBasis,
        consent_text: str = ""
    ) -> ConsentRecord:
        """Grant consent for data processing"""
        return self.consent_manager.grant_consent(subject_id, purpose, lawful_basis, consent_text)
    
    def withdraw_consent(self, consent_id: str) -> bool:
        """Withdraw consent"""
        return self.consent_manager.withdraw_consent(consent_id)
    
    def check_consent(self, subject_id: str, purpose: ProcessingPurpose) -> bool:
        """Check if valid consent exists"""
        return self.consent_manager.has_valid_consent(subject_id, purpose)
    
    def perform_retention_cleanup(self) -> Dict[str, int]:
        """Perform data retention cleanup"""
        cleanup_stats = {category.value: 0 for category in DataCategory}
        
        # This would integrate with actual data stores
        # For demonstration, we'll just log the actions
        for category in DataCategory:
            # In real implementation, query data stores for records older than retention period
            logger.info(f"Checking retention for {category.value}")
            # cleanup_stats[category.value] = deleted_count
        
        return cleanup_stats
    
    def generate_privacy_notice(self) -> Dict[str, Any]:
        """Generate privacy notice content"""
        return {
            "controller": {
                "name": "Agentic Research Engine",
                "contact": "privacy@agentic-research.com",
                "dpo_contact": "dpo@agentic-research.com"
            },
            "purposes": [purpose.value for purpose in ProcessingPurpose],
            "lawful_bases": [basis.value for basis in LawfulBasis],
            "data_categories": [category.value for category in DataCategory],
            "retention_periods": {
                category.value: str(self.retention_manager.get_retention_period(category))
                for category in DataCategory
            },
            "rights": [
                "Right of access (Article 15)",
                "Right to rectification (Article 16)", 
                "Right to erasure (Article 17)",
                "Right to restrict processing (Article 18)",
                "Right to data portability (Article 20)",
                "Right to object (Article 21)"
            ],
            "transfers": {
                "adequate_countries": CrossBorderTransferManager.ADEQUATE_COUNTRIES,
                "safeguards": "Standard Contractual Clauses (SCCs) where applicable"
            }
        }
    
    def _load_processing_records(self):
        """Load processing records from storage"""
        records_file = self.storage_path / "processing_records.json"
        if records_file.exists():
            try:
                with open(records_file) as f:
                    data = json.load(f)
                # In real implementation, deserialize DataProcessingRecord objects
                logger.info(f"Loaded {len(data)} processing records")
            except Exception as e:
                logger.error(f"Error loading processing records: {e}")
    
    def _save_processing_records(self):
        """Save processing records to storage"""
        records_file = self.storage_path / "processing_records.json"
        try:
            # In real implementation, serialize DataProcessingRecord objects
            data = []  # Convert self.processing_records to serializable format
            with open(records_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving processing records: {e}")

class ConsentManager:
    """Manage GDPR consent records"""
    
    def __init__(self, storage_file: Path):
        self.storage_file = storage_file
        self.consents: Dict[str, ConsentRecord] = {}
        self._load_consents()
    
    def grant_consent(
        self,
        subject_id: str,
        purpose: ProcessingPurpose,
        lawful_basis: LawfulBasis,
        consent_text: str = ""
    ) -> ConsentRecord:
        """Grant consent"""
        consent_id = f"consent_{secrets.token_hex(8)}"
        
        consent = ConsentRecord(
            consent_id=consent_id,
            subject_id=subject_id,
            purpose=purpose,
            lawful_basis=lawful_basis,
            granted_at=datetime.utcnow(),
            consent_text=consent_text
        )
        
        self.consents[consent_id] = consent
        self._save_consents()
        
        logger.info(f"Granted consent {consent_id} for subject {subject_id}")
        return consent
    
    def withdraw_consent(self, consent_id: str) -> bool:
        """Withdraw consent"""
        if consent_id in self.consents:
            self.consents[consent_id].withdraw()
            self._save_consents()
            logger.info(f"Withdrawn consent {consent_id}")
            return True
        return False
    
    def has_valid_consent(self, subject_id: str, purpose: ProcessingPurpose) -> bool:
        """Check for valid consent"""
        for consent in self.consents.values():
            if (consent.subject_id == subject_id and 
                consent.purpose == purpose and 
                consent.is_active()):
                return True
        return False
    
    def _load_consents(self):
        """Load consents from storage"""
        if self.storage_file.exists():
            try:
                with open(self.storage_file) as f:
                    # In real implementation, deserialize ConsentRecord objects
                    data = json.load(f)
                    logger.info(f"Loaded {len(data)} consent records")
            except Exception as e:
                logger.error(f"Error loading consents: {e}")
    
    def _save_consents(self):
        """Save consents to storage"""
        try:
            # In real implementation, serialize ConsentRecord objects
            data = {}
            with open(self.storage_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving consents: {e}")

class RequestManager:
    """Manage GDPR data subject requests"""
    
    def __init__(self, storage_file: Path):
        self.storage_file = storage_file
        self.requests: Dict[str, DataRequest] = {}
        self._load_requests()
    
    def create_request(self, subject_id: str, request_type: RequestType, notes: str = "") -> DataRequest:
        """Create data subject request"""
        request_id = f"req_{secrets.token_hex(8)}"
        
        request = DataRequest(
            request_id=request_id,
            subject_id=subject_id,
            request_type=request_type,
            requested_at=datetime.utcnow(),
            notes=notes
        )
        
        self.requests[request_id] = request
        self._save_requests()
        
        logger.info(f"Created {request_type.value} request {request_id} for subject {subject_id}")
        return request
    
    def complete_request(self, request_id: str, notes: str = "") -> bool:
        """Complete data subject request"""
        if request_id in self.requests:
            self.requests[request_id].complete(notes)
            self._save_requests()
            logger.info(f"Completed request {request_id}")
            return True
        return False
    
    def _load_requests(self):
        """Load requests from storage"""
        if self.storage_file.exists():
            try:
                with open(self.storage_file) as f:
                    data = json.load(f)
                    logger.info(f"Loaded {len(data)} data subject requests")
            except Exception as e:
                logger.error(f"Error loading requests: {e}")
    
    def _save_requests(self):
        """Save requests to storage"""
        try:
            data = {}
            with open(self.storage_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving requests: {e}")

# Example usage and compliance testing
if __name__ == "__main__":
    # Initialize GDPR compliance
    gdpr = GDPRCompliance()
    
    # Record processing activities
    gdpr.record_processing_activity(
        activity_id="user_analytics",
        controller_name="Agentic Research Engine",
        controller_contact="privacy@agentic-research.com",
        purpose=ProcessingPurpose.ANALYTICS,
        lawful_basis=LawfulBasis.LEGITIMATE_INTERESTS,
        data_categories=[DataCategory.USAGE_DATA, DataCategory.TECHNICAL_DATA],
        recipients=["Analytics Team"],
        retention_period="1 year",
        security_measures=["Pseudonymization", "Encryption", "Access controls"]
    )
    
    # Grant consent
    consent = gdpr.grant_consent(
        subject_id="user123",
        purpose=ProcessingPurpose.ANALYTICS,
        lawful_basis=LawfulBasis.CONSENT,
        consent_text="I consent to processing my usage data for analytics purposes"
    )
    
    # Check consent
    has_consent = gdpr.check_consent("user123", ProcessingPurpose.ANALYTICS)
    print(f"Has valid consent: {has_consent}")
    
    # Handle data subject request
    request = gdpr.handle_data_subject_request(
        subject_id="user123",
        request_type=RequestType.ACCESS,
        notes="User requesting access to all personal data"
    )
    
    # Generate privacy notice
    privacy_notice = gdpr.generate_privacy_notice()
    print("Privacy notice generated")
    
    # Test data minimization
    test_data = {
        "name": "John Doe",
        "email": "john@example.com",
        "ip_address": "192.168.1.1",
        "usage_stats": {"clicks": 100}
    }
    
    pseudonymized = DataMinimization.pseudonymize_data(
        test_data, ["name", "email", "ip_address"]
    )
    print(f"Pseudonymized data: {pseudonymized}")
    
    # Test retention management
    retention = RetentionManager()
    should_delete = retention.should_delete(
        DataCategory.USAGE_DATA,
        datetime.utcnow() - timedelta(days=400)
    )
    print(f"Should delete old usage data: {should_delete}")
    
    print("GDPR compliance framework initialized successfully")