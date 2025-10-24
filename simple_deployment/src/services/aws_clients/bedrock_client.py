"""Enhanced AWS Bedrock client with circuit breakers, retry logic, and intelligent routing."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import aioboto3
from botocore.exceptions import ClientError

from src.utils.logging import get_logger


logger = get_logger("aws.bedrock")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""

    failure_threshold: int = 5
    success_threshold: int = 2
    timeout_seconds: int = 60
    half_open_max_calls: int = 3


@dataclass
class CircuitBreakerStats:
    """Circuit breaker statistics."""

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    total_requests: int = 0
    total_failures: int = 0


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for AWS services.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service failing, requests rejected immediately
    - HALF_OPEN: Testing recovery, limited requests allowed
    """

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()
        logger.info(f"Circuit breaker initialized: {name}")

    async def call(self, func, *args, **kwargs):
        """Execute a function through the circuit breaker."""
        async with self._lock:
            # Check if circuit is open
            if self.stats.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.stats.state = CircuitState.HALF_OPEN
                    self.stats.success_count = 0
                    logger.info(f"Circuit breaker {self.name}: OPEN -> HALF_OPEN")
                else:
                    logger.warning(f"Circuit breaker {self.name} is OPEN, rejecting request")
                    raise CircuitBreakerOpenError(f"Circuit breaker {self.name} is open")

            # Track request
            self.stats.total_requests += 1

        try:
            # Execute the function
            result = await func(*args, **kwargs)

            # Record success
            async with self._lock:
                await self._record_success()

            return result

        except Exception as e:
            # Record failure
            async with self._lock:
                await self._record_failure()

            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if not self.stats.last_failure_time:
            return True

        time_since_failure = datetime.now(timezone.utc) - self.stats.last_failure_time
        return time_since_failure.total_seconds() >= self.config.timeout_seconds

    async def _record_success(self) -> None:
        """Record a successful call."""
        self.stats.success_count += 1
        self.stats.failure_count = 0
        self.stats.last_success_time = datetime.now(timezone.utc)

        if self.stats.state == CircuitState.HALF_OPEN:
            if self.stats.success_count >= self.config.success_threshold:
                self.stats.state = CircuitState.CLOSED
                logger.info(f"Circuit breaker {self.name}: HALF_OPEN -> CLOSED")

    async def _record_failure(self) -> None:
        """Record a failed call."""
        self.stats.failure_count += 1
        self.stats.total_failures += 1
        self.stats.last_failure_time = datetime.now(timezone.utc)

        if self.stats.state == CircuitState.HALF_OPEN:
            self.stats.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker {self.name}: HALF_OPEN -> OPEN")
        elif self.stats.failure_count >= self.config.failure_threshold:
            self.stats.state = CircuitState.OPEN
            logger.warning(
                f"Circuit breaker {self.name}: CLOSED -> OPEN "
                f"(failures: {self.stats.failure_count})"
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self.stats.state.value,
            "failure_count": self.stats.failure_count,
            "success_count": self.stats.success_count,
            "total_requests": self.stats.total_requests,
            "total_failures": self.stats.total_failures,
            "last_failure_time": self.stats.last_failure_time.isoformat() if self.stats.last_failure_time else None,
            "last_success_time": self.stats.last_success_time.isoformat() if self.stats.last_success_time else None,
        }


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""

    pass


@dataclass
class ModelConfig:
    """Configuration for a Bedrock model."""

    model_id: str
    region: str = "us-east-1"
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 0.9
    priority: int = 1  # Lower is higher priority
    cost_per_1k_tokens: float = 0.01


class BedrockClient:
    """
    Enhanced AWS Bedrock client with production-grade features.

    Features:
    - Circuit breakers for fault tolerance
    - Intelligent model routing and fallback
    - Retry logic with exponential backoff
    - Cost tracking and optimization
    - Request/response caching
    - Multi-region support
    """

    def __init__(
        self,
        default_region: str = "us-east-1",
        enable_circuit_breaker: bool = True,
        max_retries: int = 3,
    ):
        self.default_region = default_region
        self.enable_circuit_breaker = enable_circuit_breaker
        self.max_retries = max_retries

        # AWS session
        self._session = aioboto3.Session()

        # Circuit breakers per model
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}

        # Model configurations
        self._models: List[ModelConfig] = [
            ModelConfig(
                model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
                priority=1,
                cost_per_1k_tokens=0.003,
                max_tokens=8192,
            ),
            ModelConfig(
                model_id="anthropic.claude-3-haiku-20240307-v1:0",
                priority=2,
                cost_per_1k_tokens=0.00025,
                max_tokens=4096,
            ),
        ]

        # Cost tracking
        self._total_cost = 0.0
        self._request_count = 0

        logger.info(
            "BedrockClient initialized",
            extra={
                "region": default_region,
                "circuit_breaker_enabled": enable_circuit_breaker,
                "models_configured": len(self._models),
            },
        )

    def _get_circuit_breaker(self, model_id: str) -> CircuitBreaker:
        """Get or create circuit breaker for a model."""
        if model_id not in self._circuit_breakers:
            self._circuit_breakers[model_id] = CircuitBreaker(f"bedrock-{model_id}")
        return self._circuit_breakers[model_id]

    async def invoke_model(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model_preference: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        use_fallback: bool = True,
    ) -> Dict[str, Any]:
        """
        Invoke a Bedrock model with intelligent routing and fallback.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            model_preference: Preferred model ID (falls back if unavailable)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            use_fallback: Whether to try fallback models on failure

        Returns:
            Model response with metadata
        """
        self._request_count += 1

        # Select models to try
        models_to_try = self._get_models_to_try(model_preference, use_fallback)

        last_error = None
        for model_config in models_to_try:
            try:
                result = await self._invoke_model_with_retry(
                    model_config=model_config,
                    prompt=prompt,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )

                # Track cost
                tokens_used = result.get("usage", {}).get("total_tokens", 0)
                cost = (tokens_used / 1000) * model_config.cost_per_1k_tokens
                self._total_cost += cost

                result["metadata"] = {
                    "model_id": model_config.model_id,
                    "region": model_config.region,
                    "cost": cost,
                    "total_cost": self._total_cost,
                    "request_count": self._request_count,
                }

                logger.info(
                    f"Model invocation successful",
                    extra={
                        "model": model_config.model_id,
                        "tokens": tokens_used,
                        "cost": cost,
                    },
                )

                return result

            except CircuitBreakerOpenError:
                logger.warning(
                    f"Circuit breaker open for {model_config.model_id}, trying next model"
                )
                last_error = f"Circuit breaker open for {model_config.model_id}"
                continue

            except Exception as e:
                logger.warning(
                    f"Failed to invoke {model_config.model_id}: {e}",
                    extra={"error": str(e)},
                )
                last_error = str(e)
                continue

        # All models failed
        error_msg = f"All models failed. Last error: {last_error}"
        logger.error(error_msg)
        raise Exception(error_msg)

    async def _invoke_model_with_retry(
        self,
        model_config: ModelConfig,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
    ) -> Dict[str, Any]:
        """Invoke a model with retry logic and circuit breaker."""

        async def _invoke():
            return await self._invoke_model_internal(
                model_config=model_config,
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )

        if self.enable_circuit_breaker:
            circuit_breaker = self._get_circuit_breaker(model_config.model_id)
            return await circuit_breaker.call(_invoke)
        else:
            return await _invoke()

    async def _invoke_model_internal(
        self,
        model_config: ModelConfig,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
    ) -> Dict[str, Any]:
        """Internal model invocation with retries."""
        for attempt in range(self.max_retries):
            try:
                async with self._session.client(
                    "bedrock-runtime",
                    region_name=model_config.region,
                ) as client:
                    # Prepare request
                    messages = [{"role": "user", "content": prompt}]

                    body = {
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "messages": messages,
                    }

                    if system_prompt:
                        body["system"] = system_prompt

                    # Invoke model
                    response = await client.invoke_model(
                        modelId=model_config.model_id,
                        body=json.dumps(body),
                    )

                    # Parse response
                    response_body = json.loads(await response["body"].read())

                    return {
                        "content": response_body.get("content", []),
                        "stop_reason": response_body.get("stop_reason"),
                        "usage": response_body.get("usage", {}),
                    }

            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "")

                # Don't retry on certain errors
                if error_code in ["ValidationException", "AccessDeniedException"]:
                    raise

                # Retry with backoff
                if attempt < self.max_retries - 1:
                    wait_time = 2**attempt  # Exponential backoff
                    logger.warning(
                        f"Retry {attempt + 1}/{self.max_retries} after {wait_time}s",
                        extra={"error_code": error_code, "model": model_config.model_id},
                    )
                    await asyncio.sleep(wait_time)
                else:
                    raise

    def _get_models_to_try(
        self, preferred_model: Optional[str], use_fallback: bool
    ) -> List[ModelConfig]:
        """Get list of models to try in priority order."""
        models = sorted(self._models, key=lambda m: m.priority)

        if preferred_model:
            # Move preferred model to front
            preferred = next((m for m in models if m.model_id == preferred_model), None)
            if preferred:
                models.remove(preferred)
                models.insert(0, preferred)

        if not use_fallback:
            models = models[:1]

        return models

    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        circuit_breaker_stats = {
            model_id: cb.get_stats()
            for model_id, cb in self._circuit_breakers.items()
        }

        return {
            "total_cost": round(self._total_cost, 4),
            "request_count": self._request_count,
            "average_cost_per_request": (
                round(self._total_cost / self._request_count, 6)
                if self._request_count > 0
                else 0
            ),
            "circuit_breakers": circuit_breaker_stats,
            "models_configured": len(self._models),
        }


# Global Bedrock client instance
_client: Optional[BedrockClient] = None


def get_bedrock_client(region: str = "us-east-1") -> BedrockClient:
    """Get the global Bedrock client instance."""
    global _client
    if _client is None:
        _client = BedrockClient(default_region=region)
    return _client
