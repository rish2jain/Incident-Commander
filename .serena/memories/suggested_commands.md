# Suggested Commands for Development

## Quick Start Commands

### Start Demo (Recommended)
```bash
# One-command demo startup (opens browser)
python start_demo.py

# Modern Next.js dashboard system (recommended)
cd dashboard && npm run dev
# In separate terminal:
python src/main.py
```

### Judge/Hackathon Demo
```bash
# Quick 30-second judge setup
make judge-quick-start

# Preset demos
make demo-quick          # 2-minute overview
make demo-technical      # 5-minute technical deep dive
make demo-business       # 3-minute business value
make demo-interactive    # Full interactive exploration
make demo-aws-ai         # 4-minute AWS AI showcase
```

## Development Setup

### Initial Setup
```bash
# Clone and setup
git clone <repository-url>
cd incident-commander
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Start services
docker-compose up -d

# Configure environment
cp .env.example .env
# Edit .env as needed

# Initialize AWS resources (LocalStack)
awslocal dynamodb create-table --table-name incident-commander-events \
  --attribute-definitions AttributeName=incident_id,AttributeType=S \
  --key-schema AttributeName=incident_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

awslocal kinesis create-stream --stream-name incident-events --shard-count 1

# Verify setup
python scripts/verify_setup.py
```

### Frontend Setup
```bash
cd dashboard
npm install
npm run dev  # Starts on port 3000
```

## Testing Commands

### Python Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov=agents --cov-report=term-missing

# Run specific test types
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests only
pytest -m agent          # Agent-specific tests
pytest -m "not slow"     # Skip slow tests

# Run specific test file
pytest tests/test_foundation.py -v

# Run with verbose output
pytest -v -s

# Comprehensive validation
python run_comprehensive_tests.py
```

### Frontend Testing
```bash
cd dashboard
npm test              # Run Jest tests
npm run test:watch    # Watch mode
```

## Code Quality Commands

### Python Formatting & Linting
```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint with ruff
ruff check src/ tests/

# Type checking
mypy src/

# Security scanning
bandit -r src/

# All quality checks
black src/ tests/ && isort src/ tests/ && ruff check src/ tests/ && mypy src/
```

### Frontend Linting
```bash
cd dashboard
npm run lint              # ESLint
npx tsc --noEmit         # Type checking only
```

## Running the Application

### Development Server
```bash
# Backend (FastAPI)
python -m uvicorn src.main:app --reload --port 8000

# Frontend (Next.js)
cd dashboard && npm run dev

# Both with demo
python start_demo.py
```

### Production Mode
```bash
# Backend
python src/main.py

# Frontend (build first)
cd dashboard
npm run build
npm start
```

## Docker Commands

### Service Management
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart specific service
docker-compose restart redis

# Clean rebuild
docker-compose down -v
docker-compose up -d --build
```

## Health & Status Checks

### API Health
```bash
# Basic health check
curl http://localhost:8000/health

# Detailed system status
curl http://localhost:8000/status

# Performance metrics
curl http://localhost:8000/performance-metrics
```

### Service Verification
```bash
# Verify all services
python scripts/verify_setup.py

# Check Docker services
docker-compose ps

# Validate configuration
python -c "from src.utils.config import config; config.validate_required_config()"
```

## Makefile Commands
```bash
# See all available commands
make help

# Setup and validate
make setup-demo
make validate-demo
make health-check

# Demo management
make demo-reset          # Reset demo state
make cleanup-demo        # Full cleanup

# Advanced demos
make demo-with-fault-injection
make demo-with-compliance
make demo-record         # Generate HD recording
```

## Hackathon Validation
```bash
# Final validation
python hackathon/final_hackathon_validation.py

# Comprehensive validation
python hackathon/comprehensive_demo_validation.py

# Task-specific validation
make validate-task-12
make validate-task-22
```

## Utility Commands (macOS/Darwin)

### System Commands
```bash
# File operations
ls -la                    # List all files with details
find . -name "*.py"       # Find Python files
grep -r "pattern" src/    # Search in files
tree -L 2                 # Show directory tree (if installed)

# Process management
lsof -i :8000            # Check what's using port 8000
ps aux | grep python     # Find Python processes
kill -9 <PID>            # Force kill process

# Git operations
git status
git branch
git log --oneline -10
git diff
```

## Environment Management
```bash
# Python virtual environment
python -m venv .venv
source .venv/bin/activate
deactivate

# View environment info
python -c "from src.utils.config import config; print(config.get_environment_info())"
```