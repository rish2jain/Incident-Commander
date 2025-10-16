# Repository Guidelines

Incident Commander orchestrates multi-agent incident response across FastAPI services, workflow graphs, and cloud infrastructure. Use these guidelines to stay consistent with the established structure and delivery cadence.

## Project Structure & Module Organization
- `src/`: FastAPI entrypoints, orchestrator workflows under `src/orchestrator/`, shared helpers in `src/utils/`, and incident models in `src/models/`.
- `agents/<capability>/`: Individual agent logic; mirror capability folders in `tests/` for coverage.
- `tests/`: Unit suites in `tests/unit/`, integration flows in `tests/integration/`, and chaos/load exercises in dedicated subfolders.
- Supporting assets: `infrastructure/` for CDK stacks, `docs/` for published guides, `Research/` for experiments, and `docker/` for container recipes.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate`: Provision the Python 3.11 virtual environment.
- `pip install -r requirements.txt`: Install backend and agent dependencies.
- `uvicorn src.main:app --reload --port 8000`: Run the local FastAPI gateway with hot reload.
- `docker-compose up -d`: Launch LocalStack, queues, and databases for orchestration acceptance tests.
- `pytest --cov=src`: Execute unit/integration suites and verify ≥80% statement coverage.

## Coding Style & Naming Conventions
- Target Python 3.11 with full type hints; ensure `mypy src agents` succeeds.
- Follow snake_case modules, PascalCase classes, and `test_<module>_<behavior>` names.
- Run `pre-commit run --all-files` to apply formatters, linters, and security hooks before pushing.

## Testing Guidelines
- Prefer unit coverage for agent behaviors and orchestrator state machines in `tests/unit/`.
- Use fixtures in `tests/conftest.py` for Slack, Bedrock, and LocalStack stubs.
- Gate disruptive scenarios in `tests/chaos/` and `tests/load/`; keep assertions deterministic.
- Capture regressions with focused tests whenever incidents are resolved.

## Commit & Pull Request Guidelines
- Use Conventional Commits (`feat:`, `fix:`, `docs:`, `infra:`) and keep each commit scoped to one logical change.
- Reference incident IDs or `.kiro/steering/` notes in PR descriptions alongside testing evidence and relevant screenshots.
- Request reviews from both agent owners and infrastructure maintainers when changes span domains.

## Security & Configuration Tips
- Store secrets in `.env` files aligned with `.env.example`; never commit credentials.
- Exercise destructive AWS actions through LocalStack (`awslocal ...`) and guard production via IAM roles in `infrastructure/config/`.
- Register guardrails and access policies when introducing new agents or capabilities.
