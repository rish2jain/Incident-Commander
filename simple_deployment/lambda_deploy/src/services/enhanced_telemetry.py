"""
Enhanced Agent Telemetry System

Provides comprehensive operational visibility with per-agent execution stats,
error tracking by severity, and real-time performance monitoring.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque

from src.utils.logging import get_logger


logger = get_logger("enhanced_telemetry")


class ErrorSeverity(Enum):
    """Error severity levels for telemetry tracking."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AgentExecution:
    """Enhanced agent execution tracking with comprehensive metrics."""
    execution_id: str
    agent_id: str
    agent_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "running"
    confidence_score: float = 0.0
    execution_time_ms: Optional[int] = None
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    guardrail_hits: List[Dict[str, Any]] = field(default_factory=list)
    
    def complete(self, status: str = "completed", confidence: float = 0.0):
        """Mark execution as complete with final metrics."""
        self.end_time = datetime.utcnow()
        self.status = status
        self.confidence_score = confidence
        if self.start_time:
            self.execution_time_ms = int((self.end_time - self.start_time).total_seconds() * 1000)
    
    def add_error(self, error_type: str, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM):
        """Add error to execution tracking."""
        self.errors.append({
            "timestamp": datetime.utcnow().isoformat(),
            "type": error_type,
            "message": message,
            "severity": severity.value
        })
    
    def add_guardrail_hit(self, guardrail_type: str, action: str, blocked: bool = True):
        """Track guardrail policy hits."""
        self.guardrail_hits.append({
            "timestamp": datetime.utcnow().isoformat(),
            "guardrail_type": guardrail_type,
            "action": action,
            "blocked": blocked
        })


class EnhancedTelemetryService:
    """Comprehensive telemetry service for agent monitoring."""
    
    def __init__(self):
        self.executions: Dict[str, AgentExecution] = {}
        self.agent_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_execution_time": 0.0,
            "average_confidence": 0.0,
            "error_count_by_severity": defaultdict(int),
            "recent_executions": deque(maxlen=100),
            "guardrail_hits": 0,
            "performance_trend": deque(maxlen=50)
        })
        self.system_metrics = {
            "total_incidents_processed": 0,
            "average_resolution_time": 0.0,
            "success_rate": 0.0,
            "cost_savings": 0.0,
            "uptime_percentage": 99.9
        }
        
    async def start_execution(self, agent_id: str, agent_type: str) -> str:
        """Start tracking a new agent execution."""
        execution_id = f"{agent_id}-{int(datetime.utcnow().timestamp() * 1000)}"
        
        execution = AgentExecution(
            execution_id=execution_id,
            agent_id=agent_id,
            agent_type=agent_type,
            start_time=datetime.utcnow()
        )
        
        self.executions[execution_id] = execution
        self.agent_stats[agent_id]["total_executions"] += 1
        
        logger.info(f"Started execution tracking: {execution_id}")
        return execution_id
    
    async def complete_execution(self, execution_id: str, status: str = "completed", 
                               confidence: float = 0.0, metrics: Dict[str, Any] = None):
        """Complete an agent execution with final metrics."""
        if execution_id not in self.executions:
            logger.warning(f"Execution not found: {execution_id}")
            return
        
        execution = self.executions[execution_id]
        execution.complete(status, confidence)
        
        if metrics:
            execution.performance_metrics.update(metrics)
        
        # Update agent statistics
        agent_stats = self.agent_stats[execution.agent_id]
        
        if status == "completed":
            agent_stats["successful_executions"] += 1
        else:
            agent_stats["failed_executions"] += 1
        
        # Update averages
        agent_stats["recent_executions"].append({
            "execution_id": execution_id,
            "execution_time": execution.execution_time_ms,
            "confidence": confidence,
            "status": status,
            "timestamp": execution.end_time.isoformat()
        })
        
        # Calculate rolling averages
        recent_times = [e["execution_time"] for e in agent_stats["recent_executions"] 
                       if e["execution_time"] is not None]
        recent_confidences = [e["confidence"] for e in agent_stats["recent_executions"]]
        
        if recent_times:
            agent_stats["average_execution_time"] = sum(recent_times) / len(recent_times)
        if recent_confidences:
            agent_stats["average_confidence"] = sum(recent_confidences) / len(recent_confidences)
        
        # Update performance trend
        agent_stats["performance_trend"].append({
            "timestamp": execution.end_time.isoformat(),
            "execution_time": execution.execution_time_ms,
            "confidence": confidence,
            "success": status == "completed"
        })
        
        logger.info(f"Completed execution tracking: {execution_id} ({status})")
    
    async def add_execution_error(self, execution_id: str, error_type: str, 
                                message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM):
        """Add error to execution tracking."""
        if execution_id in self.executions:
            execution = self.executions[execution_id]
            execution.add_error(error_type, message, severity)
            
            # Update agent error statistics
            agent_stats = self.agent_stats[execution.agent_id]
            agent_stats["error_count_by_severity"][severity.value] += 1
    
    async def add_guardrail_hit(self, execution_id: str, guardrail_type: str, 
                              action: str, blocked: bool = True):
        """Track guardrail policy hits."""
        if execution_id in self.executions:
            execution = self.executions[execution_id]
            execution.add_guardrail_hit(guardrail_type, action, blocked)
            
            # Update agent guardrail statistics
            agent_stats = self.agent_stats[execution.agent_id]
            agent_stats["guardrail_hits"] += 1
    
    async def get_agent_telemetry(self, agent_id: str) -> Dict[str, Any]:
        """Get comprehensive telemetry for a specific agent."""
        if agent_id not in self.agent_stats:
            return {"error": f"No telemetry data for agent: {agent_id}"}
        
        stats = self.agent_stats[agent_id]
        
        # Calculate success rate
        total = stats["total_executions"]
        success_rate = (stats["successful_executions"] / total * 100) if total > 0 else 0
        
        # Get recent performance trend
        recent_trend = list(stats["performance_trend"])[-10:]  # Last 10 executions
        
        return {
            "agent_id": agent_id,
            "summary": {
                "total_executions": total,
                "success_rate": round(success_rate, 2),
                "average_execution_time_ms": round(stats["average_execution_time"], 2),
                "average_confidence": round(stats["average_confidence"], 3),
                "guardrail_hits": stats["guardrail_hits"]
            },
            "error_breakdown": dict(stats["error_count_by_severity"]),
            "recent_performance": recent_trend,
            "status": "healthy" if success_rate > 90 else "degraded" if success_rate > 70 else "critical"
        }
    
    async def get_system_telemetry(self) -> Dict[str, Any]:
        """Get comprehensive system-wide telemetry."""
        # Aggregate across all agents
        total_executions = sum(stats["total_executions"] for stats in self.agent_stats.values())
        total_successful = sum(stats["successful_executions"] for stats in self.agent_stats.values())
        total_failed = sum(stats["failed_executions"] for stats in self.agent_stats.values())
        
        system_success_rate = (total_successful / total_executions * 100) if total_executions > 0 else 0
        
        # Calculate average execution time across all agents
        all_times = []
        for stats in self.agent_stats.values():
            all_times.extend([e["execution_time"] for e in stats["recent_executions"] 
                            if e["execution_time"] is not None])
        
        avg_execution_time = sum(all_times) / len(all_times) if all_times else 0
        
        # Error analysis
        error_summary = defaultdict(int)
        for stats in self.agent_stats.values():
            for severity, count in stats["error_count_by_severity"].items():
                error_summary[severity] += count
        
        # Guardrail analysis
        total_guardrail_hits = sum(stats["guardrail_hits"] for stats in self.agent_stats.values())
        
        return {
            "system_overview": {
                "total_executions": total_executions,
                "success_rate": round(system_success_rate, 2),
                "average_execution_time_ms": round(avg_execution_time, 2),
                "total_guardrail_hits": total_guardrail_hits,
                "active_agents": len(self.agent_stats),
                "system_health": "healthy" if system_success_rate > 95 else "degraded"
            },
            "error_analysis": dict(error_summary),
            "agent_breakdown": {
                agent_id: {
                    "executions": stats["total_executions"],
                    "success_rate": round((stats["successful_executions"] / stats["total_executions"] * 100) 
                                        if stats["total_executions"] > 0 else 0, 2),
                    "avg_confidence": round(stats["average_confidence"], 3)
                }
                for agent_id, stats in self.agent_stats.items()
            },
            "performance_trends": {
                "last_hour_executions": self._get_recent_execution_count(timedelta(hours=1)),
                "last_day_executions": self._get_recent_execution_count(timedelta(days=1)),
                "peak_execution_time": max(all_times) if all_times else 0,
                "min_execution_time": min(all_times) if all_times else 0
            }
        }
    
    def _get_recent_execution_count(self, time_window: timedelta) -> int:
        """Get execution count within time window."""
        cutoff_time = datetime.utcnow() - time_window
        count = 0
        
        for stats in self.agent_stats.values():
            for execution in stats["recent_executions"]:
                exec_time = datetime.fromisoformat(execution["timestamp"])
                if exec_time > cutoff_time:
                    count += 1
        
        return count
    
    async def get_live_dashboard_data(self) -> Dict[str, Any]:
        """Get real-time data for live dashboard updates."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "active_executions": len([e for e in self.executions.values() if e.status == "running"]),
            "system_load": {
                "cpu_usage": 45.2,  # Would be real metrics in production
                "memory_usage": 67.8,
                "network_io": 23.4
            },
            "recent_activity": [
                {
                    "agent_id": execution.agent_id,
                    "status": execution.status,
                    "confidence": execution.confidence_score,
                    "execution_time": execution.execution_time_ms
                }
                for execution in list(self.executions.values())[-10:]
            ]
        }


# Global telemetry service instance
enhanced_telemetry = EnhancedTelemetryService()