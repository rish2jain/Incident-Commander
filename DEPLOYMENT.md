# Deployment Guide - Autonomous Incident Commander

## Quick Start

### Local Development

```bash
# 1. Environment setup
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Start local services
docker-compose up -d

# 3. Initialize LocalStack
awslocal bedrock create-agent --agent-name incident-commander

# 4. Start development servers
uvicorn src.main:app --reload --port 8000  # Backend API
cd dashboard && npm install && npm run dev  # Frontend at http://localhost:3000
```

### Production Deployment

```bash
# Deploy complete system to AWS
cd hackathon && python deploy_hackathon_demo.py

# Validate deployment
cd hackathon && python validate_hackathon_deployment.py
```

## System Requirements

### Local Development

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- AWS CLI configured

### Production

- AWS Account with appropriate permissions
- CDK CLI installed
- Domain name (optional)

## Environment Configuration

### Required Environment Variables

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=your-account-id

# API Keys
DATADOG_API_KEY=your-datadog-key
PAGERDUTY_API_KEY=your-pagerduty-key
SLACK_BOT_TOKEN=your-slack-token

# Database
DYNAMODB_TABLE_NAME=incident-events
OPENSEARCH_ENDPOINT=your-opensearch-endpoint
```

## Architecture Components

### Backend Services

- **FastAPI** - 50+ REST API endpoints
- **AWS Lambda** - Serverless agent functions
- **DynamoDB** - Event sourcing and state persistence
- **OpenSearch** - Vector database for RAG
- **Kinesis** - Real-time event streaming

### Frontend

- **Next.js 14** - Modern React framework
- **Three specialized dashboards** - Demo, Transparency, Operations
- **WebSocket integration** - Real-time updates
- **Professional UI/UX** - Glassmorphism design

## Monitoring & Operations

### Health Checks

- API: `https://your-api-url/health`
- Agent telemetry: `https://your-api-url/observability/telemetry`
- Business metrics: `https://your-api-url/demo/stats`

### Troubleshooting

- Check CloudWatch logs for agent execution
- Verify DynamoDB table permissions
- Ensure Bedrock model access
- Validate WebSocket connections

---

**Live Demo**: https://h8xlzr74h8.execute-api.us-east-1.amazonaws.com  
**Dashboard**: http://localhost:3000 (local development)
