# Tech Stack

## Language & Runtime
- **Python 3.11+** (required)
- Type hints enforced with mypy

## Web Framework
- **FastAPI** (0.104.1) - API server with async support
- **Uvicorn** (0.24.0) - ASGI server with hot reload
- **Pydantic** (2.5.0) - Data validation and models

## AWS Services
- **boto3** / **aioboto3** - AWS SDK
- **Kinesis** - Event streaming with partition key distribution
- **DynamoDB** - Event persistence with optimistic locking
- **OpenSearch Serverless** - Vector search for RAG memory
- **Bedrock** - Claude 3 Sonnet/Haiku for agent reasoning
- **IAM** - Role assumption with least privilege

## Data & Storage
- **Redis** (5.0.1) - Caching and rate limiting
- **OpenSearch** (2.4.0) - Hierarchical indexing for 100K+ incidents

## Monitoring & Observability
- **structlog** (23.2.0) - Structured logging with correlation IDs
- **prometheus-client** (0.19.0) - Metrics collection
- **Datadog API** - External monitoring integration
- **PagerDuty API** - Incident escalation
- **Slack Bot** - Communication agent

## Machine Learning
- **numpy** (1.24.4) - Numerical computing
- **scikit-learn** (1.3.2) - Pattern recognition
- **Bedrock Titan** - Embedding generation (1536 dimensions)

## Security & Crypto
- **cryptography** (41.0.8) - Event integrity verification
- **python-jose** (3.3.0) - Cryptographic operations

## Development & Testing
- **pytest** (7.4.3) - Test framework (37 tests passing)
- **pytest-asyncio** (0.21.1) - Async test support
- **pytest-cov** (4.1.0) - Coverage reporting (target ≥80%)
- **pytest-mock** (3.12.0) - Mocking utilities
- **black** (23.11.0) - Code formatting
- **isort** (5.12.0) - Import sorting
- **mypy** (1.7.1) - Static type checking
- **pre-commit** (3.6.0) - Git hooks for quality

## Chaos & Load Testing
- **locust** (2.17.0) - Load testing
- **chaos-toolkit** (1.16.0) - Chaos engineering

## Local Development
- **LocalStack** - AWS service emulation
- **Docker** & **Docker Compose** - Containerization