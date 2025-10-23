# SwarmAI - Design Patterns and Guidelines

## Core Architectural Patterns

### 1. Multi-Agent System Pattern
**Implementation**: Byzantine Fault-Tolerant Agent Coordination
- **5 Specialized Agents**: Each with single responsibility
  - Detection: Alert correlation (weight: 0.2)
  - Diagnosis: Root cause analysis (weight: 0.4, highest)
  - Prediction: Trend forecasting (weight: 0.3)
  - Resolution: Automated remediation (weight: 0.1)
  - Communication: Stakeholder notifications
- **Weighted Consensus**: Agents vote on decisions with expertise-based weights
- **Byzantine Tolerance**: System handles up to 33% compromised agents
- **Circuit Breakers**: Isolate failing agents without cascading failures

### 2. Event Sourcing Pattern
**Implementation**: Kinesis + DynamoDB Event Store
- **Event Stream**: Kinesis for real-time event ingestion
- **Event Persistence**: DynamoDB for immutable event log
- **Optimistic Locking**: Version-based concurrency control
- **Event Replay**: Reconstruct state from event history
- **Cryptographic Integrity**: Hash-based event verification
- **Partition Keys**: Incident ID for event distribution

### 3. Circuit Breaker Pattern
**Implementation**: Resilient Inter-Agent Communication
- **Failure Threshold**: 5 consecutive failures trigger OPEN state
- **Cooldown Period**: 30 seconds before attempting recovery
- **Health Monitoring**: Per-agent circuit breaker tracking
- **Graceful Degradation**: Multi-level fallback chains
- **Rate Limiting**: Bedrock and external service protection

### 4. CQRS (Command Query Responsibility Segregation)
**Implementation**: Separate Read and Write Paths
- **Write Side**: Event store for state mutations
- **Read Side**: DynamoDB projections for queries
- **Real-time Updates**: WebSocket for live dashboard data
- **Analytics**: Separate analytics database (planned)

### 5. Repository Pattern
**Implementation**: Data Access Abstraction
- **Interfaces**: Core abstractions in `src/interfaces/`
- **Implementations**: Concrete classes in `src/services/`
- **Dependency Injection**: Container pattern for flexibility
- **Testing**: Easy mocking and unit testing

### 6. Saga Pattern (Planned)
**Implementation**: Distributed Transaction Management
- **Compensation Logic**: Rollback mechanisms for partial failures
- **State Machines**: Step Functions for orchestration
- **Idempotency**: Safe retry of operations

## Security Design Patterns

### 1. Zero-Trust Architecture
- **Never Trust, Always Verify**: All requests authenticated and authorized
- **Least Privilege**: IAM roles with minimal permissions
- **Defense in Depth**: Multiple security layers
- **Input Validation**: Pydantic models with sanitization

### 2. Audit Logging Pattern
- **Cryptographic Integrity**: Hash-based tamper detection
- **Structured Logging**: JSON format with correlation IDs
- **Compliance**: SOC2, GDPR, HIPAA requirements
- **Immutable Logs**: Write-once, read-many pattern

### 3. Secret Management Pattern
- **AWS Secrets Manager**: Centralized secret storage
- **Automatic Rotation**: Scheduled credential updates
- **Environment-based**: Different secrets per environment
- **Never in Code**: No hardcoded credentials

## Code Organization Patterns

### 1. Layered Architecture
```
API Layer (FastAPI routers)
    ↓
Service Layer (Business logic)
    ↓
Data Layer (Event store, databases)
    ↓
Infrastructure Layer (AWS services)
```

### 2. Dependency Injection
- **Container Pattern**: `src/services/container.py`
- **Singleton Services**: Shared instances for stateful services
- **Scoped Services**: Per-request instances
- **Transient Services**: New instance per use

### 3. Interface Segregation
- **Small Interfaces**: Single responsibility per interface
- **Composition**: Combine interfaces for complex needs
- **Testability**: Easy to mock individual interfaces

### 4. Factory Pattern
- **Agent Factory**: Create agents with proper configuration
- **Client Factory**: AWS service client creation
- **Configuration Factory**: Environment-specific config

## Frontend Patterns (Next.js/React)

### 1. Component Composition
- **Atomic Design**: Atoms → Molecules → Organisms → Templates → Pages
- **Radix UI Primitives**: Accessible, unstyled base components
- **Custom Components**: Built on top of Radix primitives
- **Shared Components**: Reusable across all 3 dashboards

### 2. Server Components (Next.js 14)
- **Default Server**: Components render on server by default
- **'use client'**: Explicit client component marking
- **Data Fetching**: Server-side data loading
- **Streaming**: Progressive rendering with Suspense

### 3. State Management
- **React Hooks**: useState, useEffect, useContext
- **Context API**: Global state (theme, auth)
- **WebSocket State**: Real-time incident updates
- **Local State**: Component-specific state

### 4. Custom Hooks
- **useWebSocket**: WebSocket connection management
- **useIncident**: Incident data fetching
- **useTheme**: Theme switching logic
- **useAuth**: Authentication state

## Testing Patterns

### 1. Test Pyramid
- **Unit Tests**: 60% - Individual function testing
- **Integration Tests**: 30% - Component interaction
- **E2E Tests**: 10% - Full system workflows

### 2. Test Fixtures
- **conftest.py**: Pytest fixtures for shared test data
- **LocalStack**: AWS service mocking
- **Moto**: Alternative AWS mocking
- **Pytest-mock**: Function mocking and patching

### 3. Test Markers
- **@pytest.mark.unit**: Unit tests
- **@pytest.mark.integration**: Integration tests
- **@pytest.mark.e2e**: End-to-end tests
- **@pytest.mark.slow**: Slow-running tests
- **@pytest.mark.agent**: Agent-specific tests
- **@pytest.mark.manual**: Manual demo tests

## Error Handling Patterns

### 1. Custom Exception Hierarchy
**Location**: `src/utils/exceptions.py`
- **Base Exception**: All custom exceptions inherit from base
- **Specific Exceptions**: AgentError, EventStoreError, etc.
- **Error Context**: Rich error messages with context
- **HTTP Mapping**: Exception to HTTP status code mapping

### 2. Defensive Programming
- **Bounds Checking**: Validate inputs before processing
- **Size Limits**: Prevent memory exhaustion (e.g., 100MB log limit)
- **Depth Limits**: Prevent infinite recursion (e.g., max depth 5)
- **Timeout Protection**: All async operations have timeouts
- **Circular Reference Detection**: Prevent infinite loops

### 3. Graceful Degradation
- **Fallback Chains**: Primary → Secondary → Tertiary
- **Partial Functionality**: Degrade features, not entire system
- **Circuit Breakers**: Isolate failures automatically
- **Retry Logic**: Exponential backoff with jitter

## Performance Patterns

### 1. Caching Strategy
- **Redis**: Distributed cache for agent communication
- **Application Cache**: In-memory caching for hot data
- **CDN**: Static asset caching (CloudFront)
- **Browser Cache**: Client-side caching with versioning

### 2. Async/Await Pattern
- **Async Services**: All I/O operations are async
- **Concurrent Execution**: Multiple operations in parallel
- **Connection Pooling**: Reuse database connections
- **Batch Operations**: Group multiple writes

### 3. Pagination Pattern
- **Cursor-based**: For large result sets
- **Limit/Offset**: For small result sets
- **Virtual Scrolling**: Frontend optimization (react-window)

## Monitoring Patterns

### 1. Observability Three Pillars
- **Logs**: Structured JSON logs with correlation IDs
- **Metrics**: Prometheus-format metrics export
- **Traces**: Distributed tracing (OpenTelemetry planned)

### 2. Health Checks
- **Liveness**: Is the service running?
- **Readiness**: Can the service accept traffic?
- **Startup**: Has initialization completed?

### 3. Metrics Collection
- **RED Method**: Rate, Errors, Duration
- **USE Method**: Utilization, Saturation, Errors
- **Custom Business Metrics**: MTTR, incident count, cost savings

## Code Style Guidelines

### Python Style (Enforced by Tools)
- **Black**: Line length 100, Python 3.11 target
- **isort**: Black profile, multi-line imports
- **Ruff**: Comprehensive linting (E, W, F, I, B, C4, UP, etc.)
- **Type Hints**: All functions with type annotations
- **Docstrings**: Google-style docstrings for public APIs
- **MyPy**: Strict type checking

### TypeScript Style
- **ESLint**: Next.js configuration with strict rules
- **TypeScript**: Strict mode enabled
- **PascalCase**: Components, types, interfaces
- **camelCase**: Variables, functions, properties
- **UPPER_SNAKE_CASE**: Constants

### Naming Conventions
- **Files**: snake_case for Python, PascalCase for React components
- **Classes**: PascalCase (e.g., `DetectionAgent`, `EventStore`)
- **Functions**: snake_case for Python, camelCase for TypeScript
- **Constants**: UPPER_SNAKE_CASE
- **Private**: Leading underscore (Python) or private keyword (TS)

## API Design Guidelines

### 1. RESTful Principles
- **Resource-based URLs**: `/incidents/{id}`, not `/getIncident`
- **HTTP Methods**: GET (read), POST (create), PUT (update), DELETE (delete)
- **Status Codes**: 200 (OK), 201 (Created), 400 (Bad Request), 404 (Not Found), 500 (Error)
- **Versioning**: URL-based versioning `/api/v1/`

### 2. Request/Response Format
- **Content-Type**: application/json
- **Pydantic Models**: Request validation and response serialization
- **Error Format**: Consistent error response structure
- **Pagination**: Consistent pagination metadata

### 3. WebSocket Pattern
- **Connection Management**: Automatic reconnection
- **Message Format**: JSON with type field
- **Heartbeat**: Keep-alive messages
- **Backpressure**: Handle slow consumers

## Documentation Patterns

### 1. Code Documentation
- **Docstrings**: All public functions and classes
- **Type Hints**: Self-documenting function signatures
- **README**: Project overview and quick start
- **Architecture Docs**: System design documentation

### 2. API Documentation
- **OpenAPI/Swagger**: Auto-generated from FastAPI
- **Interactive Docs**: /docs endpoint (Swagger UI)
- **ReDoc**: /redoc endpoint (alternative UI)
- **Examples**: Request/response examples in docs

### 3. User Documentation
- **Demo Guide**: Step-by-step demo instructions
- **Deployment Guide**: Production deployment steps
- **Configuration Guide**: Environment variables reference
- **Troubleshooting**: Common issues and solutions
