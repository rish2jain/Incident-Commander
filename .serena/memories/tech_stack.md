# SwarmAI - Technology Stack

## Backend Stack (Python 3.11+)

### Core Framework
- **FastAPI** (>=0.104.0) - Modern async web framework with automatic OpenAPI docs
- **Uvicorn[standard]** (>=0.24.0) - ASGI server with WebSocket support
- **Pydantic** (>=2.5.0) - Data validation and settings management

### AWS Integration
- **boto3** (>=1.34.0) - AWS SDK for Python (sync operations)
- **aioboto3** (>=12.0.0) - Async AWS SDK (for concurrent operations)
- **AWS Services Used**:
  - DynamoDB (event persistence with optimistic locking)
  - EventBridge (event-driven architecture)
  - Kinesis (event streaming with partition keys)
  - Lambda (serverless agent execution)
  - API Gateway (production REST API)
  - CloudWatch (monitoring, logging, metrics)
  - OpenSearch Serverless (RAG memory, vector search)
  - Bedrock (7 AI services - AgentCore, Claude, Titan, Q, Nova, Guardrails, Strands)
  - S3 (artifact storage)

### Data & Communication
- **redis[hiredis]** (>=5.0.0) - Message bus failover and agent communication
- **asyncio-mqtt** (>=0.16.0) - Async MQTT for event streaming
- **websockets** (>=12.0) - WebSocket server for real-time updates
- **httpx** (>=0.25.0) - Modern async HTTP client

### AI & Machine Learning
- **chromadb** (>=0.4.0) - Vector database for embeddings
- **langchain** (>=0.1.0) - LLM application framework
- **langgraph** (>=0.0.40) - Graph-based agent orchestration
- **openai** (>=1.6.0) - OpenAI SDK (compatible with Bedrock)

### Observability & Resilience
- **prometheus-client** (>=0.19.0) - Metrics collection and export
- **structlog** (>=23.2.0) - Structured logging with JSON output
- **tenacity** (>=8.2.0) - Retry logic with exponential backoff

### Development Tools
- **pytest** (>=7.4.0) - Testing framework with async support
- **pytest-asyncio** (>=0.21.0) - Async test support
- **pytest-cov** (>=4.1.0) - Coverage reporting
- **pytest-mock** (>=3.12.0) - Mock/patch utilities
- **black** (>=23.12.0) - Code formatter (line-length: 100)
- **isort** (>=5.13.0) - Import sorting (black profile)
- **ruff** (>=0.1.9) - Fast Python linter
- **mypy** (>=1.8.0) - Static type checker
- **bandit** (>=1.7.5) - Security vulnerability scanner
- **pre-commit** (>=3.6.0) - Git hook framework
- **locust** (>=2.17.0) - Load testing
- **moto[all]** (>=4.2.0) - AWS service mocking

## Frontend Stack (TypeScript)

### Core Framework
- **Next.js** (^16.0.0) - React framework with App Router
- **React** (^18.3.1) - UI library with modern hooks
- **React-DOM** (^18.3.1) - React rendering
- **TypeScript** (^5.2.0) - Static typing

### UI Components & Styling
- **Tailwind CSS** (^3.3.0) - Utility-first CSS framework
- **tailwindcss-animate** (^1.0.7) - Animation utilities
- **tailwind-merge** (^3.3.1) - Tailwind class merging
- **class-variance-authority** (^0.7.1) - Component variants
- **Radix UI** - Accessible component primitives:
  - @radix-ui/react-avatar (^1.1.10)
  - @radix-ui/react-dialog (^1.1.15)
  - @radix-ui/react-dropdown-menu (^2.1.16)
  - @radix-ui/react-progress (^1.1.7)
  - @radix-ui/react-scroll-area (^1.2.10)
  - @radix-ui/react-select (^2.2.6)
  - @radix-ui/react-separator (^1.1.7)
  - @radix-ui/react-slot (^1.2.3)
  - @radix-ui/react-tabs (^1.1.13)
  - @radix-ui/react-tooltip (^1.2.8)
- **lucide-react** (^0.546.0) - Icon library
- **next-themes** (^0.4.6) - Theme switching

### 3D & Animation
- **three** (^0.180.0) - 3D graphics library
- **three-stdlib** (^2.25.0) - Three.js utilities
- **@react-three/fiber** (^8.15.0) - React renderer for Three.js
- **@react-three/drei** (^9.88.0) - Three.js helpers
- **framer-motion** (^12.23.24) - Animation library

### Data & Communication
- **ws** (^8.14.0) - WebSocket client
- **uuid** (^9.0.1) - UUID generation
- **react-window** (^2.2.1) - Virtual scrolling for large lists

### Development & Testing
- **eslint** (^8.51.0) - Linting
- **eslint-config-next** (^15.5.6) - Next.js ESLint config
- **jest** (^29.7.0) - Testing framework
- **jest-environment-jsdom** (^30.2.0) - Browser-like test environment
- **@testing-library/react** (^16.3.0) - React testing utilities
- **@testing-library/jest-dom** (^6.1.0) - DOM matchers
- **TypeScript types**:
  - @types/node (^20.19.23)
  - @types/react (^18.3.26)
  - @types/react-dom (^18.3.7)
  - @types/three (^0.180.0)
  - @types/uuid (^10.0.0)
  - @types/ws (^8.5.0)
  - @types/react-window (^1.8.8)

## Infrastructure & DevOps

### Infrastructure as Code
- **AWS CDK** - Multi-stack architecture
- **Docker** - Containerization
- **Docker Compose** - Local development orchestration

### CI/CD & Deployment
- **GitHub Actions** - CI/CD pipelines
- **AWS Amplify** - Static site hosting
- **LocalStack** - AWS service simulation for local development

### Monitoring & Observability
- **CloudWatch** - Logs, metrics, alarms, dashboards
- **OpenTelemetry** - Distributed tracing (planned)
- **Prometheus** - Metrics collection
- **Datadog** - External monitoring (optional)

### Security & Compliance
- **IAM** - Role-based access control
- **KMS** - Encryption key management
- **Secrets Manager** - Secret rotation
- **Bedrock Guardrails** - AI safety controls

## Code Quality Standards

### Python Configuration (pyproject.toml)
- **Black**: line-length=100, target=py311
- **isort**: profile="black", line_length=100
- **Ruff**: 
  - Select: E, W, F, I, B, C4, UP, ARG001, SIM, TCH, TID, Q, FLY, PERF, RUF
  - Ignore: E501 (line too long), B008, C901, W191
- **MyPy**: strict typing with python_version=3.11
- **Pytest**: 
  - Coverage target: 60%
  - Async mode: auto
  - Markers: slow, integration, unit, e2e, agent, manual

### TypeScript Configuration
- **ESLint**: Next.js config with strict rules
- **TypeScript**: Strict mode enabled
- **Prettier**: Integrated with Tailwind

## Environment Requirements

### Development
- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- 8GB+ RAM
- Redis (via Docker)
- LocalStack (via Docker)

### Production
- AWS Account with configured CLI
- IAM roles for Bedrock, DynamoDB, Kinesis, S3
- Managed Redis (ElastiCache) with SSL
- RDS or managed database services
- CDN (CloudFront) for static assets

## Version Control & Branching
- **Git** - Version control
- **Main Branch**: Production-ready code
- **Feature Branches**: For development
- **Pre-commit Hooks**: Automated code quality checks
