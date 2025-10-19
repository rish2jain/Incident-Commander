# Technology Stack

## Core Framework

**Python 3.11** - Primary development language
**AWS Bedrock AgentCore** - Multi-agent orchestration platform with Byzantine fault tolerance
**Custom Agent Swarm Coordinator** - Production-ready multi-agent orchestration with consensus

## Agent Architecture

### Multi-Agent Framework (FULLY IMPLEMENTED)

- **Agent Swarm Coordinator**: Custom Byzantine fault-tolerant orchestration
- **AWS Bedrock**: Foundation models (Claude 3.5 Sonnet, Claude 3 Haiku)
- **Amazon Titan Embeddings**: Production vector embeddings (amazon.titan-embed-text-v1)
- **Amazon Q Business**: Intelligent incident analysis and documentation
- **Nova Act**: Advanced reasoning and action planning
- **Strands SDK**: Enhanced agent lifecycle management
- **Bedrock Guardrails**: Safety and compliance controls with monitoring

### Memory & Learning (PRODUCTION READY)

- **OpenSearch Serverless**: Production vector database for RAG
- **AWS DynamoDB**: Event sourcing and agent state persistence
- **AWS Kinesis**: Real-time event streaming and processing
- **S3**: Incident data, model artifacts, and audit logs
- **RAG Memory System**: Hierarchical indexing with hybrid vector + text search

## Backend Services

### API Layer (PRODUCTION READY)

- **FastAPI**: 50+ REST API endpoints with comprehensive functionality
- **WebSocket**: Real-time dashboard updates and agent coordination
- **Uvicorn**: ASGI server with performance optimization
- **Pydantic**: Data validation and serialization with security controls

### Infrastructure (FULLY DEPLOYED)

- **AWS CDK**: Infrastructure as Code with multi-environment support
- **AWS Lambda**: Serverless agent functions with auto-scaling
- **AWS Step Functions**: Byzantine consensus orchestration
- **API Gateway**: External API management with rate limiting
- **CloudWatch**: Comprehensive monitoring and alerting

## Monitoring & Observability (ENTERPRISE GRADE)

### Metrics & Logging

- **CloudWatch**: Native AWS monitoring with custom metrics
- **Enhanced Telemetry**: Per-agent execution statistics and performance tracking
- **Guardrail Monitor**: Policy enforcement tracking and compliance reporting
- **System Health Monitor**: Meta-incident detection with automated recovery
- **Tamper-Proof Audit Logging**: Cryptographic integrity with 7-year retention

### Incident Simulation & Testing

- **Chaos Engineering Framework**: Controlled failure injection and recovery testing
- **LocalStack**: Local AWS environment for development
- **Performance Testing Framework**: Load testing and scalability validation
- **Security Testing Framework**: Penetration testing and vulnerability assessment

## Frontend & Demo (FULLY IMPLEMENTED)

### Interactive Dashboard

- **Enhanced 3D Dashboard**: WebSocket-based real-time visualization
- **Agent Coordination Display**: Live multi-agent interaction visualization
- **Business Impact Calculator**: Real-time ROI and cost savings analysis
- **Interactive Judge Mode**: Personalized demo experiences with custom scenarios
- **Performance Metrics**: Live MTTR tracking and business impact calculation

### Demo & Presentation

- **5 Interactive Scenarios**: Database failures, API cascades, memory leaks, network issues, security incidents
- **Real-time Visualization**: Agent confidence scores, decision trees, conflict resolution
- **Business Impact Showcase**: Executive-level metrics and ROI demonstration
- **Judge-Controlled Demos**: Personalized experiences with severity adjustment

## Integrations (PRODUCTION READY)

### AWS AI Services (8/8 COMPLETE)

- **Amazon Bedrock AgentCore**: Multi-agent orchestration
- **Claude 3.5 Sonnet**: Complex reasoning and analysis
- **Claude 3 Haiku**: Fast response generation
- **Amazon Titan Embeddings**: Production vector embeddings
- **Amazon Q Business**: Intelligent analysis and documentation
- **Nova Act**: Advanced reasoning and action planning
- **Strands SDK**: Enhanced agent lifecycle management
- **Bedrock Guardrails**: Safety and compliance controls

### External Services

- **Datadog API**: Metrics and monitoring integration
- **PagerDuty API**: Incident management and escalation
- **Slack SDK**: Team notifications and communication
- **GitHub API**: Code deployment tracking and integration

## Development Tools (COMPREHENSIVE SUITE)

### Testing Framework

- **pytest**: Unit and integration testing with 95%+ coverage
- **pytest-asyncio**: Async test support for agent coordination
- **Performance Testing**: Load testing and scalability validation
- **Security Testing**: Penetration testing and vulnerability assessment
- **Chaos Engineering**: Failure injection and recovery testing

### Development Environment

- **Docker Compose**: Local service orchestration with LocalStack
- **AWS CDK**: Infrastructure as Code with multi-environment support
- **Python 3.11**: Virtual environment management
- **Pre-commit Hooks**: Code quality and security scanning

## Local Development Workflow

- Start dependencies with `docker-compose up -d`; this provisions LocalStack, Redis, and supporting containers expected by orchestrator services.
- Use `awslocal` to create DynamoDB tables, Kinesis streams, and Bedrock stubs during development. Swap to native `aws` CLI in staging/production.
- Populate `.env` from `.env.example`, pointing SDK clients (DynamoDB, S3, Bedrock) at `localhost` endpoints exposed by LocalStack.

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
uvicorn src.main:app --reload --port 8000  # Backend API
python src/main.py  # Full system with agents
```

### Production Deployment

```bash
# Deploy complete system to AWS
cd hackathon && python deploy_hackathon_demo.py

# Deploy with production hardening
python deploy_ultimate_system.py

# Validate deployment
cd hackathon && python validate_hackathon_deployment.py
```

### Testing & Validation

```bash
# Run comprehensive test suite
python run_comprehensive_tests.py

# Performance testing
python validate_demo_performance.py

# Security validation
python harden_security.py --validate

# API testing
curl https://your-api-url/health
curl https://your-api-url/demo/incident
curl https://your-api-url/demo/stats
```

### Monitoring & Operations

```bash
# System health check
curl https://your-api-url/health

# Agent telemetry
curl https://your-api-url/observability/telemetry

# Business metrics
curl https://your-api-url/demo/stats

# Interactive demo
curl https://your-api-url/demo/judge/start
```

### AWS AI Service Integration

```bash
# Test Amazon Q integration
curl https://your-api-url/amazon-q/status

# Test Nova Act integration
curl https://your-api-url/nova-act/status

# Test Strands SDK integration
curl https://your-api-url/strands/status

# Comprehensive showcase
curl https://your-api-url/ultimate-demo/full-showcase
```

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
