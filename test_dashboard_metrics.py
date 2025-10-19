#!/usr/bin/env python3
"""
Test Script to Generate Metrics for CloudWatch Dashboard
Creates sample incidents and API calls to populate dashboard widgets
"""

import requests
import time
import json
import os
import random
from datetime import datetime


# API Gateway endpoint - must be set via environment variable
# Do not use production endpoints in CI/tests
API_BASE_URL = os.environ.get("API_BASE_URL")
if not API_BASE_URL:
    raise ValueError("API_BASE_URL environment variable must be set. Do not use production URLs in tests.")

# Sample incident scenarios
INCIDENT_SCENARIOS = [
    {
        "incident_type": "high_cpu_usage",
        "severity": "medium",
        "description": "CPU usage above 80% for 5 minutes",
        "source": "cloudwatch_alarm"
    },
    {
        "incident_type": "database_connection_failure",
        "severity": "high", 
        "description": "Database connection pool exhausted",
        "source": "application_logs"
    },
    {
        "incident_type": "memory_leak_detection",
        "severity": "medium",
        "description": "Memory usage increasing over time",
        "source": "monitoring_agent"
    },
    {
        "incident_type": "network_latency_spike",
        "severity": "low",
        "description": "Network latency above 500ms",
        "source": "network_monitor"
    },
    {
        "incident_type": "disk_space_critical",
        "severity": "high",
        "description": "Disk usage above 95%",
        "source": "system_monitor"
    }
]


def test_health_endpoint():
    """Test the health endpoint."""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"✅ Health check: {response.status_code} - {response.json()['status']}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def test_demo_endpoints():
    """Test demo endpoints."""
    endpoints = ["/demo/status", "/demo/scenarios"]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{API_BASE_URL}{endpoint}")
            print(f"✅ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint} failed: {e}")


def create_sample_incident():
    """Create a sample incident."""
    incident = random.choice(INCIDENT_SCENARIOS)
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/incidents",
            headers={"Content-Type": "application/json"},
            json=incident
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Created incident: {result['incident_id']} - {incident['incident_type']}")
            return result['incident_id']
        else:
            print(f"❌ Failed to create incident: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating incident: {e}")
        return None


def generate_dashboard_activity():
    """Generate activity to populate dashboard metrics."""
    print("🚀 Generating activity for CloudWatch Dashboard")
    print("=" * 50)
    
    # Test health endpoint multiple times
    print("\n📊 Testing health endpoint...")
    for i in range(5):
        test_health_endpoint()
        time.sleep(1)
    
    # Test demo endpoints
    print("\n📋 Testing demo endpoints...")
    test_demo_endpoints()
    
    # Create multiple incidents
    print("\n🚨 Creating sample incidents...")
    incident_ids = []
    for i in range(10):
        incident_id = create_sample_incident()
        if incident_id:
            incident_ids.append(incident_id)
        time.sleep(2)  # Space out requests
    
    print(f"\n✅ Generated {len(incident_ids)} incidents")
    print("📊 Dashboard should now show activity in:")
    print("- Lambda function invocations")
    print("- API Gateway requests")
    print("- DynamoDB writes")
    print("- CloudWatch logs")
    
    return incident_ids


def continuous_monitoring_test(duration_minutes=5):
    """Run continuous tests for a specified duration."""
    print(f"\n🔄 Running continuous monitoring test for {duration_minutes} minutes...")
    
    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    
    while time.time() < end_time:
        # Random activity
        activity = random.choice([
            lambda: test_health_endpoint(),
            lambda: test_demo_endpoints(),
            lambda: create_sample_incident()
        ])
        
        activity()
        
        # Random delay between 5-15 seconds
        delay = random.randint(5, 15)
        print(f"⏱️  Waiting {delay} seconds...")
        time.sleep(delay)
    
    print("✅ Continuous monitoring test completed!")


def main():
    """Main test function."""
    print("🎯 CloudWatch Dashboard Metrics Test")
    print("=" * 40)
    
    # Initial activity burst
    incident_ids = generate_dashboard_activity()
    
    # Ask user if they want continuous monitoring
    print(f"\n🤔 Would you like to run continuous monitoring to keep generating metrics?")
    print("This will help populate the dashboard with ongoing data.")
    
    choice = input("Run continuous monitoring? (y/n): ").lower().strip()
    
    if choice in ['y', 'yes']:
        duration = input("Duration in minutes (default 5): ").strip()
        try:
            duration = int(duration) if duration else 5
        except ValueError:
            duration = 5
        
        continuous_monitoring_test(duration)
    
    print("\n📊 Dashboard Access:")
    print("https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=IncidentCommanderHackathon")
    
    print("\n📈 Metrics Generated:")
    print(f"- {len(incident_ids)} incidents created")
    print("- Multiple API Gateway requests")
    print("- Lambda function invocations")
    print("- DynamoDB table writes")
    print("- CloudWatch log entries")
    
    print("\n✅ Test completed! Check your CloudWatch dashboard for metrics.")


if __name__ == "__main__":
    main()