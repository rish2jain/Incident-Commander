# Code Style & Conventions

## Naming Conventions
- **Modules/Files**: `snake_case` (e.g., `event_store.py`, `circuit_breaker.py`)
- **Classes**: `PascalCase` (e.g., `RobustDetectionAgent`, `IncidentMetadata`)
- **Functions/Methods**: `snake_case` (e.g., `get_incident`, `validate_config`)
- **Variables**: `snake_case` (e.g., `incident_id`, `correlation_depth`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_CORRELATION_DEPTH`, `DEFAULT_TIMEOUT`)
- **Test Functions**: `test_<module>_<behavior>` (e.g., `test_detection_agent_alert_correlation`)

## Type Hints
- **Required**: Full type hints on all functions and methods
- **Validation**: Must pass `mypy src agents` without errors
- **Examples**:
  ```python
  def process_incident(incident_id: str, severity: IncidentSeverity) -> Incident:
      ...
  
  async def correlate_alerts(alerts: list[Alert]) -> dict[str, Any]:
      ...
  ```

## Docstrings
- **Module-level**: Triple-quoted string at top explaining purpose
  ```python
  """
  FastAPI application entry point for the Incident Commander system.
  """
  ```
- **Classes/Functions**: Describe purpose, parameters, returns, raises
- **Format**: Google-style or NumPy-style docstrings

## Import Organization
- **Standard library** imports first
- **Third-party** imports second
- **Local application** imports third
- Use `isort` for automatic sorting

## Code Quality Standards
- **Formatter**: `black` with default settings (88 char line length)
- **Linter**: `pre-commit run --all-files` before commits
- **Type Checker**: `mypy src agents` must pass
- **Coverage**: ≥80% statement coverage required

## Design Patterns
- **Defensive Programming**: Bounds checking, input validation, timeout protection
- **Circuit Breaker Pattern**: For all external service calls
- **Event Sourcing**: All state changes through event store
- **Async/Await**: Use async for I/O operations
- **Pydantic Models**: For all data validation and serialization

## Error Handling
- **Custom Exceptions**: Inherit from `IncidentCommanderError`
- **Logging**: Use structured logging with correlation IDs
- **Graceful Degradation**: Circuit breakers and fallback mechanisms

## Security Practices
- **Input Validation**: All inputs validated with Pydantic
- **Secrets Management**: Environment variables, never committed
- **Audit Logging**: Cryptographic integrity verification
- **Least Privilege**: IAM roles with minimal permissions