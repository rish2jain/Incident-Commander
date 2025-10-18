# Codebase Structure

## Root Directory Layout
```
incident-commander/
├── src/                    # FastAPI application and core services
├── agents/                 # Individual agent implementations
├── tests/                  # Test suites (unit, integration, chaos)
├── infrastructure/         # CDK stacks for AWS deployment
├── docs/                   # Published documentation
├── scripts/                # Utility scripts
├── Research/               # Experimental code and prototypes
├── docker/                 # Container recipes
├── .kiro/                  # Project steering and specifications
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
└── README.md              # Project documentation
```

## src/ - Core Application
```
src/
├── __init__.py
├── main.py                 # FastAPI entrypoint, lifespan manager
├── interfaces/             # Abstract base classes and protocols
│   ├── agent.py           # BaseAgent interface
│   ├── event_store.py     # Event store interface
│   ├── circuit_breaker.py # Circuit breaker interface
│   └── consensus.py       # Consensus engine interface
├── models/                 # Pydantic data models
│   ├── incident.py        # Incident, severity, business impact
│   └── agent.py           # Agent message models
├── services/               # Shared services
│   ├── event_store.py     # Kinesis + DynamoDB implementation
│   ├── circuit_breaker.py # Circuit breaker pattern
│   ├── rate_limiter.py    # Rate limiting for APIs
│   ├── rag_memory.py      # RAG system integration
│   ├── vector_store.py    # OpenSearch Serverless wrapper
│   ├── consensus.py       # Byzantine consensus
│   ├── message_bus.py     # Inter-agent communication
│   └── aws.py             # AWS service helpers
├── orchestrator/           # Swarm coordination
│   └── swarm_coordinator.py  # Agent orchestration logic
└── utils/                  # Shared utilities
    ├── config.py          # Configuration management
    ├── logging.py         # Structured logging setup
    ├── constants.py       # Shared constants
    └── exceptions.py      # Custom exception hierarchy
```

## agents/ - Agent Implementations
```
agents/
├── __init__.py
├── detection/              # Detection agent
│   ├── __init__.py
│   └── agent.py           # RobustDetectionAgent
├── diagnosis/              # Diagnosis agent
│   ├── __init__.py
│   └── agent.py           # HardenedDiagnosisAgent
└── prediction/             # Prediction agent (in progress)
    ├── __init__.py
    └── agent.py
```

## tests/ - Test Organization
```
tests/
├── conftest.py             # Pytest fixtures (Slack, Bedrock, LocalStack stubs)
├── test_foundation.py      # Comprehensive foundation tests (37 passing)
├── unit/                   # Unit tests for individual components
├── integration/            # End-to-end integration tests
├── chaos/                  # Chaos engineering scenarios
└── load/                   # Load testing scripts
```

## Key Files to Know

### Entry Points
- `src/main.py` - FastAPI application, all endpoints defined here
- `agents/detection/agent.py` - Detection agent implementation
- `agents/diagnosis/agent.py` - Diagnosis agent implementation

### Configuration
- `.env` - Environment variables (gitignored, use .env.example)
- `src/utils/config.py` - Configuration loading and validation
- `src/utils/constants.py` - System-wide constants

### Core Interfaces
- `src/interfaces/agent.py` - All agents inherit from BaseAgent
- `src/interfaces/event_store.py` - Event store contract
- `src/interfaces/circuit_breaker.py` - Circuit breaker contract

### Business Logic
- `src/models/incident.py` - Incident model with business impact
- `src/orchestrator/swarm_coordinator.py` - Agent coordination
- `src/services/rag_memory.py` - Historical pattern matching

## Module Organization Principles
- Mirror capability folders in `tests/` for test coverage
- Each agent in `agents/<capability>/` has isolated logic
- Shared helpers in `src/utils/`, models in `src/models/`
- Infrastructure code in `infrastructure/` (CDK stacks)
- Documentation in `docs/`, experiments in `Research/`