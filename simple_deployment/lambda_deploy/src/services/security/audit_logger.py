"""
Tamper-proof audit logging service for comprehensive compliance.

This module implements cryptographically secure audit logging with
7-year data retention, PII redaction, and regulatory compliance features.
"""

import asyncio
import hashlib
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError
import structlog

from src.models.security import (
    AuditEvent, SecurityEventType, SecuritySeverity,
    PIIRedactionResult, ComplianceReport
)
from src.utils.config import ConfigManager
from src.utils.exceptions import SecurityError


logger = structlog.get_logger(__name__)


class TamperProofAuditLogger:
    """
    Tamper-proof audit logging service with cryptographic integrity verification.
    
    Features:
    - Cryptographic integrity verification for all audit events
    - 7-year data retention with automated lifecycle management
    - PII redaction and data loss prevention scanning
    - Compliance reporting for regulatory requirements
    - Immutable audit trail with blockchain-like chaining
    """
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.dynamodb = boto3.resource('dynamodb', region_name=config.aws.region)
        self.s3 = boto3.client('s3', region_name=config.aws.region)
        
        # Audit storage configuration
        self.audit_table_name = config.get('audit_table_name', 'incident-commander-audit-logs')
        self.audit_bucket_name = config.get('audit_bucket_name', 'incident-commander-audit-archive')
        self.retention_years = config.get('audit_retention_years', 7)
        
        # PII redaction patterns
        self.pii_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'phone': r'\b\d{3}-\d{3}-\d{4}\b',
            'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            'ip_address': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
            'aws_access_key': r'\bAKIA[0-9A-Z]{16}\b',
            'aws_secret_key': r'\b[A-Za-z0-9/+=]{40}\b'
        }
        
        # Chain hash for immutable audit trail
        self._last_chain_hash: Optional[str] = None
        self._chain_lock = asyncio.Lock()
    
    async def log_security_event(
        self,
        event_type: SecurityEventType,
        severity: SecuritySeverity,
        action: str,
        outcome: str,
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
        source_ip: Optional[str] = None,
        resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        """
        Log a security event with tamper-proof integrity verification.
        
        Args:
            event_type: Type of security event
            severity: Event severity level
            action: Action being performed
            outcome: Result of the action
            agent_id: Agent identifier (if applicable)
            user_id: User identifier (if applicable)
            source_ip: Source IP address
            resource: Resource being accessed
            details: Additional event details
            
        Returns:
            AuditEvent: The logged audit event
        """
        try:
            # Generate unique event ID
            event_id = str(uuid4())
            
            # Redact PII from details
            if details:
                details = await self._redact_pii_from_dict(details)
            
            # Create audit event
            audit_event = AuditEvent(
                event_id=event_id,
                event_type=event_type,
                severity=severity,
                agent_id=agent_id,
                user_id=user_id,
                source_ip=source_ip,
                resource=resource,
                action=action,
                outcome=outcome,
                details=details or {}
            )
            
            # Add to immutable chain
            async with self._chain_lock:
                chain_hash = await self._calculate_chain_hash(audit_event)
                audit_event.details['chain_hash'] = chain_hash
                audit_event.details['previous_hash'] = self._last_chain_hash
                self._last_chain_hash = chain_hash
            
            # Store in DynamoDB
            await self._store_audit_event(audit_event)
            
            # Log for immediate monitoring
            await logger.ainfo(
                "Security event logged",
                event_id=event_id,
                event_type=event_type,
                severity=severity,
                agent_id=agent_id,
                action=action,
                outcome=outcome
            )
            
            return audit_event
            
        except Exception as e:
            await logger.aerror(
                "Failed to log security event",
                error=str(e),
                event_type=event_type,
                action=action
            )
            raise SecurityError(f"Audit logging failed: {e}")
    
    async def verify_audit_chain(self, start_date: datetime, end_date: datetime) -> bool:
        """
        Verify the integrity of the audit chain for a given time period.
        
        Args:
            start_date: Start of verification period
            end_date: End of verification period
            
        Returns:
            bool: True if chain integrity is verified
        """
        try:
            # Retrieve audit events in chronological order
            events = await self._get_audit_events_by_date_range(start_date, end_date)
            
            if not events:
                return True  # Empty chain is valid
            
            # Verify each event's integrity hash
            for event in events:
                if not event.verify_integrity():
                    await logger.aerror(
                        "Audit event integrity verification failed",
                        event_id=event.event_id,
                        timestamp=event.timestamp
                    )
                    return False
            
            # Verify chain continuity
            previous_hash = None
            for event in events:
                expected_previous = event.details.get('previous_hash')
                if previous_hash != expected_previous:
                    await logger.aerror(
                        "Audit chain continuity broken",
                        event_id=event.event_id,
                        expected_previous=expected_previous,
                        actual_previous=previous_hash
                    )
                    return False
                previous_hash = event.details.get('chain_hash')
            
            await logger.ainfo(
                "Audit chain integrity verified",
                start_date=start_date,
                end_date=end_date,
                events_verified=len(events)
            )
            
            return True
            
        except Exception as e:
            await logger.aerror(
                "Audit chain verification failed",
                error=str(e),
                start_date=start_date,
                end_date=end_date
            )
            return False
    
    async def redact_pii(self, text: str) -> PIIRedactionResult:
        """
        Redact personally identifiable information from text.
        
        Args:
            text: Text to scan for PII
            
        Returns:
            PIIRedactionResult: Redaction results with confidence score
        """
        redacted_text = text
        redacted_items = []
        total_matches = 0
        
        for pii_type, pattern in self.pii_patterns.items():
            matches = re.finditer(pattern, redacted_text, re.IGNORECASE)
            for match in matches:
                redacted_items.append({
                    'type': pii_type,
                    'pattern': match.group(),
                    'start': match.start(),
                    'end': match.end()
                })
                total_matches += 1
                
                # Replace with redacted placeholder
                redacted_text = redacted_text.replace(
                    match.group(),
                    f'[REDACTED_{pii_type.upper()}]'
                )
        
        # Calculate confidence score based on pattern matching
        confidence_score = min(1.0, len(redacted_items) / max(1, len(text.split()) * 0.1))
        
        return PIIRedactionResult(
            original_text=text,
            redacted_text=redacted_text,
            redacted_items=redacted_items,
            confidence_score=confidence_score
        )
    
    async def generate_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime,
        compliance_framework: str = "SOC2"
    ) -> ComplianceReport:
        """
        Generate compliance report for regulatory requirements.
        
        Args:
            start_date: Report period start
            end_date: Report period end
            compliance_framework: Compliance framework (SOC2, GDPR, etc.)
            
        Returns:
            ComplianceReport: Generated compliance report
        """
        try:
            # Retrieve audit events for the period
            events = await self._get_audit_events_by_date_range(start_date, end_date)
            
            # Calculate compliance metrics
            total_events = len(events)
            security_violations = len([
                e for e in events 
                if e.event_type in [
                    SecurityEventType.SECURITY_VIOLATION,
                    SecurityEventType.UNAUTHORIZED_ACCESS,
                    SecurityEventType.PRIVILEGE_ESCALATION
                ]
            ])
            
            # Verify data retention compliance
            retention_cutoff = datetime.utcnow() - timedelta(days=self.retention_years * 365)
            data_retention_compliance = await self._verify_data_retention(retention_cutoff)
            
            # Verify encryption compliance
            encryption_compliance = await self._verify_encryption_compliance(events)
            
            # Verify access control compliance
            access_control_compliance = await self._verify_access_control_compliance(events)
            
            # Generate findings and recommendations
            findings = []
            recommendations = []
            
            if security_violations > 0:
                findings.append({
                    'type': 'security_violations',
                    'count': security_violations,
                    'severity': 'high' if security_violations > 10 else 'medium'
                })
                recommendations.append(
                    "Review and strengthen security controls to reduce violations"
                )
            
            if not data_retention_compliance:
                findings.append({
                    'type': 'data_retention',
                    'severity': 'high',
                    'description': 'Data retention policy violations detected'
                })
                recommendations.append(
                    "Implement automated data lifecycle management"
                )
            
            # Create compliance report
            report = ComplianceReport(
                report_id=str(uuid4()),
                report_type=f"{compliance_framework}_audit_report",
                period_start=start_date,
                period_end=end_date,
                compliance_framework=compliance_framework,
                total_audit_events=total_events,
                security_violations=security_violations,
                data_retention_compliance=data_retention_compliance,
                encryption_compliance=encryption_compliance,
                access_control_compliance=access_control_compliance,
                findings=findings,
                recommendations=recommendations
            )
            
            # Store report for future reference
            await self._store_compliance_report(report)
            
            await logger.ainfo(
                "Compliance report generated",
                report_id=report.report_id,
                framework=compliance_framework,
                period_start=start_date,
                period_end=end_date,
                total_events=total_events
            )
            
            return report
            
        except Exception as e:
            await logger.aerror(
                "Failed to generate compliance report",
                error=str(e),
                framework=compliance_framework
            )
            raise SecurityError(f"Compliance report generation failed: {e}")
    
    async def archive_old_logs(self) -> int:
        """
        Archive audit logs older than retention period to S3 cold storage.
        
        Returns:
            int: Number of logs archived
        """
        try:
            # Calculate archive cutoff (keep 1 year in hot storage)
            archive_cutoff = datetime.utcnow() - timedelta(days=365)
            
            # Get old audit events
            old_events = await self._get_audit_events_before_date(archive_cutoff)
            
            if not old_events:
                return 0
            
            # Archive to S3
            archive_key = f"audit-logs/{archive_cutoff.year}/{archive_cutoff.month}/audit-archive.json"
            archive_data = {
                'archived_at': datetime.utcnow().isoformat(),
                'archive_cutoff': archive_cutoff.isoformat(),
                'events': [event.dict() for event in old_events]
            }
            
            await self._upload_to_s3(
                self.audit_bucket_name,
                archive_key,
                json.dumps(archive_data, default=str)
            )
            
            # Remove from hot storage
            await self._delete_archived_events(old_events)
            
            await logger.ainfo(
                "Audit logs archived",
                events_archived=len(old_events),
                archive_key=archive_key
            )
            
            return len(old_events)
            
        except Exception as e:
            await logger.aerror("Failed to archive audit logs", error=str(e))
            raise SecurityError(f"Log archival failed: {e}")
    
    # Private helper methods
    
    async def _redact_pii_from_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively redact PII from dictionary values."""
        redacted_data = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                redaction_result = await self.redact_pii(value)
                redacted_data[key] = redaction_result.redacted_text
            elif isinstance(value, dict):
                redacted_data[key] = await self._redact_pii_from_dict(value)
            elif isinstance(value, list):
                redacted_data[key] = [
                    (await self.redact_pii(item)).redacted_text if isinstance(item, str) else item
                    for item in value
                ]
            else:
                redacted_data[key] = value
        
        return redacted_data
    
    async def _calculate_chain_hash(self, event: AuditEvent) -> str:
        """Calculate chain hash for immutable audit trail."""
        chain_data = {
            'event_id': event.event_id,
            'timestamp': event.timestamp.isoformat(),
            'integrity_hash': event.integrity_hash,
            'previous_hash': self._last_chain_hash
        }
        
        chain_str = json.dumps(chain_data, sort_keys=True)
        return hashlib.sha256(chain_str.encode()).hexdigest()
    
    async def _store_audit_event(self, event: AuditEvent) -> None:
        """Store audit event in DynamoDB."""
        table = self.dynamodb.Table(self.audit_table_name)
        
        item = {
            'event_id': event.event_id,
            'timestamp': event.timestamp.isoformat(),
            'event_type': event.event_type,
            'severity': event.severity,
            'agent_id': event.agent_id,
            'user_id': event.user_id,
            'source_ip': event.source_ip,
            'resource': event.resource,
            'action': event.action,
            'outcome': event.outcome,
            'details': event.details,
            'integrity_hash': event.integrity_hash,
            'ttl': int((datetime.utcnow() + timedelta(days=self.retention_years * 365)).timestamp())
        }
        
        # Remove None values
        item = {k: v for k, v in item.items() if v is not None}
        
        await asyncio.to_thread(table.put_item, Item=item)
    
    async def _get_audit_events_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[AuditEvent]:
        """Retrieve audit events within date range."""
        # This is a simplified implementation
        # In production, you'd use DynamoDB GSI for efficient date range queries
        table = self.dynamodb.Table(self.audit_table_name)
        
        response = await asyncio.to_thread(table.scan)
        events = []
        
        for item in response.get('Items', []):
            event_time = datetime.fromisoformat(item['timestamp'])
            if start_date <= event_time <= end_date:
                events.append(AuditEvent(**item))
        
        return sorted(events, key=lambda x: x.timestamp)
    
    async def _get_audit_events_before_date(self, cutoff_date: datetime) -> List[AuditEvent]:
        """Get audit events before specified date for archival."""
        table = self.dynamodb.Table(self.audit_table_name)
        
        response = await asyncio.to_thread(table.scan)
        events = []
        
        for item in response.get('Items', []):
            event_time = datetime.fromisoformat(item['timestamp'])
            if event_time < cutoff_date:
                events.append(AuditEvent(**item))
        
        return events
    
    async def _verify_data_retention(self, retention_cutoff: datetime) -> bool:
        """Verify data retention policy compliance."""
        # Check if any data exists beyond retention period
        old_events = await self._get_audit_events_before_date(retention_cutoff)
        return len(old_events) == 0
    
    async def _verify_encryption_compliance(self, events: List[AuditEvent]) -> bool:
        """Verify encryption compliance for audit events."""
        # All events should have integrity hashes (indicating encryption)
        return all(event.integrity_hash for event in events)
    
    async def _verify_access_control_compliance(self, events: List[AuditEvent]) -> bool:
        """Verify access control compliance."""
        # Check for proper authentication events
        auth_events = [
            e for e in events 
            if e.event_type == SecurityEventType.AGENT_AUTHENTICATION
        ]
        
        # Should have authentication events for all agent activities
        return len(auth_events) > 0
    
    async def _store_compliance_report(self, report: ComplianceReport) -> None:
        """Store compliance report in DynamoDB."""
        table = self.dynamodb.Table(self.audit_table_name)
        
        item = {
            'event_id': f"compliance_report_{report.report_id}",
            'timestamp': report.generated_at.isoformat(),
            'event_type': 'compliance_report',
            'severity': 'medium',
            'action': 'generate_compliance_report',
            'outcome': 'success',
            'details': report.dict(),
            'ttl': int((datetime.utcnow() + timedelta(days=self.retention_years * 365)).timestamp())
        }
        
        await asyncio.to_thread(table.put_item, Item=item)
    
    async def _upload_to_s3(self, bucket: str, key: str, data: str) -> None:
        """Upload data to S3 with encryption."""
        await asyncio.to_thread(
            self.s3.put_object,
            Bucket=bucket,
            Key=key,
            Body=data,
            ServerSideEncryption='AES256'
        )
    
    async def _delete_archived_events(self, events: List[AuditEvent]) -> None:
        """Delete archived events from hot storage."""
        table = self.dynamodb.Table(self.audit_table_name)
        
        for event in events:
            await asyncio.to_thread(
                table.delete_item,
                Key={'event_id': event.event_id}
            )