"""
Real-time integration service for WebSocket broadcasting during incident processing.

Integrates with agent processing to provide live updates to dashboard clients
during incident detection, diagnosis, prediction, resolution, and communication phases.
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.utils.logging import get_logger
from src.utils.config import config
from src.services.websocket_manager import get_websocket_manager

logger = get_logger("realtime_integration")


class RealTimeIncidentBroadcaster:
    """
    Broadcasts real-time incident processing updates to WebSocket clients.
    
    Integrates with agent processing to provide live demo experience.
    """
    
    def __init__(self):
        self.websocket_manager = get_websocket_manager()
        self.active_incidents: Dict[str, Dict[str, Any]] = {}
        self.demo_effects_enabled = config.demo_effects_enabled

    async def _maybe_sleep(self, seconds: float) -> None:
        """Sleep only when demo effects are enabled."""
        if not self.demo_effects_enabled:
            return
        await asyncio.sleep(seconds)
        
    async def start_incident_broadcast(self, incident: Any) -> None:
        """Start broadcasting for a new incident."""
        self.active_incidents[incident.id] = {
            "incident": incident,
            "start_time": datetime.utcnow(),
            "phases_completed": [],
            "agent_actions": []
        }
        
        # Broadcast incident started
        await self.websocket_manager.broadcast_incident_started(incident)
        
        logger.info(f"Started real-time broadcasting for incident {incident.id}")
    
    async def broadcast_detection_phase(self, incident_id: str, detection_results: Dict[str, Any]) -> None:
        """Broadcast detection agent activity."""
        await self.websocket_manager.broadcast_agent_action(
            agent_type="detection",
            action_description=f"🔍 Analyzing {detection_results.get('alerts_processed', 0)} alerts and correlating patterns",
            details={
                "alerts_processed": detection_results.get("alerts_processed", 0),
                "patterns_identified": detection_results.get("patterns_identified", 0),
                "correlation_confidence": detection_results.get("correlation_confidence", 0.85),
                "processing_time_ms": detection_results.get("processing_time_ms", 450)
            },
            confidence=detection_results.get("confidence", 0.9),
            status="completed"
        )
        
        # Add small delay for dramatic effect
        await self._maybe_sleep(1)
        
        await self.websocket_manager.broadcast_agent_action(
            agent_type="detection",
            action_description="✅ Incident pattern confirmed - initiating diagnosis and prediction agents",
            details={
                "incident_type": detection_results.get("incident_type", "service_degradation"),
                "severity_assessment": detection_results.get("severity", "high"),
                "affected_components": detection_results.get("affected_components", ["api-gateway", "user-service"])
            },
            confidence=0.95,
            status="completed"
        )
    
    async def broadcast_diagnosis_phase(self, incident_id: str, diagnosis_results: Dict[str, Any]) -> None:
        """Broadcast diagnosis agent activity."""
        await self.websocket_manager.broadcast_agent_action(
            agent_type="diagnosis",
            action_description="🔬 Analyzing logs and traces to identify root cause",
            details={
                "logs_analyzed": diagnosis_results.get("logs_analyzed", 15000),
                "traces_correlated": diagnosis_results.get("traces_correlated", 342),
                "error_patterns": diagnosis_results.get("error_patterns", ["connection_timeout", "memory_pressure"]),
                "analysis_depth": diagnosis_results.get("analysis_depth", 3)
            },
            confidence=diagnosis_results.get("confidence", 0.88),
            status="in_progress"
        )
        
        await self._maybe_sleep(1.5)
        
        await self.websocket_manager.broadcast_agent_action(
            agent_type="diagnosis",
            action_description="🎯 Root cause identified - database connection pool exhaustion",
            details={
                "root_cause": diagnosis_results.get("root_cause", "database_connection_pool_exhaustion"),
                "contributing_factors": diagnosis_results.get("contributing_factors", [
                    "increased_traffic_load", "connection_leak_in_payment_service"
                ]),
                "evidence_strength": diagnosis_results.get("evidence_strength", 0.92),
                "recommended_actions": diagnosis_results.get("recommended_actions", [
                    "increase_connection_pool_size", "restart_payment_service", "enable_connection_monitoring"
                ])
            },
            confidence=0.92,
            status="completed"
        )
    
    async def broadcast_prediction_phase(self, incident_id: str, prediction_results: Dict[str, Any]) -> None:
        """Broadcast prediction agent activity."""
        await self.websocket_manager.broadcast_agent_action(
            agent_type="prediction",
            action_description="🔮 Forecasting incident progression and cascade risks",
            details={
                "time_series_analyzed": prediction_results.get("time_series_points", 1440),
                "cascade_probability": prediction_results.get("cascade_probability", 0.73),
                "affected_services_forecast": prediction_results.get("affected_services_forecast", [
                    "payment-service", "user-service", "notification-service", "analytics-service"
                ]),
                "peak_impact_eta": prediction_results.get("peak_impact_eta", "8 minutes")
            },
            confidence=prediction_results.get("confidence", 0.87),
            status="completed"
        )
        
        await self._maybe_sleep(1)
        
        await self.websocket_manager.broadcast_agent_action(
            agent_type="prediction",
            action_description="⚠️ High cascade risk detected - recommending immediate resolution",
            details={
                "cascade_services": prediction_results.get("cascade_services", 4),
                "business_impact_projection": f"${prediction_results.get('projected_cost', 15000)} if unresolved",
                "sla_breach_probability": prediction_results.get("sla_breach_probability", 0.85),
                "recommended_priority": "critical"
            },
            confidence=0.91,
            status="completed"
        )
    
    async def broadcast_resolution_phase(self, incident_id: str, resolution_results: Dict[str, Any]) -> None:
        """Broadcast resolution agent activity."""
        await self.websocket_manager.broadcast_agent_action(
            agent_type="resolution",
            action_description="🔧 Executing automated remediation actions",
            details={
                "actions_planned": resolution_results.get("actions_planned", 3),
                "sandbox_validation": "passed",
                "zero_trust_verification": "approved",
                "rollback_plan": "prepared"
            },
            confidence=resolution_results.get("confidence", 0.89),
            status="in_progress"
        )
        
        await self._maybe_sleep(2)
        
        await self.websocket_manager.broadcast_agent_action(
            agent_type="resolution",
            action_description="⚡ Scaling database connection pool from 50 to 200 connections",
            details={
                "action_type": "scale_connection_pool",
                "previous_size": 50,
                "new_size": 200,
                "execution_time_ms": 1200,
                "validation_status": "success"
            },
            confidence=0.95,
            status="completed"
        )
        
        await self._maybe_sleep(1)
        
        await self.websocket_manager.broadcast_agent_action(
            agent_type="resolution",
            action_description="🔄 Restarting payment service instances with connection monitoring",
            details={
                "instances_restarted": 3,
                "health_check_status": "all_healthy",
                "monitoring_enabled": True,
                "performance_improvement": "87% latency reduction"
            },
            confidence=0.96,
            status="completed"
        )
    
    async def broadcast_communication_phase(self, incident_id: str, communication_results: Dict[str, Any]) -> None:
        """Broadcast communication agent activity."""
        await self.websocket_manager.broadcast_agent_action(
            agent_type="communication",
            action_description="📢 Notifying stakeholders and updating status pages",
            details={
                "notifications_sent": communication_results.get("notifications_sent", 15),
                "channels_used": communication_results.get("channels", ["slack", "pagerduty", "status_page"]),
                "stakeholders_notified": communication_results.get("stakeholders_notified", 8),
                "escalation_level": communication_results.get("escalation_level", "resolved")
            },
            confidence=communication_results.get("confidence", 0.98),
            status="completed"
        )
        
        await self._maybe_sleep(0.5)
        
        # Calculate resolution time
        if incident_id in self.active_incidents:
            start_time = self.active_incidents[incident_id]["start_time"]
            resolution_time = int((datetime.utcnow() - start_time).total_seconds())
            
            # Broadcast incident resolved
            incident = self.active_incidents[incident_id]["incident"]
            await self.websocket_manager.broadcast_incident_resolved(
                incident=incident,
                resolution_time_seconds=resolution_time,
                actions_executed=[
                    "Scaled database connection pool",
                    "Restarted payment service instances", 
                    "Enabled connection monitoring",
                    "Updated stakeholders"
                ]
            )
            
            # Clean up
            del self.active_incidents[incident_id]
    
    async def simulate_full_incident_processing(self, incident: Any) -> None:
        """
        Simulate complete incident processing with realistic timing and updates.
        
        Provides engaging real-time demo experience with proper pacing.
        """
        try:
            await self.start_incident_broadcast(incident)
            
            # Detection phase (30 seconds target, simulate in 3-5 seconds)
            await self._maybe_sleep(2)
            await self.broadcast_detection_phase(incident.id, {
                "alerts_processed": 1247,
                "patterns_identified": 3,
                "correlation_confidence": 0.91,
                "processing_time_ms": 2800,
                "confidence": 0.93,
                "incident_type": "database_cascade_failure",
                "severity": incident.severity.value,
                "affected_components": ["payment-service", "user-service", "database-cluster"]
            })
            
            # Diagnosis phase (120 seconds target, simulate in 8-10 seconds)  
            await self._maybe_sleep(3)
            await self.broadcast_diagnosis_phase(incident.id, {
                "logs_analyzed": 23400,
                "traces_correlated": 567,
                "error_patterns": ["connection_timeout", "pool_exhaustion", "memory_pressure"],
                "analysis_depth": 4,
                "confidence": 0.89,
                "root_cause": "database_connection_pool_exhaustion",
                "contributing_factors": ["traffic_spike", "connection_leak", "insufficient_pool_size"],
                "evidence_strength": 0.94
            })
            
            # Prediction phase (90 seconds target, simulate in 4-6 seconds)
            await self._maybe_sleep(2)
            await self.broadcast_prediction_phase(incident.id, {
                "time_series_points": 2880,
                "cascade_probability": 0.78,
                "affected_services_forecast": ["payment", "user", "notification", "analytics", "reporting"],
                "peak_impact_eta": "6 minutes",
                "confidence": 0.88,
                "projected_cost": 18500,
                "sla_breach_probability": 0.82
            })
            
            # Resolution phase (180 seconds target, simulate in 10-15 seconds)
            await self._maybe_sleep(4)
            await self.broadcast_resolution_phase(incident.id, {
                "actions_planned": 4,
                "confidence": 0.91
            })
            
            # Communication phase (10 seconds target, simulate in 2-3 seconds)
            await self._maybe_sleep(2)
            await self.broadcast_communication_phase(incident.id, {
                "notifications_sent": 18,
                "channels": ["slack", "pagerduty", "email", "status_page", "mobile_app"],
                "stakeholders_notified": 12,
                "escalation_level": "resolved",
                "confidence": 0.99
            })
            
            logger.info(f"Completed real-time broadcast simulation for incident {incident.id}")
            
        except Exception as e:
            logger.error(f"Error in incident processing simulation: {e}")
            # Broadcast error state
            await self.websocket_manager.broadcast_agent_action(
                agent_type="system",
                action_description=f"❌ Processing error: {str(e)}",
                details={"error": str(e)},
                confidence=0.0,
                status="failed"
            )


# Global broadcaster instance
_realtime_broadcaster: Optional[RealTimeIncidentBroadcaster] = None


def get_realtime_broadcaster() -> RealTimeIncidentBroadcaster:
    """Get the global real-time incident broadcaster."""
    global _realtime_broadcaster
    if _realtime_broadcaster is None:
        _realtime_broadcaster = RealTimeIncidentBroadcaster()
    return _realtime_broadcaster
