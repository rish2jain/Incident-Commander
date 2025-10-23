# SwarmAI - Codebase Structure

## Root Directory Structure
```
incident-commander/
├── src/                          # Backend Python source code
├── dashboard/                    # Frontend Next.js application
├── tests/                        # Python test suite
├── infrastructure/               # AWS CDK Infrastructure as Code
├── hackathon/                    # Hackathon submission materials
├── scripts/                      # Utility and deployment scripts
├── agents/                       # DEPRECATED - moved to src/agents/ (retained for backward compatibility, scheduled for removal in v1.0)
├── claudedocs/                   # Claude-generated documentation and analysis
├── demo_recordings/              # Demo video recordings and screenshots
├── monitoring/                   # Monitoring configurations
├── Research/                     # Research and competitive analysis
├── .github/                      # GitHub Actions workflows
├── .kiro/                        # Kiro IDE configuration
├── .claude/                      # Claude Code configuration
├── .code/                        # VSCode/Claude Code temporary files
├── .serena/                      # Serena MCP server data
└── .ruff_cache/                  # Ruff linter cache
```

## Backend Source (src/)
```
src/
├── main.py                       # FastAPI application entry point
├── lambda_handler.py             # AWS Lambda entry point
├── health_check.py               # Health check endpoint logic
├── version.py                    # Version information
├── detection_agent.py            # Detection agent implementation
├── real_aws_ai_orchestrator.py   # AWS AI services orchestrator
│
├── api/                          # FastAPI API layer
│   ├── __init__.py
│   ├── dependencies.py           # Shared dependencies (DB, Redis, etc.)
│   ├── routers/                  # API endpoint routers
│   │   ├── __init__.py
│   │   ├── incidents.py          # Incident management endpoints
│   │   ├── demo.py               # Demo scenario endpoints
│   │   ├── dashboard.py          # Dashboard data endpoints
│   │   ├── showcase.py           # Feature showcase endpoints
│   │   ├── monitoring.py         # Monitoring and metrics endpoints
│   │   ├── security.py           # Security validation endpoints
│   │   ├── business_impact.py    # Business impact calculations
│   │   ├── analytics.py          # Analytics and reporting
│   │   ├── finops.py             # FinOps cost control
│   │   ├── operator.py           # Operator controls
│   │   ├── deployment.py         # Deployment management
│   │   ├── model_routing.py      # AI model routing
│   │   ├── aws_ai_services.py    # AWS AI service integration
│   │   ├── real_aws_ai_showcase.py # Real AWS AI demonstration
│   │   ├── chaos_engineering.py  # Chaos testing endpoints
│   │   ├── visual_3d.py          # 3D visualization endpoints
│   │   ├── documentation.py      # Documentation generation
│   │   └── models.py             # Shared Pydantic models
│   │
│   └── middleware/               # API middleware
│       ├── __init__.py
│       └── auth.py               # Authentication middleware
│
├── models/                       # Pydantic data models
│   ├── __init__.py
│   ├── incident.py               # Incident domain models
│   ├── agent.py                  # Agent data models
│   ├── security.py               # Security-related models
│   ├── showcase.py               # Showcase feature models
│   └── real_time_models.py       # Real-time data models
│
├── schemas/                      # API request/response schemas
│   ├── __init__.py
│   └── incident.py               # Incident API schemas
│
├── services/                     # Business logic services (100+ files)
│   ├── __init__.py
│   │
│   # Core Services
│   ├── event_store.py            # Event sourcing implementation
│   ├── message_bus.py            # Inter-agent message bus
│   ├── consensus.py              # Consensus engine
│   ├── byzantine_consensus.py    # Byzantine fault tolerance
│   ├── circuit_breaker.py        # Circuit breaker pattern
│   ├── rate_limiter.py           # Rate limiting
│   │
│   # AWS Integration
│   ├── aws.py                    # AWS service clients
│   ├── aws_ai_integration.py     # AWS AI services integration
│   ├── aws_ai_service_manager.py # AI service manager
│   ├── aws_prize_services.py     # Prize-specific AWS services
│   ├── bedrock_agent_configurator.py # Bedrock agent config
│   │
│   # Memory & Learning
│   ├── rag_memory.py             # RAG memory system
│   ├── vector_store.py           # Vector storage (OpenSearch)
│   ├── learning.py               # Learning and adaptation
│   ├── knowledge_base_generator.py # Knowledge base creation
│   ├── knowledge_updater.py      # Knowledge base updates
│   │
│   # Agent Coordination
│   ├── agent_swarm_coordinator.py # Agent swarm orchestration
│   ├── enhanced_consensus_coordinator.py # Enhanced consensus
│   ├── step_functions_consensus.py # Step Functions integration
│   │
│   # Monitoring & Observability
│   ├── monitoring.py             # Core monitoring
│   ├── enhanced_monitoring_integration.py # Advanced monitoring
│   ├── system_health_monitor.py  # System health checks
│   ├── integration_monitor.py    # Integration monitoring
│   ├── agent_telemetry.py        # Agent telemetry
│   ├── enhanced_telemetry.py     # Enhanced telemetry
│   ├── metrics_endpoint.py       # Metrics API
│   ├── shared_memory_monitor.py  # Memory monitoring
│   │
│   # Security
│   ├── security/                 # Security services
│   │   ├── __init__.py
│   │   ├── audit_logger.py       # Cryptographic audit logging
│   │   ├── security_monitor.py   # Security monitoring
│   │   ├── agent_authenticator.py # Agent authentication
│   │   ├── compliance_manager.py # Compliance checks
│   │   └── security_testing.py   # Security testing
│   ├── security_service.py       # Security service facade
│   ├── security_validation_service.py # Security validation
│   ├── security_audit.py         # Security audits
│   ├── security_testing_framework.py # Security test framework
│   ├── security_error_integration.py # Error handling
│   ├── security_headers_middleware.py # Security headers
│   │
│   # Business Logic
│   ├── business_impact_calculator.py # ROI calculations
│   ├── business_impact_viz.py    # Business visualization
│   ├── business_metrics_service.py # Business metrics
│   ├── business_data_export.py   # Data export
│   ├── executive_reporting.py    # Executive reports
│   ├── compliance_roi_demo.py    # Compliance ROI demo
│   │
│   # FinOps & Cost Management
│   ├── finops.py                 # FinOps core
│   ├── finops_controller.py      # FinOps controls
│   ├── cost_optimizer.py         # Cost optimization
│   ├── model_cost_optimizer.py   # AI model cost optimization
│   ├── model_router.py           # Adaptive model routing
│   │
│   # Demo & Showcase
│   ├── interactive_demo_controller.py # Demo controller
│   ├── showcase_controller.py    # Showcase controller
│   ├── interactive_judge.py      # Interactive judge mode
│   ├── interactive_3d_demo.py    # 3D demo
│   ├── fault_tolerance_showcase.py # Fault tolerance demo
│   ├── agent_conversation_replay.py # Conversation replay
│   │
│   # Dashboard & UI
│   ├── dashboard_state.py        # Dashboard state management
│   ├── enhanced_dashboard.py     # Enhanced dashboard features
│   ├── visual_dashboard.py       # Visual dashboard
│   ├── visual_3d_integration.py  # 3D visualization
│   ├── websocket_manager.py      # WebSocket management
│   ├── realtime_visualization.py # Real-time viz
│   ├── realtime_integration.py   # Real-time integration
│   │
│   # Incident Management
│   ├── incident_lifecycle_manager.py # Incident lifecycle
│   ├── post_incident_documentation.py # Post-incident docs
│   ├── preventive_action_engine.py # Prevention
│   ├── detection_accuracy_testing.py # Detection testing
│   ├── resolution_success_validator.py # Resolution validation
│   ├── meta_incident_handler.py  # Meta-incident handling
│   │
│   # Quality & Testing
│   ├── chaos_engineering.py      # Chaos engineering
│   ├── chaos_engineering_framework.py # Chaos framework
│   ├── performance_testing_framework.py # Performance testing
│   ├── production_validation_framework.py # Production validation
│   ├── system_integration_validator.py # Integration validation
│   │
│   # Error Handling & Recovery
│   ├── error_handling_recovery.py # Error recovery
│   ├── log_corruption_handler.py # Log corruption handling
│   ├── log_sanitization.py       # Log sanitization
│   │
│   # Deployment & Operations
│   ├── deployment_pipeline.py    # Deployment automation
│   ├── deployment_validator.py   # Deployment validation
│   ├── scaling_manager.py        # Auto-scaling
│   ├── operator_controls.py      # Operator controls
│   ├── container.py              # Dependency injection
│   │
│   # AI & ML Services
│   ├── explainability.py         # AI explainability
│   ├── guardrails.py             # Bedrock guardrails
│   ├── guardrail_monitor.py      # Guardrail monitoring
│   ├── guardrail_tracker.py      # Guardrail tracking
│   │
│   # Utilities
│   ├── analytics.py              # Analytics service
│   ├── performance_optimizer.py  # Performance optimization
│   ├── timezone_manager.py       # Timezone handling
│   ├── documentation_generator.py # Auto documentation
│   ├── localstack_fixtures.py    # LocalStack utilities
│   └── auth_middleware.py        # Auth middleware
│
├── orchestrator/                 # Agent orchestrators
│   ├── real_time_orchestrator.py # Real-time orchestration
│   └── swarm_coordinator.py      # Swarm coordination
│
├── interfaces/                   # Core abstractions
│   ├── __init__.py
│   ├── agent.py                  # Agent interface
│   ├── event_store.py            # Event store interface
│   ├── circuit_breaker.py        # Circuit breaker interface
│   └── consensus.py              # Consensus interface
│
└── utils/                        # Utility modules
    ├── __init__.py
    ├── config.py                 # Configuration management
    ├── constants.py              # Application constants
    ├── logging.py                # Structured logging
    ├── exceptions.py             # Custom exceptions
    ├── secrets_manager.py        # Secrets management
    └── dynamodb_helpers.py       # DynamoDB utilities
```

## Frontend (dashboard/)
```
dashboard/
├── app/                          # Next.js 14 App Router pages
│   ├── layout.tsx                # Root layout
│   ├── page.tsx                  # Home page
│   ├── demo/                     # Dashboard 1: Executive view
│   │   ├── page.tsx
│   │   └── layout.tsx
│   ├── transparency/             # Dashboard 2: Engineering view
│   │   ├── page.tsx
│   │   └── layout.tsx
│   └── ops/                      # Dashboard 3: Operations view
│       ├── page.tsx
│       └── layout.tsx
│
├── src/                          # Source code
│   ├── components/               # React components (NEW LOCATION - use this for all new components)
│   │   ├── ui/                   # Reusable UI components (Radix UI based)
│   │   ├── dashboard/            # Dashboard-specific components
│   │   ├── visualization/        # 3D and data visualization
│   │   └── shared/               # Shared components
│   ├── hooks/                    # Custom React hooks
│   ├── lib/                      # Utility libraries
│   ├── services/                 # API client services
│   ├── types/                    # TypeScript type definitions
│   └── utils/                    # Utility functions
│
├── public/                       # Static assets
│   ├── images/
│   ├── fonts/
│   └── icons/
│
├── components/                   # DEPRECATED - Legacy component location (scheduled for removal in v1.0)
│                                 # DO NOT add new components here - use src/components/ instead
├── next.config.js                # Next.js configuration
├── tailwind.config.js            # Tailwind CSS configuration
├── tsconfig.json                 # TypeScript configuration
├── package.json                  # NPM dependencies and scripts
└── .env.local.example            # Environment variable template
```

## Tests Structure
```
tests/
├── __init__.py
├── conftest.py                   # Pytest fixtures and configuration
├── test_foundation.py            # Foundation tests
├── test_*.py                     # Various test modules
└── integration/                  # Integration tests
```

## Infrastructure (infrastructure/)
```
infrastructure/
└── cdk/                          # AWS CDK stacks
    ├── app.py                    # CDK app entry point
    ├── stacks/                   # CDK stack definitions
    │   ├── network_stack.py      # VPC, subnets, security groups
    │   ├── database_stack.py     # DynamoDB, OpenSearch
    │   ├── compute_stack.py      # Lambda, ECS
    │   ├── api_stack.py          # API Gateway
    │   └── monitoring_stack.py   # CloudWatch, alarms
    ├── constructs/               # Reusable CDK constructs
    └── cdk.json                  # CDK configuration
```

## Key Configuration Files
- **pyproject.toml**: Python project config, dependencies, tool settings
- **requirements.txt**: Python dependencies (generated from pyproject.toml)
- **requirements-lambda.txt**: Lambda-specific Python dependencies
- **pytest.ini**: Pytest configuration
- **.env.example**: Environment variable template
- **.env.production.template**: Production environment template
- **docker-compose.yml**: Local development services
- **Dockerfile**: Application containerization
- **Makefile**: Build and development commands
- **.pre-commit-config.yaml**: Pre-commit hooks
- **.gitignore**: Git ignore patterns
- **cdk.json**: CDK configuration
- **cdk.context.json**: CDK context values

## Documentation Directories
- **hackathon/**: Hackathon submission materials, guides, and demos
- **claudedocs/**: AI-generated documentation and analysis
- **scripts/**: Utility scripts with documentation
- **Research/**: Competitive analysis and research

## Deprecations & Migration

### Deprecated Locations
| Deprecated Path | New Location | Migration Checklist | Removal Target |
|----------------|--------------|---------------------|----------------|
| `agents/` | `src/agents/` | 1. Move files to src/agents/<br>2. Update imports<br>3. Run tests<br>4. Verify functionality | v1.0 |
| `dashboard/components/` | `dashboard/src/components/` | 1. Move React components<br>2. Update import paths<br>3. Test components<br>4. Verify rendering | v1.0 |

**Note**: Deprecated directories are retained for backward compatibility only. Do not add new code to these locations.

## File Naming Conventions
- **Python**: snake_case (e.g., `event_store.py`, `circuit_breaker.py`)
- **TypeScript/React**: PascalCase for components (e.g., `Dashboard.tsx`), camelCase for utilities
- **Tests**: `test_*.py` prefix for test files
- **Configuration**: Various conventions (`.json`, `.yaml`, `.toml`, `.ini`)