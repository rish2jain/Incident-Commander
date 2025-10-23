# Codebase Structure

## Root Layout
```
incident-commander/
├── src/                          # Backend Python source code
├── dashboard/                    # Frontend Next.js application
├── tests/                        # Python test suite
├── hackathon/                    # Hackathon submission materials
├── infrastructure/               # AWS CDK deployment code
├── claudedocs/                   # Claude-specific documentation
├── agents/                       # Agent implementations (if separate)
├── monitoring/                   # Monitoring and observability
├── .kiro/                        # Kiro IDE configuration
├── .github/                      # GitHub workflows
└── scripts/                      # Utility scripts
```

## Backend Structure (src/)
```
src/
├── api/                          # FastAPI routers and endpoints
├── services/                     # Core services (agents, WebSocket, AWS)
├── utils/                        # Utility functions and helpers
├── models/                       # Data models
├── schemas/                      # Pydantic schemas
├── interfaces/                   # Abstract base classes
├── orchestrator/                 # Agent orchestration
├── main.py                       # FastAPI application entry point
├── detection_agent.py            # Detection agent implementation
├── real_aws_ai_orchestrator.py   # AWS AI orchestration
├── health_check.py               # Health check logic
└── lambda_handler.py             # AWS Lambda handler
```

## Frontend Structure (dashboard/)
```
dashboard/
├── app/                          # Next.js 13+ app directory
│   ├── demo/                     # Dashboard 1: PowerDashboard (executive)
│   ├── transparency/             # Dashboard 2: AI transparency (engineering)
│   └── ops/                      # Dashboard 3: Operations monitoring
├── src/components/               # React components
├── public/                       # Static assets
├── next.config.js                # Next.js configuration
├── tailwind.config.js            # Tailwind CSS config
└── tsconfig.json                 # TypeScript configuration
```

## Test Structure (tests/)
```
tests/
├── unit/                         # Unit tests
├── integration/                  # Integration tests
├── manual/                       # Manual/demo tests
├── contract/                     # Contract tests
├── load/                         # Load/performance tests
├── benchmarks/                   # Benchmark tests
├── validation/                   # Validation tests
├── mocks/                        # Mock objects
├── patches/                      # Test patches
└── conftest.py                   # Pytest configuration
```

## Documentation Hierarchy
- **User Docs**: README.md, DEMO_GUIDE.md, API.md
- **Technical Docs**: ARCHITECTURE.md, DEPLOYMENT.md
- **Hackathon**: hackathon/MASTER_SUBMISSION_GUIDE.md, COMPREHENSIVE_JUDGE_GUIDE.md
- **Claude Docs**: claudedocs/ (Claude-specific analysis and reports)

## Key Configuration Files
- **Python**: pyproject.toml, pytest.ini, requirements.txt
- **Node.js**: package.json, tsconfig.json
- **Docker**: docker-compose.yml, Dockerfile
- **AWS**: cdk.json, cdk.context.json
- **Git**: .gitignore, .pre-commit-config.yaml
- **Environment**: .env.example, .env.production.template