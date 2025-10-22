# Autonomous Incident Commander – Hackathon Demo Playbook

## 1. Fast Start Checklist (60 Seconds)

```bash
pip install -r demo_requirements.txt
make test-manual
python start_live_demo.py
```

- Browser auto-opens to the enhanced dashboard.
- Trigger **Database Cascade** to showcase full agent coordination.
- Keep `validate_demo_performance.py` handy to reassure judges about reliability.

## 2. Demo Narrative (3 Minutes)

### Minute 0–1: Set the Stakes
- Highlight the live **Business Impact Meter** (cost avoidance counter).
- Call out MTTR comparison widget (Autonomous 2.8 min vs manual 30+ min).
- Mention real-time consensus among the five specialized agents.

### Minute 1–2: Trigger & Observe
- Start the **Database Cascade** scenario.
- Verbally map what each agent is doing via the activity stream.
- Point at WebSocket ticker: <100 ms latency, judges see “why it’s believable”.

### Minute 2–3: Close the Loop
- Show the **Resolution Timeline** reaching completion inside three minutes.
- Summarize business impact: “$103K+ saved in this single incident.”
- Offer to drill into logs, consensus decisions, or compliance artifacts as needed.

## 3. Core Artifacts

| Artifact | Purpose | Location |
| --- | --- | --- |
| Architecture Deep Dive | Diagram + flow reference | `docs/hackathon/architecture.md` |
| Compliance Snapshot | SOC2-ready controls checklist | `docs/hackathon/compliance_overview.md` |
| Dashboard Setup | Local launch & troubleshooting | `docs/hackathon/dashboard_setup.md` |
| Value Pitch | Talking points for judges | `docs/hackathon/dashboard_value_pitch.md` |

## 4. Scenario Reference

| Scenario | Key Talking Point | Metric to Watch |
| --- | --- | --- |
| Database Cascade | Cross-agent consensus & rollback | MTTR, cost savings |
| DDoS Flood | Auto-scaling + circuit breakers | Active connections |
| Memory Leak | Predictive detection before outage | Predicted vs actual load |
| API Overload | Rate limiting + prioritization | Request backlog |
| Storage Failure | Disaster recovery drill | Recovery timer |

Tip: rehearse “why it matters” stories for two scenarios beyond the default cascade so judges can pick one ad hoc.

## 5. Judge Q&A Cheat Sheet

- **Security?** Point to compliance checklist and `SecurityService` monitoring hooks.
- **Scalability?** Reference `validate_demo_performance.py` (1000+ incidents) and load-testing metrics.
- **Reliability?** Mention chaos experiments in `FaultToleranceShowcase` and WebSocket failover.
- **Extensibility?** New agents plug into `AgentSwarmCoordinator` via capability registration.

## 6. Troubleshooting Quick Wins

- **No WebSocket feed?** Run `python validate_websocket.py` and restart `uvicorn` if needed.
- **Dashboard assets missing?** Run `make test-manual` and review failures in `tests/manual/test_dashboard_components.py`.
- **AWS creds errors?** Ensure `.env` pulls LocalStack endpoints (`AWS_ENDPOINT_URL=http://localhost:4566`).

## 7. Closing Statement Template

> “Autonomous Incident Commander shrinks critical MTTR from 30+ minutes to under 3, saves six figures per incident, and keeps human responders focused on strategy. You just watched five agents collaborate live with full security and compliance guardrails.”
