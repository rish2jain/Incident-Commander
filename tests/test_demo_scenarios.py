"""
Comprehensive tests for demo scenarios and Byzantine fault injection.
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.services.demo_scenario_manager import (
    DemoScenarioManager,
    ScenarioType,
    ByzantineFaultType,
    DemoScenario,
    ByzantineFault
)
from src.models.incident import IncidentSeverity


@pytest.fixture
def demo_manager():
    """Create a demo scenario manager for testing."""
    return DemoScenarioManager()


@pytest.fixture
def mock_websocket_manager():
    """Mock WebSocket manager."""
    mock_ws = AsyncMock()
    mock_ws.broadcast_incident_update = AsyncMock()
    mock_ws.broadcast_agent_state = AsyncMock()
    mock_ws.broadcast_consensus_update = AsyncMock()
    return mock_ws


@pytest.fixture
def mock_enhanced_coordinator():
    """Mock enhanced consensus coordinator."""
    mock_coordinator = AsyncMock()
    mock_coordinator.handle_incident_with_pbft = AsyncMock()
    return mock_coordinator


class TestDemoScenarioManager:
    """Test demo scenario management functionality."""
    
    def test_initialization(self, demo_manager):
        """Test demo manager initialization."""
        assert len(demo_manager.scenarios) == 5
        assert len(demo_manager.byzantine_faults) == 5
        assert demo_manager.performance_metrics["scenarios_run"] == 0
        assert demo_manager.performance_metrics["faults_injected"] == 0
    
    def test_scenario_creation(self, demo_manager):
        """Test that all scenarios are properly created."""
        # Check database failure scenario
        db_scenario = demo_manager.scenarios[ScenarioType.DATABASE_FAILURE]
        assert db_scenario.title == "Critical Database Cascade Failure"
        assert db_scenario.severity == IncidentSeverity.CRITICAL
        assert len(db_scenario.phases) == 5
        assert db_scenario.business_impact["affected_users"] == 850000
        
        # Check API cascade scenario
        api_scenario = demo_manager.scenarios[ScenarioType.API_CASCADE]
        assert api_scenario.title == "Microservices API Cascade Failure"
        assert api_scenario.severity == IncidentSeverity.HIGH
        assert api_scenario.duration_seconds == 150
        
        # Check all scenarios have required fields
        for scenario in demo_manager.scenarios.values():
            assert scenario.title
            assert scenario.description
            assert scenario.severity
            assert scenario.phases
            assert scenario.expected_resolution
            assert scenario.business_impact
    
    def test_byzantine_fault_creation(self, demo_manager):
        """Test that Byzantine faults are properly created."""
        # Check conflicting recommendations fault
        conflict_fault = demo_manager.byzantine_faults[ByzantineFaultType.CONFLICTING_RECOMMENDATIONS]
        assert conflict_fault.target_agent == "diagnosis"
        assert conflict_fault.detection_probability == 0.9
        assert conflict_fault.impact_level == "medium"
        
        # Check malicious actions fault
        malicious_fault = demo_manager.byzantine_faults[ByzantineFaultType.MALICIOUS_ACTIONS]
        assert malicious_fault.target_agent == "resolution"
        assert malicious_fault.detection_probability == 0.95
        assert malicious_fault.impact_level == "high"
        
        # Check all faults have required fields
        for fault in demo_manager.byzantine_faults.values():
            assert fault.target_agent
            assert fault.description
            assert fault.duration_seconds > 0
            assert 0 <= fault.detection_probability <= 1
            assert fault.impact_level in ["low", "medium", "high", "critical"]
    
    @pytest.mark.asyncio
    async def test_trigger_demo_scenario(self, demo_manager, mock_websocket_manager):
        """Test triggering a demo scenario."""
        with patch('src.services.demo_scenario_manager.get_websocket_manager', 
                  return_value=mock_websocket_manager):
            
            scenario_id = await demo_manager.trigger_demo_scenario(ScenarioType.DATABASE_FAILURE)
            
            # Check scenario was created
            assert scenario_id.startswith("demo_database_failure_")
            assert scenario_id in demo_manager.active_scenarios
            assert demo_manager.performance_metrics["scenarios_run"] == 1
            
            # Check WebSocket broadcasts were called
            mock_websocket_manager.broadcast_incident_update.assert_called()
    
    @pytest.mark.asyncio
    async def test_inject_byzantine_fault(self, demo_manager, mock_websocket_manager):
        """Test Byzantine fault injection."""
        with patch('src.services.demo_scenario_manager.get_websocket_manager', 
                  return_value=mock_websocket_manager):
            
            fault_id = await demo_manager.inject_byzantine_fault(
                ByzantineFaultType.CONFLICTING_RECOMMENDATIONS,
                "diagnosis"
            )
            
            # Check fault was created
            assert fault_id.startswith("fault_conflicting_recommendations_")
            assert fault_id in demo_manager.active_faults
            assert demo_manager.performance_metrics["faults_injected"] == 1
            
            # Check WebSocket broadcasts were called
            mock_websocket_manager.broadcast_agent_state.assert_called_with("diagnosis", "byzantine")
    
    @pytest.mark.asyncio
    async def test_scenario_execution_phases(self, demo_manager, mock_websocket_manager, mock_enhanced_coordinator):
        """Test scenario phase execution."""
        with patch('src.services.demo_scenario_manager.get_websocket_manager', 
                  return_value=mock_websocket_manager), \
             patch('src.services.demo_scenario_manager.get_enhanced_coordinator',
                  return_value=mock_enhanced_coordinator):
            
            # Use a shorter scenario for testing
            scenario = demo_manager.scenarios[ScenarioType.NETWORK_PARTITION]
            scenario.phases = [
                {"phase": "detection", "duration": 0.1, "description": "Test detection"},
                {"phase": "resolution", "duration": 0.1, "description": "Test resolution"}
            ]
            
            scenario_id = await demo_manager.trigger_demo_scenario(ScenarioType.NETWORK_PARTITION)
            
            # Wait for scenario to complete
            await asyncio.sleep(0.5)
            
            # Check that phases were executed
            assert mock_websocket_manager.broadcast_agent_state.call_count >= 4  # At least processing + completed for each phase
            assert mock_enhanced_coordinator.handle_incident_with_pbft.called
    
    @pytest.mark.asyncio
    async def test_byzantine_fault_detection(self, demo_manager, mock_websocket_manager):
        """Test Byzantine fault detection simulation."""
        with patch('src.services.demo_scenario_manager.get_websocket_manager', 
                  return_value=mock_websocket_manager):
            
            # Use a fault with high detection probability
            fault = demo_manager.byzantine_faults[ByzantineFaultType.SIGNATURE_FORGERY]
            fault.duration_seconds = 0.1  # Short duration for testing
            
            fault_id = await demo_manager.inject_byzantine_fault(
                ByzantineFaultType.SIGNATURE_FORGERY,
                "communication"
            )
            
            # Wait for fault execution
            await asyncio.sleep(0.2)
            
            # Check that isolation was called (high probability of detection)
            calls = mock_websocket_manager.broadcast_agent_state.call_args_list
            agent_states = [call[0][1] for call in calls if len(call[0]) > 1]
            
            # Should have byzantine state and likely isolated state
            assert "byzantine" in agent_states
    
    @pytest.mark.asyncio
    async def test_reset_all_agents(self, demo_manager, mock_websocket_manager):
        """Test resetting all agents."""
        with patch('src.services.demo_scenario_manager.get_websocket_manager', 
                  return_value=mock_websocket_manager):
            
            # Add some active scenarios and faults
            demo_manager.active_scenarios["test_scenario"] = Mock()
            demo_manager.active_faults["test_fault"] = Mock()
            
            await demo_manager.reset_all_agents()
            
            # Check that all agents were reset to idle
            assert mock_websocket_manager.broadcast_agent_state.call_count == 5  # 5 agents
            
            # Check that active scenarios and faults were cleared
            assert len(demo_manager.active_scenarios) == 0
            assert len(demo_manager.active_faults) == 0
    
    def test_metrics_tracking(self, demo_manager):
        """Test performance metrics tracking."""
        # Test resolution time metrics update
        demo_manager.performance_metrics["scenarios_run"] = 1
        demo_manager.performance_metrics["average_resolution_time"] = 120.0
        
        demo_manager._update_resolution_metrics(180.0)
        
        # Should update average: (120 * 0 + 180 * 1) / 1 = 180
        assert demo_manager.performance_metrics["average_resolution_time"] == 180.0
        
        # Add another resolution time
        demo_manager.performance_metrics["scenarios_run"] = 2
        demo_manager._update_resolution_metrics(60.0)
        
        # Should update average: (180 * 1 + 60 * 1) / 2 = 120
        assert demo_manager.performance_metrics["average_resolution_time"] == 120.0
    
    def test_get_demo_metrics(self, demo_manager):
        """Test demo metrics retrieval."""
        # Add some test data
        demo_manager.performance_metrics["scenarios_run"] = 5
        demo_manager.performance_metrics["faults_injected"] = 3
        demo_manager.active_scenarios["test"] = Mock()
        demo_manager.active_faults["test"] = Mock()
        
        metrics = demo_manager.get_demo_metrics()
        
        assert metrics["performance_metrics"]["scenarios_run"] == 5
        assert metrics["performance_metrics"]["faults_injected"] == 3
        assert metrics["active_scenarios"] == 1
        assert metrics["active_faults"] == 1
        assert len(metrics["available_scenarios"]) == 5
        assert len(metrics["available_faults"]) == 5
    
    @pytest.mark.asyncio
    async def test_invalid_scenario_type(self, demo_manager):
        """Test handling of invalid scenario types."""
        with pytest.raises(ValueError, match="Unknown scenario type"):
            await demo_manager.trigger_demo_scenario("invalid_scenario")
    
    @pytest.mark.asyncio
    async def test_invalid_fault_type(self, demo_manager):
        """Test handling of invalid fault types."""
        with pytest.raises(ValueError, match="Unknown fault type"):
            await demo_manager.inject_byzantine_fault("invalid_fault")
    
    @pytest.mark.asyncio
    async def test_concurrent_scenarios(self, demo_manager, mock_websocket_manager):
        """Test running multiple scenarios concurrently."""
        with patch('src.services.demo_scenario_manager.get_websocket_manager', 
                  return_value=mock_websocket_manager):
            
            # Trigger multiple scenarios
            scenario1_id = await demo_manager.trigger_demo_scenario(ScenarioType.DATABASE_FAILURE)
            scenario2_id = await demo_manager.trigger_demo_scenario(ScenarioType.API_CASCADE)
            
            # Check both are active
            assert len(demo_manager.active_scenarios) == 2
            assert scenario1_id in demo_manager.active_scenarios
            assert scenario2_id in demo_manager.active_scenarios
            assert demo_manager.performance_metrics["scenarios_run"] == 2
    
    @pytest.mark.asyncio
    async def test_fault_simulation_methods(self, demo_manager, mock_websocket_manager):
        """Test different Byzantine fault simulation methods."""
        with patch('src.services.demo_scenario_manager.get_websocket_manager', 
                  return_value=mock_websocket_manager):
            
            fault = ByzantineFault(
                fault_type=ByzantineFaultType.CONFLICTING_RECOMMENDATIONS,
                target_agent="test_agent",
                description="Test fault",
                duration_seconds=0.1,
                detection_probability=1.0,
                impact_level="medium"
            )
            
            # Test conflicting recommendations simulation
            await demo_manager._simulate_conflicting_recommendations(fault)
            
            # Should have called broadcast_agent_state multiple times
            assert mock_websocket_manager.broadcast_agent_state.call_count >= 3
            
            # Reset mock
            mock_websocket_manager.reset_mock()
            
            # Test malicious actions simulation
            await demo_manager._simulate_malicious_actions(fault)
            
            # Should have called broadcast with malicious action detected
            calls = mock_websocket_manager.broadcast_agent_state.call_args_list
            assert any("malicious_action_detected" in str(call) for call in calls)


class TestDemoIntegration:
    """Integration tests for demo scenarios with other components."""
    
    @pytest.mark.asyncio
    async def test_scenario_with_consensus_integration(self, demo_manager):
        """Test scenario integration with Byzantine consensus."""
        # This would test the full integration with the PBFT consensus engine
        # In a real test environment with actual consensus coordination
        pass
    
    @pytest.mark.asyncio
    async def test_websocket_message_flow(self, demo_manager):
        """Test WebSocket message flow during scenarios."""
        # This would test the actual WebSocket message broadcasting
        # with real WebSocket connections in an integration environment
        pass
    
    @pytest.mark.asyncio
    async def test_performance_under_load(self, demo_manager):
        """Test demo performance under concurrent load."""
        # This would test running multiple scenarios and faults
        # simultaneously to validate system performance
        pass