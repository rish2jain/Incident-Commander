# Deployment Guide - Autonomous Incident Commander

## Overview

This guide covers deploying the Autonomous Incident Commander system to production environments using AWS infrastructure, including setup, configuration, monitoring, and operational procedures.

## Prerequisites

### Required Tools

- AWS CLI v2.0+
- AWS CDK v2.0+
- Docker 20.10+
- Python 3.11+
- Node.js 18+ (for CDK)

### AWS Account Setup

- AWS Account with appropriate permissions
- AWS CLI configured with credentials
- CDK bootstrapped in target regions

```bash
# Install AWS CDK
npm install -g aws-cdk

# Bootstrap CDK (run once per region)
cdk bootstrap aws://ACCOUNT-ID/us-east-1
cdk bootstrap aws://ACCOUNT-ID/us-west-2
```

### Required AWS Services

- Amazon Bedrock (Claude-3 models)
- Amazon DynamoDB
- Amazon Kinesis Data Streams
- Amazon OpenSearch Serverless
- Amazon S3
- AWS Lambda
- Amazon ECS/Fargate
- Amazon API Gateway
- AWS Step Functions
- Amazon CloudWatch

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Gateway   │────│   ECS Cluster   │────│   Agent Swarm   │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   DynamoDB      │    │   Kinesis       │    │   OpenSearch    │
│   Event Store   │    │   Streaming     │    │   RAG Memory    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Step Functions│    │   CloudWatch    │    │   Bedrock       │
│   Consensus     │    │   Monitoring    │    │   AI Models     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Deployment Methods

### Method 1: AWS CDK (Recommended)

#### 1. Clone and Setup

```bash
git clone https://github.com/your-org/incident-commander.git
cd incident-commander

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r infrastructure/requirements.txt
```

#### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
vim .env
```

**Environment Variables:**

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012

# Application Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO
API_RATE_LIMIT=1000
AWS_ROLE_SESSION_DURATION=3600

# Bedrock Configuration
BEDROCK_REGION=us-east-1
BEDROCK_MODELS=claude-3-sonnet,claude-3-haiku

# Database Configuration
DYNAMODB_TABLE_PREFIX=incident-commander-prod
KINESIS_STREAM_NAME=incident-events-prod

# Security Configuration
ENCRYPTION_KEY_ID=alias/incident-commander-key
AUDIT_LOG_RETENTION_DAYS=2555

# Demo Controls
DEMO_EFFECTS_ENABLED=0

# Performance Configuration
CACHE_TTL_SECONDS=300
CONNECTION_POOL_SIZE=50
MEMORY_THRESHOLD=0.8

# Cost Configuration
COST_BUDGET_HOURLY=200.0
EMERGENCY_COST_LIMIT=1000.0
```

#### 3. Deploy Infrastructure

```bash
cd infrastructure

# Install CDK dependencies
npm install

# Deploy all stacks
cdk deploy --all --require-approval never

# Or deploy specific stacks
cdk deploy IncidentCommanderCoreStack
cdk deploy IncidentCommanderAgentsStack
cdk deploy IncidentCommanderMonitoringStack
```

#### 4. Deploy Application

```bash
# Build and push Docker images
./scripts/build-and-push.sh

# Deploy ECS services
cdk deploy IncidentCommanderApplicationStack
```

### Method 2: Docker Compose (Development)

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f incident-commander
```

### Method 3: Kubernetes (Alternative)

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

## Configuration Management

### Environment-Specific Configuration

#### Development

```yaml
# config/development.yaml
environment: development
log_level: DEBUG
api_rate_limit: 100
bedrock_models:
  - claude-3-haiku # Cheaper for development
database:
  dynamodb_billing_mode: PAY_PER_REQUEST
monitoring:
  detailed_metrics: false
```

#### Staging

```yaml
# config/staging.yaml
environment: staging
log_level: INFO
api_rate_limit: 500
bedrock_models:
  - claude-3-sonnet
  - claude-3-haiku
database:
  dynamodb_billing_mode: PROVISIONED
  read_capacity: 10
  write_capacity: 5
monitoring:
  detailed_metrics: true
```

#### Production

```yaml
# config/production.yaml
environment: production
log_level: WARNING
api_rate_limit: 1000
bedrock_models:
  - claude-3-opus
  - claude-3-sonnet
  - claude-3-haiku
database:
  dynamodb_billing_mode: PROVISIONED
  read_capacity: 100
  write_capacity: 50
  auto_scaling: true
monitoring:
  detailed_metrics: true
  alerting: true
security:
  encryption_at_rest: true
  encryption_in_transit: true
  audit_logging: true
```

### Secrets Management

Use AWS Systems Manager Parameter Store or AWS Secrets Manager:

```bash
# Store secrets
aws ssm put-parameter \
  --name "/incident-commander/prod/api-key" \
  --value "your-secret-api-key" \
  --type "SecureString"

aws secretsmanager create-secret \
  --name "incident-commander/prod/database" \
  --secret-string '{"username":"admin","password":"secure-password"}'
```

## Multi-Region Deployment

### Primary Region (us-east-1)

```bash
# Deploy primary region
export AWS_REGION=us-east-1
cdk deploy --all --context region=primary
```

### Secondary Region (us-west-2)

```bash
# Deploy secondary region
export AWS_REGION=us-west-2
cdk deploy --all --context region=secondary
```

### Cross-Region Replication Setup

```bash
# Enable DynamoDB Global Tables
aws dynamodb create-global-table \
  --global-table-name incident-events \
  --replication-group RegionName=us-east-1 RegionName=us-west-2

# Configure S3 Cross-Region Replication
aws s3api put-bucket-replication \
  --bucket incident-commander-primary \
  --replication-configuration file://replication-config.json
```

## Monitoring and Alerting

### CloudWatch Dashboards

```bash
# Deploy monitoring stack
cdk deploy IncidentCommanderMonitoringStack
```

**Key Metrics:**

- Incident processing time (target: <3 minutes)
- Agent success rate (target: >95%)
- API response time (target: <500ms)
- Cost per hour (budget: $200/hour)
- System availability (target: 99.9%)

### Alerting Rules

```yaml
# CloudWatch Alarms
alarms:
  - name: HighIncidentProcessingTime
    metric: IncidentProcessingDuration
    threshold: 180 # 3 minutes
    comparison: GreaterThanThreshold

  - name: LowAgentSuccessRate
    metric: AgentSuccessRate
    threshold: 0.95
    comparison: LessThanThreshold

  - name: HighHourlyCost
    metric: HourlyCost
    threshold: 200
    comparison: GreaterThanThreshold

  - name: SystemAvailability
    metric: SystemAvailability
    threshold: 0.999
    comparison: LessThanThreshold
```

### Log Aggregation

```bash
# Configure log groups
aws logs create-log-group --log-group-name /incident-commander/application
aws logs create-log-group --log-group-name /incident-commander/agents
aws logs create-log-group --log-group-name /incident-commander/consensus

# Set retention policy
aws logs put-retention-policy \
  --log-group-name /incident-commander/application \
  --retention-in-days 30
```

## Security Configuration

### IAM Roles and Policies

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:Query",
        "kinesis:PutRecord",
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:bedrock:*:*:model/*",
        "arn:aws:dynamodb:*:*:table/incident-commander-*",
        "arn:aws:kinesis:*:*:stream/incident-events-*",
        "arn:aws:s3:::incident-commander-*/*"
      ]
    }
  ]
}
```

### Network Security

```bash
# Create VPC and security groups
aws ec2 create-vpc --cidr-block 10.0.0.0/16
aws ec2 create-security-group \
  --group-name incident-commander-sg \
  --description "Security group for Incident Commander"

# Configure security group rules
aws ec2 authorize-security-group-ingress \
  --group-id sg-12345678 \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0
```

### Encryption

```bash
# Create KMS key
aws kms create-key \
  --description "Incident Commander encryption key" \
  --key-usage ENCRYPT_DECRYPT

# Create alias
aws kms create-alias \
  --alias-name alias/incident-commander-key \
  --target-key-id key-id
```

## Performance Tuning

### Database Optimization

```bash
# Configure DynamoDB auto-scaling
aws application-autoscaling register-scalable-target \
  --service-namespace dynamodb \
  --resource-id table/incident-events \
  --scalable-dimension dynamodb:table:ReadCapacityUnits \
  --min-capacity 5 \
  --max-capacity 1000

# Set up scaling policies
aws application-autoscaling put-scaling-policy \
  --policy-name incident-events-read-scaling-policy \
  --service-namespace dynamodb \
  --resource-id table/incident-events \
  --scalable-dimension dynamodb:table:ReadCapacityUnits \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration file://scaling-policy.json
```

### ECS Optimization

```json
{
  "family": "incident-commander",
  "cpu": "2048",
  "memory": "4096",
  "networkMode": "awsvpc",
  "taskRoleArn": "arn:aws:iam::account:role/IncidentCommanderTaskRole",
  "containerDefinitions": [
    {
      "name": "incident-commander",
      "image": "your-account.dkr.ecr.region.amazonaws.com/incident-commander:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "production"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/incident-commander/application",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

## Backup and Disaster Recovery

### Automated Backups

```bash
# Enable DynamoDB point-in-time recovery
aws dynamodb put-backup-policy \
  --table-name incident-events \
  --backup-policy BackupEnabled=true

# Configure S3 versioning and lifecycle
aws s3api put-bucket-versioning \
  --bucket incident-commander-data \
  --versioning-configuration Status=Enabled

aws s3api put-bucket-lifecycle-configuration \
  --bucket incident-commander-data \
  --lifecycle-configuration file://lifecycle-config.json
```

### Disaster Recovery Testing

```bash
# Test disaster recovery procedures
./scripts/test-disaster-recovery.sh

# Validate backup integrity
./scripts/validate-backups.sh

# Test cross-region failover
./scripts/test-failover.sh
```

## Operational Procedures

### Health Checks

```bash
# Application health check
curl -f http://localhost:8000/health || exit 1

# Detailed system status
curl http://localhost:8000/status

# Agent health check
curl http://localhost:8000/agents/status
```

**Interpretation Tips**

- `uptime_seconds` reflects actual API runtime since the last successful startup.
- `services.message_bus` reports Redis/SQS failover health—investigate circuit breakers if it reports `degraded`.
- `unhealthy_agents` lists agents failing health checks, including circuit breaker state and recommendations.
- `/status` now exposes `background_tasks` and real-time rate limiter dashboards for Bedrock and external integrations.

### Scaling Operations

```bash
# Scale ECS service
aws ecs update-service \
  --cluster incident-commander \
  --service incident-commander-api \
  --desired-count 5

# Scale DynamoDB capacity
aws dynamodb update-table \
  --table-name incident-events \
  --provisioned-throughput ReadCapacityUnits=200,WriteCapacityUnits=100
```

### Maintenance Windows

```bash
# Schedule maintenance
./scripts/schedule-maintenance.sh \
  --start "2024-01-01T02:00:00Z" \
  --duration "2h" \
  --description "System updates"

# Apply updates during maintenance
./scripts/apply-updates.sh

# Validate system after maintenance
./scripts/post-maintenance-validation.sh
```

## Troubleshooting

### Message Bus Backoff

- Redis delivery failures automatically fall back to SQS with capped exponential backoff and ±10% jitter. Look for `Retrying message ...` entries in the `message_bus` logger.
- Messages exceeding retry thresholds land in the agent-specific DLQ (`incident_commander_<agent>_dlq`). Inspect and requeue once downstream services recover.

### Graceful Shutdown

- Shutdown now logs full tracebacks for cleanup failures (`exc_info=True`). Review the `incident_commander.main` logger if shutdown appears slow.
- `/status` should report `background_tasks: 0` post-deployment. Non-zero values indicate lingering coroutines that may need manual cancellation.

### Common Issues

#### High Latency

```bash
# Check API Gateway metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name Latency \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T01:00:00Z \
  --period 300 \
  --statistics Average

# Check ECS service metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=incident-commander-api \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T01:00:00Z \
  --period 300 \
  --statistics Average
```

#### Agent Failures

```bash
# Check agent logs
aws logs filter-log-events \
  --log-group-name /incident-commander/agents \
  --start-time 1640995200000 \
  --filter-pattern "ERROR"

# Restart failed agents
aws ecs update-service \
  --cluster incident-commander \
  --service detection-agent \
  --force-new-deployment
```

#### Cost Overruns

```bash
# Check current costs
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-02 \
  --granularity DAILY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE

# Trigger cost optimization
curl -X POST http://localhost:8000/cost/optimize
```

### Log Analysis

```bash
# Search application logs
aws logs filter-log-events \
  --log-group-name /incident-commander/application \
  --filter-pattern "{ $.level = \"ERROR\" }" \
  --start-time 1640995200000

# Analyze performance metrics
aws logs insights start-query \
  --log-group-name /incident-commander/application \
  --start-time 1640995200 \
  --end-time 1640998800 \
  --query-string 'fields @timestamp, duration | filter duration > 3000 | sort @timestamp desc'
```

## Rollback Procedures

### Application Rollback

```bash
# Rollback to previous version
aws ecs update-service \
  --cluster incident-commander \
  --service incident-commander-api \
  --task-definition incident-commander:previous

# Verify rollback
./scripts/verify-deployment.sh
```

### Database Rollback

```bash
# Restore from point-in-time backup
aws dynamodb restore-table-from-backup \
  --target-table-name incident-events-restored \
  --backup-arn arn:aws:dynamodb:region:account:table/incident-events/backup/backup-id
```

## Support and Maintenance

### Regular Maintenance Tasks

- Weekly: Review performance metrics and cost reports
- Monthly: Update dependencies and security patches
- Quarterly: Disaster recovery testing
- Annually: Security audit and compliance review

### Support Contacts

- **Operations Team**: ops@your-company.com
- **Security Team**: security@your-company.com
- **On-Call**: +1-555-0123 (24/7)

### Documentation Updates

Keep this deployment guide updated with:

- Configuration changes
- New deployment procedures
- Lessons learned from incidents
- Performance optimization discoveries
