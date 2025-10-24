"""
Bedrock Guardrails and Security Controls

Implements comprehensive security guardrails including PII redaction,
content filtering, and Bedrock Guardrails integration for production compliance.
"""

import re
import json
import asyncio
import hashlib
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

import boto3
from botocore.exceptions import ClientError

from src.utils.logging import get_logger
from src.utils.config import config
from src.utils.exceptions import SecurityViolationError, GuardrailViolationError


logger = get_logger("guardrails")


class ContentRiskLevel(Enum):
    """Content risk assessment levels."""
    SAFE = "safe"
    LOW_RISK = "low_risk"
    MEDIUM_RISK = "medium_risk"
    HIGH_RISK = "high_risk"
    BLOCKED = "blocked"


class PIIType(Enum):
    """Types of PII that can be detected and redacted."""
    EMAIL = "email"
    IP_ADDRESS = "ip_address"
    SSN = "ssn"
    PHONE = "phone"
    CREDIT_CARD = "credit_card"
    AWS_ACCESS_KEY = "aws_access_key"
    API_KEY = "api_key"
    PASSWORD = "password"


@dataclass
class PIIDetection:
    """PII detection result."""
    pii_type: PIIType
    original_text: str
    redacted_text: str
    confidence: float
    position: Tuple[int, int]  # Start and end positions


@dataclass
class ContentFilterResult:
    """Content filtering result."""
    original_content: str
    filtered_content: str
    risk_level: ContentRiskLevel
    violations: List[str]
    confidence: float
    processing_time_ms: int


@dataclass
class GuardrailPolicy:
    """Guardrail policy configuration."""
    name: str
    enabled: bool
    severity: str
    action: str  # "block", "redact", "warn", "log"
    patterns: List[str]
    confidence_threshold: float


class BedrockGuardrails:
    """
    Comprehensive security guardrails using AWS Bedrock Guardrails service
    and custom PII detection/redaction capabilities.
    """
    
    def __init__(self):
        """Initialize Bedrock Guardrails service."""
        self.bedrock_client = boto3.client('bedrock-runtime', region_name=config.aws_region)
        self.bedrock_agent_client = boto3.client('bedrock-agent', region_name=config.aws_region)
        
        # PII detection patterns
        self.pii_patterns = {
            PIIType.EMAIL: r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            PIIType.IP_ADDRESS: r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
            PIIType.SSN: r'\b\d{3}-?\d{2}-?\d{4}\b',
            PIIType.PHONE: r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
            PIIType.CREDIT_CARD: r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b',
            PIIType.AWS_ACCESS_KEY: r'\bAKIA[0-9A-Z]{16}\b',
            PIIType.API_KEY: r'\b[A-Za-z0-9]{32,}\b',
            PIIType.PASSWORD: r'(?i)(?:password|passwd|pwd)[\s]*[:=][\s]*[^\s\n]{6,}'
        }
        
        # Content filtering policies
        self.guardrail_policies = self._initialize_policies()
        
        # Bedrock Guardrail configuration
        self.guardrail_id = None
        self.guardrail_version = None
        
        # Performance metrics
        self.pii_detections = 0
        self.content_violations = 0
        self.processing_times = []
        
        logger.info("Bedrock Guardrails service initialized")
    
    def _initialize_policies(self) -> Dict[str, GuardrailPolicy]:
        """Initialize guardrail policies."""
        return {
            "malicious_content": GuardrailPolicy(
                name="Malicious Content Detection",
                enabled=True,
                severity="high",
                action="block",
                patterns=[
                    r'(?i)\b(?:hack|exploit|malware|virus|trojan|backdoor)\b',
                    r'(?i)\b(?:sql\s+injection|xss|csrf|rce)\b',
                    r'(?i)\b(?:delete\s+from|drop\s+table|truncate)\b'
                ],
                confidence_threshold=0.8
            ),
            "sensitive_data": GuardrailPolicy(
                name="Sensitive Data Protection",
                enabled=True,
                severity="medium",
                action="redact",
                patterns=[
                    r'(?i)\b(?:confidential|secret|private|internal)\b',
                    r'(?i)\b(?:database|db)\s+(?:password|credentials)\b'
                ],
                confidence_threshold=0.7
            ),
            "inappropriate_language": GuardrailPolicy(
                name="Inappropriate Language Filter",
                enabled=True,
                severity="low",
                action="warn",
                patterns=[
                    r'(?i)\b(?:profanity|offensive|inappropriate)\b'  # Placeholder patterns
                ],
                confidence_threshold=0.6
            )
        }
    
    async def setup_bedrock_guardrail(self) -> bool:
        """Set up Bedrock Guardrail configuration."""
        try:
            # Create guardrail configuration
            guardrail_config = {
                "name": "IncidentCommanderGuardrail",
                "description": "Security guardrails for Incident Commander system",
                "topicPolicyConfig": {
                    "topicsConfig": [
                        {
                            "name": "MaliciousContent",
                            "definition": "Content that could be used for malicious purposes",
                            "examples": [
                                "How to hack into systems",
                                "SQL injection techniques",
                                "Malware distribution"
                            ],
                            "type": "DENY"
                        },
                        {
                            "name": "SensitiveData",
                            "definition": "Sensitive or confidential information",
                            "examples": [
                                "Database passwords",
                                "API keys",
                                "Personal information"
                            ],
                            "type": "DENY"
                        }
                    ]
                },
                "contentPolicyConfig": {
                    "filtersConfig": [
                        {
                            "type": "SEXUAL",
                            "inputStrength": "HIGH",
                            "outputStrength": "HIGH"
                        },
                        {
                            "type": "VIOLENCE",
                            "inputStrength": "HIGH",
                            "outputStrength": "HIGH"
                        },
                        {
                            "type": "HATE",
                            "inputStrength": "HIGH",
                            "outputStrength": "HIGH"
                        },
                        {
                            "type": "INSULTS",
                            "inputStrength": "MEDIUM",
                            "outputStrength": "MEDIUM"
                        },
                        {
                            "type": "MISCONDUCT",
                            "inputStrength": "HIGH",
                            "outputStrength": "HIGH"
                        }
                    ]
                },
                "wordPolicyConfig": {
                    "wordsConfig": [
                        {
                            "text": "password"
                        },
                        {
                            "text": "secret"
                        },
                        {
                            "text": "confidential"
                        }
                    ],
                    "managedWordListsConfig": [
                        {
                            "type": "PROFANITY"
                        }
                    ]
                },
                "sensitiveInformationPolicyConfig": {
                    "piiEntitiesConfig": [
                        {
                            "type": "EMAIL",
                            "action": "BLOCK"
                        },
                        {
                            "type": "PHONE",
                            "action": "BLOCK"
                        },
                        {
                            "type": "SSN",
                            "action": "BLOCK"
                        },
                        {
                            "type": "CREDIT_DEBIT_CARD_NUMBER",
                            "action": "BLOCK"
                        },
                        {
                            "type": "AWS_ACCESS_KEY",
                            "action": "BLOCK"
                        },
                        {
                            "type": "AWS_SECRET_KEY",
                            "action": "BLOCK"
                        }
                    ]
                }
            }
            
            # Create the guardrail
            response = await asyncio.to_thread(
                self.bedrock_agent_client.create_guardrail,
                **guardrail_config
            )
            
            self.guardrail_id = response['guardrailId']
            self.guardrail_version = response['version']
            
            logger.info(f"Bedrock Guardrail created: {self.guardrail_id} v{self.guardrail_version}")
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConflictException':
                # Guardrail already exists, get existing one
                await self._get_existing_guardrail()
                return True
            else:
                logger.error(f"Failed to create Bedrock Guardrail: {e}")
                return False
        except Exception as e:
            logger.error(f"Unexpected error setting up Bedrock Guardrail: {e}")
            return False
    
    async def _get_existing_guardrail(self):
        """Get existing guardrail configuration."""
        try:
            # List existing guardrails
            response = await asyncio.to_thread(
                self.bedrock_agent_client.list_guardrails
            )
            
            for guardrail in response.get('guardrails', []):
                if guardrail['name'] == 'IncidentCommanderGuardrail':
                    self.guardrail_id = guardrail['id']
                    self.guardrail_version = guardrail['version']
                    logger.info(f"Using existing Bedrock Guardrail: {self.guardrail_id}")
                    return
            
            logger.warning("No existing IncidentCommanderGuardrail found")
            
        except Exception as e:
            logger.error(f"Failed to get existing guardrail: {e}")
    
    async def detect_and_redact_pii(self, text: str) -> Tuple[str, List[PIIDetection]]:
        """
        Detect and redact PII from text.
        
        Args:
            text: Input text to scan for PII
            
        Returns:
            Tuple of (redacted_text, list_of_detections)
        """
        start_time = datetime.utcnow()
        detections = []
        redacted_text = text
        
        for pii_type, pattern in self.pii_patterns.items():
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            
            for match in matches:
                detection = PIIDetection(
                    pii_type=pii_type,
                    original_text=match.group(),
                    redacted_text=f'[REDACTED_{pii_type.value.upper()}]',
                    confidence=0.9,  # High confidence for regex matches
                    position=(match.start(), match.end())
                )
                detections.append(detection)
                
                # Replace in redacted text
                redacted_text = redacted_text.replace(
                    match.group(), 
                    detection.redacted_text
                )
        
        # Update metrics
        self.pii_detections += len(detections)
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        self.processing_times.append(processing_time)
        
        if detections:
            logger.info(f"Detected and redacted {len(detections)} PII instances")
        
        return redacted_text, detections
    
    async def filter_content(self, content: str) -> ContentFilterResult:
        """
        Filter content using Bedrock Guardrails and custom policies.
        
        Args:
            content: Content to filter
            
        Returns:
            ContentFilterResult with filtering details
        """
        start_time = datetime.utcnow()
        violations = []
        risk_level = ContentRiskLevel.SAFE
        filtered_content = content
        
        try:
            # First, apply custom policy filters
            for policy_name, policy in self.guardrail_policies.items():
                if not policy.enabled:
                    continue
                
                for pattern in policy.patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        violations.append(f"Policy violation: {policy_name}")
                        
                        if policy.action == "block":
                            risk_level = ContentRiskLevel.BLOCKED
                            filtered_content = "[CONTENT BLOCKED BY SECURITY POLICY]"
                            break
                        elif policy.action == "redact":
                            filtered_content = re.sub(pattern, "[REDACTED]", filtered_content, flags=re.IGNORECASE)
                            risk_level = max(risk_level, ContentRiskLevel.MEDIUM_RISK)
                        elif policy.action == "warn":
                            risk_level = max(risk_level, ContentRiskLevel.LOW_RISK)
            
            # If we have Bedrock Guardrail configured, use it
            if self.guardrail_id and risk_level != ContentRiskLevel.BLOCKED:
                bedrock_result = await self._apply_bedrock_guardrail(filtered_content)
                if bedrock_result:
                    violations.extend(bedrock_result.get('violations', []))
                    if bedrock_result.get('blocked', False):
                        risk_level = ContentRiskLevel.BLOCKED
                        filtered_content = "[CONTENT BLOCKED BY BEDROCK GUARDRAILS]"
            
            # Calculate confidence based on number of violations
            confidence = 1.0 - (len(violations) * 0.2)
            confidence = max(0.1, min(1.0, confidence))
            
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            result = ContentFilterResult(
                original_content=content,
                filtered_content=filtered_content,
                risk_level=risk_level,
                violations=violations,
                confidence=confidence,
                processing_time_ms=processing_time
            )
            
            if violations:
                self.content_violations += len(violations)
                logger.warning(f"Content filtering violations: {violations}")
            
            return result
            
        except Exception as e:
            logger.error(f"Content filtering failed: {e}")
            # Return safe default
            return ContentFilterResult(
                original_content=content,
                filtered_content=content,
                risk_level=ContentRiskLevel.SAFE,
                violations=[],
                confidence=0.5,
                processing_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000)
            )
    
    async def _apply_bedrock_guardrail(self, content: str) -> Optional[Dict[str, Any]]:
        """Apply Bedrock Guardrail to content."""
        try:
            if not self.guardrail_id:
                return None
            
            # Use Bedrock Guardrail API
            response = await asyncio.to_thread(
                self.bedrock_client.apply_guardrail,
                guardrailIdentifier=self.guardrail_id,
                guardrailVersion=self.guardrail_version,
                source="INPUT",
                content=[{
                    "text": {
                        "text": content
                    }
                }]
            )
            
            # Parse response
            action = response.get('action', 'NONE')
            assessments = response.get('assessments', [])
            
            violations = []
            blocked = False
            
            for assessment in assessments:
                if assessment.get('topicPolicy'):
                    for topic in assessment['topicPolicy'].get('topics', []):
                        if topic.get('action') == 'BLOCKED':
                            violations.append(f"Topic policy violation: {topic.get('name')}")
                            blocked = True
                
                if assessment.get('contentPolicy'):
                    for filter_result in assessment['contentPolicy'].get('filters', []):
                        if filter_result.get('action') == 'BLOCKED':
                            violations.append(f"Content policy violation: {filter_result.get('type')}")
                            blocked = True
                
                if assessment.get('wordPolicy'):
                    for word in assessment['wordPolicy'].get('customWords', []):
                        if word.get('action') == 'BLOCKED':
                            violations.append(f"Word policy violation: {word.get('match')}")
                            blocked = True
                
                if assessment.get('sensitiveInformationPolicy'):
                    for pii in assessment['sensitiveInformationPolicy'].get('piiEntities', []):
                        if pii.get('action') == 'BLOCKED':
                            violations.append(f"PII policy violation: {pii.get('type')}")
                            blocked = True
            
            return {
                'violations': violations,
                'blocked': blocked,
                'action': action
            }
            
        except Exception as e:
            logger.error(f"Bedrock Guardrail application failed: {e}")
            return None
    
    async def validate_incident_data(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and sanitize incident data before processing.
        
        Args:
            incident_data: Raw incident data
            
        Returns:
            Sanitized incident data with security annotations
        """
        sanitized_data = incident_data.copy()
        security_annotations = {
            'pii_detections': [],
            'content_violations': [],
            'sanitization_applied': False,
            'risk_assessment': ContentRiskLevel.SAFE.value
        }
        
        # Process text fields
        text_fields = ['title', 'description', 'error_message', 'logs']
        
        for field in text_fields:
            if field in sanitized_data and isinstance(sanitized_data[field], str):
                # Detect and redact PII
                redacted_text, pii_detections = await self.detect_and_redact_pii(sanitized_data[field])
                
                # Filter content
                filter_result = await self.filter_content(redacted_text)
                
                # Update data
                sanitized_data[field] = filter_result.filtered_content
                
                # Track security annotations
                if pii_detections:
                    security_annotations['pii_detections'].extend([
                        {
                            'field': field,
                            'type': detection.pii_type.value,
                            'position': detection.position
                        }
                        for detection in pii_detections
                    ])
                    security_annotations['sanitization_applied'] = True
                
                if filter_result.violations:
                    security_annotations['content_violations'].extend([
                        {
                            'field': field,
                            'violation': violation
                        }
                        for violation in filter_result.violations
                    ])
                    security_annotations['sanitization_applied'] = True
                
                # Update risk assessment
                if filter_result.risk_level.value != ContentRiskLevel.SAFE.value:
                    security_annotations['risk_assessment'] = filter_result.risk_level.value
        
        # Add security metadata
        sanitized_data['_security'] = security_annotations
        
        if security_annotations['sanitization_applied']:
            logger.info(f"Applied security sanitization to incident data: {len(security_annotations['pii_detections'])} PII, {len(security_annotations['content_violations'])} violations")
        
        return sanitized_data
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """Get security and guardrail metrics."""
        avg_processing_time = sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0
        
        return {
            'guardrail_status': {
                'bedrock_guardrail_id': self.guardrail_id,
                'bedrock_guardrail_version': self.guardrail_version,
                'policies_enabled': len([p for p in self.guardrail_policies.values() if p.enabled])
            },
            'detection_metrics': {
                'total_pii_detections': self.pii_detections,
                'total_content_violations': self.content_violations,
                'average_processing_time_ms': avg_processing_time,
                'total_processed': len(self.processing_times)
            },
            'pii_patterns': {
                pii_type.value: pattern 
                for pii_type, pattern in self.pii_patterns.items()
            },
            'active_policies': {
                name: {
                    'enabled': policy.enabled,
                    'severity': policy.severity,
                    'action': policy.action,
                    'confidence_threshold': policy.confidence_threshold
                }
                for name, policy in self.guardrail_policies.items()
            }
        }
    
    async def test_guardrail_functionality(self) -> Dict[str, Any]:
        """Test guardrail functionality with sample data."""
        test_results = {
            'pii_detection': {},
            'content_filtering': {},
            'bedrock_integration': {},
            'overall_status': 'unknown'
        }
        
        try:
            # Test PII detection
            test_pii_text = "Contact john.doe@example.com or call 555-123-4567. SSN: 123-45-6789"
            redacted_text, detections = await self.detect_and_redact_pii(test_pii_text)
            
            test_results['pii_detection'] = {
                'original': test_pii_text,
                'redacted': redacted_text,
                'detections_count': len(detections),
                'types_detected': [d.pii_type.value for d in detections],
                'status': 'pass' if len(detections) >= 3 else 'fail'
            }
            
            # Test content filtering
            test_malicious_content = "How to hack into the database and delete all tables"
            filter_result = await self.filter_content(test_malicious_content)
            
            test_results['content_filtering'] = {
                'original': test_malicious_content,
                'filtered': filter_result.filtered_content,
                'risk_level': filter_result.risk_level.value,
                'violations_count': len(filter_result.violations),
                'status': 'pass' if filter_result.violations else 'fail'
            }
            
            # Test Bedrock integration
            if self.guardrail_id:
                bedrock_test = await self._apply_bedrock_guardrail("This is a test message")
                test_results['bedrock_integration'] = {
                    'guardrail_id': self.guardrail_id,
                    'response_received': bedrock_test is not None,
                    'status': 'pass' if bedrock_test is not None else 'fail'
                }
            else:
                test_results['bedrock_integration'] = {
                    'status': 'not_configured'
                }
            
            # Overall status
            pii_pass = test_results['pii_detection']['status'] == 'pass'
            content_pass = test_results['content_filtering']['status'] == 'pass'
            bedrock_pass = test_results['bedrock_integration']['status'] in ['pass', 'not_configured']
            
            test_results['overall_status'] = 'pass' if all([pii_pass, content_pass, bedrock_pass]) else 'fail'
            
            logger.info(f"Guardrail functionality test completed: {test_results['overall_status']}")
            
        except Exception as e:
            logger.error(f"Guardrail functionality test failed: {e}")
            test_results['overall_status'] = 'error'
            test_results['error'] = str(e)
        
        return test_results


# Global guardrails instance
_bedrock_guardrails: Optional[BedrockGuardrails] = None


async def get_bedrock_guardrails() -> BedrockGuardrails:
    """Get the global Bedrock Guardrails instance."""
    global _bedrock_guardrails
    if _bedrock_guardrails is None:
        _bedrock_guardrails = BedrockGuardrails()
        # Initialize Bedrock Guardrail on first use
        await _bedrock_guardrails.setup_bedrock_guardrail()
    return _bedrock_guardrails


async def validate_and_sanitize_input(data: Any) -> Any:
    """
    Convenience function to validate and sanitize any input data.
    
    Args:
        data: Input data to validate
        
    Returns:
        Sanitized data
    """
    guardrails = await get_bedrock_guardrails()
    
    if isinstance(data, dict):
        return await guardrails.validate_incident_data(data)
    elif isinstance(data, str):
        redacted_text, _ = await guardrails.detect_and_redact_pii(data)
        filter_result = await guardrails.filter_content(redacted_text)
        return filter_result.filtered_content
    else:
        return data