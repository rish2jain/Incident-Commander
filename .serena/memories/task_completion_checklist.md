# Task Completion Checklist

When completing any development task, follow this checklist:

## 1. Code Quality ✅
- [ ] All code has complete type hints
- [ ] Docstrings added for new modules/classes/functions
- [ ] Code follows snake_case naming conventions
- [ ] No hardcoded values (use config or constants)

## 2. Testing 🧪
- [ ] Unit tests written for new functionality
- [ ] Tests follow `test_<module>_<behavior>` naming
- [ ] All tests passing: `python -m pytest tests/ -v`
- [ ] Coverage maintained ≥80%: `python -m pytest --cov=src --cov=agents`
- [ ] Integration tests updated if needed

## 3. Type Checking & Linting 🔍
- [ ] Type checking passes: `mypy src agents`
- [ ] Code formatted: `black src agents tests`
- [ ] Imports sorted: `isort src agents tests`
- [ ] Pre-commit hooks pass: `pre-commit run --all-files`

## 4. Documentation 📚
- [ ] README updated if public API changed
- [ ] AGENTS.md updated if structure changed
- [ ] Inline comments for complex logic
- [ ] API endpoint documentation updated

## 5. Security & Validation 🛡️
- [ ] Input validation with Pydantic models
- [ ] No secrets or credentials in code
- [ ] Error handling with custom exceptions
- [ ] Audit logging for sensitive operations

## 6. Performance & Resilience ⚡
- [ ] Circuit breakers for external calls
- [ ] Timeout protection implemented
- [ ] Bounds checking for collections
- [ ] Memory pressure management
- [ ] Performance targets met (see README)

## 7. Git & Version Control 📝
- [ ] Feature branch created (not on main)
- [ ] Conventional commit message used
- [ ] Changes reviewed with `git diff`
- [ ] No debugging code or temporary files
- [ ] .gitignore respected

## 8. Verification Scripts 🔬
- [ ] Setup verification passes: `python scripts/verify_setup.py`
- [ ] Server starts successfully
- [ ] Health check passes: `curl http://localhost:8000/health`

## Quick Quality Command
```bash
# Run all quality checks in one go
black src agents tests && \
isort src agents tests && \
mypy src agents && \
pytest tests/ --cov=src --cov=agents -v && \
pre-commit run --all-files
```

## Before Pull Request
- [ ] All checklist items above completed
- [ ] Branch rebased on latest main
- [ ] PR description includes testing evidence
- [ ] References relevant incident IDs or steering docs
- [ ] Appropriate reviewers tagged