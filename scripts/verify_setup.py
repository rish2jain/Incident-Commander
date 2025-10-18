#!/usr/bin/env python3
"""
Verification script to check that the foundation setup is working correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config import config
from src.utils.logging import get_logger, IncidentCommanderLogger
from src.models.incident import Incident, IncidentSeverity, ServiceTier, BusinessImpact, IncidentMetadata
from agents.detection.agent import RobustDetectionAgent


async def main():
    """Main verification function."""
    print("🚀 Verifying Incident Commander Foundation Setup...")
    
    # Configure logging
    IncidentCommanderLogger.configure(level="INFO")
    logger = get_logger("setup_verification")
    
    try:
        # Test 1: Configuration
        print("\n✅ Testing Configuration...")
        logger.info(f"Environment: {config.environment}")
        logger.info(f"AWS Region: {config.aws.region}")
        logger.info(f"Bedrock Primary Model: {config.bedrock.primary_model}")
        print(f"   Environment: {config.environment}")
        print(f"   AWS Region: {config.aws.region}")
        
        # Test 2: Models
        print("\n✅ Testing Data Models...")
        business_impact = BusinessImpact(
            service_tier=ServiceTier.TIER_1,
            affected_users=500,
            revenue_impact_per_minute=200.0
        )
        
        metadata = IncidentMetadata(
            source_system="verification_script",
            tags={"test": "foundation_setup"}
        )
        
        incident = Incident(
            title="Foundation Verification Test",
            description="Testing that all foundation components work correctly",
            severity=IncidentSeverity.HIGH,
            business_impact=business_impact,
            metadata=metadata
        )
        
        print(f"   Created incident: {incident.id}")
        print(f"   Severity: {incident.severity}")
        print(f"   Cost per minute: ${business_impact.calculate_cost_per_minute():.2f}")
        
        # Test 3: Agent Creation
        print("\n✅ Testing Agent Creation...")
        detection_agent = RobustDetectionAgent("verification_agent")
        print(f"   Agent name: {detection_agent.name}")
        print(f"   Agent type: {detection_agent.agent_type}")
        print(f"   Is healthy: {detection_agent.is_healthy}")
        
        # Test 4: Agent Health Check
        print("\n✅ Testing Agent Health Check...")
        health_status = await detection_agent.health_check()
        print(f"   Health check result: {health_status}")
        
        # Test 5: Incident Processing
        print("\n✅ Testing Incident Processing...")
        recommendations = await detection_agent.process_incident(incident)
        print(f"   Generated {len(recommendations)} recommendations")
        
        for i, rec in enumerate(recommendations):
            print(f"   Recommendation {i+1}: {rec.action_type} (confidence: {rec.confidence})")
        
        # Test 6: Alert Analysis
        print("\n✅ Testing Alert Analysis...")
        sample_alerts = [
            {
                "id": "alert-001",
                "timestamp": "2024-01-01T12:00:00Z",
                "severity": "high",
                "source": "api-gateway",
                "message": "High error rate detected",
                "metadata": {"error_rate": "15%"}
            },
            {
                "id": "alert-002", 
                "timestamp": "2024-01-01T12:01:00Z",
                "severity": "medium",
                "source": "database",
                "message": "Connection pool exhausted",
                "metadata": {"pool_size": "100"}
            }
        ]
        
        detected_incidents = await detection_agent.analyze_alerts(sample_alerts)
        print(f"   Detected {len(detected_incidents)} incidents from {len(sample_alerts)} alerts")
        
        for i, detected_incident in enumerate(detected_incidents):
            print(f"   Incident {i+1}: {detected_incident.title} ({detected_incident.severity})")
        
        print("\n🎉 Foundation Setup Verification Complete!")
        print("✅ All core components are working correctly")
        print("\nNext steps:")
        print("1. Run tests: python -m pytest tests/test_foundation.py -v")
        print("2. Start the API server: python -m uvicorn src.main:app --reload")
        print("3. Continue with Task 1.2: AWS service clients implementation")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        logger.error(f"Setup verification failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)