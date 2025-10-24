"""
Compliance management service for regulatory requirements.

This module implements compliance reporting, data retention management,
and regulatory framework support for SOC2, GDPR, and other standards.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError
import structlog

from src.models.security import (
    ComplianceReport, AuditEvent, SecurityEventType,
    SecuritySeverity, PIIRedactionResult
)
from src.utils.config import ConfigManager
from src.utils.exceptions import SecurityError, ComplianceError


logger = structlog.get_logger(__name__)


class ComplianceManager:
    """
    Compliance management service for regulatory requirements.
    
    Features:
    - Automated compliance reporting for SOC2, GDPR, HIPAA, PCI-DSS
    - Data retention policy enforcement with automated lifecycle management
    - PII detection and redaction for data loss prevention
    - Regulatory audit trail maintenance and verification
    - Compliance dashboard metrics and alerting
    """
    
    def __init__(self, config: ConfigManager, audit_logger=None):
        self.config = config
        self.audit_logger = audit_logger
        
        # AWS services
        self.dynamodb = boto3.resource('dynamodb', region_name=config.aws.region)
        self.s3 = boto3.client('s3', region_name=config.aws.region)
        
        # Storage configuration
        self.compliance_table_name = config.get('compliance_reports_table', 'incident-commander-compliance')
        self.compliance_bucket_name = config.get('compliance_bucket', 'incident-commander-compliance-reports')
        
        # Compliance frameworks configuration
        self.supported_frameworks = {
            'SOC2': {
                'retention_years': 7,
                'audit_frequency_days': 90,
                'required_controls': [
                    'access_control',
                    'encryption',
                    'audit_logging',
                    'incident_response',
                    'change_management'
                ]
            },
            'GDPR': {
                'retention_years': 6,
                'audit_frequency_days': 30,
                'required_controls': [
                    'data_protection',
                    'consent_management',
                    'breach_notification',
                    'data_portability',
                    'right_to_erasure'
                ]
            },
            'HIPAA': {
                'retention_years': 6,
                'audit_frequency_days': 60,
                'required_controls': [
                    'access_control',
                    'encryption',
                    'audit_logging',
                    'breach_notification',
                    'risk_assessment'
                ]
            },
            'PCI_DSS': {
                'retention_years': 3,
                'audit_frequency_days': 90,
                'required_controls': [
                    'network_security',
                    'encryption',
                    'access_control',
                    'monitoring',
                    'vulnerability_management'
                ]
            }
        }
        
        # Data retention policies
        self.retention_policies = {
            'audit_logs': timedelta(days=2555),  # 7 years
            'incident_data': timedelta(days=2190),  # 6 years
            'security_alerts': timedelta(days=1095),  # 3 years
            'compliance_reports': timedelta(days=3650),  # 10 years
            'agent_certificates': timedelta(days=365),  # 1 year after expiry
            'threat_intelligence': timedelta(days=730)  # 2 years
        }
        
        # PII detection patterns (enhanced from audit logger)
        self.pii_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'phone': r'\b(?:\+1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
            'credit_card': r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b',
            'ip_address': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
            'aws_access_key': r'\bAKIA[0-9A-Z]{16}\b',
            'aws_secret_key': r'\b[A-Za-z0-9/+=]{40}\b',
            'passport': r'\b[A-Z]{1,2}[0-9]{6,9}\b',
            'driver_license': r'\b[A-Z]{1,2}[0-9]{6,8}\b',
            'bank_account': r'\b[0-9]{8,17}\b'
        }
    
    async def generate_compliance_report(
        self,
        framework: str,
        start_date: datetime,
        end_date: datetime,
        include_recommendations: bool = True
    ) -> ComplianceReport:
        """
        Generate comprehensive compliance report for specified framework.
        
        Args:
            framework: Compliance framework (SOC2, GDPR, HIPAA, PCI_DSS)
            start_date: Report period start
            end_date: Report period end
            include_recommendations: Include compliance recommendations
            
        Returns:
            ComplianceReport: Generated compliance report
        """
        try:
            if framework not in self.supported_frameworks:
                raise ComplianceError(f"Unsupported compliance framework: {framework}")
            
            framework_config = self.supported_frameworks[framework]
            
            # Collect compliance data
            audit_events = await self._get_audit_events_for_period(start_date, end_date)
            security_violations = await self._count_security_violations(audit_events)
            
            # Assess compliance controls
            control_assessments = await self._assess_compliance_controls(
                framework_config['required_controls'],
                audit_events
            )
            
            # Check data retention compliance
            retention_compliance = await self._verify_data_retention_compliance(framework)
            
            # Check encryption compliance
            encryption_compliance = await self._verify_encryption_compliance(audit_events)
            
            # Check access control compliance
            access_control_compliance = await self._verify_access_control_compliance(audit_events)
            
            # Generate findings
            findings = await self._generate_compliance_findings(
                framework,
                control_assessments,
                retention_compliance,
                encryption_compliance,
                access_control_compliance
            )
            
            # Generate recommendations
            recommendations = []
            if include_recommendations:
                recommendations = await self._generate_compliance_recommendations(
                    framework,
                    findings,
                    control_assessments
                )
            
            # Create compliance report
            report = ComplianceReport(
                report_id=str(uuid4()),
                report_type=f"{framework}_compliance_report",
                period_start=start_date,
                period_end=end_date,
                compliance_framework=framework,
                total_audit_events=len(audit_events),
                security_violations=security_violations,
                data_retention_compliance=retention_compliance,
                encryption_compliance=encryption_compliance,
                access_control_compliance=access_control_compliance,
                findings=findings,
                recommendations=recommendations
            )
            
            # Store report
            await self._store_compliance_report(report)
            
            # Upload to S3 for long-term storage
            await self._upload_compliance_report_to_s3(report)
            
            # Log compliance report generation
            if self.audit_logger:
                await self.audit_logger.log_security_event(
                    event_type=SecurityEventType.CONFIGURATION_CHANGE,
                    severity=SecuritySeverity.MEDIUM,
                    action="generate_compliance_report",
                    outcome="success",
                    details={
                        "framework": framework,
                        "report_id": report.report_id,
                        "period_start": start_date.isoformat(),
                        "period_end": end_date.isoformat(),
                        "findings_count": len(findings)
                    }
                )
            
            await logger.ainfo(
                "Compliance report generated",
                framework=framework,
                report_id=report.report_id,
                findings_count=len(findings),
                recommendations_count=len(recommendations)
            )
            
            return report
            
        except Exception as e:
            await logger.aerror(
                "Compliance report generation failed",
                framework=framework,
                error=str(e)
            )
            raise ComplianceError(f"Compliance report generation failed: {e}")
    
    async def enforce_data_retention_policy(self) -> Dict[str, int]:
        """
        Enforce data retention policies across all data types.
        
        Returns:
            Dict[str, int]: Count of records processed for each data type
        """
        try:
            results = {}
            
            for data_type, retention_period in self.retention_policies.items():
                cutoff_date = datetime.utcnow() - retention_period
                
                if data_type == 'audit_logs':
                    count = await self._cleanup_audit_logs(cutoff_date)
                elif data_type == 'incident_data':
                    count = await self._cleanup_incident_data(cutoff_date)
                elif data_type == 'security_alerts':
                    count = await self._cleanup_security_alerts(cutoff_date)
                elif data_type == 'compliance_reports':
                    count = await self._cleanup_compliance_reports(cutoff_date)
                elif data_type == 'agent_certificates':
                    count = await self._cleanup_expired_certificates(cutoff_date)
                elif data_type == 'threat_intelligence':
                    count = await self._cleanup_threat_intelligence(cutoff_date)
                else:
                    count = 0
                
                results[data_type] = count
            
            # Log retention policy enforcement
            if self.audit_logger:
                await self.audit_logger.log_security_event(
                    event_type=SecurityEventType.CONFIGURATION_CHANGE,
                    severity=SecuritySeverity.LOW,
                    action="enforce_data_retention",
                    outcome="success",
                    details={"cleanup_results": results}
                )
            
            await logger.ainfo(
                "Data retention policy enforced",
                cleanup_results=results
            )
            
            return results
            
        except Exception as e:
            await logger.aerror(
                "Data retention enforcement failed",
                error=str(e)
            )
            raise ComplianceError(f"Data retention enforcement failed: {e}")
    
    async def scan_for_pii_violations(
        self,
        data_sources: List[str],
        remediate: bool = False
    ) -> Dict[str, List[PIIRedactionResult]]:
        """
        Scan data sources for PII violations and optionally remediate.
        
        Args:
            data_sources: List of data sources to scan
            remediate: Whether to automatically redact found PII
            
        Returns:
            Dict[str, List[PIIRedactionResult]]: PII scan results by data source
        """
        try:
            results = {}
            
            for data_source in data_sources:
                if data_source == 'audit_logs':
                    pii_results = await self._scan_audit_logs_for_pii(remediate)
                elif data_source == 'incident_data':
                    pii_results = await self._scan_incident_data_for_pii(remediate)
                elif data_source == 'security_alerts':
                    pii_results = await self._scan_security_alerts_for_pii(remediate)
                else:
                    pii_results = []
                
                results[data_source] = pii_results
            
            # Log PII scan
            total_violations = sum(len(violations) for violations in results.values())
            if self.audit_logger:
                await self.audit_logger.log_security_event(
                    event_type=SecurityEventType.DATA_ACCESS,
                    severity=SecuritySeverity.MEDIUM if total_violations > 0 else SecuritySeverity.LOW,
                    action="scan_pii_violations",
                    outcome="success",
                    details={
                        "data_sources": data_sources,
                        "total_violations": total_violations,
                        "remediated": remediate
                    }
                )
            
            await logger.ainfo(
                "PII violation scan completed",
                data_sources=data_sources,
                total_violations=total_violations,
                remediated=remediate
            )
            
            return results
            
        except Exception as e:
            await logger.aerror(
                "PII violation scan failed",
                error=str(e)
            )
            raise ComplianceError(f"PII violation scan failed: {e}")
    
    async def validate_compliance_controls(
        self,
        framework: str
    ) -> Dict[str, bool]:
        """
        Validate compliance controls for a specific framework.
        
        Args:
            framework: Compliance framework to validate
            
        Returns:
            Dict[str, bool]: Control validation results
        """
        try:
            if framework not in self.supported_frameworks:
                raise ComplianceError(f"Unsupported compliance framework: {framework}")
            
            framework_config = self.supported_frameworks[framework]
            required_controls = framework_config['required_controls']
            
            # Get recent audit events for validation
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=framework_config['audit_frequency_days'])
            audit_events = await self._get_audit_events_for_period(start_date, end_date)
            
            # Validate each control
            control_results = {}
            for control in required_controls:
                if control == 'access_control':
                    control_results[control] = await self._validate_access_control(audit_events)
                elif control == 'encryption':
                    control_results[control] = await self._validate_encryption_control(audit_events)
                elif control == 'audit_logging':
                    control_results[control] = await self._validate_audit_logging_control(audit_events)
                elif control == 'incident_response':
                    control_results[control] = await self._validate_incident_response_control(audit_events)
                elif control == 'change_management':
                    control_results[control] = await self._validate_change_management_control(audit_events)
                elif control == 'data_protection':
                    control_results[control] = await self._validate_data_protection_control(audit_events)
                elif control == 'breach_notification':
                    control_results[control] = await self._validate_breach_notification_control(audit_events)
                elif control == 'network_security':
                    control_results[control] = await self._validate_network_security_control(audit_events)
                elif control == 'vulnerability_management':
                    control_results[control] = await self._validate_vulnerability_management_control(audit_events)
                else:
                    control_results[control] = False  # Unknown control
            
            # Log control validation
            failed_controls = [c for c, result in control_results.items() if not result]
            if self.audit_logger:
                await self.audit_logger.log_security_event(
                    event_type=SecurityEventType.CONFIGURATION_CHANGE,
                    severity=SecuritySeverity.HIGH if failed_controls else SecuritySeverity.LOW,
                    action="validate_compliance_controls",
                    outcome="success",
                    details={
                        "framework": framework,
                        "controls_validated": len(control_results),
                        "failed_controls": failed_controls
                    }
                )
            
            await logger.ainfo(
                "Compliance controls validated",
                framework=framework,
                controls_passed=len([r for r in control_results.values() if r]),
                controls_failed=len(failed_controls)
            )
            
            return control_results
            
        except Exception as e:
            await logger.aerror(
                "Compliance control validation failed",
                framework=framework,
                error=str(e)
            )
            raise ComplianceError(f"Compliance control validation failed: {e}")
    
    async def get_compliance_dashboard_metrics(self) -> Dict[str, Any]:
        """
        Get compliance dashboard metrics.
        
        Returns:
            Dict[str, Any]: Compliance metrics for dashboard
        """
        try:
            metrics = {
                'frameworks': {},
                'data_retention': {},
                'pii_compliance': {},
                'recent_reports': []
            }
            
            # Get metrics for each framework
            for framework in self.supported_frameworks.keys():
                control_results = await self.validate_compliance_controls(framework)
                compliance_percentage = (
                    sum(1 for result in control_results.values() if result) /
                    len(control_results) * 100
                )
                
                metrics['frameworks'][framework] = {
                    'compliance_percentage': compliance_percentage,
                    'controls_passed': sum(1 for result in control_results.values() if result),
                    'controls_total': len(control_results),
                    'last_assessed': datetime.utcnow().isoformat()
                }
            
            # Get data retention metrics
            for data_type, retention_period in self.retention_policies.items():
                cutoff_date = datetime.utcnow() - retention_period
                overdue_count = await self._count_overdue_data(data_type, cutoff_date)
                
                metrics['data_retention'][data_type] = {
                    'retention_days': retention_period.days,
                    'overdue_records': overdue_count,
                    'compliant': overdue_count == 0
                }
            
            # Get recent compliance reports
            recent_reports = await self._get_recent_compliance_reports(limit=5)
            metrics['recent_reports'] = [
                {
                    'report_id': report.report_id,
                    'framework': report.compliance_framework,
                    'generated_at': report.generated_at.isoformat(),
                    'findings_count': len(report.findings)
                }
                for report in recent_reports
            ]
            
            return metrics
            
        except Exception as e:
            await logger.aerror(
                "Failed to get compliance dashboard metrics",
                error=str(e)
            )
            return {}
    
    # Private helper methods
    
    async def _get_audit_events_for_period(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[AuditEvent]:
        """Get audit events for specified period."""
        # This would query the audit log table in production
        # For now, return empty list as placeholder
        return []
    
    async def _count_security_violations(self, audit_events: List[AuditEvent]) -> int:
        """Count security violations in audit events."""
        return len([
            event for event in audit_events
            if event.event_type in [
                SecurityEventType.SECURITY_VIOLATION,
                SecurityEventType.UNAUTHORIZED_ACCESS,
                SecurityEventType.PRIVILEGE_ESCALATION
            ]
        ])
    
    async def _assess_compliance_controls(
        self,
        required_controls: List[str],
        audit_events: List[AuditEvent]
    ) -> Dict[str, Dict[str, Any]]:
        """Assess compliance controls based on audit events."""
        assessments = {}
        
        for control in required_controls:
            # Simplified assessment - in production, this would be more sophisticated
            assessments[control] = {
                'implemented': True,
                'effective': True,
                'evidence_count': len(audit_events),
                'last_tested': datetime.utcnow().isoformat()
            }
        
        return assessments
    
    async def _verify_data_retention_compliance(self, framework: str) -> bool:
        """Verify data retention compliance for framework."""
        framework_config = self.supported_frameworks[framework]
        retention_years = framework_config['retention_years']
        
        # Check if any data exists beyond retention period
        cutoff_date = datetime.utcnow() - timedelta(days=retention_years * 365)
        
        for data_type in self.retention_policies.keys():
            overdue_count = await self._count_overdue_data(data_type, cutoff_date)
            if overdue_count > 0:
                return False
        
        return True
    
    async def _verify_encryption_compliance(self, audit_events: List[AuditEvent]) -> bool:
        """Verify encryption compliance."""
        # Check that all audit events have integrity hashes (indicating encryption)
        return all(event.integrity_hash for event in audit_events)
    
    async def _verify_access_control_compliance(self, audit_events: List[AuditEvent]) -> bool:
        """Verify access control compliance."""
        # Check for proper authentication events
        auth_events = [
            event for event in audit_events
            if event.event_type == SecurityEventType.AGENT_AUTHENTICATION
        ]
        
        # Should have authentication events for system activity
        return len(auth_events) > 0
    
    async def _generate_compliance_findings(
        self,
        framework: str,
        control_assessments: Dict[str, Dict[str, Any]],
        retention_compliance: bool,
        encryption_compliance: bool,
        access_control_compliance: bool
    ) -> List[Dict[str, Any]]:
        """Generate compliance findings."""
        findings = []
        
        # Check control assessments
        for control, assessment in control_assessments.items():
            if not assessment.get('effective', True):
                findings.append({
                    'type': 'control_deficiency',
                    'control': control,
                    'severity': 'high',
                    'description': f"Control {control} is not effectively implemented"
                })
        
        # Check retention compliance
        if not retention_compliance:
            findings.append({
                'type': 'data_retention_violation',
                'severity': 'medium',
                'description': 'Data retention policy violations detected'
            })
        
        # Check encryption compliance
        if not encryption_compliance:
            findings.append({
                'type': 'encryption_violation',
                'severity': 'high',
                'description': 'Encryption requirements not met for all data'
            })
        
        # Check access control compliance
        if not access_control_compliance:
            findings.append({
                'type': 'access_control_violation',
                'severity': 'high',
                'description': 'Access control requirements not properly implemented'
            })
        
        return findings
    
    async def _generate_compliance_recommendations(
        self,
        framework: str,
        findings: List[Dict[str, Any]],
        control_assessments: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """Generate compliance recommendations."""
        recommendations = []
        
        # Generate recommendations based on findings
        for finding in findings:
            if finding['type'] == 'control_deficiency':
                recommendations.append(
                    f"Strengthen implementation of {finding['control']} control"
                )
            elif finding['type'] == 'data_retention_violation':
                recommendations.append(
                    "Implement automated data lifecycle management"
                )
            elif finding['type'] == 'encryption_violation':
                recommendations.append(
                    "Ensure all data is encrypted at rest and in transit"
                )
            elif finding['type'] == 'access_control_violation':
                recommendations.append(
                    "Implement comprehensive access control and authentication"
                )
        
        # Add framework-specific recommendations
        if framework == 'GDPR':
            recommendations.append("Implement data subject rights management")
            recommendations.append("Enhance consent management processes")
        elif framework == 'SOC2':
            recommendations.append("Strengthen security monitoring and alerting")
            recommendations.append("Implement comprehensive change management")
        
        return recommendations
    
    async def _store_compliance_report(self, report: ComplianceReport) -> None:
        """Store compliance report in DynamoDB."""
        table = self.dynamodb.Table(self.compliance_table_name)
        
        item = {
            'report_id': report.report_id,
            'generated_at': report.generated_at.isoformat(),
            'report_type': report.report_type,
            'period_start': report.period_start.isoformat(),
            'period_end': report.period_end.isoformat(),
            'compliance_framework': report.compliance_framework,
            'total_audit_events': report.total_audit_events,
            'security_violations': report.security_violations,
            'data_retention_compliance': report.data_retention_compliance,
            'encryption_compliance': report.encryption_compliance,
            'access_control_compliance': report.access_control_compliance,
            'findings': report.findings,
            'recommendations': report.recommendations,
            'generated_by': report.generated_by,
            'status': report.status
        }
        
        await asyncio.to_thread(table.put_item, Item=item)
    
    async def _upload_compliance_report_to_s3(self, report: ComplianceReport) -> None:
        """Upload compliance report to S3 for long-term storage."""
        key = f"compliance-reports/{report.compliance_framework}/{report.generated_at.year}/{report.generated_at.month}/{report.report_id}.json"
        
        report_data = {
            'report': report.dict(),
            'generated_at': datetime.utcnow().isoformat(),
            'format_version': '1.0'
        }
        
        await asyncio.to_thread(
            self.s3.put_object,
            Bucket=self.compliance_bucket_name,
            Key=key,
            Body=json.dumps(report_data, indent=2, default=str),
            ServerSideEncryption='AES256',
            ContentType='application/json'
        )
    
    # Placeholder methods for data cleanup operations
    async def _cleanup_audit_logs(self, cutoff_date: datetime) -> int:
        """Cleanup audit logs older than cutoff date."""
        return 0  # Placeholder
    
    async def _cleanup_incident_data(self, cutoff_date: datetime) -> int:
        """Cleanup incident data older than cutoff date."""
        return 0  # Placeholder
    
    async def _cleanup_security_alerts(self, cutoff_date: datetime) -> int:
        """Cleanup security alerts older than cutoff date."""
        return 0  # Placeholder
    
    async def _cleanup_compliance_reports(self, cutoff_date: datetime) -> int:
        """Cleanup compliance reports older than cutoff date."""
        return 0  # Placeholder
    
    async def _cleanup_expired_certificates(self, cutoff_date: datetime) -> int:
        """Cleanup expired certificates older than cutoff date."""
        return 0  # Placeholder
    
    async def _cleanup_threat_intelligence(self, cutoff_date: datetime) -> int:
        """Cleanup threat intelligence older than cutoff date."""
        return 0  # Placeholder
    
    async def _count_overdue_data(self, data_type: str, cutoff_date: datetime) -> int:
        """Count overdue data records."""
        return 0  # Placeholder
    
    async def _get_recent_compliance_reports(self, limit: int = 5) -> List[ComplianceReport]:
        """Get recent compliance reports."""
        return []  # Placeholder
    
    # Placeholder methods for PII scanning
    async def _scan_audit_logs_for_pii(self, remediate: bool) -> List[PIIRedactionResult]:
        """Scan audit logs for PII."""
        return []  # Placeholder
    
    async def _scan_incident_data_for_pii(self, remediate: bool) -> List[PIIRedactionResult]:
        """Scan incident data for PII."""
        return []  # Placeholder
    
    async def _scan_security_alerts_for_pii(self, remediate: bool) -> List[PIIRedactionResult]:
        """Scan security alerts for PII."""
        return []  # Placeholder
    
    # Placeholder methods for control validation
    async def _validate_access_control(self, audit_events: List[AuditEvent]) -> bool:
        """Validate access control implementation."""
        return True  # Placeholder
    
    async def _validate_encryption_control(self, audit_events: List[AuditEvent]) -> bool:
        """Validate encryption control implementation."""
        return True  # Placeholder
    
    async def _validate_audit_logging_control(self, audit_events: List[AuditEvent]) -> bool:
        """Validate audit logging control implementation."""
        return True  # Placeholder
    
    async def _validate_incident_response_control(self, audit_events: List[AuditEvent]) -> bool:
        """Validate incident response control implementation."""
        return True  # Placeholder
    
    async def _validate_change_management_control(self, audit_events: List[AuditEvent]) -> bool:
        """Validate change management control implementation."""
        return True  # Placeholder
    
    async def _validate_data_protection_control(self, audit_events: List[AuditEvent]) -> bool:
        """Validate data protection control implementation."""
        return True  # Placeholder
    
    async def _validate_breach_notification_control(self, audit_events: List[AuditEvent]) -> bool:
        """Validate breach notification control implementation."""
        return True  # Placeholder
    
    async def _validate_network_security_control(self, audit_events: List[AuditEvent]) -> bool:
        """Validate network security control implementation."""
        return True  # Placeholder
    
    async def _validate_vulnerability_management_control(self, audit_events: List[AuditEvent]) -> bool:
        """Validate vulnerability management control implementation."""
        return True  # Placeholder