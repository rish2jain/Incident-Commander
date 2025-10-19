"""
Performance Validation Tests.

Tests to validate system performance meets requirements and targets
across all integrated components.
"""

import pytest
import asyncio
import time
import statistics
from typing import List, Dict, Any
from datetime import datetime, timedelta

from src.services.showcase_controller import get_showcase_controller
from src.services.visual_3d_integration import get_visual_3d_integration
from src.services.enhanced_monitoring_integration import get_enhanced_monitoring_integration
from src.services.websocket_manager import get_websocket_manager


class TestPerformanceValidation:
    """Performance validation tests for integrated system."""
    
    # Performance targets from requirements
    PERFORMANCE_TARGETS = {
        "showcase_response_time_seconds": 30.0,
        "3d_visualization_fps": 60.0,
        "websocket_message_latency_ms": 100.0,
        "agent_coordination_time_seconds": 5.0,
        "monitoring_collection_interval_seconds": 30.0,
        "system_availability_percentage": 99.0
    }
    
    @pytest.mark.asyncio
    async def test_showcase_controller_performance(self):
        """Test showcase controller meets performance targets."""
        showcase = get_showcase_controller()
        
        # Test multiple showcase generations for consistency
        response_times = []
        
        for i in range(5):
            incident_data = {
                "title": f"Performance Test Incident {i}",
                "description": f"Performance validation test {i}",
                "severity": "high",
                "affected_users": 10000,
                "revenue_impact_per_minute": 1500.0
            }
            
            start_time = time.time()
            showcase_response = await showcase.generate_demo_showcase(incident_data)
            response_time = time.time() - start_time
            
            response_times.append(response_time)
            
            # Validate individual response
            assert showcase_response is not None
            assert showcase_response.execution_time < self.PERFORMANCE_TARGETS["showcase_response_time_seconds"]
        
        # Validate performance consistency
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        std_dev = statistics.stdev(response_times) if len(response_times) > 1 else 0
        
        assert avg_response_time < self.PERFORMANCE_TARGETS["showcase_response_time_seconds"]
        assert max_response_time < self.PERFORMANCE_TARGETS["showcase_response_time_seconds"] * 1.2  # 20% tolerance
        assert std_dev < 5.0  # Response time should be consistent
        
        print(f"Showcase performance: avg={avg_response_time:.2f}s, max={max_response_time:.2f}s, std={std_dev:.2f}s")
    
    @pytest.mark.asyncio
    async def test_3d_visualization_performance(self):
        """Test 3D visualization meets FPS targets."""
        visual_3d = get_visual_3d_integration()
        
        # Ensure streaming is active
        if not visual_3d.streaming_active:
            await visual_3d.start_real_time_streaming()
            await asyncio.sleep(2)  # Allow startup
        
        # Monitor FPS over time
        fps_samples = []
        sample_count = 10
        
        for i in range(sample_count):
            viz_status = await visual_3d.get_visualization_status()
            current_fps = viz_status.get("actual_fps", 0)
            fps_samples.append(current_fps)
            
            # Add some load to test performance under stress
            if i % 2 == 0:
                await visual_3d.register_agent(f"perf_test_agent_{i}", "detection")
                await visual_3d.update_agent_state(f"perf_test_agent_{i}", "processing", 0.8)
            
            await asyncio.sleep(0.5)  # Sample every 500ms
        
        # Validate FPS performance
        avg_fps = statistics.mean(fps_samples)
        min_fps = min(fps_samples)
        
        target_fps = self.PERFORMANCE_TARGETS["3d_visualization_fps"]
        assert avg_fps >= target_fps * 0.9, f"Average FPS too low: {avg_fps:.1f} < {target_fps * 0.9:.1f}"
        assert min_fps >= target_fps * 0.8, f"Minimum FPS too low: {min_fps:.1f} < {target_fps * 0.8:.1f}"
        
        print(f"3D visualization performance: avg_fps={avg_fps:.1f}, min_fps={min_fps:.1f}, target={target_fps}")
    
    @pytest.mark.asyncio
    async def test_websocket_message_latency(self):
        """Test WebSocket message latency meets targets."""
        websocket_manager = get_websocket_manager()
        
        # Test message broadcasting latency
        latencies = []
        message_count = 20
        
        for i in range(message_count):
            start_time = time.time()
            
            # Broadcast a test message
            await websocket_manager.broadcast_agent_action(
                f"latency_test_agent_{i}",
                f"Latency test message {i}",
                {"test": True, "timestamp": start_time},
                0.8
            )
            
            # Measure time to complete broadcast
            latency_ms = (time.time() - start_time) * 1000
            latencies.append(latency_ms)
            
            await asyncio.sleep(0.1)  # Small delay between messages
        
        # Validate latency performance
        avg_latency = statistics.mean(latencies)
        max_latency = max(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
        
        target_latency = self.PERFORMANCE_TARGETS["websocket_message_latency_ms"]
        assert avg_latency < target_latency, f"Average latency too high: {avg_latency:.1f}ms > {target_latency}ms"
        assert p95_latency < target_latency * 2, f"P95 latency too high: {p95_latency:.1f}ms > {target_latency * 2}ms"
        
        print(f"WebSocket performance: avg={avg_latency:.1f}ms, max={max_latency:.1f}ms, p95={p95_latency:.1f}ms")
    
    @pytest.mark.asyncio
    async def test_agent_coordination_performance(self):
        """Test agent coordination meets timing targets."""
        visual_3d = get_visual_3d_integration()
        websocket_manager = get_websocket_manager()
        
        # Test coordination workflow timing
        coordination_times = []
        agent_count = 5
        
        for test_run in range(3):
            start_time = time.time()
            
            # Simulate agent coordination workflow
            agents = []
            for i in range(agent_count):
                agent_id = f"coord_test_agent_{test_run}_{i}"
                agents.append(agent_id)
                
                # Register agent
                await visual_3d.register_agent(agent_id, "detection")
                
                # Update state
                await visual_3d.update_agent_state(agent_id, "processing", 0.8)
                
                # Broadcast action
                await websocket_manager.broadcast_agent_action(
                    agent_id,
                    f"Coordination test action {i}",
                    {"coordination_test": True, "agent_index": i},
                    0.8
                )
            
            # Create connections between agents
            for i in range(len(agents) - 1):
                await visual_3d.create_agent_connection(
                    agents[i], agents[i + 1], "coordination", 0.9, 2000
                )
            
            coordination_time = time.time() - start_time
            coordination_times.append(coordination_time)
        
        # Validate coordination performance
        avg_coordination_time = statistics.mean(coordination_times)
        max_coordination_time = max(coordination_times)
        
        target_time = self.PERFORMANCE_TARGETS["agent_coordination_time_seconds"]
        assert avg_coordination_time < target_time, f"Average coordination time too high: {avg_coordination_time:.2f}s > {target_time}s"
        assert max_coordination_time < target_time * 1.5, f"Max coordination time too high: {max_coordination_time:.2f}s > {target_time * 1.5}s"
        
        print(f"Agent coordination performance: avg={avg_coordination_time:.2f}s, max={max_coordination_time:.2f}s")
    
    @pytest.mark.asyncio
    async def test_monitoring_collection_performance(self):
        """Test monitoring collection meets interval targets."""
        monitoring = get_enhanced_monitoring_integration()
        
        # Ensure monitoring is active
        if not monitoring.monitoring_active:
            await monitoring.start_enhanced_monitoring()
            await asyncio.sleep(2)  # Allow startup
        
        # Monitor collection performance
        status = await monitoring.get_monitoring_status()
        collection_interval = status.get("collection_interval_seconds", 0)
        
        target_interval = self.PERFORMANCE_TARGETS["monitoring_collection_interval_seconds"]
        assert collection_interval <= target_interval, f"Collection interval too high: {collection_interval}s > {target_interval}s"
        
        # Test metrics generation performance
        start_time = time.time()
        metrics = monitoring.get_prometheus_metrics()
        metrics_generation_time = time.time() - start_time
        
        assert metrics_generation_time < 1.0, f"Metrics generation too slow: {metrics_generation_time:.2f}s"
        assert len(metrics) > 100, f"Insufficient metrics generated: {len(metrics)} chars"
        
        print(f"Monitoring performance: interval={collection_interval}s, metrics_gen={metrics_generation_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_concurrent_load_performance(self):
        """Test system performance under concurrent load."""
        showcase = get_showcase_controller()
        visual_3d = get_visual_3d_integration()
        websocket_manager = get_websocket_manager()
        
        # Define concurrent load parameters
        concurrent_showcases = 3
        concurrent_agents = 10
        concurrent_messages = 20
        
        start_time = time.time()
        
        # Create concurrent tasks
        tasks = []
        
        # Concurrent showcase operations
        for i in range(concurrent_showcases):
            incident_data = {
                "title": f"Load Test Incident {i}",
                "description": f"Concurrent load test {i}",
                "severity": "high",
                "affected_users": 5000 + i * 1000,
                "revenue_impact_per_minute": 1000.0 + i * 200
            }
            tasks.append(showcase.generate_demo_showcase(incident_data))
        
        # Concurrent agent operations
        for i in range(concurrent_agents):
            agent_id = f"load_test_agent_{i}"
            tasks.append(visual_3d.register_agent(agent_id, "detection"))
        
        # Concurrent WebSocket messages
        for i in range(concurrent_messages):
            tasks.append(websocket_manager.broadcast_agent_action(
                f"load_test_agent_{i % concurrent_agents}",
                f"Load test message {i}",
                {"load_test": True, "message_id": i},
                0.8
            ))
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # Validate performance under load
        assert total_time < 45.0, f"Concurrent load test took too long: {total_time:.2f}s"
        
        # Check for exceptions
        exceptions = [r for r in results if isinstance(r, Exception)]
        exception_rate = len(exceptions) / len(results)
        assert exception_rate < 0.1, f"Too many exceptions under load: {exception_rate:.1%}"
        
        # Verify system is still responsive after load
        viz_status = await visual_3d.get_visualization_status()
        assert viz_status is not None
        assert viz_status["agents_count"] >= concurrent_agents * 0.8  # Allow some failures
        
        print(f"Concurrent load performance: {total_time:.2f}s, {len(exceptions)} exceptions out of {len(results)} operations")
    
    @pytest.mark.asyncio
    async def test_memory_usage_stability(self):
        """Test memory usage remains stable under extended operation."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        visual_3d = get_visual_3d_integration()
        websocket_manager = get_websocket_manager()
        
        # Run extended operations
        operation_count = 100
        memory_samples = []
        
        for i in range(operation_count):
            # Create and clean up agents
            agent_id = f"memory_test_agent_{i}"
            await visual_3d.register_agent(agent_id, "detection")
            await visual_3d.update_agent_state(agent_id, "processing", 0.8)
            
            # Broadcast messages
            await websocket_manager.broadcast_agent_action(
                agent_id,
                f"Memory test action {i}",
                {"memory_test": True, "iteration": i},
                0.8
            )
            
            # Sample memory every 10 operations
            if i % 10 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_samples.append(current_memory)
            
            # Small delay to allow cleanup
            if i % 20 == 0:
                await asyncio.sleep(0.1)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - initial_memory
        max_memory = max(memory_samples) if memory_samples else final_memory
        
        # Validate memory stability
        assert memory_growth < 100, f"Excessive memory growth: {memory_growth:.1f}MB"
        assert max_memory < initial_memory + 150, f"Peak memory too high: {max_memory:.1f}MB"
        
        print(f"Memory stability: initial={initial_memory:.1f}MB, final={final_memory:.1f}MB, growth={memory_growth:.1f}MB")
    
    @pytest.mark.asyncio
    async def test_error_recovery_performance(self):
        """Test system recovery performance after errors."""
        visual_3d = get_visual_3d_integration()
        monitoring = get_enhanced_monitoring_integration()
        
        # Record initial state
        initial_viz_status = await visual_3d.get_visualization_status()
        initial_monitoring_status = await monitoring.get_monitoring_status()
        
        # Simulate errors and measure recovery time
        recovery_times = []
        
        for test_run in range(3):
            # Simulate component failure by stopping services
            start_time = time.time()
            
            if visual_3d.streaming_active:
                await visual_3d.stop_real_time_streaming()
            
            if monitoring.monitoring_active:
                await monitoring.stop_enhanced_monitoring()
            
            # Restart services
            await visual_3d.start_real_time_streaming()
            await monitoring.start_enhanced_monitoring()
            
            # Wait for full recovery
            recovery_complete = False
            recovery_start = time.time()
            
            while not recovery_complete and (time.time() - recovery_start) < 30:
                viz_status = await visual_3d.get_visualization_status()
                monitoring_status = await monitoring.get_monitoring_status()
                
                if (viz_status["streaming_active"] and 
                    monitoring_status["monitoring_active"]):
                    recovery_complete = True
                else:
                    await asyncio.sleep(0.5)
            
            recovery_time = time.time() - start_time
            recovery_times.append(recovery_time)
            
            assert recovery_complete, f"Recovery not completed within timeout for run {test_run}"
        
        # Validate recovery performance
        avg_recovery_time = statistics.mean(recovery_times)
        max_recovery_time = max(recovery_times)
        
        assert avg_recovery_time < 10.0, f"Average recovery time too high: {avg_recovery_time:.2f}s"
        assert max_recovery_time < 15.0, f"Max recovery time too high: {max_recovery_time:.2f}s"
        
        print(f"Error recovery performance: avg={avg_recovery_time:.2f}s, max={max_recovery_time:.2f}s")
    
    @pytest.mark.asyncio
    async def test_overall_system_availability(self):
        """Test overall system availability meets targets."""
        showcase = get_showcase_controller()
        visual_3d = get_visual_3d_integration()
        monitoring = get_enhanced_monitoring_integration()
        
        # Test system availability over multiple operations
        total_operations = 50
        successful_operations = 0
        
        for i in range(total_operations):
            try:
                # Test showcase operation
                incident_data = {
                    "title": f"Availability Test {i}",
                    "description": f"System availability test {i}",
                    "severity": "medium",
                    "affected_users": 1000,
                    "revenue_impact_per_minute": 500.0
                }
                
                showcase_response = await showcase.generate_demo_showcase(incident_data)
                
                # Test 3D visualization operation
                agent_id = f"availability_test_agent_{i}"
                await visual_3d.register_agent(agent_id, "detection")
                await visual_3d.update_agent_state(agent_id, "processing", 0.8)
                
                # Test monitoring operation
                status = await monitoring.get_monitoring_status()
                
                # If all operations succeeded, count as successful
                if (showcase_response is not None and 
                    status is not None):
                    successful_operations += 1
                
            except Exception as e:
                print(f"Operation {i} failed: {e}")
                # Continue testing even if some operations fail
                continue
            
            # Small delay between operations
            await asyncio.sleep(0.1)
        
        # Calculate availability
        availability_percentage = (successful_operations / total_operations) * 100
        target_availability = self.PERFORMANCE_TARGETS["system_availability_percentage"]
        
        assert availability_percentage >= target_availability, f"System availability too low: {availability_percentage:.1f}% < {target_availability}%"
        
        print(f"System availability: {availability_percentage:.1f}% ({successful_operations}/{total_operations} operations successful)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])