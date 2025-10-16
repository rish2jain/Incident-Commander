# Technology Stack

## Core Framework

**Python 3.11** - Primary development language
**AWS Bedrock AgentCore** - Multi-agent orchestration platform
**LangGraph** - Agent workflow management and inter-agent communication

## Agent Architecture

### Multi-Agent Framework

- **LangGraph**: State management and agent orchestration
- **AutoGen**: Alternative for agent-to-agent communication
- **AWS Bedrock**: Foundation models (Claude-3, GPT-4)
- **Bedrock Guardrails**: Safety and compliance controls

### Memory & Learning

- **ChromaDB**: Local vector database for development
- **Pinecone**: Production vector database for RAG
- **AWS DynamoDB**: Agent state persistence
- **S3**: Incident data and model artifacts

## Backend Services

### API Layer

- **FastAPI**: REST API and WebSocket endpoints
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation and serialization

### Infrastructure

- **AWS CDK**: Infrastructure as Code
- **AWS Lambda**: Serverless agent functions
- **AWS ECS**: Container orchestration for agent system
- **API Gateway**: External API management

## Monitoring & Observability

### Metrics & Logging

- **Prometheus**: Metrics collection
- **Grafana**: Visualization dashboards
- **Vector**: High-performance log aggregation
- **LangSmith**: Agent tracing and debugging

### Incident Simulation

- **Chaos Toolkit**: Controlled failure injection
- **LocalStack Pro**: Local AWS environment testing
- **Moto**: AWS service mocking (fallback)

## Frontend & Demo

### Web Interface

- **React**: Frontend framework
- **Recharts**: Real-time metrics visualization
- **Framer Motion**: Smooth animations
- **Socket.io**: Real-time agent communication
- **Streamlit**: Rapid prototyping alternative

## Integrations

### External Services

- **Datadog API**: Metrics and monitoring
- **PagerDuty API**: Incident management
- **Slack SDK**: Team notifications
- **GitHub API**: Code deployment tracking

## Development Tools

### Testing

- **pytest**: Unit and integration testing
- **pytest-asyncio**: Async test support
- **Locust**: Load testing
- **pytest-benchmark**: Performance testing

### Development Environment

- **Docker Compose**: Local service orchestration
- **pyenv**: Python version management
- **pip**: Package management

## Common Commands

### Development Setup

```bash
# Environment setup
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start local services
docker-compose up -d

# Initialize LocalStack
awslocal bedrock create-agent --agent-name incident-commander

# Start development servers
uvicorn main:app --reload --port 8000  # Backend
npm run dev  # Frontend (if applicable)
python agent_orchestrator.py  # Agent system
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Load testing
locust -f tests/load_test.py

# Chaos testing
chaos run chaos-experiment.yaml
```

### Deployment

```bash
# Deploy infrastructure
cdk deploy IncidentCommanderStack

# Package and deploy agents
sam build && sam deploy

# Update agent configuration
aws bedrock update-agent --agent-id <id>
```

### Monitoring

```bash
# View agent logs
aws logs tail /aws/lambda/detection-agent --follow

# Check metrics
curl http://localhost:9090/metrics

# Agent debugging
python -m langsmith.debug agent_trace_id
```
