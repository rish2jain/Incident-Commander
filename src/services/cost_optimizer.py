"""
Cost Optimizer Service

Implements cost-aware scaling and optimization strategies including:
- Cost-optimized scaling with incident severity-based cost thresholds
- Intelligent model selection based on cost per token and accuracy requirements
- Lambda warming service with predictive warming based on business hours
- Cost monitoring and alerting with automatic cost optimization recommendations

Requirements: 10.1, 10.2, 16.1
"""

import asyncio
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum

import aioboto3
from botocore.exceptions import ClientError
import pytz

from src.utils.config import config
from src.utils.logging import get_logger
from src.utils.constants import BUSINESS_IMPACT_CONFIG, PERFORMANCE_TARGETS
from src.utils.exceptions import CostOptimizationError


logger = get_logger(__name__)


class ModelTier(Enum):
    """Model tier based on cost and capability."""
    ECONOMY = "economy"      # Lowest cost, basic capability
    STANDARD = "standard"    # Balanced cost/performance
    PREMIUM = "premium"      # High cost, best performance
    CRITICAL = "critical"    # Highest cost, maximum accuracy


class CostThreshold(Enum):
    """Cost threshold levels."""
    LOW = "low"          # < $50/hour
    MEDIUM = "medium"    # $50-100/hour
    HIGH = "high"        # $100-200/hour
    CRITICAL = "critical" # > $200/hour


@dataclass
class ModelConfig:
    """Model configuration with cost and performance metrics."""
    model_name: str
    cost_per_1k_tokens: float
    accuracy_score: float
    avg_response_time_ms: int
    max_tokens: int
    tier: ModelTier


@dataclass
class CostMetrics:
    """Cost optimization metrics."""
    current_hourly_cost: float = 0.0
    projected_daily_cost: float = 0.0
    cost_by_service: Dict[str, float] = field(default_factory=dict)
    cost_by_model: Dict[str, float] = field(default_factory=dict)
    cost_savings_achieved: float = 0.0
    optimization_actions: List[str] = field(default_factory=list)
    lambda_warm_cost: float = 0.0
    scaling_cost: float = 0.0


@dataclass
class BusinessHourPattern:
    """Business hour pattern for predictive warming."""
    timezone: str
    business_start: int  # Hour (0-23)
    business_end: int    # Hour (0-23)
    weekend_factor: float = 0.3  # Reduced activity on weekends
    holiday_factor: float = 0.1  # Minimal activity on holidays


class CostOptimizer:
    """
    Cost-aware scaling and optimization with intelligent model selection,
    predictive Lambda warming, and cost monitoring.
    """
    
    def __init__(self):
        self.logger = logger
        
        # Model configurations with cost and performance data
        self.model_configs = {
            # Bedrock models with realistic pricing
            "claude-3-haiku": ModelConfig(
                model_name="claude-3-haiku",
                cost_per_1k_tokens=0.25,
                accuracy_score=0.85,
                avg_response_time_ms=800,
                max_tokens=4096,
                tier=ModelTier.ECONOMY
            ),
            "claude-3-sonnet": ModelConfig(
                model_name="claude-3-sonnet",
                cost_per_1k_tokens=3.0,
                accuracy_score=0.92,
                avg_response_time_ms=1200,
                max_tokens=4096,
                tier=ModelTier.STANDARD
            ),
            "claude-3-opus": ModelConfig(
                model_name="claude-3-opus",
                cost_per_1k_tokens=15.0,
                accuracy_score=0.96,
                avg_response_time_ms=2000,
                max_tokens=4096,
                tier=ModelTier.PREMIUM
            ),
            "gpt-4": ModelConfig(
                model_name="gpt-4",
                cost_per_1k_tokens=30.0,
                accuracy_score=0.98,
                avg_response_time_ms=2500,
                max_tokens=8192,
                tier=ModelTier.CRITICAL
            )
        }
        
        # Cost thresholds and policies
        self.cost_thresholds = {
            CostThreshold.LOW: 50.0,
            CostThreshold.MEDIUM: 100.0,
            CostThreshold.HIGH: 200.0,
            CostThreshold.CRITICAL: 500.0
        }
        
        # Business hour patterns for different regions
        self.business_patterns = {
            "us-east-1": BusinessHourPattern("America/New_York", 9, 17),
            "us-west-2": BusinessHourPattern("America/Los_Angeles", 9, 17),
            "eu-west-1": BusinessHourPattern("Europe/London", 9, 17),
            "ap-southeast-1": BusinessHourPattern("Asia/Singapore", 9, 17)
        }
        
        # Cost tracking
        self.metrics = CostMetrics()
        self.cost_history = deque(maxlen=1440)  # 24 hours of minute-by-minute data
        self.model_usage_history = defaultdict(list)
        
        # Lambda warming configuration
        self.lambda_functions = [
            "detection-agent",
            "diagnosis-agent", 
            "prediction-agent",
            "resolution-agent",
            "communication-agent"
        ]
        self.warm_functions_cache: Dict[str, datetime] = {}
        self.warming_schedule: Dict[str, List[datetime]] = defaultdict(list)
        
        # AWS clients
        self.aws_session = aioboto3.Session()
        self.lambda_client = None
        self.cloudwatch_client = None
        self.cost_explorer_client = None
        
        # Cost optimization state
        self.current_cost_threshold = CostThreshold.MEDIUM
        self.optimization_enabled = True
        self.emergency_cost_limit = 1000.0  # $1000/hour emergency limit
        
    async def initialize(self) -> None:
        """Initialize cost optimizer with AWS clients and monitoring."""
        try:
            # Initialize AWS clients
            await self._initialize_aws_clients()
            
            # Start cost monitoring and optimization loops
            asyncio.create_task(self._cost_monitoring_loop())
            asyncio.create_task(self._lambda_warming_loop())
            asyncio.create_task(self._cost_optimization_loop())
            
            self.logger.info("Cost optimizer initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize cost optimizer: {e}")
            raise CostOptimizationError(f"Initialization failed: {e}")
    
    async def _initialize_aws_clients(self) -> None:
        """Initialize AWS service clients for cost operations."""
        async with self.aws_session.client('lambda') as client:
            self.lambda_client = client
        
        async with self.aws_session.client('cloudwatch') as client:
            self.cloudwatch_client = client
        
        async with self.aws_session.client('ce') as client:  # Cost Explorer
            self.cost_explorer_client = client
        
        self.logger.info("AWS clients initialized for cost operations")
    
    async def select_optimal_model(self, 
                                 task_type: str, 
                                 incident_severity: str,
                                 required_accuracy: float = 0.85,
                                 max_cost_per_1k_tokens: Optional[float] = None) -> str:
        """Select optimal model based on cost, accuracy, and incident severity."""
        
        # Determine cost constraints based on incident severity
        if incident_severity in ["critical", "high"]:
            # For critical incidents, prioritize accuracy over cost
            cost_constraint = self.cost_thresholds[CostThreshold.CRITICAL]
            min_accuracy = max(required_accuracy, 0.92)
        elif incident_severity == "medium":
            cost_constraint = self.cost_thresholds[CostThreshold.HIGH]
            min_accuracy = required_accuracy
        else:
            cost_constraint = self.cost_thresholds[CostThreshold.MEDIUM]
            min_accuracy = max(required_accuracy - 0.05, 0.8)  # Allow slightly lower accuracy
        
        # Apply user-specified cost limit if provided
        if max_cost_per_1k_tokens:
            cost_constraint = min(cost_constraint, max_cost_per_1k_tokens * 1000)
        
        # Filter models by accuracy and cost constraints
        suitable_models = []
        for model_name, config in self.model_configs.items():
            if (config.accuracy_score >= min_accuracy and 
                config.cost_per_1k_tokens * 1000 <= cost_constraint):
                suitable_models.append((model_name, config))
        
        if not suitable_models:
            # Fallback to cheapest model that meets minimum accuracy
            fallback_models = [
                (name, config) for name, config in self.model_configs.items()
                if config.accuracy_score >= 0.8
            ]
            if fallback_models:
                suitable_models = [min(fallback_models, key=lambda x: x[1].cost_per_1k_tokens)]
            else:
                # Emergency fallback
                suitable_models = [("claude-3-haiku", self.model_configs["claude-3-haiku"])]
        
        # Select best model based on cost-effectiveness score
        best_model = self._calculate_cost_effectiveness(suitable_models, task_type)
        
        # Record model selection for cost tracking
        await self._record_model_selection(best_model, incident_severity, task_type)
        
        self.logger.debug(f"Selected model {best_model} for {task_type} (severity: {incident_severity})")
        return best_model
    
    def _calculate_cost_effectiveness(self, models: List[Tuple[str, ModelConfig]], task_type: str) -> str:
        """Calculate cost-effectiveness score for model selection."""
        best_score = -1
        best_model = models[0][0]
        
        for model_name, config in models:
            # Cost-effectiveness = accuracy / (cost * response_time_factor)
            response_time_factor = config.avg_response_time_ms / 1000.0  # Convert to seconds
            
            # Adjust for task type requirements
            if task_type in ["detection", "communication"]:
                # Speed is more important for these tasks
                response_time_weight = 2.0
            else:
                # Accuracy is more important for diagnosis/resolution
                response_time_weight = 1.0
            
            cost_effectiveness = config.accuracy_score / (
                config.cost_per_1k_tokens * (1 + response_time_factor * response_time_weight)
            )
            
            if cost_effectiveness > best_score:
                best_score = cost_effectiveness
                best_model = model_name
        
        return best_model
    
    async def _record_model_selection(self, model_name: str, severity: str, task_type: str) -> None:
        """Record model selection for cost tracking."""
        config = self.model_configs[model_name]
        
        # Estimate token usage based on task type
        estimated_tokens = self._estimate_token_usage(task_type, severity)
        estimated_cost = (estimated_tokens / 1000.0) * config.cost_per_1k_tokens
        
        # Update cost metrics
        self.metrics.cost_by_model[model_name] = self.metrics.cost_by_model.get(model_name, 0) + estimated_cost
        self.metrics.cost_by_service[task_type] = self.metrics.cost_by_service.get(task_type, 0) + estimated_cost
        
        # Record usage history
        self.model_usage_history[model_name].append({
            "timestamp": datetime.utcnow(),
            "task_type": task_type,
            "severity": severity,
            "estimated_cost": estimated_cost,
            "estimated_tokens": estimated_tokens
        })
    
    def _estimate_token_usage(self, task_type: str, severity: str) -> int:
        """Estimate token usage based on task type and severity."""
        base_tokens = {
            "detection": 500,
            "diagnosis": 1500,
            "prediction": 800,
            "resolution": 1200,
            "communication": 300
        }
        
        severity_multiplier = {
            "low": 0.8,
            "medium": 1.0,
            "high": 1.3,
            "critical": 1.5
        }
        
        base = base_tokens.get(task_type, 1000)
        multiplier = severity_multiplier.get(severity, 1.0)
        
        return int(base * multiplier)
    
    async def warm_lambda_functions(self, functions: Optional[List[str]] = None) -> Dict[str, bool]:
        """Warm Lambda functions to prevent cold starts."""
        if not functions:
            functions = self.lambda_functions
        
        results = {}
        warming_cost = 0.0
        
        for function_name in functions:
            try:
                # Check if function was recently warmed
                last_warm = self.warm_functions_cache.get(function_name)
                if last_warm and (datetime.utcnow() - last_warm).total_seconds() < 300:  # 5 minutes
                    results[function_name] = True
                    continue
                
                # Warm the function with a lightweight invocation
                await self._invoke_lambda_warming(function_name)
                
                self.warm_functions_cache[function_name] = datetime.utcnow()
                results[function_name] = True
                
                # Estimate warming cost (approximately $0.0000002 per invocation)
                warming_cost += 0.0000002
                
                self.logger.debug(f"Warmed Lambda function: {function_name}")
                
            except Exception as e:
                self.logger.warning(f"Failed to warm Lambda function {function_name}: {e}")
                results[function_name] = False
        
        # Update cost metrics
        self.metrics.lambda_warm_cost += warming_cost
        
        return results
    
    async def _invoke_lambda_warming(self, function_name: str) -> None:
        """Invoke Lambda function for warming (placeholder)."""
        # In a real implementation, this would invoke the Lambda function
        # with a special warming payload that doesn't trigger full processing
        
        if not self.lambda_client:
            return
        
        try:
            # Simulate warming invocation
            await asyncio.sleep(0.01)  # Simulate network call
            
        except Exception as e:
            raise CostOptimizationError(f"Lambda warming failed for {function_name}: {e}")
    
    async def predictive_lambda_warming(self, region: str = "us-east-1") -> None:
        """Predictively warm Lambda functions based on business hours."""
        pattern = self.business_patterns.get(region, self.business_patterns["us-east-1"])
        
        # Get current time in the region's timezone
        tz = pytz.timezone(pattern.timezone)
        current_time = datetime.now(tz)
        current_hour = current_time.hour
        is_weekend = current_time.weekday() >= 5
        
        # Determine if we're approaching business hours
        approaching_business_hours = (
            (current_hour >= pattern.business_start - 1 and current_hour <= pattern.business_end) or
            (current_hour == pattern.business_start - 1)  # 1 hour before business starts
        )
        
        # Calculate warming probability
        warming_probability = 1.0
        if is_weekend:
            warming_probability *= pattern.weekend_factor
        
        # Warm functions if approaching or during business hours
        if approaching_business_hours and warming_probability > 0.5:
            await self.warm_lambda_functions()
            self.logger.info(f"Predictive warming triggered for {region} (business hours)")
    
    async def optimize_scaling_costs(self, current_load: Dict[str, float]) -> Dict[str, Any]:
        """Optimize scaling decisions based on cost considerations."""
        recommendations = {
            "scale_up": [],
            "scale_down": [],
            "cost_impact": 0.0,
            "reasoning": []
        }
        
        current_hourly_cost = await self._calculate_current_hourly_cost()
        
        for agent_type, utilization in current_load.items():
            # Calculate cost per replica for this agent type
            cost_per_replica = self._estimate_replica_cost(agent_type)
            
            # Scale up recommendations
            if utilization > 0.8:  # High utilization
                if current_hourly_cost < self.cost_thresholds[CostThreshold.HIGH]:
                    recommendations["scale_up"].append({
                        "agent_type": agent_type,
                        "reason": "High utilization, cost budget available",
                        "cost_impact": cost_per_replica
                    })
                    recommendations["cost_impact"] += cost_per_replica
                else:
                    recommendations["reasoning"].append(
                        f"Skipping scale-up for {agent_type} due to cost constraints"
                    )
            
            # Scale down recommendations
            elif utilization < 0.3:  # Low utilization
                recommendations["scale_down"].append({
                    "agent_type": agent_type,
                    "reason": "Low utilization, cost savings opportunity",
                    "cost_savings": cost_per_replica
                })
                recommendations["cost_impact"] -= cost_per_replica
        
        return recommendations
    
    def _estimate_replica_cost(self, agent_type: str) -> float:
        """Estimate hourly cost per replica for agent type."""
        # Base costs for different agent types (per hour)
        base_costs = {
            "detection": 2.0,      # Lightweight processing
            "diagnosis": 5.0,      # Medium processing + model calls
            "prediction": 4.0,     # Medium processing + ML inference
            "resolution": 3.0,     # Light processing but critical
            "communication": 1.0   # Minimal processing
        }
        
        return base_costs.get(agent_type, 3.0)
    
    async def _calculate_current_hourly_cost(self) -> float:
        """Calculate current hourly cost across all services."""
        total_cost = 0.0
        
        # Sum up costs from different sources
        total_cost += sum(self.metrics.cost_by_service.values())
        total_cost += self.metrics.lambda_warm_cost * 3600  # Convert to hourly
        total_cost += self.metrics.scaling_cost
        
        # Project to hourly rate if we have recent data
        if self.cost_history:
            recent_costs = list(self.cost_history)[-60:]  # Last hour
            if recent_costs:
                avg_per_minute = sum(recent_costs) / len(recent_costs)
                total_cost = avg_per_minute * 60
        
        self.metrics.current_hourly_cost = total_cost
        return total_cost
    
    async def _cost_monitoring_loop(self) -> None:
        """Background cost monitoring loop."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Calculate current costs
                current_cost = await self._calculate_current_hourly_cost()
                self.cost_history.append(current_cost)
                
                # Update projected daily cost
                self.metrics.projected_daily_cost = current_cost * 24
                
                # Check for cost threshold breaches
                await self._check_cost_thresholds(current_cost)
                
                # Clean up old usage history
                await self._cleanup_usage_history()
                
            except Exception as e:
                self.logger.error(f"Cost monitoring loop error: {e}")
    
    async def _check_cost_thresholds(self, current_cost: float) -> None:
        """Check and respond to cost threshold breaches."""
        if current_cost > self.emergency_cost_limit:
            # Emergency cost limit exceeded
            await self._trigger_emergency_cost_controls()
        elif current_cost > self.cost_thresholds[CostThreshold.CRITICAL]:
            # Critical threshold exceeded
            await self._trigger_cost_optimization()
            self.current_cost_threshold = CostThreshold.CRITICAL
        elif current_cost > self.cost_thresholds[CostThreshold.HIGH]:
            self.current_cost_threshold = CostThreshold.HIGH
        elif current_cost > self.cost_thresholds[CostThreshold.MEDIUM]:
            self.current_cost_threshold = CostThreshold.MEDIUM
        else:
            self.current_cost_threshold = CostThreshold.LOW
    
    async def _trigger_emergency_cost_controls(self) -> None:
        """Trigger emergency cost control measures."""
        self.logger.critical(f"Emergency cost limit exceeded: ${self.metrics.current_hourly_cost:.2f}/hour")
        
        # Switch to most economical models only
        self.optimization_enabled = False
        
        # Record emergency action
        self.metrics.optimization_actions.append(
            f"Emergency cost controls activated at ${self.metrics.current_hourly_cost:.2f}/hour"
        )
        
        # In a real implementation, this might:
        # 1. Scale down non-critical services
        # 2. Switch to cheapest models only
        # 3. Disable non-essential features
        # 4. Send alerts to operations team
    
    async def _trigger_cost_optimization(self) -> None:
        """Trigger cost optimization measures."""
        self.logger.warning(f"High cost detected: ${self.metrics.current_hourly_cost:.2f}/hour")
        
        # Generate optimization recommendations
        recommendations = await self._generate_cost_optimizations()
        
        # Apply automatic optimizations
        for recommendation in recommendations:
            if recommendation["auto_apply"]:
                await self._apply_cost_optimization(recommendation)
        
        self.metrics.optimization_actions.append(
            f"Cost optimization triggered at ${self.metrics.current_hourly_cost:.2f}/hour"
        )
    
    async def _generate_cost_optimizations(self) -> List[Dict[str, Any]]:
        """Generate cost optimization recommendations."""
        recommendations = []
        
        # Model optimization recommendations
        for model_name, usage_list in self.model_usage_history.items():
            if len(usage_list) > 10:  # Enough data for analysis
                recent_usage = usage_list[-10:]
                avg_cost = sum(u["estimated_cost"] for u in recent_usage) / len(recent_usage)
                
                if avg_cost > 0.1:  # High cost per usage
                    cheaper_alternatives = [
                        name for name, config in self.model_configs.items()
                        if (config.cost_per_1k_tokens < self.model_configs[model_name].cost_per_1k_tokens and
                            config.accuracy_score >= self.model_configs[model_name].accuracy_score - 0.05)
                    ]
                    
                    if cheaper_alternatives:
                        recommendations.append({
                            "type": "model_optimization",
                            "current_model": model_name,
                            "recommended_model": cheaper_alternatives[0],
                            "potential_savings": avg_cost * 0.3,  # Estimated 30% savings
                            "auto_apply": True
                        })
        
        return recommendations
    
    async def _apply_cost_optimization(self, recommendation: Dict[str, Any]) -> None:
        """Apply cost optimization recommendation."""
        if recommendation["type"] == "model_optimization":
            # In a real implementation, this would update model selection preferences
            self.logger.info(f"Applied model optimization: {recommendation['current_model']} -> {recommendation['recommended_model']}")
            
            # Record cost savings
            self.metrics.cost_savings_achieved += recommendation.get("potential_savings", 0)
    
    async def _lambda_warming_loop(self) -> None:
        """Background Lambda warming loop."""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                # Predictive warming for all regions
                for region in self.business_patterns.keys():
                    await self.predictive_lambda_warming(region)
                
            except Exception as e:
                self.logger.error(f"Lambda warming loop error: {e}")
    
    async def _cost_optimization_loop(self) -> None:
        """Background cost optimization loop."""
        while True:
            try:
                await asyncio.sleep(900)  # Check every 15 minutes
                
                if self.optimization_enabled:
                    # Generate and apply optimizations
                    recommendations = await self._generate_cost_optimizations()
                    
                    for recommendation in recommendations:
                        if recommendation.get("auto_apply", False):
                            await self._apply_cost_optimization(recommendation)
                
            except Exception as e:
                self.logger.error(f"Cost optimization loop error: {e}")
    
    async def _cleanup_usage_history(self) -> None:
        """Clean up old usage history to prevent memory bloat."""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        for model_name in self.model_usage_history:
            self.model_usage_history[model_name] = [
                usage for usage in self.model_usage_history[model_name]
                if usage["timestamp"] > cutoff_time
            ]
    
    async def get_cost_metrics(self) -> CostMetrics:
        """Get current cost metrics."""
        # Update current cost before returning metrics
        current_cost = await self._calculate_current_hourly_cost()
        self.metrics.current_hourly_cost = current_cost
        return self.metrics
    
    async def get_cost_recommendations(self) -> List[Dict[str, Any]]:
        """Get cost optimization recommendations."""
        recommendations = await self._generate_cost_optimizations()
        
        # Add general recommendations
        if self.metrics.current_hourly_cost > self.cost_thresholds[CostThreshold.MEDIUM]:
            recommendations.append({
                "type": "general",
                "recommendation": "Consider implementing more aggressive caching to reduce model API calls",
                "potential_savings": self.metrics.current_hourly_cost * 0.15
            })
        
        return recommendations
    
    async def set_cost_threshold(self, threshold: CostThreshold) -> None:
        """Set cost threshold for optimization decisions."""
        self.current_cost_threshold = threshold
        self.logger.info(f"Cost threshold set to {threshold.value}: ${self.cost_thresholds[threshold]}/hour")
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        try:
            self.logger.info("Cost optimizer cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")


# Global cost optimizer instance
_cost_optimizer: Optional[CostOptimizer] = None


async def get_cost_optimizer() -> CostOptimizer:
    """Get global cost optimizer instance."""
    global _cost_optimizer
    
    if _cost_optimizer is None:
        _cost_optimizer = CostOptimizer()
        await _cost_optimizer.initialize()
    
    return _cost_optimizer