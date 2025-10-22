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
├── dashboard/               # ✅ IMPLEMENTED - Next.js dashboard with 3 specialized views
├── monitoring/              # ✅ IMPLEMENTED - System monitoring
├── demo_recordings/         # ✅ IMPLEMENTED - Professional HD recordings and screenshots
├── hackathon/              # ✅ IMPLEMENTED - Hackathon-specific materials and validation
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
│   ├── business_impact_calculator.py # ✅ ROI and cost savings calculation
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

### Hackathon Materials (`hackathon/`) - ✅ OCTOBER 2025 UPDATE

```
hackathon/
├── README.md                                    # Hackathon-specific documentation
├── MASTER_SUBMISSION_GUIDE.md                  # Complete submission package
├── COMPREHENSIVE_JUDGE_GUIDE.md                # Judge evaluation guide
├── FINAL_HACKATHON_STATUS_OCT21.md            # Current system status
├── LATEST_DEMO_RECORDING_SUMMARY.md           # Professional recording details
├── deploy_hackathon_demo.py                   # AWS deployment script
├── validate_hackathon_deployment.py           # Deployment validation
├── test_enhanced_validation.py                # Enhanced validation system
├── validate_phase2_ui_enhancements.py         # UI feature validation
└── archive/                                   # Historical documents
```

### Dashboard (`dashboard/`) - ✅ NEXT.JS IMPLEMENTATION

```
dashboard/
├── app/                    # Next.js 14 app router
│   ├── page.tsx           # Homepage with navigation
│   ├── demo/              # PowerDashboard for presentations
│   ├── transparency/      # AI explainability dashboard
│   ├── ops/              # Operations monitoring dashboard
│   └── insights-demo/    # Enhanced insights demo
├── src/
│   ├── components/       # React components
│   │   ├── RefinedDashboard.tsx    # Phase 2 UI features
│   │   ├── TransparencyDashboard.tsx # AI transparency
│   │   └── OperationsDashboard.tsx   # Real-time operations
│   ├── hooks/           # Custom React hooks
│   ├── utils/           # Utility functions
│   └── types/           # TypeScript definitions
├── public/              # Static assets
├── package.json         # Dependencies and scripts
└── next.config.js       # Next.js configuration
```

### Demo Recordings (`demo_recordings/`) - ✅ PROFESSIONAL MATERIALS

```
demo_recordings/
├── videos/
│   └── 00b6a99e232bc15389fff08c63a89189.webm  # 2-minute HD recording
├── screenshots/         # 19 comprehensive feature captures
│   ├── 01_system_overview.png
│   ├── 02_incident_trigger.png
│   └── ... (17 more screenshots)
└── metrics/
    └── comprehensive_demo_metrics_20251021_222000.json
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
