"""
Security Integration for Error Handling System

Provides security event logging for error handling and recovery operations,
integrating the security service with the error handling recovery system.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any

from src.services.security_service import get_security_service
from src.services.error_handling_recovery import (
    ErrorHandlingRecoverySystem, 
    ErrorContext, 
    ErrorSeverity as ErrorHandlingSeverity
)
from src.models.security import SecurityEventType, SecuritySeverity
from src.utils.logging import get_logger


logger = get_logger("security_error_integration")


class SecurityAwareErrorHandler:
    """
    Security-aware error handler that integrates security logging
    with the error handling and recovery system.
    """
    
    def __init__(self):
        self.security_service = get_security_service()
        self.error_handler = ErrorHandlingRecoverySystem()
        
    async def handle_error_with_security_logging(
        self,
        error: Exception,
        component: str,
        context_data: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        incident_id: Optional[str] = None,
        agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle error with comprehensive security logging.
        
        Integrates error handling with security audit trail.
        """
        # Handle error through standard error handling system
        error_result = await self.error_handler.handle_error(
            error=error,
            component=component,
            context_data=context_data,
            correlation_id=correlation_id,
            incident_id=incident_id
        )
        
        # Determine security severity based on error handling severity
        security_severity = self._map_error_severity_to_security(
            ErrorHandlingSeverity(error_result["severity"])
        )
        
        # Log security event for error occurrence
        await self.security_service.log_security_event(
            event_type=self._determine_security_event_type(error, component),
            severity=security_severity,
            action="handle_error",
            outcome=error_result["recovery_result"]["status"],
            agent_id=agent_id,
            resource=component,
            details={
                "error_id": error_result["error_id"],
                "error_type": type(error).__name__,
                "error_message": str(error),
                "recovery_strategy": error_result["recovery_strategy"],
                "escalation_triggered": error_result["escalation_triggered"],
                "correlation_id": correlation_id,
                "incident_id": incident_id,
                "context_data": context_data or {}
            }
        )
        
        # Log additional security events for specific error types
        await self._log_specialized_security_events(
            error, component, error_result, agent_id
        )
        
        return error_result
    
    def _map_error_severity_to_security(
        self, 
        error_severity: ErrorHandlingSeverity
    ) -> SecuritySeverity:
        """Map error handling severity to security severity."""
        mapping = {
            ErrorHandlingSeverity.LOW: SecuritySeverity.LOW,
            ErrorHandlingSeverity.MEDIUM: SecuritySeverity.MEDIUM,
            ErrorHandlingSeverity.HIGH: SecuritySeverity.HIGH,
            ErrorHandlingSeverity.CRITICAL: SecuritySeverity.CRITICAL
        }
        return mapping.get(error_severity, SecuritySeverity.MEDIUM)
    
    def _determine_security_event_type(
        self, 
        error: Exception, 
        component: str
    ) -> SecurityEventType:
        """Determine appropriate security event type based on error and component."""
        # Agent-related errors
        if "agent" in component.lower():
            if isinstance(error, (TimeoutError, asyncio.TimeoutError)):
                return SecurityEventType.SUSPICIOUS_BEHAVIOR
            elif isinstance(error, (PermissionError, ValueError)):
                return SecurityEventType.AGENT_AUTHORIZATION
            else:
                return SecurityEventType.AGENT_AUTHENTICATION
        
        # Security-related errors
        if isinstance(error, PermissionError):
            return SecurityEventType.UNAUTHORIZED_ACCESS
        elif isinstance(error, (ConnectionError, TimeoutError)):
            return SecurityEventType.SECURITY_VIOLATION
        elif "config" in component.lower():
            return SecurityEventType.CONFIGURATION_CHANGE
        else:
            return SecurityEventType.SECURITY_VIOLATION
    
    async def _log_specialized_security_events(
        self,
        error: Exception,
        component: str,
        error_result: Dict[str, Any],
        agent_id: Optional[str]
    ):
        """Log specialized security events for specific error scenarios."""
        
        # Agent timeout or failure - potential security concern
        if agent_id and isinstance(error, (TimeoutError, asyncio.TimeoutError)):
            await self.security_service.detect_agent_anomaly(
                agent_id=agent_id,
                anomaly_indicators=["timeout_error", "unresponsive_behavior"],
                confidence_score=0.7
            )
        
        # Multiple consecutive failures - potential compromise
        if error_result["recovery_strategy"] == "human_escalation":
            await self.security_service.log_security_event(
                event_type=SecurityEventType.SECURITY_VIOLATION,
                severity=SecuritySeverity.HIGH,
                action="escalate_error",
                outcome="escalated",
                agent_id=agent_id,
                resource=component,
                details={
                    "escalation_reason": "multiple_recovery_failures",
                    "error_type": type(error).__name__,
                    "component": component
                }
            )
        
        # Configuration or privilege-related errors
        if isinstance(error, PermissionError):
            await self.security_service.log_security_event(
                event_type=SecurityEventType.PRIVILEGE_ESCALATION,
                severity=SecuritySeverity.HIGH,
                action="permission_denied",
                outcome="blocked",
                agent_id=agent_id,
                resource=component,
                details={
                    "attempted_action": str(error),
                    "component": component
                }
            )
    
    async def log_recovery_action_security(
        self,
        recovery_action: str,
        component: str,
        outcome: str,
        agent_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log security event for recovery actions."""
        # Determine severity based on recovery action type
        high_risk_actions = ["agent_restart", "system_restart", "human_escalation"]
        severity = (SecuritySeverity.HIGH if recovery_action in high_risk_actions 
                   else SecuritySeverity.MEDIUM)
        
        await self.security_service.log_security_event(
            event_type=SecurityEventType.CONFIGURATION_CHANGE,
            severity=severity,
            action=f"recovery_{recovery_action}",
            outcome=outcome,
            agent_id=agent_id,
            resource=component,
            details=details or {}
        )
    
    async def validate_recovery_action_security(
        self,
        recovery_action: str,
        component: str,
        agent_id: Optional[str] = None
    ) -> bool:
        """Validate recovery action from security perspective."""
        # Check if agent has valid certificate for security-sensitive actions
        if agent_id and recovery_action in ["agent_restart", "system_restart"]:
            is_valid = await self.security_service.validate_agent_certificate(agent_id)
            if not is_valid:
                await self.security_service.log_security_event(
                    event_type=SecurityEventType.UNAUTHORIZED_ACCESS,
                    severity=SecuritySeverity.HIGH,
                    action="validate_recovery_action",
                    outcome="denied",
                    agent_id=agent_id,
                    resource=component,
                    details={
                        "recovery_action": recovery_action,
                        "denial_reason": "invalid_certificate"
                    }
                )
                return False
        
        # Log successful validation
        await self.security_service.log_security_event(
            event_type=SecurityEventType.AGENT_AUTHORIZATION,
            severity=SecuritySeverity.LOW,
            action="validate_recovery_action",
            outcome="approved",
            agent_id=agent_id,
            resource=component,
            details={"recovery_action": recovery_action}
        )
        
        return True
    
    async def get_security_error_metrics(self) -> Dict[str, Any]:
        """Get security metrics related to error handling."""
        security_metrics = await self.security_service.get_security_metrics()
        error_analytics = self.error_handler.get_error_analytics()
        
        return {
            "security_metrics": {
                "security_events_total": security_metrics.security_events_total,
                "security_violations": security_metrics.security_events_by_severity.get("high", 0) + 
                                     security_metrics.security_events_by_severity.get("critical", 0),
                "suspicious_behaviors": security_metrics.suspicious_behaviors_detected,
                "potential_compromises": security_metrics.potential_compromises_detected
            },
            "error_metrics": {
                "total_errors": error_analytics["error_analytics"]["total_errors_last_hour"],
                "recovery_success_rate": error_analytics["system_health"]["recovery_success_rate"],
                "escalation_rate": error_analytics["system_health"]["escalation_rate"],
                "system_stability": error_analytics["system_health"]["system_stability"]
            },
            "integrated_metrics": {
                "security_error_correlation": self._calculate_security_error_correlation(
                    security_metrics, error_analytics
                ),
                "risk_assessment": self._assess_security_risk_from_errors(
                    security_metrics, error_analytics
                )
            }
        }
    
    def _calculate_security_error_correlation(
        self, 
        security_metrics, 
        error_analytics
    ) -> float:
        """Calculate correlation between security events and system errors."""
        security_events = security_metrics.security_events_total
        system_errors = error_analytics["error_analytics"]["total_errors_last_hour"]
        
        if system_errors == 0:
            return 0.0
        
        # Simple correlation: ratio of security events to total errors
        correlation = min(1.0, security_events / system_errors)
        return round(correlation, 3)
    
    def _assess_security_risk_from_errors(
        self, 
        security_metrics, 
        error_analytics
    ) -> str:
        """Assess overall security risk based on error patterns."""
        # High risk indicators
        if (security_metrics.potential_compromises_detected > 0 or
            error_analytics["system_health"]["system_stability"] == "unstable"):
            return "high"
        
        # Medium risk indicators
        if (security_metrics.suspicious_behaviors_detected > 2 or
            error_analytics["system_health"]["escalation_rate"] > 20):
            return "medium"
        
        # Low risk
        if error_analytics["system_health"]["recovery_success_rate"] > 90:
            return "low"
        
        return "medium"


# Global security-aware error handler instance
_security_error_handler = None


def get_security_error_handler() -> SecurityAwareErrorHandler:
    """Get the global security-aware error handler instance."""
    global _security_error_handler
    if _security_error_handler is None:
        _security_error_handler = SecurityAwareErrorHandler()
    return _security_error_handler