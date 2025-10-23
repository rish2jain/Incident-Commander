# Design Patterns and Guidelines

## Architectural Patterns

### Event-Driven Architecture
- **Event Store**: Kinesis for streaming, DynamoDB for persistence
- **Event Sourcing**: All state changes captured as events
- **CQRS**: Separate read and write models where applicable
- **Correlation IDs**: Track events across system boundaries

### Multi-Agent System
- **Agent Specialization**: Each agent has single responsibility
  - Detection: Alert correlation and incident detection
  - Diagnosis: Root cause analysis
  - Prediction: Trend forecasting and risk assessment
  - Resolution: Automated remediation
  - Communication: Stakeholder notifications

- **Agent Communication**: Message bus pattern via Redis
- **Consensus**: Byzantine fault-tolerant consensus for decisions
- **Coordination**: Orchestrator manages agent lifecycle

### Circuit Breaker Pattern
- External service protection (Bedrock, Slack, PagerDuty, Datadog)
- Configurable thresholds and fallback strategies
- Health monitoring and automatic recovery
- Agent-level circuit breakers for fault isolation

### Memory System (RAG)
- **Vector Search**: OpenSearch Serverless
- **Embeddings**: Bedrock Titan (1536 dimensions)
- **Pattern Storage**: Historical incident patterns
- **Similarity Search**: K-nearest neighbors for pattern matching

## Python Backend Patterns

### Async/Await
```python
# Prefer async for I/O-bound operations
async def fetch_data() -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

# Use asyncio.gather for concurrent operations
results = await asyncio.gather(
    fetch_data_1(),
    fetch_data_2(),
    fetch_data_3()
)
```

### Dependency Injection
```python
# Use dependency injection for testability
class DetectionAgent:
    def __init__(
        self,
        event_store: EventStore,
        message_bus: MessageBus,
        circuit_breaker: CircuitBreaker
    ):
        self.event_store = event_store
        self.message_bus = message_bus
        self.circuit_breaker = circuit_breaker
```

### Error Handling
```python
# Custom exception hierarchy
class SwarmAIException(Exception):
    """Base exception"""
    pass

class AgentException(SwarmAIException):
    """Agent-specific errors"""
    pass

# Structured error handling with logging
try:
    result = await dangerous_operation()
except AgentException as e:
    logger.error(
        "Agent operation failed",
        exc_info=True,
        extra={"correlation_id": correlation_id}
    )
    raise
```

### Configuration Management
```python
# Centralized config with validation
from pydantic_settings import BaseSettings

class Config(BaseSettings):
    aws_region: str = "us-east-1"
    redis_host: str = "localhost"
    redis_port: int = 6379
    
    class Config:
        env_file = ".env"
        
config = Config()
```

### Defensive Programming
```python
# Bounds checking and validation
def process_alerts(alerts: list[Alert]) -> list[Incident]:
    if len(alerts) > MAX_ALERTS:
        # Alert storm protection
        alerts = sample_alerts(alerts, MAX_ALERTS)
    
    # Depth limiting for recursion
    def correlate(alert, depth=0, max_depth=5):
        if depth >= max_depth:
            logger.warning("Max correlation depth reached")
            return []
        # ... correlation logic
    
    # Size limiting for logs
    if log_size > MAX_LOG_SIZE:
        log_data = intelligently_sample(log_data, MAX_LOG_SIZE)
```

## React/TypeScript Frontend Patterns

### Component Organization
```typescript
// Functional components with hooks
interface CardProps {
  title: string;
  children: React.ReactNode;
}

export function Card({ title, children }: CardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  return (
    <div className="card">
      <h3>{title}</h3>
      {children}
    </div>
  );
}
```

### Custom Hooks
```typescript
// Reusable logic in custom hooks
function useWebSocket(url: string) {
  const [data, setData] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  
  useEffect(() => {
    const ws = new WebSocket(url);
    
    ws.onopen = () => setIsConnected(true);
    ws.onmessage = (event) => setData(JSON.parse(event.data));
    ws.onclose = () => setIsConnected(false);
    
    return () => ws.close();
  }, [url]);
  
  return { data, isConnected };
}
```

### State Management
```typescript
// React hooks for local state
// Context API for shared state across components
const DashboardContext = createContext<DashboardState | null>(null);

export function useDashboard() {
  const context = useContext(DashboardContext);
  if (!context) {
    throw new Error("useDashboard must be used within DashboardProvider");
  }
  return context;
}
```

### Styling with Tailwind
```typescript
// Use Tailwind utility classes
<div className="flex items-center justify-between p-4 bg-gray-900 rounded-lg">
  <span className="text-white font-semibold">{title}</span>
</div>

// Use clsx/cn for conditional classes
import { cn } from "@/lib/utils";

<div className={cn(
  "base-class",
  isActive && "active-class",
  isError && "error-class"
)}>
```

## API Design Patterns

### RESTful Endpoints
```python
# Versioned API routes
app.include_router(incidents_router, prefix="/api/v1/incidents")

# Resource-based endpoints
@router.get("/incidents/{incident_id}")
async def get_incident(incident_id: str) -> IncidentResponse:
    """Get incident by ID"""
    pass

@router.post("/incidents")
async def create_incident(incident: IncidentCreate) -> IncidentResponse:
    """Create new incident"""
    pass
```

### WebSocket Patterns
```python
# Connection management
@app.websocket("/dashboard/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connection_id = str(uuid4())
    
    try:
        # Register connection
        await connection_manager.connect(connection_id, websocket)
        
        # Message loop
        while True:
            data = await websocket.receive_json()
            await handle_message(connection_id, data)
            
    except WebSocketDisconnect:
        await connection_manager.disconnect(connection_id)
```

### Response Schemas
```python
# Consistent response format with Pydantic
class APIResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

## Testing Patterns

### Unit Testing
```python
# Pytest with fixtures
@pytest.fixture
async def detection_agent():
    event_store = MockEventStore()
    message_bus = MockMessageBus()
    agent = DetectionAgent(event_store, message_bus)
    return agent

async def test_alert_correlation(detection_agent):
    # Arrange
    alerts = [create_test_alert() for _ in range(3)]
    
    # Act
    incidents = await detection_agent.correlate_alerts(alerts)
    
    # Assert
    assert len(incidents) == 1
    assert incidents[0].severity == "high"
```

### Integration Testing
```python
# Mark integration tests
@pytest.mark.integration
async def test_end_to_end_incident_flow():
    # Test complete flow from detection to resolution
    pass
```

### Mocking
```python
# Use pytest-mock for external dependencies
async def test_bedrock_call(mocker):
    mock_bedrock = mocker.patch("boto3.client")
    mock_bedrock.return_value.invoke_model.return_value = {
        "body": json.dumps({"response": "test"})
    }
    
    result = await call_bedrock_model("test prompt")
    assert result == "test"
```

## Performance Patterns

### Caching
```python
# Redis caching for expensive operations
async def get_incident_with_cache(incident_id: str) -> Incident:
    # Try cache first
    cached = await redis.get(f"incident:{incident_id}")
    if cached:
        return Incident.parse_raw(cached)
    
    # Fetch from database
    incident = await db.get_incident(incident_id)
    
    # Update cache
    await redis.setex(
        f"incident:{incident_id}",
        3600,  # TTL: 1 hour
        incident.json()
    )
    
    return incident
```

### Rate Limiting
```python
# Token bucket rate limiting
class RateLimiter:
    def __init__(self, requests_per_second: int):
        self.rate = requests_per_second
        self.tokens = requests_per_second
        self.last_update = time.time()
    
    async def acquire(self) -> bool:
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(
            self.rate,
            self.tokens + elapsed * self.rate
        )
        self.last_update = now
        
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False
```

### Batch Processing
```python
# Process items in batches
async def process_alerts_batch(alerts: list[Alert]):
    batch_size = 100
    for i in range(0, len(alerts), batch_size):
        batch = alerts[i:i + batch_size]
        await asyncio.gather(*[
            process_alert(alert) for alert in batch
        ])
```

## Security Patterns

### Input Validation
```python
# Pydantic for request validation
class IncidentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    severity: Literal["low", "medium", "high", "critical"]
    service_tier: int = Field(..., ge=1, le=3)
    
    @validator("title")
    def sanitize_title(cls, v):
        # Remove dangerous characters
        return v.replace("<", "").replace(">", "")
```

### Authentication
```python
# JWT-based authentication
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.get("/protected")
async def protected_route(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    # Verify JWT token
    payload = verify_jwt(token)
    return {"user_id": payload["sub"]}
```

## Logging Patterns

### Structured Logging
```python
# JSON-formatted logs with correlation IDs
logger.info(
    "Incident detected",
    extra={
        "incident_id": incident.id,
        "correlation_id": correlation_id,
        "severity": incident.severity,
        "service_tier": incident.service_tier,
        "business_impact": incident.business_impact
    }
)
```

## Guidelines Summary

### DO
✅ Use async/await for I/O operations
✅ Implement circuit breakers for external services
✅ Add correlation IDs for request tracing
✅ Use type hints everywhere
✅ Write tests for new features
✅ Document complex logic
✅ Validate all inputs
✅ Handle errors gracefully
✅ Use environment variables for config
✅ Follow SOLID principles

### DON'T
❌ Block the event loop with sync operations
❌ Ignore error handling
❌ Hard-code configuration values
❌ Skip input validation
❌ Leave debug print statements
❌ Create circular dependencies
❌ Expose sensitive data in logs
❌ Use global mutable state
❌ Write untested code
❌ Violate single responsibility principle