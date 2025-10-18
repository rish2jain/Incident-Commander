#!/usr/bin/env python3
"""
Quick test script to verify WebSocket functionality.

Run this after starting the FastAPI server to test real-time updates.
"""

import asyncio
import json
import websockets
from datetime import datetime, timezone


async def test_websocket_connection():
    """Test WebSocket connection and message reception."""
    uri = "ws://localhost:8000/ws"
    
    try:
        print(f"🔌 Connecting to {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected successfully!")
            
            # Send ping message
            ping_message = {
                "type": "ping",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            await websocket.send(json.dumps(ping_message))
            print("📤 Sent ping message")
            
            # Listen for messages for 30 seconds
            print("👂 Listening for messages (30 seconds)...")
            
            try:
                while True:
                    message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    data = json.loads(message)
                    
                    print(f"📨 Received: {data['type']}")
                    if data.get('data'):
                        print(f"   Data: {json.dumps(data['data'], indent=2)}")
                    
            except asyncio.TimeoutError:
                print("⏰ Timeout reached - test complete")
                
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")


async def test_incident_trigger():
    """Test triggering an incident and receiving real-time updates."""
    import aiohttp
    
    # Trigger a demo incident
    async with aiohttp.ClientSession() as session:
        try:
            print("\n🎯 Triggering demo incident...")
            
            async with session.post(
                "http://localhost:8000/demo/scenarios/database_cascade"
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Demo incident triggered: {result['incident_id']}")
                else:
                    print(f"❌ Failed to trigger incident: {response.status}")
                    
        except Exception as e:
            print(f"❌ Failed to trigger incident: {e}")


async def main():
    """Run WebSocket tests."""
    print("🚀 Starting WebSocket functionality test")
    print("=" * 50)
    
    # Test 1: Basic WebSocket connection
    await test_websocket_connection()
    
    # Test 2: Trigger incident and watch real-time updates
    print("\n" + "=" * 50)
    print("🎭 Testing real-time incident processing")
    
    # Start WebSocket listener in background
    websocket_task = asyncio.create_task(test_websocket_connection())
    
    # Wait a moment then trigger incident
    await asyncio.sleep(2)
    await test_incident_trigger()
    
    # Let WebSocket listener continue for a bit
    try:
        await asyncio.wait_for(websocket_task, timeout=60.0)
    except asyncio.TimeoutError:
        websocket_task.cancel()
    
    print("\n✅ WebSocket test complete!")


if __name__ == "__main__":
    asyncio.run(main())