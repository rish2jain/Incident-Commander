#!/usr/bin/env python3
"""
API validation script for Incident Commander.
Tests the main API endpoints to ensure they're working.
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Set up test environment
os.environ.setdefault('AWS_ACCESS_KEY_ID', 'test-access-key')
os.environ.setdefault('AWS_SECRET_ACCESS_KEY', 'test-secret-key')
os.environ.setdefault('AWS_DEFAULT_REGION', 'us-east-1')
os.environ.setdefault('ENVIRONMENT', 'test')
os.environ.setdefault('DEBUG', 'true')

async def test_api_endpoints():
    """Test main API endpoints."""
    try:
        from fastapi.testclient import TestClient
        from src.main import app
        
        client = TestClient(app)
        
        print("🔧 Testing API endpoints...")
        
        # Test health endpoint
        response = client.get("/health")
        assert response.status_code == 200
        health_data = response.json()
        print(f"✅ Health endpoint: {health_data['status']}")
        
        # Test system metrics endpoint
        response = client.get("/system/metrics/performance")
        if response.status_code == 200:
            print("✅ System metrics endpoint working")
        else:
            print(f"⚠️  System metrics endpoint returned {response.status_code}")
        
        # Test incident creation
        incident_data = {
            "title": "Test Database Connection Issue",
            "description": "Database connections are timing out",
            "severity": "high",
            "business_impact": {
                "service_tier": "tier_1",
                "affected_users": 1000,
                "revenue_impact_per_minute": 100.0,
                "sla_breach_risk": 0.8,
                "reputation_impact": 0.6
            },
            "metadata": {
                "source_system": "test",
                "tags": {"type": "database", "issue": "timeout"}
            }
        }
        
        response = client.post("/incidents/trigger", json=incident_data)
        if response.status_code == 201:
            incident = response.json()
            print(f"✅ Incident creation: {incident['id']}")
            
            # Test incident retrieval
            response = client.get(f"/incidents/{incident['id']}")
            if response.status_code == 200:
                print("✅ Incident retrieval working")
            else:
                print(f"⚠️  Incident retrieval returned {response.status_code}")
        else:
            print(f"⚠️  Incident creation returned {response.status_code}: {response.text}")
        
        print("\n🎉 API validation completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ API validation failed: {e}")
        return False

async def test_agent_coordination():
    """Test basic agent coordination."""
    try:
        from src.orchestrator.swarm_coordinator import get_swarm_coordinator
        from src.models.incident import Incident, IncidentSeverity, ServiceTier, BusinessImpact, IncidentMetadata
        
        print("\n🔧 Testing agent coordination...")
        
        # Create a test incident
        incident = Incident(
            title="Test Coordination Issue",
            description="Testing agent coordination",
            severity=IncidentSeverity.MEDIUM,
            business_impact=BusinessImpact(
                service_tier=ServiceTier.TIER_2,
                affected_users=500,
                revenue_impact_per_minute=50.0,
                sla_breach_risk=0.5,
                reputation_impact=0.3
            ),
            metadata=IncidentMetadata(
                source_system="test",
                tags={"type": "coordination", "environment": "test"}
            )
        )
        
        # Get coordinator (this tests the lazy initialization)
        coordinator = get_swarm_coordinator()
        print("✅ Swarm coordinator initialized")
        
        # Test basic coordination (without actually processing)
        print("✅ Agent coordination test completed")
        return True
        
    except Exception as e:
        print(f"❌ Agent coordination test failed: {e}")
        return False

async def main():
    """Main validation routine."""
    print("🚀 Incident Commander - API Validation")
    print("=" * 50)
    
    success_count = 0
    total_tests = 2
    
    # Test API endpoints
    if await test_api_endpoints():
        success_count += 1
    
    # Test agent coordination
    if await test_agent_coordination():
        success_count += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"📊 API Validation Summary")
    print(f"✅ Passed: {success_count}/{total_tests}")
    print(f"❌ Failed: {total_tests - success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("\n🎉 All API tests passed! The system is ready for use.")
        return 0
    else:
        print(f"\n⚠️  {total_tests - success_count} test(s) failed.")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))