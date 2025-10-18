"""
Custom exceptions for the Incident Commander system.
"""


class IncidentCommanderError(Exception):
    """Base exception for all Incident Commander errors."""
    pass


class ConfigurationError(IncidentCommanderError):
    """Raised when configuration is invalid or missing."""
    pass


class AgentError(IncidentCommanderError):
    """Base exception for agent-related errors."""
    pass


class AgentTimeoutError(AgentError):
    """Raised when an agent operation times out."""
    pass


class AgentCommunicationError(AgentError):
    """Raised when agent communication fails."""
    pass


class CircuitBreakerOpenError(AgentError):
    """Raised when circuit breaker is open."""
    pass


class ConsensusError(IncidentCommanderError):
    """Base exception for consensus-related errors."""
    pass


class ConsensusTimeoutError(ConsensusError):
    """Raised when consensus cannot be reached within timeout."""
    pass


class InsufficientConfidenceError(ConsensusError):
    """Raised when consensus confidence is below threshold."""
    pass


class ByzantineFaultError(ConsensusError):
    """Raised when Byzantine fault is detected."""
    pass


class ByzantineAttackDetectedError(ByzantineFaultError):
    """Raised when a Byzantine attack is detected."""
    pass


class EventStoreError(IncidentCommanderError):
    """Base exception for event store errors."""
    pass


class OptimisticLockException(EventStoreError):
    """Raised when concurrent writers conflict on event store updates."""
    pass


class EventCorruptionError(EventStoreError):
    """Raised when event corruption is detected."""
    pass


class SecurityError(IncidentCommanderError):
    """Base exception for security-related errors."""
    pass


class AuthenticationError(SecurityError):
    """Raised when authentication fails."""
    pass


class AuthorizationError(SecurityError):
    """Raised when authorization fails."""
    pass


class ValidationError(SecurityError):
    """Raised when input validation fails."""
    pass


class ComplianceError(SecurityError):
    """Raised when compliance operations fail."""
    pass


class RateLimitError(IncidentCommanderError):
    """Raised when rate limit is exceeded."""
    pass


class ResourceLimitError(IncidentCommanderError):
    """Raised when resource limits are exceeded."""
    pass


class MemoryPressureError(ResourceLimitError):
    """Raised when memory pressure exceeds limits."""
    pass


class AllActionsFailed(IncidentCommanderError):
    """Raised when all fallback actions have failed."""
    pass


class HumanEscalationRequired(IncidentCommanderError):
    """Raised when human intervention is required."""
    pass


class MessageBusError(IncidentCommanderError):
    """Base exception for message bus errors."""
    pass


class MessageDeliveryError(MessageBusError):
    """Raised when message delivery fails."""
    pass


class CommunicationError(IncidentCommanderError):
    """Raised when communication operations fail."""
    pass


class ScalingError(IncidentCommanderError):
    """Raised when scaling operations fail."""
    pass


class PerformanceOptimizationError(IncidentCommanderError):
    """Raised when performance optimization operations fail."""
    pass


class CostOptimizationError(IncidentCommanderError):
    """Raised when cost optimization operations fail."""
    pass