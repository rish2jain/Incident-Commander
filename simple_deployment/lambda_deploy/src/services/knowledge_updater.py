"""
Knowledge base updater service for agent learning system.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4

from pydantic import BaseModel

from src.models.incident import Incident, IncidentSeverity, IncidentStatus
from src.models.agent import AgentRecommendation, ConsensusDecision, AgentPerformanceMetrics
from src.services.learning import learning_manager, LearningEvent, KnowledgePattern
from src.services.vector_store import vector_store, VectorDocument
from src.utils.config import config
from src.utils.logging import get_logger

logger = get_logger(__name__)


class KnowledgeUpdateResult(BaseModel):
    """Result of knowledge base update operation."""
    
    success: bool = False
    updated_components: List[str] = []
    errors: List[str] = []
    
    # Update statistics
    incidents_processed: int = 0
    patterns_discovered: int = 0
    embeddings_updated: int = 0
    agent_metrics_updated: int = 0
    
    # Performance metrics
    processing_time_ms: int = 0
    memory_usage_mb: float = 0.0
    
    # Validation results
    data_quality_score: float = 0.0
    privacy_compliance: bool = True
    integrity_verified: bool = True
    
    timestamp: datetime = datetime.utcnow()


class DataQualityValidator:
    """Validates data quality for knowledge updates."""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        
        # Quality thresholds
        self.min_description_length = 10
        self.max_description_length = 1000
        self.required_fields_incident = [
            'id', 'title', 'description', 'severity', 'status', 'detected_at'
        ]
        self.required_fields_recommendation = [
            'agent_name', 'action_id', 'confidence', 'description'
        ]
    
    def validate_incident_data(self, incident: Incident) -> Tuple[bool, List[str]]:
        """Validate incident data quality."""
        
        errors = []
        
        # Check required fields
        for field in self.required_fields_incident:
            if not getattr(incident, field, None):
                errors.append(f"Missing required field: {field}")
        
        # Validate description length
        if len(incident.description) < self.min_description_length:
            errors.append(f"Description too short: {len(incident.description)} chars")
        elif len(incident.description) > self.max_description_length:
            errors.append(f"Description too long: {len(incident.description)} chars")
        
        # Check data integrity
        if not incident.verify_integrity():
            errors.append("Incident integrity check failed")
        
        # Validate timestamps
        if incident.resolved_at and incident.detected_at:
            if incident.resolved_at < incident.detected_at:
                errors.append("Resolved timestamp before detected timestamp")
        
        # Validate business impact
        if incident.business_impact.affected_users < 0:
            errors.append("Negative affected users count")
        
        return len(errors) == 0, errors
    
    def validate_recommendations(self, recommendations: List[AgentRecommendation]) -> Tuple[bool, List[str]]:
        """Validate agent recommendations data quality."""
        
        errors = []
        
        for i, rec in enumerate(recommendations):
            # Check required fields
            for field in self.required_fields_recommendation:
                if not getattr(rec, field, None):
                    errors.append(f"Recommendation {i}: Missing required field: {field}")
            
            # Validate confidence range
            if not (0.0 <= rec.confidence <= 1.0):
                errors.append(f"Recommendation {i}: Invalid confidence: {rec.confidence}")
            
            # Check for reasonable processing time
            if rec.processing_time_ms and rec.processing_time_ms > 300000:  # 5 minutes
                errors.append(f"Recommendation {i}: Excessive processing time: {rec.processing_time_ms}ms")
        
        return len(errors) == 0, errors
    
    def calculate_quality_score(self, incident: Incident, 
                              recommendations: List[AgentRecommendation]) -> float:
        """Calculate overall data quality score (0.0 to 1.0)."""
        
        score = 1.0
        
        # Incident quality factors
        incident_valid, incident_errors = self.validate_incident_data(incident)
        if not incident_valid:
            score -= 0.3 * (len(incident_errors) / len(self.required_fields_incident))
        
        # Recommendations quality factors
        rec_valid, rec_errors = self.validate_recommendations(recommendations)
        if not rec_valid:
            score -= 0.2 * (len(rec_errors) / max(len(recommendations), 1))
        
        # Completeness factors
        if not incident.resolved_at:
            score -= 0.1  # Incomplete incident
        
        if len(recommendations) == 0:
            score -= 0.2  # No recommendations
        
        # Evidence quality
        total_evidence = sum(len(rec.evidence) for rec in recommendations)
        if total_evidence == 0:
            score -= 0.1  # No supporting evidence
        
        return max(0.0, score)


class PrivacyComplianceChecker:
    """Checks for PII and privacy compliance."""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        
        # PII patterns (simplified)
        self.pii_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'ip_address': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'phone': r'\b\d{3}-\d{3}-\d{4}\b',
            'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
        }
    
    def scan_for_pii(self, text: str) -> List[str]:
        """Scan text for potential PII."""
        
        import re
        found_pii = []
        
        for pii_type, pattern in self.pii_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                found_pii.append(pii_type)
        
        return found_pii
    
    def check_incident_compliance(self, incident: Incident) -> Tuple[bool, List[str]]:
        """Check incident for privacy compliance."""
        
        violations = []
        
        # Check incident description
        pii_in_description = self.scan_for_pii(incident.description)
        if pii_in_description:
            violations.extend([f"PII in description: {pii}" for pii in pii_in_description])
        
        # Check incident title
        pii_in_title = self.scan_for_pii(incident.title)
        if pii_in_title:
            violations.extend([f"PII in title: {pii}" for pii in pii_in_title])
        
        # Check metadata tags
        for key, value in incident.metadata.tags.items():
            pii_in_tag = self.scan_for_pii(f"{key} {value}")
            if pii_in_tag:
                violations.extend([f"PII in tag {key}: {pii}" for pii in pii_in_tag])
        
        return len(violations) == 0, violations
    
    def redact_pii(self, text: str) -> str:
        """Redact PII from text."""
        
        import re
        redacted_text = text
        
        for pii_type, pattern in self.pii_patterns.items():
            redacted_text = re.sub(pattern, f'[REDACTED_{pii_type.upper()}]', redacted_text, flags=re.IGNORECASE)
        
        return redacted_text


class KnowledgeUpdaterService:
    """Service for updating agent knowledge base with new incident data."""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.data_validator = DataQualityValidator()
        self.privacy_checker = PrivacyComplianceChecker()
        
        # Update configuration
        self.batch_size = 10
        self.max_concurrent_updates = 5
        self.update_timeout_seconds = 300
        
        # Statistics
        self.total_updates_processed = 0
        self.successful_updates = 0
        self.failed_updates = 0
        self.last_update_time: Optional[datetime] = None
    
    async def update_knowledge_base(self, incident: Incident,
                                  recommendations: List[AgentRecommendation],
                                  final_decision: ConsensusDecision) -> KnowledgeUpdateResult:
        """Update the complete knowledge base with new incident data."""
        
        start_time = datetime.utcnow()
        result = KnowledgeUpdateResult()
        
        try:
            self.logger.info(f"Starting knowledge base update for incident: {incident.id}")
            
            # 1. Validate data quality and completeness
            await self._validate_data_quality(incident, recommendations, result)
            
            # 2. Check privacy compliance and redact PII
            await self._ensure_privacy_compliance(incident, recommendations, result)
            
            # 3. Update vector embeddings in ChromaDB/Pinecone
            await self._update_vector_embeddings(incident, recommendations, result)
            
            # 4. Refresh agent knowledge graphs and relationships
            await self._update_knowledge_graphs(incident, recommendations, final_decision, result)
            
            # 5. Update agent decision trees and resolution playbooks
            await self._update_decision_trees(incident, recommendations, final_decision, result)
            
            # 6. Validate RAG retrieval accuracy
            await self._validate_rag_accuracy(incident, result)
            
            # 7. Test agent learning and adaptation mechanisms
            await self._test_learning_mechanisms(incident, recommendations, result)
            
            # 8. Update agent confidence scoring
            await self._update_confidence_scoring(recommendations, result)
            
            # 9. Refresh similarity search indexes
            await self._refresh_search_indexes(result)
            
            # 10. Generate learning effectiveness report
            await self._generate_effectiveness_report(result)
            
            # Calculate final metrics
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            result.processing_time_ms = int(processing_time)
            result.success = len(result.errors) == 0
            
            # Update statistics
            self.total_updates_processed += 1
            if result.success:
                self.successful_updates += 1
            else:
                self.failed_updates += 1
            self.last_update_time = datetime.utcnow()
            
            self.logger.info(f"Knowledge base update completed for {incident.id}: {result.success}")
            return result
            
        except Exception as e:
            result.success = False
            result.errors.append(f"Knowledge update failed: {str(e)}")
            self.logger.error(f"Knowledge base update error: {e}")
            self.failed_updates += 1
            return result
    
    async def _validate_data_quality(self, incident: Incident,
                                   recommendations: List[AgentRecommendation],
                                   result: KnowledgeUpdateResult) -> None:
        """Validate new incident data format and completeness."""
        
        try:
            # Validate incident data
            incident_valid, incident_errors = self.data_validator.validate_incident_data(incident)
            if not incident_valid:
                result.errors.extend(incident_errors)
            
            # Validate recommendations
            rec_valid, rec_errors = self.data_validator.validate_recommendations(recommendations)
            if not rec_valid:
                result.errors.extend(rec_errors)
            
            # Calculate quality score
            result.data_quality_score = self.data_validator.calculate_quality_score(incident, recommendations)
            
            if result.data_quality_score < 0.6:
                result.errors.append(f"Data quality score too low: {result.data_quality_score:.2f}")
            
            result.updated_components.append("data_validation")
            self.logger.debug(f"Data validation completed with quality score: {result.data_quality_score:.2f}")
            
        except Exception as e:
            result.errors.append(f"Data validation error: {str(e)}")
    
    async def _ensure_privacy_compliance(self, incident: Incident,
                                       recommendations: List[AgentRecommendation],
                                       result: KnowledgeUpdateResult) -> None:
        """Ensure data privacy and PII redaction compliance."""
        
        try:
            # Check incident for PII
            incident_compliant, incident_violations = self.privacy_checker.check_incident_compliance(incident)
            if not incident_compliant:
                result.errors.extend(incident_violations)
                result.privacy_compliance = False
            
            # Redact PII from incident data (in-place modification for learning)
            incident.description = self.privacy_checker.redact_pii(incident.description)
            incident.title = self.privacy_checker.redact_pii(incident.title)
            
            # Check recommendations for PII
            for rec in recommendations:
                rec.description = self.privacy_checker.redact_pii(rec.description)
                rec.reasoning = self.privacy_checker.redact_pii(rec.reasoning)
            
            result.updated_components.append("privacy_compliance")
            self.logger.debug("Privacy compliance check completed")
            
        except Exception as e:
            result.errors.append(f"Privacy compliance error: {str(e)}")
            result.privacy_compliance = False
    
    async def _update_vector_embeddings(self, incident: Incident,
                                      recommendations: List[AgentRecommendation],
                                      result: KnowledgeUpdateResult) -> None:
        """Update vector embeddings in ChromaDB/Pinecone."""
        
        try:
            # Add incident document to vector store
            document_id = await vector_store.add_incident_document(incident, recommendations)
            
            if document_id:
                result.embeddings_updated += 1
                result.updated_components.append("vector_embeddings")
                self.logger.debug(f"Added vector embedding for incident: {incident.id}")
            else:
                result.errors.append("Failed to create vector embedding")
            
        except Exception as e:
            result.errors.append(f"Vector embedding error: {str(e)}")
    
    async def _update_knowledge_graphs(self, incident: Incident,
                                     recommendations: List[AgentRecommendation],
                                     final_decision: ConsensusDecision,
                                     result: KnowledgeUpdateResult) -> None:
        """Refresh agent knowledge graphs and relationships."""
        
        try:
            # Process incident for learning patterns
            await learning_manager.process_incident_resolution(incident, recommendations, final_decision)
            
            result.patterns_discovered = len(learning_manager.knowledge_patterns)
            result.updated_components.append("knowledge_graphs")
            self.logger.debug("Knowledge graphs updated")
            
        except Exception as e:
            result.errors.append(f"Knowledge graph update error: {str(e)}")
    
    async def _update_decision_trees(self, incident: Incident,
                                   recommendations: List[AgentRecommendation],
                                   final_decision: ConsensusDecision,
                                   result: KnowledgeUpdateResult) -> None:
        """Update agent decision trees and resolution playbooks."""
        
        try:
            # Extract decision patterns
            decision_pattern = {
                "incident_type": f"{incident.severity}_{incident.business_impact.service_tier}",
                "successful_action": final_decision.selected_action,
                "confidence_threshold": final_decision.final_confidence,
                "agent_consensus": final_decision.consensus_method,
                "resolution_time": incident.calculate_duration_minutes()
            }
            
            # Add pattern to vector store
            pattern_id = await vector_store.add_knowledge_pattern(
                f"decision_pattern_{incident.id}",
                decision_pattern
            )
            
            if pattern_id:
                result.updated_components.append("decision_trees")
                self.logger.debug("Decision trees updated")
            
        except Exception as e:
            result.errors.append(f"Decision tree update error: {str(e)}")
    
    async def _validate_rag_accuracy(self, incident: Incident,
                                   result: KnowledgeUpdateResult) -> None:
        """Validate RAG retrieval accuracy with new data."""
        
        try:
            # Search for similar incidents
            similar_incidents = await vector_store.search_similar_incidents(incident, max_results=5)
            
            # Validate search results quality
            if similar_incidents:
                avg_similarity = sum(r.similarity_score for r in similar_incidents) / len(similar_incidents)
                if avg_similarity > 0.7:
                    result.updated_components.append("rag_validation")
                    self.logger.debug(f"RAG validation passed with avg similarity: {avg_similarity:.2f}")
                else:
                    result.errors.append(f"RAG accuracy too low: {avg_similarity:.2f}")
            
        except Exception as e:
            result.errors.append(f"RAG validation error: {str(e)}")
    
    async def _test_learning_mechanisms(self, incident: Incident,
                                      recommendations: List[AgentRecommendation],
                                      result: KnowledgeUpdateResult) -> None:
        """Test agent learning and adaptation mechanisms."""
        
        try:
            # Validate learning events were generated
            recent_events = [
                event for event in learning_manager.learning_events
                if event.incident_id == incident.id
            ]
            
            if recent_events:
                result.updated_components.append("learning_mechanisms")
                self.logger.debug(f"Learning mechanisms tested: {len(recent_events)} events")
            else:
                result.errors.append("No learning events generated")
            
        except Exception as e:
            result.errors.append(f"Learning mechanism test error: {str(e)}")
    
    async def _update_confidence_scoring(self, recommendations: List[AgentRecommendation],
                                       result: KnowledgeUpdateResult) -> None:
        """Update agent confidence scoring based on historical accuracy."""
        
        try:
            # Update agent metrics
            for rec in recommendations:
                if rec.agent_name in learning_manager.agent_metrics:
                    metrics = learning_manager.agent_metrics[rec.agent_name]
                    
                    # Update confidence-related metrics
                    total_confidence = (
                        metrics.average_confidence * (metrics.total_incidents_processed - 1) +
                        rec.confidence
                    )
                    metrics.average_confidence = total_confidence / metrics.total_incidents_processed
                    
                    result.agent_metrics_updated += 1
            
            result.updated_components.append("confidence_scoring")
            self.logger.debug("Confidence scoring updated")
            
        except Exception as e:
            result.errors.append(f"Confidence scoring error: {str(e)}")
    
    async def _refresh_search_indexes(self, result: KnowledgeUpdateResult) -> None:
        """Refresh similarity search indexes."""
        
        try:
            # Clean up old cached embeddings
            await vector_store.cleanup_old_embeddings()
            
            result.updated_components.append("search_indexes")
            self.logger.debug("Search indexes refreshed")
            
        except Exception as e:
            result.errors.append(f"Search index refresh error: {str(e)}")
    
    async def _generate_effectiveness_report(self, result: KnowledgeUpdateResult) -> None:
        """Generate learning effectiveness report."""
        
        try:
            # Get learning report
            learning_report = await learning_manager.get_learning_report()
            
            # Get vector store stats
            vector_stats = await vector_store.get_vector_store_stats()
            
            # Add to result
            result.updated_components.append("effectiveness_report")
            
            self.logger.info(f"Learning effectiveness report generated: "
                           f"{learning_report['total_incidents_learned']} incidents, "
                           f"{vector_stats['total_documents']} documents")
            
        except Exception as e:
            result.errors.append(f"Effectiveness report error: {str(e)}")
    
    async def get_update_statistics(self) -> Dict[str, Any]:
        """Get knowledge updater statistics."""
        
        success_rate = (
            self.successful_updates / self.total_updates_processed
            if self.total_updates_processed > 0 else 0.0
        )
        
        return {
            "total_updates_processed": self.total_updates_processed,
            "successful_updates": self.successful_updates,
            "failed_updates": self.failed_updates,
            "success_rate": success_rate,
            "last_update_time": self.last_update_time.isoformat() if self.last_update_time else None,
            "batch_size": self.batch_size,
            "max_concurrent_updates": self.max_concurrent_updates
        }


# Global knowledge updater service instance
knowledge_updater = KnowledgeUpdaterService()