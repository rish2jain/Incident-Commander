# Task Completion Checklist

When a development task is completed, follow this checklist to ensure quality and consistency:

## 1. Code Quality Checks

### Python Code
```bash
# Format code with Black
black src/ tests/

# Sort imports
isort src/ tests/

# Run linting
ruff check src/ tests/

# Type checking
mypy src/

# Security scan
bandit -r src/
```

### TypeScript/React Code
```bash
cd dashboard

# Lint JavaScript/TypeScript
npm run lint

# Type checking
npx tsc --noEmit
```

## 2. Run Tests

### Unit Tests
```bash
# Run all unit tests
pytest -m unit -v

# With coverage
pytest -m unit --cov=src --cov=agents --cov-report=term-missing
```

### Integration Tests
```bash
# Run integration tests
pytest -m integration -v

# Specific test file
pytest tests/test_milestone1_integration.py -v
```

### Coverage Requirements
- **Minimum**: 80% code coverage (configured in pytest.ini)
- **Target**: 90%+ for critical paths
- **Check**: `pytest --cov=src --cov-report=html` and review htmlcov/index.html

## 3. Manual Testing

### Backend Testing
```bash
# Start backend server
python -m uvicorn src.main:app --reload

# Test health endpoints
curl http://localhost:8000/health
curl http://localhost:8000/status

# Test specific features (if applicable)
# Example: trigger incident
curl -X POST http://localhost:8000/incidents/trigger -H "Content-Type: application/json" -d '{"scenario": "test"}'
```

### Frontend Testing
```bash
# Start frontend
cd dashboard && npm run dev

# Manual browser testing:
# - Navigate to http://localhost:3000
# - Test key user flows
# - Check responsive design
# - Verify WebSocket connections
```

## 4. Verify Integration

### Services Check
```bash
# Ensure Docker services are running
docker-compose ps

# Verify Redis
redis-cli ping

# Verify LocalStack (if needed)
awslocal dynamodb list-tables
awslocal kinesis list-streams
```

### System Health
```bash
# Comprehensive health check
make health-check

# Or manually:
python scripts/verify_setup.py
```

## 5. Documentation

### Code Documentation
- [ ] All public functions have docstrings
- [ ] Complex logic has inline comments
- [ ] Type hints are present and accurate
- [ ] README updated if API changes

### Technical Documentation
- [ ] Update ARCHITECTURE.md if architecture changed
- [ ] Update API.md if endpoints added/modified
- [ ] Add migration notes if breaking changes

## 6. Git Workflow

### Before Committing
```bash
# Check git status
git status

# Review changes
git diff

# Verify on correct branch (not main/master)
git branch
```

### Commit Standards
```bash
# Stage relevant changes
git add <files>

# Commit with descriptive message
git commit -m "feat: add detection agent timeout handling

- Add configurable timeout for detection operations
- Implement graceful degradation on timeout
- Add tests for timeout scenarios"

# Push to feature branch
git push origin feature/detection-agent-timeout
```

### Commit Message Format
- **Prefix**: feat, fix, refactor, test, docs, chore
- **Subject**: Imperative, concise (50 chars)
- **Body**: Detailed explanation (if needed)
- **Footer**: Issue references, breaking changes

## 7. Performance Validation

### Check Performance Targets
Verify agents meet performance targets (defined in README):

| Agent         | Target | Max  |
|--------------|--------|------|
| Detection    | 30s    | 60s  |
| Diagnosis    | 120s   | 180s |
| Prediction   | 90s    | 150s |
| Resolution   | 180s   | 300s |
| Communication| 10s    | 30s  |

### Benchmark Testing
```bash
# Run benchmarks if applicable
pytest -m benchmark -v

# Check for performance regressions
python tests/benchmarks/benchmark_agents.py
```

## 8. Security Review

### Checklist
- [ ] No secrets in code
- [ ] Input validation on all external data
- [ ] Proper error handling (no sensitive data in errors)
- [ ] Authentication/authorization applied
- [ ] Dependencies up to date
- [ ] Security scan passed (bandit)

### Validation
```bash
# Security scan
bandit -r src/

# Check for known vulnerabilities
pip-audit  # If available
```

## 9. Clean Up

### Remove Temporary Files
```bash
# Remove __pycache__ directories
find . -type d -name "__pycache__" -exec rm -rf {} +

# Remove .pyc files
find . -name "*.pyc" -delete

# Remove test artifacts
rm -rf htmlcov/ .coverage .pytest_cache/
```

### Workspace Hygiene
- [ ] No debug print statements
- [ ] No commented-out code blocks
- [ ] No temporary test files
- [ ] No unused imports

## 10. Final Verification

### Pre-Merge Checklist
- [ ] All tests passing
- [ ] Code quality checks passed
- [ ] Documentation updated
- [ ] Changes reviewed (self-review)
- [ ] Feature branch committed
- [ ] Ready for pull request

### Validation Command
```bash
# Run comprehensive tests
python run_comprehensive_tests.py

# Or use Make
make comprehensive-validation
```

## 11. Task-Specific Validation

### For Agent Changes
```bash
pytest -m agent -v
make validate-task-12  # If related to Task 12
```

### For Dashboard Changes
```bash
cd dashboard
npm run build  # Ensure build succeeds
npm test       # Run Jest tests
```

### For Infrastructure Changes
```bash
# Validate CDK if applicable
cd infrastructure/cdk
cdk synth
```

## Summary Checklist

Quick reference for task completion:

- [ ] Code formatted (black, isort)
- [ ] Linting passed (ruff, eslint)
- [ ] Type checking passed (mypy, tsc)
- [ ] Tests written and passing
- [ ] Coverage ≥80%
- [ ] Manual testing completed
- [ ] Documentation updated
- [ ] Performance validated
- [ ] Security reviewed
- [ ] Clean workspace
- [ ] Committed to feature branch
- [ ] Ready for PR