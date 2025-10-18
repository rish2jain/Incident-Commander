#!/usr/bin/env python3
"""
Test script for Milestone 2 agents completion.

Tests the enhanced prediction, resolution, and communication agents.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.incident import Incident, BusinessImpact, IncidentMetadata, ServiceTier
from src.services.aws import AWSServiceFactory
from src.services.rag_memory import ScalableRAGMemory
from agents.prediction.agent import PredictionAgent
from agents.resolution.agent import SecureResolutionAgent
from agents.communication.agent import ResilientCommunicationAgent
from src.utils.logging import get_logger

logger = get_logger(__name__)


async def test_prediction_agent():
    """Test the enhanced prediction agent."""
    logger.info("Testing Prediction Agent...")
    
    try:
        # Initialize services
        aws_factory = AWSServiceFactory()
        rag_memory = ScalableRAGMemory(aws_factory)
        
        # Create prediction agent
        prediction_agent = PredictionAgent(aws_factory, rag_memory, "test_prediction")
        
        # Create test incident
        incident = Incident(
            id="test_prediction_001",
            title="High CPU Utilization Detected",
            description="CPU utilization has been increasing steadily over the past hour",
            severity="high",
            status="investigating",
            business_impact=BusinessImpact(
                service_tier=ServiceTier.TIER_1,
                affected_users=5000
            ),
            metadata=IncidentMetadata(
                source_system="cloudwatch",
                tags={"service": "web-api", "environment": "production"}
            ),
            detected_at=datetime.utcnow()
        )
        
        # Test prediction processing
        logger.info("Processing incident with prediction agent...")
        recommendation = await prediction_agent.process_incident(incident)
        
        # Verify recommendation
        assert recommendation is not None, "Prediction agent should return recommendations"
        assert len(recommendation) > 0, "Prediction agent should return at least one recommendation"
        first_rec = recommendation[0]
        assert first_rec.incident_id == incident.id, "Recommendation should match incident ID"
        assert first_rec.agent_name == "prediction", "Agent name should be prediction"
        
        logger.info(f"✅ Prediction Agent Test Passed")
        logger.info(f"   - Action Type: {first_rec.action_type}")
        logger.info(f"   - Confidence: {first_rec.confidence:.2f}")
        logger.info(f"   - Risk Level: {first_rec.risk_level}")
        logger.info(f"   - Reasoning: {first_rec.reasoning[:100]}...")
        
        # Test health check
        health_status = await prediction_agent.get_health_status()
        assert health_status["agent_type"] == "prediction", "Health status should show correct agent type"
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Prediction Agent Test Failed: {e}")
        return False


async def test_resolution_agent():
    """Test the secure resolution agent."""
    logger.info("Testing Resolution Agent...")
    
    try:
        # Initialize services
        aws_factory = AWSServiceFactory()
        
        # Create resolution agent
        resolution_agent = SecureResolutionAgent(aws_factory, "test_resolution")
        
        # Create test incident
        incident = Incident(
            id="test_resolution_001",
            title="Database Connection Pool Exhausted",
            description="Database connection pool has reached maximum capacity",
            severity="critical",
            status="investigating",
            business_impact=BusinessImpact(
                service_tier=ServiceTier.TIER_1,
                affected_users=10000
            ),
            metadata=IncidentMetadata(
                source_system="application",
                tags={"service": "database", "environment": "production"}
            ),
            detected_at=datetime.utcnow()
        )
        
        # Test resolution processing
        logger.info("Processing incident with resolution agent...")
        recommendation = await resolution_agent.process_incident(incident)
        
        # Verify recommendation
        assert recommendation is not None, "Resolution agent should return recommendations"
        assert len(recommendation) > 0, "Resolution agent should return at least one recommendation"
        first_rec = recommendation[0]
        assert first_rec.incident_id == incident.id, "Recommendation should match incident ID"
        
        logger.info(f"✅ Resolution Agent Test Passed")
        logger.info(f"   - Action Type: {first_rec.action_type}")
        logger.info(f"   - Confidence: {first_rec.confidence:.2f}")
        logger.info(f"   - Risk Level: {first_rec.risk_level}")
        logger.info(f"   - Reasoning: {first_rec.reasoning[:100]}...")
        
        # Test health check
        health_status = await resolution_agent.get_health_status()
        assert health_status["agent_id"] == "test_resolution", "Health status should show correct agent ID"
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Resolution Agent Test Failed: {e}")
        return False


async def test_communication_agent():
    """Test the resilient communication agent."""
    logger.info("Testing Communication Agent...")
    
    try:
        # Create communication agent
        communication_agent = ResilientCommunicationAgent("test_communication")
        
        # Create test incident
        incident = Incident(
            id="test_communication_001",
            title="API Gateway Timeout Spike",
            description="API Gateway is experiencing increased timeout rates",
            severity="high",
            status="investigating",
            business_impact=BusinessImpact(
                service_tier=ServiceTier.TIER_2,
                affected_users=2000
            ),
            metadata=IncidentMetadata(
                source_system="api_gateway",
                tags={"service": "api-gateway", "environment": "production"}
            ),
            detected_at=datetime.utcnow()
        )
        
        # Test communication processing
        logger.info("Processing incident with communication agent...")
        recommendation = await communication_agent.process_incident(incident)
        
        # Verify recommendation
        assert recommendation is not None, "Communication agent should return recommendations"
        assert len(recommendation) > 0, "Communication agent should return at least one recommendation"
        first_rec = recommendation[0]
        assert first_rec.incident_id == incident.id, "Recommendation should match incident ID"
        
        logger.info(f"✅ Communication Agent Test Passed")
        logger.info(f"   - Action Type: {first_rec.action_type}")
        logger.info(f"   - Confidence: {first_rec.confidence:.2f}")
        logger.info(f"   - Risk Level: {first_rec.risk_level}")
        logger.info(f"   - Reasoning: {first_rec.reasoning[:100]}...")
        
        # Test health check
        health_status = await communication_agent.get_health_status()
        assert health_status["agent_id"] == "test_communication", "Health status should show correct agent ID"
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Communication Agent Test Failed: {e}")
        return False


async def test_agent_integration():
    """Test agent integration with swarm coordinator."""
    logger.info("Testing Agent Integration...")
    
    try:
        from src.orchestrator.swarm_coordinator import get_swarm_coordinator
        
        # Get coordinator
        coordinator = get_swarm_coordinator()
        
        # Initialize services
        aws_factory = AWSServiceFactory()
        rag_memory = ScalableRAGMemory(aws_factory)
        
        # Create agents
        prediction_agent = PredictionAgent(aws_factory, rag_memory, "integration_prediction")
        resolution_agent = SecureResolutionAgent(aws_factory, "integration_resolution")
        communication_agent = ResilientCommunicationAgent("integration_communication")
        
        # Register agents
        await coordinator.register_agent(prediction_agent)
        await coordinator.register_agent(resolution_agent)
        await coordinator.register_agent(communication_agent)
        
        # Verify registration
        agent_health = coordinator.get_agent_health_status()
        assert "integration_prediction" in agent_health, "Prediction agent should be registered"
        assert "integration_resolution" in agent_health, "Resolution agent should be registered"
        assert "integration_communication" in agent_health, "Communication agent should be registered"
        
        logger.info(f"✅ Agent Integration Test Passed")
        logger.info(f"   - Registered Agents: {len(agent_health)}")
        
        # Test health check
        is_healthy = await coordinator.health_check()
        logger.info(f"   - System Health: {'Healthy' if is_healthy else 'Unhealthy'}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Agent Integration Test Failed: {e}")
        return False


async def main():
    """Run all Milestone 2 tests."""
    logger.info("🚀 Starting Milestone 2 Agent Tests")
    logger.info("=" * 60)
    
    tests = [
        ("Prediction Agent", test_prediction_agent),
        ("Resolution Agent", test_resolution_agent),
        ("Communication Agent", test_communication_agent),
        ("Agent Integration", test_agent_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 Running {test_name} Test...")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ {test_name} Test Failed with Exception: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 Test Results Summary:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\n🎯 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All Milestone 2 agent tests passed!")
        logger.info("✅ Milestone 2 core agents are ready for production")
        return True
    else:
        logger.error(f"❌ {total - passed} tests failed")
        logger.error("🔧 Please fix failing tests before proceeding")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)