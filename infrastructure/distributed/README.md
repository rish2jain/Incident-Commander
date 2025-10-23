# Distributed Platform Scaffolding

This directory captures the **Phase 2 distributed architecture** baseline for Incident Commander. It defines service boundaries, event schemas, and the AWS EventBridge routing plan needed to operate LangGraph services across multiple nodes.

## Contents

- `service_catalog.yaml` – declarative list of microservices with ownership metadata.
- `event_schemas/incident_events.json` – starter schema for EventBridge detail payloads.
- `topology.drawio` (placeholder) – diagram slot for the target topology.

## Next Steps

- Flesh out IaC modules (CDK/Terraform) that consume the catalog and event definitions.
- Attach health checks and scaling policies per service descriptor.
- Integrate with the Phase 1 LangGraph orchestrator to publish domain events.

