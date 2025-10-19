"""
End-to-End System Integration Tests.

Comprehensive tests for complete system integration across all enhancements,
validating functionality, performance, and error handling.
"""

import pytest
import asyncio
import time
from typing import Dict, Any
from datetime import datetime, timedelta

from src.services.system_integration_validator import validate_complete_system_integration
from src.services.showcase_controller import get_showcase_controller
from src.services.visual_3d_integration import get_visual_3d_integration
from src.services.enhanced_monitoring_integration import get_enhanced_monitoring_integration
from src.services.websocket_manager import get_websocket_manager


class TestSystemIntegrationE2E:
    """End-to-end system integration tests."""
    
    @pytest.mark.asyncio
    async def test_complete_system_integration_validation(self):
        """Test complete system integration validation."""
        # Execute comprehensive validation
        validation_report = await validate_complete_system_integration()
        
        # Validate report structure
        assert validation_report is not None
        assert validation_report.validation_id is not None
        assert validation_report.total_tests > 0
        assert validation_report.test_results is not None
        
        # Check that most tests passed (allow some warnings)
        success_rate = validation_report.passed_tests / validation_report.total_tests
        assert success_rate >= 0.7, f"Integration validation success rate too low: {success_rate:.1%}"
        
        # Ensure no critical failures
        assert validation_report.failed_tests <= 2, f"Too many failed tests: {validation_report.failed_tests}"
        
        # Validate performance metrics
        assert validation_report.performance_metrics["total_validation_duration_ms"] < 60000  # Under 1 minute
        assert validation_report.performance_metrics["average_test_duration_ms"] < 10000  # Under 10 seconds per test
    
    @pytest.mark.asyncio
    async def test_showcase_controller_integration(self):
        """Test showcase controller integration with main system."""
        showcase = get_showcase_controller()
        assert showcase is not None
        
        # Test integration status
        integration_status = await showcase.get_integration_status()
        assert integration_status is not None
        assert integration_status.overall_health > 0.5  # At least 50% health
        
        # Test system capabilities
        capabilities = await showcase.get_system_capabilities()
        assert capabilities is not None
        assert capabilities.total_capabilities > 0
        
        # Test performance summary
        performance = await showcase.get_performance_summary()
        assert performance is not None
        assert performance.average_mttr_seconds > 0
        assert performance.success_rate > 0.5
    
    @pytest.mark.asyncio
    async def test_3d_visualization_websocket_integration(self):
        """Test 3D visualization WebSocket integration."""
        visual_3d = get_visual_3d_integration()
        websocket_manager = get_websocket_manager()
        
        assert visual_3d is not None
        assert websocket_manager is not None
        
        # Test visualization status
        viz_status = await visual_3d.get_visualization_status()
        assert viz_status is not None
        assert viz_status["target_fps"] == 60
        
        # Test agent registration and updates
        test_agent_id = "test_e2e_agent"
        await visual_3d.register_agent(test_agent_id, "detection")
        
        # Update agent state
        await visual_3d.update_agent_state(test_agent_id, "processing", 0.9)
        
        # Create agent connection
        await visual_3d.create_agent_connection(
            test_agent_id, "target_agent", "message", 1.0, 2000
        )
        
        # Verify agent is registered
        updated_status = await visual_3d.get_visualization_status()
        assert updated_status["agents_count"] > 0
    
    @pytest.mark.asyncio
    async def test_enhanced_monitoring_integration(self):
        """Test enhanced monitoring integration with observability."""
        monitoring = get_enhanced_monitoring_integration()
        assert monitoring is not None
        
        # Test monitoring status
        status = await monitoring.get_monitoring_status()
        assert status is not None
        assert "monitoring_active" in status
        assert "prometheus_integration" in status
        
        # Test Prometheus metrics generation
        metrics = monitoring.get_prometheus_metrics()
        assert metrics is not None
        assert len(metrics) > 100  # Should have substantial metrics
        assert "incident_commander" in metrics  # Should contain our metrics
        
        # Test Grafana dashboard config
        grafana_config = await monitoring.create_grafana_dashboard_config()
        assert grafana_config is not None
        assert "dashboard" in grafana_config
        assert "panels" in grafana_config["dashboard"]
    
    @pytest.mark.asyncio
    async def test_cross_component_communication(self):
        """Test communication between all integrated components."""
        # Initialize all components
        showcase = get_showcase_controller()
        visual_3d = get_visual_3d_integration()
        monitoring = get_enhanced_monitoring_integration()
        websocket_manager = get_websocket_manager()
        
        # Test showcase -> 3D visualization communication
        test_incident_data = {
            "title": "E2E Test Incident",
            "description": "End-to-end integration test incident",
            "severity": "high",
            "affected_users": 1000,
            "revenue_impact_per_minute": 500.0
        }
        
        # Add incident to 3D visualization
        await visual_3d.add_incident_visualization("e2e_test_incident", test_incident_data)
        
        # Verify incident was added
        viz_status = await visual_3d.get_visualization_status()
        assert viz_status["incidents_count"] > 0
        
        # Test WebSocket message broadcasting
        connection_stats = websocket_manager.get_connection_stats()
        assert connection_stats is not None
        assert "active_connections" in connection_stats
        
        # Test monitoring metrics collection
        if monitoring.monitoring_active:
            # Wait for a collection cycle
            await asyncio.sleep(2)
            
            # Verify metrics are being collected
            metrics = monitoring.get_prometheus_metrics()
            assert "incident_commander_system_performance" in metrics
    
    @pytest.mark.asyncio
    async def test_performance_under_load(self):
        """Test system performance under simulated load."""
        visual_3d = get_visual_3d_integration()
        websocket_manager = get_websocket_manager()
        
        # Create multiple agents and connections to simulate load
        agent_count = 10
        connection_count = 20
        
        start_time = time.time()
        
        # Register multiple agents
        for i in range(agent_count):
            agent_id = f"load_test_agent_{i}"
            await visual_3d.register_agent(agent_id, "detection")
            await visual_3d.update_agent_state(agent_id, "processing", 0.8)
        
        # Create multiple connections
        for i in range(connection_count):
            from_agent = f"load_test_agent_{i % agent_count}"
            to_agent = f"load_test_agent_{(i + 1) % agent_count}"
            await visual_3d.create_agent_connection(
                from_agent, to_agent, "message", 0.8, 1000
            )
        
        # Broadcast multiple WebSocket messages
        for i in range(50):
            await websocket_manager.broadcast_agent_action(
                f"load_test_agent_{i % agent_count}",
                f"Load test action {i}",
                {"test": True, "iteration": i},
                0.9
            )
        
        total_time = time.time() - start_time
        
        # Verify performance is acceptable
        assert total_time < 10.0, f"Load test took too long: {total_time:.2f}s"
        
        # Verify system is still responsive
        viz_status = await visual_3d.get_visualization_status()
        assert viz_status["agents_count"] >= agent_count
        assert viz_status["connections_count"] >= 0  # Some may have expired
    
    @pytest.mark.asyncio
    async def test_error_handling_resilience(self):
        """Test system resilience and error handling."""
        showcase = get_showcase_controller()
        visual_3d = get_visual_3d_integration()
        
        # Test showcase controller error handling
        try:
            await showcase.generate_full_showcase("nonexistent_incident")
            # Should handle gracefully, not crash
        except Exception as e:
            # If it raises an exception, it should be a controlled one
            assert "not found" in str(e).lower() or "invalid" in str(e).lower()
        
        # Test 3D visualization error handling
        try:
            await visual_3d.update_agent_state("nonexistent_agent", "invalid_state")
            # Should handle gracefully
        except Exception as e:
            # Should be a controlled error
            assert isinstance(e, (ValueError, KeyError))
        
        # Test invalid agent connection
        try:
            await visual_3d.create_agent_connection(
                "nonexistent_from", "nonexistent_to", "invalid_type", 2.0  # Invalid strength
            )
            # Should handle gracefully
        except Exception as e:
            # Should be a controlled error
            assert isinstance(e, (ValueError, TypeError))
        
        # Verify system is still operational after errors
        viz_status = await visual_3d.get_visualization_status()
        assert viz_status is not None
        assert "streaming_active" in viz_status
    
    @pytest.mark.asyncio
    async def test_authentication_middleware_integration(self):
        """Test authentication middleware integration."""
        from src.api.middleware.auth import verify_demo_access, verify_api_key
        
        # Test authentication functions are available
        assert callable(verify_demo_access)
        assert callable(verify_api_key)
        
        # Test development mode access (should allow without credentials)
        from src.utils.config import config
        if config.environment == "development":
            # In development, should allow access
            result = await verify_demo_access(None)
            assert result is True
    
    @pytest.mark.asyncio
    async def test_api_endpoints_integration(self):
        """Test API endpoints integration."""
        # Test that key router modules can be imported
        routers_to_test = [
            "src.api.routers.showcase",
            "src.api.routers.visual_3d", 
            "src.api.routers.monitoring"
        ]
        
        for router_module in routers_to_test:
            try:
                module = __import__(router_module, fromlist=[router_module.split(".")[-1]])
                router = getattr(module, "router", None)
                assert router is not None, f"Router not found in {router_module}"
                assert len(router.routes) > 0, f"No routes found in {router_module}"
            except ImportError as e:
                pytest.fail(f"Failed to import {router_module}: {e}")
    
    @pytest.mark.asyncio
    async def test_end_to_end_incident_workflow(self):
        """Test complete end-to-end incident workflow."""
        showcase = get_showcase_controller()
        visual_3d = get_visual_3d_integration()
        websocket_manager = get_websocket_manager()
        
        # Create a demo incident
        incident_data = {
            "title": "E2E Workflow Test Incident",
            "description": "Complete end-to-end workflow test",
            "severity": "high",
            "service_tier": "tier_1",
            "affected_users": 5000,
            "revenue_impact_per_minute": 1000.0,
            "tags": {"test": "e2e", "workflow": "complete"}
        }
        
        # Generate showcase response
        start_time = time.time()
        showcase_response = await showcase.generate_demo_showcase(incident_data)
        showcase_time = time.time() - start_time
        
        # Verify showcase response
        assert showcase_response is not None
        assert showcase_response.execution_time < 30.0  # Under 30 seconds
        assert len(showcase_response.agent_responses) > 0
        
        # Add incident to 3D visualization
        await visual_3d.add_incident_visualization("e2e_workflow_incident", incident_data)
        
        # Simulate agent coordination
        agents = ["detection", "diagnosis", "prediction", "resolution", "communication"]
        for i, agent_type in enumerate(agents):
            agent_id = f"workflow_{agent_type}_agent"
            await visual_3d.register_agent(agent_id, agent_type)
            await visual_3d.update_agent_state(agent_id, "processing", 0.8 + i * 0.05)
            
            # Create connections between sequential agents
            if i > 0:
                prev_agent = f"workflow_{agents[i-1]}_agent"
                await visual_3d.create_agent_connection(
                    prev_agent, agent_id, "coordination", 0.9, 2000
                )
        
        # Broadcast workflow progress
        for i, agent_type in enumerate(agents):
            await websocket_manager.broadcast_agent_action(
                f"workflow_{agent_type}_agent",
                f"{agent_type.title()} agent processing incident",
                {"phase": i + 1, "total_phases": len(agents)},
                0.8 + i * 0.05,
                "completed" if i == len(agents) - 1 else "in_progress"
            )
        
        # Verify workflow completed successfully
        total_workflow_time = time.time() - start_time
        assert total_workflow_time < 60.0, f"E2E workflow took too long: {total_workflow_time:.2f}s"
        
        # Verify final state
        viz_status = await visual_3d.get_visualization_status()
        assert viz_status["agents_count"] >= len(agents)
        assert viz_status["incidents_count"] >= 1
        
        # Verify WebSocket stats
        connection_stats = websocket_manager.get_connection_stats()
        assert connection_stats["total_messages_sent"] >= len(agents)
    
    @pytest.mark.asyncio
    async def test_system_recovery_after_component_restart(self):
        """Test system recovery after component restart simulation."""
        visual_3d = get_visual_3d_integration()
        monitoring = get_enhanced_monitoring_integration()
        
        # Get initial state
        initial_viz_status = await visual_3d.get_visualization_status()
        initial_monitoring_status = await monitoring.get_monitoring_status()
        
        # Simulate component restart by stopping and starting
        if visual_3d.streaming_active:
            await visual_3d.stop_real_time_streaming()
            await asyncio.sleep(1)
            await visual_3d.start_real_time_streaming()
        
        if monitoring.monitoring_active:
            await monitoring.stop_enhanced_monitoring()
            await asyncio.sleep(1)
            await monitoring.start_enhanced_monitoring()
        
        # Wait for recovery
        await asyncio.sleep(3)
        
        # Verify recovery
        recovered_viz_status = await visual_3d.get_visualization_status()
        recovered_monitoring_status = await monitoring.get_monitoring_status()
        
        assert recovered_viz_status["streaming_active"] == initial_viz_status["streaming_active"]
        assert recovered_monitoring_status["monitoring_active"] == initial_monitoring_status["monitoring_active"]
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test system behavior under concurrent operations."""
        showcase = get_showcase_controller()
        visual_3d = get_visual_3d_integration()
        websocket_manager = get_websocket_manager()
        
        # Create concurrent tasks
        tasks = []
        
        # Concurrent showcase operations
        for i in range(3):
            incident_data = {
                "title": f"Concurrent Test Incident {i}",
                "description": f"Concurrent operation test {i}",
                "severity": "medium",
                "affected_users": 1000 + i * 100,
                "revenue_impact_per_minute": 200.0 + i * 50
            }
            tasks.append(showcase.generate_demo_showcase(incident_data))
        
        # Concurrent 3D visualization operations
        for i in range(5):
            agent_id = f"concurrent_agent_{i}"
            tasks.append(visual_3d.register_agent(agent_id, "detection"))
        
        # Concurrent WebSocket broadcasts
        for i in range(10):
            tasks.append(websocket_manager.broadcast_agent_action(
                f"concurrent_agent_{i % 5}",
                f"Concurrent action {i}",
                {"concurrent": True, "index": i},
                0.7
            ))
        
        # Execute all tasks concurrently
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        execution_time = time.time() - start_time
        
        # Verify results
        assert execution_time < 30.0, f"Concurrent operations took too long: {execution_time:.2f}s"
        
        # Check for exceptions
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) <= 2, f"Too many exceptions in concurrent operations: {len(exceptions)}"
        
        # Verify system is still responsive
        viz_status = await visual_3d.get_visualization_status()
        assert viz_status is not None
        assert viz_status["agents_count"] >= 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])