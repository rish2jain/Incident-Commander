from datetime import datetime
from typing import Awaitable

import pytest


pytestmark = [
    pytest.mark.filterwarnings(
        "ignore:.*:pydantic.warnings.PydanticDeprecatedSince20"
    )
]


@pytest.fixture
def anyio_backend():
    return "asyncio"


class StubAWSFactory:
    def __init__(self):
        self.cleaned = False

    async def cleanup(self):
        self.cleaned = True


class StubCoordinator:
    def __init__(self):
        self.registered = []
        self.shutdown_called = False

    async def register_agent(self, agent):
        self.registered.append(agent)

    async def shutdown(self):
        self.shutdown_called = True

    async def health_check(self) -> bool:
        return True


class StubHealthMonitor:
    def __init__(self):
        self.started = False
        self.stopped = False

    async def start_monitoring(self):
        self.started = True

    async def stop_monitoring(self):
        self.stopped = True

    def get_current_health_status(self):
        return {"overall_status": "healthy", "timestamp": datetime.utcnow().isoformat()}


class StubMetaHandler:
    pass


class StubConsensus:
    pass


class StubOptimizer:
    pass


class StubScalingManager:
    pass


class StubCostOptimizer:
    pass


@pytest.mark.anyio("asyncio")
async def test_lifespan_startup_and_shutdown(monkeypatch):
    import src.main as main
    from src.models.agent import AgentType

    class StubAgent:
        def __init__(self, name: str, *args, **kwargs):
            self.name = name
            key = "detection" if "detection" in name else (
                "diagnosis" if "diagnosis" in name else (
                    "prediction" if "prediction" in name else (
                        "resolution" if "resolution" in name else "communication"
                    )
                )
            )
            type_map = {
                "detection": AgentType.DETECTION,
                "diagnosis": AgentType.DIAGNOSIS,
                "prediction": AgentType.PREDICTION,
                "resolution": AgentType.RESOLUTION,
                "communication": AgentType.COMMUNICATION,
            }
            self.agent_type = type_map[key]
            self.is_healthy = True
            self.processing_count = 0
            self.error_count = 0
            self.last_heartbeat = datetime.utcnow()

        async def process_incident(self, incident):
            return None

        async def health_check(self):
            return True

    stub_factory = StubAWSFactory()
    stub_coordinator = StubCoordinator()
    stub_monitor = StubHealthMonitor()
    stub_meta = StubMetaHandler()
    stub_consensus = StubConsensus()
    stub_optimizer = StubOptimizer()
    stub_scaling = StubScalingManager()
    stub_cost = StubCostOptimizer()

    monkeypatch.setattr(main, "AWSServiceFactory", lambda: stub_factory)
    monkeypatch.setattr(main, "get_swarm_coordinator", lambda service_factory=None: stub_coordinator)
    monkeypatch.setattr(main, "ScalableRAGMemory", lambda service_factory=None: object())
    monkeypatch.setattr(main, "get_system_health_monitor", lambda _factory: stub_monitor)
    monkeypatch.setattr(main, "get_meta_incident_handler", lambda _factory, _monitor: stub_meta)
    monkeypatch.setattr(main, "get_byzantine_consensus_engine", lambda _factory: stub_consensus)

    async def _return_optimizer() -> StubOptimizer:
        return stub_optimizer

    async def _return_scaling() -> StubScalingManager:
        return stub_scaling

    async def _return_cost() -> StubCostOptimizer:
        return stub_cost

    monkeypatch.setattr(main, "get_performance_optimizer", _return_optimizer)
    monkeypatch.setattr(main, "get_scaling_manager", _return_scaling)
    monkeypatch.setattr(main, "get_cost_optimizer", _return_cost)

    monkeypatch.setattr(main, "RobustDetectionAgent", lambda name: StubAgent(name))
    monkeypatch.setattr(main, "HardenedDiagnosisAgent", lambda name: StubAgent(name))
    monkeypatch.setattr(main, "PredictionAgent", lambda aws, rag, name: StubAgent(name))
    monkeypatch.setattr(main, "SecureResolutionAgent", lambda aws, name: StubAgent(name))
    monkeypatch.setattr(main, "ResilientCommunicationAgent", lambda name: StubAgent(name))

    # Reset globals to ensure clean run
    main._background_tasks.clear()
    main.aws_factory = None
    main.coordinator_instance = None
    main.rag_memory_instance = None
    main.health_monitor_instance = None
    main.meta_incident_handler_instance = None
    main.byzantine_consensus_instance = None
    main.performance_optimizer_instance = None
    main.scaling_manager_instance = None
    main.cost_optimizer_instance = None

    async with main.app.router.lifespan_context(main.app):
        assert stub_monitor.started is True
        assert len(stub_coordinator.registered) == 5
        assert main.coordinator_instance is stub_coordinator

    # After shutdown services should be cleaned up
    assert stub_monitor.stopped is True
    assert stub_coordinator.shutdown_called is True
    assert stub_factory.cleaned is True
    assert main.coordinator_instance is None
    assert main.aws_factory is None
    assert not main._background_tasks
