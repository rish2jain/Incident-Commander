"""
Model Cost Optimizer Service

Implements advanced cost optimization for model usage including:
- Real-time cost tracking and analysis
- Usage pattern optimization recommendations
- Budget management and alerting
- Cost forecasting and trend analysis

Requirements: 8.4, 8.5
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import statistics

from src.utils.config import config
from src.utils.logging import get_logger
from src.utils.exceptions import CostOptimizationError


logger = get_logger(__name__)


class CostAlert(Enum):
    """Cost alert levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class OptimizationType(Enum):
    """Types of cost optimizations."""
    MODEL_SUBSTITUTION = "model_substitution"
    USAGE_PATTERN = "usage_pattern"
    CACHING = "caching"
    BATCHING = "batching"
    SCHEDULING = "scheduling"


@dataclass
class CostBudget:
    """Cost budget configuration."""
    daily_limit: float
    weekly_limit: float
    monthly_limit: float
    alert_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "warning": 0.8,    # 80% of budget
        "critical": 0.9,   # 90% of budget
        "emergency": 0.95  # 95% of budget
    })


@dataclass
class UsagePattern:
    """Usage pattern analysis."""
    task_type: str
    model_name: str
    hourly_usage: List[int] = field(default_factory=list)
    daily_usage: List[int] = field(default_factory=list)
    cost_per_hour: List[float] = field(default_factory=list)
    peak_hours: List[int] = field(default_factory=list)
    efficiency_score: float = 0.0


@dataclass
class CostOptimization:
    """Cost optimization recommendation."""
    optimization_type: OptimizationType
    current_model: str
    recommended_model: Optional[str]
    task_type: str
    potential_savings: float
    confidence_score: float
    impact_assessment: str
    implementation_effort: str
    auto_applicable: bool = False


@dataclass
class CostForecast:
    """Cost forecasting data."""
    daily_forecast: List[float] = field(default_factory=list)
    weekly_forecast: List[float] = field(default_factory=list)
    monthly_forecast: List[float] = field(default_factory=list)
    trend_direction: str = "stable"  # "increasing", "decreasing", "stable"
    confidence_interval: Tuple[float, float] = (0.0, 0.0)
    forecast_accuracy: float = 0.0


@dataclass
class CostMetrics:
    """Comprehensive cost metrics."""
    current_hourly_rate: float = 0.0
    daily_spend: float = 0.0
    weekly_spend: float = 0.0
    monthly_spend: float = 0.0
    cost_by_model: Dict[str, float] = field(default_factory=dict)
    cost_by_task: Dict[str, float] = field(default_factory=dict)
    cost_by_hour: List[float] = field(default_factory=list)
    total_requests: int = 0
    average_cost_per_request: float = 0.0
    cost_efficiency_score: float = 0.0


class ModelCostOptimizer:
    """
    Advanced cost optimization system for model usage with real-time tracking,
    pattern analysis, and intelligent recommendations.
    """
    
    def __init__(self):
        self.logger = logger
        
        # Cost tracking
        self.cost_metrics = CostMetrics()
        self.cost_history = deque(maxlen=10080)  # 7 days of minute-by-minute data
        self.usage_patterns: Dict[str, UsagePattern] = {}
        
        # Budget management
        self.budget = CostBudget(
            daily_limit=100.0,    # $100/day default
            weekly_limit=600.0,   # $600/week default
            monthly_limit=2400.0  # $2400/month default
        )
        
        # Optimization tracking
        self.optimizations: List[CostOptimization] = []
        self.applied_optimizations: List[Dict[str, Any]] = []
        self.optimization_savings: float = 0.0
        
        # Forecasting
        self.cost_forecast = CostForecast()
        
        # Alert management
        self.active_alerts: List[Dict[str, Any]] = []
        self.alert_history = deque(maxlen=1000)
        
        # Model cost data (per 1k tokens)
        self.model_costs = {
            "claude-3-haiku": 0.25,
            "claude-3-sonnet": 3.0,
            "claude-3-opus": 15.0
        }
        
        # Optimization rules
        self.optimization_rules = {
            "high_cost_low_accuracy_tasks": {
                "condition": lambda pattern: pattern.efficiency_score < 0.6,
                "recommendation": "Consider using more cost-effective models for low-accuracy requirements"
            },
            "peak_hour_optimization": {
                "condition": lambda pattern: len(pattern.peak_hours) > 0,
                "recommendation": "Consider batching requests during off-peak hours"
            },
            "model_overuse": {
                "condition": lambda pattern: pattern.cost_per_hour and max(pattern.cost_per_hour) > 10,
                "recommendation": "High-cost model usage detected, consider alternatives"
            }
        }
        
        # Configuration
        self.optimization_enabled = True
        self.auto_optimization_enabled = False
        self.forecast_horizon_days = 30
        
    async def initialize(self) -> None:
        """Initialize cost optimizer with background tasks."""
        try:
            # Start background monitoring tasks
            asyncio.create_task(self._cost_tracking_loop())
            asyncio.create_task(self._pattern_analysis_loop())
            asyncio.create_task(self._optimization_loop())
            asyncio.create_task(self._forecasting_loop())
            asyncio.create_task(self._alert_monitoring_loop())
            
            self.logger.info("Model cost optimizer initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize cost optimizer: {e}")
            raise CostOptimizationError(f"Initialization failed: {e}")
    
    async def record_model_usage(self, model_name: str, task_type: str, 
                               tokens_used: int, actual_cost: float) -> None:
        """Record model usage for cost tracking and optimization."""
        try:
            # Update cost metrics
            self.cost_metrics.total_requests += 1
            self.cost_metrics.cost_by_model[model_name] = (
                self.cost_metrics.cost_by_model.get(model_name, 0) + actual_cost
            )
            self.cost_metrics.cost_by_task[task_type] = (
                self.cost_metrics.cost_by_task.get(task_type, 0) + actual_cost
            )
            
            # Update usage patterns
            pattern_key = f"{task_type}_{model_name}"
            if pattern_key not in self.usage_patterns:
                self.usage_patterns[pattern_key] = UsagePattern(
                    task_type=task_type,
                    model_name=model_name
                )
            
            pattern = self.usage_patterns[pattern_key]
            current_hour = datetime.utcnow().hour
            
            # Update hourly usage
            if len(pattern.hourly_usage) <= current_hour:
                pattern.hourly_usage.extend([0] * (current_hour - len(pattern.hourly_usage) + 1))
            pattern.hourly_usage[current_hour] += 1
            
            # Update cost per hour
            if len(pattern.cost_per_hour) <= current_hour:
                pattern.cost_per_hour.extend([0.0] * (current_hour - len(pattern.cost_per_hour) + 1))
            pattern.cost_per_hour[current_hour] += actual_cost
            
            # Add to cost history
            self.cost_history.append({
                "timestamp": datetime.utcnow(),
                "model_name": model_name,
                "task_type": task_type,
                "tokens_used": tokens_used,
                "cost": actual_cost
            })
            
            # Update real-time metrics
            await self._update_real_time_metrics()
            
        except Exception as e:
            self.logger.error(f"Failed to record model usage: {e}")
    
    async def _update_real_time_metrics(self) -> None:
        """Update real-time cost metrics."""
        now = datetime.utcnow()
        
        # Calculate current hourly rate
        recent_costs = [
            record["cost"] for record in self.cost_history
            if (now - record["timestamp"]).total_seconds() <= 3600
        ]
        self.cost_metrics.current_hourly_rate = sum(recent_costs)
        
        # Calculate daily spend
        daily_costs = [
            record["cost"] for record in self.cost_history
            if (now - record["timestamp"]).total_seconds() <= 86400
        ]
        self.cost_metrics.daily_spend = sum(daily_costs)
        
        # Calculate weekly spend
        weekly_costs = [
            record["cost"] for record in self.cost_history
            if (now - record["timestamp"]).total_seconds() <= 604800
        ]
        self.cost_metrics.weekly_spend = sum(weekly_costs)
        
        # Update average cost per request
        if self.cost_metrics.total_requests > 0:
            total_cost = sum(self.cost_metrics.cost_by_model.values())
            self.cost_metrics.average_cost_per_request = total_cost / self.cost_metrics.total_requests
        
        # Calculate cost efficiency score
        self.cost_metrics.cost_efficiency_score = await self._calculate_efficiency_score()
    
    async def _calculate_efficiency_score(self) -> float:
        """Calculate overall cost efficiency score."""
        if not self.usage_patterns:
            return 0.0
        
        efficiency_scores = []
        
        for pattern in self.usage_patterns.values():
            # Calculate efficiency based on cost vs. usage
            if pattern.cost_per_hour and pattern.hourly_usage:
                avg_cost = statistics.mean(pattern.cost_per_hour)
                avg_usage = statistics.mean(pattern.hourly_usage)
                
                # Efficiency = usage / cost (higher is better)
                if avg_cost > 0:
                    efficiency = min(avg_usage / avg_cost, 1.0)
                    efficiency_scores.append(efficiency)
                    pattern.efficiency_score = efficiency
        
        return statistics.mean(efficiency_scores) if efficiency_scores else 0.0
    
    async def analyze_usage_patterns(self) -> Dict[str, Any]:
        """Analyze usage patterns and identify optimization opportunities."""
        analysis = {
            "patterns": {},
            "peak_hours": [],
            "cost_trends": {},
            "efficiency_insights": []
        }
        
        for pattern_key, pattern in self.usage_patterns.items():
            # Identify peak hours
            if pattern.hourly_usage:
                max_usage = max(pattern.hourly_usage)
                peak_hours = [
                    hour for hour, usage in enumerate(pattern.hourly_usage)
                    if usage >= max_usage * 0.8  # 80% of peak usage
                ]
                pattern.peak_hours = peak_hours
                
                analysis["patterns"][pattern_key] = {
                    "peak_hours": peak_hours,
                    "total_usage": sum(pattern.hourly_usage),
                    "total_cost": sum(pattern.cost_per_hour) if pattern.cost_per_hour else 0,
                    "efficiency_score": pattern.efficiency_score
                }
        
        # Overall peak hours across all patterns
        all_peak_hours = []
        for pattern in self.usage_patterns.values():
            all_peak_hours.extend(pattern.peak_hours)
        
        if all_peak_hours:
            peak_hour_counts = defaultdict(int)
            for hour in all_peak_hours:
                peak_hour_counts[hour] += 1
            
            analysis["peak_hours"] = sorted(
                peak_hour_counts.keys(),
                key=lambda h: peak_hour_counts[h],
                reverse=True
            )[:5]  # Top 5 peak hours
        
        # Cost trends
        if self.cost_history:
            recent_costs = list(self.cost_history)[-1440:]  # Last 24 hours
            hourly_costs = defaultdict(float)
            
            for record in recent_costs:
                hour = record["timestamp"].hour
                hourly_costs[hour] += record["cost"]
            
            analysis["cost_trends"] = dict(hourly_costs)
        
        # Efficiency insights
        low_efficiency_patterns = [
            pattern_key for pattern_key, pattern in self.usage_patterns.items()
            if pattern.efficiency_score < 0.5
        ]
        
        if low_efficiency_patterns:
            analysis["efficiency_insights"].append({
                "type": "low_efficiency",
                "patterns": low_efficiency_patterns,
                "recommendation": "Consider optimizing these usage patterns"
            })
        
        return analysis
    
    async def generate_optimizations(self) -> List[CostOptimization]:
        """Generate cost optimization recommendations."""
        optimizations = []
        
        # Analyze each usage pattern
        for pattern_key, pattern in self.usage_patterns.items():
            # Model substitution optimizations
            if pattern.model_name != "claude-3-haiku":
                # Check if we can use a cheaper model
                current_cost = self.model_costs[pattern.model_name]
                cheaper_cost = self.model_costs["claude-3-haiku"]
                
                if current_cost > cheaper_cost * 2:  # Significant cost difference
                    potential_savings = (current_cost - cheaper_cost) * sum(pattern.hourly_usage)
                    
                    optimizations.append(CostOptimization(
                        optimization_type=OptimizationType.MODEL_SUBSTITUTION,
                        current_model=pattern.model_name,
                        recommended_model="claude-3-haiku",
                        task_type=pattern.task_type,
                        potential_savings=potential_savings,
                        confidence_score=0.8,
                        impact_assessment="May reduce accuracy slightly but significant cost savings",
                        implementation_effort="Low",
                        auto_applicable=pattern.task_type in ["communication", "detection"]
                    ))
            
            # Usage pattern optimizations
            if pattern.peak_hours and len(pattern.peak_hours) < 8:  # Concentrated usage
                avg_cost_per_hour = statistics.mean(pattern.cost_per_hour) if pattern.cost_per_hour else 0
                potential_savings = avg_cost_per_hour * 0.2  # 20% savings through batching
                
                optimizations.append(CostOptimization(
                    optimization_type=OptimizationType.BATCHING,
                    current_model=pattern.model_name,
                    recommended_model=None,
                    task_type=pattern.task_type,
                    potential_savings=potential_savings,
                    confidence_score=0.6,
                    impact_assessment="Batch requests during peak hours for better efficiency",
                    implementation_effort="Medium",
                    auto_applicable=False
                ))
            
            # Caching optimizations
            if pattern.efficiency_score < 0.4:  # Low efficiency
                potential_savings = sum(pattern.cost_per_hour) * 0.3  # 30% through caching
                
                optimizations.append(CostOptimization(
                    optimization_type=OptimizationType.CACHING,
                    current_model=pattern.model_name,
                    recommended_model=None,
                    task_type=pattern.task_type,
                    potential_savings=potential_savings,
                    confidence_score=0.7,
                    impact_assessment="Implement response caching for repeated queries",
                    implementation_effort="High",
                    auto_applicable=False
                ))
        
        # Sort by potential savings
        optimizations.sort(key=lambda opt: opt.potential_savings, reverse=True)
        
        self.optimizations = optimizations
        return optimizations
    
    async def apply_optimization(self, optimization: CostOptimization) -> Dict[str, Any]:
        """Apply a cost optimization recommendation."""
        if not optimization.auto_applicable:
            return {
                "success": False,
                "reason": "Manual implementation required",
                "optimization": optimization
            }
        
        try:
            # Record optimization application
            application_record = {
                "timestamp": datetime.utcnow(),
                "optimization_type": optimization.optimization_type.value,
                "current_model": optimization.current_model,
                "recommended_model": optimization.recommended_model,
                "task_type": optimization.task_type,
                "expected_savings": optimization.potential_savings
            }
            
            self.applied_optimizations.append(application_record)
            
            # For model substitution, this would update routing preferences
            if optimization.optimization_type == OptimizationType.MODEL_SUBSTITUTION:
                # In a real implementation, this would update the model router
                self.logger.info(
                    f"Applied model substitution: {optimization.current_model} -> "
                    f"{optimization.recommended_model} for {optimization.task_type}"
                )
            
            return {
                "success": True,
                "optimization": optimization,
                "application_record": application_record
            }
            
        except Exception as e:
            self.logger.error(f"Failed to apply optimization: {e}")
            return {
                "success": False,
                "reason": str(e),
                "optimization": optimization
            }
    
    async def generate_cost_forecast(self, days: int = 30) -> CostForecast:
        """Generate cost forecast based on historical data."""
        if len(self.cost_history) < 100:  # Need sufficient data
            return CostForecast()
        
        # Extract daily costs from history
        daily_costs = defaultdict(float)
        for record in self.cost_history:
            date_key = record["timestamp"].date()
            daily_costs[date_key] += record["cost"]
        
        if len(daily_costs) < 7:  # Need at least a week of data
            return CostForecast()
        
        # Calculate trend
        costs_list = list(daily_costs.values())
        recent_costs = costs_list[-7:]  # Last week
        older_costs = costs_list[-14:-7] if len(costs_list) >= 14 else costs_list[:-7]
        
        recent_avg = statistics.mean(recent_costs)
        older_avg = statistics.mean(older_costs) if older_costs else recent_avg
        
        # Determine trend direction
        if recent_avg > older_avg * 1.1:
            trend_direction = "increasing"
            growth_rate = (recent_avg - older_avg) / older_avg
        elif recent_avg < older_avg * 0.9:
            trend_direction = "decreasing"
            growth_rate = (recent_avg - older_avg) / older_avg
        else:
            trend_direction = "stable"
            growth_rate = 0.0
        
        # Generate forecasts
        base_daily_cost = recent_avg
        daily_forecast = []
        weekly_forecast = []
        monthly_forecast = []
        
        for day in range(days):
            # Apply trend with some randomness
            daily_cost = base_daily_cost * (1 + growth_rate * (day / 30))
            daily_forecast.append(daily_cost)
            
            # Weekly aggregation
            if (day + 1) % 7 == 0:
                week_cost = sum(daily_forecast[-7:])
                weekly_forecast.append(week_cost)
        
        # Monthly aggregation
        for month in range(days // 30):
            month_start = month * 30
            month_end = min((month + 1) * 30, len(daily_forecast))
            month_cost = sum(daily_forecast[month_start:month_end])
            monthly_forecast.append(month_cost)
        
        # Calculate confidence interval (simple approach)
        std_dev = statistics.stdev(costs_list) if len(costs_list) > 1 else 0
        confidence_interval = (
            max(0, recent_avg - 2 * std_dev),
            recent_avg + 2 * std_dev
        )
        
        forecast = CostForecast(
            daily_forecast=daily_forecast,
            weekly_forecast=weekly_forecast,
            monthly_forecast=monthly_forecast,
            trend_direction=trend_direction,
            confidence_interval=confidence_interval,
            forecast_accuracy=0.8  # Placeholder accuracy score
        )
        
        self.cost_forecast = forecast
        return forecast
    
    async def check_budget_alerts(self) -> List[Dict[str, Any]]:
        """Check for budget threshold breaches and generate alerts."""
        alerts = []
        
        # Check daily budget
        daily_usage_pct = self.cost_metrics.daily_spend / self.budget.daily_limit
        if daily_usage_pct >= self.budget.alert_thresholds["emergency"]:
            alerts.append({
                "level": CostAlert.EMERGENCY,
                "type": "daily_budget",
                "message": f"Daily budget 95% exceeded: ${self.cost_metrics.daily_spend:.2f} / ${self.budget.daily_limit:.2f}",
                "usage_percentage": daily_usage_pct * 100,
                "timestamp": datetime.utcnow()
            })
        elif daily_usage_pct >= self.budget.alert_thresholds["critical"]:
            alerts.append({
                "level": CostAlert.CRITICAL,
                "type": "daily_budget",
                "message": f"Daily budget 90% exceeded: ${self.cost_metrics.daily_spend:.2f} / ${self.budget.daily_limit:.2f}",
                "usage_percentage": daily_usage_pct * 100,
                "timestamp": datetime.utcnow()
            })
        elif daily_usage_pct >= self.budget.alert_thresholds["warning"]:
            alerts.append({
                "level": CostAlert.WARNING,
                "type": "daily_budget",
                "message": f"Daily budget 80% reached: ${self.cost_metrics.daily_spend:.2f} / ${self.budget.daily_limit:.2f}",
                "usage_percentage": daily_usage_pct * 100,
                "timestamp": datetime.utcnow()
            })
        
        # Check weekly budget
        weekly_usage_pct = self.cost_metrics.weekly_spend / self.budget.weekly_limit
        if weekly_usage_pct >= self.budget.alert_thresholds["critical"]:
            alerts.append({
                "level": CostAlert.CRITICAL,
                "type": "weekly_budget",
                "message": f"Weekly budget 90% exceeded: ${self.cost_metrics.weekly_spend:.2f} / ${self.budget.weekly_limit:.2f}",
                "usage_percentage": weekly_usage_pct * 100,
                "timestamp": datetime.utcnow()
            })
        
        # Check for unusual spending patterns
        if self.cost_metrics.current_hourly_rate > self.cost_metrics.average_cost_per_request * 100:
            alerts.append({
                "level": CostAlert.WARNING,
                "type": "spending_spike",
                "message": f"Unusual spending spike detected: ${self.cost_metrics.current_hourly_rate:.2f}/hour",
                "timestamp": datetime.utcnow()
            })
        
        # Update active alerts
        self.active_alerts = alerts
        
        # Add to alert history
        for alert in alerts:
            self.alert_history.append(alert)
        
        return alerts
    
    async def get_cost_report(self) -> Dict[str, Any]:
        """Generate comprehensive cost report."""
        # Generate latest optimizations and forecasts
        optimizations = await self.generate_optimizations()
        forecast = await self.generate_cost_forecast()
        usage_analysis = await self.analyze_usage_patterns()
        alerts = await self.check_budget_alerts()
        
        return {
            "cost_metrics": self.cost_metrics,
            "budget_status": {
                "daily_usage": self.cost_metrics.daily_spend / self.budget.daily_limit,
                "weekly_usage": self.cost_metrics.weekly_spend / self.budget.weekly_limit,
                "remaining_daily": max(0, self.budget.daily_limit - self.cost_metrics.daily_spend),
                "remaining_weekly": max(0, self.budget.weekly_limit - self.cost_metrics.weekly_spend)
            },
            "usage_analysis": usage_analysis,
            "optimizations": [
                {
                    "type": opt.optimization_type.value,
                    "current_model": opt.current_model,
                    "recommended_model": opt.recommended_model,
                    "task_type": opt.task_type,
                    "potential_savings": opt.potential_savings,
                    "confidence_score": opt.confidence_score,
                    "impact_assessment": opt.impact_assessment,
                    "auto_applicable": opt.auto_applicable
                }
                for opt in optimizations[:10]  # Top 10 optimizations
            ],
            "cost_forecast": {
                "trend_direction": forecast.trend_direction,
                "next_7_days": sum(forecast.daily_forecast[:7]) if forecast.daily_forecast else 0,
                "next_30_days": sum(forecast.daily_forecast[:30]) if forecast.daily_forecast else 0,
                "confidence_interval": forecast.confidence_interval
            },
            "alerts": alerts,
            "applied_optimizations_count": len(self.applied_optimizations),
            "total_optimization_savings": self.optimization_savings
        }
    
    async def set_budget(self, daily_limit: float, weekly_limit: float, monthly_limit: float) -> None:
        """Set cost budget limits."""
        self.budget = CostBudget(
            daily_limit=daily_limit,
            weekly_limit=weekly_limit,
            monthly_limit=monthly_limit
        )
        self.logger.info(f"Budget updated: daily=${daily_limit}, weekly=${weekly_limit}, monthly=${monthly_limit}")
    
    async def _cost_tracking_loop(self) -> None:
        """Background cost tracking loop."""
        while True:
            try:
                await asyncio.sleep(60)  # Update every minute
                await self._update_real_time_metrics()
                
            except Exception as e:
                self.logger.error(f"Cost tracking loop error: {e}")
    
    async def _pattern_analysis_loop(self) -> None:
        """Background pattern analysis loop."""
        while True:
            try:
                await asyncio.sleep(3600)  # Analyze every hour
                await self.analyze_usage_patterns()
                
            except Exception as e:
                self.logger.error(f"Pattern analysis loop error: {e}")
    
    async def _optimization_loop(self) -> None:
        """Background optimization loop."""
        while True:
            try:
                await asyncio.sleep(1800)  # Generate optimizations every 30 minutes
                
                if self.optimization_enabled:
                    optimizations = await self.generate_optimizations()
                    
                    # Auto-apply eligible optimizations
                    if self.auto_optimization_enabled:
                        for opt in optimizations:
                            if opt.auto_applicable and opt.confidence_score > 0.8:
                                result = await self.apply_optimization(opt)
                                if result["success"]:
                                    self.optimization_savings += opt.potential_savings
                
            except Exception as e:
                self.logger.error(f"Optimization loop error: {e}")
    
    async def _forecasting_loop(self) -> None:
        """Background forecasting loop."""
        while True:
            try:
                await asyncio.sleep(21600)  # Update forecast every 6 hours
                await self.generate_cost_forecast(self.forecast_horizon_days)
                
            except Exception as e:
                self.logger.error(f"Forecasting loop error: {e}")
    
    async def _alert_monitoring_loop(self) -> None:
        """Background alert monitoring loop."""
        while True:
            try:
                await asyncio.sleep(300)  # Check alerts every 5 minutes
                await self.check_budget_alerts()
                
            except Exception as e:
                self.logger.error(f"Alert monitoring loop error: {e}")
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        try:
            self.logger.info("Model cost optimizer cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")


# Global cost optimizer instance
_cost_optimizer: Optional[ModelCostOptimizer] = None


async def get_cost_optimizer() -> ModelCostOptimizer:
    """Get global cost optimizer instance."""
    global _cost_optimizer
    
    if _cost_optimizer is None:
        _cost_optimizer = ModelCostOptimizer()
        await _cost_optimizer.initialize()
    
    return _cost_optimizer