# Suggested Commands

## Environment Setup
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# .venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration
```

## Development Server
```bash
# Start FastAPI server with hot reload
python -m uvicorn src.main:app --reload --port 8000

# Access API documentation
open http://localhost:8000/docs  # OpenAPI/Swagger UI
open http://localhost:8000/redoc  # ReDoc alternative
```

## Testing
```bash
# Run all tests with verbose output
python -m pytest tests/ -v

# Run foundation tests specifically
python -m pytest tests/test_foundation.py -v

# Run with coverage report
python -m pytest tests/ --cov=src --cov=agents

# Run coverage with HTML report
python -m pytest tests/ --cov=src --cov=agents --cov-report=html
# Then open htmlcov/index.html

# Run specific test file
python -m pytest tests/test_<module>.py -v

# Run specific test function
python -m pytest tests/test_<module>.py::test_function_name -v
```

## Code Quality
```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Format code with black
black src agents tests

# Sort imports with isort
isort src agents tests

# Type check with mypy
mypy src agents

# Individual checks
black --check src agents tests  # Check without modifying
isort --check src agents tests  # Check import sorting
```

## Local Development Infrastructure
```bash
# Start LocalStack and other services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Use LocalStack AWS CLI
awslocal s3 ls
awslocal dynamodb list-tables
```

## Verification & Validation
```bash
# Verify complete setup
python scripts/verify_setup.py

# Check system health
curl http://localhost:8000/health

# Get system status
curl http://localhost:8000/status
```

## Git & Version Control
```bash
# Check status
git status
git branch

# Create feature branch
git checkout -b feature/<feature-name>

# Commit with conventional commit format
git commit -m "feat: add new capability"
git commit -m "fix: resolve issue with X"
git commit -m "docs: update README"
git commit -m "infra: add CDK stack"
```

## Utility Commands (macOS/Darwin)
```bash
# File operations
ls -la          # List all files with details
find . -name "*.py"  # Find Python files
grep -r "pattern" src/  # Search in files

# Process management
ps aux | grep python  # Find Python processes
kill -9 <PID>        # Force kill process

# Network
lsof -i :8000    # Check what's using port 8000
netstat -an      # Network connections

# System info
uname -a         # System information
python --version # Python version
pip list         # Installed packages
```

## AWS Operations (Production)
```bash
# Configure AWS CLI (real AWS)
aws configure

# Check credentials
aws sts get-caller-identity

# List resources
aws dynamodb list-tables --region us-east-1
aws kinesis list-streams --region us-east-1
```