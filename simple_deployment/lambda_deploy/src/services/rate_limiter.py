"""
Rate limiting implementation with token bucket algorithm and intelligent routing.
"""

import asyncio
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from src.utils.constants import RATE_LIMITS
from src.utils.logging import get_logger
from src.utils.exceptions import RateLimitError


logger = get_logger("rate_limiter")


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    requests_per_period: int
    period_seconds: int
    burst_capacity: int = None  # Allow burst up to this many requests
    
    def __post_init__(self):
        if self.burst_capacity is None:
            self.burst_capacity = self.requests_per_period * 2


class RequestPriority(Enum):
    """Request priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class QueuedRequest:
    """Queued request with priority and metadata."""
    request_id: str
    priority: RequestPriority
    queued_at: datetime
    service: str
    metadata: Dict[str, Any]


class TokenBucket:
    """Token bucket implementation for rate limiting."""
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.
        
        Args:
            capacity: Maximum number of tokens
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
    
    async def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False if not enough tokens
        """
        async with self._lock:
            self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            return False
    
    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        
        # Add tokens based on elapsed time
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def get_status(self) -> Dict[str, Any]:
        """Get current bucket status."""
        self._refill()
        return {
            "tokens": self.tokens,
            "capacity": self.capacity,
            "refill_rate": self.refill_rate,
            "utilization": (self.capacity - self.tokens) / self.capacity
        }


class BedrockRateLimitManager:
    """Rate limit manager for Bedrock with intelligent model routing."""
    
    def __init__(self):
        """Initialize Bedrock rate limit manager."""
        self.model_buckets: Dict[str, TokenBucket] = {}
        self.model_health: Dict[str, float] = {}  # Health score 0.0-1.0
        self.model_costs: Dict[str, float] = {
            "anthropic.claude-3-sonnet-20240229-v1:0": 1.0,  # Base cost
            "anthropic.claude-3-haiku-20240307-v1:0": 0.3,   # Cheaper model
        }
        self.request_queue: deque = deque()
        self._setup_model_buckets()
    
    def _setup_model_buckets(self) -> None:
        """Setup token buckets for each model."""
        bedrock_config = RATE_LIMITS.get("bedrock", {"requests": 100, "period": 60})
        
        # Create buckets for each model with different capacities
        self.model_buckets["anthropic.claude-3-sonnet-20240229-v1:0"] = TokenBucket(
            capacity=bedrock_config["requests"],
            refill_rate=bedrock_config["requests"] / bedrock_config["period"]
        )
        
        self.model_buckets["anthropic.claude-3-haiku-20240307-v1:0"] = TokenBucket(
            capacity=bedrock_config["requests"] * 2,  # Higher capacity for cheaper model
            refill_rate=(bedrock_config["requests"] * 2) / bedrock_config["period"]
        )
        
        # Initialize health scores
        for model in self.model_buckets.keys():
            self.model_health[model] = 1.0
    
    async def request_model_access(self, preferred_model: str, 
                                 complexity_score: float = 0.5,
                                 priority: RequestPriority = RequestPriority.MEDIUM) -> str:
        """
        Request access to a model with intelligent routing.
        
        Args:
            preferred_model: Preferred model ID
            complexity_score: Task complexity (0.0-1.0)
            priority: Request priority
            
        Returns:
            Selected model ID
            
        Raises:
            RateLimitError: If no models are available
        """
        # Try preferred model first if healthy and available
        if (preferred_model in self.model_buckets and 
            self.model_health.get(preferred_model, 0) > 0.5):
            
            if await self.model_buckets[preferred_model].consume():
                logger.debug(f"Granted access to preferred model: {preferred_model}")
                return preferred_model
        
        # Find alternative model based on complexity and availability
        alternative_model = await self._find_alternative_model(
            complexity_score, priority, exclude=preferred_model
        )
        
        if alternative_model:
            logger.info(f"Routing to alternative model: {alternative_model} (preferred: {preferred_model})")
            return alternative_model
        
        # If high priority, queue the request
        if priority in [RequestPriority.HIGH, RequestPriority.CRITICAL]:
            await self._queue_request(preferred_model, priority)
            
            # Wait briefly and try again
            await asyncio.sleep(1)
            return await self.request_model_access(preferred_model, complexity_score, priority)
        
        raise RateLimitError(f"No models available. Preferred: {preferred_model}")
    
    async def _find_alternative_model(self, complexity_score: float, 
                                    priority: RequestPriority,
                                    exclude: str = None) -> Optional[str]:
        """Find alternative model based on complexity and availability."""
        candidates = []
        
        for model_id, bucket in self.model_buckets.items():
            if model_id == exclude:
                continue
            
            health = self.model_health.get(model_id, 0)
            cost = self.model_costs.get(model_id, 1.0)
            
            # Check if model can handle the complexity
            if model_id.endswith("haiku") and complexity_score > 0.8:
                continue  # Haiku not suitable for very complex tasks
            
            # Check availability
            bucket_status = bucket.get_status()
            if bucket_status["tokens"] < 1:
                continue
            
            # Calculate suitability score
            suitability = health * (1 / cost) * bucket_status["utilization"]
            candidates.append((model_id, suitability))
        
        if not candidates:
            return None
        
        # Sort by suitability and try to consume token
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        for model_id, _ in candidates:
            if await self.model_buckets[model_id].consume():
                return model_id
        
        return None
    
    async def _queue_request(self, model_id: str, priority: RequestPriority) -> None:
        """Queue high-priority request for later processing."""
        request = QueuedRequest(
            request_id=f"req_{int(time.time() * 1000)}",
            priority=priority,
            queued_at=datetime.utcnow(),
            service=model_id,
            metadata={}
        )
        
        # Insert based on priority
        inserted = False
        for i, queued_req in enumerate(self.request_queue):
            if priority.value > queued_req.priority.value:
                self.request_queue.insert(i, request)
                inserted = True
                break
        
        if not inserted:
            self.request_queue.append(request)
        
        logger.info(f"Queued {priority.name} priority request for {model_id}")
    
    def update_model_health(self, model_id: str, health_score: float) -> None:
        """Update model health score based on recent performance."""
        if model_id in self.model_health:
            # Exponential moving average
            self.model_health[model_id] = (
                0.7 * self.model_health[model_id] + 0.3 * health_score
            )
            logger.debug(f"Updated {model_id} health score to {self.model_health[model_id]:.2f}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive rate limiter status."""
        status = {
            "timestamp": datetime.utcnow().isoformat(),
            "models": {},
            "queue_length": len(self.request_queue),
            "total_requests_queued": len(self.request_queue)
        }
        
        for model_id, bucket in self.model_buckets.items():
            bucket_status = bucket.get_status()
            status["models"][model_id] = {
                "health": self.model_health.get(model_id, 0),
                "cost_factor": self.model_costs.get(model_id, 1.0),
                "tokens_available": bucket_status["tokens"],
                "capacity": bucket_status["capacity"],
                "utilization": bucket_status["utilization"]
            }
        
        return status


class ExternalServiceRateLimiter:
    """Rate limiter for external services (Datadog, PagerDuty, Slack)."""
    
    def __init__(self):
        """Initialize external service rate limiter."""
        self.service_buckets: Dict[str, TokenBucket] = {}
        self.request_queues: Dict[str, deque] = defaultdict(deque)
        self._setup_service_buckets()
    
    def _setup_service_buckets(self) -> None:
        """Setup token buckets for external services."""
        for service, config in RATE_LIMITS.items():
            if service == "bedrock":  # Skip Bedrock, handled separately
                continue
            
            self.service_buckets[service] = TokenBucket(
                capacity=config["requests"] * 2,  # Allow burst
                refill_rate=config["requests"] / config["period"]
            )
    
    async def request_service_access(self, service: str, 
                                   priority: RequestPriority = RequestPriority.MEDIUM) -> bool:
        """
        Request access to external service.
        
        Args:
            service: Service name (slack, pagerduty, datadog, email)
            priority: Request priority
            
        Returns:
            True if access granted immediately
            
        Raises:
            RateLimitError: If service is not configured
        """
        if service not in self.service_buckets:
            raise RateLimitError(f"Service {service} not configured")
        
        bucket = self.service_buckets[service]
        
        # Try immediate access
        if await bucket.consume():
            return True
        
        # Queue high-priority requests
        if priority in [RequestPriority.HIGH, RequestPriority.CRITICAL]:
            await self._queue_service_request(service, priority)
            
            # Brief wait and retry
            await asyncio.sleep(0.5)
            if await bucket.consume():
                return True
        
        raise RateLimitError(f"Rate limit exceeded for {service}")
    
    async def _queue_service_request(self, service: str, priority: RequestPriority) -> None:
        """Queue service request for later processing."""
        request = QueuedRequest(
            request_id=f"svc_{service}_{int(time.time() * 1000)}",
            priority=priority,
            queued_at=datetime.utcnow(),
            service=service,
            metadata={}
        )
        
        queue = self.request_queues[service]
        
        # Insert based on priority
        inserted = False
        for i, queued_req in enumerate(queue):
            if priority.value > queued_req.priority.value:
                queue.insert(i, request)
                inserted = True
                break
        
        if not inserted:
            queue.append(request)
    
    async def batch_requests(self, service: str, requests: List[Dict[str, Any]], 
                           max_batch_size: int = 10) -> List[List[Dict[str, Any]]]:
        """
        Batch requests to optimize rate limit usage.
        
        Args:
            service: Service name
            requests: List of requests to batch
            max_batch_size: Maximum requests per batch
            
        Returns:
            List of batches
        """
        if service not in self.service_buckets:
            raise RateLimitError(f"Service {service} not configured")
        
        batches = []
        current_batch = []
        
        for request in requests:
            current_batch.append(request)
            
            if len(current_batch) >= max_batch_size:
                batches.append(current_batch)
                current_batch = []
        
        if current_batch:
            batches.append(current_batch)
        
        logger.info(f"Created {len(batches)} batches for {service} ({len(requests)} total requests)")
        return batches
    
    def get_service_status(self, service: str) -> Dict[str, Any]:
        """Get status for specific service."""
        if service not in self.service_buckets:
            return {"error": f"Service {service} not configured"}
        
        bucket_status = self.service_buckets[service].get_status()
        queue_length = len(self.request_queues[service])
        
        return {
            "service": service,
            "tokens_available": bucket_status["tokens"],
            "capacity": bucket_status["capacity"],
            "utilization": bucket_status["utilization"],
            "queue_length": queue_length,
            "status": "healthy" if bucket_status["utilization"] < 0.8 else "degraded"
        }


# Global rate limiter instances
bedrock_rate_limiter = BedrockRateLimitManager()
external_service_rate_limiter = ExternalServiceRateLimiter()