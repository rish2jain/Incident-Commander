"""
Circuit breaker implementation for resilient agent communication.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Callable, Any, Dict, List
from enum import Enum

from src.interfaces.circuit_breaker import (
    CircuitBreaker, AgentCircuitBreaker, CircuitBreakerManager,
    CircuitBreakerState, CircuitBreakerStats
)
from src.utils.constants import CIRCUIT_BREAKER_CONFIG
from src.utils.logging import get_logger
from src.utils.exceptions import CircuitBreakerOpenError, AgentTimeoutError


logger = get_logger("circuit_breaker")


class ResilientCircuitBreaker(CircuitBreaker):
    """Circuit breaker implementation with configurable thresholds."""
    
    def __init__(self, name: str, failure_threshold: int = None, 
                 timeout_seconds: int = None, success_threshold: int = None):
        """Initialize circuit breaker with configuration from constants."""
        config = CIRCUIT_BREAKER_CONFIG
        super().__init__(
            name=name,
            failure_threshold=failure_threshold or config["failure_threshold"],
            timeout_seconds=timeout_seconds or config["timeout"],
            success_threshold=success_threshold or config["success_threshold"]
        )
        self._consecutive_failures = 0
        self._consecutive_successes = 0
        self._last_state_change = datetime.utcnow()
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        if not self.can_execute():
            raise CircuitBreakerOpenError(
                f"Circuit breaker {self.name} is open. "
                f"Retry after {self.timeout.total_seconds()}s"
            )
        
        try:
            # Execute the function
            result = await func(*args, **kwargs)
            self.record_success()
            return result
            
        except Exception as e:
            self.record_failure()
            raise e
    
    def can_execute(self) -> bool:
        """Check if execution is allowed based on current state."""
        current_time = datetime.utcnow()
        
        if self._state == CircuitBreakerState.CLOSED:
            return True
        
        elif self._state == CircuitBreakerState.OPEN:
            # Check if timeout period has passed
            if current_time - self._last_failure_time >= self.timeout:
                self._transition_to_half_open()
                return True
            return False
        
        elif self._state == CircuitBreakerState.HALF_OPEN:
            return True
        
        return False
    
    def record_success(self) -> None:
        """Record a successful execution."""
        self.stats.record_success()
        self._consecutive_failures = 0
        
        if self._state == CircuitBreakerState.HALF_OPEN:
            self._consecutive_successes += 1
            if self._consecutive_successes >= self.success_threshold:
                self._transition_to_closed()
        
        logger.debug(f"Circuit breaker {self.name}: Success recorded")
    
    def record_failure(self) -> None:
        """Record a failed execution."""
        self.stats.record_failure()
        self._consecutive_successes = 0
        self._consecutive_failures += 1
        
        if self._state == CircuitBreakerState.CLOSED:
            if self._consecutive_failures >= self.failure_threshold:
                self._transition_to_open()
        
        elif self._state == CircuitBreakerState.HALF_OPEN:
            self._transition_to_open()
        
        logger.warning(f"Circuit breaker {self.name}: Failure recorded ({self._consecutive_failures}/{self.failure_threshold})")
    
    def _transition_to_open(self) -> None:
        """Transition to OPEN state."""
        self._state = CircuitBreakerState.OPEN
        self._last_failure_time = datetime.utcnow()
        self._last_state_change = datetime.utcnow()
        self.stats.record_state_change(self._state)
        logger.warning(f"Circuit breaker {self.name} opened due to {self._consecutive_failures} consecutive failures")
    
    def _transition_to_half_open(self) -> None:
        """Transition to HALF_OPEN state."""
        self._state = CircuitBreakerState.HALF_OPEN
        self._consecutive_successes = 0
        self._last_state_change = datetime.utcnow()
        self.stats.record_state_change(self._state)
        logger.info(f"Circuit breaker {self.name} transitioned to half-open")
    
    def _transition_to_closed(self) -> None:
        """Transition to CLOSED state."""
        self._state = CircuitBreakerState.CLOSED
        self._consecutive_failures = 0
        self._consecutive_successes = 0
        self._last_state_change = datetime.utcnow()
        self.stats.record_state_change(self._state)
        logger.info(f"Circuit breaker {self.name} closed after {self.success_threshold} successes")
    
    def get_stats(self) -> CircuitBreakerStats:
        """Get circuit breaker statistics."""
        return self.stats
    
    def reset(self) -> None:
        """Reset circuit breaker to closed state."""
        self._state = CircuitBreakerState.CLOSED
        self._consecutive_failures = 0
        self._consecutive_successes = 0
        self._last_failure_time = None
        self._last_state_change = datetime.utcnow()
        self.stats = CircuitBreakerStats()
        logger.info(f"Circuit breaker {self.name} reset to closed state")


class AgentCircuitBreakerImpl(ResilientCircuitBreaker, AgentCircuitBreaker):
    """Circuit breaker specifically for agent communication."""
    
    def __init__(self, agent_name: str):
        """Initialize agent circuit breaker."""
        super().__init__(f"agent_{agent_name}")
        self.agent_name = agent_name
        self._call_timeout = 30  # 30 second timeout for agent calls
    
    async def call_agent(self, agent_func: Callable, *args, **kwargs) -> Any:
        """Call agent function with circuit breaker protection and timeout."""
        if not self.can_execute():
            raise CircuitBreakerOpenError(
                f"Agent {self.agent_name} circuit breaker is open. "
                f"Service may be unhealthy."
            )
        
        try:
            # Add timeout to agent call
            result = await asyncio.wait_for(
                agent_func(*args, **kwargs),
                timeout=self._call_timeout
            )
            self.record_success()
            return result
            
        except asyncio.TimeoutError:
            self.record_failure()
            raise AgentTimeoutError(f"Agent {self.agent_name} call timed out after {self._call_timeout}s")
        
        except Exception as e:
            self.record_failure()
            raise e
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get agent health status based on circuit breaker state."""
        stats = self.get_stats()
        
        health_status = {
            "agent_name": self.agent_name,
            "circuit_breaker_state": self._state.value,
            "is_healthy": self._state != CircuitBreakerState.OPEN,
            "failure_rate": stats.failure_rate,
            "success_rate": stats.success_rate,
            "total_calls": stats.total_calls,
            "consecutive_failures": self._consecutive_failures,
            "last_failure": stats.last_failure_time.isoformat() if stats.last_failure_time else None,
            "last_success": stats.last_success_time.isoformat() if stats.last_success_time else None,
            "state_changes": stats.state_changes
        }
        
        # Add health recommendations
        if self._state == CircuitBreakerState.OPEN:
            health_status["recommendation"] = "Service is unhealthy. Check agent logs and dependencies."
        elif stats.failure_rate > 0.5:
            health_status["recommendation"] = "Service is degraded. Monitor closely."
        else:
            health_status["recommendation"] = "Service is healthy."
        
        return health_status


class CircuitBreakerManagerImpl(CircuitBreakerManager):
    """Manager for multiple circuit breakers."""
    
    def __init__(self):
        """Initialize circuit breaker manager."""
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._agent_circuit_breakers: Dict[str, AgentCircuitBreaker] = {}
    
    def get_circuit_breaker(self, name: str) -> CircuitBreaker:
        """Get or create circuit breaker by name."""
        if name not in self._circuit_breakers:
            self._circuit_breakers[name] = ResilientCircuitBreaker(name)
            logger.info(f"Created circuit breaker: {name}")
        
        return self._circuit_breakers[name]
    
    def get_agent_circuit_breaker(self, agent_name: str) -> AgentCircuitBreaker:
        """Get or create agent circuit breaker."""
        if agent_name not in self._agent_circuit_breakers:
            self._agent_circuit_breakers[agent_name] = AgentCircuitBreakerImpl(agent_name)
            logger.info(f"Created agent circuit breaker: {agent_name}")
        
        return self._agent_circuit_breakers[agent_name]
    
    def get_all_stats(self) -> Dict[str, CircuitBreakerStats]:
        """Get statistics for all circuit breakers."""
        all_stats = {}
        
        for name, cb in self._circuit_breakers.items():
            all_stats[name] = cb.get_stats()
        
        for agent_name, cb in self._agent_circuit_breakers.items():
            all_stats[f"agent_{agent_name}"] = cb.get_stats()
        
        return all_stats
    
    def reset_all(self) -> None:
        """Reset all circuit breakers."""
        for cb in self._circuit_breakers.values():
            cb.reset()
        
        for cb in self._agent_circuit_breakers.values():
            cb.reset()
        
        logger.info("Reset all circuit breakers")
    
    def get_unhealthy_services(self) -> List[str]:
        """Get list of services with open circuit breakers."""
        unhealthy = []
        
        for name, cb in self._circuit_breakers.items():
            if cb.state == CircuitBreakerState.OPEN:
                unhealthy.append(name)
        
        for agent_name, cb in self._agent_circuit_breakers.items():
            if cb.state == CircuitBreakerState.OPEN:
                unhealthy.append(f"agent_{agent_name}")
        
        return unhealthy
    
    def get_health_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive health dashboard data."""
        dashboard = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_circuit_breakers": len(self._circuit_breakers) + len(self._agent_circuit_breakers),
            "healthy_services": 0,
            "degraded_services": 0,
            "unhealthy_services": 0,
            "services": {}
        }
        
        # Process regular circuit breakers
        for name, cb in self._circuit_breakers.items():
            stats = cb.get_stats()
            service_info = {
                "state": cb.state.value,
                "failure_rate": stats.failure_rate,
                "total_calls": stats.total_calls,
                "last_failure": stats.last_failure_time.isoformat() if stats.last_failure_time else None
            }
            
            if cb.state == CircuitBreakerState.OPEN:
                dashboard["unhealthy_services"] += 1
                service_info["status"] = "unhealthy"
            elif stats.failure_rate > 0.3:
                dashboard["degraded_services"] += 1
                service_info["status"] = "degraded"
            else:
                dashboard["healthy_services"] += 1
                service_info["status"] = "healthy"
            
            dashboard["services"][name] = service_info
        
        # Process agent circuit breakers
        for agent_name, cb in self._agent_circuit_breakers.items():
            health_status = cb.get_health_status()
            service_name = f"agent_{agent_name}"
            
            if not health_status["is_healthy"]:
                dashboard["unhealthy_services"] += 1
            elif health_status["failure_rate"] > 0.3:
                dashboard["degraded_services"] += 1
            else:
                dashboard["healthy_services"] += 1
            
            dashboard["services"][service_name] = health_status
        
        return dashboard


# Global circuit breaker manager instance
circuit_breaker_manager = CircuitBreakerManagerImpl()