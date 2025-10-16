# Project Structure

## Root Directory Organization

```
incident-commander/
├── .kiro/                    # Kiro IDE configuration
│   └── steering/            # AI assistant guidance rules
├── .venv/                   # Python virtual environment
├── Research/                # Market research and competitive analysis
├── src/                     # Source code (to be created)
├── agents/                  # Individual agent implementations
├── infrastructure/          # AWS CDK infrastructure code
├── tests/                   # Test suite
├── docs/                    # Documentation
├── scripts/                 # Utility and setup scripts
└── docker/                  # Docker configurations
```

## Source Code Structure

### Core Agent System (`src/`)

```
src/
├── __init__.py
├── main.py                  # FastAPI application entry point
├── orchestrator/            # Multi-agent orchestration
│   ├── __init__.py
│   ├── graph.py            # LangGraph workflow definitions
│   ├── state.py            # Shared state management
│   └── coordinator.py      # Agent coordination logic
├── models/                  # Pydantic data models
│   ├── __init__.py
│   ├── incident.py         # Incident data structures
│   ├── agent.py            # Agent communication models
│   └── metrics.py          # Performance metrics models
├── services/                # External service integrations
│   ├── __init__.py
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
