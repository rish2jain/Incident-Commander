# SwarmAI - Task Completion Checklist

## Pre-Development Checklist

### Before Starting Any Task
- [ ] Understand the requirement completely (ask clarifying questions if needed)
- [ ] Check existing code for similar patterns or implementations
- [ ] Review relevant documentation (ARCHITECTURE.md, API.md, etc.)
- [ ] Verify current git branch and create feature branch if needed
- [ ] Pull latest changes from main branch
- [ ] Ensure development environment is properly set up
- [ ] Start required services (Docker, LocalStack, Redis)

## Code Development Checklist

### During Implementation
- [ ] Follow existing code patterns and conventions
- [ ] Use appropriate design patterns (see design_patterns_and_guidelines memory)
- [ ] Add type hints to all Python functions
- [ ] Follow Black formatting (line length 100)
- [ ] Use proper naming conventions (snake_case for Python, camelCase for TypeScript)
- [ ] Add docstrings to public functions/classes (Google style)
- [ ] Handle errors gracefully with custom exceptions
- [ ] Add appropriate logging with structured context
- [ ] Implement defensive programming (bounds checking, validation)
- [ ] Consider async/await for I/O operations
- [ ] Add timeout protection for external calls
- [ ] Implement circuit breaker for external service calls
- [ ] Validate all inputs using Pydantic models

### Code Quality
- [ ] Run Black formatter: `black src/ tests/`
- [ ] Run isort: `isort src/ tests/`
- [ ] Run Ruff linting: `ruff check src/ tests/`
- [ ] Run MyPy type checking: `mypy src/`
- [ ] Fix all linting errors and warnings
- [ ] Run security scan: `bandit -r src/`
- [ ] Address any security concerns

### Frontend Specific (TypeScript/React)
- [ ] Use proper TypeScript types (avoid `any`)
- [ ] Follow React best practices (hooks rules)
- [ ] Use 'use client' directive when needed (interactivity, hooks)
- [ ] Implement proper error boundaries
- [ ] Add loading and error states
- [ ] Ensure accessibility (ARIA labels, keyboard navigation)
- [ ] Optimize for performance (memo, useMemo, useCallback)
- [ ] Test responsive design (mobile, tablet, desktop)
- [ ] Run ESLint: `npm run lint`
- [ ] Run TypeScript check: `npx tsc --noEmit`

## Testing Checklist

### Unit Tests
- [ ] Write unit tests for all new functions/methods
- [ ] Test happy path (expected behavior)
- [ ] Test edge cases (empty inputs, null, undefined)
- [ ] Test error conditions (invalid inputs, exceptions)
- [ ] Test boundary conditions (min/max values)
- [ ] Mock external dependencies (AWS services, Redis, etc.)
- [ ] Aim for >60% code coverage (minimum requirement)
- [ ] Use appropriate test markers (@pytest.mark.unit, etc.)

### Integration Tests
- [ ] Write integration tests for component interactions
- [ ] Test agent coordination and consensus
- [ ] Test event store integration
- [ ] Test message bus communication
- [ ] Test WebSocket real-time updates
- [ ] Test circuit breaker behavior
- [ ] Test with LocalStack for AWS services
- [ ] Use appropriate test markers (@pytest.mark.integration)

### Test Execution
- [ ] Run all tests: `pytest`
- [ ] Run with coverage: `pytest --cov=src --cov-report=term-missing`
- [ ] Verify all tests pass
- [ ] Check coverage report (aim for >60%)
- [ ] Run frontend tests: `npm test` (in dashboard directory)
- [ ] Fix any failing tests before committing

### Manual Testing
- [ ] Test in development environment
- [ ] Test all API endpoints with /docs (Swagger UI)
- [ ] Test WebSocket connections and real-time updates
- [ ] Test demo scenarios work correctly
- [ ] Test error handling and recovery
- [ ] Test with different data scenarios
- [ ] Test performance under load (if relevant)

## Documentation Checklist

### Code Documentation
- [ ] Add/update docstrings for public APIs
- [ ] Add inline comments for complex logic
- [ ] Update type hints if function signatures changed
- [ ] Document any workarounds or TODOs with issue references

### Project Documentation
- [ ] Update README.md if user-facing changes
- [ ] Update API.md if API endpoints changed
- [ ] Update ARCHITECTURE.md if architectural changes
- [ ] Update DEPLOYMENT.md if deployment process changed
- [ ] Add/update examples if new features added
- [ ] Update configuration guide if new env vars added

### API Documentation (OpenAPI/Swagger)
- [ ] Verify OpenAPI schema is auto-generated correctly
- [ ] Check /docs endpoint displays new endpoints
- [ ] Add request/response examples
- [ ] Document error responses
- [ ] Add tags for endpoint categorization

## Git Commit Checklist

### Pre-Commit
- [ ] Review all changes: `git diff`
- [ ] Stage only relevant changes: `git add <files>`
- [ ] Verify no sensitive data (API keys, secrets, etc.)
- [ ] Run pre-commit hooks: `pre-commit run --all-files`
- [ ] Fix any pre-commit issues

### Commit Message
- [ ] Use conventional commit format: `type(scope): subject`
- [ ] Choose appropriate type (feat, fix, docs, etc.)
- [ ] Add scope (agents, api, dashboard, etc.)
- [ ] Write clear, concise subject line (imperative mood)
- [ ] Add detailed body if needed (why, not what)
- [ ] Reference issues: `Closes #123`, `Fixes #456`

### Example Commits
```
feat(agents): add resolution agent with zero-trust architecture
fix(event-store): handle concurrent write conflicts
docs(readme): update deployment instructions
refactor(consensus): simplify weighted voting logic
test(agents): add integration tests for agent coordination
```

## Pull Request Checklist

### Before Creating PR
- [ ] Ensure branch is up to date with main
- [ ] Resolve any merge conflicts
- [ ] Run full test suite locally
- [ ] Verify CI/CD pipeline passes (if applicable)
- [ ] Review your own changes first

### PR Description
- [ ] Write clear PR title (similar to commit message)
- [ ] Describe what changed and why
- [ ] List any breaking changes
- [ ] Add screenshots/videos for UI changes
- [ ] Link related issues
- [ ] Add testing instructions
- [ ] Note any deployment considerations

### PR Review Process
- [ ] Request review from appropriate team members
- [ ] Respond to review comments promptly
- [ ] Make requested changes
- [ ] Re-request review after changes
- [ ] Ensure all CI checks pass
- [ ] Get approval before merging

## Deployment Checklist

### Pre-Deployment
- [ ] All tests pass in staging environment
- [ ] Performance testing completed (if applicable)
- [ ] Security scanning completed
- [ ] Database migrations tested (if applicable)
- [ ] Configuration validated for target environment
- [ ] Backup critical data
- [ ] Notify stakeholders of deployment

### Deployment
- [ ] Use appropriate deployment script
- [ ] Monitor deployment progress
- [ ] Verify health checks pass
- [ ] Check application logs for errors
- [ ] Verify metrics are being collected
- [ ] Test critical user paths
- [ ] Monitor for alerts or anomalies

### Post-Deployment
- [ ] Verify all services are running
- [ ] Check CloudWatch dashboards
- [ ] Verify business metrics (MTTR, incident count, etc.)
- [ ] Test key functionality in production
- [ ] Monitor error rates and latency
- [ ] Update deployment documentation
- [ ] Communicate deployment success to team

### Rollback Plan
- [ ] Document rollback procedure
- [ ] Know how to quickly revert changes
- [ ] Test rollback in staging (if possible)
- [ ] Monitor for issues requiring rollback
- [ ] Execute rollback if critical issues found

## Release Checklist

### Pre-Release
- [ ] Update version number (src/version.py, package.json)
- [ ] Update CHANGELOG.md with release notes
- [ ] Review all changes since last release
- [ ] Ensure all PRs are merged
- [ ] Run full test suite
- [ ] Create release branch (if using GitFlow)

### Release Process
- [ ] Tag release in git: `git tag -a v0.2.0 -m "Release v0.2.0"`
- [ ] Push tag: `git push origin v0.2.0`
- [ ] Create GitHub release with notes
- [ ] Build and publish Docker images (if applicable)
- [ ] Deploy to production
- [ ] Update documentation website (if applicable)

### Post-Release
- [ ] Announce release to team/users
- [ ] Monitor production closely
- [ ] Address any issues promptly
- [ ] Update project board/roadmap
- [ ] Plan next release cycle

## Performance Checklist

### Code Performance
- [ ] Avoid N+1 queries (database, API calls)
- [ ] Use async/await for concurrent operations
- [ ] Implement caching where appropriate
- [ ] Use pagination for large data sets
- [ ] Optimize database queries (indexes, etc.)
- [ ] Minimize external API calls
- [ ] Use connection pooling
- [ ] Profile code if performance-critical

### Frontend Performance
- [ ] Optimize bundle size
- [ ] Use code splitting (dynamic imports)
- [ ] Implement lazy loading for images
- [ ] Use React.memo for expensive components
- [ ] Optimize re-renders (useMemo, useCallback)
- [ ] Use virtual scrolling for long lists
- [ ] Compress images and assets
- [ ] Enable caching headers

## Security Checklist

### Code Security
- [ ] Validate all user inputs
- [ ] Sanitize data before rendering
- [ ] Use parameterized queries (prevent SQL injection)
- [ ] Implement proper authentication
- [ ] Use least privilege IAM roles
- [ ] Never commit secrets or API keys
- [ ] Use environment variables for sensitive data
- [ ] Implement rate limiting
- [ ] Add CORS configuration
- [ ] Use HTTPS for all external communications

### AWS Security
- [ ] Use IAM roles, not access keys
- [ ] Enable encryption at rest
- [ ] Enable encryption in transit
- [ ] Configure security groups properly
- [ ] Use VPC for network isolation
- [ ] Enable CloudTrail logging
- [ ] Set up CloudWatch alarms
- [ ] Implement backup strategy

## Cleanup Checklist

### Post-Task Cleanup
- [ ] Remove debug statements and console.logs
- [ ] Remove commented-out code
- [ ] Clean up unused imports
- [ ] Remove temporary files
- [ ] Delete feature branch after merge (if not auto-deleted)
- [ ] Close related issues
- [ ] Update task tracking board
- [ ] Document any technical debt created

## Knowledge Sharing Checklist

### Team Communication
- [ ] Update team on progress/completion
- [ ] Share learnings or gotchas
- [ ] Document decisions in architectural decision records
- [ ] Update team wiki/knowledge base
- [ ] Present demo if significant feature
- [ ] Mentor junior developers on new patterns

## Continuous Improvement Checklist

### Retrospective Questions
- [ ] What went well?
- [ ] What could be improved?
- [ ] What did I learn?
- [ ] What patterns can be reused?
- [ ] What documentation needs updating?
- [ ] What tests need adding?
- [ ] What technical debt was created?
- [ ] What can be automated?
