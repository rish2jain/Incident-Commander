"""
Preventive Action Recommendation Engine

Provides intelligent preventive action recommendations based on predicted incidents.
Implements cost-benefit analysis and historical success rate tracking.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from src.services.rag_memory import ScalableRAGMemory
from src.utils.logging import get_logger
from src.utils.exceptions import AgentError

logger = get_logger(__name__)


class PreventiveActionType(Enum):
    """Types of preventive actions"""
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    RESTART_SERVICE = "restart_service"
    CLEAR_CACHE = "clear_cache"
    INCREASE_TIMEOUT = "increase_timeout"
    REDUCE_LOAD = "reduce_load"
    FAILOVER = "failover"
    MAINTENANCE_MODE = "maintenance_mode"
    CIRCUIT_BREAKER = "circuit_breaker"
    RATE_LIMITING = "rate_limiting"


@dataclass
class PreventiveAction:
    """Represents a preventive action recommendation"""
    action_type: PreventiveActionType
    action_id: str
    description: str
    target_service: str
    estimated_cost: float  # Cost in dollars
    estimated_benefit: float  # Benefit in dollars (prevented incident cost)
    success_probability: float  # Historical success rate
    execution_time_minutes: int
    risk_level: str  # LOW, MEDIUM, HIGH
    prerequisites: List[str]
    rollback_plan: str
    automation_available: bool
    
    @property
    def cost_benefit_ratio(self) -> float:
        """Calculate cost-benefit ratio"""
        if self.estimated_cost == 0:
            return float('inf')
        return self.estimated_benefit / self.estimated_cost
    
    @property
    def expected_value(self) -> float:
        """Calculate expected value (benefit * probability - cost)"""
        return (self.estimated_benefit * self.success_probability) - self.estimated_cost


@dataclass
class PreventiveActionRecommendation:
    """Complete recommendation with multiple action options"""
    incident_type: str
    predicted_probability: float
    time_to_incident: timedelta
    recommended_actions: List[PreventiveAction]
    reasoning: str
    confidence: float
    created_at: datetime


class PreventiveActionDatabase:
    """Database of preventive actions with risk assessment"""
    
    def __init__(self):
        self.actions_db = self._initialize_actions_database()
        logger.info(f"Initialized preventive action database with {len(self.actions_db)} action types")
    
    def _initialize_actions_database(self) -> Dict[str, List[PreventiveAction]]:
        """Initialize the preventive actions database"""
        actions_db = {
            "cpu_spike": [
                PreventiveAction(
                    action_type=PreventiveActionType.SCALE_UP,
                    action_id="scale_up_cpu_spike",
                    description="Scale up compute resources to handle increased CPU load",
                    target_service="compute",
                    estimated_cost=50.0,  # $50 for additional instances
                    estimated_benefit=5000.0,  # Prevent $5k incident
                    success_probability=0.85,
                    execution_time_minutes=5,
                    risk_level="LOW",
                    prerequisites=["auto_scaling_enabled", "capacity_available"],
                    rollback_plan="Scale down instances after load normalizes",
                    automation_available=True
                ),
                PreventiveAction(
                    action_type=PreventiveActionType.REDUCE_LOAD,
                    action_id="reduce_load_cpu_spike",
                    description="Implement rate limiting to reduce incoming load",
                    target_service="load_balancer",
                    estimated_cost=0.0,  # No direct cost
                    estimated_benefit=3000.0,  # Prevent partial outage
                    success_probability=0.70,
                    execution_time_minutes=2,
                    risk_level="LOW",
                    prerequisites=["rate_limiting_configured"],
                    rollback_plan="Remove rate limiting rules",
                    automation_available=True
                )
            ],
            "memory_leak": [
                PreventiveAction(
                    action_type=PreventiveActionType.RESTART_SERVICE,
                    action_id="restart_service_memory_leak",
                    description="Restart affected service to clear memory leak",
                    target_service="application",
                    estimated_cost=100.0,  # Brief service interruption cost
                    estimated_benefit=8000.0,  # Prevent major outage
                    success_probability=0.90,
                    execution_time_minutes=3,
                    risk_level="MEDIUM",
                    prerequisites=["rolling_restart_available", "health_checks_enabled"],
                    rollback_plan="Rollback to previous version if restart fails",
                    automation_available=True
                ),
                PreventiveAction(
                    action_type=PreventiveActionType.SCALE_UP,
                    action_id="scale_up_memory_leak",
                    description="Scale up memory resources temporarily",
                    target_service="compute",
                    estimated_cost=75.0,
                    estimated_benefit=6000.0,
                    success_probability=0.75,
                    execution_time_minutes=5,
                    risk_level="LOW",
                    prerequisites=["auto_scaling_enabled"],
                    rollback_plan="Scale down after memory issue resolved",
                    automation_available=True
                )
            ],
            "database_slowdown": [
                PreventiveAction(
                    action_type=PreventiveActionType.CLEAR_CACHE,
                    action_id="clear_cache_db_slowdown",
                    description="Clear database query cache to improve performance",
                    target_service="database",
                    estimated_cost=10.0,  # Brief performance impact
                    estimated_benefit=4000.0,
                    success_probability=0.65,
                    execution_time_minutes=1,
                    risk_level="LOW",
                    prerequisites=["cache_management_enabled"],
                    rollback_plan="Rebuild cache from warm data",
                    automation_available=True
                ),
                PreventiveAction(
                    action_type=PreventiveActionType.SCALE_UP,
                    action_id="scale_up_db_slowdown",
                    description="Scale up database read replicas",
                    target_service="database",
                    estimated_cost=200.0,
                    estimated_benefit=10000.0,
                    success_probability=0.80,
                    execution_time_minutes=10,
                    risk_level="LOW",
                    prerequisites=["read_replicas_configured"],
                    rollback_plan="Scale down replicas after load normalizes",
                    automation_available=True
                )
            ],
            "network_congestion": [
                PreventiveAction(
                    action_type=PreventiveActionType.FAILOVER,
                    action_id="failover_network_congestion",
                    description="Failover to alternate network path",
                    target_service="network",
                    estimated_cost=0.0,
                    estimated_benefit=7000.0,
                    success_probability=0.85,
                    execution_time_minutes=2,
                    risk_level="MEDIUM",
                    prerequisites=["multi_path_networking", "failover_configured"],
                    rollback_plan="Failback to primary path when congestion clears",
                    automation_available=True
                ),
                PreventiveAction(
                    action_type=PreventiveActionType.RATE_LIMITING,
                    action_id="rate_limit_network_congestion",
                    description="Implement traffic shaping to reduce network load",
                    target_service="network",
                    estimated_cost=0.0,
                    estimated_benefit=3000.0,
                    success_probability=0.70,
                    execution_time_minutes=1,
                    risk_level="LOW",
                    prerequisites=["traffic_shaping_available"],
                    rollback_plan="Remove traffic shaping rules",
                    automation_available=True
                )
            ],
            "disk_space_exhaustion": [
                PreventiveAction(
                    action_type=PreventiveActionType.CLEAR_CACHE,
                    action_id="clear_logs_disk_space",
                    description="Clear old log files and temporary data",
                    target_service="storage",
                    estimated_cost=5.0,  # Minimal operational cost
                    estimated_benefit=5000.0,
                    success_probability=0.90,
                    execution_time_minutes=2,
                    risk_level="LOW",
                    prerequisites=["log_rotation_configured"],
                    rollback_plan="Restore critical logs from backup if needed",
                    automation_available=True
                ),
                PreventiveAction(
                    action_type=PreventiveActionType.SCALE_UP,
                    action_id="expand_storage_disk_space",
                    description="Expand storage capacity",
                    target_service="storage",
                    estimated_cost=100.0,
                    estimated_benefit=8000.0,
                    success_probability=0.95,
                    execution_time_minutes=5,
                    risk_level="LOW",
                    prerequisites=["elastic_storage_available"],
                    rollback_plan="Reduce storage allocation after cleanup",
                    automation_available=True
                )
            ]
        }
        
        return actions_db
    
    def get_actions_for_incident_type(self, incident_type: str) -> List[PreventiveAction]:
        """Get available preventive actions for an incident type"""
        return self.actions_db.get(incident_type, [])
    
    def get_all_incident_types(self) -> List[str]:
        """Get all supported incident types"""
        return list(self.actions_db.keys())


class PreventiveActionEngine:
    """Engine for generating preventive action recommendations"""
    
    def __init__(self, rag_memory: ScalableRAGMemory):
        self.rag_memory = rag_memory
        self.actions_db = PreventiveActionDatabase()
        self.success_rate_cache = {}  # Cache for historical success rates
        
        logger.info("Initialized Preventive Action Engine")
    
    async def generate_recommendations(
        self,
        incident_type: str,
        predicted_probability: float,
        time_to_incident: timedelta,
        service_context: Dict[str, Any] = None
    ) -> PreventiveActionRecommendation:
        """
        Generate preventive action recommendations for a predicted incident
        
        Args:
            incident_type: Type of predicted incident
            predicted_probability: Probability of incident occurring
            time_to_incident: Time until predicted incident
            service_context: Additional context about affected services
            
        Returns:
            PreventiveActionRecommendation with ranked actions
        """
        try:
            logger.info(f"Generating preventive actions for {incident_type} (p={predicted_probability:.2f})")
            
            # Get available actions for this incident type
            available_actions = self.actions_db.get_actions_for_incident_type(incident_type)
            
            if not available_actions:
                logger.warning(f"No preventive actions available for incident type: {incident_type}")
                return PreventiveActionRecommendation(
                    incident_type=incident_type,
                    predicted_probability=predicted_probability,
                    time_to_incident=time_to_incident,
                    recommended_actions=[],
                    reasoning="No preventive actions available for this incident type",
                    confidence=0.0,
                    created_at=datetime.utcnow()
                )
            
            # Update success probabilities with historical data
            updated_actions = await self._update_success_probabilities(
                available_actions, incident_type
            )
            
            # Filter actions based on time constraints
            feasible_actions = self._filter_by_time_constraints(
                updated_actions, time_to_incident
            )
            
            # Perform cost-benefit analysis
            analyzed_actions = await self._perform_cost_benefit_analysis(
                feasible_actions, predicted_probability, service_context
            )
            
            # Rank actions by expected value
            ranked_actions = self._rank_actions(analyzed_actions)
            
            # Generate reasoning
            reasoning = self._generate_reasoning(
                incident_type, predicted_probability, time_to_incident, ranked_actions
            )
            
            # Calculate overall confidence
            confidence = self._calculate_confidence(ranked_actions, predicted_probability)
            
            return PreventiveActionRecommendation(
                incident_type=incident_type,
                predicted_probability=predicted_probability,
                time_to_incident=time_to_incident,
                recommended_actions=ranked_actions[:5],  # Top 5 recommendations
                reasoning=reasoning,
                confidence=confidence,
                created_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error generating preventive action recommendations: {e}")
            return PreventiveActionRecommendation(
                incident_type=incident_type,
                predicted_probability=predicted_probability,
                time_to_incident=time_to_incident,
                recommended_actions=[],
                reasoning=f"Error generating recommendations: {str(e)}",
                confidence=0.0,
                created_at=datetime.utcnow()
            )
    
    async def _update_success_probabilities(
        self,
        actions: List[PreventiveAction],
        incident_type: str
    ) -> List[PreventiveAction]:
        """Update action success probabilities based on historical data"""
        try:
            updated_actions = []
            
            for action in actions:
                # Check cache first
                cache_key = f"{incident_type}:{action.action_id}"
                if cache_key in self.success_rate_cache:
                    historical_success_rate = self.success_rate_cache[cache_key]
                else:
                    # Query RAG memory for historical success rate
                    historical_success_rate = await self._get_historical_success_rate(
                        action.action_id, incident_type
                    )
                    self.success_rate_cache[cache_key] = historical_success_rate
                
                # Create updated action with historical success rate
                updated_action = PreventiveAction(
                    action_type=action.action_type,
                    action_id=action.action_id,
                    description=action.description,
                    target_service=action.target_service,
                    estimated_cost=action.estimated_cost,
                    estimated_benefit=action.estimated_benefit,
                    success_probability=historical_success_rate if historical_success_rate > 0 else action.success_probability,
                    execution_time_minutes=action.execution_time_minutes,
                    risk_level=action.risk_level,
                    prerequisites=action.prerequisites,
                    rollback_plan=action.rollback_plan,
                    automation_available=action.automation_available
                )
                
                updated_actions.append(updated_action)
            
            return updated_actions
            
        except Exception as e:
            logger.error(f"Error updating success probabilities: {e}")
            return actions  # Return original actions if update fails
    
    async def _get_historical_success_rate(
        self,
        action_id: str,
        incident_type: str
    ) -> float:
        """Get historical success rate for a specific action"""
        try:
            # Query RAG memory for incidents where this action was used
            query = f"preventive_action:{action_id} incident_type:{incident_type}"
            
            search_results = await self.rag_memory.search_similar_incidents(
                query=query,
                limit=50
            )
            
            if not search_results:
                return 0.0  # No historical data
            
            # Calculate success rate from historical data
            successful_actions = 0
            total_actions = len(search_results)
            
            for result in search_results:
                metadata = result.get("metadata", {})
                action_outcome = metadata.get("preventive_action_outcome", "unknown")
                
                if action_outcome == "successful":
                    successful_actions += 1
            
            success_rate = successful_actions / total_actions if total_actions > 0 else 0.0
            
            logger.info(f"Historical success rate for {action_id}: {success_rate:.2f} ({successful_actions}/{total_actions})")
            
            return success_rate
            
        except Exception as e:
            logger.error(f"Error getting historical success rate: {e}")
            return 0.0
    
    def _filter_by_time_constraints(
        self,
        actions: List[PreventiveAction],
        time_to_incident: timedelta
    ) -> List[PreventiveAction]:
        """Filter actions that can be executed within time constraints"""
        try:
            time_to_incident_minutes = time_to_incident.total_seconds() / 60
            
            # Keep actions that can be executed with some buffer time
            buffer_minutes = 2  # 2-minute buffer
            feasible_actions = [
                action for action in actions
                if action.execution_time_minutes <= (time_to_incident_minutes - buffer_minutes)
            ]
            
            logger.info(f"Filtered {len(feasible_actions)} feasible actions from {len(actions)} total")
            
            return feasible_actions
            
        except Exception as e:
            logger.error(f"Error filtering by time constraints: {e}")
            return actions
    
    async def _perform_cost_benefit_analysis(
        self,
        actions: List[PreventiveAction],
        predicted_probability: float,
        service_context: Dict[str, Any] = None
    ) -> List[PreventiveAction]:
        """Perform cost-benefit analysis on actions"""
        try:
            analyzed_actions = []
            
            for action in actions:
                # Adjust benefit based on predicted probability
                adjusted_benefit = action.estimated_benefit * predicted_probability
                
                # Adjust cost based on service context (if available)
                adjusted_cost = action.estimated_cost
                if service_context:
                    # Example: adjust cost based on service tier
                    service_tier = service_context.get("service_tier", "standard")
                    if service_tier == "critical":
                        adjusted_cost *= 0.8  # Lower cost threshold for critical services
                    elif service_tier == "development":
                        adjusted_cost *= 1.5  # Higher cost threshold for dev services
                
                # Create analyzed action with adjusted values
                analyzed_action = PreventiveAction(
                    action_type=action.action_type,
                    action_id=action.action_id,
                    description=action.description,
                    target_service=action.target_service,
                    estimated_cost=adjusted_cost,
                    estimated_benefit=adjusted_benefit,
                    success_probability=action.success_probability,
                    execution_time_minutes=action.execution_time_minutes,
                    risk_level=action.risk_level,
                    prerequisites=action.prerequisites,
                    rollback_plan=action.rollback_plan,
                    automation_available=action.automation_available
                )
                
                analyzed_actions.append(analyzed_action)
            
            return analyzed_actions
            
        except Exception as e:
            logger.error(f"Error performing cost-benefit analysis: {e}")
            return actions
    
    def _rank_actions(self, actions: List[PreventiveAction]) -> List[PreventiveAction]:
        """Rank actions by expected value and other factors"""
        try:
            # Sort by expected value (descending), then by success probability (descending)
            ranked_actions = sorted(
                actions,
                key=lambda a: (a.expected_value, a.success_probability, -a.estimated_cost),
                reverse=True
            )
            
            logger.info(f"Ranked {len(ranked_actions)} actions by expected value")
            
            return ranked_actions
            
        except Exception as e:
            logger.error(f"Error ranking actions: {e}")
            return actions
    
    def _generate_reasoning(
        self,
        incident_type: str,
        predicted_probability: float,
        time_to_incident: timedelta,
        ranked_actions: List[PreventiveAction]
    ) -> str:
        """Generate reasoning for the recommendations"""
        try:
            reasoning_parts = [
                f"Predicted {incident_type} with {predicted_probability:.1%} probability",
                f"Time to incident: {time_to_incident}",
                f"Analyzed {len(ranked_actions)} preventive actions"
            ]
            
            if ranked_actions:
                top_action = ranked_actions[0]
                reasoning_parts.extend([
                    f"Top recommendation: {top_action.description}",
                    f"Expected value: ${top_action.expected_value:.0f}",
                    f"Success probability: {top_action.success_probability:.1%}"
                ])
            
            return ". ".join(reasoning_parts)
            
        except Exception as e:
            logger.error(f"Error generating reasoning: {e}")
            return f"Error generating reasoning: {str(e)}"
    
    def _calculate_confidence(
        self,
        ranked_actions: List[PreventiveAction],
        predicted_probability: float
    ) -> float:
        """Calculate overall confidence in recommendations"""
        try:
            if not ranked_actions:
                return 0.0
            
            # Base confidence on prediction probability and top action success rate
            top_action_success = ranked_actions[0].success_probability
            
            # Combine prediction confidence with action success probability
            confidence = (predicted_probability + top_action_success) / 2
            
            # Boost confidence if multiple good actions are available
            if len(ranked_actions) > 1:
                second_action_success = ranked_actions[1].success_probability
                if second_action_success > 0.7:
                    confidence = min(confidence * 1.1, 1.0)
            
            return confidence
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.5
    
    async def record_action_outcome(
        self,
        action_id: str,
        incident_type: str,
        outcome: str,
        details: Dict[str, Any] = None
    ):
        """Record the outcome of a preventive action for learning"""
        try:
            # Store outcome in RAG memory for future reference
            outcome_data = {
                "action_id": action_id,
                "incident_type": incident_type,
                "outcome": outcome,  # "successful", "failed", "partial"
                "timestamp": datetime.utcnow().isoformat(),
                "details": details or {}
            }
            
            # This would be stored in the RAG memory system
            # For now, just log it
            logger.info(f"Recorded preventive action outcome: {action_id} -> {outcome}")
            
        except Exception as e:
            logger.error(f"Error recording action outcome: {e}")
    
    async def get_prevention_statistics(self) -> Dict[str, Any]:
        """Get statistics about preventive action effectiveness"""
        try:
            stats = {
                "total_incident_types": len(self.actions_db.get_all_incident_types()),
                "total_actions_available": sum(
                    len(actions) for actions in self.actions_db.actions_db.values()
                ),
                "cache_size": len(self.success_rate_cache),
                "most_effective_actions": [],
                "incident_type_coverage": self.actions_db.get_all_incident_types()
            }
            
            # Find most effective actions (highest expected value)
            all_actions = []
            for actions in self.actions_db.actions_db.values():
                all_actions.extend(actions)
            
            # Sort by expected value
            sorted_actions = sorted(all_actions, key=lambda a: a.expected_value, reverse=True)
            
            stats["most_effective_actions"] = [
                {
                    "action_id": action.action_id,
                    "description": action.description,
                    "expected_value": action.expected_value,
                    "success_probability": action.success_probability
                }
                for action in sorted_actions[:5]
            ]
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting prevention statistics: {e}")
            return {"error": str(e)}