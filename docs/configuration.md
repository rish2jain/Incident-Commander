# Configuration Reference

This document provides a comprehensive reference for configuring the Autonomous Incident Commander system across different environments.

## Environment Variables

### Core Environment Settings

| Variable      | Required | Default       | Description                                              |
| ------------- | -------- | ------------- | -------------------------------------------------------- |
| `ENVIRONMENT` | No       | `development` | Environment name: `development`, `staging`, `production` |

### AWS Configuration

| Variable                  | Required | Default     | Description                                     |
| ------------------------- | -------- | ----------- | ----------------------------------------------- |
| `AWS_REGION`              | No       | `us-east-1` | AWS region for all services                     |
| `AWS_PROFILE`             | No       | None        | AWS CLI profile to use                          |
| `AWS_ENDPOINT_URL`        | No       | None        | LocalStack endpoint (development only)          |
| `AWS_ROLE_SESSION_DURATION` | No     | `3600`      | STS session duration in seconds (max `43200`)   |

**Production Requirements:**

- `AWS_ENDPOINT_URL` must NOT be set (prevents LocalStack usage)
- Proper IAM roles and policies must be configured
- All AWS services must be in the same region
- `AWS_ROLE_SESSION_DURATION` must be <= 43200 seconds and align with IAM max session duration

### Bedrock Configuration

| Variable                 | Required | Default                                   | Description                 |
| ------------------------ | -------- | ----------------------------------------- | --------------------------- |
| `BEDROCK_PRIMARY_MODEL`  | No       | `anthropic.claude-3-sonnet-20240229-v1:0` | Primary LLM model           |
| `BEDROCK_FALLBACK_MODEL` | No       | `anthropic.claude-3-haiku-20240307-v1:0`  | Fallback LLM model          |
| `BEDROCK_MAX_TOKENS`     | No       | `4096`                                    | Maximum tokens per request  |
| `BEDROCK_TEMPERATURE`    | No       | `0.1`                                     | Model temperature (0.0-1.0) |

**Production Limits:**

- `BEDROCK_MAX_TOKENS` should not exceed 8192
- Rate limits: 1000 requests/minute, 100K tokens/minute
- Concurrent requests limited to 50

### Database Configuration

| Variable                | Required | Default              | Description                  |
| ----------------------- | -------- | -------------------- | ---------------------------- |
| `DYNAMODB_TABLE_PREFIX` | No       | `incident-commander` | Prefix for DynamoDB tables   |
| `KINESIS_STREAM_NAME`   | No       | `incident-events`    | Kinesis stream for events    |
| `OPENSEARCH_ENDPOINT`   | No       | None                 | OpenSearch endpoint for logs |

### Redis Configuration

| Variable         | Required     | Default     | Description                   |
| ---------------- | ------------ | ----------- | ----------------------------- |
| `REDIS_HOST`     | No           | `localhost` | Redis server hostname         |
| `REDIS_PORT`     | No           | `6379`      | Redis server port             |
| `REDIS_PASSWORD` | Prod/Staging | None        | Redis authentication password |
| `REDIS_DB`       | No           | `0`         | Redis database number         |
| `REDIS_SSL`      | Prod         | `false`     | Enable SSL/TLS for Redis      |

**Production Requirements:**

- `REDIS_HOST` must NOT be `localhost`
- `REDIS_PASSWORD` is required
- `REDIS_SSL` must be `true`
- Use managed Redis service (ElastiCache, Redis Cloud, etc.)

### External Service Integrations

| Variable            | Required     | Default | Description                          |
| ------------------- | ------------ | ------- | ------------------------------------ |
| `DATADOG_API_KEY`   | Prod/Staging | None    | Datadog API key for metrics          |
| `PAGERDUTY_API_KEY` | Prod         | None    | PagerDuty API key for incidents      |
| `SLACK_BOT_TOKEN`   | Prod         | None    | Slack bot token for notifications    |
| `SLACK_CHANNEL`     | Prod         | None    | Slack channel for incident updates   |
| `GITHUB_TOKEN`      | No           | None    | GitHub token for deployment tracking |

**Production Requirements:**

- All service API keys must be valid and have appropriate permissions
- Slack bot must be installed in the workspace
- PagerDuty integration must be configured with proper escalation policies

### Security Configuration

| Variable         | Required     | Default | Description                            |
| ---------------- | ------------ | ------- | -------------------------------------- |
| `JWT_SECRET_KEY` | Prod/Staging | None    | Secret key for JWT token signing       |
| `ENCRYPTION_KEY` | Prod         | None    | Key for encrypting sensitive data      |
| `API_RATE_LIMIT` | No           | `100`   | API requests per minute per client     |
| `CORS_ORIGINS`   | Prod         | None    | Allowed CORS origins (comma-separated) |

**Production Requirements:**

- `JWT_SECRET_KEY` must be cryptographically secure (32+ characters)
- `ENCRYPTION_KEY` must be 32 bytes, base64 encoded
- `CORS_ORIGINS` must be explicitly set (no wildcards)

### Demo & Visualization Controls

| Variable               | Required | Default | Description                                           |
| ---------------------- | -------- | ------- | ----------------------------------------------------- |
| `DEMO_EFFECTS_ENABLED` | No       | `0`     | Set to `1` to enable timed demo delays and animations |

**Recommendation:** Keep disabled (`0`) in production and staging to avoid artificial latency.

## Environment-Specific Configuration

### Development Environment

**Prerequisites:**

- Docker and Docker Compose installed
- Python 3.11+ with pip
- AWS CLI configured (optional, for real AWS testing)

**Required Services:**

```bash
# Start local development services
docker-compose up -d

# Services started:
# - LocalStack (AWS services simulation)
# - Redis (message bus)
# - PostgreSQL (optional, for local testing)
```

**Environment File (`.env`):**

```bash
ENVIRONMENT=development
AWS_ENDPOINT_URL=http://localhost:4566
REDIS_HOST=localhost
REDIS_PORT=6379
# External service keys are optional in development
```

### Staging Environment

**Prerequisites:**

- AWS account with appropriate permissions
- Managed Redis instance
- External service accounts (Datadog, etc.)

**Required Configuration:**

```bash
ENVIRONMENT=staging
AWS_REGION=us-east-1
REDIS_HOST=staging-redis.example.com
REDIS_PASSWORD=secure-password
REDIS_SSL=true
DATADOG_API_KEY=your-datadog-key
JWT_SECRET_KEY=your-jwt-secret
```

### Production Environment

**Prerequisites:**

- Production AWS account with strict IAM policies
- Managed Redis with encryption and authentication
- All external service integrations configured
- SSL certificates and security hardening

**Required Configuration:**

```bash
ENVIRONMENT=production
AWS_REGION=us-east-1

# Redis (managed service)
REDIS_HOST=prod-redis.cache.amazonaws.com
REDIS_PASSWORD=production-secure-password
REDIS_SSL=true

# External Services
DATADOG_API_KEY=prod-datadog-key
PAGERDUTY_API_KEY=prod-pagerduty-key
SLACK_BOT_TOKEN=xoxb-your-slack-token
SLACK_CHANNEL=#incident-alerts

# Security
JWT_SECRET_KEY=production-jwt-secret-32-chars-min
ENCRYPTION_KEY=base64-encoded-32-byte-key
CORS_ORIGINS=https://incident-commander.example.com
API_RATE_LIMIT=50
```

## Service Limits and Quotas

### AWS Bedrock Limits

| Environment | Concurrent Requests | Requests/Minute | Tokens/Minute | Timeout |
| ----------- | ------------------- | --------------- | ------------- | ------- |
| Development | 5                   | 100             | 10,000        | 60s     |
| Staging     | 20                  | 500             | 50,000        | 30s     |
| Production  | 50                  | 1,000           | 100,000       | 30s     |

### Redis Configuration Limits

| Environment | Max Connections | Memory Limit | Persistence |
| ----------- | --------------- | ------------ | ----------- |
| Development | 100             | 256MB        | None        |
| Staging     | 500             | 2GB          | AOF         |
| Production  | 2000            | 8GB          | AOF + RDB   |

### Rate Limiting

| Service       | Development | Staging | Production |
| ------------- | ----------- | ------- | ---------- |
| API Endpoints | 100/min     | 200/min | 50/min     |
| Slack API     | 10/min      | 20/min  | 1/sec      |
| PagerDuty API | 20/min      | 50/min  | 2/min      |
| Datadog API   | 100/min     | 500/min | 1000/min   |

## Configuration Validation

The system automatically validates configuration on startup:

### Development Warnings

- Using real AWS services without LocalStack
- Remote Redis without authentication
- Missing optional external service keys

### Staging Requirements

- Datadog API key must be present
- JWT secret key must be configured
- Redis should use authentication

### Production Requirements

- All external service API keys required
- Security configuration mandatory
- Redis must use SSL and authentication
- CORS origins must be explicitly set
- No LocalStack or localhost configurations

## Troubleshooting Configuration Issues

### Common Configuration Errors

**Error: "DATADOG_API_KEY is required in production"**

- Solution: Set the `DATADOG_API_KEY` environment variable
- Verify the API key is valid and has metric submission permissions

**Error: "REDIS_HOST should not be localhost in production"**

- Solution: Configure a managed Redis service
- Update `REDIS_HOST` to point to the managed instance
- Ensure `REDIS_PASSWORD` and `REDIS_SSL=true` are set

**Error: "JWT_SECRET_KEY is required in production"**

- Solution: Generate a secure JWT secret key
- Use at least 32 characters of random data
- Store securely in environment variables or secrets manager

### Configuration Testing

Test configuration validity:

```bash
# Validate current configuration
python -c "from src.utils.config import config; config.validate_required_config()"

# Check environment info
python -c "from src.utils.config import config; print(config.get_environment_info())"

# Test Redis connection
python -c "from src.services.message_bus import get_message_bus; import asyncio; asyncio.run(get_message_bus().health_check())"
```

### Environment Variable Precedence

1. Environment variables (highest priority)
2. `.env` file in project root
3. Default values in configuration classes

### Security Best Practices

**Development:**

- Use `.env` file for local configuration
- Never commit `.env` files to version control
- Use LocalStack for AWS services when possible

**Staging/Production:**

- Use environment variables or secrets management
- Rotate API keys and secrets regularly
- Enable audit logging for configuration changes
- Use least-privilege IAM policies

## Migration Guide

### From Development to Staging

1. Set `ENVIRONMENT=staging`
2. Configure managed Redis instance
3. Add required API keys (Datadog, JWT)
4. Remove LocalStack configuration
5. Test all integrations

### From Staging to Production

1. Set `ENVIRONMENT=production`
2. Add all required external service keys
3. Configure production security settings
4. Enable SSL for all external connections
5. Set up monitoring and alerting
6. Perform security audit

## Configuration Templates

### Docker Compose (.env)

```bash
ENVIRONMENT=development
AWS_ENDPOINT_URL=http://localhost:4566
REDIS_HOST=localhost
DATADOG_API_KEY=optional-for-testing
```

### Kubernetes ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: incident-commander-config
data:
  ENVIRONMENT: "production"
  AWS_REGION: "us-east-1"
  REDIS_HOST: "prod-redis.cache.amazonaws.com"
  REDIS_SSL: "true"
  API_RATE_LIMIT: "50"
```

### AWS Systems Manager Parameters

```bash
# Store sensitive configuration in Parameter Store
aws ssm put-parameter --name "/incident-commander/prod/datadog-api-key" --value "your-key" --type "SecureString"
aws ssm put-parameter --name "/incident-commander/prod/jwt-secret" --value "your-secret" --type "SecureString"
```
