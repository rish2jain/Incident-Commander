# Code Style and Conventions

## Python Style (Backend)

### Formatting
- **Formatter**: Black with line-length 100
- **Import Sorting**: isort (black profile)
- **Linting**: ruff + flake8 + mypy
- **Target Version**: Python 3.11+

### Naming Conventions
- **Variables/Functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: `_leading_underscore`
- **Modules**: `lowercase_with_underscores.py`

### Type Hints
- **Required**: All function signatures must have type hints
- **Style**: Use modern syntax (list[str] not List[str])
- **Validation**: mypy strict mode enabled
- **Models**: Pydantic v2 for data validation

### Documentation
- **Docstrings**: Google style preferred
- **Required For**: Public functions, classes, modules
- **Format**:
```python
def function(param: str) -> bool:
    """Brief description.
    
    Args:
        param: Description of parameter
        
    Returns:
        Description of return value
    """
```

### Async Patterns
- Use `async`/`await` for I/O-bound operations
- Prefix async functions with clear intent
- Use `asyncio.gather()` for concurrent operations
- Proper error handling with try/except in async contexts

### Error Handling
- Custom exception hierarchy (defined in project)
- Structured logging with correlation IDs
- Defensive programming with bounds checking
- Circuit breaker patterns for external services

## TypeScript/React Style (Frontend)

### Formatting
- **Line Length**: Consistent with Next.js defaults
- **Linting**: ESLint with Next.js config
- **Type Checking**: TypeScript strict mode

### Naming Conventions
- **Variables/Functions**: `camelCase`
- **Components**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Files**: `PascalCase.tsx` for components, `camelCase.ts` for utilities
- **CSS Classes**: Tailwind utility classes

### Component Patterns
- **Functional Components**: Use hooks, no class components
- **Props**: Define explicit TypeScript interfaces
- **State**: React hooks (useState, useEffect, etc.)
- **Style**: Tailwind CSS utility classes

### File Organization
- One component per file (except small related components)
- Co-locate component-specific utilities
- Shared utilities in `src/` directory

## General Principles

### SOLID Principles
- Single Responsibility: Each component has one reason to change
- Open/Closed: Open for extension, closed for modification
- Liskov Substitution: Derived classes substitutable for base
- Interface Segregation: Don't depend on unused interfaces
- Dependency Inversion: Depend on abstractions, not concretions

### Code Quality
- **DRY**: Don't repeat yourself - abstract common patterns
- **KISS**: Keep it simple - prefer simple solutions
- **YAGNI**: You aren't gonna need it - implement only requirements
- **Defensive Programming**: Validate inputs, handle errors
- **Performance**: O(n) complexity targets documented

### Security
- Zero Trust Architecture principles
- Input validation on all external data
- Least privilege access patterns
- Audit logging for sensitive operations
- No secrets in code (use environment variables)

## Configuration Standards
- Environment-specific config via .env files
- Validation on startup (fail fast)
- Sensible defaults for development
- Required config explicit for production