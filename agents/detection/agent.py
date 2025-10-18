"""
Robust Detection Agent with defensive programming and alert storm handling.
"""

import asyncio
import time
import psutil
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass

from src.interfaces.agent import DetectionAgent
from src.models.incident import Incident, IncidentSeverity, ServiceTier, BusinessImpact, IncidentMetadata
from src.models.agent import AgentRecommendation, ActionType, RiskLevel, Evidence, AgentMessage
from src.utils.constants import RESOURCE_LIMITS, PERFORMANCE_TARGETS, AGENT_CONFIG
from src.utils.logging import get_logger
from src.utils.exceptions import MemoryPressureError, AgentTimeoutError, ResourceLimitError
from src.services.shared_memory_monitor import get_shared_memory_monitor


logger = get_logger("detection_agent")


@dataclass
class AlertSample:
    """Represents a sampled alert."""
    alert_id: str
    timestamp: datetime
    severity: str
    source: str
    message: str
    metadata: Dict[str, Any]
    priority_score: float = 0.0


@dataclass
class CorrelationGroup:
    """Group of correlated alerts."""
    group_id: str
    alerts: List[AlertSample]
    correlation_score: float
    created_at: datetime
    last_updated: datetime


class AlertSampler:
    """Handles alert sampling during high-volume scenarios."""
    
    def __init__(self, max_rate: int = None):
        """
        Initialize alert sampler.
        
        Args:
            max_rate: Maximum alerts per second to process
        """
        self.max_rate = max_rate or AGENT_CONFIG["detection"]["max_alert_rate"]
        self.alert_buffer = deque(maxlen=RESOURCE_LIMITS["alert_buffer_size"])
        self.last_sample_time = time.time()
        self.sample_count = 0
        self.dropped_count = 0
    
    async def should_sample_alert(self, alert: Dict[str, Any]) -> bool:
        """
        Determine if alert should be sampled based on current load.
        
        Args:
            alert: Alert data
            
        Returns:
            True if alert should be processed
        """
        current_time = time.time()
        time_window = current_time - self.last_sample_time
        
        # Reset counters every second
        if time_window >= 1.0:
            self.sample_count = 0
            self.last_sample_time = current_time
        
        # Check if we're under rate limit
        if self.sample_count < self.max_rate:
            self.sample_count += 1
            return True
        
        # Apply priority-based sampling for high-severity alerts
        priority_score = self._calculate_priority_score(alert)
        threshold = AGENT_CONFIG["detection"]["alert_sampling_threshold"]
        if priority_score > threshold:  # High priority alerts always get through
            self.sample_count += 1
            return True
        
        # Exponential sampling based on cached memory pressure
        monitor = get_shared_memory_monitor()
        memory_usage = await monitor.get_memory_pressure()
        if memory_usage < RESOURCE_LIMITS["memory_threshold"]:
            sample_rate = max(0.1, 1.0 - memory_usage)  # Reduce sampling as memory increases
            if time.time() % (1.0 / sample_rate) < 0.1:  # Simple time-based sampling
                self.sample_count += 1
                return True
        
        self.dropped_count += 1
        return False
    
    def _calculate_priority_score(self, alert: Dict[str, Any]) -> float:
        """Calculate priority score for alert."""
        score = 0.0
        
        # Severity-based scoring
        severity = alert.get('severity', '').lower()
        severity_scores = {
            'critical': 1.0,
            'high': 0.8,
            'medium': 0.5,
            'low': 0.2
        }
        score += severity_scores.get(severity, 0.3)
        
        # Source-based scoring (customer-facing services get higher priority)
        source = alert.get('source', '').lower()
        if any(keyword in source for keyword in ['api', 'web', 'frontend', 'customer']):
            score += 0.2
        
        # Frequency-based scoring (repeated alerts get higher priority)
        alert_key = f"{alert.get('source', '')}-{alert.get('alert_type', '')}"
        # This would be enhanced with actual frequency tracking
        
        return min(1.0, score)


class MemoryBoundedDetectionAgent:
    """Memory-aware detection agent with pressure management."""
    
    def __init__(self):
        """Initialize memory-bounded detection agent."""
        self.memory_threshold = RESOURCE_LIMITS["memory_threshold"]
        self.alert_buffer = deque(maxlen=RESOURCE_LIMITS["alert_buffer_size"])
        self.correlation_cache = {}
        self.cache_ttl = timedelta(minutes=10)
    
    async def check_memory_pressure(self) -> float:
        """
        Check current memory pressure using cached statistics.
        
        Returns:
            Memory usage as percentage (0.0 to 1.0)
        """
        monitor = get_shared_memory_monitor()
        return await monitor.get_memory_pressure()
    
    def emergency_cleanup(self) -> None:
        """Perform emergency cleanup when memory pressure is high."""
        logger.warning("Performing emergency cleanup due to memory pressure")
        
        # Clear old correlation cache entries
        current_time = datetime.utcnow()
        expired_keys = [
            key for key, (_, timestamp) in self.correlation_cache.items()
            if current_time - timestamp > self.cache_ttl
        ]
        
        for key in expired_keys:
            del self.correlation_cache[key]
        
        # Reduce alert buffer size temporarily
        if len(self.alert_buffer) > 500:
            # Keep only the most recent 500 alerts
            recent_alerts = list(self.alert_buffer)[-500:]
            self.alert_buffer.clear()
            self.alert_buffer.extend(recent_alerts)
        
        logger.info(f"Emergency cleanup completed. Freed {len(expired_keys)} cache entries")
    
    async def should_drop_alerts(self) -> bool:
        """Check if alerts should be dropped due to memory pressure."""
        memory_usage = await self.check_memory_pressure()
        
        if memory_usage > self.memory_threshold:
            self.emergency_cleanup()
            
            # If still over threshold after cleanup, start dropping alerts
            if await self.check_memory_pressure() > self.memory_threshold:
                return True
        
        return False
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get detailed memory statistics using cached data."""
        monitor = get_shared_memory_monitor()
        memory_stats = await monitor.get_memory_stats()
        
        return {
            "total_mb": memory_stats.total_mb,
            "available_mb": memory_stats.available_mb,
            "used_mb": memory_stats.used_mb,
            "percentage": memory_stats.percentage,
            "alert_buffer_size": len(self.alert_buffer),
            "correlation_cache_size": len(self.correlation_cache),
            "processed_alert_count": len(self.processed_alert_ids),
            "cache_statistics": monitor.get_cache_statistics()
        }


class RobustDetectionAgent(DetectionAgent, MemoryBoundedDetectionAgent):
    """
    Robust detection agent with defensive programming and alert storm handling.
    """
    
    def __init__(self, name: str = "robust_detection"):
        """Initialize robust detection agent."""
        DetectionAgent.__init__(self, name)
        MemoryBoundedDetectionAgent.__init__(self)
        
        self.alert_sampler = AlertSampler()  # Uses config default
        self.correlation_groups: Dict[str, CorrelationGroup] = {}
        self.processing_timeout = PERFORMANCE_TARGETS["detection"]["max"]
        
        # Defensive programming state
        self.max_correlation_depth = RESOURCE_LIMITS["correlation_depth"]
        self.processed_alert_ids: Set[str] = set()
        self.circular_reference_detector: Set[str] = set()
    
    async def process_incident(self, incident: Incident) -> List[AgentRecommendation]:
        """
        Process incident and return detection recommendations.
        
        Args:
            incident: Incident to process
            
        Returns:
            List of detection recommendations
        """
        start_time = time.time()
        
        try:
            self.increment_processing_count()
            
            # Check memory pressure before processing
            if await self.should_drop_alerts():
                raise MemoryPressureError("Memory pressure too high, dropping incident")
            
            # Analyze incident for additional detection insights
            recommendations = []
            
            # Create recommendation for enhanced monitoring
            if incident.severity in [IncidentSeverity.CRITICAL, IncidentSeverity.HIGH]:
                monitoring_rec = AgentRecommendation(
                    agent_name=self.agent_type,
                    incident_id=incident.id,
                    action_type=ActionType.ESCALATE_INCIDENT,
                    action_id="enhance_monitoring",
                    confidence=0.8,
                    risk_level=RiskLevel.LOW,
                    estimated_impact="Improved detection accuracy",
                    reasoning="High severity incident requires enhanced monitoring",
                    urgency=0.7
                )
                
                # Add evidence
                monitoring_rec.add_evidence(
                    source="incident_analysis",
                    data={"severity": incident.severity, "business_impact": incident.business_impact.model_dump()},
                    confidence=0.9,
                    description="High severity incident detected"
                )
                
                recommendations.append(monitoring_rec)
            
            # Check processing time
            processing_time = time.time() - start_time
            if processing_time > self.processing_timeout:
                logger.warning(f"Detection processing exceeded timeout: {processing_time}s")
                raise AgentTimeoutError(f"Processing timeout exceeded: {processing_time}s")
            
            return recommendations
            
        except Exception as e:
            self.increment_error_count()
            logger.error(f"Detection agent processing failed: {e}")
            raise
    
    async def analyze_alerts(self, alerts: List[Dict[str, Any]]) -> List[Incident]:
        """
        Analyze incoming alerts and detect incidents with defensive programming.
        
        Args:
            alerts: List of alert data
            
        Returns:
            List of detected incidents
        """
        start_time = time.time()
        incidents = []
        
        try:
            # Check memory pressure
            if await self.should_drop_alerts():
                logger.warning("Dropping alerts due to memory pressure")
                return incidents
            
            # Sample alerts if too many
            sampled_alerts = []
            for alert in alerts:
                if await self.alert_sampler.should_sample_alert(alert):
                    # Defensive parsing
                    try:
                        parsed_alert = self._parse_alert_safely(alert)
                        if parsed_alert and parsed_alert.alert_id not in self.processed_alert_ids:
                            sampled_alerts.append(parsed_alert)
                            self.processed_alert_ids.add(parsed_alert.alert_id)
                    except Exception as e:
                        logger.warning(f"Failed to parse alert safely: {e}")
                        continue
            
            logger.info(f"Sampled {len(sampled_alerts)} alerts from {len(alerts)} total")
            
            # Correlate alerts with timeout protection
            correlation_task = asyncio.create_task(self._correlate_alerts_with_timeout(sampled_alerts))
            
            try:
                timeout = AGENT_CONFIG["detection"]["correlation_timeout"]
                correlated_groups = await asyncio.wait_for(
                    correlation_task, 
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                logger.warning("Alert correlation timed out, using simple grouping")
                if AGENT_CONFIG["detection"]["simple_grouping_fallback"]:
                    correlated_groups = self._simple_alert_grouping(sampled_alerts)
                else:
                    correlated_groups = []
            
            # Convert correlation groups to incidents
            for group in correlated_groups:
                try:
                    incident = self._create_incident_from_group(group)
                    if incident:
                        incidents.append(incident)
                except Exception as e:
                    logger.warning(f"Failed to create incident from group {group.group_id}: {e}")
                    continue
            
            # Check total processing time
            total_time = time.time() - start_time
            if total_time > self.processing_timeout:
                logger.warning(f"Alert analysis exceeded timeout: {total_time}s")
            
            return incidents
            
        except Exception as e:
            self.increment_error_count()
            logger.error(f"Alert analysis failed: {e}")
            return incidents  # Return partial results instead of failing completely
    
    def _parse_alert_safely(self, alert: Dict[str, Any]) -> Optional[AlertSample]:
        """
        Safely parse alert data with defensive programming.
        
        Args:
            alert: Raw alert data
            
        Returns:
            Parsed alert sample or None if parsing fails
        """
        try:
            # Validate required fields
            required_fields = ['id', 'timestamp', 'severity', 'source', 'message']
            for field in required_fields:
                if field not in alert:
                    logger.warning(f"Alert missing required field: {field}")
                    return None
            
            # Parse timestamp safely
            timestamp_str = alert.get('timestamp')
            if isinstance(timestamp_str, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except ValueError:
                    timestamp = datetime.utcnow()
            else:
                timestamp = datetime.utcnow()
            
            # Sanitize string fields
            alert_id = str(alert['id'])[:100]  # Limit length
            severity = str(alert['severity']).lower()[:20]
            source = str(alert['source'])[:100]
            message = str(alert['message'])[:1000]  # Limit message length
            
            # Validate severity
            valid_severities = ['critical', 'high', 'medium', 'low']
            if severity not in valid_severities:
                severity = 'medium'  # Default severity
            
            # Extract metadata safely
            metadata = {}
            if isinstance(alert.get('metadata'), dict):
                # Limit metadata size and sanitize
                for key, value in list(alert['metadata'].items())[:10]:  # Max 10 metadata fields
                    if isinstance(key, str) and len(key) <= 50:
                        metadata[key] = str(value)[:200]  # Limit value length
            
            return AlertSample(
                alert_id=alert_id,
                timestamp=timestamp,
                severity=severity,
                source=source,
                message=message,
                metadata=metadata,
                priority_score=self.alert_sampler._calculate_priority_score(alert)
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse alert: {e}")
            return None
    
    async def _correlate_alerts_with_timeout(self, alerts: List[AlertSample]) -> List[CorrelationGroup]:
        """Correlate alerts with timeout protection."""
        return await asyncio.wait_for(
            self.correlate_events([alert.__dict__ for alert in alerts]),
            timeout=30  # 30 second timeout for correlation
        )
    
    def _simple_alert_grouping(self, alerts: List[AlertSample]) -> List[CorrelationGroup]:
        """Simple alert grouping fallback when correlation fails."""
        groups = []
        source_groups = defaultdict(list)
        
        # Group by source
        for alert in alerts:
            source_groups[alert.source].append(alert)
        
        # Create correlation groups
        for source, source_alerts in source_groups.items():
            if len(source_alerts) > 0:
                group = CorrelationGroup(
                    group_id=f"simple_{source}_{int(time.time())}",
                    alerts=source_alerts,
                    correlation_score=0.5,  # Medium confidence for simple grouping
                    created_at=datetime.utcnow(),
                    last_updated=datetime.utcnow()
                )
                groups.append(group)
        
        return groups
    
    def _create_incident_from_group(self, group: CorrelationGroup) -> Optional[Incident]:
        """Create incident from correlation group."""
        try:
            if not group.alerts:
                return None
            
            # Determine incident severity based on alert severities
            severity_scores = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
            max_severity_score = max(
                severity_scores.get(alert.severity, 1) 
                for alert in group.alerts
            )
            
            severity_map = {4: IncidentSeverity.CRITICAL, 3: IncidentSeverity.HIGH, 
                          2: IncidentSeverity.MEDIUM, 1: IncidentSeverity.LOW}
            incident_severity = severity_map[max_severity_score]
            
            # Determine service tier based on source
            service_tier = ServiceTier.TIER_2  # Default
            sources = [alert.source.lower() for alert in group.alerts]
            if any('api' in source or 'web' in source for source in sources):
                service_tier = ServiceTier.TIER_1
            elif any('internal' in source or 'batch' in source for source in sources):
                service_tier = ServiceTier.TIER_3
            
            # Create business impact
            business_impact = BusinessImpact(
                service_tier=service_tier,
                affected_users=len(group.alerts) * 100,  # Rough estimate
                sla_breach_risk=min(1.0, group.correlation_score)
            )
            
            # Create metadata
            metadata = IncidentMetadata(
                source_system="detection_agent",
                alert_ids=[alert.alert_id for alert in group.alerts],
                tags={
                    "correlation_group_id": group.group_id,
                    "correlation_score": str(group.correlation_score),
                    "alert_count": str(len(group.alerts))
                }
            )
            
            # Create incident
            incident = Incident(
                title=f"Correlated incident from {len(group.alerts)} alerts",
                description=f"Incident detected from correlated alerts in {group.alerts[0].source}",
                severity=incident_severity,
                business_impact=business_impact,
                metadata=metadata
            )
            
            return incident
            
        except Exception as e:
            logger.error(f"Failed to create incident from group: {e}")
            return None
    
    async def correlate_events(self, events: List[Dict[str, Any]]) -> List[CorrelationGroup]:
        """
        Correlate related events and alerts with circular reference detection.
        
        Args:
            events: List of events to correlate
            
        Returns:
            List of correlated event groups
        """
        try:
            # Clear circular reference detector for new correlation
            self.circular_reference_detector.clear()
            
            groups = []
            processed_events = set()
            
            for event in events:
                event_id = event.get('alert_id', str(hash(str(event))))
                
                # Skip if already processed
                if event_id in processed_events:
                    continue
                
                # Detect circular references
                if event_id in self.circular_reference_detector:
                    logger.warning(f"Circular reference detected for event {event_id}")
                    continue
                
                self.circular_reference_detector.add(event_id)
                
                # Find related events (simplified correlation logic)
                related_events = [event]
                source = event.get('source', '')
                
                for other_event in events:
                    other_id = other_event.get('alert_id', str(hash(str(other_event))))
                    
                    if (other_id != event_id and 
                        other_id not in processed_events and
                        other_event.get('source', '') == source):
                        related_events.append(other_event)
                        processed_events.add(other_id)
                
                # Create correlation group
                if related_events:
                    group = CorrelationGroup(
                        group_id=f"corr_{event_id}_{int(time.time())}",
                        alerts=[AlertSample(
                            alert_id=e.get('alert_id', str(hash(str(e)))),
                            timestamp=datetime.utcnow(),
                            severity=e.get('severity', 'medium'),
                            source=e.get('source', 'unknown'),
                            message=e.get('message', ''),
                            metadata=e.get('metadata', {})
                        ) for e in related_events],
                        correlation_score=min(1.0, len(related_events) / 5.0),  # Higher score for more events
                        created_at=datetime.utcnow(),
                        last_updated=datetime.utcnow()
                    )
                    groups.append(group)
                
                processed_events.add(event_id)
                
                # Prevent infinite loops with depth limit
                if len(groups) >= self.max_correlation_depth:
                    logger.warning(f"Reached maximum correlation depth: {self.max_correlation_depth}")
                    break
            
            return groups
            
        except Exception as e:
            logger.error(f"Event correlation failed: {e}")
            return []
    
    async def handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Handle message from another agent."""
        try:
            logger.info(f"Detection agent received message: {message.message_type}")
            
            if message.message_type == "health_check":
                return AgentMessage(
                    sender_agent=self.agent_type,
                    recipient_agent=message.sender_agent,
                    message_type="health_response",
                    payload={"status": "healthy", "processing_count": self.processing_count},
                    correlation_id=message.correlation_id
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to handle message: {e}")
            return None
    
    async def health_check(self) -> bool:
        """Perform health check for detection agent."""
        try:
            # Check memory usage
            memory_usage = await self.check_memory_pressure()
            if memory_usage > 0.9:  # 90% memory usage is unhealthy
                self.is_healthy = False
                return False
            
            # Check error rate
            if self.error_count > 50:  # Too many errors
                self.is_healthy = False
                return False
            
            # Update heartbeat
            self.update_heartbeat()
            self.is_healthy = True
            return True
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self.is_healthy = False
            return False