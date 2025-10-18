"""
Unit tests for constants and configuration management.
"""

import pytest
from src.utils.constants import (
    AGENT_CONFIG,
    CONSENSUS_CONFIG,
    PERFORMANCE_TARGETS,
    RESOURCE_LIMITS,
    CIRCUIT_BREAKER_CONFIG,
    SHARED_RETRY_POLICIES,
    RetryPolicy
)


class TestConstants:
    """Test cases for configuration constants."""
    
    def test_agent_config_structure(self):
        """Test agent configuration has expected structure."""
        required_agents = ["detection", "resolution", "diagnosis", "prediction", "communication"]
        
        for agent in required_agents:
            assert agent in AGENT_CONFIG, f"Missing config for {agent} agent"
            assert isinstance(AGENT_CONFIG[agent], dict)
    
    def test_detection_agent_config(self):
        """Test detection agent configuration."""
        config = AGENT_CONFIG["detection"]
        
        assert "max_alert_rate" in config
        assert "alert_sampling_threshold" in config
        assert "correlation_timeout" in config
        assert "simple_grouping_fallback" in config
        
        assert isinstance(config["max_alert_rate"], int)
        assert 0.0 <= config["alert_sampling_threshold"] <= 1.0
        assert config["correlation_timeout"] > 0
        assert isinstance(config["simple_grouping_fallback"], bool)
    
    def test_resolution_agent_config(self):
        """Test resolution agent configuration."""
        config = AGENT_CONFIG["resolution"]
        
        assert "max_concurrent_actions" in config
        assert "target_resolution_time_minutes" in config
        assert "max_processing_time_minutes" in config
        assert "require_approval_for_high_risk" in config
        assert "sandbox_validation_enabled" in config
        
        assert config["max_concurrent_actions"] > 0
        assert config["target_resolution_time_minutes"] > 0
        assert config["max_processing_time_minutes"] > config["target_resolution_time_minutes"]
        assert isinstance(config["require_approval_for_high_risk"], bool)
        assert isinstance(config["sandbox_validation_enabled"], bool)
    
    def test_consensus_config(self):
        """Test consensus configuration."""
        assert "agent_weights" in CONSENSUS_CONFIG
        assert "autonomous_confidence_threshold" in CONSENSUS_CONFIG
        
        weights = CONSENSUS_CONFIG["agent_weights"]
        assert abs(sum(weights.values()) - 1.0) < 0.01  # Should sum to ~1.0
        
        threshold = CONSENSUS_CONFIG["autonomous_confidence_threshold"]
        assert 0.0 <= threshold <= 1.0
    
    def test_performance_targets(self):
        """Test performance targets configuration."""
        required_agents = ["detection", "diagnosis", "prediction", "resolution", "communication"]
        
        for agent in required_agents:
            assert agent in PERFORMANCE_TARGETS
            config = PERFORMANCE_TARGETS[agent]
            
            assert "target" in config
            assert "max" in config
            assert config["target"] > 0
            assert config["max"] > config["target"]
    
    def test_circuit_breaker_config(self):
        """Test circuit breaker configuration."""
        assert "failure_threshold" in CIRCUIT_BREAKER_CONFIG
        assert "timeout" in CIRCUIT_BREAKER_CONFIG
        assert "success_threshold" in CIRCUIT_BREAKER_CONFIG
        
        assert CIRCUIT_BREAKER_CONFIG["failure_threshold"] > 0
        assert CIRCUIT_BREAKER_CONFIG["timeout"] > 0
        assert CIRCUIT_BREAKER_CONFIG["success_threshold"] > 0
    
    def test_retry_policies(self):
        """Test retry policies configuration."""
        for agent_name, policy in SHARED_RETRY_POLICIES.items():
            assert isinstance(policy, RetryPolicy)
            assert policy.max_retries > 0
            assert policy.timeout > 0
            assert policy.base_delay > 0
    
    def test_retry_policy_delay_calculation(self):
        """Test retry policy delay calculation."""
        policy = RetryPolicy(max_retries=3, timeout=30, base_delay=1.0)
        
        # Test exponential backoff
        assert policy.get_delay(0) == 1.0
        assert policy.get_delay(1) == 2.0
        assert policy.get_delay(2) == 4.0
        assert policy.get_delay(3) == 8.0
    
    def test_resource_limits(self):
        """Test resource limits configuration."""
        assert "memory_threshold" in RESOURCE_LIMITS
        assert "alert_buffer_size" in RESOURCE_LIMITS
        assert "correlation_depth" in RESOURCE_LIMITS
        
        assert 0.0 <= RESOURCE_LIMITS["memory_threshold"] <= 1.0
        assert RESOURCE_LIMITS["alert_buffer_size"] > 0
        assert RESOURCE_LIMITS["correlation_depth"] > 0
    
    def test_config_consistency(self):
        """Test configuration consistency across different sections."""
        # Performance targets should align with agent configs
        detection_target = PERFORMANCE_TARGETS["detection"]["max"]
        detection_timeout = AGENT_CONFIG["detection"]["correlation_timeout"]
        
        # Correlation timeout should be less than max processing time
        assert detection_timeout < detection_target
        
        # Resolution timeouts should be consistent
        resolution_config = AGENT_CONFIG["resolution"]
        resolution_target = resolution_config["target_resolution_time_minutes"] * 60
        resolution_max = resolution_config["max_processing_time_minutes"] * 60
        
        perf_target = PERFORMANCE_TARGETS["resolution"]["target"]
        perf_max = PERFORMANCE_TARGETS["resolution"]["max"]
        
        assert resolution_target == perf_target
        assert resolution_max == perf_max