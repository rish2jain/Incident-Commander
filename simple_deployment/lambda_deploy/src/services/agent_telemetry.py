"""
Agent Performance Telemetry System

Comprehensive telemetry collection and analysis for agent performance,
execution statistics, and optimization recommendations. Provides detailed
insights into agent behavior and system performance.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import statistics
import json

from src.utils.logging import get_logger
from src.utils.constants import PERFORMANCE_TARGETS, AGENT_CONFIG
from src.models.agent import AgentType, AgentPerformanceMetrics


logger = get_logger("agent_telemetry")


class TelemetryEventType(str, Enum):
    """Types of telemetry events."""
    AGENT_START = "agent_start"
    AGENT_COMPLETE = "agent_complete"
    AGENT_ERROR = "agent_error"
    AGENT_TIMEOUT = "agent_timeout"
    CONSENSUS_START = "consensus_start"
    CONSENSUS_COMPLETE = "consensus_complete"
    ACTION_EXECUTED = "action_executed"
    ESCALATION_TRIGGERED = "escalation_triggered"


class PerformanceCategory(str, Enum):
    """Performance categories for analysis."""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class TelemetryEvent:
    """Individual telemetry event."""
    id: str
    timestamp: datetime
    event_type: TelemetryEventType
    agent_name: str
    agent_type: AgentType
    
    # Performance data
    duration_ms: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    
    # Context information
    incident_id: Optional[str] = None
    correlation_id: Optional[str] = None
    
    # Event-specific data
    success: bool = True
    error_message: Optional[str] = None
    confidence_score: Optional[float] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "agent_name": self.agent_name,
            "agent_type": self.agent_type.value,
            "duration_ms": self.duration_ms,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent,
            "incident_id": self.incident_id,
            "correlation_id": self.correlation_id,
            "success": self.success,
            "error_message": self.error_message,
            "confidence_score": self.confidence_score,
            "metadata": self.metadata
        }


@dataclass
class AgentPerformanceAnalysis:
    """Comprehensive performance analysis for an agent."""
    agent_name: str
    agent_type: AgentType
    analysis_period: timedelta
    
    # Basic statistics
    total_executions: int
    successful_executions: int
    failed_executions: int
    timeout_count: int
    
    # Performance metrics
    average_duration_ms: float
    median_duration_ms: float
    p95_duration_ms: float
    p99_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    
    # Resource utilization
    average_memory_mb: float
    peak_memory_mb: float
    average_cpu_percent: float
    peak_cpu_percent: float
    
    # Quality metrics
    average_confidence: float
    success_rate: float
    error_rate: float
    timeout_rate: float
    
    # Performance category
    performance_category: PerformanceCategory
    
    # Trends and patterns
    performance_trend: str  # "improving", "stable", "degrading"
    peak_usage_hours: List[int]  # Hours of day with peak usage
    
    # Recommendations
    optimization_recommendations: List[str]
    
    def calculate_efficiency_score(self) -> float:
        """Calculate overall efficiency score (0-100)."""
        # Weighted scoring based on multiple factors
        success_weight = 0.3
        speed_weight = 0.25
        resource_weight = 0.25
        confidence_weight = 0.2
        
        # Success rate component (0-100)
        success_component = self.success_rate * 100
        
        # Speed component - compare against target
        target_ms = PERFORMANCE_TARGETS.get(self.agent_type.value, {}).get("target", 1000)
        speed_ratio = min(1.0, target_ms / max(1, self.average_duration_ms))
        speed_component = speed_ratio * 100
        
        # Resource efficiency (inverse of usage)
        memory_efficiency = max(0, 100 - (self.average_memory_mb / 10))  # Assume 1GB baseline
        cpu_efficiency = max(0, 100 - self.average_cpu_percent)
        resource_component = (memory_efficiency + cpu_efficiency) / 2
        
        # Confidence component
        confidence_component = self.average_confidence * 100
        
        efficiency_score = (
            success_component * success_weight +
            speed_component * speed_weight +
            resource_component * resource_weight +
            confidence_component * confidence_weight
        )
        
        return min(100.0, max(0.0, efficiency_score))


@dataclass
class SystemPerformanceReport:
    """System-wide performance report."""
    generated_at: datetime
    analysis_period: timedelta
    
    # System overview
    total_agents: int
    active_agents: int
    total_executions: int
    system_success_rate: float
    
    # Performance breakdown
    agent_analyses: Dict[str, AgentPerformanceAnalysis]
    
    # System-wide metrics
    average_incident_resolution_time_ms: float
    consensus_success_rate: float
    escalation_rate: float
    
    # Resource utilization
    total_memory_usage_mb: float
    total_cpu_usage_percent: float
    
    # Trends and insights
    performance_trends: Dict[str, str]
    bottlenecks: List[str]
    optimization_opportunities: List[str]
    
    # Recommendations
    system_recommendations: List[str]


class AgentTelemetryCollector:
    """
    Comprehensive agent performance telemetry collection and analysis system.
    
    Collects detailed performance metrics, analyzes trends, and provides
    optimization recommendations for the multi-agent system.
    """
    
    def __init__(self):
        self.logger = get_logger("agent_telemetry")
        self.events: List[TelemetryEvent] = []
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.collection_active = False
        
        # Configuration
        self.max_events_in_memory = 50000
        self.retention_period = timedelta(days=30)
        
        # Performance baselines (learned over time)
        self.performance_baselines: Dict[str, Dict[str, float]] = {}
        
        # Analytics cache
        self._analytics_cache: Dict[str, Any] = {}
        self._cache_expiry: Optional[datetime] = None
        self._cache_duration = timedelta(minutes=5)
    
    async def start_collection(self) -> None:
        """Start telemetry collection."""
        if self.collection_active:
            self.logger.warning("Telemetry collection already active")
            return
        
        self.collection_active = True
        self.logger.info("Agent telemetry collection started")
    
    async def stop_collection(self) -> None:
        """Stop telemetry collection."""
        self.collection_active = False
        self.logger.info("Agent telemetry collection stopped")
    
    async def record_agent_start(
        self,
        agent_name: str,
        agent_type: AgentType,
        incident_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Record agent execution start."""
        if not self.collection_active:
            return ""
        
        session_id = f"{agent_name}-{int(time.time() * 1000)}"
        
        # Store session info for completion tracking
        self.active_sessions[session_id] = {
            "agent_name": agent_name,
            "agent_type": agent_type,
            "start_time": time.time(),
            "incident_id": incident_id,
            "correlation_id": correlation_id,
            "metadata": metadata or {}
        }
        
        event = TelemetryEvent(
            id=f"start-{session_id}",
            timestamp=datetime.utcnow(),
            event_type=TelemetryEventType.AGENT_START,
            agent_name=agent_name,
            agent_type=agent_type,
            incident_id=incident_id,
            correlation_id=correlation_id,
            metadata=metadata or {}
        )
        
        await self._record_event(event)
        return session_id
    
    async def record_agent_complete(
        self,
        session_id: str,
        success: bool = True,
        confidence_score: Optional[float] = None,
        error_message: Optional[str] = None,
        memory_usage_mb: Optional[float] = None,
        cpu_usage_percent: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record agent execution completion."""
        if not self.collection_active or session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        duration_ms = (time.time() - session["start_time"]) * 1000
        
        event = TelemetryEvent(
            id=f"complete-{session_id}",
            timestamp=datetime.utcnow(),
            event_type=TelemetryEventType.AGENT_COMPLETE,
            agent_name=session["agent_name"],
            agent_type=session["agent_type"],
            duration_ms=duration_ms,
            memory_usage_mb=memory_usage_mb,
            cpu_usage_percent=cpu_usage_percent,
            incident_id=session["incident_id"],
            correlation_id=session["correlation_id"],
            success=success,
            error_message=error_message,
            confidence_score=confidence_score,
            metadata=metadata or {}
        )
        
        await self._record_event(event)
        
        # Clean up session
        del self.active_sessions[session_id]
    
    async def record_agent_error(
        self,
        agent_name: str,
        agent_type: AgentType,
        error_message: str,
        incident_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record agent error event."""
        if not self.collection_active:
            return
        
        event = TelemetryEvent(
            id=f"error-{agent_name}-{int(time.time() * 1000)}",
            timestamp=datetime.utcnow(),
            event_type=TelemetryEventType.AGENT_ERROR,
            agent_name=agent_name,
            agent_type=agent_type,
            incident_id=incident_id,
            correlation_id=correlation_id,
            success=False,
            error_message=error_message,
            metadata=metadata or {}
        )
        
        await self._record_event(event)
    
    async def record_consensus_event(
        self,
        event_type: TelemetryEventType,
        participating_agents: List[str],
        duration_ms: Optional[float] = None,
        success: bool = True,
        incident_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record consensus-related events."""
        if not self.collection_active:
            return
        
        event = TelemetryEvent(
            id=f"consensus-{int(time.time() * 1000)}",
            timestamp=datetime.utcnow(),
            event_type=event_type,
            agent_name="consensus_engine",
            agent_type=AgentType.RESOLUTION,  # Use resolution as default for consensus
            duration_ms=duration_ms,
            incident_id=incident_id,
            success=success,
            metadata={
                "participating_agents": participating_agents,
                **(metadata or {})
            }
        )
        
        await self._record_event(event)
    
    async def _record_event(self, event: TelemetryEvent) -> None:
        """Record a telemetry event."""
        self.events.append(event)
        
        # Manage memory usage
        if len(self.events) > self.max_events_in_memory:
            # Remove oldest events (in production, these would be persisted)
            self.events = self.events[-self.max_events_in_memory:]
        
        # Clear analytics cache
        self._invalidate_cache()
        
        # Update performance baselines
        await self._update_baselines(event)
        
        self.logger.debug(f"Recorded telemetry event: {event.id}")
    
    async def _update_baselines(self, event: TelemetryEvent) -> None:
        """Update performance baselines based on new events."""
        if event.event_type != TelemetryEventType.AGENT_COMPLETE or not event.success:
            return
        
        agent_key = f"{event.agent_type.value}"
        
        if agent_key not in self.performance_baselines:
            self.performance_baselines[agent_key] = {
                "duration_samples": [],
                "memory_samples": [],
                "cpu_samples": [],
                "confidence_samples": []
            }
        
        baselines = self.performance_baselines[agent_key]
        
        # Add samples (keep last 100 for rolling baseline)
        if event.duration_ms is not None:
            baselines["duration_samples"].append(event.duration_ms)
            if len(baselines["duration_samples"]) > 100:
                baselines["duration_samples"].pop(0)
        
        if event.memory_usage_mb is not None:
            baselines["memory_samples"].append(event.memory_usage_mb)
            if len(baselines["memory_samples"]) > 100:
                baselines["memory_samples"].pop(0)
        
        if event.cpu_usage_percent is not None:
            baselines["cpu_samples"].append(event.cpu_usage_percent)
            if len(baselines["cpu_samples"]) > 100:
                baselines["cpu_samples"].pop(0)
        
        if event.confidence_score is not None:
            baselines["confidence_samples"].append(event.confidence_score)
            if len(baselines["confidence_samples"]) > 100:
                baselines["confidence_samples"].pop(0)
    
    async def analyze_agent_performance(
        self,
        agent_name: Optional[str] = None,
        agent_type: Optional[AgentType] = None,
        hours: int = 24
    ) -> Dict[str, AgentPerformanceAnalysis]:
        """Analyze performance for specific agent or all agents."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Filter events
        relevant_events = [
            event for event in self.events
            if event.timestamp >= cutoff_time and event.event_type == TelemetryEventType.AGENT_COMPLETE
        ]
        
        if agent_name:
            relevant_events = [e for e in relevant_events if e.agent_name == agent_name]
        
        if agent_type:
            relevant_events = [e for e in relevant_events if e.agent_type == agent_type]
        
        # Group by agent
        agents_events: Dict[str, List[TelemetryEvent]] = {}
        for event in relevant_events:
            key = event.agent_name
            if key not in agents_events:
                agents_events[key] = []
            agents_events[key].append(event)
        
        # Analyze each agent
        analyses = {}
        for agent_key, events in agents_events.items():
            if events:
                analysis = await self._analyze_single_agent(events, timedelta(hours=hours))
                analyses[agent_key] = analysis
        
        return analyses
    
    async def _analyze_single_agent(
        self,
        events: List[TelemetryEvent],
        period: timedelta
    ) -> AgentPerformanceAnalysis:
        """Analyze performance for a single agent."""
        if not events:
            raise ValueError("No events provided for analysis")
        
        agent_name = events[0].agent_name
        agent_type = events[0].agent_type
        
        # Basic statistics
        total_executions = len(events)
        successful_executions = sum(1 for e in events if e.success)
        failed_executions = total_executions - successful_executions
        timeout_events = [e for e in self.events if e.agent_name == agent_name and e.event_type == TelemetryEventType.AGENT_TIMEOUT]
        timeout_count = len(timeout_events)
        
        # Duration statistics
        durations = [e.duration_ms for e in events if e.duration_ms is not None]
        if durations:
            average_duration = statistics.mean(durations)
            median_duration = statistics.median(durations)
            min_duration = min(durations)
            max_duration = max(durations)
            
            # Percentiles
            sorted_durations = sorted(durations)
            p95_duration = sorted_durations[int(0.95 * len(sorted_durations))] if sorted_durations else 0
            p99_duration = sorted_durations[int(0.99 * len(sorted_durations))] if sorted_durations else 0
        else:
            average_duration = median_duration = min_duration = max_duration = p95_duration = p99_duration = 0
        
        # Resource utilization
        memory_values = [e.memory_usage_mb for e in events if e.memory_usage_mb is not None]
        cpu_values = [e.cpu_usage_percent for e in events if e.cpu_usage_percent is not None]
        
        average_memory = statistics.mean(memory_values) if memory_values else 0
        peak_memory = max(memory_values) if memory_values else 0
        average_cpu = statistics.mean(cpu_values) if cpu_values else 0
        peak_cpu = max(cpu_values) if cpu_values else 0
        
        # Quality metrics
        confidence_values = [e.confidence_score for e in events if e.confidence_score is not None]
        average_confidence = statistics.mean(confidence_values) if confidence_values else 0
        
        success_rate = successful_executions / total_executions if total_executions > 0 else 0
        error_rate = failed_executions / total_executions if total_executions > 0 else 0
        timeout_rate = timeout_count / total_executions if total_executions > 0 else 0
        
        # Performance category
        performance_category = self._categorize_performance(
            success_rate, average_duration, agent_type
        )
        
        # Trends
        performance_trend = self._analyze_performance_trend(events)
        peak_usage_hours = self._analyze_peak_usage_hours(events)
        
        # Recommendations
        recommendations = self._generate_optimization_recommendations(
            agent_name, agent_type, success_rate, average_duration, average_memory, average_cpu
        )
        
        return AgentPerformanceAnalysis(
            agent_name=agent_name,
            agent_type=agent_type,
            analysis_period=period,
            total_executions=total_executions,
            successful_executions=successful_executions,
            failed_executions=failed_executions,
            timeout_count=timeout_count,
            average_duration_ms=average_duration,
            median_duration_ms=median_duration,
            p95_duration_ms=p95_duration,
            p99_duration_ms=p99_duration,
            min_duration_ms=min_duration,
            max_duration_ms=max_duration,
            average_memory_mb=average_memory,
            peak_memory_mb=peak_memory,
            average_cpu_percent=average_cpu,
            peak_cpu_percent=peak_cpu,
            average_confidence=average_confidence,
            success_rate=success_rate,
            error_rate=error_rate,
            timeout_rate=timeout_rate,
            performance_category=performance_category,
            performance_trend=performance_trend,
            peak_usage_hours=peak_usage_hours,
            optimization_recommendations=recommendations
        )
    
    def _categorize_performance(
        self,
        success_rate: float,
        average_duration_ms: float,
        agent_type: AgentType
    ) -> PerformanceCategory:
        """Categorize agent performance."""
        target_ms = PERFORMANCE_TARGETS.get(agent_type.value, {}).get("target", 1000)
        max_ms = PERFORMANCE_TARGETS.get(agent_type.value, {}).get("max", 2000)
        
        # Critical issues
        if success_rate < 0.8 or average_duration_ms > max_ms * 1.5:
            return PerformanceCategory.CRITICAL
        
        # Poor performance
        if success_rate < 0.9 or average_duration_ms > max_ms:
            return PerformanceCategory.POOR
        
        # Acceptable performance
        if success_rate < 0.95 or average_duration_ms > target_ms * 1.5:
            return PerformanceCategory.ACCEPTABLE
        
        # Good performance
        if success_rate < 0.98 or average_duration_ms > target_ms:
            return PerformanceCategory.GOOD
        
        # Excellent performance
        return PerformanceCategory.EXCELLENT
    
    def _analyze_performance_trend(self, events: List[TelemetryEvent]) -> str:
        """Analyze performance trend over time."""
        if len(events) < 10:
            return "insufficient_data"
        
        # Split events into two halves and compare
        mid_point = len(events) // 2
        first_half = events[:mid_point]
        second_half = events[mid_point:]
        
        first_half_success = sum(1 for e in first_half if e.success) / len(first_half)
        second_half_success = sum(1 for e in second_half if e.success) / len(second_half)
        
        first_half_duration = statistics.mean([e.duration_ms for e in first_half if e.duration_ms])
        second_half_duration = statistics.mean([e.duration_ms for e in second_half if e.duration_ms])
        
        # Determine trend
        success_improving = second_half_success > first_half_success * 1.05
        success_degrading = second_half_success < first_half_success * 0.95
        
        speed_improving = second_half_duration < first_half_duration * 0.95
        speed_degrading = second_half_duration > first_half_duration * 1.05
        
        if (success_improving and not success_degrading) or (speed_improving and not speed_degrading):
            return "improving"
        elif (success_degrading and not success_improving) or (speed_degrading and not speed_improving):
            return "degrading"
        else:
            return "stable"
    
    def _analyze_peak_usage_hours(self, events: List[TelemetryEvent]) -> List[int]:
        """Analyze peak usage hours."""
        hour_counts: Dict[int, int] = {}
        
        for event in events:
            hour = event.timestamp.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        if not hour_counts:
            return []
        
        # Find hours with above-average usage
        average_count = sum(hour_counts.values()) / len(hour_counts)
        peak_hours = [hour for hour, count in hour_counts.items() if count > average_count * 1.5]
        
        return sorted(peak_hours)
    
    def _generate_optimization_recommendations(
        self,
        agent_name: str,
        agent_type: AgentType,
        success_rate: float,
        average_duration_ms: float,
        average_memory_mb: float,
        average_cpu_percent: float
    ) -> List[str]:
        """Generate optimization recommendations for an agent."""
        recommendations = []
        
        target_ms = PERFORMANCE_TARGETS.get(agent_type.value, {}).get("target", 1000)
        
        # Performance recommendations
        if success_rate < 0.9:
            recommendations.append("Low success rate - review error handling and retry logic")
        
        if average_duration_ms > target_ms * 2:
            recommendations.append("High response time - consider algorithm optimization or caching")
        
        if average_memory_mb > 500:  # 500MB threshold
            recommendations.append("High memory usage - review data structures and implement memory optimization")
        
        if average_cpu_percent > 80:
            recommendations.append("High CPU usage - consider computational optimization or load balancing")
        
        # Agent-specific recommendations
        if agent_type == AgentType.DETECTION:
            if average_duration_ms > 30000:  # 30 seconds
                recommendations.append("Detection taking too long - consider parallel processing or alert sampling")
        
        elif agent_type == AgentType.DIAGNOSIS:
            if average_duration_ms > 120000:  # 2 minutes
                recommendations.append("Diagnosis taking too long - optimize log analysis or implement caching")
        
        elif agent_type == AgentType.PREDICTION:
            if average_duration_ms > 90000:  # 1.5 minutes
                recommendations.append("Prediction taking too long - consider model optimization or feature reduction")
        
        elif agent_type == AgentType.RESOLUTION:
            if average_duration_ms > 180000:  # 3 minutes
                recommendations.append("Resolution taking too long - review action execution and approval processes")
        
        if not recommendations:
            recommendations.append("Performance is within acceptable ranges - continue monitoring")
        
        return recommendations
    
    async def generate_system_performance_report(self, hours: int = 24) -> SystemPerformanceReport:
        """Generate comprehensive system performance report."""
        current_time = datetime.utcnow()
        analysis_period = timedelta(hours=hours)
        
        # Get agent analyses
        agent_analyses = await self.analyze_agent_performance(hours=hours)
        
        # System overview
        total_agents = len(set(e.agent_name for e in self.events))
        active_agents = len(agent_analyses)
        
        cutoff_time = current_time - analysis_period
        recent_events = [e for e in self.events if e.timestamp >= cutoff_time]
        total_executions = len([e for e in recent_events if e.event_type == TelemetryEventType.AGENT_COMPLETE])
        
        successful_executions = len([e for e in recent_events if e.event_type == TelemetryEventType.AGENT_COMPLETE and e.success])
        system_success_rate = successful_executions / max(1, total_executions)
        
        # Calculate system metrics
        incident_durations = []
        consensus_events = [e for e in recent_events if e.event_type in [TelemetryEventType.CONSENSUS_START, TelemetryEventType.CONSENSUS_COMPLETE]]
        consensus_successes = len([e for e in consensus_events if e.event_type == TelemetryEventType.CONSENSUS_COMPLETE and e.success])
        consensus_success_rate = consensus_successes / max(1, len(consensus_events) // 2)  # Assuming start/complete pairs
        
        escalation_events = [e for e in recent_events if e.event_type == TelemetryEventType.ESCALATION_TRIGGERED]
        escalation_rate = len(escalation_events) / max(1, total_executions)
        
        # Resource utilization
        memory_values = [e.memory_usage_mb for e in recent_events if e.memory_usage_mb is not None]
        cpu_values = [e.cpu_usage_percent for e in recent_events if e.cpu_usage_percent is not None]
        
        total_memory_usage = sum(memory_values) if memory_values else 0
        total_cpu_usage = statistics.mean(cpu_values) if cpu_values else 0
        
        # Performance trends
        performance_trends = {}
        for agent_name, analysis in agent_analyses.items():
            performance_trends[agent_name] = analysis.performance_trend
        
        # Identify bottlenecks
        bottlenecks = []
        for agent_name, analysis in agent_analyses.items():
            if analysis.performance_category in [PerformanceCategory.POOR, PerformanceCategory.CRITICAL]:
                bottlenecks.append(f"{agent_name}: {analysis.performance_category.value} performance")
        
        # Optimization opportunities
        optimization_opportunities = []
        for analysis in agent_analyses.values():
            optimization_opportunities.extend(analysis.optimization_recommendations)
        
        # System recommendations
        system_recommendations = self._generate_system_recommendations(
            agent_analyses, system_success_rate, escalation_rate
        )
        
        return SystemPerformanceReport(
            generated_at=current_time,
            analysis_period=analysis_period,
            total_agents=total_agents,
            active_agents=active_agents,
            total_executions=total_executions,
            system_success_rate=system_success_rate,
            agent_analyses=agent_analyses,
            average_incident_resolution_time_ms=statistics.mean(incident_durations) if incident_durations else 0,
            consensus_success_rate=consensus_success_rate,
            escalation_rate=escalation_rate,
            total_memory_usage_mb=total_memory_usage,
            total_cpu_usage_percent=total_cpu_usage,
            performance_trends=performance_trends,
            bottlenecks=bottlenecks,
            optimization_opportunities=list(set(optimization_opportunities)),
            system_recommendations=system_recommendations
        )
    
    def _generate_system_recommendations(
        self,
        agent_analyses: Dict[str, AgentPerformanceAnalysis],
        system_success_rate: float,
        escalation_rate: float
    ) -> List[str]:
        """Generate system-wide optimization recommendations."""
        recommendations = []
        
        # System-level issues
        if system_success_rate < 0.9:
            recommendations.append("System success rate below 90% - investigate agent failures and improve error handling")
        
        if escalation_rate > 0.1:
            recommendations.append("High escalation rate - review consensus thresholds and agent confidence scoring")
        
        # Agent-specific issues
        critical_agents = [name for name, analysis in agent_analyses.items() 
                          if analysis.performance_category == PerformanceCategory.CRITICAL]
        
        if critical_agents:
            recommendations.append(f"Critical performance issues in agents: {', '.join(critical_agents)}")
        
        # Resource optimization
        high_memory_agents = [name for name, analysis in agent_analyses.items() 
                             if analysis.average_memory_mb > 500]
        
        if high_memory_agents:
            recommendations.append(f"High memory usage in agents: {', '.join(high_memory_agents)} - consider memory optimization")
        
        # Performance trends
        degrading_agents = [name for name, analysis in agent_analyses.items() 
                           if analysis.performance_trend == "degrading"]
        
        if degrading_agents:
            recommendations.append(f"Performance degrading in agents: {', '.join(degrading_agents)} - investigate recent changes")
        
        if not recommendations:
            recommendations.append("System performance is within acceptable ranges - continue monitoring")
        
        return recommendations
    
    def _invalidate_cache(self) -> None:
        """Invalidate analytics cache."""
        self._analytics_cache = {}
        self._cache_expiry = None
    
    async def export_telemetry_data(
        self,
        format_type: str = "json",
        hours: int = 24,
        agent_name: Optional[str] = None
    ) -> str:
        """Export telemetry data in specified format."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        events = [e for e in self.events if e.timestamp >= cutoff_time]
        
        if agent_name:
            events = [e for e in events if e.agent_name == agent_name]
        
        if format_type.lower() == "json":
            return json.dumps([event.to_dict() for event in events], indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")


# Global instance for use across the application
_agent_telemetry_instance: Optional[AgentTelemetryCollector] = None


def get_agent_telemetry() -> AgentTelemetryCollector:
    """Get the global agent telemetry collector instance."""
    global _agent_telemetry_instance
    
    if _agent_telemetry_instance is None:
        _agent_telemetry_instance = AgentTelemetryCollector()
    
    return _agent_telemetry_instance