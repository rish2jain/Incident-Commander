"""
System Load Testing.

Load tests for validating system performance under high concurrent usage,
simulating multiple judges and demo scenarios running simultaneously.
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import pytest

from src.services.showcase_controller import get_showcase_controller
from src.services.visual_3d_integration import get_visual_3d_integration
from src.services.enhanced_monitoring_integration import get_enhanced_monitoring_integration
from src.services.websocket_manager import get_websocket_manager


class SystemLoadTester:
    """System load testing utility."""
    
    def __init__(self):
        self.showcase = get_showcase_controller()
        self.visual_3d = get_visual_3d_integration()
        self.monitoring = get_enhanced_monitoring_integration()
        self.websocket_manager = get_websocket_manager()
        
        self.results = {
            "showcase_operations": [],
            "3d_operations": [],
            "websocket_operations": [],
            "errors": []
        }
    
    async def simulate_judge_session(self, judge_id: int, session_duration: int = 60) -> Dict[str, Any]:
        """Simulate a judge session with multiple operations."""
        session_start = time.time()
        session_results = {
            "judge_id": judge_id,
            "operations": 0,
            "errors": 0,
            "showcase_calls": 0,
            "3d_interactions": 0,
            "websocket_messages": 0
        }
        
        while (time.time() - session_start) < session_duration:
            try:
                # Simulate showcase demonstration
                incident_data = {
                    "title": f"Judge {judge_id} Demo Incident",
                    "description": f"Load test incident from judge {judge_id}",
                    "severity": "high",
                    "affected_users": 5000 + judge_id * 100,
                    "revenue_impact_per_minute": 1000.0 + judge_id * 50
                }
                
                start_time = time.time()
                showcase_response = await self.showcase.generate_demo_showcase(incident_data)
                showcase_time = time.time() - start_time
                
                self.results["showcase_operations"].append(showcase_time)
                session_results["showcase_calls"] += 1
                
                # Simulate 3D visualization interactions
                agent_id = f"judge_{judge_id}_agent_{session_results['3d_interactions']}"
                
                start_time = time.time()
                await self.visual_3d.register_agent(agent_id, "detection")
                await self.visual_3d.update_agent_state(agent_id, "processing", 0.8)
                viz_time = time.time() - start_time
                
                self.results["3d_operations"].append(viz_time)
                session_results["3d_interactions"] += 1
                
                # Simulate WebSocket messages
                start_time = time.time()
                await self.websocket_manager.broadcast_agent_action(
                    agent_id,
                    f"Judge {judge_id} interaction",
                    {"judge_id": judge_id, "session_time": time.time() - session_start},
                    0.8
                )
                websocket_time = time.time() - start_time
                
                self.results["websocket_operations"].append(websocket_time)
                session_results["websocket_messages"] += 1
                
                session_results["operations"] += 1
                
                # Simulate thinking time between operations
                await asyncio.sleep(2 + judge_id * 0.1)  # Stagger operations
                
            except Exception as e:
                self.results["errors"].append({
                    "judge_id": judge_id,
                    "error": str(e),
                    "timestamp": time.time()
                })
                session_results["errors"] += 1
                
                # Continue despite errors
                await asyncio.sleep(1)
        
        session_results["duration"] = time.time() - session_start
        return session_results
    
    async def run_concurrent_load_test(self, concurrent_judges: int = 10, 
                                     session_duration: int = 60) -> Dict[str, Any]:
        """Run concurrent load test with multiple simulated judges."""
        print(f"Starting load test with {concurrent_judges} concurrent judges for {session_duration}s")
        
        # Start all judge sessions concurrently
        start_time = time.time()
        
        judge_tasks = [
            self.simulate_judge_session(judge_id, session_duration)
            for judge_id in range(concurrent_judges)
        ]
        
        session_results = await asyncio.gather(*judge_tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        
        # Analyze results
        successful_sessions = [r for r in session_results if not isinstance(r, Exception)]
        failed_sessions = [r for r in session_results if isinstance(r, Exception)]
        
        # Calculate performance metrics
        total_operations = sum(s["operations"] for s in successful_sessions)
        total_errors = sum(s["errors"] for s in successful_sessions) + len(failed_sessions)
        
        showcase_stats = self._calculate_stats(self.results["showcase_operations"])
        viz_stats = self._calculate_stats(self.results["3d_operations"])
        websocket_stats = self._calculate_stats(self.results["websocket_operations"])
        
        return {
            "test_config": {
                "concurrent_judges": concurrent_judges,
                "session_duration": session_duration,
                "total_test_time": total_time
            },
            "session_results": {
                "successful_sessions": len(successful_sessions),
                "failed_sessions": len(failed_sessions),
                "total_operations": total_operations,
                "total_errors": total_errors,
                "error_rate": total_errors / (total_operations + total_errors) if (total_operations + total_errors) > 0 else 0,
                "operations_per_second": total_operations / total_time if total_time > 0 else 0
            },
            "performance_metrics": {
                "showcase_operations": showcase_stats,
                "3d_operations": viz_stats,
                "websocket_operations": websocket_stats
            },
            "detailed_sessions": successful_sessions,
            "errors": self.results["errors"]
        }
    
    def _calculate_stats(self, times: List[float]) -> Dict[str, float]:
        """Calculate performance statistics."""
        if not times:
            return {"count": 0, "avg": 0, "min": 0, "max": 0, "p95": 0, "p99": 0}
        
        sorted_times = sorted(times)
        return {
            "count": len(times),
            "avg": statistics.mean(times),
            "min": min(times),
            "max": max(times),
            "p95": sorted_times[int(len(sorted_times) * 0.95)] if len(sorted_times) > 1 else sorted_times[0],
            "p99": sorted_times[int(len(sorted_times) * 0.99)] if len(sorted_times) > 1 else sorted_times[0]
        }


class TestSystemLoad:
    """System load tests."""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_light_load(self):
        """Test system under light concurrent load."""
        tester = SystemLoadTester()
        
        # Light load: 3 concurrent judges for 30 seconds
        results = await tester.run_concurrent_load_test(
            concurrent_judges=3,
            session_duration=30
        )
        
        # Validate light load performance
        assert results["session_results"]["successful_sessions"] >= 2, "Too many session failures under light load"
        assert results["session_results"]["error_rate"] < 0.1, f"Error rate too high: {results['session_results']['error_rate']:.1%}"
        assert results["session_results"]["operations_per_second"] > 0.5, "Operations per second too low"
        
        # Validate response times
        showcase_stats = results["performance_metrics"]["showcase_operations"]
        assert showcase_stats["avg"] < 30.0, f"Average showcase time too high: {showcase_stats['avg']:.2f}s"
        assert showcase_stats["p95"] < 45.0, f"P95 showcase time too high: {showcase_stats['p95']:.2f}s"
        
        print(f"Light load test results: {results['session_results']['operations_per_second']:.1f} ops/sec, "
              f"{results['session_results']['error_rate']:.1%} error rate")
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_moderate_load(self):
        """Test system under moderate concurrent load."""
        tester = SystemLoadTester()
        
        # Moderate load: 5 concurrent judges for 45 seconds
        results = await tester.run_concurrent_load_test(
            concurrent_judges=5,
            session_duration=45
        )
        
        # Validate moderate load performance
        assert results["session_results"]["successful_sessions"] >= 4, "Too many session failures under moderate load"
        assert results["session_results"]["error_rate"] < 0.15, f"Error rate too high: {results['session_results']['error_rate']:.1%}"
        assert results["session_results"]["operations_per_second"] > 0.8, "Operations per second too low"
        
        # Validate response times (allow some degradation under load)
        showcase_stats = results["performance_metrics"]["showcase_operations"]
        assert showcase_stats["avg"] < 35.0, f"Average showcase time too high: {showcase_stats['avg']:.2f}s"
        assert showcase_stats["p95"] < 50.0, f"P95 showcase time too high: {showcase_stats['p95']:.2f}s"
        
        print(f"Moderate load test results: {results['session_results']['operations_per_second']:.1f} ops/sec, "
              f"{results['session_results']['error_rate']:.1%} error rate")
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_heavy_load(self):
        """Test system under heavy concurrent load."""
        tester = SystemLoadTester()
        
        # Heavy load: 10 concurrent judges for 60 seconds
        results = await tester.run_concurrent_load_test(
            concurrent_judges=10,
            session_duration=60
        )
        
        # Validate heavy load performance (more lenient thresholds)
        assert results["session_results"]["successful_sessions"] >= 7, "Too many session failures under heavy load"
        assert results["session_results"]["error_rate"] < 0.25, f"Error rate too high: {results['session_results']['error_rate']:.1%}"
        assert results["session_results"]["operations_per_second"] > 1.0, "Operations per second too low"
        
        # Validate response times (allow more degradation under heavy load)
        showcase_stats = results["performance_metrics"]["showcase_operations"]
        assert showcase_stats["avg"] < 45.0, f"Average showcase time too high: {showcase_stats['avg']:.2f}s"
        assert showcase_stats["p95"] < 60.0, f"P95 showcase time too high: {showcase_stats['p95']:.2f}s"
        
        print(f"Heavy load test results: {results['session_results']['operations_per_second']:.1f} ops/sec, "
              f"{results['session_results']['error_rate']:.1%} error rate")
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_stress_load(self):
        """Test system under stress load to find breaking point."""
        tester = SystemLoadTester()
        
        # Stress load: 15 concurrent judges for 30 seconds
        results = await tester.run_concurrent_load_test(
            concurrent_judges=15,
            session_duration=30
        )
        
        # Validate stress load performance (very lenient thresholds)
        assert results["session_results"]["successful_sessions"] >= 10, "System completely failed under stress"
        assert results["session_results"]["error_rate"] < 0.4, f"Error rate too high: {results['session_results']['error_rate']:.1%}"
        
        # System should still be somewhat responsive
        assert results["session_results"]["operations_per_second"] > 0.5, "System became unresponsive"
        
        print(f"Stress load test results: {results['session_results']['operations_per_second']:.1f} ops/sec, "
              f"{results['session_results']['error_rate']:.1%} error rate")
        
        # Log detailed error information for analysis
        if results["errors"]:
            print(f"Stress test errors ({len(results['errors'])} total):")
            for error in results["errors"][:5]:  # Show first 5 errors
                print(f"  Judge {error['judge_id']}: {error['error']}")
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_sustained_load(self):
        """Test system under sustained load over extended period."""
        tester = SystemLoadTester()
        
        # Sustained load: 5 concurrent judges for 2 minutes
        results = await tester.run_concurrent_load_test(
            concurrent_judges=5,
            session_duration=120
        )
        
        # Validate sustained load performance
        assert results["session_results"]["successful_sessions"] >= 4, "System degraded under sustained load"
        assert results["session_results"]["error_rate"] < 0.2, f"Error rate too high: {results['session_results']['error_rate']:.1%}"
        
        # Check for performance degradation over time
        showcase_stats = results["performance_metrics"]["showcase_operations"]
        assert showcase_stats["avg"] < 40.0, f"Average response time degraded: {showcase_stats['avg']:.2f}s"
        
        # Verify system stability (no memory leaks, etc.)
        total_operations = results["session_results"]["total_operations"]
        assert total_operations > 50, f"Too few operations completed: {total_operations}"
        
        print(f"Sustained load test results: {total_operations} total operations, "
              f"{results['session_results']['operations_per_second']:.1f} ops/sec average")
    
    @pytest.mark.asyncio
    async def test_burst_load(self):
        """Test system response to sudden burst of concurrent requests."""
        showcase = get_showcase_controller()
        visual_3d = get_visual_3d_integration()
        websocket_manager = get_websocket_manager()
        
        # Create burst of concurrent operations
        burst_size = 20
        tasks = []
        
        # Prepare incident data
        incident_data = {
            "title": "Burst Load Test Incident",
            "description": "Testing system response to burst load",
            "severity": "high",
            "affected_users": 10000,
            "revenue_impact_per_minute": 2000.0
        }
        
        start_time = time.time()
        
        # Create burst of showcase operations
        for i in range(burst_size):
            tasks.append(showcase.generate_demo_showcase(incident_data))
        
        # Execute burst
        results = await asyncio.gather(*tasks, return_exceptions=True)
        burst_time = time.time() - start_time
        
        # Analyze burst results
        successful_operations = [r for r in results if not isinstance(r, Exception)]
        failed_operations = [r for r in results if isinstance(r, Exception)]
        
        success_rate = len(successful_operations) / len(results)
        operations_per_second = len(successful_operations) / burst_time
        
        # Validate burst performance
        assert success_rate >= 0.7, f"Burst success rate too low: {success_rate:.1%}"
        assert burst_time < 60.0, f"Burst took too long: {burst_time:.2f}s"
        assert operations_per_second > 0.5, f"Burst throughput too low: {operations_per_second:.1f} ops/sec"
        
        print(f"Burst load test: {len(successful_operations)}/{len(results)} successful in {burst_time:.2f}s "
              f"({operations_per_second:.1f} ops/sec)")
    
    @pytest.mark.asyncio
    async def test_mixed_operation_load(self):
        """Test system under mixed operation types load."""
        showcase = get_showcase_controller()
        visual_3d = get_visual_3d_integration()
        monitoring = get_enhanced_monitoring_integration()
        websocket_manager = get_websocket_manager()
        
        # Mixed operations test
        operation_count = 30
        tasks = []
        operation_types = []
        
        for i in range(operation_count):
            operation_type = i % 4  # Cycle through 4 operation types
            
            if operation_type == 0:  # Showcase operation
                incident_data = {
                    "title": f"Mixed Load Test {i}",
                    "description": f"Mixed operation test {i}",
                    "severity": "medium",
                    "affected_users": 2000 + i * 100,
                    "revenue_impact_per_minute": 500.0 + i * 25
                }
                tasks.append(showcase.generate_demo_showcase(incident_data))
                operation_types.append("showcase")
                
            elif operation_type == 1:  # 3D visualization operation
                agent_id = f"mixed_test_agent_{i}"
                async def viz_operation():
                    await visual_3d.register_agent(agent_id, "detection")
                    await visual_3d.update_agent_state(agent_id, "processing", 0.8)
                    return "viz_complete"
                
                tasks.append(viz_operation())
                operation_types.append("visualization")
                
            elif operation_type == 2:  # Monitoring operation
                tasks.append(monitoring.get_monitoring_status())
                operation_types.append("monitoring")
                
            else:  # WebSocket operation
                tasks.append(websocket_manager.broadcast_agent_action(
                    f"mixed_test_agent_{i}",
                    f"Mixed test message {i}",
                    {"mixed_test": True, "operation_id": i},
                    0.8
                ))
                operation_types.append("websocket")
        
        # Execute mixed operations
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # Analyze mixed operation results
        successful_ops = sum(1 for r in results if not isinstance(r, Exception))
        failed_ops = len(results) - successful_ops
        
        success_rate = successful_ops / len(results)
        operations_per_second = successful_ops / total_time
        
        # Validate mixed operation performance
        assert success_rate >= 0.8, f"Mixed operation success rate too low: {success_rate:.1%}"
        assert total_time < 45.0, f"Mixed operations took too long: {total_time:.2f}s"
        assert operations_per_second > 1.0, f"Mixed operation throughput too low: {operations_per_second:.1f} ops/sec"
        
        # Analyze by operation type
        type_results = {}
        for i, (result, op_type) in enumerate(zip(results, operation_types)):
            if op_type not in type_results:
                type_results[op_type] = {"success": 0, "total": 0}
            type_results[op_type]["total"] += 1
            if not isinstance(result, Exception):
                type_results[op_type]["success"] += 1
        
        print(f"Mixed load test: {successful_ops}/{len(results)} successful in {total_time:.2f}s")
        for op_type, stats in type_results.items():
            success_rate = stats["success"] / stats["total"]
            print(f"  {op_type}: {stats['success']}/{stats['total']} ({success_rate:.1%})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "not slow"])  # Run fast tests by default