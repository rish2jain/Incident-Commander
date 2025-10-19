#!/usr/bin/env python3
"""
Demo Performance Validation Script

Validates that the Incident Commander demo meets performance targets
and provides consistent experience for hackathon presentation.
"""

import asyncio
import json
import os
import statistics
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

try:
    import aiohttp
    import websockets
except ImportError:
    print("❌ Missing dependencies. Install with:")
    print("pip install aiohttp websockets")
    exit(1)


class DemoPerformanceValidator:
    """Validates demo performance and consistency."""
    
    def __init__(self):
        self.api_base = os.environ.get("HACKATHON_API_URL", "http://localhost:8000").rstrip("/")
        self.ws_url = os.environ.get(
            "HACKATHON_WEBSOCKET_URL",
            self.api_base.replace("http", "ws") + "/dashboard/ws"
        )
        self.dashboard_metrics_endpoint = f"{self.api_base}/dashboard/demo-metrics"
        self.performance_targets = {
            "incident_resolution_seconds": 180,  # 3 minutes max
            "api_response_ms": 500,  # 500ms max
            "websocket_latency_ms": 100,  # 100ms max
            "scenario_trigger_ms": 1000,  # 1 second max
        }
        
    async def test_api_performance(self) -> Dict[str, Any]:
        """Test API endpoint performance."""
        print("⚡ Testing API performance...")
        
        endpoints = [
            "/health",
            "/system-status",
            "/dashboard/metrics",
            "/dashboard/demo-metrics"
        ]
        
        results = {}
        
        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints:
                response_times = []
                
                for i in range(5):  # Test each endpoint 5 times
                    start_time = time.time()
                    try:
                        async with session.get(f"{self.api_base}{endpoint}") as response:
                            await response.text()
                            response_time_ms = (time.time() - start_time) * 1000
                            response_times.append(response_time_ms)
                            
                            if response.status != 200:
                                print(f"⚠️  {endpoint}: HTTP {response.status}")
                                
                    except Exception as e:
                        print(f"❌ {endpoint}: {e}")
                        response_times.append(float('inf'))
                
                avg_response_time = statistics.mean(response_times) if response_times else float('inf')
                max_response_time = max(response_times) if response_times else float('inf')
                
                results[endpoint] = {
                    "avg_ms": avg_response_time,
                    "max_ms": max_response_time,
                    "meets_target": avg_response_time <= self.performance_targets["api_response_ms"]
                }
                
                status = "✅" if results[endpoint]["meets_target"] else "❌"
                print(f"  {status} {endpoint}: {avg_response_time:.1f}ms avg, {max_response_time:.1f}ms max")
        
        return results
    
    async def test_websocket_latency(self) -> Dict[str, Any]:
        """Test WebSocket connection and message latency."""
        print("🔌 Testing WebSocket latency...")
        
        latencies = []
        
        try:
            async with websockets.connect(self.ws_url) as websocket:
                # Test ping/pong latency
                for i in range(10):
                    start_time = time.time()
                    
                    ping_msg = {
                        "type": "ping",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    await websocket.send(json.dumps(ping_msg))
                    
                    # Wait for any response (welcome message or pong)
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        latency_ms = (time.time() - start_time) * 1000
                        latencies.append(latency_ms)
                    except asyncio.TimeoutError:
                        latencies.append(float('inf'))
                    
                    await asyncio.sleep(0.1)  # Small delay between tests
                
        except Exception as e:
            print(f"❌ WebSocket connection failed: {e}")
            return {"error": str(e), "meets_target": False}
        
        if latencies:
            avg_latency = statistics.mean(latencies)
            max_latency = max(latencies)
            meets_target = avg_latency <= self.performance_targets["websocket_latency_ms"]
            
            status = "✅" if meets_target else "❌"
            print(f"  {status} WebSocket latency: {avg_latency:.1f}ms avg, {max_latency:.1f}ms max")
            
            return {
                "avg_ms": avg_latency,
                "max_ms": max_latency,
                "meets_target": meets_target
            }
        else:
            return {"error": "No successful latency measurements", "meets_target": False}
    
    async def test_scenario_trigger_performance(self) -> Dict[str, Any]:
        """Test demo scenario trigger performance."""
        print("🎯 Testing scenario trigger performance...")
        
        results = {}
        
        async with aiohttp.ClientSession() as session:
            scenarios = await self._load_available_scenarios(session)
            if not scenarios:
                print("⚠️  No scenarios available from demo metrics")
                return {"error": "No scenarios available", "meets_target": False}

            for scenario in scenarios:
                trigger_times = []
                
                for i in range(3):  # Test each scenario 3 times
                    start_time = time.time()
                    
                    try:
                        async with session.post(
                            f"{self.api_base}/dashboard/trigger-demo",
                            json={"scenario_type": scenario}
                        ) as response:
                            await response.text()
                            trigger_time_ms = (time.time() - start_time) * 1000
                            trigger_times.append(trigger_time_ms)
                            
                            if response.status != 200:
                                print(f"⚠️  {scenario}: HTTP {response.status}")
                    
                    except Exception as e:
                        print(f"❌ {scenario}: {e}")
                        trigger_times.append(float('inf'))
                    
                    # Wait between triggers to avoid overwhelming system
                    await asyncio.sleep(2)
                
                if trigger_times:
                    avg_trigger_time = statistics.mean(trigger_times)
                    max_trigger_time = max(trigger_times)
                    meets_target = avg_trigger_time <= self.performance_targets["scenario_trigger_ms"]

                    results[scenario] = {
                        "avg_ms": avg_trigger_time,
                        "max_ms": max_trigger_time,
                        "meets_target": meets_target
                    }

                    status = "✅" if meets_target else "❌"
                    print(f"  {status} {scenario}: {avg_trigger_time:.1f}ms avg, {max_trigger_time:.1f}ms max")

        return results

    async def _load_available_scenarios(self, session: aiohttp.ClientSession) -> List[str]:
        try:
            async with session.get(self.dashboard_metrics_endpoint) as response:
                if response.status != 200:
                    return []
                payload = await response.json()
                scenarios = payload.get("available_scenarios", [])
                # Limit to a few scenarios for quicker validation cycles
                return scenarios[:3]
        except Exception:
            return []

    async def test_end_to_end_incident_flow(self) -> Dict[str, Any]:
        """Test complete incident processing flow timing."""
        print("🔄 Testing end-to-end incident flow...")
        
        incident_times = []
        
        for i in range(3):  # Test 3 complete flows
            print(f"  Testing flow {i+1}/3...")
            
            # Start WebSocket listener
            messages_received = []
            start_time = None
            resolution_time = None
            
            try:
                async with websockets.connect(self.ws_url) as websocket:
                    # Start message listener
                    async def message_listener():
                        nonlocal start_time, resolution_time
                        
                        while True:
                            try:
                                message = await websocket.recv()
                                data = json.loads(message)
                                messages_received.append(data)
                                
                                if data['type'] == 'incident_update':
                                    phase = data.get('data', {}).get('incident', {}).get('phase')
                                    if phase in {"scenario_started", "detecting"} and start_time is None:
                                        start_time = time.time()
                                    if phase == 'resolved':
                                        resolution_time = time.time()
                                        break
                                    
                            except websockets.exceptions.ConnectionClosed:
                                break
                    
                    # Start listener task
                    listener_task = asyncio.create_task(message_listener())
                    
                    # Trigger incident
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            f"{self.api_base}/dashboard/trigger-demo",
                            json={"scenario_type": "memory_leak"}
                        ) as response:
                            if response.status != 200:
                                print(f"❌ Failed to trigger incident: {response.status}")
                                continue
                    
                    # Wait for resolution (max 5 minutes)
                    try:
                        await asyncio.wait_for(listener_task, timeout=300)
                        
                        if start_time and resolution_time:
                            incident_duration = resolution_time - start_time
                            incident_times.append(incident_duration)
                            
                            meets_target = incident_duration <= self.performance_targets["incident_resolution_seconds"]
                            status = "✅" if meets_target else "❌"
                            print(f"    {status} Flow {i+1}: {incident_duration:.1f}s resolution time")
                        else:
                            print(f"    ❌ Flow {i+1}: Incomplete incident flow")
                            
                    except asyncio.TimeoutError:
                        print(f"    ❌ Flow {i+1}: Timeout (>5 minutes)")
                        incident_times.append(float('inf'))
                        
            except Exception as e:
                print(f"    ❌ Flow {i+1}: {e}")
                incident_times.append(float('inf'))
            
            # Wait between tests
            if i < 2:
                await asyncio.sleep(5)
        
        if incident_times:
            valid_times = [t for t in incident_times if t != float('inf')]
            
            if valid_times:
                avg_resolution_time = statistics.mean(valid_times)
                max_resolution_time = max(valid_times)
                meets_target = avg_resolution_time <= self.performance_targets["incident_resolution_seconds"]
                
                return {
                    "avg_seconds": avg_resolution_time,
                    "max_seconds": max_resolution_time,
                    "meets_target": meets_target,
                    "successful_flows": len(valid_times),
                    "total_flows": len(incident_times)
                }
            else:
                return {
                    "error": "No successful incident flows",
                    "meets_target": False,
                    "successful_flows": 0,
                    "total_flows": len(incident_times)
                }
        else:
            return {
                "error": "No incident flow tests completed",
                "meets_target": False
            }
    
    async def run_performance_validation(self) -> Dict[str, Any]:
        """Run complete performance validation suite."""
        print("🚀 Starting Demo Performance Validation")
        print("=" * 60)
        
        results = {}
        
        # Test 1: API Performance
        results['api_performance'] = await self.test_api_performance()
        
        # Test 2: WebSocket Latency
        results['websocket_latency'] = await self.test_websocket_latency()
        
        # Test 3: Scenario Trigger Performance
        results['scenario_triggers'] = await self.test_scenario_trigger_performance()
        
        # Test 4: End-to-End Incident Flow
        results['incident_flow'] = await self.test_end_to_end_incident_flow()
        
        # Generate summary
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE VALIDATION SUMMARY")
        print("=" * 60)
        
        all_targets_met = True
        
        # API Performance Summary
        api_results = results['api_performance']
        api_passed = all(endpoint['meets_target'] for endpoint in api_results.values())
        print(f"API Performance: {'✅ PASS' if api_passed else '❌ FAIL'}")
        if not api_passed:
            all_targets_met = False
        
        # WebSocket Latency Summary
        ws_results = results['websocket_latency']
        ws_passed = ws_results.get('meets_target', False)
        print(f"WebSocket Latency: {'✅ PASS' if ws_passed else '❌ FAIL'}")
        if not ws_passed:
            all_targets_met = False
        
        # Scenario Triggers Summary
        scenario_results = results['scenario_triggers']
        if isinstance(scenario_results, dict) and scenario_results and 'error' not in scenario_results:
            scenario_passed = all(scenario['meets_target'] for scenario in scenario_results.values())
        else:
            scenario_passed = False
        print(f"Scenario Triggers: {'✅ PASS' if scenario_passed else '❌ FAIL'}")
        if not scenario_passed:
            all_targets_met = False
        
        # Incident Flow Summary
        flow_results = results['incident_flow']
        flow_passed = flow_results.get('meets_target', False)
        print(f"Incident Resolution: {'✅ PASS' if flow_passed else '❌ FAIL'}")
        if not flow_passed:
            all_targets_met = False
        
        # Overall Assessment
        print("\n" + "=" * 60)
        if all_targets_met:
            print("🎉 ALL PERFORMANCE TARGETS MET")
            print("✅ Demo is ready for hackathon presentation!")
            print("💡 Consistent sub-3-minute incident resolution achieved")
        else:
            print("⚠️  PERFORMANCE ISSUES DETECTED")
            print("🔧 Address performance issues before demo")
            
            # Provide specific recommendations
            print("\n🛠️  RECOMMENDATIONS:")
            
            if not api_passed:
                print("  • Optimize API endpoint response times")
                print("  • Check for blocking operations in request handlers")
            
            if not ws_passed:
                print("  • Investigate WebSocket connection latency")
                print("  • Ensure WebSocket server is properly configured")
            
            if not scenario_passed:
                print("  • Optimize scenario trigger processing")
                print("  • Check for bottlenecks in incident creation")
            
            if not flow_passed:
                print("  • Investigate incident processing delays")
                print("  • Verify agent coordination timing")
        
        return {
            'results': results,
            'all_targets_met': all_targets_met,
            'summary': {
                'api_performance': api_passed,
                'websocket_latency': ws_passed,
                'scenario_triggers': scenario_passed,
                'incident_flow': flow_passed
            }
        }


async def main():
    """Run demo performance validation."""
    validator = DemoPerformanceValidator()
    
    try:
        validation_results = await validator.run_performance_validation()
        
        if validation_results['all_targets_met']:
            print("\n🚀 Demo performance validated - ready for hackathon!")
            exit(0)
        else:
            print("\n🛠️  Performance optimization needed before demo")
            exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Performance validation cancelled")
        exit(1)
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
