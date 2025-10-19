"""Centralized service container for runtime singletons."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Optional, AsyncIterator

from src.services.aws import AWSServiceFactory
from src.services.consensus import get_consensus_engine
from src.services.cost_optimizer import get_cost_optimizer, CostOptimizer
from src.services.scaling_manager import get_scaling_manager
from src.services.performance_optimizer import get_performance_optimizer
from src.services.meta_incident_handler import get_meta_incident_handler
from src.services.system_health_monitor import get_system_health_monitor
from src.services.realtime_integration import get_realtime_broadcaster
from src.services.message_bus import get_message_bus, ResilientMessageBus
from src.services.explainability import get_explainability_service, ExplainabilityService
from src.services.finops import get_finops_service, FinOpsService
from src.services.analytics import get_analytics_service, AnalyticsService
from src.services.operator_controls import get_operator_control_service, OperatorControlService
from src.services.rag_memory import ScalableRAGMemory
from src.services.byzantine_consensus import get_byzantine_consensus_engine
from src.orchestrator.swarm_coordinator import get_swarm_coordinator, AgentSwarmCoordinator


class ServiceContainer:
    """Lightweight dependency container for reusable singletons."""

    def __init__(self) -> None:
        self._aws_factory: Optional[AWSServiceFactory] = None
        self._coordinator: Optional[AgentSwarmCoordinator] = None
        self._message_bus: Optional[ResilientMessageBus] = None
        self._health_monitor = None
        self._meta_handler = None
        self._performance_optimizer = None
        self._scaling_manager = None
        self._cost_optimizer: Optional[CostOptimizer] = None
        self._broadcaster = None
        self._explainability: Optional[ExplainabilityService] = None
        self._finops: Optional[FinOpsService] = None
        self._analytics: Optional[AnalyticsService] = None
        self._operator_controls: Optional[OperatorControlService] = None
        self._rag_memory: Optional[ScalableRAGMemory] = None
        self._byzantine_consensus = None
        self._lock = asyncio.Lock()

    async def startup(self) -> None:
        async with self._lock:
            if self._aws_factory is not None:
                return

            self._aws_factory = AWSServiceFactory()
            self._coordinator = get_swarm_coordinator(service_factory=self._aws_factory)
            self._message_bus = get_message_bus(self._aws_factory)
            self._health_monitor = get_system_health_monitor(self._aws_factory)
            await self._health_monitor.start_monitoring()
            self._meta_handler = get_meta_incident_handler(self._aws_factory, self._health_monitor)
            self._performance_optimizer = await get_performance_optimizer()
            self._scaling_manager = await get_scaling_manager()
            self._cost_optimizer = await get_cost_optimizer()
            self._broadcaster = get_realtime_broadcaster(self._aws_factory)
            self._explainability = await get_explainability_service()
            self._finops = await get_finops_service()
            self._analytics = get_analytics_service()
            self._operator_controls = get_operator_control_service()
            self._rag_memory = ScalableRAGMemory(self._aws_factory)
            self._byzantine_consensus = get_byzantine_consensus_engine(self._aws_factory)

    async def shutdown(self) -> None:
        async with self._lock:
            if self._aws_factory is None:
                return

            try:
                if self._health_monitor is not None:
                    await self._health_monitor.stop_monitoring()
            finally:
                self._health_monitor = None

            try:
                if self._coordinator is not None:
                    await self._coordinator.shutdown()
            finally:
                self._coordinator = None

            try:
                if self._message_bus is not None:
                    await self._message_bus.shutdown()
            finally:
                self._message_bus = None

            if self._aws_factory is not None:
                await self._aws_factory.cleanup()
            self._aws_factory = None
            self._meta_handler = None
            self._performance_optimizer = None
            self._scaling_manager = None
            self._cost_optimizer = None
            self._broadcaster = None
            self._operator_controls = None
            self._rag_memory = None
            self._byzantine_consensus = None

    # Accessors -----------------------------------------------------------------

    @property
    def aws_factory(self) -> AWSServiceFactory:
        if self._aws_factory is None:
            raise RuntimeError("ServiceContainer.startup() must be called before use")
        return self._aws_factory

    @property
    def coordinator(self) -> AgentSwarmCoordinator:
        if self._coordinator is None:
            raise RuntimeError("Coordinator not initialized")
        return self._coordinator

    @property
    def health_monitor(self):
        if self._health_monitor is None:
            raise RuntimeError("health_monitor not initialized")
        return self._health_monitor

    @property
    def meta_handler(self):
        if self._meta_handler is None:
            raise RuntimeError("meta_handler not initialized")
        return self._meta_handler

    @property
    def performance_optimizer(self):
        if self._performance_optimizer is None:
            raise RuntimeError("performance_optimizer not initialized")
        return self._performance_optimizer

    @property
    def scaling_manager(self):
        if self._scaling_manager is None:
            raise RuntimeError("scaling_manager not initialized")
        return self._scaling_manager

    @property
    def cost_optimizer(self) -> CostOptimizer:
        if self._cost_optimizer is None:
            raise RuntimeError("Cost optimizer unavailable")
        return self._cost_optimizer

    @property
    def broadcaster(self):
        return self._broadcaster

    @property
    def explainability(self) -> ExplainabilityService:
        if self._explainability is None:
            raise RuntimeError("Explainability service unavailable")
        return self._explainability

    @property
    def finops(self) -> FinOpsService:
        if self._finops is None:
            raise RuntimeError("FinOps service unavailable")
        return self._finops

    @property
    def analytics(self) -> AnalyticsService:
        if self._analytics is None:
            raise RuntimeError("Analytics service unavailable")
        return self._analytics

    @property
    def operator_controls(self) -> OperatorControlService:
        if self._operator_controls is None:
            raise RuntimeError("Operator controls unavailable")
        return self._operator_controls

    @property
    def rag_memory(self) -> ScalableRAGMemory:
        if self._rag_memory is None:
            raise RuntimeError("RAG memory unavailable")
        return self._rag_memory

    @property
    def byzantine_consensus(self):
        if self._byzantine_consensus is None:
            raise RuntimeError("Byzantine consensus unavailable")
        return self._byzantine_consensus

    @asynccontextmanager
    async def lifespan(self) -> AsyncIterator["ServiceContainer"]:
        await self.startup()
        try:
            yield self
        finally:
            await self.shutdown()


_container = ServiceContainer()


def get_container() -> ServiceContainer:
    """Return global service container instance."""
    return _container
