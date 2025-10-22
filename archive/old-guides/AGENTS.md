# Repository Guidelines

## Project Structure & Module Organization
- `src/`: FastAPI entrypoints, orchestrator workflows, and shared utilities.
- `agents/<capability>/`: Individual agent logic mirrored by capability-specific tests.
- `tests/`: Unit suites in `tests/unit/`, integration flows in `tests/integration/`, chaos/load exercises under dedicated subfolders.
- Supporting assets: `infrastructure/` for CDK stacks, `docs/` for guides, `Research/` for experiments, and `docker/` for container images.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate`: Create and activate the Python 3.11 virtual environment.
- `pip install -r requirements.txt`: Install backend and agent dependencies.
- `uvicorn src.main:app --reload --port 8000`: Run the FastAPI gateway locally with hot reload.
- `docker-compose up -d`: Launch LocalStack, queues, and backing services for orchestration acceptance tests.
- `pytest --cov=src`: Execute unit/integration suites and enforce ≥80% statement coverage.

## Coding Style & Naming Conventions
- Target Python 3.11 with full type hints; keep `mypy src agents` clean.
- Follow snake_case modules, PascalCase classes, and `test_<module>_<behavior>` patterns.
- Run `pre-commit run --all-files` before committing to apply formatters, linters, and security hooks.

## Testing Guidelines
- Use `pytest` fixtures from `tests/conftest.py` to stub Slack, Bedrock, and LocalStack services.
- Prefer focused unit tests for orchestrator state machines and agent behaviors; escalate scenarios to integration when dependencies matter.
- Maintain deterministic assertions in chaos/load suites and monitor coverage thresholds via `pytest --cov=src`.

## Commit & Pull Request Guidelines
- Adopt Conventional Commits (e.g., `feat:`, `fix:`, `docs:`) scoped to one logical change.
- Reference incident IDs or `.kiro/steering/` notes in PR descriptions and attach testing evidence or relevant screenshots.
- Request reviews from agent owners and infrastructure maintainers when changes span domains.

## Security & Configuration Tips
- Store secrets in `.env` aligned with `.env.example`; never commit credentials.
- Exercise destructive AWS actions through LocalStack (`awslocal ...`) before promoting changes.
- Register guardrails and IAM policies when adding agents or capabilities, and keep infrastructure settings in `infrastructure/config/`.
