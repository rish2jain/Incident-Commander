"""
Shared Operational Constants

Canonical values referenced across orchestrator code, agents, and documentation.
All runtime services should load these constants to stay synchronized.
"""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class RetryPolicy:
    """Retry policy configuration."""
    max_retries: int
    timeout: int
    base_delay: float = 1.0
    
    def get_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay."""
        return self.base_delay * (2 ** attempt)


# Consensus Configuration
CONSENSUS_CONFIG = {
    "agent_weights": {
        "detection": 0.2,
        "diagnosis": 0.4,
        "prediction": 0.3,
        "resolution": 0.1
        # Note: Communication agent (0.0 weight) is non-voting - not included in consensus
    },
    "autonomous_confidence_threshold": 0.85,  # Byzantine consensus threshold
    "decision_timeout": 300  # 5 minutes
}

# Circuit Breaker Configuration
CIRCUIT_BREAKER_CONFIG = {
    "failure_threshold": 5,
    "timeout": 30,  # seconds
    "success_threshold": 2  # for half-open to closed transition
}

# Performance Targets (seconds)
PERFORMANCE_TARGETS = {
    "detection": {"target": 30, "max": 60},
    "diagnosis": {"target": 120, "max": 180},
    "prediction": {"target": 90, "max": 150},
    "resolution": {"target": 180, "max": 300},
    "communication": {"target": 10, "max": 30}
}

# Rate Limits (requests per time period)
RATE_LIMITS = {
    "slack": {"requests": 1, "period": 1},  # 1/sec
    "pagerduty": {"requests": 2, "period": 60},  # 2/min
    "email": {"requests": 10, "period": 1},  # 10/sec
    "datadog": {"requests": 20, "period": 1},  # 20/sec
    "bedrock": {"requests": 100, "period": 60}  # 100/min
}

# Shared Retry Policies
SHARED_RETRY_POLICIES: Dict[str, RetryPolicy] = {
    "detection": RetryPolicy(max_retries=3, timeout=30),
    "diagnosis": RetryPolicy(max_retries=3, timeout=60),
    "prediction": RetryPolicy(max_retries=3, timeout=45),
    "resolution": RetryPolicy(max_retries=2, timeout=120),
    "communication": RetryPolicy(max_retries=5, timeout=15)
}

# Memory and Resource Limits
RESOURCE_LIMITS = {
    "memory_threshold": 0.8,  # 80% memory usage threshold
    "alert_buffer_size": 1000,  # Maximum alerts in buffer
    "log_analysis_limit": 100 * 1024 * 1024,  # 100MB
    "correlation_depth": 5,  # Maximum correlation depth
    "checkpoint_interval": 300  # 5 minutes
}

# Agent Dependency Ordering
AGENT_DEPENDENCY_ORDER = {
    "detection": 0,      # First responder
    "diagnosis": 1,      # Depends on detection
    "prediction": 1,     # Parallel to diagnosis
    "resolution": 2,     # Depends on diagnosis/prediction
    "communication": 3   # Final step
}

# Learning and Knowledge Management
LEARNING_CONFIG = {
    "min_confidence_threshold": 0.6,
    "learning_rate": 0.1,
    "pattern_discovery_threshold": 3,  # Min incidents to form pattern
    "validation_window_days": 30,
    "checkpoint_cadence_minutes": 15,
    "knowledge_retention_days": 2555,  # 7 years for compliance
    "embedding_dimension": 1536,  # Bedrock Titan embedding size
    "similarity_threshold": 0.7,
    "max_vector_cache_size": 1000,
    "data_quality_threshold": 0.6
}

# Security and Compliance
SECURITY_CONFIG = {
    "credential_rotation_hours": 12,
    "audit_log_retention_days": 2555,  # 7 years
    "session_timeout_minutes": 60,
    "max_failed_auth_attempts": 5,
    "encryption_key_rotation_days": 90,
    "pii_redaction_enabled": True,
    "integrity_check_enabled": True
}

# System Health and Monitoring
HEALTH_CONFIG = {
    "health_check_interval_seconds": 30,
    "meta_incident_timeout_minutes": 5,
    "system_uptime_target": 0.999,  # 99.9%
    "auto_scaling_threshold_percent": 70,
    "lambda_warmup_interval_minutes": 10,
    "alert_storm_threshold": 50000  # alerts per hour
}

# Business Impact Calculation
BUSINESS_IMPACT_CONFIG = {
    "tier_1_cost_per_minute": 1000.0,  # Critical services
    "tier_2_cost_per_minute": 500.0,   # Important services
    "tier_3_cost_per_minute": 100.0,   # Non-critical services
    "user_impact_multiplier_cap": 10.0,  # Max 10x multiplier
    "sla_breach_penalty_multiplier": 2.0
}

# Agent-Specific Configuration
AGENT_CONFIG = {
    "detection": {
        "max_alert_rate": 100,  # alerts per second
        "alert_sampling_threshold": 0.8,  # priority score threshold
        "correlation_timeout": 30,  # seconds
        "simple_grouping_fallback": True
    },
    "resolution": {
        "max_concurrent_actions": 3,
        "target_resolution_time_minutes": 3,  # 180 seconds
        "max_processing_time_minutes": 5,     # 300 seconds
        "require_approval_for_high_risk": True,
        "sandbox_validation_enabled": True
    },
    "diagnosis": {
        "max_log_analysis_size_mb": 100,
        "trace_analysis_timeout": 120,  # seconds
        "root_cause_confidence_threshold": 0.7
    },
    "prediction": {
        "forecast_window_minutes": 30,
        "model_confidence_threshold": 0.6,
        "trend_analysis_lookback_hours": 24
    },
    "communication": {
        "notification_retry_attempts": 3,
        "escalation_timeout_minutes": 15,
        "message_template_cache_size": 100
    }
}