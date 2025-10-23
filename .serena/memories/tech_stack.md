# Technology Stack

## Backend (Python 3.11+)
- **Framework**: FastAPI + Uvicorn
- **Async Runtime**: asyncio, aioboto3, aiohttp
- **Data Validation**: Pydantic v2.5+
- **AWS SDK**: boto3, aioboto3, botocore

## AWS Services
- **AI/ML**: Bedrock (Claude, Titan), Amazon Q, Nova Act, Strands SDK
- **Storage**: S3, DynamoDB
- **Streaming**: Kinesis
- **Search**: OpenSearch Serverless
- **Infrastructure**: LocalStack (dev), AWS CDK (prod)

## Data & Caching
- **Cache/Message Bus**: Redis 5.0+ (with hiredis)
- **Data Processing**: numpy, pandas, scikit-learn

## Frontend (Next.js 16 + React 18.3)
- **Framework**: Next.js 16.0.0 with Turbopack
- **UI Library**: React 18.3.1 + TypeScript 5.2
- **Styling**: Tailwind CSS 3.3 + PostCSS
- **Components**: Radix UI, Framer Motion 12.23
- **3D Visualization**: Three.js 0.180 + @react-three/fiber + @react-three/drei
- **Icons**: Lucide React 0.546

## Communication
- **WebSocket**: websockets 12.0, python-socketio, ws
- **HTTP**: requests, httpx, aiohttp

## Security
- **Cryptography**: cryptography 41.0+, pycryptodome 3.19+
- **Auth**: PyJWT 2.8+, python-jose 3.3+, passlib 1.7+

## Observability
- **Monitoring**: Prometheus, psutil, memory-profiler
- **Telemetry**: OpenTelemetry API/SDK 1.21+
- **Structured Logging**: structlog (implicit from AWS integrations)

## Testing
- **Framework**: pytest 7.4+ with pytest-asyncio, pytest-cov, pytest-mock
- **Coverage**: 80% minimum requirement
- **Mocking**: requests-mock, moto[all]
- **Frontend Testing**: Jest 29.7, @testing-library/react, @testing-library/jest-dom

## Development Tools
- **Formatting**: black (line-length 100), isort
- **Linting**: ruff, flake8, mypy, eslint
- **Security**: bandit
- **Pre-commit**: pre-commit hooks configured

## Infrastructure
- **Containerization**: Docker + Docker Compose
- **IaC**: AWS CDK (TypeScript)
- **Package Management**: pip (Python), npm (Node.js)