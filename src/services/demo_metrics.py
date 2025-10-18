"""
Demo Metrics and Performance Comparison

Provides before/after MTTR comparison, business impact calculation,
demo scenario timing validation, and judge interaction logging.

Task 12.3: Create demo metrics and performance comparison
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import statistics

from src.utils.logging import get_logger
from src.services.demo_controller import get_demo_controller, DemoScenarioType


logger = get_logger("demo_metrics")


class PerformanceMetricType(Enum):
    """Types of performance metrics."""
    MTTR_REDUCTION = "mttr_reduction"
    COST_SAVINGS = "cost_savings"
    AUTOMATION_EFFICIENCY = "automation_efficiency"
    BUSINESS_IMPACT_REDUCTION = "business_impact_reduction"
    SLA_COMPLIANCE = "sla_compliance"
    CUSTOMER_SATISFACTION = "customer_satisfaction"


@dataclass
class MTTRComparison:
    """MTTR comparison between traditional and autonomous response."""
    scenario_type: str
    traditional_mttr_minutes: float
    autonomous_mttr_minutes: float
    reduction_percentage: float
    time_saved_minutes: float
    improvement_factor: float


@dataclass
class BusinessImpactComparison:
    """Business impact comparison showing cost savings and efficiency gains."""
    scenario_type: str
    traditional_cost: float
    autonomous_cost: float
    cost_savings: float
    cost_savings_percentage: float
    affected_users: int
    revenue_protected: float
    customer_impact_reduction: float


@dataclass
class PerformanceGuarantee:
    """Performance guarantee validation for demo scenarios."""
    scenario_type: str
    guaranteed_completion_minutes: int
    actual_completion_minutes: float
    guarantee_met: bool
    performance_margin: float
    consistency_score: float


@dataclass
class JudgeInteractionLog:
    """Judge interaction logging for demo session recording."""
    session_id: str
    judge_id: str
    interaction_timestamp: datetime
    interaction_type: str
    interaction_data: Dict[str, Any]
    session_state_before: Dict[str, Any]
    session_state_after: Dict[str, Any]
    impact_on_metrics: Dict[str, float]


class DemoMetricsAnalyzer:
    """
    Demo metrics and performance comparison analyzer.
    
    Provides comprehensive analysis of demo performance, MTTR comparisons,
    business impact calculations, and performance guarantee validation.
    """
    
    def __init__(self):
        self.demo_controller = get_demo_controller()
        self.performance_history: Dict[str, List[Dict[str, Any]]] = {}
        self.judge_interaction_logs: List[JudgeInteractionLog] = []
        self.baseline_metrics = self._initialize_baseline_metrics()
        
    def _initialize_baseline_metrics(self) -> Dict[str, Dict[str, float]]:
        """Initialize baseline metrics for traditional incident response."""
        return {
            "database_cascade": {
                "traditional_mttr_minutes": 45,
                "traditional_cost_per_minute": 2000.0,
                "traditional_manual_steps": 15,
                "traditional_human_interventions": 8,
                "traditional_error_rate": 0.15,
                "traditional_escalation_rate": 0.25
            },
            "ddos_attack": {
                "traditional_mttr_minutes": 30,
                "traditional_cost_per_minute": 1500.0,
                "traditional_manual_steps": 12,
                "traditional_human_interventions": 6,
                "traditional_error_rate": 0.12,
                "traditional_escalation_rate": 0.20
            },
            "memory_leak": {
                "traditional_mttr_minutes": 25,
                "traditional_cost_per_minute": 300.0,
                "traditional_manual_steps": 8,
                "traditional_human_interventions": 4,
                "traditional_error_rate": 0.08,
                "traditional_escalation_rate": 0.15
            },
            "api_overload": {
                "traditional_mttr_minutes": 25,
                "traditional_cost_per_minute": 800.0,
                "traditional_manual_steps": 10,
                "traditional_human_interventions": 5,
                "traditional_error_rate": 0.10,
                "traditional_escalation_rate": 0.18
            },
            "storage_failure": {
                "traditional_mttr_minutes": 50,
                "traditional_cost_per_minute": 3000.0,
                "traditional_manual_steps": 18,
                "traditional_human_interventions": 10,
                "traditional_error_rate": 0.20,
                "traditional_escalation_rate": 0.30
            }
        }
    
    def calculate_mttr_comparison(self, session_id: str) -> MTTRComparison:
        """
        Calculate MTTR comparison showing 95% reduction demonstration.
        
        Provides dramatic before/after comparison with detailed metrics.
        """
        # Get session metrics
        session_metrics = self.demo_controller.get_real_time_metrics(session_id)
        if not session_metrics:
            raise ValueError(f"Session {session_id} not found")
        
        scenario_type = session_metrics["scenario_type"]
        baseline = self.baseline_metrics[scenario_type]
        
        traditional_mttr = baseline["traditional_mttr_minutes"]
        autonomous_mttr = session_metrics["metrics"]["mttr_seconds"] / 60.0
        
        reduction_percentage = ((traditional_mttr - autonomous_mttr) / traditional_mttr) * 100
        time_saved = traditional_mttr - autonomous_mttr
        improvement_factor = traditional_mttr / autonomous_mttr if autonomous_mttr > 0 else float('inf')
        
        return MTTRComparison(
            scenario_type=scenario_type,
            traditional_mttr_minutes=traditional_mttr,
            autonomous_mttr_minutes=autonomous_mttr,
            reduction_percentage=reduction_percentage,
            time_saved_minutes=time_saved,
            improvement_factor=improvement_factor
        )
    
    def calculate_business_impact_comparison(self, session_id: str) -> BusinessImpactComparison:
        """
        Calculate business impact and cost savings visualization.
        
        Shows dramatic cost reduction and business value creation.
        """
        session_metrics = self.demo_controller.get_real_time_metrics(session_id)
        if not session_metrics:
            raise ValueError(f"Session {session_id} not found")
        
        scenario_type = session_metrics["scenario_type"]
        baseline = self.baseline_metrics[scenario_type]
        
        traditional_cost = baseline["traditional_mttr_minutes"] * baseline["traditional_cost_per_minute"]
        autonomous_cost = session_metrics["metrics"]["cost_accumulated"]
        cost_savings = traditional_cost - autonomous_cost
        cost_savings_percentage = (cost_savings / traditional_cost) * 100 if traditional_cost > 0 else 0
        
        affected_users = session_metrics["metrics"]["affected_users"]
        revenue_protected = cost_savings
        
        # Calculate customer impact reduction based on MTTR improvement
        mttr_comparison = self.calculate_mttr_comparison(session_id)
        customer_impact_reduction = min(95.0, mttr_comparison.reduction_percentage * 0.9)  # Cap at 95%
        
        return BusinessImpactComparison(
            scenario_type=scenario_type,
            traditional_cost=traditional_cost,
            autonomous_cost=autonomous_cost,
            cost_savings=cost_savings,
            cost_savings_percentage=cost_savings_percentage,
            affected_users=affected_users,
            revenue_protected=revenue_protected,
            customer_impact_reduction=customer_impact_reduction
        )
    
    def validate_performance_guarantee(self, session_id: str) -> PerformanceGuarantee:
        """
        Validate demo scenario timing and performance guarantees.
        
        Ensures 5-minute completion guarantee and consistent performance.
        """
        session_metrics = self.demo_controller.get_real_time_metrics(session_id)
        if not session_metrics:
            raise ValueError(f"Session {session_id} not found")
        
        scenario_type = session_metrics["scenario_type"]
        guaranteed_completion_minutes = 5  # 5-minute guarantee
        actual_completion_minutes = session_metrics["metrics"]["mttr_seconds"] / 60.0
        
        guarantee_met = actual_completion_minutes <= guaranteed_completion_minutes
        performance_margin = guaranteed_completion_minutes - actual_completion_minutes
        
        # Calculate consistency score based on historical performance
        if scenario_type not in self.performance_history:
            self.performance_history[scenario_type] = []
        
        self.performance_history[scenario_type].append({
            "completion_time": actual_completion_minutes,
            "timestamp": datetime.utcnow()
        })
        
        # Calculate consistency score (lower standard deviation = higher consistency)
        recent_times = [
            entry["completion_time"] 
            for entry in self.performance_history[scenario_type][-10:]  # Last 10 runs
        ]
        
        if len(recent_times) > 1:
            std_dev = statistics.stdev(recent_times)
            consistency_score = max(0.0, 1.0 - (std_dev / guaranteed_completion_minutes))
        else:
            consistency_score = 1.0
        
        return PerformanceGuarantee(
            scenario_type=scenario_type,
            guaranteed_completion_minutes=guaranteed_completion_minutes,
            actual_completion_minutes=actual_completion_minutes,
            guarantee_met=guarantee_met,
            performance_margin=performance_margin,
            consistency_score=consistency_score
        )
    
    def log_judge_interaction(
        self,
        session_id: str,
        judge_id: str,
        interaction_type: str,
        interaction_data: Dict[str, Any]
    ) -> str:
        """
        Log judge interaction for demo session recording.
        
        Captures complete interaction context for replay and analysis.
        """
        # Get session state before interaction
        session_state_before = self.demo_controller.get_real_time_metrics(session_id)
        
        # Create interaction log
        interaction_log = JudgeInteractionLog(
            session_id=session_id,
            judge_id=judge_id,
            interaction_timestamp=datetime.utcnow(),
            interaction_type=interaction_type,
            interaction_data=interaction_data,
            session_state_before=session_state_before or {},
            session_state_after={},  # Will be updated after interaction
            impact_on_metrics={}
        )
        
        self.judge_interaction_logs.append(interaction_log)
        
        logger.info(f"Logged judge interaction: {interaction_type} for session {session_id}")
        return f"interaction_{len(self.judge_interaction_logs)}"
    
    def update_interaction_impact(
        self,
        interaction_index: int,
        session_state_after: Dict[str, Any],
        impact_on_metrics: Dict[str, float]
    ):
        """Update interaction log with post-interaction state and impact."""
        if 0 <= interaction_index < len(self.judge_interaction_logs):
            self.judge_interaction_logs[interaction_index].session_state_after = session_state_after
            self.judge_interaction_logs[interaction_index].impact_on_metrics = impact_on_metrics
    
    def generate_comprehensive_demo_report(self, session_id: str) -> Dict[str, Any]:
        """
        Generate comprehensive demo performance report.
        
        Includes all metrics, comparisons, and performance validations.
        """
        try:
            mttr_comparison = self.calculate_mttr_comparison(session_id)
            business_impact = self.calculate_business_impact_comparison(session_id)
            performance_guarantee = self.validate_performance_guarantee(session_id)
            
            # Get session-specific judge interactions
            session_interactions = [
                {
                    "interaction_type": log.interaction_type,
                    "timestamp": log.interaction_timestamp.isoformat(),
                    "interaction_data": log.interaction_data,
                    "impact_on_metrics": log.impact_on_metrics
                }
                for log in self.judge_interaction_logs
                if log.session_id == session_id
            ]
            
            return {
                "session_id": session_id,
                "report_timestamp": datetime.utcnow().isoformat(),
                "mttr_analysis": {
                    "traditional_mttr_minutes": mttr_comparison.traditional_mttr_minutes,
                    "autonomous_mttr_minutes": mttr_comparison.autonomous_mttr_minutes,
                    "reduction_percentage": mttr_comparison.reduction_percentage,
                    "time_saved_minutes": mttr_comparison.time_saved_minutes,
                    "improvement_factor": mttr_comparison.improvement_factor,
                    "meets_95_percent_target": mttr_comparison.reduction_percentage >= 95.0
                },
                "business_impact_analysis": {
                    "traditional_cost": business_impact.traditional_cost,
                    "autonomous_cost": business_impact.autonomous_cost,
                    "cost_savings": business_impact.cost_savings,
                    "cost_savings_percentage": business_impact.cost_savings_percentage,
                    "revenue_protected": business_impact.revenue_protected,
                    "affected_users": business_impact.affected_users,
                    "customer_impact_reduction": business_impact.customer_impact_reduction
                },
                "performance_validation": {
                    "guaranteed_completion_minutes": performance_guarantee.guaranteed_completion_minutes,
                    "actual_completion_minutes": performance_guarantee.actual_completion_minutes,
                    "guarantee_met": performance_guarantee.guarantee_met,
                    "performance_margin_minutes": performance_guarantee.performance_margin,
                    "consistency_score": performance_guarantee.consistency_score
                },
                "judge_interactions": {
                    "total_interactions": len(session_interactions),
                    "interaction_log": session_interactions
                },
                "key_achievements": {
                    "mttr_reduction_achieved": f"{mttr_comparison.reduction_percentage:.1f}%",
                    "cost_savings_achieved": f"${business_impact.cost_savings:,.2f}",
                    "performance_guarantee_met": performance_guarantee.guarantee_met,
                    "customer_impact_reduced": f"{business_impact.customer_impact_reduction:.1f}%"
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate demo report for session {session_id}: {e}")
            raise
    
    def get_aggregate_performance_metrics(self) -> Dict[str, Any]:
        """
        Get aggregate performance metrics across all demo sessions.
        
        Provides overall system performance and consistency analysis.
        """
        if not self.performance_history:
            return {"message": "No performance history available"}
        
        aggregate_metrics = {}
        
        for scenario_type, history in self.performance_history.items():
            if not history:
                continue
                
            completion_times = [entry["completion_time"] for entry in history]
            
            aggregate_metrics[scenario_type] = {
                "total_runs": len(completion_times),
                "average_completion_minutes": statistics.mean(completion_times),
                "median_completion_minutes": statistics.median(completion_times),
                "min_completion_minutes": min(completion_times),
                "max_completion_minutes": max(completion_times),
                "std_deviation": statistics.stdev(completion_times) if len(completion_times) > 1 else 0.0,
                "consistency_score": max(0.0, 1.0 - (statistics.stdev(completion_times) / 5.0)) if len(completion_times) > 1 else 1.0,
                "guarantee_success_rate": sum(1 for t in completion_times if t <= 5.0) / len(completion_times)
            }
        
        # Calculate overall system metrics
        all_completion_times = []
        for history in self.performance_history.values():
            all_completion_times.extend([entry["completion_time"] for entry in history])
        
        if all_completion_times:
            aggregate_metrics["overall_system"] = {
                "total_demo_runs": len(all_completion_times),
                "average_completion_minutes": statistics.mean(all_completion_times),
                "overall_guarantee_success_rate": sum(1 for t in all_completion_times if t <= 5.0) / len(all_completion_times),
                "overall_consistency_score": max(0.0, 1.0 - (statistics.stdev(all_completion_times) / 5.0)) if len(all_completion_times) > 1 else 1.0
            }
        
        return {
            "aggregate_performance": aggregate_metrics,
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "performance_summary": {
                "scenarios_analyzed": len(self.performance_history),
                "total_demo_sessions": sum(len(history) for history in self.performance_history.values()),
                "overall_performance_rating": "excellent" if aggregate_metrics.get("overall_system", {}).get("overall_guarantee_success_rate", 0) > 0.95 else "good"
            }
        }
    
    def get_judge_interaction_analytics(self, judge_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get analytics on judge interactions for demo improvement.
        
        Analyzes interaction patterns and their impact on demo effectiveness.
        """
        relevant_logs = self.judge_interaction_logs
        if judge_id:
            relevant_logs = [log for log in self.judge_interaction_logs if log.judge_id == judge_id]
        
        if not relevant_logs:
            return {"message": f"No interaction logs found{' for judge ' + judge_id if judge_id else ''}"}
        
        # Analyze interaction patterns
        interaction_types = {}
        interaction_impact = {}
        
        for log in relevant_logs:
            # Count interaction types
            if log.interaction_type not in interaction_types:
                interaction_types[log.interaction_type] = 0
            interaction_types[log.interaction_type] += 1
            
            # Analyze impact on metrics
            for metric, impact in log.impact_on_metrics.items():
                if metric not in interaction_impact:
                    interaction_impact[metric] = []
                interaction_impact[metric].append(impact)
        
        # Calculate average impacts
        average_impacts = {}
        for metric, impacts in interaction_impact.items():
            if impacts:
                average_impacts[metric] = {
                    "average_impact": statistics.mean(impacts),
                    "max_impact": max(impacts),
                    "min_impact": min(impacts),
                    "impact_consistency": 1.0 - (statistics.stdev(impacts) / abs(statistics.mean(impacts))) if len(impacts) > 1 and statistics.mean(impacts) != 0 else 1.0
                }
        
        return {
            "judge_id": judge_id or "all_judges",
            "analysis_period": {
                "start_time": min(log.interaction_timestamp for log in relevant_logs).isoformat(),
                "end_time": max(log.interaction_timestamp for log in relevant_logs).isoformat(),
                "total_interactions": len(relevant_logs)
            },
            "interaction_patterns": {
                "interaction_type_distribution": interaction_types,
                "most_common_interaction": max(interaction_types.items(), key=lambda x: x[1])[0] if interaction_types else None,
                "interaction_frequency": len(relevant_logs) / max(1, (max(log.interaction_timestamp for log in relevant_logs) - min(log.interaction_timestamp for log in relevant_logs)).total_seconds() / 3600)  # per hour
            },
            "interaction_impact_analysis": average_impacts,
            "demo_effectiveness": {
                "judge_engagement_score": min(1.0, len(relevant_logs) / 10.0),  # Normalize to 0-1
                "interaction_diversity": len(interaction_types) / 5.0,  # Assuming 5 possible interaction types
                "demo_interactivity_rating": "high" if len(relevant_logs) > 5 else "medium" if len(relevant_logs) > 2 else "low"
            }
        }


# Global demo metrics analyzer instance
_demo_metrics_analyzer = None


def get_demo_metrics_analyzer() -> DemoMetricsAnalyzer:
    """Get the global demo metrics analyzer instance."""
    global _demo_metrics_analyzer
    if _demo_metrics_analyzer is None:
        _demo_metrics_analyzer = DemoMetricsAnalyzer()
    return _demo_metrics_analyzer