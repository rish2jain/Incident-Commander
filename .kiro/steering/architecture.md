# Architecture Guidelines

## Core Architectural Principles

### Multi-Agent Orchestration

The system follows a **swarm intelligence** pattern where specialized agents collaborate autonomously:

```python
class AgentSwarm:
    def __init__(self):
        self.agents = {
            "detection": DetectionAgent(),
            "diagnosis": DiagnosisAgent(),
            "prediction": PredictionAgent(),
            "resolution": ResolutionAgent(),
            "communication": CommunicationAgent()
        }
        self.coordinator = SwarmCoordinator()

    async def handle_incident(self, incident_data):
        # Parallel activation of detection and prediction
        detection_task = self.agents["detection"].analyze(incident_data)
        prediction_task = self.agents["prediction"].forecast(incident_data)

        # Sequential diagnosis based on detection results
        detection_result = await detection_task
        diagnosis_result = await self.agents["diagnosis"].investigate(detection_result)

        # Consensus-based resolution
        resolution_plan = await self.coordinator.build_consensus([
            detection_result, diagnosis_result, await prediction_task
        ])

        return await self.agents["resolution"].execute(resolution_plan)
```

## State Management

### Event Sourcing Pattern

All incident state changes must use event sourcing to prevent race conditions:

```python
class IncidentEventStore:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table('incident-events')

    def append_event(self, incident_id: str, event: IncidentEvent) -> int:
        # Use DynamoDB conditional writes for true distributed locking
        current_version = self.get_current_version(incident_id)
        new_version = current_version + 1

        try:
            self.table.put_item(
                Item={
                    'incident_id': incident_id,
                    'version': new_version,
                    'event_data': event.to_dict(),
                    'timestamp': event.timestamp,
                    'event_type': event.event_type
                },
                ConditionExpression='attribute_not_exists(version) OR version = :expected_version',
                ExpressionAttributeValues={':expected_version': current_version}
            )
            return new_version
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise OptimisticLockException(f"Version conflict for incident {incident_id}")
            raise

    def replay_events(self, incident_id: str) -> IncidentState:
        response = self.table.query(
            KeyConditionExpression=Key('incident_id').eq(incident_id),
            ScanIndexForward=True  # Sort by version ascending
        )

        state = IncidentState()
        for item in response['Items']:
            event = IncidentEvent.from_dict(item['event_data'])
            state = state.apply_event(event)
        return state
```

**Rules:**

- Never directly modify incident state
- All state changes go through event store
- Use DynamoDB conditional writes for distributed optimistic locking
- Implement event replay for state reconstruction
- Store events in DynamoDB with GSI for querying
- Handle OptimisticLockException with exponential backoff retry

### Concurrency Control

**Distributed Locking Strategy:**

- Use DynamoDB conditional writes with version numbers for optimistic locking
- No external lock service required - DynamoDB provides atomic compare-and-swap
- Retry with exponential backoff on OptimisticLockException
- Each incident has a single version counter to prevent race conditions

**Exception Handling:**

```python
class OptimisticLockException(Exception):
    """Raised when concurrent writers conflict on event store updates"""
    pass

async def append_event_with_retry(store, incident_id, event, max_retries=3):
    for attempt in range(max_retries):
        try:
            return store.append_event(incident_id, event)
        except OptimisticLockException:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### Agent Memory Architecture

Implement distributed memory using RAG pattern:

```python
class AgentMemory:
    def __init__(self):
        self.vector_store = ChromaDB()  # Local dev
        self.knowledge_graph = Neo4j()   # Relationships
        self.event_store = DynamoDB()    # Temporal data

    async def learn_from_incident(self, incident: Incident):
        # Store vector embeddings for similarity search
        embedding = await self.embed_incident(incident)
        await self.vector_store.add(incident.id, embedding, incident.metadata)

        # Update knowledge graph relationships
        await self.knowledge_graph.add_incident_relationships(incident)

        # Store temporal sequence
        await self.event_store.append_timeline(incident.timeline)
```

### Agent Circuit Breakers

Implement circuit breaker pattern for all agent communications:

```python
class AgentCircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=30):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout  # Store timeout properly
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.last_failure_time = None

    async def call_agent(self, agent_func, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerOpenError(f"Circuit breaker open, retry after {self.timeout}s")

        try:
            result = await asyncio.wait_for(agent_func(*args, **kwargs), timeout=30)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            raise e
```

**Requirements:**

- 30-second timeout for all agent calls
- 5 failure threshold before opening circuit
- Exponential backoff for retries
- Dead letter queue for failed messages

## Agent Communication

### Resilient Message Bus

Use centralized message bus instead of direct agent communication:

```python
class ResilientMessageBus:
    def __init__(self):
        self.redis_client = Redis()
        self.retry_policies = {
            "detection": RetryPolicy(max_retries=3, timeout=30),
            "diagnosis": RetryPolicy(max_retries=5, timeout=60),
            "resolution": RetryPolicy(max_retries=2, timeout=120)
        }

    async def send_with_resilience(self, message, target_agent):
        retry_policy = self.retry_policies[target_agent]

        for attempt in range(retry_policy.max_retries):
            try:
                await asyncio.wait_for(
                    self.send_message(message, target_agent),
                    timeout=retry_policy.timeout
                )
                return
            except Exception as e:
                if attempt == retry_policy.max_retries - 1:
                    await self.send_to_dlq(message, target_agent, str(e))
                    raise
                await asyncio.sleep(retry_policy.get_delay(attempt))
```

### Agent Dependency Ordering

Prevent deadlocks with topological ordering:

```python
AGENT_DEPENDENCY_ORDER = {
    "detection": 0,      # First responder
    "diagnosis": 1,      # Depends on detection
    "prediction": 1,     # Parallel to diagnosis
    "resolution": 2,     # Depends on diagnosis/prediction
    "communication": 3   # Final step
}

class DependencyManager:
    def can_execute(self, agent_name: str, current_state: dict) -> bool:
        required_level = AGENT_DEPENDENCY_ORDER[agent_name]

        # Level 0 agents (detection) can always start
        if required_level == 0:
            return True

        completed_agents = [name for name, status in current_state.items()
                          if status == "completed"]

        # Check if any prerequisite level is satisfied
        # Agent can execute if ANY agent from a LOWER level has completed
        for completed_agent in completed_agents:
            completed_level = AGENT_DEPENDENCY_ORDER[completed_agent]
            if completed_level < required_level:
                return True

        return False
```

## Conflict Resolution

### Multi-Agent Consensus

When agents provide conflicting recommendations:

```python
class ConflictResolver:
    def __init__(self):
        self.weights = {
            "detection": 0.2,
            "diagnosis": 0.4,
            "prediction": 0.3,
            "resolution": 0.1
        }

    def resolve_actions(self, agent_recommendations: List[AgentAction]) -> AgentAction:
        if len(agent_recommendations) == 1:
            return agent_recommendations[0]

        # Group recommendations by action_id and aggregate confidence
        action_groups = {}
        for rec in agent_recommendations:
            if rec.action_id not in action_groups:
                action_groups[rec.action_id] = {
                    'recommendations': [],
                    'total_weighted_confidence': 0.0,
                    'action': rec
                }
            action_groups[rec.action_id]['recommendations'].append(rec)

        # Calculate aggregated weighted confidence for each action
        for action_id, group in action_groups.items():
            total_confidence = 0.0
            for rec in group['recommendations']:
                agent_weight = self.weights.get(rec.agent_name, 0.1)
                total_confidence += rec.confidence * agent_weight
            group['total_weighted_confidence'] = total_confidence

        # Select action with highest aggregated confidence
        best_action_id = max(action_groups.keys(),
                           key=lambda aid: action_groups[aid]['total_weighted_confidence'])
        best_confidence = action_groups[best_action_id]['total_weighted_confidence']

        # Require minimum confidence threshold (now achievable with multiple agents)
        if best_confidence < 0.7:
            return self.escalate_to_human(agent_recommendations)

        return action_groups[best_action_id]['action']

    def escalate_to_human(self, recommendations: List[AgentAction]) -> HumanEscalation:
        return HumanEscalation(
            reason="Insufficient confidence in automated resolution",
            recommendations=recommendations,
            required_approval_level="senior_sre"
        )
```

**Conflict Resolution Rules:**

- Diagnosis agent has highest weight (0.4)
- Prediction agent weight (0.3) for forward-looking decisions
- Multiple agents can support the same action (confidence aggregates)
- Require 70% aggregated confidence threshold for autonomous actions
- Escalate to human when aggregated confidence < 70%
- Log all conflicts for learning and model improvement

## Failure Handling

### Graceful Degradation

Each agent must have fallback mechanisms:

```python
class RobustAgent:
    def __init__(self):
        self.fallback_chain = [
            self.primary_action,
            self.secondary_action,
            self.safe_mode_action,
            self.emergency_escalation
        ]

    async def execute_with_fallback(self, context: IncidentContext) -> ActionResult:
        for i, action_method in enumerate(self.fallback_chain):
            try:
                result = await action_method(context)
                if self.validate_result(result):
                    if i > 0:  # Used fallback
                        await self.log_fallback_usage(i, action_method.__name__)
                    return result
            except Exception as e:
                await self.log_failure(action_method.__name__, e)
                if i == len(self.fallback_chain) - 1:  # Last resort
                    raise AllActionsFailed(f"All fallback actions failed: {e}")
                continue
```

### Partial Information Handling

```python
class PartialDataHandler:
    def __init__(self):
        self.confidence_adjustments = {
            "missing_logs": -0.2,
            "missing_metrics": -0.15,
            "missing_traces": -0.1,
            "stale_data": -0.05
        }

    def adjust_confidence(self, base_confidence: float, missing_data: List[str]) -> float:
        adjusted = base_confidence
        for missing_type in missing_data:
            adjustment = self.confidence_adjustments.get(missing_type, -0.1)
            adjusted += adjustment

        return max(0.0, min(1.0, adjusted))  # Clamp to [0,1]

    def can_proceed_with_partial_data(self, available_data: dict, required_confidence: float = 0.6) -> bool:
        missing_data = self.identify_missing_data(available_data)
        adjusted_confidence = self.adjust_confidence(0.8, missing_data)  # Base confidence
        return adjusted_confidence >= required_confidence
```

**Partial Information Rules:**

- Continue operation when some data sources are unavailable
- Use confidence scoring based on available information
- Clearly communicate uncertainty levels
- Implement data source health checks
- Degrade gracefully rather than failing completely

## Performance Requirements

### Response Time Targets

```python
PERFORMANCE_TARGETS = {
    "detection": {"target": 30, "max": 60},      # seconds
    "diagnosis": {"target": 120, "max": 180},    # seconds
    "prediction": {"target": 90, "max": 150},    # seconds
    "resolution": {"target": 180, "max": 300},   # seconds
    "communication": {"target": 10, "max": 30}   # seconds
}

class PerformanceMonitor:
    async def track_agent_performance(self, agent_name: str, start_time: float):
        duration = time.time() - start_time
        target = PERFORMANCE_TARGETS[agent_name]["target"]
        max_allowed = PERFORMANCE_TARGETS[agent_name]["max"]

        if duration > max_allowed:
            await self.alert_performance_violation(agent_name, duration)
        elif duration > target:
            await self.log_performance_warning(agent_name, duration)
```

### Scalability Patterns

```python
class ScalabilityManager:
    def __init__(self):
        self.connection_pools = {
            "datadog": ConnectionPool(max_size=20),
            "pagerduty": ConnectionPool(max_size=10),
            "aws": ConnectionPool(max_size=50)
        }
        self.lambda_warmer = LambdaWarmer()

    async def predictive_scaling(self, incident_pattern: str):
        # Scale based on historical incident patterns
        if incident_pattern in ["cascade_failure", "ddos_attack"]:
            await self.scale_resolution_agents(replicas=5)
        elif incident_pattern == "database_slowdown":
            await self.scale_diagnosis_agents(replicas=3)

    async def warm_lambda_functions(self):
        # Prevent cold starts during incidents
        critical_functions = [
            "detection-agent", "diagnosis-agent",
            "resolution-agent", "communication-agent"
        ]
        await self.lambda_warmer.warm_functions(critical_functions)
```

**Scalability Requirements:**

- Connection pooling for external APIs (Datadog: 20, AWS: 50)
- Predictive scaling based on incident patterns
- Lambda warming for cold start prevention (<100ms)
- Async processing for non-critical operations
- Auto-scaling triggers at 70% resource utilization

## Data Flow Architecture

### Event-Driven Processing

```python
class EventProcessor:
    def __init__(self):
        self.event_bus = EventBridge()
        self.processors = {
            "incident.detected": [self.trigger_diagnosis, self.trigger_prediction],
            "diagnosis.completed": [self.trigger_resolution],
            "resolution.completed": [self.trigger_communication, self.update_knowledge_base]
        }

    async def process_event(self, event: IncidentEvent):
        event_type = f"{event.source}.{event.action}"
        processors = self.processors.get(event_type, [])

        # Process in parallel where possible
        tasks = [processor(event) for processor in processors]
        await asyncio.gather(*tasks, return_exceptions=True)
```

### Stream Processing

```python
class IncidentStream:
    def __init__(self):
        self.kinesis_client = boto3.client('kinesis')
        self.stream_name = "incident-events"

    async def publish_event(self, event: IncidentEvent):
        await self.kinesis_client.put_record(
            StreamName=self.stream_name,
            Data=event.to_json(),
            PartitionKey=event.incident_id
        )

    async def consume_events(self, processor_func):
        # Consume events with checkpointing
        async for event in self.stream_consumer():
            try:
                await processor_func(event)
                await self.checkpoint(event.sequence_number)
            except Exception as e:
                await self.handle_processing_error(event, e)
```
