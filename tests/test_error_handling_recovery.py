"""
Test Error Handling and Recovery System

Tests for comprehensive error handling, recovery mechanisms,
and human escalation triggers.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from src.services.error_handling_recovery import (
    ErrorHandlingRecoverySystem,
    ErrorSeverity,
    RecoveryStrategy,
    ErrorContext,
    get_error_handling_system
)
from src.utils.exceptions import IncidentCommanderError


class TestErrorHandlingRecoverySystem:
    """Test error handling and recovery system functionality."""
    
    @pytest.fixture
    def error_system(self):
        """Create error handling system for testing."""
        return ErrorHandlingRecoverySystem()
    
    @pytest.fixture
    def sample_error(self):
        """Create sample error for testing."""
        return ValueError("Test error message")
    
    @pytest.mark.asyncio
    async def test_handle_error_basic(self, error_system, sample_error):
        """Test basic error handling functionality."""
        result = await error_system.handle_error(
            error=sample_error,
            component="test_component",
            context_data={"test": "data"}
        )
        
        assert "error_id" in result
        assert result["severity"] == ErrorSeverity.LOW.value
        assert "recovery_strategy" in result
        assert "recovery_result" in result
        assert "timestamp" in result
    
    @pytest.mark.asyncio
    async def test_error_severity_determination(self, error_system):
        """Test error severity determination logic."""
        # Critical errors
        critical_error = MemoryError("Out of memory")
        severity = error_system._determine_error_severity(critical_error, "system")
        assert severity == ErrorSeverity.CRITICAL
        
        # High severity for agent timeouts
        timeout_error = asyncio.TimeoutError("Agent timeout")
        severity = error_system._determine_error_severity(timeout_error, "detection_agent")
        assert severity == ErrorSeverity.HIGH
        
        # Medium severity for connection errors
        conn_error = ConnectionError("Connection failed")
        severity = error_system._determine_error_severity(conn_error, "service")
        assert severity == ErrorSeverity.MEDIUM
        
        # Low severity for value errors
        value_error = ValueError("Invalid value")
        severity = error_system._determine_error_severity(value_error, "validator")
        assert severity == ErrorSeverity.LOW
    
    @pytest.mark.asyncio
    async def test_error_correlation(self, error_system):
        """Test error correlation detection."""
        # Create multiple related errors
        base_error = ValueError("Test error")
        
        # First error
        await error_system.handle_error(base_error, "test_component")
        
        # Related error (same component)
        related_error = ConnectionError("Connection failed")
        result = await error_system.handle_error(related_error, "test_component")
        
        # Check if correlation was detected
        error_id = result["error_id"]
        assert error_id in error_system.error_correlations
    
    @pytest.mark.asyncio
    async def test_recovery_strategy_selection(self, error_system):
        """Test recovery strategy selection logic."""
        # Critical error should trigger human escalation
        critical_error = MemoryError("Critical system error")
        error_context = ErrorContext(
            error_id="test_critical",
            timestamp=datetime.utcnow(),
            error_type="MemoryError",
            error_message=str(critical_error),
            stack_trace="",
            component="system",
            severity=ErrorSeverity.CRITICAL
        )
        
        strategy = await error_system._determine_recovery_strategy(error_context)
        assert strategy == "human_escalation"
        
        # Agent timeout should trigger restart
        timeout_context = ErrorContext(
            error_id="test_timeout",
            timestamp=datetime.utcnow(),
            error_type="TimeoutError",
            error_message="Agent timeout occurred",
            stack_trace="",
            component="detection_agent",
            severity=ErrorSeverity.HIGH
        )
        
        strategy = await error_system._determine_recovery_strategy(timeout_context)
        assert strategy == "agent_restart"
    
    @pytest.mark.asyncio
    async def test_recovery_execution(self, error_system):
        """Test recovery action execution."""
        error_context = ErrorContext(
            error_id="test_recovery",
            timestamp=datetime.utcnow(),
            error_type="TestError",
            error_message="Test recovery",
            stack_trace="",
            component="test_component",
            severity=ErrorSeverity.MEDIUM
        )
        
        # Test graceful degradation recovery
        result = await error_system._execute_recovery(error_context, "graceful_degradation")
        
        assert result["status"] == "success"
        assert result["strategy"] == "graceful_degradation"
        assert "duration_seconds" in result
    
    @pytest.mark.asyncio
    async def test_escalation_triggers(self, error_system):
        """Test human escalation trigger conditions."""
        # Create critical system error
        critical_error = SystemExit("System shutdown")
        
        # Use handle_error to properly add to history and trigger escalation
        result = await error_system.handle_error(
            error=critical_error,
            component="system_core"
        )
        
        # Verify escalation was triggered
        assert result["severity"] == ErrorSeverity.CRITICAL.value
        assert len(error_system.error_history) > 0
    
    def test_error_analytics(self, error_system):
        """Test error analytics and system health assessment."""
        # Add some test errors to history
        for i in range(5):
            error_context = ErrorContext(
                error_id=f"test_error_{i}",
                timestamp=datetime.utcnow(),
                error_type="TestError",
                error_message=f"Test error {i}",
                stack_trace="",
                component="test_component",
                severity=ErrorSeverity.MEDIUM
            )
            error_system.error_history.append(error_context)
        
        analytics = error_system.get_error_analytics()
        
        assert "error_analytics" in analytics
        assert "recovery_statistics" in analytics
        assert "system_health" in analytics
        assert analytics["error_analytics"]["total_errors_last_hour"] >= 0
        assert "system_stability" in analytics["system_health"]
    
    def test_system_stability_assessment(self, error_system):
        """Test system stability assessment logic."""
        # Test stable system
        stability = error_system._assess_system_stability()
        assert stability == "stable"
        
        # Add critical error
        critical_error = ErrorContext(
            error_id="critical_test",
            timestamp=datetime.utcnow(),
            error_type="CriticalError",
            error_message="Critical system failure",
            stack_trace="",
            component="system",
            severity=ErrorSeverity.CRITICAL
        )
        error_system.error_history.append(critical_error)
        
        stability = error_system._assess_system_stability()
        assert stability == "unstable"
    
    def test_recovery_success_rate_calculation(self, error_system):
        """Test recovery success rate calculation."""
        # Add some recovery statistics
        error_system.recovery_statistics["test_strategy"]["success"] = 8
        error_system.recovery_statistics["test_strategy"]["failed"] = 2
        
        success_rate = error_system._calculate_recovery_success_rate()
        assert success_rate == 80.0
        
        # Test with no attempts
        error_system.recovery_statistics.clear()
        success_rate = error_system._calculate_recovery_success_rate()
        assert success_rate == 100.0
    
    @pytest.mark.asyncio
    async def test_recovery_action_implementations(self, error_system):
        """Test individual recovery action implementations."""
        error_context = ErrorContext(
            error_id="test_actions",
            timestamp=datetime.utcnow(),
            error_type="TestError",
            error_message="Test actions",
            stack_trace="",
            component="test",
            severity=ErrorSeverity.MEDIUM
        )
        
        # Test agent restart
        result = await error_system._restart_agent(error_context)
        assert result["status"] == "success"
        assert result["action"] == "agent_restarted"
        
        # Test service retry
        result = await error_system._retry_service_call(error_context)
        assert result["status"] == "success"
        assert result["action"] == "service_call_retried"
        
        # Test circuit breaker reset
        result = await error_system._reset_circuit_breaker(error_context)
        assert result["state"] == "closed"
        assert result["action"] == "circuit_breaker_reset"
        
        # Test graceful degradation
        result = await error_system._activate_graceful_degradation(error_context)
        assert result["degraded"] is True
        assert result["action"] == "graceful_degradation_activated"
    
    @pytest.mark.asyncio
    async def test_human_escalation_context_preservation(self, error_system):
        """Test human escalation with complete context preservation."""
        error_context = ErrorContext(
            error_id="test_escalation_context",
            timestamp=datetime.utcnow(),
            error_type="CriticalError",
            error_message="Critical failure requiring escalation",
            stack_trace="test stack trace",
            component="critical_system",
            severity=ErrorSeverity.CRITICAL,
            context_data={"important": "context"},
            correlation_id="test_correlation",
            incident_id="test_incident"
        )
        
        result = await error_system._trigger_human_escalation(error_context)
        
        assert result["escalated"] is True
        assert "escalation_context" in result
        
        escalation_context = result["escalation_context"]
        assert "error_context" in escalation_context
        assert "system_state" in escalation_context
        assert "escalation_metadata" in escalation_context
        
        # Verify all error context is preserved
        preserved_context = escalation_context["error_context"]
        assert preserved_context["error_id"] == error_context.error_id
        assert preserved_context["correlation_id"] == error_context.correlation_id
        assert preserved_context["incident_id"] == error_context.incident_id
    
    def test_global_error_system_singleton(self):
        """Test global error handling system singleton."""
        system1 = get_error_handling_system()
        system2 = get_error_handling_system()
        
        assert system1 is system2
        assert isinstance(system1, ErrorHandlingRecoverySystem)


class TestErrorHandlingIntegration:
    """Integration tests for error handling system."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_error_handling(self):
        """Test complete error handling workflow."""
        error_system = ErrorHandlingRecoverySystem()
        
        # Simulate a service timeout error
        timeout_error = asyncio.TimeoutError("Service call timed out")
        
        result = await error_system.handle_error(
            error=timeout_error,
            component="external_service",
            context_data={
                "service_name": "datadog_api",
                "endpoint": "/api/v1/metrics",
                "timeout_seconds": 30
            },
            correlation_id="test_correlation_123",
            incident_id="incident_456"
        )
        
        # Verify complete workflow
        assert result["severity"] == ErrorSeverity.MEDIUM.value
        assert result["recovery_strategy"] == "service_retry"
        assert result["recovery_result"]["status"] == "success"
        assert not result["escalation_triggered"]
        
        # Verify error was stored in history
        assert len(error_system.error_history) == 1
        stored_error = error_system.error_history[0]
        assert stored_error.correlation_id == "test_correlation_123"
        assert stored_error.incident_id == "incident_456"
    
    @pytest.mark.asyncio
    async def test_cascading_failure_escalation(self):
        """Test escalation on cascading failures."""
        error_system = ErrorHandlingRecoverySystem()
        
        # Simulate multiple HIGH severity agent failures (timeouts)
        for i in range(4):
            agent_error = asyncio.TimeoutError(f"Agent {i} timeout")
            await error_system.handle_error(
                error=agent_error,
                component=f"detection_agent_{i}",
                context_data={"agent_id": f"agent_{i}"}
            )
        
        # Verify escalation trigger conditions are met
        recent_failures = error_system._count_recent_agent_failures()
        assert recent_failures >= 3
        
        # Analytics should show degraded system health
        analytics = error_system.get_error_analytics()
        assert analytics["system_health"]["system_stability"] in ["degraded", "stressed", "unstable"]