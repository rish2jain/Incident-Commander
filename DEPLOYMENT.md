# Deployment Guide - SwarmAI Incident Commander

Complete deployment guide for local development, AWS production, and demo environments.

---

## 🚀 Quick Start (Choose Your Path)

### Option 1: Local Development (2 minutes)

```bash
# 1. Start backend API
python src/main.py

# 2. Start dashboard (separate terminal)
cd dashboard && npm run dev

# Access at:
# - PowerDashboard: http://localhost:3000/demo
# - AI Transparency: http://localhost:3000/transparency
# - Operations: http://localhost:3000/ops
# - API Docs: http://localhost:8000/docs
```

### Option 2: Live Demo (30 seconds)

```bash
# Test production API
curl https://h8xlzr74h8.execute-api.us-east-1.amazonaws.com/health

# Result: {"status": "healthy", "timestamp": "..."}
```

### Option 3: AWS Production Deployment (5 minutes)

See [AWS CloudFront Deployment](#aws-cloudfront-deployment) below.

---

## 📋 Prerequisites

### Required Tools

```bash
# Python 3.11+
python3 --version

# Node.js 18+
node --version
npm --version

# AWS CLI v2+
aws --version
aws configure  # Configure credentials

# AWS CDK v2+ (for production deployment)
npm install -g aws-cdk
cdk --version
```

### Required Environment Variables

```bash
# AWS Configuration
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=your-account-id

# Optional: Third-party integrations
export DATADOG_API_KEY=your-key
export PAGERDUTY_API_KEY=your-key
export SLACK_BOT_TOKEN=your-token
```

---

## 🏠 Local Development

### 1. Backend Setup

```bash
# Install Python dependencies
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Start FastAPI server
python src/main.py

# API available at:
# - http://localhost:8000 (main API)
# - http://localhost:8000/docs (Swagger UI)
# - http://localhost:8000/redoc (ReDoc)
```

### 2. Dashboard Setup

```bash
# Install Node dependencies
cd dashboard
npm install

# Start development server
npm run dev

# Dashboard available at:
# - http://localhost:3000/demo (PowerDashboard)
# - http://localhost:3000/transparency (AI Transparency)
# - http://localhost:3000/ops (Operations)
```

### 3. Verify Installation

```bash
# Test backend health
curl http://localhost:8000/health

# Test WebSocket (in browser console)
const ws = new WebSocket('ws://localhost:8000/dashboard/ws');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

---

## ☁️ AWS CloudFront Deployment

Complete production deployment using CloudFront + S3 with Origin Access Control (OAC).

### Prerequisites

```bash
# Verify AWS credentials
aws sts get-caller-identity

# Bootstrap CDK (first time only)
cdk bootstrap aws://ACCOUNT-ID/us-east-1
```

### Deployment Steps

#### 1. Build Dashboard

```bash
cd dashboard
npm install
npm run build  # Creates dashboard/out/ directory
```

#### 2. Deploy Infrastructure

```bash
# Navigate to CDK directory
cd infrastructure/cdk

# Set environment
export ENVIRONMENT=production  # or 'development'

# Synthesize CloudFormation template
cdk synth

# Deploy stack
cdk deploy IncidentCommanderDashboard-${ENVIRONMENT}

# Outputs will include:
# - CloudFrontDistribution URL
# - S3 Bucket name
# - CloudFront Distribution ID
```

#### 3. Upload Dashboard

```bash
# Sync built files to S3
aws s3 sync ../../dashboard/out/ s3://YOUR-BUCKET-NAME/ --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id YOUR-DISTRIBUTION-ID \
  --paths "/*"
```

#### 4. Verify Deployment

```bash
# Wait for CloudFront propagation (2-5 minutes)
# Then access your CloudFront URL
curl https://YOUR-DISTRIBUTION-ID.cloudfront.net/
```

### Quick Deployment Script

```bash
# Use the deployment script for automated deployment
cd infrastructure/cdk
./deploy_dashboard_cloudfront.sh production

# Script performs:
# 1. Dashboard build
# 2. CDK deploy
# 3. S3 sync
# 4. CloudFront invalidation
```

---

## 🔧 Configuration

### Dashboard Environment

Create `dashboard/.env.local`:

```env
# API Configuration
NEXT_PUBLIC_API_URL=https://your-api-url.com
NEXT_PUBLIC_WS_URL=wss://your-api-url.com

# Feature Flags
NEXT_PUBLIC_ENABLE_WEBSOCKET=true
NEXT_PUBLIC_ENABLE_DEMO_MODE=false
```

### Backend Environment

Create `.env` in project root:

```env
# AWS Services
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0

# Database
DYNAMODB_TABLE_NAME=incident-events
OPENSEARCH_ENDPOINT=your-opensearch-endpoint

# Optional Integrations
DATADOG_API_KEY=your-datadog-key
PAGERDUTY_API_KEY=your-pagerduty-key
```

---

## 🎯 Deployment Architectures

### Local Development
```
┌─────────────┐     ┌──────────────┐
│   Browser   │────▶│  Next.js Dev │
│ localhost   │     │  Port 3000   │
└─────────────┘     └──────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │  FastAPI     │
                    │  Port 8000   │
                    └──────────────┘
```

### AWS Production
```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   Browser   │────▶│  CloudFront  │────▶│  S3 Bucket   │
│             │     │  (CDN + OAC) │     │  (Static)    │
└─────────────┘     └──────────────┘     └──────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │  API Gateway │
                    │  + Lambda    │
                    └──────────────┘
```

---

## 📊 Monitoring & Operations

### Health Checks

```bash
# Backend health
curl https://your-api-url/health

# WebSocket status
curl https://your-api-url/dashboard/ws/health

# Agent telemetry
curl https://your-api-url/observability/telemetry

# Business metrics
curl https://your-api-url/demo/stats
```

### CloudWatch Monitoring

```bash
# View Lambda logs
aws logs tail /aws/lambda/incident-commander --follow

# View API Gateway logs
aws logs tail /aws/apigateway/incident-commander --follow
```

---

## 🐛 Troubleshooting

### Dashboard Issues

**Problem:** Dashboard not loading
**Solution:**
```bash
cd dashboard
rm -rf .next node_modules
npm install
npm run build
```

**Problem:** WebSocket connection failed
**Solution:**
- Verify API is running: `curl http://localhost:8000/health`
- Check CORS configuration in `src/main.py`
- Ensure WebSocket endpoint is accessible

### Deployment Issues

**Problem:** CDK deployment fails
**Solution:**
```bash
# Verify AWS credentials
aws sts get-caller-identity

# Ensure CDK is bootstrapped
cdk bootstrap

# Check CloudFormation events
aws cloudformation describe-stack-events \
  --stack-name IncidentCommanderDashboard-production
```

**Problem:** CloudFront serves 403 errors
**Solution:**
- Verify S3 bucket policy allows CloudFront OAC
- Check CloudFront distribution settings
- Ensure `index.html` exists in S3 root

**Problem:** Old content cached
**Solution:**
```bash
# Create invalidation
aws cloudfront create-invalidation \
  --distribution-id YOUR-ID \
  --paths "/*"
```

---

## 📚 Additional Resources

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Detailed CloudFront deployment guide
- **[DEPLOYMENT_QUICK_REFERENCE.md](DEPLOYMENT_QUICK_REFERENCE.md)** - Quick reference card
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture documentation
- **[hackathon/README.md](hackathon/README.md)** - Hackathon-specific deployment notes
- **[archive/docs/deployment/](archive/docs/deployment/)** - Historical deployment documentation

---

## 🎓 Deployment Best Practices

1. **Always build locally first** - Test `npm run build` before deploying
2. **Use environment-specific stacks** - Separate dev/staging/production
3. **Enable CloudFront logging** - Track access patterns and errors
4. **Set up CloudWatch alarms** - Monitor API errors and latency
5. **Use CDK for infrastructure** - Keep infrastructure as code
6. **Invalidate CloudFront cache** - After every deployment
7. **Test health endpoints** - Before marking deployment complete

---

**Last Updated:** October 24, 2025
**Maintained By:** SwarmAI Development Team
**Status:** Production Ready ✅
