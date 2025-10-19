# Project Structure

## Root Directory Organization (PRODUCTION READY)

```
incident-commander/
├── .kiro/                    # Kiro IDE configuration and steering rules
├── .venv/                   # Python virtual environment
├── Research/                # Market research and competitive analysis
├── src/                     # ✅ IMPLEMENTED - Core source code
├── agents/                  # ✅ IMPLEMENTED - Individual agent implementations
├── infrastructure/          # ✅ IMPLEMENTED - AWS CDK infrastructure code
├── tests/                   # ✅ IMPLEMENTED - Comprehensive test suite
├── docs/                    # ✅ IMPLEMENTED - Complete documentation
├── scripts/                 # ✅ IMPLEMENTED - Deployment and utility scripts
├── winning_enhancements/    # ✅ IMPLEMENTED - Prize-winning features
├── dashboard/               # ✅ IMPLEMENTED - Interactive dashboard
├── monitoring/              # ✅ IMPLEMENTED - System monitoring
└── deployment_package/      # ✅ IMPLEMENTED - Production deployment assets
```

## Source Code Structure

### Core Agent System (`src/`) - ✅ FULLY IMPLEMENTED

```
src/
├── __init__.py
├── main.py                  # ✅ FastAPI application with 50+ endpoints
├── lambda_handler.py        # ✅ AWS Lambda deployment handler
├── orchestrator/            # ✅ Multi-agent orchestration
│   └── swarm_coordinator.py # ✅ Byzantine fault-tolerant coordination
├── models/                  # ✅ Pydantic data models
│   ├── incident.py         # ✅ Incident data structures with business impact
│   ├── agent.py            # ✅ Agent communication and consensus models
│   ├── security.py         # ✅ Security and audit models
│   └── showcase.py         # ✅ Demo and presentation models
├── services/                # ✅ 40+ Production services
│   ├── agent_swarm_coordinator.py    # ✅ Multi-agent orchestration
│   ├── byzantine_consensus.py        # ✅ Fault-tolerant consensus
│   ├── business_impact_calculat
│   ├── aws.py              # AWS service clients
│   ├── monitoring.py       # Datadog, Prometheus integration
│   └── notifications.py    # Slack, PagerDuty integration
└── utils/                   # Shared utilities
    ├── __init__.py
    ├── logging.py          # Structured logging
    ├── config.py           # Configuration management
    └── exceptions.py       # Custom exceptions
```

### Individual Agents (`agents/`)

```
agents/
├── detection/
│   ├── __init__.py
│   ├── agent.py            # Detection agent implementation
│   ├── monitors.py         # Metric monitoring logic
│   └── patterns.py         # Anomaly detection patterns
├── diagnosis/
│   ├── __init__.py
│   ├── agent.py            # Diagnosis agent implementation
│   ├── analyzers.py        # Log and trace analysis
│   └── knowledge.py        # RAG knowledge base
├── prediction/
│   ├── __init__.py
│   ├── agent.py            # Prediction agent implementation
│   ├── models.py           # ML prediction models
│   └── features.py         # Feature engineering
├── resolution/
│   ├── __init__.py
│   ├── agent.py            # Resolution agent implementation
│   ├── actions.py          # Automated remediation actions
│   └── rollback.py         # Rollback mechanisms
└── communication/
    ├── __init__.py
    ├── agent.py            # Communication agent implementation
    ├── templates.py        # Message templates
    └── channels.py         # Notification channels
```

### Infrastructure (`infrastructure/`)

```
infrastructure/
├── __init__.py
├── app.py                  # CDK app entry point
├── stacks/
│   ├── __init__.py
│   ├── bedrock_stack.py    # Bedrock agents and models
│   ├── compute_stack.py    # Lambda and ECS resources
│   ├── storage_stack.py    # DynamoDB, S3, vector DB
│   └── monitoring_stack.py # CloudWatch, observability
├── constructs/             # Reusable CDK constructs
│   ├── __init__.py
│   ├── agent_construct.py  # Bedrock agent construct
│   └── api_construct.py    # API Gateway construct
└── config/
    ├── dev.py              # Development environment config
    ├── staging.py          # Staging environment config
    └── prod.py             # Production environment config
```

### Testing (`tests/`)

```
tests/
├── __init__.py
├── conftest.py             # Pytest configuration and fixtures
├── unit/                   # Unit tests
│   ├── test_agents.py      # Individual agent tests
│   ├── test_orchestrator.py # Orchestration logic tests
│   └── test_services.py    # Service integration tests
├── integration/            # Integration tests
│   ├── test_workflows.py   # End-to-end workflow tests
│   ├── test_api.py         # API endpoint tests
│   └── test_incidents.py   # Incident simulation tests
├── load/                   # Load testing
│   ├── locustfile.py       # Locust load test scenarios
│   └── scenarios/          # Different load test scenarios
└── chaos/                  # Chaos engineering tests
    ├── experiments/        # Chaos toolkit experiments
    └── scenarios/          # Failure injection scenarios
```

## Configuration Files

### Root Level

- `requirements.txt` - Python dependencies
- `pyproject.toml` - Python project configuration
- `docker-compose.yml` - Local development services
- `cdk.json` - CDK configuration
- `.env.example` - Environment variables template
- `.gitignore` - Git ignore patterns
- `README.md` - Project documentation

### Development Tools

- `pytest.ini` - Pytest configuration
- `mypy.ini` - Type checking configuration
- `.pre-commit-config.yaml` - Pre-commit hooks
- `Dockerfile` - Container image definition

## Key Conventions

### File Naming

- Use snake_case for Python files and directories
- Use descriptive names that indicate purpose
- Prefix test files with `test_`
- Use `__init__.py` to make directories Python packages

### Code Organization

- Each agent is self-contained in its own directory
- Shared utilities go in `src/utils/`
- External integrations go in `src/services/`
- Infrastructure code is separate from application code
- Tests mirror the source code structure

### Import Patterns

```python
# Absolute imports from project root
from src.orchestrator.graph import IncidentGraph
from agents.detection.agent import DetectionAgent

# Relative imports within modules
from .models import IncidentModel
from ..utils.logging import get_logger
```

### Environment Management

- Use `.env` files for local development
- AWS Parameter Store for production secrets
- Separate configurations per environment (dev/staging/prod)
- Never commit secrets to version control
