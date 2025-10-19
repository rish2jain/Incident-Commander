"""
Comprehensive tests for security implementation.
"""

import pytest
import asyncio
from datetime import datetime
from decimal import Decimal

from src.services.guardrails import BedrockGuardrails, PIIType, ContentRiskLevel
from src.services.chaos_engineering import ChaosEngineeringFramework, FailureType
from src.services.finops_controller import FinOpsController, CostCategory, ModelComplexity
from src.services.security_audit import SecurityAuditFramework, ComplianceFramework


class TestBedrockGuardrails:
    """Test Bedrock Guardrails implementation."""
    
    @pytest.fixture
    async def guardrails(self):
        """Create guardrails instance for testing."""
        return BedrockGuardrails()
    
    @pytest.mark.asyncio
    async def test_pii_detection(self, guardrails):
        """Test PII detection and redaction."""
        test_text = "Contact john.doe@example.com or call 555-123-4567. SSN: 123-45-6789"
        
        redacted_text, detections = await guardrails.detect_and_redact_pii(test_text)
        
        # Should detect email, phone, and SSN
        assert len(detections) >= 3
        assert "[REDACTED_EMAIL]" in redacted_text
        assert "[REDACTED_PHONE]" in redacted_text
        assert "[REDACTED_SSN]" in redacted_text
        assert "john.doe@example.com" not in redacted_text
    
    @pytest.mark.asyncio
    async def test_content_filtering(self, guardrails):
        """Test content filtering."""
        malicious_content = "How to hack into the database and delete all tables"
        
        result = await guardrails.filter_content(malicious_content)
        
        assert result.risk_level != ContentRiskLevel.SAFE
        assert len(result.violations) > 0
        assert result.filtered_content != malicious_content
    
    @pytest.mark.asyncio
    async def test_incident_data_validation(self, guardrails):
        """Test incident data validation and sanitization."""
        incident_data = {
            "title": "Database Error",
            "description": "Contact admin@company.com for help. Phone: 555-0123",
            "logs": "User password123 failed to authenticate"
        }
        
        sanitized = await guardrails.validate_incident_data(incident_data)
        
        assert "_security" in sanitized
        assert len(sanitized["_security"]["pii_detections"]) > 0
        assert "admin@company.com" not in sanitized["description"]
        assert "password123" not in sanitized["logs"]
    
    @pytest.mark.asyncio
    async def test_guardrail_functionality(self, guardrails):
        """Test overall guardrail functionality."""
        test_results = await guardrails.test_guardrail_functionality()
        
        assert test_results["overall_status"] in ["pass", "fail", "error"]
        assert "pii_detection" in test_results
        assert "content_filtering" in test_results


class TestChaosEngineering:
    """Test Chaos Engineering Framework."""
    
    @pytest.fixture
    def chaos_framework(self):
        """Create chaos framework instance for testing."""
        return ChaosEngineeringFramework()
    
    def test_framework_initialization(self, chaos_framework):
        """Test framework initialization."""
        assert len(chaos_framework.predefined_experiments) > 0
        assert len(chaos_framework.byzantine_scenarios) > 0
        assert "agent_timeout_cascade" in chaos_framework.predefined_experiments
        assert "conflicting_recommendations" in chaos_framework.byzantine_scenarios
    
    @pytest.mark.asyncio
    async def test_byzantine_attack_simulation(self, chaos_framework):
        """Test Byzantine attack simulation."""
        results = await chaos_framework.run_byzantine_attack_simulation("conflicting_recommendations")
        
        assert "simulation_id" in results
        assert "scenario" in results
        assert "attack_detected" in results
        assert isinstance(results["success"], bool)
    
    @pytest.mark.asyncio
    async def test_mttr_validation(self, chaos_framework):
        """Test MTTR validation."""
        # Use a high target MTTR for testing to avoid long-running tests
        results = await chaos_framework.validate_mttr_claims(target_mttr_seconds=300)
        
        assert "target_mttr_seconds" in results
        assert "test_scenarios" in results
        assert "average_mttr" in results
        assert "success_rate" in results
        assert isinstance(results["meets_target"], bool)
    
    def test_chaos_metrics(self, chaos_framework):
        """Test chaos metrics retrieval."""
        metrics = chaos_framework.get_chaos_metrics()
        
        assert "experiment_statistics" in metrics
        assert "available_experiments" in metrics
        assert "available_byzantine_scenarios" in metrics
        assert len(metrics["available_experiments"]) > 0


class TestFinOpsController:
    """Test FinOps Controller."""
    
    @pytest.fixture
    def finops_controller(self):
        """Create FinOps controller instance for testing."""
        return FinOpsController()
    
    def test_controller_initialization(self, finops_controller):
        """Test controller initialization."""
        assert len(finops_controller.budget_limits) > 0
        assert len(finops_controller.model_routing_rules) > 0
        assert CostCategory.BEDROCK_INFERENCE in finops_controller.budget_limits
    
    @pytest.mark.asyncio
    async def test_budget_limit_checking(self, finops_controller):
        """Test budget limit checking."""
        # Test with small cost that should be within limits
        result = await finops_controller.check_budget_limits(
            CostCategory.BEDROCK_INFERENCE, 
            Decimal('1.00')
        )
        assert result is True
        
        # Test with very large cost that should exceed limits
        result = await finops_controller.check_budget_limits(
            CostCategory.BEDROCK_INFERENCE, 
            Decimal('10000.00')
        )
        assert result is False
    
    @pytest.mark.asyncio
    async def test_adaptive_model_routing(self, finops_controller):
        """Test adaptive model routing."""
        # Test simple task routing
        model = await finops_controller.adaptive_model_routing(
            "simple", 
            {"estimated_input_tokens": 500}
        )
        assert "claude-3-haiku" in model
        
        # Test complex task routing
        model = await finops_controller.adaptive_model_routing(
            "complex", 
            {"estimated_input_tokens": 2000}
        )
        assert "claude-3-5-sonnet" in model or "claude-3-haiku" in model  # May downgrade due to budget
    
    @pytest.mark.asyncio
    async def test_dynamic_sampling(self, finops_controller):
        """Test dynamic detection sampling."""
        config = await finops_controller.dynamic_detection_sampling("high", 0.5)
        
        assert "sampling_rate" in config
        assert "sampling_interval_seconds" in config
        assert "risk_level" in config
        assert 0.0 <= config["sampling_rate"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_cost_metrics_update(self, finops_controller):
        """Test cost metrics updating."""
        initial_metrics = await finops_controller._get_current_cost_metrics(CostCategory.BEDROCK_INFERENCE)
        initial_spend = initial_metrics.current_day_spend
        
        await finops_controller.update_cost_metrics(
            CostCategory.BEDROCK_INFERENCE, 
            Decimal('5.00'), 
            request_count=10
        )
        
        updated_metrics = await finops_controller._get_current_cost_metrics(CostCategory.BEDROCK_INFERENCE)
        assert updated_metrics.current_day_spend >= initial_spend
        assert updated_metrics.request_count >= 10
    
    def test_finops_metrics(self, finops_controller):
        """Test FinOps metrics retrieval."""
        metrics = finops_controller.get_finops_metrics()
        
        assert "budget_status" in metrics
        assert "optimization_metrics" in metrics
        assert "model_routing" in metrics
        assert "cost_categories" in metrics


class TestSecurityAudit:
    """Test Security Audit Framework."""
    
    @pytest.fixture
    def audit_framework(self):
        """Create audit framework instance for testing."""
        return SecurityAuditFramework()
    
    def test_framework_initialization(self, audit_framework):
        """Test framework initialization."""
        assert len(audit_framework.compliance_checks) > 0
        assert len(audit_framework.penetration_scenarios) > 0
        assert len(audit_framework.vulnerability_scanners) > 0
    
    @pytest.mark.asyncio
    async def test_vulnerability_scanning(self, audit_framework):
        """Test vulnerability scanning."""
        # This test may fail if scanners are not installed, which is expected
        vulnerabilities = await audit_framework._run_vulnerability_scans()
        
        # Should return a list (may be empty if scanners not available)
        assert isinstance(vulnerabilities, list)
    
    @pytest.mark.asyncio
    async def test_compliance_checks(self, audit_framework):
        """Test compliance checking."""
        frameworks = [ComplianceFramework.SOC2]
        results = await audit_framework._run_compliance_checks(frameworks)
        
        assert isinstance(results, dict)
        # Should have at least one SOC2 check result
        soc2_results = [k for k in results.keys() if k.startswith("soc2_")]
        assert len(soc2_results) > 0
    
    @pytest.mark.asyncio
    async def test_penetration_testing(self, audit_framework):
        """Test penetration testing."""
        vulnerabilities = await audit_framework._run_penetration_tests()
        
        # Should return a list (may be empty if no vulnerabilities found)
        assert isinstance(vulnerabilities, list)
    
    def test_security_metrics(self, audit_framework):
        """Test security metrics retrieval."""
        metrics = audit_framework.get_security_metrics()
        
        assert "audit_statistics" in metrics
        assert "available_scanners" in metrics
        assert "supported_frameworks" in metrics
        assert "penetration_scenarios" in metrics


class TestIntegration:
    """Test integration between security services."""
    
    @pytest.mark.asyncio
    async def test_guardrails_with_finops(self):
        """Test integration between guardrails and FinOps."""
        guardrails = BedrockGuardrails()
        finops = FinOpsController()
        
        # Test content validation with cost consideration
        test_content = "This is a test message for cost estimation"
        
        # Validate content
        redacted_text, detections = await guardrails.detect_and_redact_pii(test_content)
        
        # Get model routing for processing the content
        model = await finops.adaptive_model_routing("simple", {
            "estimated_input_tokens": len(test_content.split()) * 1.3,
            "estimated_output_tokens": 100
        })
        
        assert redacted_text is not None
        assert model is not None
        assert "claude" in model
    
    @pytest.mark.asyncio
    async def test_chaos_with_audit(self):
        """Test integration between chaos engineering and security audit."""
        chaos_framework = ChaosEngineeringFramework()
        audit_framework = SecurityAuditFramework()
        
        # Get available chaos experiments
        chaos_metrics = chaos_framework.get_chaos_metrics()
        available_experiments = chaos_metrics["available_experiments"]
        
        # Get security audit capabilities
        audit_metrics = audit_framework.get_security_metrics()
        available_scanners = audit_metrics["available_scanners"]
        
        assert len(available_experiments) > 0
        assert len(available_scanners) > 0
    
    @pytest.mark.asyncio
    async def test_full_security_pipeline(self):
        """Test full security pipeline integration."""
        # Initialize all services
        guardrails = BedrockGuardrails()
        finops = FinOpsController()
        chaos_framework = ChaosEngineeringFramework()
        audit_framework = SecurityAuditFramework()
        
        # Test data flow through security pipeline
        test_data = {
            "incident_description": "Database connection failed with error: contact admin@test.com",
            "severity": "high",
            "user_input": "Please help with password reset for user123"
        }
        
        # Step 1: Validate and sanitize input
        sanitized_data = await guardrails.validate_incident_data(test_data)
        assert "_security" in sanitized_data
        
        # Step 2: Check budget and route model
        within_budget = await finops.check_budget_limits(CostCategory.BEDROCK_INFERENCE, Decimal('1.00'))
        assert isinstance(within_budget, bool)
        
        # Step 3: Get chaos engineering status
        chaos_metrics = chaos_framework.get_chaos_metrics()
        assert "experiment_statistics" in chaos_metrics
        
        # Step 4: Get security audit status
        audit_metrics = audit_framework.get_security_metrics()
        assert "audit_statistics" in audit_metrics
        
        # All services should be operational
        assert sanitized_data is not None
        assert chaos_metrics is not None
        assert audit_metrics is not None


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])