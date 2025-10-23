# API Documentation - Autonomous Incident Commander

## Base URL

- **Production**: `https://h8xlzr74h8.execute-api.us-east-1.amazonaws.com`
- **Local**: `http://localhost:8000`

## Core Endpoints

### Health & Status

```bash
GET /health
# Returns system health status

GET /demo/stats
# Returns business metrics and ROI data

GET /observability/telemetry
# Returns agent performance metrics
```

### Incident Management

```bash
POST /incidents/trigger
# Triggers incident simulation
# Body: { "incident_type": "database_failure", "severity": "high" }

GET /incidents/{incident_id}
# Returns incident details and resolution status

GET /incidents/{incident_id}/agents
# Returns agent coordination and consensus data
```

### Agent Coordination

```bash
GET /agents/status
# Returns status of all 5 agents

GET /agents/{agent_name}/confidence
# Returns confidence scores and decision rationale

POST /agents/consensus
# Triggers Byzantine consensus process
```

### Dashboard Data

```bash
GET /dashboard/demo/data
# Returns demo dashboard metrics

GET /dashboard/transparency/data
# Returns AI transparency data

GET /dashboard/ops/data
# Returns operations monitoring data
```

### AWS AI Services

```bash
GET /real-aws-ai/prize-eligibility
# Returns AWS AI service integration status

GET /amazon-q/status
# Returns Amazon Q Business integration status

GET /nova-act/status
# Returns Nova Act integration status

GET /strands/status
# Returns Strands SDK integration status
```

## WebSocket Endpoints

### Real-time Updates

```javascript
// Connect to WebSocket
const ws = new WebSocket("ws://localhost:8000/ws");

// Message types:
// - incident_update: Real-time incident status
// - agent_consensus: Agent decision updates
// - metrics_update: Business metrics changes
// - system_health: System status updates
```

## Authentication

### Development

No authentication required for local development.

### Production

API key required for production endpoints:

```bash
curl -H "X-API-Key: your-api-key" https://your-api-url/endpoint
```

## Response Format

### Success Response

```json
{
  "status": "success",
  "data": { ... },
  "timestamp": "2025-10-23T10:00:00Z"
}
```

### Error Response

```json
{
  "status": "error",
  "message": "Error description",
  "code": "ERROR_CODE",
  "timestamp": "2025-10-23T10:00:00Z"
}
```

## Rate Limits

- **General endpoints**: 100 requests/minute
- **Incident triggers**: 10 requests/minute
- **WebSocket connections**: 5 concurrent connections

## Examples

### Trigger Incident Simulation

```bash
curl -X POST http://localhost:8000/incidents/trigger \
  -H "Content-Type: application/json" \
  -d '{"incident_type": "database_failure", "severity": "high"}'
```

### Get Business Metrics

```bash
curl http://localhost:8000/demo/stats
```

### Check AWS AI Integration

```bash
curl http://localhost:8000/real-aws-ai/prize-eligibility
```

---

**Total Endpoints**: 50+ comprehensive API endpoints  
**Real-time Features**: WebSocket integration with 0.2ms latency  
**AWS Integration**: All 8 AWS AI services operational
