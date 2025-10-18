#!/usr/bin/env python3
"""
Validation script for WebSocket real-time integration.

Tests the critical path WebSocket functionality for hackathon demo.
"""

import asyncio
import json
import sys
from datetime import datetime

try:
    import websockets
    import aiohttp
except ImportError:
    print("❌ Missing dependencies. Install with:")
    print("pip install websockets aiohttp")
    sys.exit(1)


class WebSocketValidator:
    """Validates WebSocket functionality for demo readiness."""
    
    def __init__(self):
        self.api_base = "http://localhost:8000"
        self.ws_url = "ws://localhost:8000/ws"
        self.messages_received = []
        
    async def test_api_health(self):
        """Test API server health."""
        print("🏥 Testing API health...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base}/health") as response:
                    if response.status == 200:
                        print("✅ API server is healthy")
                        return True
                    else:
                        print(f"❌ API health check failed: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ API connection failed: {e}")
            return False
    
    async def test_websocket_connection(self):
        """Test WebSocket connection."""
        print("🔌 Testing WebSocket connection...")
        
        try:
            async with websockets.connect(self.ws_url) as websocket:
                print("✅ WebSocket connected successfully")
                
                # Test ping/pong
                ping_msg = {"type": "ping", "timestamp": datetime.utcnow().isoformat()}
                await websocket.send(json.dumps(ping_msg))
                
                # Wait for welcome message and pong
                for _ in range(2):
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    self.messages_received.append(data)
                    print(f"📨 Received: {data['type']}")
                
                return True
                
        except Exception as e:
            print(f"❌ WebSocket connection failed: {e}")
            return False
    
    async def test_real_time_incident_flow(self):
        """Test complete real-time incident processing flow."""
        print("🎭 Testing real-time incident processing...")
        
        # Start WebSocket listener
        websocket_task = None
        incident_messages = []
        
        try:
            async with websockets.connect(self.ws_url) as websocket:
                print("🔌 WebSocket connected for incident test")
                
                # Start listening for messages
                async def message_listener():
                    try:
                        while True:
                            message = await websocket.recv()
                            data = json.loads(message)
                            incident_messages.append(data)
                            print(f"📡 Real-time update: {data['type']}")
                            
                            if data['type'] == 'agent_action':
                                action = data['data']['action']
                                print(f"   🤖 {action['agent_type']}: {action['description']}")
                            elif data['type'] == 'incident_resolved':
                                print(f"   ✅ Incident resolved!")
                                break
                                
                    except websockets.exceptions.ConnectionClosed:
                        pass
                
                # Start message listener
                websocket_task = asyncio.create_task(message_listener())
                
                # Trigger demo incident
                async with aiohttp.ClientSession() as session:
                    print("🚨 Triggering database cascade scenario...")
                    async with session.post(f"{self.api_base}/demo/scenarios/database_cascade") as response:
                        if response.status == 200:
                            result = await response.json()
                            print(f"✅ Incident triggered: {result['incident_id']}")
                        else:
                            print(f"❌ Failed to trigger incident: {response.status}")
                            return False
                
                # Wait for incident processing to complete
                await asyncio.wait_for(websocket_task, timeout=60.0)
                
                # Validate message flow
                message_types = [msg['type'] for msg in incident_messages]
                expected_types = ['incident_started', 'agent_action', 'incident_resolved']
                
                print(f"\n📊 Message flow analysis:")
                print(f"   Total messages: {len(incident_messages)}")
                print(f"   Message types: {set(message_types)}")
                
                # Check for key message types
                has_incident_start = 'incident_started' in message_types
                has_agent_actions = 'agent_action' in message_types
                has_incident_resolved = 'incident_resolved' in message_types
                
                if has_incident_start and has_agent_actions and has_incident_resolved:
                    print("✅ Complete incident flow validated!")
                    
                    # Count agent actions by type
                    agent_actions = {}
                    for msg in incident_messages:
                        if msg['type'] == 'agent_action':
                            agent_type = msg['data']['action']['agent_type']
                            agent_actions[agent_type] = agent_actions.get(agent_type, 0) + 1
                    
                    print(f"   Agent activity: {agent_actions}")
                    return True
                else:
                    print("❌ Incomplete incident flow")
                    print(f"   Start: {has_incident_start}, Actions: {has_agent_actions}, Resolved: {has_incident_resolved}")
                    return False
                
        except asyncio.TimeoutError:
            print("⏰ Incident processing timeout - may indicate slow performance")
            return False
        except Exception as e:
            print(f"❌ Real-time incident test failed: {e}")
            return False
        finally:
            if websocket_task and not websocket_task.done():
                websocket_task.cancel()
    
    async def run_validation(self):
        """Run complete validation suite."""
        print("🚀 Starting WebSocket Integration Validation")
        print("=" * 60)
        
        results = {}
        
        # Test 1: API Health
        results['api_health'] = await self.test_api_health()
        
        # Test 2: WebSocket Connection
        if results['api_health']:
            results['websocket_connection'] = await self.test_websocket_connection()
        else:
            results['websocket_connection'] = False
            print("⏭️  Skipping WebSocket test - API not available")
        
        # Test 3: Real-time Incident Flow
        if results['websocket_connection']:
            results['realtime_flow'] = await self.test_real_time_incident_flow()
        else:
            results['realtime_flow'] = False
            print("⏭️  Skipping real-time flow test - WebSocket not available")
        
        # Summary
        print("\n" + "=" * 60)
        print("📋 VALIDATION SUMMARY")
        print("=" * 60)
        
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        all_passed = all(results.values())
        
        if all_passed:
            print("\n🎉 ALL TESTS PASSED - Demo ready for hackathon!")
            print("💡 WebSocket real-time integration is working correctly")
        else:
            print("\n⚠️  SOME TESTS FAILED - Demo needs attention")
            print("🔧 Check server logs and fix issues before demo")
        
        return all_passed


async def main():
    """Run WebSocket validation."""
    validator = WebSocketValidator()
    success = await validator.run_validation()
    
    if success:
        print("\n🚀 Ready for hackathon demo!")
        sys.exit(0)
    else:
        print("\n🛠️  Fix issues before demo")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())