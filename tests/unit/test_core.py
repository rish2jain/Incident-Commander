"""Test core package initialization and constants."""

import pytest
from src import __version__, __author__
from src.utils.constants import (
    CONSENSUS_CONFIG,
    CIRCUIT_BREAKER_CONFIG,
    PERFORMANCE_TARGETS,
    RATE_LIMITS,
    SHARED_RETRY_POLICIES,
    RESOURCE_LIMITS,
    AGENT_DEPENDENCY_ORDER,
    RetryPolicy
)


def test_package_metadata():
    """Test package version and author are defined."""
    assert __version__ == "0.1.0"
    assert __author__ == "Incident Commander Team"


def test_consensus_config():
    """Test consensus configuration values."""
    assert CONSENSUS_CONFIG["autonomous_confidence_threshold"] == 0.7
    assert abs(sum(CONSENSUS_CONFIG["agent_weights"].values()) - 1.0) < 1e-10
    assert CONSENSUS_CONFIG["decision_timeout"] == 300


def test_circuit_breaker_config():
    """Test circuit breaker configuration."""
    assert CIRCUIT_BREAKER_CONFIG["failure_threshold"] == 5
    assert CIRCUIT_BREAKER_CONFIG["timeout"] == 30
    assert CIRCUIT_BREAKER_CONFIG["success_threshold"] == 2


def test_performance_targets():
    """Test performance targets are reasonable."""
    for agent, targets in PERFORMANCE_TARGETS.items():
        assert targets["max"] > targets["target"]
        assert targets["target"] > 0
        assert targets["max"] <= 300  # No agent should take more than 5 minutes


def test_retry_policies():
    """Test retry policies are properly configured."""
    for agent, policy in SHARED_RETRY_POLICIES.items():
        assert isinstance(policy, RetryPolicy)
        assert policy.max_retries > 0
        assert policy.timeout > 0
        assert policy.get_delay(0) == policy.base_delay
        assert policy.get_delay(1) == policy.base_delay * 2


def test_agent_dependency_order():
    """Test agent dependency ordering is logical."""
    assert AGENT_DEPENDENCY_ORDER["detection"] == 0  # First
    assert AGENT_DEPENDENCY_ORDER["communication"] == 3  # Last
    assert AGENT_DEPENDENCY_ORDER["diagnosis"] > AGENT_DEPENDENCY_ORDER["detection"]
    assert AGENT_DEPENDENCY_ORDER["resolution"] > AGENT_DEPENDENCY_ORDER["diagnosis"]


def test_resource_limits():
    """Test resource limits are sensible."""
    assert 0 < RESOURCE_LIMITS["memory_threshold"] < 1
    assert RESOURCE_LIMITS["alert_buffer_size"] > 0
    assert RESOURCE_LIMITS["log_analysis_limit"] > 0
    assert RESOURCE_LIMITS["correlation_depth"] > 0