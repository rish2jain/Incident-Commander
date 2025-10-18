"""
Circuit breaker interface for resilient agent communication.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable, Any, Optional, Dict, List
from datetime import datetime, timedelta


class CircuitBreakerState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, blocking calls
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerStats:
    """Circuit breaker statistics."""
    
    def __init__(self):
        """Initialize stats."""
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_success_time: Optional[datetime] = None
        self.state_changes = 0
        self.current_state = CircuitBreakerState.CLOSED
    
    @property
    def failure_rate(self) -> float:
        """Calculate current failure rate."""
        if self.total_calls == 0:
            return 0.0
        return self.failed_calls / self.total_calls
    
    @property
    def success_rate(self) -> float:
        """Calculate current success rate."""
        if self.total_calls == 0:
            return 1.0
        return self.successful_calls / self.total_calls
    
    def record_success(self) -> None:
        """Record a successful call."""
        self.total_calls += 1
        self.successful_calls += 1
        self.last_success_time = datetime.utcnow()
    
    def record_failure(self) -> None:
        """Record a failed call."""
        self.total_calls += 1
        self.failed_calls += 1
        self.last_failure_time = datetime.utcnow()
    
    def record_state_change(self, new_state: CircuitBreakerState) -> None:
        """Record a state change."""
        self.current_state = new_state
        self.state_changes += 1


class CircuitBreaker(ABC):
    """Abstract circuit breaker interface."""
    
    def __init__(self, name: str, failure_threshold: int = 5, 
                 timeout_seconds: int = 30, success_threshold: int = 2):
        """
        Initialize circuit breaker.
        
        Args:
            name: Name of the circuit breaker
            failure_threshold: Number of failures before opening
            timeout_seconds: Seconds to wait before trying half-open
            success_threshold: Successes needed to close from half-open
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout = timedelta(seconds=timeout_seconds)
        self.success_threshold = success_threshold
        self.stats = CircuitBreakerStats()
        self._state = CircuitBreakerState.CLOSED
        self._last_failure_time: Optional[datetime] = None
        self._half_open_successes = 0
    
    @property
    def state(self) -> CircuitBreakerState:
        """Get current circuit breaker state."""
        return self._state
    
    @abstractmethod
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit breaker is open
        """
        pass
    
    @abstractmethod
    def can_execute(self) -> bool:
        """
        Check if execution is allowed based on current state.
        
        Returns:
            True if execution is allowed
        """
        pass
    
    @abstractmethod
    def record_success(self) -> None:
        """Record a successful execution."""
        pass
    
    @abstractmethod
    def record_failure(self) -> None:
        """Record a failed execution."""
        pass
    
    @abstractmethod
    def get_stats(self) -> CircuitBreakerStats:
        """
        Get circuit breaker statistics.
        
        Returns:
            Current statistics
        """
        pass
    
    @abstractmethod
    def reset(self) -> None:
        """Reset circuit breaker to closed state."""
        pass


class AgentCircuitBreaker(CircuitBreaker):
    """Circuit breaker specifically for agent communication."""
    
    @abstractmethod
    async def call_agent(self, agent_func: Callable, *args, **kwargs) -> Any:
        """
        Call agent function with circuit breaker protection.
        
        Args:
            agent_func: Agent function to call
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Agent function result
            
        Raises:
            CircuitBreakerOpenError: If circuit breaker is open
            AgentTimeoutError: If agent call times out
        """
        pass
    
    @abstractmethod
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get agent health status based on circuit breaker state.
        
        Returns:
            Health status information
        """
        pass


class CircuitBreakerManager(ABC):
    """Manager for multiple circuit breakers."""
    
    @abstractmethod
    def get_circuit_breaker(self, name: str) -> CircuitBreaker:
        """
        Get or create circuit breaker by name.
        
        Args:
            name: Circuit breaker name
            
        Returns:
            Circuit breaker instance
        """
        pass
    
    @abstractmethod
    def get_all_stats(self) -> Dict[str, CircuitBreakerStats]:
        """
        Get statistics for all circuit breakers.
        
        Returns:
            Dictionary mapping names to stats
        """
        pass
    
    @abstractmethod
    def reset_all(self) -> None:
        """Reset all circuit breakers."""
        pass
    
    @abstractmethod
    def get_unhealthy_services(self) -> List[str]:
        """
        Get list of services with open circuit breakers.
        
        Returns:
            List of unhealthy service names
        """
        pass