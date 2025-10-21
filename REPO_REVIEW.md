# Repository Improvement Suggestions

## Backend Architecture
- Clarify CLI entrypoint: either add a `main()` wrapper in `src/main.py` for the `incident-commander` console script or drop the script to prevent broken installs.
- Break up oversized service modules by domain (alert ingestion, consensus, demo tooling) and enforce interface-based boundaries to reduce coupling.
- Replace blocking system calls (e.g., `psutil`) inside async agents with executor offloading or telemetry workers to keep event loops responsive.
- Add durable storage for `swarm_coordinator` state (Redis/Dynamo) so incidents survive process restarts and support replay analytics.

## Dependency & Build Hygiene
- Consolidate Python dependency declarations (pyproject/requirements/demo) into a single authoritative list and generate pins to avoid version drift.
- Remove committed vendor directories like `node_modules/`, `.venv/`, and `__pycache__/` and reinforce `.gitignore` via CI checks.
- Streamline Lambda packaging by scripting dependency pruning from `requirements-lambda.txt` to keep deploy artifacts reproducible.

## Testing & QA
- Raise coverage enforcement to the documented ≥80% or adjust docs, and add orchestrator/fixture unit tests to back critical flows.
- Default integration tests to LocalStack/moto stubs so CI does not depend on live AWS endpoints.
- Integrate `mypy`, `ruff`, and dashboard Jest/lint runs into CI to gate merges across Python and frontend code.

## Frontend & Contracts
- Retire legacy dashboard HTML artifacts and standardize on the Next.js build to avoid divergent UX.
- Document shared REST/WebSocket contracts (e.g., `/dashboard/ws`) and generate TypeScript types from FastAPI schemas to keep clients in sync.

## Documentation & Onboarding
- Relocate promotional status markdowns into `docs/` or a release archive to declutter the repo root.
- Refresh `README.md` with the current bootstrap flow (venv, `uvicorn`, demo presets) and link to `AGENTS.md` for contributor expectations.
- Expand `.env.example` with required LocalStack/AWS variables and guardrail registration hints for safer onboarding.
