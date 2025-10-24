"""
Comprehensive Error Handling and Recovery

Provides graceful degradation strategies, automatic recovery mechanisms,
human escalation triggers, and system-wide error logging.

Task 13.3: Add comprehensive error handling and recovery
"""

import asyncio
import json
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Type
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict

from src.utils.logging import get_logger
from src.utils.exceptions import IncidentCommanderError


logger = get_logger("error_handling_recovery")


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecoveryStrategy(Enum):
    """Recovery strategy types."""
    RETRY = "retry"
    FALLBACK = "fallback"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    CIRCUIT_BREAKER = "circuit_breaker"
    HUMAN_ESCALATION = "human_escalation"
    SYSTEM_RESTART = "system_restart"


@dataclass
class ErrorContext:
    """Comprehensive error context for analysis and recovery."""
    error_id: str
    timestamp: datetime
    error_type: str
    error_message: str
    stack_trace: str
    component: str
    severity: ErrorSeverity
    context_data: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    incident_id: Optional[str] = None


@dataclass
class RecoveryAction:
    """Recovery action definition."""
    action_id: str
    strategy: RecoveryStrategy
    action_function: Callable
    max_attempts: int
    timeout_seconds: int
    success_criteria: Callable[[Any], bool]
    fallback_action: Optional['RecoveryAction'] = None


@dataclass
class EscalationTrigger:
    """Human escalation trigger configuration."""
    trigger_id: str
    conditions: List[Callable[[ErrorContext], bool]]
    escalation_level: str
    notification_channels: List[str]
    context_preservation: bool = True
    auto_escalation_delay: timedelta = timedelta(minutes=5)


class ErrorHandlingRecoverySystem:
    """
    Comprehensive error handling and recovery system.
    
    Provides graceful degradation, automatic recovery, human escalation,
    and system-wide error correlation for maximum resilience.
    """
    
    def __init__(self):
        self.error_history: List[ErrorContext] = []
        self.recovery_actions: Dict[str, RecoveryAction] = {}
        self.escalation_triggers: Dict[str, EscalationTrigger] = {}
        self.error_correlations: Dict[str, List[str]] = defaultdict(list)
        self.recovery_statistics: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.active_recoveries: Dict[str, Dict[str, Any]] = {}
        self._initialize_recovery_actions()
        self._initialize_escalation_triggers()
        
    def _initialize_recovery_actions(self):
        """Initialize standard recovery actions."""
        # Agent failure recovery
        self.recovery_actions["agent_restart"] = RecoveryAction(
            action_id="agent_restart",
            strategy=RecoveryStrategy.RETRY,
            action_function=self._restart_agent,
            max_attempts=3,
            timeout_seconds=30,
            success_criteria=lambda result: result.get("status") == "success"
        )
        
        # Service timeout recovery
        self.recovery_actions["service_retry"] = RecoveryAction(
            action_id="service_retry",
            strategy=RecoveryStrategy.RETRY,
            action_function=self._retry_service_call,
            max_attempts=5,
            timeout_seconds=60,
            success_criteria=lambda result: result is not None
        )
        
        # Circuit breaker recovery
        self.recovery_actions["circuit_breaker_reset"] = RecoveryAction(
            action_id="circuit_breaker_reset",
            strategy=RecoveryStrategy.CIRCUIT_BREAKER,
            action_function=self._reset_circuit_breaker,
            max_attempts=1,
            timeout_seconds=10,
            success_criteria=lambda result: result.get("state") == "closed"
        )
        
        # Graceful degradation
        self.recovery_actions["graceful_degradation"] = RecoveryAction(
            action_id="graceful_degradation",
            strategy=RecoveryStrategy.GRACEFUL_DEGRADATION,
            action_function=self._activate_graceful_degradation,
            max_attempts=1,
            timeout_seconds=5,
            success_criteria=lambda result: result.get("degraded") is True
        )
        
        # Human escalation
        self.recovery_actions["human_escalation"] = RecoveryAction(
            action_id="human_escalation",
            strategy=RecoveryStrategy.HUMAN_ESCALATION,
            action_function=self._trigger_human_escalation,
            max_attempts=1,
            timeout_seconds=30,
            success_criteria=lambda result: result.get("escalated") is True
        )
    
    def _initialize_escalation_triggers(self):
        """Initialize escalation triggers for human intervention."""
        # Critical system failure
        self.escalation_triggers["critical_system_failure"] = EscalationTrigger(
            trigger_id="critical_system_failure",
            conditions=[
                lambda ctx: ctx.severity == ErrorSeverity.CRITICAL,
                lambda ctx: "system" in ctx.component.lower()
            ],
            escalation_level="senior_sre",
            notification_channels=["pagerduty", "slack", "email"],
            auto_escalation_delay=timedelta(minutes=1)
        )
        
        # Multiple agent failures
        self.escalation_triggers["multiple_agent_failures"] = EscalationTrigger(
            trigger_id="multiple_agent_failures",
            conditions=[
                lambda ctx: self._count_recent_agent_failures() >= 3
            ],
            escalation_level="incident_commander",
            notification_channels=["pagerduty", "slack"],
            auto_escalation_delay=timedelta(minutes=2)
        )
        
        # Recovery failure cascade
        self.escalation_triggers["recovery_failure_cascade"] = EscalationTrigger(
            trigger_id="recovery_failure_cascade",
            conditions=[
                lambda ctx: self._count_failed_recoveries() >= 5
            ],
            escalation_level="engineering_manager",
            notification_channels=["pagerduty", "slack", "email"],
            auto_escalation_delay=timedelta(minutes=3)
        )
    
    async def handle_error(
        self, 
        error: Exception, 
        component: str,
        context_data: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        incident_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle error with comprehensive recovery and escalation.
        
        Returns recovery result and actions taken.
        """
        # Create error context
        error_context = ErrorContext(
            error_id=f"error_{int(datetime.utcnow().timestamp())}_{hash(str(error)) % 10000}",
            timestamp=datetime.utcnow(),
            error_type=type(error).__name__,
            error_message=str(error),
            stack_trace=traceback.format_exc(),
            component=component,
            severity=self._determine_error_severity(error, component),
            context_data=context_data or {},
            correlation_id=correlation_id,
            incident_id=incident_id
        )
        
        # Store error for analysis
        self.error_history.append(error_context)
        
        # Correlate with recent errors
        await self._correlate_error(error_context)
        
        # Log error with full context
        self._log_error_with_context(error_context)
        
        # Determine recovery strategy
        recovery_strategy = await self._determine_recovery_strategy(error_context)
        
        # Execute recovery
        recovery_result = await self._execute_recovery(error_context, recovery_strategy)
        
        # Check escalation triggers
        await self._check_escalation_triggers(error_context)
        
        return {
            "error_id": error_context.error_id,
            "severity": error_context.severity.value,
            "recovery_strategy": recovery_strategy,
            "recovery_result": recovery_result,
            "escalation_triggered": recovery_result.get("escalation_triggered", False),
            "timestamp": error_context.timestamp.isoformat()
        }
    
    def _determine_error_severity(self, error: Exception, component: str) -> ErrorSeverity:
        """Determine error severity based on error type and component."""
        # Critical errors
        if isinstance(error, (SystemExit, KeyboardInterrupt, MemoryError)):
            return ErrorSeverity.CRITICAL
        
        # Component-based severity
        if "agent" in component.lower():
            if isinstance(error, (TimeoutError, asyncio.TimeoutError)):
                return ErrorSeverity.HIGH
            elif isinstance(error, ConnectionError):
                return ErrorSeverity.MEDIUM
        
        if "consensus" in component.lower() or "coordinator" in component.lower():
            return ErrorSeverity.HIGH
        
        if "database" in component.lower() or "storage" in component.lower():
            return ErrorSeverity.HIGH
        
        # Default severity based on error type
        if isinstance(error, (ValueError, TypeError, AttributeError)):
            return ErrorSeverity.LOW
        elif isinstance(error, (ConnectionError, TimeoutError)):
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.MEDIUM
    
    async def _correlate_error(self, error_context: ErrorContext):
        """Correlate error with recent errors for pattern detection."""
        recent_errors = [
            err for err in self.error_history[-50:]  # Last 50 errors
            if (datetime.utcnow() - err.timestamp).total_seconds() < 300  # Last 5 minutes
        ]
        
        # Find correlations
        correlations = []
        for recent_error in recent_errors:
            if recent_error.error_id == error_context.error_id:
                continue
                
            # Same component correlation
            if recent_error.component == error_context.component:
                correlations.append(recent_error.error_id)
            
            # Same error type correlation
            if recent_error.error_type == error_context.error_type:
                correlations.append(recent_error.error_id)
            
            # Same incident correlation
            if (recent_error.incident_id and error_context.incident_id and 
                recent_error.incident_id == error_context.incident_id):
                correlations.append(recent_error.error_id)
        
        if correlations:
            self.error_correlations[error_context.error_id] = correlations
            logger.warning(f"Error correlation detected: {error_context.error_id} correlated with {len(correlations)} recent errors")
    
    def _log_error_with_context(self, error_context: ErrorContext):
        """Log error with comprehensive context information."""
        log_data = {
            "error_id": error_context.error_id,
            "timestamp": error_context.timestamp.isoformat(),
            "error_type": error_context.error_type,
            "error_message": error_context.error_message,
            "component": error_context.component,
            "severity": error_context.severity.value,
            "correlation_id": error_context.correlation_id,
            "incident_id": error_context.incident_id,
            "context_data": error_context.context_data,
            "correlations": self.error_correlations.get(error_context.error_id, [])
        }
        
        # Log at appropriate level based on severity
        if error_context.severity == ErrorSeverity.CRITICAL:
            logger.critical(f"CRITICAL ERROR: {json.dumps(log_data, indent=2)}")
        elif error_context.severity == ErrorSeverity.HIGH:
            logger.error(f"HIGH SEVERITY ERROR: {json.dumps(log_data, indent=2)}")
        elif error_context.severity == ErrorSeverity.MEDIUM:
            logger.warning(f"MEDIUM SEVERITY ERROR: {json.dumps(log_data, indent=2)}")
        else:
            logger.info(f"LOW SEVERITY ERROR: {json.dumps(log_data, indent=2)}")
    
    async def _determine_recovery_strategy(self, error_context: ErrorContext) -> str:
        """Determine appropriate recovery strategy based on error context."""
        # Critical errors require immediate escalation
        if error_context.severity == ErrorSeverity.CRITICAL:
            return "human_escalation"
        
        # Component-specific strategies
        if "agent" in error_context.component.lower():
            if "timeout" in error_context.error_message.lower():
                return "agent_restart"
            else:
                return "graceful_degradation"
        
        if "service" in error_context.component.lower():
            return "service_retry"
        
        if "circuit_breaker" in error_context.component.lower():
            return "circuit_breaker_reset"
        
        # Check for error patterns
        correlations = self.error_correlations.get(error_context.error_id, [])
        if len(correlations) >= 3:
            return "human_escalation"
        
        # Default to graceful degradation
        return "graceful_degradation"
    
    async def _execute_recovery(
        self, 
        error_context: ErrorContext, 
        strategy: str
    ) -> Dict[str, Any]:
        """Execute recovery action with monitoring and fallback."""
        if strategy not in self.recovery_actions:
            logger.error(f"Unknown recovery strategy: {strategy}")
            return {"status": "failed", "reason": "unknown_strategy"}
        
        recovery_action = self.recovery_actions[strategy]
        recovery_id = f"recovery_{error_context.error_id}_{strategy}"
        
        # Track active recovery
        self.active_recoveries[recovery_id] = {
            "error_context": error_context,
            "recovery_action": recovery_action,
            "start_time": datetime.utcnow(),
            "attempts": 0
        }
        
        try:
            # Execute recovery with retries
            for attempt in range(recovery_action.max_attempts):
                self.active_recoveries[recovery_id]["attempts"] = attempt + 1
                
                try:
                    # Execute recovery action with timeout
                    result = await asyncio.wait_for(
                        recovery_action.action_function(error_context),
                        timeout=recovery_action.timeout_seconds
                    )
                    
                    # Check success criteria
                    if recovery_action.success_criteria(result):
                        # Recovery successful
                        self.recovery_statistics[strategy]["success"] += 1
                        
                        recovery_result = {
                            "status": "success",
                            "strategy": strategy,
                            "attempts": attempt + 1,
                            "result": result,
                            "duration_seconds": (datetime.utcnow() - self.active_recoveries[recovery_id]["start_time"]).total_seconds()
                        }
                        
                        logger.info(f"Recovery successful: {recovery_id} after {attempt + 1} attempts")
                        return recovery_result
                    
                except Exception as recovery_error:
                    logger.warning(f"Recovery attempt {attempt + 1} failed for {recovery_id}: {recovery_error}")
                    
                    if attempt < recovery_action.max_attempts - 1:
                        # Wait before retry with exponential backoff
                        await asyncio.sleep(2 ** attempt)
            
            # All attempts failed
            self.recovery_statistics[strategy]["failed"] += 1
            
            # Try fallback if available
            if recovery_action.fallback_action:
                logger.info(f"Attempting fallback recovery for {recovery_id}")
                return await self._execute_recovery(error_context, recovery_action.fallback_action.action_id)
            
            return {
                "status": "failed",
                "strategy": strategy,
                "attempts": recovery_action.max_attempts,
                "reason": "max_attempts_exceeded"
            }
            
        finally:
            # Clean up active recovery tracking
            if recovery_id in self.active_recoveries:
                del self.active_recoveries[recovery_id]
    
    async def _check_escalation_triggers(self, error_context: ErrorContext):
        """Check if error should trigger human escalation."""
        for trigger_id, trigger in self.escalation_triggers.items():
            # Check all conditions
            if all(condition(error_context) for condition in trigger.conditions):
                logger.critical(f"Escalation trigger activated: {trigger_id}")
                
                # Schedule escalation with delay
                asyncio.create_task(
                    self._schedule_escalation(error_context, trigger)
                )
    
    async def _schedule_escalation(self, error_context: ErrorContext, trigger: EscalationTrigger):
        """Schedule human escalation with auto-escalation delay."""
        # Wait for auto-escalation delay
        await asyncio.sleep(trigger.auto_escalation_delay.total_seconds())
        
        # Execute escalation
        escalation_result = await self._trigger_human_escalation(error_context)
        
        logger.critical(f"Human escalation executed: {trigger.trigger_id} for error {error_context.error_id}")
    
    # Recovery action implementations
    async def _restart_agent(self, error_context: ErrorContext) -> Dict[str, Any]:
        """Restart failed agent."""
        # Simulate agent restart
        await asyncio.sleep(1)
        return {"status": "success", "action": "agent_restarted"}
    
    async def _retry_service_call(self, error_context: ErrorContext) -> Dict[str, Any]:
        """Retry failed service call."""
        # Simulate service retry
        await asyncio.sleep(0.5)
        return {"status": "success", "action": "service_call_retried"}
    
    async def _reset_circuit_breaker(self, error_context: ErrorContext) -> Dict[str, Any]:
        """Reset circuit breaker to closed state."""
        # Simulate circuit breaker reset
        return {"state": "closed", "action": "circuit_breaker_reset"}
    
    async def _activate_graceful_degradation(self, error_context: ErrorContext) -> Dict[str, Any]:
        """Activate graceful degradation mode."""
        # Simulate graceful degradation activation
        return {"degraded": True, "action": "graceful_degradation_activated"}
    
    async def _trigger_human_escalation(self, error_context: ErrorContext) -> Dict[str, Any]:
        """Trigger human escalation with complete context preservation."""
        escalation_context = {
            "error_context": {
                "error_id": error_context.error_id,
                "timestamp": error_context.timestamp.isoformat(),
                "error_type": error_context.error_type,
                "error_message": error_context.error_message,
                "component": error_context.component,
                "severity": error_context.severity.value,
                "context_data": error_context.context_data,
                "correlation_id": error_context.correlation_id,
                "incident_id": error_context.incident_id
            },
            "system_state": {
                "recent_errors": len([
                    err for err in self.error_history[-10:]
                    if (datetime.utcnow() - err.timestamp).total_seconds() < 300
                ]),
                "active_recoveries": len(self.active_recoveries),
                "recovery_statistics": dict(self.recovery_statistics)
            },
            "escalation_metadata": {
                "escalation_time": datetime.utcnow().isoformat(),
                "escalation_reason": "automatic_trigger",
                "context_preserved": True
            }
        }
        
        # Log escalation with full context
        logger.critical(f"HUMAN ESCALATION TRIGGERED: {json.dumps(escalation_context, indent=2)}")
        
        return {"escalated": True, "escalation_context": escalation_context}
    
    # Helper methods for escalation conditions
    def _count_recent_agent_failures(self) -> int:
        """Count recent agent failures for escalation trigger."""
        recent_time = datetime.utcnow() - timedelta(minutes=5)
        return len([
            err for err in self.error_history
            if (err.timestamp > recent_time and 
                "agent" in err.component.lower() and
                err.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL])
        ])
    
    def _count_failed_recoveries(self) -> int:
        """Count recent failed recoveries for escalation trigger."""
        return sum(
            stats["failed"] for stats in self.recovery_statistics.values()
        )
    
    def get_error_analytics(self) -> Dict[str, Any]:
        """Get comprehensive error analytics and system health."""
        recent_time = datetime.utcnow() - timedelta(hours=1)
        recent_errors = [err for err in self.error_history if err.timestamp > recent_time]
        
        error_by_severity = defaultdict(int)
        error_by_component = defaultdict(int)
        error_by_type = defaultdict(int)
        
        for error in recent_errors:
            error_by_severity[error.severity.value] += 1
            error_by_component[error.component] += 1
            error_by_type[error.error_type] += 1
        
        return {
            "error_analytics": {
                "total_errors_last_hour": len(recent_errors),
                "errors_by_severity": dict(error_by_severity),
                "errors_by_component": dict(error_by_component),
                "errors_by_type": dict(error_by_type),
                "error_correlations": len(self.error_correlations),
                "active_recoveries": len(self.active_recoveries)
            },
            "recovery_statistics": dict(self.recovery_statistics),
            "system_health": {
                "error_rate_last_hour": len(recent_errors),
                "recovery_success_rate": self._calculate_recovery_success_rate(),
                "escalation_rate": self._calculate_escalation_rate(),
                "system_stability": self._assess_system_stability()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _calculate_recovery_success_rate(self) -> float:
        """Calculate overall recovery success rate."""
        total_attempts = sum(
            stats["success"] + stats["failed"] 
            for stats in self.recovery_statistics.values()
        )
        total_successes = sum(
            stats["success"] 
            for stats in self.recovery_statistics.values()
        )
        
        return (total_successes / total_attempts * 100) if total_attempts > 0 else 100.0
    
    def _calculate_escalation_rate(self) -> float:
        """Calculate escalation rate."""
        recent_time = datetime.utcnow() - timedelta(hours=1)
        recent_errors = [err for err in self.error_history if err.timestamp > recent_time]
        escalations = sum(
            1 for err in recent_errors 
            if err.severity == ErrorSeverity.CRITICAL
        )
        
        return (escalations / len(recent_errors) * 100) if recent_errors else 0.0
    
    def _assess_system_stability(self) -> str:
        """Assess overall system stability."""
        recent_time = datetime.utcnow() - timedelta(minutes=30)
        recent_errors = [err for err in self.error_history if err.timestamp > recent_time]
        
        critical_errors = sum(1 for err in recent_errors if err.severity == ErrorSeverity.CRITICAL)
        high_errors = sum(1 for err in recent_errors if err.severity == ErrorSeverity.HIGH)
        
        if critical_errors > 0:
            return "unstable"
        elif high_errors > 3:
            return "degraded"
        elif len(recent_errors) > 10:
            return "stressed"
        else:
            return "stable"


# Global error handling and recovery system instance
_error_handling_system = None


def get_error_handling_system() -> ErrorHandlingRecoverySystem:
    """Get the global error handling and recovery system instance."""
    global _error_handling_system
    if _error_handling_system is None:
        _error_handling_system = ErrorHandlingRecoverySystem()
    return _error_handling_system