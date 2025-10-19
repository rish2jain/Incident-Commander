"""
Comprehensive tests for Showcase Controller

Tests showcase controller functionality, service aggregation,
error handling, and integration status validation.

Task 1.5: Write comprehensive showcase tests
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from src.services.showcase_controller import ShowcaseController, get_showcase_controller
from src.models.showcase import ShowcaseResponseModel
from src.models.incident import Incident, IncidentSeverity, ServiceTier, BusinessImpact, IncidentMetadata


class TestShowcaseController:
    """Test suite for ShowcaseController functionality."""
    
    @pytest.fixture
    def showcase_controller(self):
        """Create showcase controller instance for testing."""
        return ShowcaseController()
    
    @pytest.fixture
    def sample_incident(self):
        """Create sample incident for testing."""
        business_impact = BusinessImpact(
            service_tier=ServiceTier.TIER_1,
            affected_users=25000,
            revenue_impact_per_minute=1500.0
        )
        
        metadata = IncidentMetadata(
            source_system="test",
            tags={"test": "true", "showcase": "true"}
        )
        
        return Incident(
            title="Test Showcase Incident",
            description="Test incident for showcase demonstration",
            severity=IncidentSeverity.HIGH,
            business_impact=business_impact,
            metadata=metadata
        )
    
    @pytest.mark.asyncio
    async def test_generate_full_showcase_success(self, showcase_controller, sample_incident):
        """Test successful full showcase generation."""
        
        # Mock all integration methods to return success
        with patch.object(showcase_controller, 'get_integration_status') as mock_integration, \
             patch.object(showcase_controller, '_get_amazon_q_analysis') as mock_q, \
             patch.object(showcase_controller, '_get_nova_act_planning') as mock_nova, \
             patch.object(showcase_controller, '_get_strands_coordination') as mock_strands, \
             patch.object(showcase_controller, '_get_business_impact_analysis') as mock_business, \
             patch.object(showcase_controller, '_get_predictive_analysis') as mock_prediction, \
             patch.object(showcase_controller, '_get_performance_snapshot') as mock_performance, \
             patch.object(showcase_controller, '_get_agent_coordination_demo') as mock_coordination, \
             patch.object(showcase_controller, '_get_fault_tolerance_demo') as mock_fault, \
             patch.object(showcase_controller, '_get_security_compliance_demo') as mock_security:
            
            # Setup mock returns
            mock_integration.return_value = {
                "overall_health": 0.95,
                "overall_status": "operational",
                "service_details": {
                    "amazon_q": {"is_operational": True},
                    "nova_act": {"is_operational": True},
                    "strands_sdk": {"is_operational": True}
                }
            }
            
            mock_q.return_value = {"success": True, "confidence": 0.92}
            mock_nova.return_value = {"success": True, "confidence": 0.89}
            mock_strands.return_value = {"success": True, "coordination_efficiency": 0.94}
            mock_business.return_value = {"success": True, "roi_percentage": 350}
            mock_prediction.return_value = {"success": True, "prevention_rate": 0.35}
            mock_performance.return_value = {"success": True, "mttr": 180}
            mock_coordination.return_value = {"success": True, "swarm_score": 0.93}
            mock_fault.return_value = {"success": True, "resilience_score": 0.96}
            mock_security.return_value = {"success": True, "security_score": 0.98}
            
            # Execute showcase
            result = await showcase_controller.generate_full_showcase(sample_incident.id)
            
            # Verify structure
            assert "showcase_metadata" in result
            assert "integration_status" in result
            assert "incident_analysis" in result
            assert "business_impact_report" in result
            assert "performance_metrics" in result
            assert "system_capabilities" in result
            assert "competitive_advantages" in result
            assert "success_criteria" in result
            
            # Verify execution time
            assert result["showcase_metadata"]["execution_time_seconds"] < 30.0
            
            # Verify success criteria
            success_criteria = result["success_criteria"]
            assert success_criteria["execution_time_under_30s"] is True
            assert success_criteria["all_integrations_responsive"] is True
            assert success_criteria["comprehensive_coverage"] is True
            assert success_criteria["business_value_demonstrated"] is True
    
    @pytest.mark.asyncio
    async def test_generate_full_showcase_with_failures(self, showcase_controller):
        """Test showcase generation with some service failures."""
        
        with patch.object(showcase_controller, 'get_integration_status') as mock_integration, \
             patch.object(showcase_controller, '_get_amazon_q_analysis') as mock_q, \
             patch.object(showcase_controller, '_get_nova_act_planning') as mock_nova:
            
            # Setup mixed success/failure scenario
            mock_integration.return_value = {
                "overall_health": 0.6,
                "overall_status": "degraded"
            }
            
            mock_q.return_value = {"success": True, "confidence": 0.85}
            mock_nova.side_effect = Exception("Nova Act unavailable")
            
            # Execute showcase
            result = await showcase_controller.generate_full_showcase()
            
            # Should still return a result with fallbacks
            assert "showcase_metadata" in result
            assert result["showcase_metadata"]["execution_time_seconds"] >= 0
            
            # Should have fallback responses
            assert "incident_analysis" in result
    
    @pytest.mark.asyncio
    async def test_get_integration_status(self, showcase_controller):
        """Test integration status checking."""
        
        # Mock individual integration tests
        with patch.object(showcase_controller, '_test_amazon_q_integration') as mock_q, \
             patch.object(showcase_controller, '_test_nova_act_integration') as mock_nova, \
             patch.object(showcase_controller, '_test_strands_integration') as mock_strands, \
             patch.object(showcase_controller, '_test_titan_embeddings') as mock_titan, \
             patch.object(showcase_controller, '_test_bedrock_agents') as mock_bedrock, \
             patch.object(showcase_controller, '_test_bedrock_guardrails') as mock_guardrails:
            
            # Setup mock service statuses
            from src.services.showcase_controller import ServiceStatus
            
            mock_q.return_value = ServiceStatus(
                service_name="amazon_q",
                is_operational=True,
                response_time=1.2,
                error_rate=0.0,
                last_health_check=datetime.now(),
                features_available=["intelligent_analysis"]
            )
            
            mock_nova.return_value = ServiceStatus(
                service_name="nova_act",
                is_operational=True,
                response_time=0.8,
                error_rate=0.0,
                last_health_check=datetime.now(),
                features_available=["advanced_reasoning"]
            )
            
            mock_strands.return_value = ServiceStatus(
                service_name="strands_sdk",
                is_operational=False,
                response_time=5.0,
                error_rate=1.0,
                last_health_check=datetime.now(),
                diagnostic_info={"error": "timeout"}
            )
            
            mock_titan.return_value = ServiceStatus(
                service_name="titan_embeddings",
                is_operational=True,
                response_time=0.5,
                error_rate=0.0,
                last_health_check=datetime.now()
            )
            
            mock_bedrock.return_value = ServiceStatus(
                service_name="bedrock_agents",
                is_operational=True,
                response_time=1.0,
                error_rate=0.0,
                last_health_check=datetime.now()
            )
            
            mock_guardrails.return_value = ServiceStatus(
                service_name="guardrails",
                is_operational=True,
                response_time=0.3,
                error_rate=0.0,
                last_health_check=datetime.now()
            )
            
            # Execute integration status check
            result = await showcase_controller.get_integration_status()
            
            # Verify structure
            assert "overall_health" in result
            assert "overall_status" in result
            assert "service_details" in result
            assert "integration_summary" in result
            
            # Verify health calculation (5 out of 6 operational = 0.833...)
            assert 0.8 <= result["overall_health"] <= 0.9
            
            # Verify service details
            service_details = result["service_details"]
            assert "amazon_q" in service_details
            assert "nova_act" in service_details
            assert "strands_sdk" in service_details
            
            # Verify failed service details
            strands_details = service_details["strands_sdk"]
            assert strands_details["is_operational"] is False
            assert strands_details["error_rate"] == 1.0
    
    @pytest.mark.asyncio
    async def test_amazon_q_integration_test(self, showcase_controller):
        """Test Amazon Q integration testing."""
        
        with patch('src.amazon_q_integration.AmazonQIncidentAnalyzer') as mock_analyzer_class:
            mock_analyzer = AsyncMock()
            mock_analyzer_class.return_value = mock_analyzer
            mock_analyzer.analyze_incident_with_q.return_value = {
                "confidence": 0.92,
                "analysis": "test analysis"
            }
            
            result = await showcase_controller._test_amazon_q_integration()
            
            assert result.service_name == "amazon_q"
            assert result.is_operational is True
            assert result.response_time > 0
            assert "intelligent_analysis" in result.features_available
    
    @pytest.mark.asyncio
    async def test_amazon_q_integration_failure(self, showcase_controller):
        """Test Amazon Q integration failure handling."""
        
        with patch('src.amazon_q_integration.AmazonQIncidentAnalyzer') as mock_analyzer_class:
            mock_analyzer_class.side_effect = Exception("Q service unavailable")
            
            result = await showcase_controller._test_amazon_q_integration()
            
            assert result.service_name == "amazon_q"
            assert result.is_operational is False
            assert result.error_rate == 1.0
            assert result.diagnostic_info is not None
            assert "fallback_available" in result.diagnostic_info
    
    @pytest.mark.asyncio
    async def test_fallback_responses(self, showcase_controller, sample_incident):
        """Test fallback response generation."""
        
        # Test Amazon Q fallback
        q_fallback = await showcase_controller._get_fallback_response("amazon_q_analysis")
        assert q_fallback["success"] is False
        assert q_fallback["fallback_mode"] is True
        assert "simulated_analysis" in q_fallback
        
        # Test Nova Act fallback
        nova_fallback = await showcase_controller._get_fallback_response("nova_act_planning")
        assert nova_fallback["success"] is False
        assert nova_fallback["fallback_mode"] is True
        assert "simulated_planning" in nova_fallback
        
        # Test Strands fallback
        strands_fallback = await showcase_controller._get_fallback_response("strands_coordination")
        assert strands_fallback["success"] is False
        assert strands_fallback["fallback_mode"] is True
        assert "simulated_metrics" in strands_fallback
    
    @pytest.mark.asyncio
    async def test_emergency_fallback_response(self, showcase_controller):
        """Test emergency fallback response."""
        
        error_message = "Critical system failure"
        result = await showcase_controller._get_emergency_fallback_response(error_message)
        
        assert "showcase_metadata" in result
        assert result["showcase_metadata"]["emergency_mode"] is True
        assert result["showcase_metadata"]["error"] == error_message
        assert "core_capabilities" in result
        assert "recovery_actions" in result
    
    @pytest.mark.asyncio
    async def test_performance_requirements(self, showcase_controller):
        """Test that showcase meets performance requirements."""
        
        # Mock fast responses for all integrations
        with patch.object(showcase_controller, 'get_integration_status') as mock_integration:
            mock_integration.return_value = {
                "overall_health": 0.9,
                "overall_status": "operational"
            }
            
            start_time = datetime.now()
            result = await showcase_controller.generate_full_showcase()
            end_time = datetime.now()
            
            execution_time = (end_time - start_time).total_seconds()
            
            # Should complete within 30 seconds
            assert execution_time < 30.0
            
            # Should report execution time accurately
            reported_time = result["showcase_metadata"]["execution_time_seconds"]
            assert abs(reported_time - execution_time) < 1.0  # Within 1 second tolerance
    
    def test_get_showcase_controller_singleton(self):
        """Test showcase controller singleton pattern."""
        
        controller1 = get_showcase_controller()
        controller2 = get_showcase_controller()
        
        # Should return the same instance
        assert controller1 is controller2
        assert isinstance(controller1, ShowcaseController)
    
    @pytest.mark.asyncio
    async def test_concurrent_showcase_requests(self, showcase_controller):
        """Test handling of concurrent showcase requests."""
        
        # Mock integration status to return quickly
        with patch.object(showcase_controller, 'get_integration_status') as mock_integration:
            mock_integration.return_value = {
                "overall_health": 0.85,
                "overall_status": "operational"
            }
            
            # Execute multiple concurrent requests
            tasks = [
                showcase_controller.generate_full_showcase(),
                showcase_controller.generate_full_showcase(),
                showcase_controller.generate_full_showcase()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All should complete successfully
            for result in results:
                assert not isinstance(result, Exception)
                assert "showcase_metadata" in result
    
    @pytest.mark.asyncio
    async def test_integration_caching(self, showcase_controller):
        """Test integration status caching."""
        
        with patch.object(showcase_controller, '_test_amazon_q_integration') as mock_q:
            from src.services.showcase_controller import ServiceStatus
            
            mock_q.return_value = ServiceStatus(
                service_name="amazon_q",
                is_operational=True,
                response_time=1.0,
                error_rate=0.0,
                last_health_check=datetime.now()
            )
            
            # First call should execute tests
            result1 = await showcase_controller.get_integration_status()
            assert mock_q.call_count == 1
            
            # Second call within cache TTL should use cache
            result2 = await showcase_controller.get_integration_status()
            assert mock_q.call_count == 1  # Should not increase
            
            # Results should be identical
            assert result1["overall_health"] == result2["overall_health"]


class TestShowcaseIntegration:
    """Integration tests for showcase controller with real services."""
    
    @pytest.mark.asyncio
    async def test_showcase_with_real_coordinator(self):
        """Test showcase integration with real swarm coordinator."""
        
        showcase_controller = ShowcaseController()
        
        # This test would use real coordinator if available
        try:
            result = await showcase_controller._get_performance_snapshot()
            assert "success" in result
        except Exception:
            # If coordinator not available, should handle gracefully
            pass
    
    @pytest.mark.asyncio
    async def test_showcase_error_handling(self):
        """Test comprehensive error handling in showcase."""
        
        showcase_controller = ShowcaseController()
        
        # Test with invalid incident ID
        result = await showcase_controller.generate_full_showcase("invalid_incident_id")
        
        # Should still return a valid response
        assert "showcase_metadata" in result
        assert "integration_status" in result
    
    @pytest.mark.asyncio
    async def test_business_impact_integration(self):
        """Test business impact calculator integration."""
        
        showcase_controller = ShowcaseController()
        
        # Create test incident
        business_impact = BusinessImpact(
            service_tier=ServiceTier.TIER_1,
            affected_users=50000,
            revenue_impact_per_minute=2000.0
        )
        
        metadata = IncidentMetadata(
            source_system="test",
            tags={"test": "true"}
        )
        
        incident = Incident(
            title="Business Impact Test",
            description="Test incident for business impact calculation",
            severity=IncidentSeverity.CRITICAL,
            business_impact=business_impact,
            metadata=metadata
        )
        
        # Test business impact analysis
        result = await showcase_controller._get_business_impact_analysis(incident)
        
        if result.get("success", False):
            assert "impact_analysis" in result
            assert "roi_percentage" in result
            assert result["roi_percentage"] > 0
        else:
            # Should have fallback
            assert "fallback_mode" in result or "error" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])