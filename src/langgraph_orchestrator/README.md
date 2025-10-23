# LangGraph Orchestrator

This package contains the **Phase 1 LangGraph migration** for Incident Commander. The goal is to replace the bespoke `AgentSwarmCoordinator` with a composable `StateGraph` implementation that can run locally today and be promoted to the LangGraph Platform in Phase 2.

## Quick Start

```python
from src.langgraph_orchestrator import IncidentResponseGraph
from src.models.incident import Incident, IncidentSeverity, IncidentStatus, BusinessImpact, IncidentMetadata, ServiceTier

graph = IncidentResponseGraph()

incident = Incident(
    title="Elevated error rates",
    description="Checkout requests are timing out for US-East customers",
    severity=IncidentSeverity.HIGH,
    status=IncidentStatus.DETECTED,
    business_impact=BusinessImpact(service_tier=ServiceTier.TIER_1, affected_users=1200),
    metadata=IncidentMetadata(source_system="synthetic-monitoring"),
)

state = await graph.run(incident, context={"telemetry_sources": ["cloudwatch", "app_traces"]})
print(state.consensus)
```

### Node Topology

```
START → detection → analysis (diagnosis+prediction) → consensus → resolution → communication → END
```

- **Parallel analysis**: diagnosis and prediction execute concurrently within the analysis hub.
- **PBFT consensus**: the node delegates to `ByzantineFaultTolerantConsensus`, with a weighted fallback if PBFT is unavailable.
- **Message bus hooks**: detection and communication nodes emit optional Redis/SQS events when a message bus is supplied.

## Files

- `incident_graph.py` – builds and executes the LangGraph `StateGraph`.
- `state_schema.py` – typed state, timeline helpers, and node result contracts.
- `agents/` – concrete LangGraph nodes for detection, diagnosis, prediction, consensus, resolution, and communication.
- `utils/` – routing helpers and streaming stubs used by the graph.

## Phase 1 Deliverables Covered

- ✅ LangGraph scaffolding with nodes and shared state schema.
- ✅ Parallel diagnosis/prediction execution with normalized telemetry.
- ✅ PBFT integration and fallback consensus path.
- ✅ Message bus adapter hooks for detection/communication.

## Next Steps

- Integrate real agent implementations instead of heuristics.
- Expand test coverage with parity tests against the legacy coordinator.
- Wire LangGraph streaming callbacks to the existing real-time dashboard.

