"""
FinOps Controller for Cost Management and Optimization

Implements workload-aware spending caps, adaptive model routing,
and dynamic resource allocation for cost-effective operations.
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from decimal import Decimal

import boto3
from botocore.exceptions import ClientError

from src.utils.logging import get_logger
from src.utils.config import config
from src.utils.exceptions import BudgetExceededError, CostOptimizationError


logger = get_logger("finops_controller")


class ServiceTier(Enum):
    """Service tiers for cost optimization."""
    PREMIUM = "premium"
    STANDARD = "standard"
    ECONOMY = "economy"
    EMERGENCY = "emergency"


class ModelComplexity(Enum):
    """Model complexity levels for routing decisions."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    CRITICAL = "critical"


class CostCategory(Enum):
    """Cost categories for tracking."""
    BEDROCK_INFERENCE = "bedrock_inference"
    BEDROCK_EMBEDDINGS = "bedrock_embeddings"
    NOVA_ACTIONS = "nova_actions"
    AMAZON_Q = "amazon_q"
    STRANDS_SDK = "strands_sdk"
    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORKING = "networking"


@dataclass
class BudgetLimit:
    """Budget limit configuration."""
    category: CostCategory
    daily_limit_usd: Decimal
    hourly_limit_usd: Decimal
    monthly_limit_usd: Decimal
    alert_threshold_percent: int = 80
    hard_limit_enabled: bool = True


@dataclass
class CostMetrics:
    """Cost tracking metrics."""
    category: CostCategory
    current_hour_spend: Decimal = Decimal('0')
    current_day_spend: Decimal = Decimal('0')
    current_month_spend: Decimal = Decimal('0')
    request_count: int = 0
    average_cost_per_request: Decimal = Decimal('0')
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ModelRoutingRule:
    """Model routing rule for cost optimization."""
    complexity_threshold: ModelComplexity
    preferred_model: str
    fallback_model: str
    cost_per_1k_tokens: Decimal
    performance_score: float
    conditions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkloadProfile:
    """Workload profile for adaptive scaling."""
    incident_severity: str
    expected_duration_minutes: int
    agent_count: int
    model_usage_pattern: Dict[str, int]
    estimated_cost_usd: Decimal
    priority_level: int


class FinOpsController:
    """
    Comprehensive FinOps controller for cost management and optimization.
    
    Provides workload-aware spending caps, adaptive model routing,
    dynamic resource allocation, and cost optimization strategies.
    """
    
    def __init__(self):
        """Initialize FinOps controller."""
        self.cost_explorer = boto3.client('ce', region_name=config.aws_region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=config.aws_region)
        self.pricing = boto3.client('pricing', region_name='us-east-1')  # Pricing API only in us-east-1
        
        # Budget configuration
        self.budget_limits = self._initialize_budget_limits()
        self.cost_metrics: Dict[CostCategory, CostMetrics] = {}
        
        # Model routing configuration
        self.model_routing_rules = self._initialize_model_routing()
        self.current_service_tier = ServiceTier.STANDARD
        
        # Workload tracking
        self.active_workloads: Dict[str, WorkloadProfile] = {}
        self.cost_history: List[Dict[str, Any]] = []
        
        # Optimization settings
        self.auto_optimization_enabled = True
        self.emergency_throttling_enabled = True
        self.cost_alerts_enabled = True
        
        # Performance metrics
        self.total_cost_saved = Decimal('0')
        self.optimization_decisions = 0
        self.budget_violations = 0
        
        logger.info("FinOps Controller initialized")
    
    def _initialize_budget_limits(self) -> Dict[CostCategory, BudgetLimit]:
        """Initialize budget limits for different cost categories."""
        return {
            CostCategory.BEDROCK_INFERENCE: BudgetLimit(
                category=CostCategory.BEDROCK_INFERENCE,
                daily_limit_usd=Decimal('1000'),
                hourly_limit_usd=Decimal('100'),
                monthly_limit_usd=Decimal('25000'),
                alert_threshold_percent=80
            ),
            CostCategory.BEDROCK_EMBEDDINGS: BudgetLimit(
                category=CostCategory.BEDROCK_EMBEDDINGS,
                daily_limit_usd=Decimal('200'),
                hourly_limit_usd=Decimal('25'),
                monthly_limit_usd=Decimal('5000'),
                alert_threshold_percent=75
            ),
            CostCategory.NOVA_ACTIONS: BudgetLimit(
                category=CostCategory.NOVA_ACTIONS,
                daily_limit_usd=Decimal('500'),
                hourly_limit_usd=Decimal('50'),
                monthly_limit_usd=Decimal('12000'),
                alert_threshold_percent=85
            ),
            CostCategory.AMAZON_Q: BudgetLimit(
                category=CostCategory.AMAZON_Q,
                daily_limit_usd=Decimal('300'),
                hourly_limit_usd=Decimal('30'),
                monthly_limit_usd=Decimal('7500'),
                alert_threshold_percent=80
            ),
            CostCategory.STRANDS_SDK: BudgetLimit(
                category=CostCategory.STRANDS_SDK,
                daily_limit_usd=Decimal('150'),
                hourly_limit_usd=Decimal('20'),
                monthly_limit_usd=Decimal('4000'),
                alert_threshold_percent=80
            ),
            CostCategory.COMPUTE: BudgetLimit(
                category=CostCategory.COMPUTE,
                daily_limit_usd=Decimal('400'),
                hourly_limit_usd=Decimal('40'),
                monthly_limit_usd=Decimal('10000'),
                alert_threshold_percent=70
            )
        }
    
    def _initialize_model_routing(self) -> Dict[str, ModelRoutingRule]:
        """Initialize model routing rules for cost optimization."""
        return {
            "simple_tasks": ModelRoutingRule(
                complexity_threshold=ModelComplexity.SIMPLE,
                preferred_model="anthropic.claude-3-haiku-20240307-v1:0",
                fallback_model="anthropic.claude-3-haiku-20240307-v1:0",
                cost_per_1k_tokens=Decimal('0.25'),
                performance_score=0.8,
                conditions={
                    "max_tokens": 1000,
                    "response_time_priority": "high",
                    "cost_priority": "high"
                }
            ),
            "moderate_tasks": ModelRoutingRule(
                complexity_threshold=ModelComplexity.MODERATE,
                preferred_model="anthropic.claude-3-haiku-20240307-v1:0",
                fallback_model="anthropic.claude-3-5-sonnet-20241022-v2:0",
                cost_per_1k_tokens=Decimal('1.25'),
                performance_score=0.9,
                conditions={
                    "max_tokens": 4000,
                    "accuracy_priority": "medium",
                    "cost_priority": "medium"
                }
            ),
            "complex_tasks": ModelRoutingRule(
                complexity_threshold=ModelComplexity.COMPLEX,
                preferred_model="anthropic.claude-3-5-sonnet-20241022-v2:0",
                fallback_model="anthropic.claude-3-5-sonnet-20241022-v2:0",
                cost_per_1k_tokens=Decimal('3.00'),
                performance_score=0.95,
                conditions={
                    "max_tokens": 8000,
                    "accuracy_priority": "high",
                    "reasoning_required": True
                }
            ),
            "critical_tasks": ModelRoutingRule(
                complexity_threshold=ModelComplexity.CRITICAL,
                preferred_model="anthropic.claude-3-5-sonnet-20241022-v2:0",
                fallback_model="anthropic.claude-3-5-sonnet-20241022-v2:0",
                cost_per_1k_tokens=Decimal('3.00'),
                performance_score=0.98,
                conditions={
                    "max_tokens": 16000,
                    "accuracy_priority": "critical",
                    "no_cost_optimization": True
                }
            )
        }
    
    async def check_budget_limits(self, category: CostCategory, estimated_cost: Decimal) -> bool:
        """
        Check if operation would exceed budget limits.
        
        Args:
            category: Cost category
            estimated_cost: Estimated cost of operation
            
        Returns:
            True if within budget, False if would exceed limits
        """
        if category not in self.budget_limits:
            logger.warning(f"No budget limit configured for category: {category}")
            return True
        
        budget_limit = self.budget_limits[category]
        current_metrics = await self._get_current_cost_metrics(category)
        
        # Check hourly limit
        projected_hourly = current_metrics.current_hour_spend + estimated_cost
        if budget_limit.hard_limit_enabled and projected_hourly > budget_limit.hourly_limit_usd:
            logger.warning(f"Operation would exceed hourly budget for {category}: {projected_hourly} > {budget_limit.hourly_limit_usd}")
            self.budget_violations += 1
            return False
        
        # Check daily limit
        projected_daily = current_metrics.current_day_spend + estimated_cost
        if budget_limit.hard_limit_enabled and projected_daily > budget_limit.daily_limit_usd:
            logger.warning(f"Operation would exceed daily budget for {category}: {projected_daily} > {budget_limit.daily_limit_usd}")
            self.budget_violations += 1
            return False
        
        # Check alert thresholds
        hourly_usage_percent = (projected_hourly / budget_limit.hourly_limit_usd) * 100
        daily_usage_percent = (projected_daily / budget_limit.daily_limit_usd) * 100
        
        if hourly_usage_percent > budget_limit.alert_threshold_percent:
            await self._send_budget_alert(category, "hourly", hourly_usage_percent)
        
        if daily_usage_percent > budget_limit.alert_threshold_percent:
            await self._send_budget_alert(category, "daily", daily_usage_percent)
        
        return True
    
    async def adaptive_model_routing(self, task_complexity: str, context: Dict[str, Any]) -> str:
        """
        Route to appropriate model based on complexity and cost constraints.
        
        Args:
            task_complexity: Task complexity level
            context: Additional context for routing decision
            
        Returns:
            Selected model identifier
        """
        try:
            complexity_enum = ModelComplexity(task_complexity.lower())
        except ValueError:
            complexity_enum = ModelComplexity.MODERATE
            logger.warning(f"Unknown complexity level: {task_complexity}, defaulting to moderate")
        
        # Get current service tier and budget status
        current_tier = await self._get_current_service_tier()
        budget_status = await self._get_budget_status()
        
        # Find appropriate routing rule
        selected_rule = None
        for rule_name, rule in self.model_routing_rules.items():
            if rule.complexity_threshold == complexity_enum:
                selected_rule = rule
                break
        
        if not selected_rule:
            # Default to moderate complexity rule
            selected_rule = self.model_routing_rules["moderate_tasks"]
            logger.warning(f"No routing rule found for complexity {complexity_enum}, using moderate")
        
        # Apply cost optimization based on current constraints
        selected_model = selected_rule.preferred_model
        
        # Check if we need to downgrade due to budget constraints
        if current_tier in [ServiceTier.ECONOMY, ServiceTier.EMERGENCY]:
            # Force downgrade to cheaper model
            if complexity_enum != ModelComplexity.CRITICAL:
                cheaper_rule = self.model_routing_rules["simple_tasks"]
                selected_model = cheaper_rule.preferred_model
                logger.info(f"Downgraded model due to service tier {current_tier}: {selected_model}")
                self.optimization_decisions += 1
        
        # Check budget constraints
        estimated_cost = await self._estimate_model_cost(selected_model, context)
        category = CostCategory.BEDROCK_INFERENCE
        
        if not await self.check_budget_limits(category, estimated_cost):
            # Budget exceeded, try fallback model
            fallback_model = selected_rule.fallback_model
            fallback_cost = await self._estimate_model_cost(fallback_model, context)
            
            if await self.check_budget_limits(category, fallback_cost):
                selected_model = fallback_model
                logger.info(f"Used fallback model due to budget constraints: {selected_model}")
                self.optimization_decisions += 1
            else:
                # Even fallback exceeds budget
                if complexity_enum == ModelComplexity.CRITICAL:
                    # Allow critical tasks to proceed
                    logger.warning(f"Critical task proceeding despite budget constraints: {selected_model}")
                else:
                    raise BudgetExceededError(f"Budget exceeded for {category}, cannot proceed with operation")
        
        # Record the routing decision
        await self._record_routing_decision(complexity_enum, selected_model, estimated_cost, context)
        
        return selected_model
    
    async def dynamic_detection_sampling(self, incident_risk_level: str, system_load: float) -> Dict[str, Any]:
        """
        Adjust detection sampling based on risk and cost constraints.
        
        Args:
            incident_risk_level: Risk level (low, medium, high, critical)
            system_load: Current system load (0.0 to 1.0)
            
        Returns:
            Sampling configuration
        """
        base_sampling_rate = 1.0  # 100% sampling by default
        
        # Adjust based on risk level
        risk_multipliers = {
            "low": 0.3,
            "medium": 0.6,
            "high": 0.9,
            "critical": 1.0
        }
        
        risk_multiplier = risk_multipliers.get(incident_risk_level.lower(), 0.6)
        
        # Adjust based on system load
        load_adjustment = 1.0 - (system_load * 0.3)  # Reduce sampling under high load
        
        # Adjust based on budget status
        budget_status = await self._get_budget_status()
        budget_multiplier = 1.0
        
        if budget_status["overall_usage_percent"] > 80:
            budget_multiplier = 0.5  # Reduce sampling when budget is tight
        elif budget_status["overall_usage_percent"] > 90:
            budget_multiplier = 0.3  # Aggressive reduction near budget limit
        
        # Calculate final sampling rate
        final_sampling_rate = base_sampling_rate * risk_multiplier * load_adjustment * budget_multiplier
        final_sampling_rate = max(0.1, min(1.0, final_sampling_rate))  # Clamp between 10% and 100%
        
        # Determine sampling interval
        base_interval_seconds = 30
        sampling_interval = int(base_interval_seconds / final_sampling_rate)
        
        sampling_config = {
            "sampling_rate": final_sampling_rate,
            "sampling_interval_seconds": sampling_interval,
            "risk_level": incident_risk_level,
            "system_load": system_load,
            "budget_constraint": budget_multiplier < 1.0,
            "estimated_cost_reduction_percent": (1.0 - final_sampling_rate) * 100
        }
        
        logger.info(f"Dynamic sampling configured: {sampling_config}")
        return sampling_config
    
    async def workload_aware_scaling(self, workload_profile: WorkloadProfile) -> Dict[str, Any]:
        """
        Scale resources based on workload profile and cost constraints.
        
        Args:
            workload_profile: Workload characteristics
            
        Returns:
            Scaling recommendations
        """
        workload_id = f"workload_{int(datetime.utcnow().timestamp())}"
        self.active_workloads[workload_id] = workload_profile
        
        # Analyze workload requirements
        scaling_recommendations = {
            "workload_id": workload_id,
            "agent_scaling": {},
            "model_allocation": {},
            "resource_limits": {},
            "cost_optimization": {},
            "estimated_total_cost": Decimal('0')
        }
        
        # Agent scaling based on incident severity
        severity_scaling = {
            "low": {"detection": 1, "diagnosis": 1, "prediction": 1, "resolution": 1, "communication": 1},
            "medium": {"detection": 2, "diagnosis": 2, "prediction": 1, "resolution": 2, "communication": 1},
            "high": {"detection": 3, "diagnosis": 3, "prediction": 2, "resolution": 3, "communication": 2},
            "critical": {"detection": 5, "diagnosis": 5, "prediction": 3, "resolution": 5, "communication": 3}
        }
        
        base_scaling = severity_scaling.get(workload_profile.incident_severity.lower(), severity_scaling["medium"])
        
        # Apply budget constraints
        budget_status = await self._get_budget_status()
        if budget_status["overall_usage_percent"] > 80:
            # Reduce scaling under budget pressure
            scaling_factor = 0.7
            base_scaling = {agent: max(1, int(count * scaling_factor)) for agent, count in base_scaling.items()}
            logger.info(f"Applied budget-constrained scaling: {scaling_factor}")
        
        scaling_recommendations["agent_scaling"] = base_scaling
        
        # Model allocation based on workload pattern
        total_model_requests = sum(workload_profile.model_usage_pattern.values())
        for model_type, request_count in workload_profile.model_usage_pattern.items():
            allocation_percent = (request_count / total_model_requests) * 100 if total_model_requests > 0 else 0
            
            # Route to appropriate models
            if model_type == "simple":
                recommended_model = "anthropic.claude-3-haiku-20240307-v1:0"
            elif model_type == "complex":
                recommended_model = "anthropic.claude-3-5-sonnet-20241022-v2:0"
            else:
                recommended_model = await self.adaptive_model_routing("moderate", {"workload_id": workload_id})
            
            scaling_recommendations["model_allocation"][model_type] = {
                "recommended_model": recommended_model,
                "allocation_percent": allocation_percent,
                "estimated_requests": request_count
            }
        
        # Resource limits based on cost constraints
        max_cost_per_hour = self.budget_limits[CostCategory.BEDROCK_INFERENCE].hourly_limit_usd * Decimal('0.8')
        scaling_recommendations["resource_limits"] = {
            "max_cost_per_hour_usd": float(max_cost_per_hour),
            "max_concurrent_requests": 100,  # Based on cost and performance limits
            "timeout_seconds": 300
        }
        
        # Cost optimization strategies
        scaling_recommendations["cost_optimization"] = {
            "use_spot_instances": budget_status["overall_usage_percent"] > 70,
            "enable_request_batching": True,
            "cache_embeddings": True,
            "compress_responses": budget_status["overall_usage_percent"] > 60
        }
        
        # Estimate total cost
        estimated_cost = await self._estimate_workload_cost(workload_profile, scaling_recommendations)
        scaling_recommendations["estimated_total_cost"] = float(estimated_cost)
        
        logger.info(f"Workload scaling recommendations generated for {workload_id}: estimated cost ${estimated_cost}")
        
        return scaling_recommendations
    
    async def _get_current_cost_metrics(self, category: CostCategory) -> CostMetrics:
        """Get current cost metrics for a category."""
        if category not in self.cost_metrics:
            self.cost_metrics[category] = CostMetrics(category=category)
        
        # In a real implementation, this would query AWS Cost Explorer
        # For now, return cached metrics
        return self.cost_metrics[category]
    
    async def _get_current_service_tier(self) -> ServiceTier:
        """Get current service tier based on system status and budget."""
        budget_status = await self._get_budget_status()
        
        if budget_status["overall_usage_percent"] > 95:
            return ServiceTier.EMERGENCY
        elif budget_status["overall_usage_percent"] > 85:
            return ServiceTier.ECONOMY
        elif budget_status["overall_usage_percent"] > 70:
            return ServiceTier.STANDARD
        else:
            return ServiceTier.PREMIUM
    
    async def _get_budget_status(self) -> Dict[str, Any]:
        """Get overall budget status across all categories."""
        total_spent = Decimal('0')
        total_budget = Decimal('0')
        category_status = {}
        
        for category, budget_limit in self.budget_limits.items():
            metrics = await self._get_current_cost_metrics(category)
            usage_percent = (metrics.current_day_spend / budget_limit.daily_limit_usd) * 100
            
            category_status[category.value] = {
                "spent_today": float(metrics.current_day_spend),
                "daily_budget": float(budget_limit.daily_limit_usd),
                "usage_percent": float(usage_percent)
            }
            
            total_spent += metrics.current_day_spend
            total_budget += budget_limit.daily_limit_usd
        
        overall_usage_percent = (total_spent / total_budget) * 100 if total_budget > 0 else 0
        
        return {
            "overall_usage_percent": float(overall_usage_percent),
            "total_spent_today": float(total_spent),
            "total_daily_budget": float(total_budget),
            "categories": category_status
        }
    
    async def _estimate_model_cost(self, model_id: str, context: Dict[str, Any]) -> Decimal:
        """Estimate cost for model inference."""
        # Simplified cost estimation based on model and expected tokens
        token_estimates = {
            "anthropic.claude-3-haiku-20240307-v1:0": {"input": Decimal('0.25'), "output": Decimal('1.25')},
            "anthropic.claude-3-5-sonnet-20241022-v2:0": {"input": Decimal('3.00'), "output": Decimal('15.00')}
        }
        
        model_costs = token_estimates.get(model_id, {"input": Decimal('1.00'), "output": Decimal('5.00')})
        
        # Estimate tokens based on context
        estimated_input_tokens = context.get("estimated_input_tokens", 1000)
        estimated_output_tokens = context.get("estimated_output_tokens", 500)
        
        input_cost = (Decimal(estimated_input_tokens) / 1000) * model_costs["input"]
        output_cost = (Decimal(estimated_output_tokens) / 1000) * model_costs["output"]
        
        return input_cost + output_cost
    
    async def _estimate_workload_cost(self, workload_profile: WorkloadProfile, scaling_config: Dict[str, Any]) -> Decimal:
        """Estimate total cost for workload."""
        total_cost = Decimal('0')
        
        # Estimate based on model usage and scaling
        for model_type, allocation in scaling_config["model_allocation"].items():
            model_id = allocation["recommended_model"]
            request_count = allocation["estimated_requests"]
            
            # Estimate cost per request
            context = {"estimated_input_tokens": 1000, "estimated_output_tokens": 500}
            cost_per_request = await self._estimate_model_cost(model_id, context)
            
            model_total_cost = cost_per_request * Decimal(request_count)
            total_cost += model_total_cost
        
        # Add compute costs based on agent scaling
        agent_scaling = scaling_config["agent_scaling"]
        total_agents = sum(agent_scaling.values())
        compute_cost_per_agent_hour = Decimal('0.50')  # Estimated
        duration_hours = Decimal(workload_profile.expected_duration_minutes) / 60
        
        compute_cost = total_agents * compute_cost_per_agent_hour * duration_hours
        total_cost += compute_cost
        
        return total_cost
    
    async def _send_budget_alert(self, category: CostCategory, period: str, usage_percent: float):
        """Send budget alert notification."""
        logger.warning(f"Budget alert: {category.value} {period} usage at {usage_percent:.1f}%")
        
        # In a real implementation, this would send notifications via SNS, Slack, etc.
        alert_data = {
            "category": category.value,
            "period": period,
            "usage_percent": usage_percent,
            "timestamp": datetime.utcnow().isoformat(),
            "severity": "high" if usage_percent > 90 else "medium"
        }
        
        # Store alert for tracking
        if not hasattr(self, 'budget_alerts'):
            self.budget_alerts = []
        self.budget_alerts.append(alert_data)
    
    async def _record_routing_decision(self, complexity: ModelComplexity, selected_model: str, 
                                     estimated_cost: Decimal, context: Dict[str, Any]):
        """Record model routing decision for analysis."""
        decision_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "complexity": complexity.value,
            "selected_model": selected_model,
            "estimated_cost": float(estimated_cost),
            "context": context
        }
        
        if not hasattr(self, 'routing_decisions'):
            self.routing_decisions = []
        self.routing_decisions.append(decision_record)
        
        # Keep only recent decisions
        if len(self.routing_decisions) > 1000:
            self.routing_decisions = self.routing_decisions[-500:]
    
    async def update_cost_metrics(self, category: CostCategory, actual_cost: Decimal, 
                                request_count: int = 1):
        """Update cost metrics with actual usage."""
        if category not in self.cost_metrics:
            self.cost_metrics[category] = CostMetrics(category=category)
        
        metrics = self.cost_metrics[category]
        
        # Update current period costs
        current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        current_day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Reset counters if new period
        if metrics.last_updated.replace(minute=0, second=0, microsecond=0) < current_hour:
            metrics.current_hour_spend = Decimal('0')
        
        if metrics.last_updated.replace(hour=0, minute=0, second=0, microsecond=0) < current_day:
            metrics.current_day_spend = Decimal('0')
        
        # Update metrics
        metrics.current_hour_spend += actual_cost
        metrics.current_day_spend += actual_cost
        metrics.request_count += request_count
        
        if metrics.request_count > 0:
            total_cost = metrics.current_day_spend
            metrics.average_cost_per_request = total_cost / metrics.request_count
        
        metrics.last_updated = datetime.utcnow()
        
        logger.debug(f"Updated cost metrics for {category.value}: +${actual_cost}")
    
    def get_finops_metrics(self) -> Dict[str, Any]:
        """Get comprehensive FinOps metrics and statistics."""
        return {
            "budget_status": {
                "total_violations": self.budget_violations,
                "categories": {
                    category.value: {
                        "daily_limit": float(limit.daily_limit_usd),
                        "hourly_limit": float(limit.hourly_limit_usd),
                        "alert_threshold": limit.alert_threshold_percent,
                        "hard_limit_enabled": limit.hard_limit_enabled
                    }
                    for category, limit in self.budget_limits.items()
                }
            },
            "optimization_metrics": {
                "total_cost_saved": float(self.total_cost_saved),
                "optimization_decisions": self.optimization_decisions,
                "current_service_tier": self.current_service_tier.value,
                "auto_optimization_enabled": self.auto_optimization_enabled
            },
            "model_routing": {
                "available_rules": list(self.model_routing_rules.keys()),
                "recent_decisions": getattr(self, 'routing_decisions', [])[-10:]  # Last 10 decisions
            },
            "active_workloads": len(self.active_workloads),
            "cost_categories": {
                category.value: {
                    "current_hour_spend": float(metrics.current_hour_spend),
                    "current_day_spend": float(metrics.current_day_spend),
                    "request_count": metrics.request_count,
                    "average_cost_per_request": float(metrics.average_cost_per_request)
                }
                for category, metrics in self.cost_metrics.items()
            }
        }
    
    async def generate_cost_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive cost optimization report."""
        budget_status = await self._get_budget_status()
        
        report = {
            "report_timestamp": datetime.utcnow().isoformat(),
            "executive_summary": {
                "total_spend_today": budget_status["total_spent_today"],
                "budget_utilization": budget_status["overall_usage_percent"],
                "cost_savings_achieved": float(self.total_cost_saved),
                "optimization_opportunities": []
            },
            "budget_analysis": budget_status,
            "optimization_recommendations": [],
            "cost_trends": [],
            "risk_assessment": {
                "budget_risk_level": "low",
                "projected_monthly_spend": 0.0,
                "budget_runway_days": 0
            }
        }
        
        # Generate optimization recommendations
        if budget_status["overall_usage_percent"] > 80:
            report["optimization_recommendations"].extend([
                "Enable aggressive model downgrading for non-critical tasks",
                "Increase detection sampling intervals during low-risk periods",
                "Implement request batching to reduce API calls",
                "Consider using spot instances for non-critical workloads"
            ])
        
        if budget_status["overall_usage_percent"] > 90:
            report["optimization_recommendations"].extend([
                "Activate emergency cost controls",
                "Temporarily disable non-essential features",
                "Implement strict rate limiting",
                "Consider workload deferral for low-priority incidents"
            ])
        
        # Risk assessment
        if budget_status["overall_usage_percent"] > 95:
            report["risk_assessment"]["budget_risk_level"] = "critical"
        elif budget_status["overall_usage_percent"] > 85:
            report["risk_assessment"]["budget_risk_level"] = "high"
        elif budget_status["overall_usage_percent"] > 70:
            report["risk_assessment"]["budget_risk_level"] = "medium"
        
        logger.info(f"Generated cost optimization report: {report['risk_assessment']['budget_risk_level']} risk level")
        
        return report


# Global FinOps controller instance
_finops_controller: Optional[FinOpsController] = None


def get_finops_controller() -> FinOpsController:
    """Get the global FinOps controller instance."""
    global _finops_controller
    if _finops_controller is None:
        _finops_controller = FinOpsController()
    return _finops_controller