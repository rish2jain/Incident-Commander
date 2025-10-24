"""
Model Router Service

Implements intelligent model routing with cost optimization and performance-based selection.
Routes requests to appropriate models (Haiku/Sonnet) based on latency, cost, and accuracy requirements.

Requirements: 8.1, 8.2, 8.3
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum

from src.utils.config import config
from src.utils.logging import get_logger
from src.utils.exceptions import ModelRoutingError
from src.services.aws import get_aws_service_factory, BedrockClient


logger = get_logger(__name__)


class ModelTier(Enum):
    """Model tier based on cost and capability."""
    ECONOMY = "economy"      # Lowest cost, basic capability (Haiku)
    STANDARD = "standard"    # Balanced cost/performance (Sonnet)
    PREMIUM = "premium"      # High cost, best performance (Opus)


class RoutingStrategy(Enum):
    """Model routing strategy."""
    COST_OPTIMIZED = "cost_optimized"        # Minimize cost
    LATENCY_OPTIMIZED = "latency_optimized"  # Minimize response time
    ACCURACY_OPTIMIZED = "accuracy_optimized" # Maximize accuracy
    BALANCED = "balanced"                     # Balance all factors


@dataclass
class ModelConfig:
    """Model configuration with performance and cost metrics."""
    model_id: str
    model_name: str
    cost_per_1k_tokens: float
    accuracy_score: float
    avg_response_time_ms: int
    max_tokens: int
    tier: ModelTier
    availability_score: float = 1.0
    last_health_check: Optional[datetime] = None


@dataclass
class RoutingRequest:
    """Model routing request parameters."""
    task_type: str
    incident_severity: str = "medium"
    required_accuracy: float = 0.85
    max_latency_ms: Optional[int] = None
    max_cost_per_1k_tokens: Optional[float] = None
    strategy: RoutingStrategy = RoutingStrategy.BALANCED
    context_length: int = 1000


@dataclass
class RoutingResult:
    """Model routing result."""
    selected_model: str
    model_config: ModelConfig
    routing_reason: str
    estimated_cost: float
    estimated_latency_ms: int
    confidence_score: float
    fallback_models: List[str] = field(default_factory=list)


@dataclass
class ModelMetrics:
    """Model performance metrics."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time_ms: float = 0.0
    total_cost: float = 0.0
    total_tokens: int = 0
    last_used: Optional[datetime] = None
    error_rate: float = 0.0


@dataclass
class CostAnalysis:
    """Cost analysis and optimization data."""
    current_hourly_cost: float = 0.0
    projected_daily_cost: float = 0.0
    cost_by_model: Dict[str, float] = field(default_factory=dict)
    cost_by_task_type: Dict[str, float] = field(default_factory=dict)
    potential_savings: float = 0.0
    optimization_recommendations: List[str] = field(default_factory=list)


class ModelRouter:
    """
    Intelligent model routing service with cost optimization and performance-based selection.
    Routes requests to appropriate models based on requirements and real-time metrics.
    """
    
    def __init__(self):
        self.logger = logger
        
        # Model configurations with realistic Bedrock pricing
        self.model_configs = {
            "claude-3-haiku": ModelConfig(
                model_id="anthropic.claude-3-haiku-20240307-v1:0",
                model_name="claude-3-haiku",
                cost_per_1k_tokens=0.25,
                accuracy_score=0.85,
                avg_response_time_ms=800,
                max_tokens=4096,
                tier=ModelTier.ECONOMY
            ),
            "claude-3-sonnet": ModelConfig(
                model_id="anthropic.claude-3-sonnet-20240229-v1:0",
                model_name="claude-3-sonnet",
                cost_per_1k_tokens=3.0,
                accuracy_score=0.92,
                avg_response_time_ms=1200,
                max_tokens=4096,
                tier=ModelTier.STANDARD
            ),
            "claude-3-opus": ModelConfig(
                model_id="anthropic.claude-3-opus-20240229-v1:0",
                model_name="claude-3-opus",
                cost_per_1k_tokens=15.0,
                accuracy_score=0.96,
                avg_response_time_ms=2000,
                max_tokens=4096,
                tier=ModelTier.PREMIUM
            )
        }
        
        # Task-specific model preferences
        self.task_preferences = {
            "detection": {
                "preferred_tier": ModelTier.ECONOMY,
                "max_latency_ms": 1000,
                "min_accuracy": 0.80
            },
            "diagnosis": {
                "preferred_tier": ModelTier.STANDARD,
                "max_latency_ms": 2000,
                "min_accuracy": 0.90
            },
            "prediction": {
                "preferred_tier": ModelTier.STANDARD,
                "max_latency_ms": 1500,
                "min_accuracy": 0.88
            },
            "resolution": {
                "preferred_tier": ModelTier.STANDARD,
                "max_latency_ms": 2500,
                "min_accuracy": 0.92
            },
            "communication": {
                "preferred_tier": ModelTier.ECONOMY,
                "max_latency_ms": 800,
                "min_accuracy": 0.85
            }
        }
        
        # Performance tracking
        self.model_metrics: Dict[str, ModelMetrics] = {
            model_name: ModelMetrics() for model_name in self.model_configs.keys()
        }
        
        # Cost tracking
        self.cost_analysis = CostAnalysis()
        self.cost_history = deque(maxlen=1440)  # 24 hours of minute-by-minute data
        
        # Routing statistics
        self.routing_history = deque(maxlen=10000)  # Last 10k routing decisions
        self.model_health_cache: Dict[str, Tuple[bool, datetime]] = {}
        
        # AWS clients
        self.aws_factory = get_aws_service_factory()
        self.bedrock_client: Optional[BedrockClient] = None
        
        # Configuration
        self.health_check_interval = 300  # 5 minutes
        self.cost_optimization_enabled = True
        self.fallback_enabled = True
        
    async def initialize(self) -> None:
        """Initialize model router with AWS clients and health checks."""
        try:
            # Initialize Bedrock client
            self.bedrock_client = BedrockClient(self.aws_factory)
            
            # Perform initial health checks
            await self._perform_health_checks()
            
            # Start background tasks
            asyncio.create_task(self._health_monitoring_loop())
            asyncio.create_task(self._cost_tracking_loop())
            asyncio.create_task(self._metrics_cleanup_loop())
            
            self.logger.info("Model router initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize model router: {e}")
            raise ModelRoutingError(f"Initialization failed: {e}")
    
    async def route_request(self, request: RoutingRequest) -> RoutingResult:
        """
        Route request to optimal model based on requirements and current metrics.
        
        Args:
            request: Routing request with requirements
            
        Returns:
            Routing result with selected model and metadata
        """
        try:
            # Get task preferences
            task_prefs = self.task_preferences.get(request.task_type, {})
            
            # Filter available models based on requirements
            available_models = await self._filter_available_models(request, task_prefs)
            
            if not available_models:
                raise ModelRoutingError("No models available that meet requirements")
            
            # Select optimal model based on strategy
            selected_model = self._select_optimal_model(available_models, request, task_prefs)
            
            # Calculate estimates
            model_config = self.model_configs[selected_model]
            estimated_cost = self._estimate_cost(model_config, request.context_length)
            estimated_latency = self._estimate_latency(model_config, request.context_length)
            
            # Generate fallback options
            fallback_models = self._generate_fallback_options(selected_model, available_models)
            
            # Create routing result
            result = RoutingResult(
                selected_model=selected_model,
                model_config=model_config,
                routing_reason=self._generate_routing_reason(selected_model, request),
                estimated_cost=estimated_cost,
                estimated_latency_ms=estimated_latency,
                confidence_score=self._calculate_confidence_score(selected_model, request),
                fallback_models=fallback_models
            )
            
            # Record routing decision
            await self._record_routing_decision(request, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Model routing failed: {e}")
            raise ModelRoutingError(f"Routing failed: {e}")
    
    async def _filter_available_models(self, request: RoutingRequest, task_prefs: Dict[str, Any]) -> List[str]:
        """Filter models based on availability and requirements."""
        available_models = []
        
        for model_name, config in self.model_configs.items():
            # Check model health
            if not await self._is_model_healthy(model_name):
                continue
            
            # Check accuracy requirements
            min_accuracy = max(request.required_accuracy, task_prefs.get("min_accuracy", 0.8))
            if config.accuracy_score < min_accuracy:
                continue
            
            # Check latency requirements
            max_latency = request.max_latency_ms or task_prefs.get("max_latency_ms", 5000)
            if config.avg_response_time_ms > max_latency:
                continue
            
            # Check cost requirements
            if request.max_cost_per_1k_tokens and config.cost_per_1k_tokens > request.max_cost_per_1k_tokens:
                continue
            
            available_models.append(model_name)
        
        return available_models
    
    def _select_optimal_model(self, available_models: List[str], 
                            request: RoutingRequest, 
                            task_prefs: Dict[str, Any]) -> str:
        """Select optimal model based on routing strategy."""
        if len(available_models) == 1:
            return available_models[0]
        
        # Calculate scores for each model
        model_scores = {}
        
        for model_name in available_models:
            config = self.model_configs[model_name]
            metrics = self.model_metrics[model_name]
            
            if request.strategy == RoutingStrategy.COST_OPTIMIZED:
                # Prioritize lowest cost
                score = 1.0 / (config.cost_per_1k_tokens + 0.01)
            elif request.strategy == RoutingStrategy.LATENCY_OPTIMIZED:
                # Prioritize lowest latency
                actual_latency = metrics.avg_response_time_ms or config.avg_response_time_ms
                score = 1.0 / (actual_latency + 1)
            elif request.strategy == RoutingStrategy.ACCURACY_OPTIMIZED:
                # Prioritize highest accuracy
                score = config.accuracy_score
            else:  # BALANCED
                # Balance cost, latency, and accuracy
                cost_score = 1.0 / (config.cost_per_1k_tokens + 0.01)
                latency_score = 1.0 / (config.avg_response_time_ms + 1)
                accuracy_score = config.accuracy_score
                availability_score = config.availability_score
                
                # Weight based on incident severity
                if request.incident_severity in ["critical", "high"]:
                    # Prioritize accuracy and availability for critical incidents
                    score = (accuracy_score * 0.4 + availability_score * 0.3 + 
                            latency_score * 0.2 + cost_score * 0.1)
                else:
                    # Balance all factors for normal incidents
                    score = (cost_score * 0.3 + latency_score * 0.25 + 
                            accuracy_score * 0.25 + availability_score * 0.2)
            
            # Apply task preference bonus
            preferred_tier = task_prefs.get("preferred_tier")
            if preferred_tier and config.tier == preferred_tier:
                score *= 1.2
            
            model_scores[model_name] = score
        
        # Select model with highest score
        return max(model_scores.keys(), key=lambda m: model_scores[m])
    
    def _estimate_cost(self, config: ModelConfig, context_length: int) -> float:
        """Estimate cost for request based on context length."""
        # Estimate total tokens (input + output)
        estimated_input_tokens = context_length
        estimated_output_tokens = min(config.max_tokens // 4, 500)  # Conservative estimate
        total_tokens = estimated_input_tokens + estimated_output_tokens
        
        return (total_tokens / 1000.0) * config.cost_per_1k_tokens
    
    def _estimate_latency(self, config: ModelConfig, context_length: int) -> int:
        """Estimate latency based on model config and context length."""
        base_latency = config.avg_response_time_ms
        
        # Add latency based on context length (longer context = more processing time)
        context_latency = (context_length / 1000) * 50  # 50ms per 1k tokens
        
        return int(base_latency + context_latency)
    
    def _generate_fallback_options(self, selected_model: str, available_models: List[str]) -> List[str]:
        """Generate fallback model options."""
        fallbacks = []
        
        # Remove selected model from available options
        remaining_models = [m for m in available_models if m != selected_model]
        
        # Sort by reliability (availability score) and add top 2 as fallbacks
        remaining_models.sort(
            key=lambda m: self.model_configs[m].availability_score, 
            reverse=True
        )
        
        return remaining_models[:2]
    
    def _generate_routing_reason(self, selected_model: str, request: RoutingRequest) -> str:
        """Generate human-readable routing reason."""
        config = self.model_configs[selected_model]
        
        reasons = []
        
        if request.strategy == RoutingStrategy.COST_OPTIMIZED:
            reasons.append(f"Cost-optimized selection (${config.cost_per_1k_tokens}/1k tokens)")
        elif request.strategy == RoutingStrategy.LATENCY_OPTIMIZED:
            reasons.append(f"Latency-optimized selection ({config.avg_response_time_ms}ms avg)")
        elif request.strategy == RoutingStrategy.ACCURACY_OPTIMIZED:
            reasons.append(f"Accuracy-optimized selection ({config.accuracy_score:.2f} accuracy)")
        else:
            reasons.append("Balanced optimization")
        
        if request.incident_severity in ["critical", "high"]:
            reasons.append("High-priority incident")
        
        task_prefs = self.task_preferences.get(request.task_type, {})
        if task_prefs.get("preferred_tier") == config.tier:
            reasons.append(f"Preferred tier for {request.task_type}")
        
        return "; ".join(reasons)
    
    def _calculate_confidence_score(self, selected_model: str, request: RoutingRequest) -> float:
        """Calculate confidence score for routing decision."""
        config = self.model_configs[selected_model]
        metrics = self.model_metrics[selected_model]
        
        # Base confidence from model accuracy
        confidence = config.accuracy_score
        
        # Adjust based on model reliability
        if metrics.total_requests > 0:
            success_rate = metrics.successful_requests / metrics.total_requests
            confidence *= success_rate
        
        # Adjust based on availability
        confidence *= config.availability_score
        
        # Adjust based on how well requirements are met
        if request.required_accuracy <= config.accuracy_score:
            confidence *= 1.1
        
        return min(confidence, 1.0)
    
    async def _record_routing_decision(self, request: RoutingRequest, result: RoutingResult) -> None:
        """Record routing decision for analytics and optimization."""
        decision_record = {
            "timestamp": datetime.utcnow(),
            "task_type": request.task_type,
            "incident_severity": request.incident_severity,
            "strategy": request.strategy.value,
            "selected_model": result.selected_model,
            "estimated_cost": result.estimated_cost,
            "estimated_latency_ms": result.estimated_latency_ms,
            "confidence_score": result.confidence_score,
            "routing_reason": result.routing_reason
        }
        
        self.routing_history.append(decision_record)
        
        # Update cost tracking
        self.cost_analysis.cost_by_model[result.selected_model] = (
            self.cost_analysis.cost_by_model.get(result.selected_model, 0) + 
            result.estimated_cost
        )
        self.cost_analysis.cost_by_task_type[request.task_type] = (
            self.cost_analysis.cost_by_task_type.get(request.task_type, 0) + 
            result.estimated_cost
        )
    
    async def record_request_completion(self, model_name: str, 
                                      success: bool, 
                                      actual_latency_ms: int,
                                      actual_cost: float,
                                      tokens_used: int) -> None:
        """Record actual request completion metrics."""
        metrics = self.model_metrics[model_name]
        
        # Update request counts
        metrics.total_requests += 1
        if success:
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1
        
        # Update response time (moving average)
        if metrics.avg_response_time_ms == 0:
            metrics.avg_response_time_ms = actual_latency_ms
        else:
            # Exponential moving average with alpha=0.1
            metrics.avg_response_time_ms = (
                0.9 * metrics.avg_response_time_ms + 0.1 * actual_latency_ms
            )
        
        # Update cost and token tracking
        metrics.total_cost += actual_cost
        metrics.total_tokens += tokens_used
        metrics.last_used = datetime.utcnow()
        
        # Update error rate
        metrics.error_rate = metrics.failed_requests / metrics.total_requests
        
        # Update model availability score based on recent performance
        if metrics.total_requests >= 10:
            recent_success_rate = metrics.successful_requests / metrics.total_requests
            self.model_configs[model_name].availability_score = recent_success_rate
        
        self.logger.debug(f"Recorded completion for {model_name}: success={success}, latency={actual_latency_ms}ms")
    
    async def _is_model_healthy(self, model_name: str) -> bool:
        """Check if model is healthy and available."""
        # Check cache first
        if model_name in self.model_health_cache:
            is_healthy, last_check = self.model_health_cache[model_name]
            if (datetime.utcnow() - last_check).total_seconds() < self.health_check_interval:
                return is_healthy
        
        # Perform health check
        try:
            if self.bedrock_client:
                config = self.model_configs[model_name]
                # Simple health check with minimal prompt
                await self.bedrock_client.invoke_model(
                    config.model_id, 
                    "Health check", 
                    max_tokens=10
                )
                
            self.model_health_cache[model_name] = (True, datetime.utcnow())
            return True
            
        except Exception as e:
            self.logger.warning(f"Health check failed for {model_name}: {e}")
            self.model_health_cache[model_name] = (False, datetime.utcnow())
            return False
    
    async def _perform_health_checks(self) -> None:
        """Perform health checks on all models."""
        for model_name in self.model_configs.keys():
            await self._is_model_healthy(model_name)
    
    async def _health_monitoring_loop(self) -> None:
        """Background health monitoring loop."""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._perform_health_checks()
                
            except Exception as e:
                self.logger.error(f"Health monitoring loop error: {e}")
    
    async def _cost_tracking_loop(self) -> None:
        """Background cost tracking loop."""
        while True:
            try:
                await asyncio.sleep(60)  # Update every minute
                
                # Calculate current hourly cost
                current_cost = sum(self.cost_analysis.cost_by_model.values())
                self.cost_analysis.current_hourly_cost = current_cost
                self.cost_analysis.projected_daily_cost = current_cost * 24
                
                # Add to history
                self.cost_history.append(current_cost)
                
                # Generate optimization recommendations
                if self.cost_optimization_enabled:
                    await self._generate_cost_optimizations()
                
            except Exception as e:
                self.logger.error(f"Cost tracking loop error: {e}")
    
    async def _generate_cost_optimizations(self) -> None:
        """Generate cost optimization recommendations."""
        recommendations = []
        
        # Analyze model usage patterns
        total_cost = sum(self.cost_analysis.cost_by_model.values())
        if total_cost > 0:
            for model_name, cost in self.cost_analysis.cost_by_model.items():
                cost_percentage = (cost / total_cost) * 100
                
                # High-cost model recommendations
                if cost_percentage > 50 and model_name != "claude-3-haiku":
                    cheaper_alternative = self._find_cheaper_alternative(model_name)
                    if cheaper_alternative:
                        potential_savings = cost * 0.3  # Estimated 30% savings
                        recommendations.append(
                            f"Consider using {cheaper_alternative} instead of {model_name} "
                            f"for non-critical tasks (potential savings: ${potential_savings:.2f})"
                        )
        
        # Task-specific recommendations
        for task_type, cost in self.cost_analysis.cost_by_task_type.items():
            if cost > 10:  # High cost tasks
                task_prefs = self.task_preferences.get(task_type, {})
                if task_prefs.get("preferred_tier") != ModelTier.ECONOMY:
                    recommendations.append(
                        f"Consider using economy tier models for {task_type} tasks "
                        f"to reduce costs (current cost: ${cost:.2f})"
                    )
        
        self.cost_analysis.optimization_recommendations = recommendations
    
    def _find_cheaper_alternative(self, model_name: str) -> Optional[str]:
        """Find cheaper alternative model with similar capabilities."""
        current_config = self.model_configs[model_name]
        
        # Find models with lower cost but similar accuracy (within 5%)
        alternatives = []
        for name, config in self.model_configs.items():
            if (name != model_name and 
                config.cost_per_1k_tokens < current_config.cost_per_1k_tokens and
                config.accuracy_score >= current_config.accuracy_score - 0.05):
                alternatives.append(name)
        
        # Return cheapest alternative
        if alternatives:
            return min(alternatives, key=lambda m: self.model_configs[m].cost_per_1k_tokens)
        
        return None
    
    async def _metrics_cleanup_loop(self) -> None:
        """Background metrics cleanup loop."""
        while True:
            try:
                await asyncio.sleep(3600)  # Cleanup every hour
                
                # Clean up old routing history (keep last 24 hours)
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                self.routing_history = deque(
                    [record for record in self.routing_history 
                     if record["timestamp"] > cutoff_time],
                    maxlen=10000
                )
                
                # Reset daily cost tracking
                if datetime.utcnow().hour == 0:  # Midnight
                    self.cost_analysis.cost_by_model.clear()
                    self.cost_analysis.cost_by_task_type.clear()
                
            except Exception as e:
                self.logger.error(f"Metrics cleanup loop error: {e}")
    
    async def get_model_metrics(self) -> Dict[str, ModelMetrics]:
        """Get current model performance metrics."""
        return self.model_metrics.copy()
    
    async def get_cost_analysis(self) -> CostAnalysis:
        """Get current cost analysis."""
        return self.cost_analysis
    
    async def get_routing_statistics(self) -> Dict[str, Any]:
        """Get routing statistics and analytics."""
        if not self.routing_history:
            return {"total_requests": 0}
        
        # Calculate statistics from routing history
        total_requests = len(self.routing_history)
        
        # Model usage distribution
        model_usage = defaultdict(int)
        strategy_usage = defaultdict(int)
        task_type_usage = defaultdict(int)
        
        total_estimated_cost = 0.0
        total_estimated_latency = 0.0
        
        for record in self.routing_history:
            model_usage[record["selected_model"]] += 1
            strategy_usage[record["strategy"]] += 1
            task_type_usage[record["task_type"]] += 1
            total_estimated_cost += record["estimated_cost"]
            total_estimated_latency += record["estimated_latency_ms"]
        
        return {
            "total_requests": total_requests,
            "model_usage_distribution": dict(model_usage),
            "strategy_usage_distribution": dict(strategy_usage),
            "task_type_distribution": dict(task_type_usage),
            "average_estimated_cost": total_estimated_cost / total_requests,
            "average_estimated_latency_ms": total_estimated_latency / total_requests,
            "cost_analysis": self.cost_analysis,
            "model_health": {
                name: self.model_health_cache.get(name, (False, None))[0]
                for name in self.model_configs.keys()
            }
        }
    
    async def update_model_config(self, model_name: str, updates: Dict[str, Any]) -> None:
        """Update model configuration."""
        if model_name not in self.model_configs:
            raise ModelRoutingError(f"Model {model_name} not found")
        
        config = self.model_configs[model_name]
        
        # Update allowed fields
        allowed_fields = ["cost_per_1k_tokens", "accuracy_score", "avg_response_time_ms", "availability_score"]
        for field, value in updates.items():
            if field in allowed_fields and hasattr(config, field):
                setattr(config, field, value)
        
        self.logger.info(f"Updated configuration for model {model_name}: {updates}")
    
    async def set_routing_strategy(self, strategy: RoutingStrategy) -> None:
        """Set default routing strategy."""
        # This would be used as default when no strategy is specified in requests
        self.logger.info(f"Default routing strategy set to {strategy.value}")
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        try:
            if self.bedrock_client:
                # Cleanup would be handled by AWS service factory
                pass
            
            self.logger.info("Model router cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")


# Global model router instance
_model_router: Optional[ModelRouter] = None


async def get_model_router() -> ModelRouter:
    """Get global model router instance."""
    global _model_router
    
    if _model_router is None:
        _model_router = ModelRouter()
        await _model_router.initialize()
    
    return _model_router