"""
Agent learning and knowledge management service.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4

import numpy as np
from pydantic import BaseModel

from src.models.incident import Incident, IncidentSeverity, IncidentStatus
from src.models.agent import AgentRecommendation, ConsensusDecision, AgentPerformanceMetrics
from src.utils.config import config
from src.utils.logging import get_logger

logger = get_logger(__name__)


class LearningEvent(BaseModel):
    """Event for agent learning system."""
    
    id: str = str(uuid4())
    event_type: str  # incident_resolved, pattern_discovered, accuracy_updated
    incident_id: str
    agent_name: str
    
    # Learning data
    learning_data: Dict[str, Any] = {}
    confidence_before: Optional[float] = None
    confidence_after: Optional[float] = None
    accuracy_improvement: Optional[float] = None
    
    # Metadata
    timestamp: datetime = datetime.utcnow()
    data_sources: List[str] = []
    validation_status: str = "pending"  # pending, validated, rejected


class KnowledgePattern(BaseModel):
    """Discovered incident pattern for knowledge base."""
    
    id: str = str(uuid4())
    pattern_name: str
    pattern_type: str  # symptom, cause, resolution, prevention
    
    # Pattern characteristics
    incident_signatures: List[Dict[str, Any]] = []
    success_rate: float = 0.0
    confidence_threshold: float = 0.6
    
    # Usage statistics
    times_applied: int = 0
    successful_applications: int = 0
    last_used: Optional[datetime] = None
    
    # Learning metadata
    discovered_by: str
    discovery_date: datetime = datetime.utcnow()
    validation_incidents: List[str] = []
    
    def calculate_effectiveness(self) -> float:
        """Calculate pattern effectiveness score."""
        if self.times_applied == 0:
            return 0.0
        return self.successful_applications / self.times_applied


class AgentLearningManager:
    """Manages agent learning and knowledge updates."""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.learning_events: List[LearningEvent] = []
        self.knowledge_patterns: Dict[str, KnowledgePattern] = {}
        self.agent_metrics: Dict[str, AgentPerformanceMetrics] = {}
        
        # Learning configuration
        self.min_confidence_threshold = 0.6
        self.learning_rate = 0.1
        self.pattern_discovery_threshold = 3  # Min incidents to form pattern
        self.validation_window_days = 30
    
    async def process_incident_resolution(self, incident: Incident, 
                                        recommendations: List[AgentRecommendation],
                                        final_decision: ConsensusDecision) -> None:
        """Process completed incident for learning updates."""
        try:
            self.logger.info(f"Processing incident resolution for learning: {incident.id}")
            
            # Validate incident data completeness
            if not self._validate_incident_data(incident):
                self.logger.warning(f"Incomplete incident data for learning: {incident.id}")
                return
            
            # Update agent performance metrics
            await self._update_agent_metrics(incident, recommendations, final_decision)
            
            # Discover new patterns
            await self._discover_patterns(incident, recommendations)
            
            # Update knowledge base
            await self._update_knowledge_base(incident, recommendations, final_decision)
            
            # Generate learning events
            await self._generate_learning_events(incident, recommendations, final_decision)
            
            # Validate learning effectiveness
            await self._validate_learning_effectiveness()
            
            self.logger.info(f"Completed learning update for incident: {incident.id}")
            
        except Exception as e:
            self.logger.error(f"Error processing incident for learning: {e}")
            raise
    
    def _validate_incident_data(self, incident: Incident) -> bool:
        """Validate incident data completeness for learning."""
        required_fields = [
            incident.id, incident.title, incident.description,
            incident.severity, incident.status, incident.detected_at
        ]
        
        if not all(required_fields):
            return False
        
        # Check for resolved status
        if incident.status != IncidentStatus.RESOLVED:
            return False
        
        # Verify integrity
        if not incident.verify_integrity():
            self.logger.warning(f"Incident integrity check failed: {incident.id}")
            return False
        
        return True
    
    async def _update_agent_metrics(self, incident: Incident,
                                  recommendations: List[AgentRecommendation],
                                  final_decision: ConsensusDecision) -> None:
        """Update performance metrics for all participating agents."""
        
        for recommendation in recommendations:
            agent_name = recommendation.agent_name
            
            # Initialize metrics if not exists
            if agent_name not in self.agent_metrics:
                self.agent_metrics[agent_name] = AgentPerformanceMetrics(
                    agent_name=agent_name,
                    agent_type=recommendation.agent_type
                )
            
            metrics = self.agent_metrics[agent_name]
            
            # Update counters
            metrics.total_incidents_processed += 1
            
            # Determine if recommendation was successful
            was_successful = (
                recommendation.action_id == final_decision.selected_action and
                incident.status == IncidentStatus.RESOLVED
            )
            
            if was_successful:
                metrics.successful_recommendations += 1
            else:
                metrics.failed_recommendations += 1
            
            # Update timing metrics
            if recommendation.processing_time_ms:
                metrics.update_timing_metrics(recommendation.processing_time_ms)
            
            # Update confidence metrics
            total_confidence = (
                metrics.average_confidence * (metrics.total_incidents_processed - 1) +
                recommendation.confidence
            )
            metrics.average_confidence = total_confidence / metrics.total_incidents_processed
            
            # Calculate accuracy rate (simplified - would need post-incident validation)
            metrics.accuracy_rate = metrics.calculate_success_rate()
            
            self.logger.debug(f"Updated metrics for agent {agent_name}")
    
    async def _discover_patterns(self, incident: Incident,
                               recommendations: List[AgentRecommendation]) -> None:
        """Discover new incident patterns from resolved incidents."""
        
        # Extract incident signature
        signature = self._extract_incident_signature(incident)
        
        # Look for similar incidents
        similar_incidents = await self._find_similar_incidents(signature)
        
        if len(similar_incidents) >= self.pattern_discovery_threshold:
            # Create new pattern
            pattern = KnowledgePattern(
                pattern_name=f"{incident.severity}_{incident.business_impact.service_tier}_pattern",
                pattern_type="resolution",
                incident_signatures=[signature],
                discovered_by="learning_manager",
                validation_incidents=[inc.id for inc in similar_incidents]
            )
            
            # Calculate initial success rate
            successful_resolutions = sum(
                1 for inc in similar_incidents 
                if inc.status == IncidentStatus.RESOLVED
            )
            pattern.success_rate = successful_resolutions / len(similar_incidents)
            
            self.knowledge_patterns[pattern.id] = pattern
            
            self.logger.info(f"Discovered new pattern: {pattern.pattern_name}")
    
    def _extract_incident_signature(self, incident: Incident) -> Dict[str, Any]:
        """Extract key characteristics that define an incident pattern."""
        return {
            "severity": incident.severity,  # Already a string due to use_enum_values=True
            "service_tier": incident.business_impact.service_tier,  # Already a string
            "source_system": incident.metadata.source_system,
            "tags": incident.metadata.tags,
            "duration_minutes": incident.calculate_duration_minutes(),
            "cost_impact": incident.calculate_total_cost(),
            "affected_users": incident.business_impact.affected_users
        }
    
    async def _find_similar_incidents(self, signature: Dict[str, Any]) -> List[Incident]:
        """Find incidents with similar signatures (simplified implementation)."""
        # In production, this would query the vector database
        # For now, return empty list as placeholder
        return []
    
    async def _update_knowledge_base(self, incident: Incident,
                                   recommendations: List[AgentRecommendation],
                                   final_decision: ConsensusDecision) -> None:
        """Update the RAG knowledge base with new incident data."""
        
        # Create knowledge entry
        knowledge_entry = {
            "incident_id": incident.id,
            "incident_signature": self._extract_incident_signature(incident),
            "successful_resolution": final_decision.selected_action,
            "resolution_confidence": final_decision.final_confidence,
            "resolution_time_minutes": incident.calculate_duration_minutes(),
            "business_impact": incident.calculate_total_cost(),
            "lessons_learned": self._extract_lessons_learned(recommendations, final_decision),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # In production, this would:
        # 1. Generate embeddings using Bedrock Titan
        # 2. Store in OpenSearch Serverless
        # 3. Update knowledge graph relationships
        # 4. Archive to S3 for long-term storage
        
        self.logger.info(f"Updated knowledge base with incident: {incident.id}")
    
    def _extract_lessons_learned(self, recommendations: List[AgentRecommendation],
                               final_decision: ConsensusDecision) -> Dict[str, Any]:
        """Extract lessons learned from incident resolution."""
        return {
            "effective_agents": [
                rec.agent_name for rec in recommendations 
                if rec.action_id == final_decision.selected_action
            ],
            "confidence_factors": [
                {
                    "agent": rec.agent_name,
                    "confidence": rec.confidence,
                    "evidence_count": len(rec.evidence)
                }
                for rec in recommendations
            ],
            "consensus_method": final_decision.consensus_method,
            "conflicts_resolved": final_decision.conflicts_detected,
            "decision_quality": "high" if final_decision.final_confidence > 0.8 else "medium"
        }
    
    async def _generate_learning_events(self, incident: Incident,
                                      recommendations: List[AgentRecommendation],
                                      final_decision: ConsensusDecision) -> None:
        """Generate learning events for system monitoring."""
        
        for recommendation in recommendations:
            event = LearningEvent(
                event_type="incident_resolved",
                incident_id=incident.id,
                agent_name=recommendation.agent_name,
                learning_data={
                    "recommendation_confidence": recommendation.confidence,
                    "was_selected": recommendation.action_id == final_decision.selected_action,
                    "processing_time_ms": recommendation.processing_time_ms,
                    "evidence_count": len(recommendation.evidence)
                },
                data_sources=recommendation.data_sources,
                validation_status="validated" if incident.status == IncidentStatus.RESOLVED else "pending"
            )
            
            self.learning_events.append(event)
    
    async def _validate_learning_effectiveness(self) -> None:
        """Validate that learning is improving agent performance."""
        
        # Check recent performance trends
        recent_events = [
            event for event in self.learning_events
            if event.timestamp > datetime.utcnow() - timedelta(days=self.validation_window_days)
        ]
        
        if len(recent_events) < 10:  # Need minimum data for validation
            return
        
        # Calculate improvement metrics
        for agent_name, metrics in self.agent_metrics.items():
            # Calculate trend in accuracy
            agent_events = [e for e in recent_events if e.agent_name == agent_name]
            
            if len(agent_events) >= 5:
                # Simple trend calculation (would be more sophisticated in production)
                recent_accuracy = sum(
                    1 for e in agent_events[-5:] 
                    if e.learning_data.get("was_selected", False)
                ) / 5
                
                older_accuracy = sum(
                    1 for e in agent_events[-10:-5] 
                    if e.learning_data.get("was_selected", False)
                ) / 5 if len(agent_events) >= 10 else recent_accuracy
                
                improvement = recent_accuracy - older_accuracy
                metrics.improvement_rate = improvement
                
                if improvement > 0.1:  # 10% improvement
                    self.logger.info(f"Agent {agent_name} showing significant improvement: {improvement:.2%}")
                elif improvement < -0.1:  # 10% degradation
                    self.logger.warning(f"Agent {agent_name} showing performance degradation: {improvement:.2%}")
    
    async def get_learning_report(self) -> Dict[str, Any]:
        """Generate comprehensive learning effectiveness report."""
        
        total_incidents = len(set(event.incident_id for event in self.learning_events))
        total_patterns = len(self.knowledge_patterns)
        
        # Calculate overall system improvement
        recent_events = [
            event for event in self.learning_events
            if event.timestamp > datetime.utcnow() - timedelta(days=30)
        ]
        
        overall_accuracy = (
            sum(1 for e in recent_events if e.learning_data.get("was_selected", False)) /
            len(recent_events) if recent_events else 0
        )
        
        # Agent performance summary
        agent_summary = {}
        for agent_name, metrics in self.agent_metrics.items():
            agent_summary[agent_name] = {
                "incidents_processed": metrics.total_incidents_processed,
                "success_rate": metrics.calculate_success_rate(),
                "average_confidence": metrics.average_confidence,
                "improvement_rate": metrics.improvement_rate,
                "avg_processing_time_ms": metrics.average_processing_time_ms
            }
        
        return {
            "report_generated": datetime.utcnow().isoformat(),
            "total_incidents_learned": total_incidents,
            "total_patterns_discovered": total_patterns,
            "overall_system_accuracy": overall_accuracy,
            "agent_performance": agent_summary,
            "learning_events_count": len(self.learning_events),
            "knowledge_base_size": total_patterns,
            "validation_window_days": self.validation_window_days
        }
    
    async def cleanup_old_data(self, retention_days: int = 90) -> None:
        """Clean up old learning data to prevent memory bloat."""
        
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        # Remove old learning events
        initial_count = len(self.learning_events)
        self.learning_events = [
            event for event in self.learning_events
            if event.timestamp > cutoff_date
        ]
        
        removed_events = initial_count - len(self.learning_events)
        
        # Archive old patterns (in production, move to cold storage)
        old_patterns = [
            pattern for pattern in self.knowledge_patterns.values()
            if pattern.last_used and pattern.last_used < cutoff_date
        ]
        
        for pattern in old_patterns:
            # In production: archive to S3
            del self.knowledge_patterns[pattern.id]
        
        self.logger.info(
            f"Cleaned up {removed_events} old learning events and "
            f"{len(old_patterns)} old patterns"
        )


# Global learning manager instance
learning_manager = AgentLearningManager()