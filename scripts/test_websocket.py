#!/usr/bin/env python3
"""
WebSocket Connection Test

Tests the WebSocket connection to identify ops dashboard connection issues.
"""

import asyncio
import websockets
import json
from datetime import datetime

async def test_websocket_connection():
    """Test WebSocket connection to the backend"""
    
    # Test different possible WebSocket URLs
    urls_to_test = [
        "ws://localhost:8000/ws",
        "ws://localhost:8000/dashboard/ws",
        "ws://localhost:8000/dashboard/ws?client_id=test&dashboard_type=ops"
    ]
    
    for url in urls_to_test:
        print(f"\n🔍 Testing WebSocket URL: {url}")
        try:
            async with websockets.connect(url) as websocket:
                print(f"✅ Connected successfully to {url}")
                
                # Send a test message
                test_message = {
                    "type": "ping",
                    "timestamp": datetime.now().isoformat(),
                    "client_id": "test_client"
                }
                
                await websocket.send(json.dumps(test_message))
                print(f"📤 Sent test message: {test_message}")
                
                # Wait for response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=3)
                    print(f"📥 Received response: {response}")
                except asyncio.TimeoutError:
                    print("⏰ No response received within 3 seconds")
                
                return url  # Return successful URL
                
        except websockets.exceptions.InvalidStatus as e:
            print(f"❌ Invalid status code: {e}")
        except websockets.exceptions.ConnectionClosed as e:
            print(f"❌ Connection closed: {e}")
        except OSError as e:
            print(f"❌ Connection failed: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
    
    print("\n❌ All WebSocket URLs failed to connect")
    return None

async def main():
    """Main test function"""
    print("🔌 WebSocket Connection Test")
    print("=" * 50)
    
    successful_url = await test_websocket_connection()
    
    if successful_url:
        print(f"\n✅ WebSocket is working at: {successful_url}")
        print("💡 Update the frontend to use this URL")
    else:
        print("\n❌ WebSocket connection failed")
        print("💡 Check backend WebSocket endpoint configuration")

if __name__ == "__main__":
    asyncio.run(main())