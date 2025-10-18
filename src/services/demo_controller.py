"""
Demo Controller for Autonomous Incident Commander

Provides controlled scenario execution with real-time visualization,
MTTR tracking, and business impact calculation for demonstrations.

Task 12.1: Build demo controller with controlled scenario execution
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum

from src.utils.logging import get_logger
from src.models.incident import Incident, IncidentSeverity, ServiceTier, BusinessImpact, IncidentMetadata
from src.orchestrator.swarm_coordinator import get_swarm_coordinator


logger = get_logger("demo_controller")


class DemoScenarioType(Enum):
    """Available demo scenario types."""
    DATABASE_CASCADE = "database_cascade"
    DDOS_ATTACK = "ddos_attack"
    MEMORY_LEAK = "memory_leak"
    API_OVERLOAD = "api_overload"
    STORAGE_FAILURE = "storage_failure"


class DemoPhase(Enum):
    """Demo execution phases."""
    INITIALIZING = "initializing"
    DETECTING = "detecting"
    DIAGNOSING = "diagnosing"
    PREDICTING = "predicting"
    RESOLVING = "resolving"
    COMMUNICATING = "communicating"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class DemoMetrics:
    """Real-time demo metrics for visualization."""
    mttr_seconds: float = 0.0
    cost_accumulated: float = 0.0
    cost_per_minute: float = 0.0
    affected_users: int = 0
    sla_breach_countdown: float = 0.0
    reputation_impact_score: float = 0.0
    traditional_mttr_estimate: float = 1800.0  # 30 minutes traditional response
    autonomous_improvement_percentage: float = 0.0


@dataclass
class DemoSession:
    """Active demo session state."""
    session_id: str
    scenario_type: DemoScenarioType
    incident_id: str
    start_time: datetime
    current_phase: DemoPhase = DemoPhase.INITIALIZING
    metrics: DemoMetrics = field(default_factory=DemoMetrics)
    phase_timings: Dict[str, float] = field(default_factory=dict)
    agent_confidence_scores: Dict[str, float] = field(default_factory=dict)
    is_active: bool = True
    completion_guarantee_minutes: int = 5
    environment_isolated: bool = True


class DemoController:
    """
    Controlled demo execution with real-time visualization and metrics.
    
    Provides deterministic scenario execution with 5-minute completion guarantee,
    real-time MTTR countdown, cost accumulation, and demo environment isolation.
    """
    
    def __init__(self, task_scheduler: Optional[Callable[[Awaitable[Any], str], None]] = None):
        self.active_sessions: Dict[str, DemoSession] = {}
        self.scenario_configs = self._initialize_scenario_configs()
        self.coordinator = None  # Will be initialized when needed
        self._task_scheduler = task_scheduler

    def set_task_scheduler(self, scheduler: Optional[Callable[[Awaitable[Any], str], None]]) -> None:
        """Update background scheduler used for demo tasks."""
        self._task_scheduler = scheduler

    def _schedule_task(self, coro: Awaitable[Any], description: str) -> None:
        """Schedule coroutine using configured scheduler or fallback to create_task."""
        if self._task_scheduler:
            self._task_scheduler(coro, description)
        else:
            asyncio.create_task(coro, name=description)
        
    def _initialize_scenario_configs(self) -> Dict[DemoScenarioType, Dict[str, Any]]:
        """Initialize predefined scenario configurations."""
        return {
            DemoScenarioType.DATABASE_CASCADE: {
                "title": "Database Connection Pool Exhaustion",
                "description": "Critical database connection pool exhaustion causing cascade failures across payment processing services",
                "severity": IncidentSeverity.CRITICAL,
                "service_tier": ServiceTier.TIER_1,
                "affected_users": 50000,
                "revenue_impact_per_minute": 2000.0,
                "complexity": "high",
                "estimated_phases": {
                    "detecting": 25,    # seconds
                    "diagnosing": 75,
                    "predicting": 50,
                    "resolving": 100,
                    "communicating": 15
                },
                "sla_target_minutes": 15,
                "traditional_mttr_minutes": 45
            },
            DemoScenarioType.DDOS_ATTACK: {
                "title": "Distributed Denial of Service Attack",
                "description": "Large-scale DDoS attack overwhelming API gateway and causing service degradation",
                "severity": IncidentSeverity.HIGH,
                "service_tier": ServiceTier.TIER_1,
                "affected_users": 25000,
                "revenue_impact_per_minute": 1500.0,
                "complexity": "medium",
                "estimated_phases": {
                    "detecting": 20,
                    "diagnosing": 60,
                    "predicting": 45,
                    "resolving": 90,
                    "communicating": 10
                },
                "sla_target_minutes": 10,
                "traditional_mttr_minutes": 30
            },
            DemoScenarioType.MEMORY_LEAK: {
                "title": "Application Memory Leak",
                "description": "Memory leak in user service causing gradual performance degradation and eventual service crashes",
                "severity": IncidentSeverity.MEDIUM,
                "service_tier": ServiceTier.TIER_2,
                "affected_users": 5000,
                "revenue_impact_per_minute": 300.0,
                "complexity": "low",
                "estimated_phases": {
                    "detecting": 15,
                    "diagnosing": 45,
                    "predicting": 30,
                    "resolving": 60,
                    "communicating": 10
                },
                "sla_target_minutes": 20,
                "traditional_mttr_minutes": 25
            },
            DemoScenarioType.API_OVERLOAD: {
                "title": "API Rate Limit Exceeded",
                "description": "Sudden traffic spike causing API rate limits to be exceeded, resulting in service degradation",
                "severity": IncidentSeverity.HIGH,
                "service_tier": ServiceTier.TIER_1,
                "affected_users": 15000,
                "revenue_impact_per_minute": 800.0,
                "complexity": "medium",
                "estimated_phases": {
                    "detecting": 20,
                    "diagnosing": 50,
                    "predicting": 40,
                    "resolving": 80,
                    "communicating": 10
                },
                "sla_target_minutes": 12,
                "traditional_mttr_minutes": 25
            },
            DemoScenarioType.STORAGE_FAILURE: {
                "title": "Distributed Storage System Failure",
                "description": "Multiple storage nodes failing simultaneously, causing data availability issues",
                "severity": IncidentSeverity.CRITICAL,
                "service_tier": ServiceTier.TIER_1,
                "affected_users": 75000,
                "revenue_impact_per_minute": 3000.0,
                "complexity": "high",
                "estimated_phases": {
                    "detecting": 25,
                    "diagnosing": 70,
                    "predicting": 50,
                    "resolving": 110,
                    "communicating": 15
                },
                "sla_target_minutes": 20,
                "traditional_mttr_minutes": 50
            },
            DemoScenarioType.API_OVERLOAD: {
                "title": "API Rate Limit Exceeded",
                "description": "Sudden traffic spike causing API rate limits to be exceeded, resulting in service degradation",
                "severity": IncidentSeverity.HIGH,
                "service_tier": ServiceTier.TIER_1,
                "affected_users": 15000,
                "revenue_impact_per_minute": 800.0,
                "complexity": "medium",
                "estimated_phases": {
                    "detecting": 20,
                    "diagnosing": 60,
                    "predicting": 45,
                    "resolving": 90,
                    "communicating": 10
                },
                "sla_target_minutes": 12,
                "traditional_mttr_minutes": 25
            },
            DemoScenarioType.STORAGE_FAILURE: {
                "title": "Distributed Storage System Failure",
                "description": "Multiple storage nodes failing simultaneously, causing data availability issues",
                "severity": IncidentSeverity.CRITICAL,
                "service_tier": ServiceTier.TIER_1,
                "affected_users": 75000,
                "revenue_impact_per_minute": 3000.0,
                "complexity": "high",
                "estimated_phases": {
                    "detecting": 20,
                    "diagnosing": 75,
                    "predicting": 45,
                    "resolving": 120,
                    "communicating": 15
                },
                "sla_target_minutes": 10,
                "traditional_mttr_minutes": 60
            }
        }
    
    async def start_demo_scenario(
        self, 
        scenario_type: DemoScenarioType,
        session_id: Optional[str] = None
    ) -> DemoSession:
        """
        Start a controlled demo scenario with deterministic execution.
        
        Args:
            scenario_type: Type of scenario to execute
            session_id: Optional custom session ID
            
        Returns:
            DemoSession: Active demo session with real-time metrics
        """
        if session_id is None:
            session_id = f"demo_{scenario_type.value}_{int(time.time())}"
        
        logger.info(f"Starting demo scenario: {scenario_type.value} (session: {session_id})")
        
        # Create incident from scenario configuration
        config = self.scenario_configs[scenario_type]
        
        business_impact = BusinessImpact(
            service_tier=config["service_tier"],
            affected_users=config["affected_users"],
            revenue_impact_per_minute=config["revenue_impact_per_minute"]
        )
        
        metadata = IncidentMetadata(
            source_system="demo_controller",
            tags={
                "demo": "true",
                "scenario": scenario_type.value,
                "complexity": config["complexity"],
                "session_id": session_id,
                "controlled_execution": "true"
            }
        )
        
        incident = Incident(
            title=config["title"],
            description=config["description"],
            severity=config["severity"],
            business_impact=business_impact,
            metadata=metadata
        )
        
        # Initialize demo session
        demo_session = DemoSession(
            session_id=session_id,
            scenario_type=scenario_type,
            incident_id=incident.id,
            start_time=datetime.utcnow()
        )
        
        # Initialize metrics
        demo_session.metrics.cost_per_minute = config["revenue_impact_per_minute"]
        demo_session.metrics.affected_users = config["affected_users"]
        demo_session.metrics.traditional_mttr_estimate = config["traditional_mttr_minutes"] * 60
        demo_session.metrics.sla_breach_countdown = config["sla_target_minutes"] * 60
        
        # Store active session
        self.active_sessions[session_id] = demo_session
        
        # Start processing in background with controlled execution
        self._schedule_task(
            self._execute_controlled_scenario(demo_session, incident),
            f"demo-session-{session_id}"
        )
        
        logger.info(f"Demo scenario started: {session_id}")
        return demo_session
    
    async def _execute_controlled_scenario(self, session: DemoSession, incident: Incident):
        """Execute scenario with controlled timing and guaranteed completion."""
        try:
            # Get coordinator
            if self.coordinator is None:
                self.coordinator = get_swarm_coordinator()
            
            config = self.scenario_configs[session.scenario_type]
            
            # Phase 1: Detection
            session.current_phase = DemoPhase.DETECTING
            session.phase_timings["detecting_start"] = time.time()
            
            # Simulate controlled detection phase
            await asyncio.sleep(min(config["estimated_phases"]["detecting"], 30))
            session.phase_timings["detecting_end"] = time.time()
            session.agent_confidence_scores["detection"] = 0.95
            
            # Phase 2: Diagnosis
            session.current_phase = DemoPhase.DIAGNOSING
            session.phase_timings["diagnosing_start"] = time.time()
            
            # Simulate controlled diagnosis phase
            await asyncio.sleep(min(config["estimated_phases"]["diagnosing"], 90))
            session.phase_timings["diagnosing_end"] = time.time()
            session.agent_confidence_scores["diagnosis"] = 0.88
            
            # Phase 3: Prediction
            session.current_phase = DemoPhase.PREDICTING
            session.phase_timings["predicting_start"] = time.time()
            
            # Simulate controlled prediction phase
            await asyncio.sleep(min(config["estimated_phases"]["predicting"], 60))
            session.phase_timings["predicting_end"] = time.time()
            session.agent_confidence_scores["prediction"] = 0.82
            
            # Phase 4: Resolution
            session.current_phase = DemoPhase.RESOLVING
            session.phase_timings["resolving_start"] = time.time()
            
            # Simulate controlled resolution phase
            await asyncio.sleep(min(config["estimated_phases"]["resolving"], 120))
            session.phase_timings["resolving_end"] = time.time()
            session.agent_confidence_scores["resolution"] = 0.91
            
            # Phase 5: Communication
            session.current_phase = DemoPhase.COMMUNICATING
            session.phase_timings["communicating_start"] = time.time()
            
            # Simulate controlled communication phase
            await asyncio.sleep(min(config["estimated_phases"]["communicating"], 15))
            session.phase_timings["communicating_end"] = time.time()
            session.agent_confidence_scores["communication"] = 0.96
            
            # Complete demo
            session.current_phase = DemoPhase.COMPLETED
            session.is_active = False
            
            # Calculate final metrics
            total_time = time.time() - session.start_time.timestamp()
            session.metrics.mttr_seconds = total_time
            session.metrics.cost_accumulated = session.metrics.cost_per_minute * (total_time / 60.0)
            session.metrics.autonomous_improvement_percentage = (
                (session.metrics.traditional_mttr_estimate - total_time) / 
                session.metrics.traditional_mttr_estimate * 100
            )
            
            logger.info(f"Demo scenario completed: {session.session_id} in {total_time:.1f}s")
            
        except Exception as e:
            logger.error(f"Demo scenario failed: {session.session_id}: {e}")
            session.current_phase = DemoPhase.FAILED
            session.is_active = False
    
    def get_real_time_metrics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get real-time metrics for active demo session."""
        session = self.active_sessions.get(session_id)
        if not session:
            return None
        
        current_time = datetime.utcnow()
        elapsed_time = (current_time - session.start_time).total_seconds()
        
        # Update real-time metrics
        session.metrics.mttr_seconds = elapsed_time
        session.metrics.cost_accumulated = session.metrics.cost_per_minute * (elapsed_time / 60.0)
        session.metrics.sla_breach_countdown = max(0, session.metrics.sla_breach_countdown - elapsed_time)
        
        # Calculate reputation impact (increases over time)
        session.metrics.reputation_impact_score = min(100, (elapsed_time / 300) * 100)  # Max at 5 minutes
        
        # Calculate improvement percentage
        if elapsed_time > 0:
            session.metrics.autonomous_improvement_percentage = (
                (session.metrics.traditional_mttr_estimate - elapsed_time) / 
                session.metrics.traditional_mttr_estimate * 100
            )
        
        return {
            "session_id": session_id,
            "scenario_type": session.scenario_type.value,
            "current_phase": session.current_phase.value,
            "is_active": session.is_active,
            "elapsed_time_seconds": elapsed_time,
            "metrics": {
                "mttr_seconds": session.metrics.mttr_seconds,
                "cost_accumulated": round(session.metrics.cost_accumulated, 2),
                "cost_per_minute": session.metrics.cost_per_minute,
                "affected_users": session.metrics.affected_users,
                "sla_breach_countdown": session.metrics.sla_breach_countdown,
                "reputation_impact_score": round(session.metrics.reputation_impact_score, 1),
                "traditional_mttr_estimate": session.metrics.traditional_mttr_estimate,
                "autonomous_improvement_percentage": round(session.metrics.autonomous_improvement_percentage, 1)
            },
            "agent_confidence_scores": session.agent_confidence_scores,
            "phase_timings": session.phase_timings,
            "completion_guarantee_minutes": session.completion_guarantee_minutes,
            "environment_isolated": session.environment_isolated
        }
    
    def get_comparison_metrics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get before/after comparison metrics for demo visualization."""
        session = self.active_sessions.get(session_id)
        if not session:
            return None
        
        config = self.scenario_configs[session.scenario_type]
        current_time = datetime.utcnow()
        elapsed_time = (current_time - session.start_time).total_seconds()
        
        # Calculate improvement percentage
        traditional_mttr_seconds = config["traditional_mttr_minutes"] * 60
        improvement_percentage = ((traditional_mttr_seconds - elapsed_time) / traditional_mttr_seconds) * 100
        
        traditional_cost = config["traditional_mttr_minutes"] * session.metrics.cost_per_minute
        autonomous_cost = session.metrics.cost_accumulated
        
        # Calculate improvement percentage
        traditional_mttr_seconds = config["traditional_mttr_minutes"] * 60
        improvement_percentage = ((traditional_mttr_seconds - elapsed_time) / traditional_mttr_seconds) * 100
        
        return {
            "scenario": session.scenario_type.value,
            "traditional_response": {
                "mttr_minutes": config["traditional_mttr_minutes"],
                "total_cost": traditional_cost,
                "affected_users": session.metrics.affected_users,
                "manual_steps_required": 15,
                "human_intervention_points": 8
            },
            "autonomous_response": {
                "mttr_minutes": elapsed_time / 60.0,
                "total_cost": autonomous_cost,
                "affected_users": session.metrics.affected_users,
                "automated_steps": 12,
                "human_intervention_points": 0 if session.current_phase != DemoPhase.FAILED else 1
            },
            "improvement": {
                "mttr_reduction_percentage": improvement_percentage,
                "cost_savings": traditional_cost - autonomous_cost,
                "time_saved_minutes": config["traditional_mttr_minutes"] - (elapsed_time / 60.0),
                "automation_efficiency": 95.0 if session.current_phase != DemoPhase.FAILED else 0.0
            },
            "business_impact": {
                "revenue_protected": max(0, traditional_cost - autonomous_cost),
                "customer_satisfaction_improvement": 85.0,
                "sla_compliance": session.metrics.sla_breach_countdown > 0,
                "reputation_protection_score": 100 - session.metrics.reputation_impact_score
            }
        }
    
    def list_active_sessions(self) -> List[Dict[str, Any]]:
        """List all active demo sessions."""
        return [
            {
                "session_id": session_id,
                "scenario_type": session.scenario_type.value,
                "current_phase": session.current_phase.value,
                "is_active": session.is_active,
                "elapsed_time_seconds": (datetime.utcnow() - session.start_time).total_seconds(),
                "start_time": session.start_time.isoformat()
            }
            for session_id, session in self.active_sessions.items()
        ]
    
    def stop_demo_session(self, session_id: str) -> bool:
        """Stop an active demo session."""
        session = self.active_sessions.get(session_id)
        if not session:
            return False
        
        session.is_active = False
        session.current_phase = DemoPhase.COMPLETED
        logger.info(f"Demo session stopped: {session_id}")
        return True
    
    def cleanup_completed_sessions(self, max_age_hours: int = 24):
        """Clean up completed demo sessions older than specified age."""
        current_time = datetime.utcnow()
        sessions_to_remove = []
        
        for session_id, session in self.active_sessions.items():
            if not session.is_active:
                age = current_time - session.start_time
                if age.total_seconds() > max_age_hours * 3600:
                    sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.active_sessions[session_id]
            logger.info(f"Cleaned up completed demo session: {session_id}")
        
        return len(sessions_to_remove)


# Global demo controller instance
_demo_controller: Optional[DemoController] = None


def get_demo_controller(task_scheduler: Optional[Callable[[Awaitable[Any], str], None]] = None) -> DemoController:
    """Get the global demo controller instance."""
    global _demo_controller
    if _demo_controller is None:
        _demo_controller = DemoController(task_scheduler=task_scheduler)
    elif task_scheduler is not None:
        _demo_controller.set_task_scheduler(task_scheduler)
    return _demo_controller
