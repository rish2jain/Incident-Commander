# SwarmAI - Code Style and Conventions

## Python Code Style (Backend)

### Formatting (Black)
- **Line Length**: 100 characters maximum
- **Target Version**: Python 3.11
- **String Quotes**: Double quotes preferred
- **Trailing Commas**: In multi-line structures
- **Magic Comma**: Preserves developer line breaks
- **Configuration**: `[tool.black]` in pyproject.toml

### Import Ordering (isort)
- **Profile**: black (compatible with Black formatter)
- **Order**: Standard library → Third-party → First-party → Local
- **Style**: Multi-line with trailing commas
- **Configuration**: `[tool.isort]` in pyproject.toml

### Linting (Ruff)
**Selected Rules**:
- **E**: pycodestyle errors
- **W**: pycodestyle warnings
- **F**: pyflakes (unused imports, undefined names)
- **I**: isort (import sorting)
- **B**: flake8-bugbear (common bugs)
- **C4**: flake8-comprehensions (list/dict comprehensions)
- **UP**: pyupgrade (modern Python syntax)
- **ARG001**: unused-function-args
- **SIM**: flake8-simplify (code simplification)
- **TCH**: flake8-type-checking (type checking imports)
- **TID**: flake8-tidy-imports (import hygiene)
- **Q**: flake8-quotes (quote consistency)
- **FLY**: flynt (f-string conversion)
- **PERF**: perflint (performance anti-patterns)
- **RUF**: ruff-specific rules

**Ignored Rules**:
- **E501**: Line too long (handled by Black)
- **B008**: Function calls in argument defaults
- **C901**: Function too complex
- **W191**: Indentation contains tabs

### Type Hints (MyPy)
- **Python Version**: 3.11
- **Strict Mode**: Enabled
- **Required**:
  - check_untyped_defs: true
  - disallow_any_generics: true
  - disallow_incomplete_defs: true
  - disallow_untyped_defs: true (except tests)
  - no_implicit_optional: true
  - warn_redundant_casts: true
  - warn_unused_ignores: true
  - warn_return_any: true
  - strict_equality: true
- **All functions must have type annotations**

### Naming Conventions (Python)
- **Modules/Files**: snake_case (e.g., `event_store.py`, `circuit_breaker.py`)
- **Classes**: PascalCase (e.g., `DetectionAgent`, `EventStore`, `CircuitBreaker`)
- **Functions/Methods**: snake_case (e.g., `process_incident`, `get_health_status`)
- **Variables**: snake_case (e.g., `incident_id`, `agent_name`, `max_retries`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- **Private**: Leading underscore (e.g., `_internal_method`, `_private_var`)
- **Protected**: Single leading underscore (e.g., `_protected_method`)
- **Magic Methods**: Double underscores (e.g., `__init__`, `__str__`)
- **Type Variables**: PascalCase with T prefix (e.g., `TModel`, `TResponse`)

### Docstrings (Google Style)
```python
def process_incident(incident_id: str, severity: int) -> IncidentResult:
    """Process an incident with the given ID and severity.

    Args:
        incident_id: Unique identifier for the incident
        severity: Severity level from 1 (low) to 5 (critical)

    Returns:
        IncidentResult containing the processing outcome and metadata

    Raises:
        IncidentNotFoundError: If the incident ID doesn't exist
        InvalidSeverityError: If severity is out of range

    Example:
        >>> result = process_incident("inc-123", severity=4)
        >>> print(result.status)
        'resolved'
    """
    # Implementation
```

### Error Handling
```python
# Custom exception hierarchy (src/utils/exceptions.py)
class SwarmAIError(Exception):
    """Base exception for all SwarmAI errors."""
    pass

class AgentError(SwarmAIError):
    """Agent-related errors."""
    pass

class EventStoreError(SwarmAIError):
    """Event store errors."""
    pass

# Usage
try:
    result = await agent.process()
except AgentError as e:
    logger.error(f"Agent processing failed: {e}", exc_info=True)
    raise
```

### Async/Await Pattern
```python
# All I/O operations should be async
async def fetch_incident(incident_id: str) -> Incident:
    """Fetch incident from event store."""
    async with event_store.session() as session:
        return await session.get_incident(incident_id)

# Use asyncio.gather for concurrent operations
incidents = await asyncio.gather(
    fetch_incident("inc-1"),
    fetch_incident("inc-2"),
    fetch_incident("inc-3"),
)
```

### Logging
```python
import structlog

logger = structlog.get_logger(__name__)

# Structured logging with context
logger.info(
    "incident_detected",
    incident_id="inc-123",
    severity=4,
    agent="detection",
    correlation_id="corr-456"
)
```

## TypeScript/React Code Style (Frontend)

### Formatting (Prettier via ESLint)
- **Line Length**: 100 characters (matches Python)
- **Semicolons**: Required
- **Quotes**: Double quotes for strings
- **Trailing Commas**: ES5 style
- **Arrow Parens**: Always
- **Tab Width**: 2 spaces

### Linting (ESLint)
- **Config**: Next.js ESLint configuration with strict rules
- **React Rules**: react-hooks/rules-of-hooks, react-hooks/exhaustive-deps
- **TypeScript Rules**: Strict type checking
- **Accessibility**: jsx-a11y rules for accessible components

### TypeScript Configuration
- **Strict Mode**: Enabled
- **No Implicit Any**: true
- **Strict Null Checks**: true
- **Target**: ES2022
- **Module**: ESNext
- **JSX**: preserve (Next.js handles transformation)

### Naming Conventions (TypeScript/React)
- **Components**: PascalCase (e.g., `Dashboard.tsx`, `IncidentCard.tsx`)
- **Hooks**: camelCase with 'use' prefix (e.g., `useWebSocket`, `useIncident`)
- **Functions**: camelCase (e.g., `fetchIncidents`, `formatTimestamp`)
- **Variables**: camelCase (e.g., `incidentData`, `isLoading`, `errorMessage`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `API_BASE_URL`, `MAX_RETRIES`)
- **Types/Interfaces**: PascalCase (e.g., `Incident`, `AgentStatus`, `ApiResponse`)
- **Type Suffixes**: Add 'Props', 'State', 'Config' as appropriate
  - Component props: `DashboardProps`
  - State types: `IncidentState`
  - Configuration: `WebSocketConfig`
- **Private**: No leading underscore, use TypeScript private keyword

### Component Patterns
```typescript
// Server Component (default in Next.js 14)
export default function IncidentList() {
  // Fetch data directly in component
  const incidents = await fetchIncidents();
  
  return (
    <div>
      {incidents.map(incident => (
        <IncidentCard key={incident.id} incident={incident} />
      ))}
    </div>
  );
}

// Client Component (for interactivity)
'use client';

import { useState, useEffect } from 'react';

interface DashboardProps {
  initialData: Incident[];
}

export default function Dashboard({ initialData }: DashboardProps) {
  const [incidents, setIncidents] = useState(initialData);
  
  useEffect(() => {
    // WebSocket connection, event handlers, etc.
  }, []);
  
  return <div>{/* component JSX */}</div>;
}
```

### Type Definitions
```typescript
// Prefer interfaces for objects
interface Incident {
  id: string;
  title: string;
  severity: number;
  status: IncidentStatus;
  createdAt: Date;
}

// Use type for unions, intersections, primitives
type IncidentStatus = 'detected' | 'diagnosed' | 'resolved' | 'closed';
type IncidentId = string;
type ApiResponse<T> = {
  data: T;
  error?: string;
  metadata: ResponseMetadata;
};

// Generic types
interface Repository<T> {
  findById(id: string): Promise<T>;
  findAll(): Promise<T[]>;
  save(entity: T): Promise<void>;
}
```

### Custom Hooks
```typescript
// Custom hook pattern
export function useIncidents(autoRefresh = false) {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  
  useEffect(() => {
    // Fetch logic
  }, [autoRefresh]);
  
  return { incidents, isLoading, error };
}
```

## File Organization

### Python Files
```
# Standard file structure
"""Module docstring describing purpose."""

# 1. Standard library imports
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

# 2. Third-party imports
import boto3
from fastapi import FastAPI
from pydantic import BaseModel

# 3. Local imports (absolute)
from src.models.incident import Incident
from src.services.event_store import EventStore
from src.utils.logging import get_logger

# 4. Logger setup
logger = get_logger(__name__)

# 5. Constants
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30

# 6. Type definitions
IncidentId = str

# 7. Classes and functions
class MyClass:
    """Class docstring."""
    pass

def my_function() -> None:
    """Function docstring."""
    pass
```

### TypeScript/React Files
```typescript
// 1. React imports
import React, { useState, useEffect } from 'react';

// 2. Next.js imports
import { Metadata } from 'next';

// 3. Third-party imports
import { motion } from 'framer-motion';

// 4. Local component imports
import { Card } from '@/components/ui/card';
import { IncidentCard } from '@/components/dashboard/IncidentCard';

// 5. Hook imports
import { useIncidents } from '@/hooks/useIncidents';

// 6. Type imports
import type { Incident } from '@/types/incident';

// 7. Utility imports
import { formatDate } from '@/lib/utils';

// 8. Constants
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;

// 9. Type definitions (if not in separate file)
interface Props {
  // ...
}

// 10. Component definition
export default function Component(props: Props) {
  // Component implementation
}
```

## Git Commit Messages

### Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, no logic change)
- **refactor**: Code refactoring
- **perf**: Performance improvements
- **test**: Adding or updating tests
- **chore**: Maintenance tasks
- **ci**: CI/CD changes
- **build**: Build system changes

### Examples
```
feat(agents): add prediction agent with time-series forecasting

Implement the prediction agent to forecast incident trends using
historical data. Includes ARIMA model integration and confidence scoring.

Closes #123

---

fix(event-store): handle concurrent write conflicts

Add optimistic locking to prevent data corruption during concurrent
writes to the same incident.

Fixes #456

---

docs(readme): update deployment instructions

Add production deployment section with AWS CDK setup and
environment configuration examples.
```

## Testing Conventions

### Test File Naming
- **Python**: `test_<module>.py` (e.g., `test_event_store.py`)
- **TypeScript**: `<component>.test.tsx` or `<module>.test.ts`

### Test Function Naming
```python
# Python: test_<description>_<expected_outcome>
def test_incident_detection_creates_event():
    """Test that incident detection creates an event in the store."""
    pass

def test_agent_consensus_handles_timeout():
    """Test that consensus handles agent timeout gracefully."""
    pass
```

### Test Organization
```python
class TestDetectionAgent:
    """Tests for DetectionAgent."""
    
    def test_alert_correlation(self):
        """Test alert correlation logic."""
        pass
    
    def test_alert_storm_handling(self):
        """Test handling of alert storms."""
        pass
```

## Comments

### When to Comment
- **Complex algorithms**: Explain the "why" not the "what"
- **Business logic**: Clarify non-obvious business rules
- **Workarounds**: Explain temporary solutions and link to issues
- **TODO**: Mark incomplete work with issue references

### Comment Style
```python
# Good: Explains why
# Use exponential backoff to prevent overwhelming the service
# during recovery from an outage
retry_delay = min(base_delay * (2 ** attempt), max_delay)

# Bad: Explains what (obvious from code)
# Multiply base_delay by 2 to the power of attempt
retry_delay = base_delay * (2 ** attempt)

# TODO(#123): Implement caching for incident patterns
# Current implementation fetches from database on every request,
# causing performance issues for high-traffic scenarios.
```

## Configuration Management

### Environment Variables
- **Naming**: UPPER_SNAKE_CASE
- **Prefixes**: 
  - `AWS_` for AWS-specific config
  - `REDIS_` for Redis config
  - `NEXT_PUBLIC_` for client-accessible config (Next.js)
- **Validation**: Use Pydantic BaseSettings for validation
- **Documentation**: Document in .env.example with descriptions

### Configuration Files
- **Python**: pyproject.toml for project config
- **TypeScript**: tsconfig.json, next.config.js
- **Shared**: JSON or YAML for AWS CDK, Docker Compose
