# Autonomous Incident Commander API Documentation

## Overview

The Autonomous Incident Commander provides a comprehensive REST API for managing incident detection, diagnosis, and resolution through multi-agent coordination. This documentation covers all available endpoints, authentication, and usage examples.

## Base URL

```
Production: https://api.incident-commander.com/v1
Development: http://localhost:8000
```

## Authentication

All API requests require authentication using API keys:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     https://api.incident-commander.com/v1/incidents
```

## Core Endpoints

### Incident Management

#### Trigger New Incident

```http
POST /incidents/trigger
```

Create and process a new incident through the agent swarm.

**Request Body:**

```json
{
  "title": "Database Connection Pool Exhaustion",
  "description": "Critical database connection pool exhausted causing cascade failures",
  "severity": "critical",
  "service_tier": "tier_1",
  "affected_users": 50000,
  "revenue_impact_per_minute": 2000.0,
  "source_system": "datadog",
  "tags": {
    "environment": "production",
    "service": "user-database"
  }
}
```

**Response:**

```json
{
  "incident_id": "inc_2024_001",
  "status": "processing",
  "message": "Incident is being processed by agent swarm",
  "estimated_completion_minutes": 3,
  "cost_per_minute": 2000.0
}
```

#### Get Incident Status

```http
GET /incidents/{incident_id}
```

Retrieve current status and details of an incident.

**Response:**

```json
{
  "incident_id": "inc_2024_001",
  "status": "resolved",
  "phase": "completed",
  "start_time": "2024-01-01T10:00:00Z",
  "end_time": "2024-01-01T10:02:45Z",
  "duration_seconds": 165,
  "consensus_decision": {
    "selected_action": "restart_database_service",
    "final_confidence": 0.92,
    "requires_human_approval": false
  },
  "business_impact": {
    "total_cost": 5500.0,
    "affected_users": 50000,
    "sla_breach": false
  }
}
```

#### Get Incident Timeline

```http
GET /incidents/{incident_id}/timeline
```

Retrieve detailed timeline of incident processing.

**Response:**

```json
{
  "incident_id": "inc_2024_001",
  "timeline": [
    {
      "timestamp": "2024-01-01T10:00:00Z",
      "event": "incident_started",
      "description": "Incident processing started",
      "phase": "detection"
    },
    {
      "timestamp": "2024-01-01T10:00:30Z",
      "event": "agent_completed",
      "description": "Detection agent completed",
      "agent": "detection_agent",
      "duration_seconds": 30,
      "recommendations_count": 1
    }
  ],
  "total_events": 8,
  "processing_duration_seconds": 165
}
```

### Agent Management

#### Get Agent Status

```http
GET /agents/status
```

Retrieve status of all registered agents.

**Response:**

```json
{
  "agents": {
    "detection_agent": {
      "is_healthy": true,
      "processing_count": 5,
      "error_count": 0,
      "last_activity": "2024-01-01T10:00:00Z"
    }
  },
  "metrics": {
    "total_incidents": 150,
    "success_rate": 0.96,
    "average_processing_time": 142.5
  }
}
```

### System Health

#### System Health Check

```http
GET /health
```

Basic system health check.

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T10:00:00Z",
  "environment": "production",
  "services": {
    "api": "healthy",
    "event_store": "healthy",
    "agents": "healthy",
    "consensus_engine": "healthy"
  }
}
```

#### Detailed System Status

```http
GET /status
```

Comprehensive system status including circuit breakers and rate limiters.

### Performance Optimization (Task 15)

#### Get Performance Metrics

```http
GET /performance/metrics
```

Retrieve comprehensive performance optimization metrics.

**Response:**

```json
{
  "performance_optimization": {
    "connection_pools": {
      "aws": 0.65,
      "datadog": 0.45
    },
    "cache_hit_rates": {
      "incident_patterns": 0.85,
      "agent_configs": 0.92
    },
    "memory_usage_percent": 72.5,
    "gc_collections": 15
  },
  "scaling": {
    "incidents_per_minute": 12.5,
    "agent_utilization": {
      "detection": 0.68,
      "diagnosis": 0.72
    }
  },
  "cost_optimization": {
    "current_hourly_cost": 145.5,
    "projected_daily_cost": 3492.0,
    "cost_savings_achieved": 892.3
  }
}
```

#### Get Performance Recommendations

```http
GET /performance/recommendations
```

Get optimization recommendations.

#### Trigger Scaling Optimization

```http
POST /scaling/optimize
```

Trigger scaling optimization based on current load.

#### Trigger Cost Optimization

```http
POST /cost/optimize
```

Trigger cost optimization analysis and actions.

### Demo Scenarios

#### Run Demo Scenario

```http
POST /demo/scenarios/{scenario_name}
```

Execute predefined demo scenarios.

Available scenarios:

- `database_cascade`
- `ddos_attack`
- `memory_leak`
- `api_overload`
- `storage_failure`

**Response:**

```json
{
  "scenario": "database_cascade",
  "status": "started",
  "incident_id": "demo_inc_001",
  "estimated_duration_minutes": 3,
  "cost_per_minute": 2000.0,
  "demo_features": {
    "real_time_mttr": true,
    "cost_accumulation": true,
    "agent_coordination": true
  }
}
```

## Error Handling

All API endpoints return standard HTTP status codes:

- `200 OK` - Request successful
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Authentication required
- `404 Not Found` - Resource not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

Error responses include details:

```json
{
  "error": "Incident not found",
  "type": "NotFoundError",
  "incident_id": "invalid_id",
  "timestamp": "2024-01-01T10:00:00Z"
}
```

## Rate Limits

API endpoints are rate limited:

- **Incident Creation**: 10 requests/minute
- **Status Queries**: 100 requests/minute
- **Demo Scenarios**: 5 requests/minute

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Webhooks

Configure webhooks to receive incident status updates:

```http
POST /webhooks/configure
```

**Request:**

```json
{
  "url": "https://your-app.com/webhooks/incidents",
  "events": ["incident.resolved", "incident.escalated"],
  "secret": "your_webhook_secret"
}
```

Webhook payloads include incident details and status changes.

## SDKs and Libraries

Official SDKs available:

- **Python**: `pip install incident-commander-sdk`
- **JavaScript**: `npm install @incident-commander/sdk`
- **Go**: `go get github.com/incident-commander/go-sdk`

## Examples

### Python SDK

```python
from incident_commander import IncidentCommander

client = IncidentCommander(api_key="your_api_key")

# Trigger incident
incident = client.incidents.create({
    "title": "Database Issue",
    "severity": "high",
    "affected_users": 1000
})

# Monitor progress
status = client.incidents.get(incident.id)
print(f"Status: {status.phase}, Duration: {status.duration_seconds}s")
```

### JavaScript SDK

```javascript
const { IncidentCommander } = require("@incident-commander/sdk");

const client = new IncidentCommander({ apiKey: "your_api_key" });

// Trigger incident
const incident = await client.incidents.create({
  title: "API Gateway Overload",
  severity: "critical",
  affectedUsers: 25000,
});

// Get timeline
const timeline = await client.incidents.getTimeline(incident.id);
console.log(`Timeline events: ${timeline.totalEvents}`);
```

## Support

- **Documentation**: https://docs.incident-commander.com
- **API Status**: https://status.incident-commander.com
- **Support**: support@incident-commander.com
- **GitHub**: https://github.com/incident-commander/api
