"""
Interactive Judge Features for Demo Controller

Provides web interface for custom incident triggering, real-time agent confidence
visualizations, decision tree displays, and conflict resolution visualization.

Task 12.2: Add interactive judge features and real-time visualization
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from src.utils.logging import get_logger
from src.models.incident import Incident, IncidentSeverity, ServiceTier, BusinessImpact, IncidentMetadata
from src.services.demo_controller import get_demo_controller, DemoScenarioType


logger = get_logger("interactive_judge")


class JudgeInteractionType(Enum):
    """Types of judge interactions."""
    CUSTOM_INCIDENT_TRIGGER = "custom_incident_trigger"
    SEVERITY_ADJUSTMENT = "severity_adjustment"
    AGENT_CONFIDENCE_VIEW = "agent_confidence_view"
    DECISION_TREE_EXPLORATION = "decision_tree_exploration"
    CONFLICT_RESOLUTION_VIEW = "conflict_resolution_view"
    REASONING_TRACE_VIEW = "reasoning_trace_view"


@dataclass
class AgentConfidenceVisualization:
    """Real-time agent confidence score visualization data."""
    agent_name: str
    current_confidence: float
    confidence_history: List[Tuple[datetime, float]] = field(default_factory=list)
    reasoning_factors: Dict[str, float] = field(default_factory=dict)
    evidence_sources: List[str] = field(default_factory=list)
    uncertainty_factors: List[str] = field(default_factory=list)


@dataclass
class DecisionTreeNode:
    """Interactive decision tree node for visualization."""
    node_id: str
    decision_point: str
    confidence_score: float
    evidence: List[str]
    children: List['DecisionTreeNode'] = field(default_factory=list)
    selected_path: bool = False
    alternative_paths: List[str] = field(default_factory=list)


@dataclass
class ConflictResolutionVisualization:
    """Conflict resolution process visualization data."""
    conflict_id: str
    conflicting_agents: List[str]
    agent_recommendations: Dict[str, Dict[str, Any]]
    weighted_scores: Dict[str, float]
    resolution_process: List[Dict[str, Any]]
    final_decision: Optional[Dict[str, Any]] = None
    consensus_confidence: float = 0.0


@dataclass
class JudgeInteraction:
    """Judge interaction tracking."""
    interaction_id: str
    interaction_type: JudgeInteractionType
    timestamp: datetime
    session_id: str
    parameters: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None


class InteractiveJudgeInterface:
    """
    Interactive judge interface for real-time demo control and visualization.
    
    Provides web interface capabilities for custom incident triggering,
    real-time agent confidence visualizations, and decision tree exploration.
    """
    
    def __init__(self):
        self.active_interactions: Dict[str, JudgeInteraction] = {}
        self.confidence_visualizations: Dict[str, Dict[str, AgentConfidenceVisualization]] = {}
        self.decision_trees: Dict[str, DecisionTreeNode] = {}
        self.conflict_resolutions: Dict[str, ConflictResolutionVisualization] = {}
        self.demo_controller = get_demo_controller()
        
    async def create_custom_incident(
        self,
        judge_id: str,
        title: str,
        description: str,
        severity: str,
        service_tier: str,
        affected_users: int,
        revenue_impact_per_minute: float,
        custom_parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create custom incident with judge-specified parameters.
        
        Allows judges to trigger incidents with custom severity, impact, and parameters
        for interactive demonstration and testing.
        """
        interaction_id = f"custom_incident_{judge_id}_{int(datetime.utcnow().timestamp())}"
        
        try:
            # Create custom incident
            business_impact = BusinessImpact(
                service_tier=ServiceTier(service_tier),
                affected_users=affected_users,
                revenue_impact_per_minute=revenue_impact_per_minute
            )
            
            metadata = IncidentMetadata(
                source_system="interactive_judge",
                tags={
                    "judge_id": judge_id,
                    "custom_incident": "true",
                    "interaction_id": interaction_id,
                    **(custom_parameters or {})
                }
            )
            
            incident = Incident(
                title=title,
                description=description,
                severity=IncidentSeverity(severity),
                business_impact=business_impact,
                metadata=metadata
            )
            
            # Start demo session for custom incident
            session = await self.demo_controller.start_demo_scenario(
                scenario_type=DemoScenarioType.DATABASE_CASCADE,  # Use as template
                session_id=f"judge_{judge_id}_{incident.id}"
            )
            
            # Override with custom parameters
            session.incident_id = incident.id
            session.metrics.cost_per_minute = revenue_impact_per_minute
            session.metrics.affected_users = affected_users
            
            # Track judge interaction
            interaction = JudgeInteraction(
                interaction_id=interaction_id,
                interaction_type=JudgeInteractionType.CUSTOM_INCIDENT_TRIGGER,
                timestamp=datetime.utcnow(),
                session_id=session.session_id,
                parameters={
                    "title": title,
                    "severity": severity,
                    "service_tier": service_tier,
                    "affected_users": affected_users,
                    "revenue_impact_per_minute": revenue_impact_per_minute
                },
                result={
                    "incident_id": incident.id,
                    "session_id": session.session_id
                }
            )
            
            self.active_interactions[interaction_id] = interaction
            
            logger.info(f"Judge {judge_id} created custom incident: {incident.id}")
            
            return {
                "interaction_id": interaction_id,
                "incident_id": incident.id,
                "session_id": session.session_id,
                "status": "created",
                "estimated_completion_minutes": 5,
                "real_time_features": {
                    "agent_confidence_tracking": True,
                    "decision_tree_visualization": True,
                    "conflict_resolution_display": True,
                    "reasoning_trace_analysis": True
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to create custom incident for judge {judge_id}: {e}")
            raise
    
    async def adjust_incident_severity(
        self,
        judge_id: str,
        session_id: str,
        new_severity: str,
        adjustment_reason: str
    ) -> Dict[str, Any]:
        """
        Allow judges to adjust incident severity during demo execution.
        
        Provides interactive control over incident parameters to demonstrate
        system adaptability and response to changing conditions.
        """
        interaction_id = f"severity_adjust_{judge_id}_{int(datetime.utcnow().timestamp())}"
        
        try:
            # Get current session
            session = self.demo_controller.active_sessions.get(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")
            
            # Adjust severity and recalculate impact
            old_severity = session.scenario_type.value
            new_severity_enum = IncidentSeverity(new_severity)
            
            # Adjust cost based on severity
            severity_multipliers = {
                "low": 0.5,
                "medium": 1.0,
                "high": 1.5,
                "critical": 2.0
            }
            
            multiplier = severity_multipliers.get(new_severity, 1.0)
            session.metrics.cost_per_minute *= multiplier
            
            # Track interaction
            interaction = JudgeInteraction(
                interaction_id=interaction_id,
                interaction_type=JudgeInteractionType.SEVERITY_ADJUSTMENT,
                timestamp=datetime.utcnow(),
                session_id=session_id,
                parameters={
                    "old_severity": old_severity,
                    "new_severity": new_severity,
                    "adjustment_reason": adjustment_reason,
                    "multiplier": multiplier
                }
            )
            
            self.active_interactions[interaction_id] = interaction
            
            logger.info(f"Judge {judge_id} adjusted severity for session {session_id}: {old_severity} -> {new_severity}")
            
            return {
                "interaction_id": interaction_id,
                "session_id": session_id,
                "old_severity": old_severity,
                "new_severity": new_severity,
                "cost_multiplier": multiplier,
                "new_cost_per_minute": session.metrics.cost_per_minute,
                "adjustment_reason": adjustment_reason,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to adjust severity for judge {judge_id}: {e}")
            raise
    
    def get_real_time_agent_confidence(self, session_id: str) -> Dict[str, AgentConfidenceVisualization]:
        """
        Get real-time agent confidence score visualizations.
        
        Provides live confidence tracking with reasoning factors,
        evidence sources, and uncertainty analysis.
        """
        if session_id not in self.confidence_visualizations:
            # Initialize confidence visualizations for session
            self.confidence_visualizations[session_id] = {
                "detection": AgentConfidenceVisualization(
                    agent_name="detection",
                    current_confidence=0.95,
                    reasoning_factors={
                        "alert_correlation": 0.9,
                        "pattern_matching": 0.85,
                        "anomaly_detection": 0.92,
                        "historical_similarity": 0.88
                    },
                    evidence_sources=[
                        "CloudWatch metrics spike",
                        "Application error logs",
                        "Database connection pool exhaustion",
                        "Similar incident patterns"
                    ],
                    uncertainty_factors=[
                        "Limited historical data for this pattern",
                        "Partial metric availability"
                    ]
                ),
                "diagnosis": AgentConfidenceVisualization(
                    agent_name="diagnosis",
                    current_confidence=0.88,
                    reasoning_factors={
                        "root_cause_analysis": 0.85,
                        "log_correlation": 0.90,
                        "dependency_mapping": 0.82,
                        "failure_propagation": 0.87
                    },
                    evidence_sources=[
                        "Database query performance degradation",
                        "Connection timeout patterns",
                        "Cascade failure indicators",
                        "Resource utilization metrics"
                    ],
                    uncertainty_factors=[
                        "Multiple potential root causes",
                        "Incomplete dependency graph"
                    ]
                ),
                "prediction": AgentConfidenceVisualization(
                    agent_name="prediction",
                    current_confidence=0.82,
                    reasoning_factors={
                        "trend_analysis": 0.80,
                        "impact_forecasting": 0.85,
                        "escalation_probability": 0.78,
                        "recovery_time_estimation": 0.83
                    },
                    evidence_sources=[
                        "Historical incident progression",
                        "Resource consumption trends",
                        "Business impact modeling",
                        "Recovery time patterns"
                    ],
                    uncertainty_factors=[
                        "External factors not modeled",
                        "Limited prediction horizon"
                    ]
                ),
                "resolution": AgentConfidenceVisualization(
                    agent_name="resolution",
                    current_confidence=0.91,
                    reasoning_factors={
                        "action_effectiveness": 0.90,
                        "risk_assessment": 0.88,
                        "rollback_capability": 0.95,
                        "validation_coverage": 0.92
                    },
                    evidence_sources=[
                        "Proven resolution procedures",
                        "Automated rollback mechanisms",
                        "Validation test coverage",
                        "Success rate history"
                    ],
                    uncertainty_factors=[
                        "Potential side effects",
                        "Timing dependencies"
                    ]
                ),
                "communication": AgentConfidenceVisualization(
                    agent_name="communication",
                    current_confidence=0.96,
                    reasoning_factors={
                        "stakeholder_identification": 0.95,
                        "message_clarity": 0.98,
                        "channel_availability": 0.94,
                        "escalation_accuracy": 0.97
                    },
                    evidence_sources=[
                        "Stakeholder directory accuracy",
                        "Communication channel health",
                        "Message template effectiveness",
                        "Escalation policy compliance"
                    ],
                    uncertainty_factors=[
                        "Stakeholder availability",
                        "Message delivery timing"
                    ]
                )
            }
            
            # Add confidence history
            current_time = datetime.utcnow()
            for agent_viz in self.confidence_visualizations[session_id].values():
                # Simulate confidence evolution over time
                for i in range(10):
                    timestamp = current_time - timedelta(seconds=30 * i)
                    confidence = agent_viz.current_confidence + (i * 0.01)  # Slight variation
                    agent_viz.confidence_history.append((timestamp, confidence))
        
        return self.confidence_visualizations[session_id]
    
    def get_interactive_decision_tree(self, session_id: str) -> DecisionTreeNode:
        """
        Get interactive decision tree for agent reasoning visualization.
        
        Provides hierarchical decision tree with confidence scores,
        evidence, and alternative paths for judge exploration.
        """
        if session_id not in self.decision_trees:
            # Create decision tree for session
            root = DecisionTreeNode(
                node_id="root",
                decision_point="Incident Detection",
                confidence_score=0.95,
                evidence=[
                    "Multiple alert sources correlating",
                    "Anomaly detection threshold exceeded",
                    "Pattern matches historical incidents"
                ],
                selected_path=True
            )
            
            # Detection branch
            detection_node = DecisionTreeNode(
                node_id="detection",
                decision_point="Root Cause Analysis",
                confidence_score=0.88,
                evidence=[
                    "Database connection pool exhaustion identified",
                    "Cascade failure pattern detected",
                    "Resource utilization confirms bottleneck"
                ],
                selected_path=True,
                alternative_paths=[
                    "Network connectivity issue",
                    "Application memory leak",
                    "External service dependency failure"
                ]
            )
            
            # Resolution branch
            resolution_node = DecisionTreeNode(
                node_id="resolution",
                decision_point="Resolution Strategy Selection",
                confidence_score=0.91,
                evidence=[
                    "Connection pool scaling proven effective",
                    "Automated rollback available",
                    "Low risk of side effects"
                ],
                selected_path=True,
                alternative_paths=[
                    "Service restart approach",
                    "Traffic throttling strategy",
                    "Manual intervention escalation"
                ]
            )
            
            # Build tree structure
            detection_node.children.append(resolution_node)
            root.children.append(detection_node)
            
            self.decision_trees[session_id] = root
        
        return self.decision_trees[session_id]
    
    def get_conflict_resolution_visualization(self, session_id: str) -> ConflictResolutionVisualization:
        """
        Get conflict resolution process visualization.
        
        Shows weighted scoring, agent disagreements, and consensus building
        process with detailed breakdown of decision factors.
        """
        if session_id not in self.conflict_resolutions:
            # Create conflict resolution visualization
            conflict_viz = ConflictResolutionVisualization(
                conflict_id=f"conflict_{session_id}",
                conflicting_agents=["diagnosis", "prediction"],
                agent_recommendations={
                    "diagnosis": {
                        "action": "immediate_connection_pool_scaling",
                        "confidence": 0.88,
                        "reasoning": "Clear evidence of connection pool exhaustion",
                        "risk_level": "low",
                        "estimated_resolution_time": 120
                    },
                    "prediction": {
                        "action": "gradual_traffic_throttling",
                        "confidence": 0.82,
                        "reasoning": "Prevent cascade failure propagation",
                        "risk_level": "medium",
                        "estimated_resolution_time": 300
                    }
                },
                weighted_scores={
                    "diagnosis": 0.88 * 0.4,  # 40% weight for diagnosis agent
                    "prediction": 0.82 * 0.3   # 30% weight for prediction agent
                },
                resolution_process=[
                    {
                        "step": 1,
                        "action": "Collect agent recommendations",
                        "timestamp": datetime.utcnow() - timedelta(seconds=30),
                        "status": "completed"
                    },
                    {
                        "step": 2,
                        "action": "Calculate weighted confidence scores",
                        "timestamp": datetime.utcnow() - timedelta(seconds=20),
                        "status": "completed"
                    },
                    {
                        "step": 3,
                        "action": "Analyze risk-benefit tradeoffs",
                        "timestamp": datetime.utcnow() - timedelta(seconds=10),
                        "status": "in_progress"
                    },
                    {
                        "step": 4,
                        "action": "Generate consensus decision",
                        "timestamp": datetime.utcnow(),
                        "status": "pending"
                    }
                ],
                final_decision={
                    "selected_action": "immediate_connection_pool_scaling",
                    "consensus_confidence": 0.85,
                    "reasoning": "Higher weighted confidence and lower risk profile",
                    "fallback_plan": "gradual_traffic_throttling if scaling fails"
                },
                consensus_confidence=0.85
            )
            
            self.conflict_resolutions[session_id] = conflict_viz
        
        return self.conflict_resolutions[session_id]
    
    def get_reasoning_trace(self, session_id: str, agent_name: str) -> Dict[str, Any]:
        """
        Get detailed reasoning trace for specific agent.
        
        Provides step-by-step reasoning process with evidence weighting,
        confidence evolution, and decision factors.
        """
        reasoning_traces = {
            "detection": {
                "agent": "detection",
                "reasoning_steps": [
                    {
                        "step": 1,
                        "description": "Alert correlation analysis",
                        "evidence": ["CloudWatch CPU spike", "Database connection errors"],
                        "confidence_change": 0.7,
                        "reasoning": "Multiple correlated alerts indicate system-wide issue"
                    },
                    {
                        "step": 2,
                        "description": "Pattern matching against historical incidents",
                        "evidence": ["Similar pattern from 3 months ago", "Connection pool exhaustion signature"],
                        "confidence_change": 0.85,
                        "reasoning": "Strong pattern match with known incident type"
                    },
                    {
                        "step": 3,
                        "description": "Anomaly detection validation",
                        "evidence": ["Statistical deviation from baseline", "Threshold breach confirmation"],
                        "confidence_change": 0.95,
                        "reasoning": "Statistical confirmation of anomalous behavior"
                    }
                ],
                "final_confidence": 0.95,
                "evidence_weights": {
                    "alert_correlation": 0.3,
                    "pattern_matching": 0.4,
                    "anomaly_detection": 0.3
                },
                "uncertainty_factors": [
                    "Limited historical data for exact pattern",
                    "Potential for false positive correlation"
                ]
            },
            "diagnosis": {
                "agent": "diagnosis",
                "reasoning_steps": [
                    {
                        "step": 1,
                        "description": "Root cause hypothesis generation",
                        "evidence": ["Connection pool metrics", "Database performance logs"],
                        "confidence_change": 0.6,
                        "reasoning": "Initial evidence points to database bottleneck"
                    },
                    {
                        "step": 2,
                        "description": "Dependency analysis",
                        "evidence": ["Service dependency map", "Failure propagation patterns"],
                        "confidence_change": 0.75,
                        "reasoning": "Dependency analysis confirms cascade failure potential"
                    },
                    {
                        "step": 3,
                        "description": "Log correlation and validation",
                        "evidence": ["Application error logs", "Database query performance"],
                        "confidence_change": 0.88,
                        "reasoning": "Log evidence strongly supports connection pool exhaustion"
                    }
                ],
                "final_confidence": 0.88,
                "evidence_weights": {
                    "performance_metrics": 0.4,
                    "dependency_analysis": 0.3,
                    "log_correlation": 0.3
                },
                "uncertainty_factors": [
                    "Multiple potential contributing factors",
                    "Incomplete visibility into all dependencies"
                ]
            }
        }
        
        return reasoning_traces.get(agent_name, {})
    
    def log_judge_interaction(
        self,
        judge_id: str,
        interaction_type: JudgeInteractionType,
        session_id: str,
        parameters: Dict[str, Any]
    ) -> str:
        """Log judge interaction for analysis and replay."""
        interaction_id = f"{interaction_type.value}_{judge_id}_{int(datetime.utcnow().timestamp())}"
        
        interaction = JudgeInteraction(
            interaction_id=interaction_id,
            interaction_type=interaction_type,
            timestamp=datetime.utcnow(),
            session_id=session_id,
            parameters=parameters
        )
        
        self.active_interactions[interaction_id] = interaction
        
        logger.info(f"Logged judge interaction: {interaction_id} for session {session_id}")
        return interaction_id
    
    def get_judge_interaction_history(self, judge_id: str) -> List[Dict[str, Any]]:
        """Get interaction history for specific judge."""
        judge_interactions = [
            {
                "interaction_id": interaction.interaction_id,
                "interaction_type": interaction.interaction_type.value,
                "timestamp": interaction.timestamp.isoformat(),
                "session_id": interaction.session_id,
                "parameters": interaction.parameters,
                "result": interaction.result
            }
            for interaction in self.active_interactions.values()
            if interaction.parameters.get("judge_id") == judge_id or 
               judge_id in interaction.interaction_id
        ]
        
        return sorted(judge_interactions, key=lambda x: x["timestamp"], reverse=True)


# Global interactive judge interface instance
_interactive_judge = None


def get_interactive_judge() -> InteractiveJudgeInterface:
    """Get the global interactive judge interface instance."""
    global _interactive_judge
    if _interactive_judge is None:
        _interactive_judge = InteractiveJudgeInterface()
    return _interactive_judge