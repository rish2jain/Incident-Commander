# SwarmAI - Suggested Commands and Workflows

## Development Workflows

### Initial Setup
```bash
# Clone repository
git clone <repository-url>
cd incident-commander

# Python environment setup
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Start required services (Docker)
docker-compose up -d

# Verify services are running
docker-compose ps

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Initialize AWS resources (LocalStack)
awslocal dynamodb create-table \
  --table-name incident-commander-events \
  --attribute-definitions AttributeName=incident_id,AttributeType=S \
  --key-schema AttributeName=incident_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

awslocal kinesis create-stream \
  --stream-name incident-events \
  --shard-count 1

# Verify setup
python scripts/verify_setup.py

# Frontend setup
cd dashboard
npm install
cd ..
```

### Daily Development
```bash
# Start backend (development mode with hot reload)
python -m uvicorn src.main:app --reload --port 8000

# Or use the demo script
python start_demo.py

# Start frontend (separate terminal)
cd dashboard
npm run dev

# Access dashboards
# - Demo: http://localhost:3000/demo
# - Transparency: http://localhost:3000/transparency
# - Operations: http://localhost:3000/ops
# - API Docs: http://localhost:8000/docs
# - Classic Demo: http://localhost:8000
```

## Testing Commands

### Python Tests
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_foundation.py

# Run specific test function
pytest tests/test_foundation.py::test_incident_detection

# Run tests by marker
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m "not slow"    # Skip slow tests
pytest -m agent         # Agent-specific tests

# Run comprehensive tests
python run_comprehensive_tests.py

# Watch mode (requires pytest-watch)
ptw  # or pytest-watch
```

### Frontend Tests
```bash
cd dashboard

# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run with coverage
npm test -- --coverage

# Run specific test file
npm test -- IncidentCard.test.tsx
```

### Code Quality Checks
```bash
# Python linting
ruff check src/
ruff check tests/

# Python formatting (check only)
black --check src/
black --check tests/

# Python formatting (apply)
black src/
black tests/

# Import sorting (check)
isort --check-only src/
isort --check-only tests/

# Import sorting (apply)
isort src/
isort tests/

# Type checking
mypy src/

# Security scanning
bandit -r src/

# All pre-commit checks
pre-commit run --all-files

# Frontend linting
cd dashboard
npm run lint

# Frontend type checking
cd dashboard
npx tsc --noEmit
```

## Deployment Commands

### Local Docker Deployment
```bash
# Build Docker image
docker build -t swarm-ai:latest .

# Run Docker container
docker run -p 8000:8000 \
  --env-file .env \
  --name swarm-ai \
  swarm-ai:latest

# Docker Compose (full stack)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### AWS CDK Deployment
```bash
# Install CDK (if not already installed)
npm install -g aws-cdk

# Navigate to CDK directory
cd infrastructure/cdk

# Install dependencies
pip install -r requirements.txt

# Bootstrap CDK (first time only)
cdk bootstrap

# Synthesize CloudFormation template
cdk synth

# Deploy all stacks
cdk deploy --all

# Deploy specific stack
cdk deploy NetworkStack
cdk deploy DatabaseStack
cdk deploy ComputeStack

# View differences before deploy
cdk diff

# Destroy stacks (careful!)
cdk destroy --all
```

### Production Deployment (Automated)
```bash
# Complete production deployment (8-phase automation)
./run_deployment.sh --environment production --full-deployment

# Setup monitoring with detailed dashboards
python setup_monitoring.py \
  --environment production \
  --enable-detailed-monitoring

# Validate deployment
python validate_deployment.py --environment production

# Test AWS integration
python test_aws_integration.py \
  --environment production \
  --verbose

# Test complete deployment system
python hackathon/test_complete_deployment_system.py \
  --environment production

# Check system status
python check_system_status.py --environment production
```

### Core System Deployment Scripts
```bash
# Deploy core system (Phase 1-4)
python deploy_core_system.py --environment production

# Deploy complete system (Phase 1-8)
python deploy_complete_system.py --environment production

# Deploy with validation
python deploy_validated_system.py --environment production

# Production deployment with all checks
python deploy_production.py --environment production
```

## Monitoring & Debugging

### Health Checks
```bash
# Backend health
curl http://localhost:8000/health

# Detailed status
curl http://localhost:8000/status

# Frontend health (in browser)
# http://localhost:3000/api/health
```

### Logs
```bash
# Backend logs (if using systemd)
journalctl -u swarm-ai -f

# Docker logs
docker-compose logs -f app

# CloudWatch logs (production)
aws logs tail /aws/lambda/incident-commander --follow

# View specific log group
aws logs tail /incident-commander/detection-agent --follow
```

### Metrics
```bash
# Prometheus metrics endpoint
curl http://localhost:8000/metrics

# CloudWatch metrics (production)
# Replace <START_ISO> and <END_ISO> with actual ISO 8601 timestamps
# Example: export START_ISO=$(date -u -d '1 day ago' '+%Y-%m-%dT%H:%M:%SZ')
#          export END_ISO=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
aws cloudwatch get-metric-statistics \
  --namespace SwarmAI \
  --metric-name IncidentCount \
  --start-time <START_ISO> \
  --end-time <END_ISO> \
  --period 3600 \
  --statistics Sum
```

### Debugging
```bash
# Python debugger (add to code)
import pdb; pdb.set_trace()

# Or use breakpoint() (Python 3.7+)
breakpoint()

# Run with debugger
python -m pdb src/main.py

# Interactive Python shell with app context
python -c "from src.main import app; import IPython; IPython.embed()"
```

## Demo & Hackathon Commands

### Demo Recording
```bash
# Quick demo recording
python quick_demo_record.py

# Comprehensive demo recording
python record_demo.py

# Enhanced demo recorder
python test_enhanced_recorder.py

# Comprehensive demo recorder with all features
cd scripts
python comprehensive_demo_recorder.py
```

### Demo Execution
```bash
# Start simple demo
python start_simple.py

# Start full demo with dashboard
python start_demo.py

# Run specific demo scenario
curl -X POST http://localhost:8000/demo/scenarios/database_outage
curl -X POST http://localhost:8000/demo/scenarios/memory_leak
curl -X POST http://localhost:8000/demo/scenarios/api_cascade_failure
```

### Hackathon Validation
```bash
# Final hackathon validation
cd hackathon
python final_hackathon_validation.py

# Test complete deployment system
python hackathon/test_complete_deployment_system.py \
  --environment production
```

## Maintenance Commands

### Database Maintenance
```bash
# DynamoDB backup (production)
aws dynamodb create-backup \
  --table-name incident-commander-events \
  --backup-name events-backup-$(date +%Y%m%d)

# DynamoDB restore
aws dynamodb restore-table-from-backup \
  --target-table-name incident-commander-events-restored \
  --backup-arn <backup-arn>

# OpenSearch snapshot
aws opensearch create-snapshot \
  --domain-name incident-patterns \
  --snapshot-name snapshot-$(date +%Y%m%d)
```

### Cache Management
```bash
# Clear Redis cache
redis-cli FLUSHDB

# Redis info
redis-cli INFO

# Redis monitor (watch commands)
redis-cli MONITOR
```

### Cleanup
```bash
# Clean Python cache
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete

# Clean test artifacts
rm -rf .pytest_cache
rm -rf htmlcov
rm -rf .coverage

# Clean build artifacts
rm -rf build/
rm -rf dist/
rm -rf **/*.egg-info/

# Frontend cleanup
cd dashboard
rm -rf .next
rm -rf node_modules
rm -rf .turbo

# Docker cleanup
docker system prune -a
docker volume prune
```

## Git Workflows

### Feature Development
```bash
# Create feature branch
git checkout -b feature/new-agent

# Regular commits
git add .
git commit -m "feat(agents): implement new agent"

# Push to remote
git push -u origin feature/new-agent

# Create pull request (using GitHub CLI)
gh pr create --title "Add new agent" --body "Description"
```

### Code Review
```bash
# Fetch latest changes
git fetch origin

# Checkout PR for review
gh pr checkout 123

# View changes
git diff main

# Run tests
pytest

# Leave review comment
gh pr review 123 --comment -b "LGTM!"
```

### Release Process
```bash
# Update version
# Edit src/version.py

# Create release tag
git tag -a v0.2.0 -m "Release v0.2.0"

# Push tag
git push origin v0.2.0

# Create GitHub release
gh release create v0.2.0 \
  --title "v0.2.0" \
  --notes "Release notes here"
```

## Useful Aliases
```bash
# Add to ~/.bashrc or ~/.zshrc

# Python
alias venv="source .venv/bin/activate"
alias pytest-cov="pytest --cov=src --cov-report=term-missing"
alias fmt="black src/ tests/ && isort src/ tests/"
alias lint="ruff check src/ tests/ && mypy src/"

# Docker
alias dcu="docker-compose up -d"
alias dcd="docker-compose down"
alias dcl="docker-compose logs -f"
alias dps="docker ps"

# Git
alias gs="git status"
alias gl="git log --oneline --graph --all"
alias gp="git push"
alias gc="git commit -m"

# SwarmAI specific
alias demo="python start_demo.py"
alias test-all="pytest && cd dashboard && npm test && cd .."
alias deploy-prod="python deploy_production.py --environment production"
```

## Performance Profiling
```bash
# Python profiling
python -m cProfile -o profile.stats src/main.py
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(20)"

# Memory profiling (requires memory_profiler)
python -m memory_profiler src/main.py

# Load testing with Locust
locust -f tests/load_test.py --host=http://localhost:8000
```

## Environment Management
```bash
# List environments
aws elasticbeanstalk describe-environments

# Switch environment
export ENVIRONMENT=staging
export ENVIRONMENT=production

# View current configuration
python -c "from src.utils.config import config; print(config.get_environment_info())"

# Validate configuration
python -c "from src.utils.config import config; config.validate_required_config()"
```
