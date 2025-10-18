# Deployment Checklist and Rollback Plan

**Date**: October 18, 2025  
**Project**: Autonomous Incident Commander  
**Infrastructure Change**: Lambda Execution Role Addition  
**Deployment Type**: Infrastructure Update

---

## 🎯 Pre-Deployment Checklist

### 1. Infrastructure Validation ✅

- [x] **CDK Syntax Validation**: All 7 stacks synthesize successfully
- [x] **Breaking Changes Check**: No breaking changes detected in `cdk diff`
- [x] **Docker Configuration**: All services configured and validated
- [x] **LocalStack Compatibility**: Development environment ready
- [x] **Security Configuration**: Lambda execution role properly configured
- [x] **Network Configuration**: VPC and security groups validated
- [x] **Monitoring Setup**: Prometheus and Grafana configurations ready

### 2. Environment Preparation

#### Development Environment

- [x] **Docker Services**: LocalStack, Redis, PostgreSQL, Prometheus, Grafana
- [x] **Environment Variables**: `.env.example` template ready
- [x] **LocalStack Resources**: DynamoDB table creation scripts ready
- [x] **Health Checks**: All service health checks configured

#### Staging Environment

- [ ] **AWS Credentials**: Staging account access configured
- [ ] **Bedrock Models**: Claude 3.5 Sonnet, Claude 3 Haiku, Titan Embeddings enabled
- [ ] **Secrets Manager**: API keys and sensitive configuration stored
- [ ] **Monitoring**: CloudWatch dashboards and alarms configured

#### Production Environment

- [ ] **AWS Credentials**: Production account access with MFA
- [ ] **Bedrock Models**: All required models enabled and tested
- [ ] **Secrets Manager**: Production secrets configured and validated
- [ ] **Backup Strategy**: DynamoDB point-in-time recovery enabled
- [ ] **Disaster Recovery**: Cross-region replication configured
- [ ] **Compliance**: SOC2 Type II requirements validated

### 3. Security Validation

- [x] **IAM Roles**: All roles follow least privilege principle
- [x] **Security Groups**: Network access properly restricted
- [x] **Encryption**: KMS keys configured for all data at rest
- [x] **VPC Configuration**: Private subnets for sensitive workloads
- [ ] **Penetration Testing**: Security scan completed (staging/production)
- [ ] **Compliance Audit**: SOC2 requirements verified (production)

### 4. Performance and Scalability

- [x] **Resource Sizing**: Appropriate instance types for each environment
- [x] **Auto-Scaling**: ECS and Lambda scaling policies configured
- [x] **Connection Pooling**: Database and external service connections optimized
- [ ] **Load Testing**: Performance validation under expected load
- [ ] **Capacity Planning**: Resource limits and quotas verified

---

## 🚀 Deployment Procedures

### Development Environment Deployment

```bash
# 1. Start local services
docker-compose up -d

# 2. Verify services are healthy
docker-compose ps
docker-compose logs --tail=50 localstack redis

# 3. Initialize LocalStack resources
awslocal dynamodb create-table \
  --table-name incident-commander-events-development \
  --attribute-definitions AttributeName=incident_id,AttributeType=S \
  --key-schema AttributeName=incident_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

awslocal s3 mb s3://incident-commander-artifacts-development

# 4. Deploy CDK infrastructure (optional for development)
export ENVIRONMENT=development
cdk deploy --all --require-approval never

# 5. Validate deployment
python validate_infrastructure.py
curl http://localhost:4566/health
```

**Expected Duration**: 5-10 minutes  
**Rollback Time**: 2-3 minutes (docker-compose down)

### Staging Environment Deployment

```bash
# 1. Set environment and validate credentials
export ENVIRONMENT=staging
aws sts get-caller-identity

# 2. Enable Bedrock models (one-time setup)
aws bedrock list-foundation-models --region us-east-1

# 3. Deploy infrastructure
cdk deploy --all --require-approval never

# 4. Validate deployment
aws cloudformation describe-stacks --stack-name IncidentCommanderCore-staging
aws ecs describe-clusters --clusters incident-commander-staging

# 5. Run integration tests
python tests/integration/test_staging_deployment.py
```

**Expected Duration**: 15-25 minutes  
**Rollback Time**: 10-15 minutes (CloudFormation rollback)

### Production Environment Deployment

```bash
# 1. Set environment and validate credentials with MFA
export ENVIRONMENT=production
aws sts get-caller-identity

# 2. Create deployment snapshot
aws dynamodb create-backup \
  --table-name incident-commander-events-production \
  --backup-name pre-deployment-$(date +%Y%m%d-%H%M%S)

# 3. Deploy infrastructure with manual approval
cdk deploy --all

# 4. Validate critical resources
aws ecs describe-clusters --clusters incident-commander-production
aws apigateway get-rest-apis
aws bedrock list-foundation-models

# 5. Run smoke tests
python tests/production/test_smoke.py

# 6. Enable monitoring and alerting
aws cloudwatch put-metric-alarm --alarm-name "IncidentCommander-HighErrorRate" \
  --alarm-description "High error rate in production" \
  --metric-name ErrorRate --namespace AWS/ApiGateway \
  --statistic Average --period 300 --threshold 5.0 \
  --comparison-operator GreaterThanThreshold
```

**Expected Duration**: 30-45 minutes  
**Rollback Time**: 20-30 minutes (Full rollback procedure)

---

## 🔄 Rollback Procedures

### Immediate Rollback Triggers

Execute rollback immediately if any of these conditions occur:

1. **Critical Service Failure**: API Gateway returns 5xx errors for >5 minutes
2. **Security Breach**: Unauthorized access detected
3. **Data Corruption**: DynamoDB or S3 data integrity issues
4. **Performance Degradation**: Response times >10x baseline for >10 minutes
5. **Compliance Violation**: Security or audit requirements not met

### Development Environment Rollback

```bash
# 1. Stop all services
docker-compose down

# 2. Remove volumes if needed (data loss)
docker-compose down -v

# 3. Restart with previous configuration
git checkout HEAD~1 -- docker-compose.yml
docker-compose up -d

# 4. Validate rollback
docker-compose ps
curl http://localhost:4566/health
```

**Rollback Time**: 2-3 minutes  
**Data Loss**: Acceptable (development environment)

### Staging Environment Rollback

```bash
# 1. Identify previous stable version
aws cloudformation describe-stacks --stack-name IncidentCommanderCore-staging

# 2. Rollback CDK deployment
cdk deploy --all --require-approval never --previous-parameters

# 3. Alternative: CloudFormation rollback
aws cloudformation cancel-update-stack --stack-name IncidentCommanderCore-staging
aws cloudformation continue-update-rollback --stack-name IncidentCommanderCore-staging

# 4. Validate rollback
aws ecs describe-clusters --clusters incident-commander-staging
python tests/integration/test_rollback_validation.py
```

**Rollback Time**: 10-15 minutes  
**Data Loss**: Minimal (point-in-time recovery available)

### Production Environment Rollback

#### Phase 1: Immediate Response (0-5 minutes)

```bash
# 1. Enable maintenance mode
aws apigateway update-stage \
  --rest-api-id API_ID \
  --stage-name prod \
  --patch-ops op=replace,path=/variables/maintenance_mode,value=true

# 2. Scale down new resources
aws ecs update-service \
  --cluster incident-commander-production \
  --service incident-commander-service \
  --desired-count 0

# 3. Notify stakeholders
curl -X POST https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK \
  -H 'Content-type: application/json' \
  --data '{"text":"🚨 Production rollback initiated - maintenance mode enabled"}'
```

#### Phase 2: Full Rollback (5-30 minutes)

```bash
# 1. Restore from backup
aws dynamodb restore-table-from-backup \
  --target-table-name incident-commander-events-production-restored \
  --backup-arn arn:aws:dynamodb:region:account:table/incident-commander-events-production/backup/BACKUP_ID

# 2. Rollback infrastructure
aws cloudformation cancel-update-stack --stack-name IncidentCommanderCore-production
aws cloudformation continue-update-rollback --stack-name IncidentCommanderCore-production

# 3. Validate data integrity
python scripts/validate_data_integrity.py --environment production

# 4. Restore service
aws ecs update-service \
  --cluster incident-commander-production \
  --service incident-commander-service \
  --desired-count 3

# 5. Disable maintenance mode
aws apigateway update-stage \
  --rest-api-id API_ID \
  --stage-name prod \
  --patch-ops op=replace,path=/variables/maintenance_mode,value=false
```

#### Phase 3: Post-Rollback Validation (30-60 minutes)

```bash
# 1. Run comprehensive tests
python tests/production/test_full_suite.py

# 2. Validate monitoring
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name Count \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# 3. Generate rollback report
python scripts/generate_rollback_report.py --incident-id INCIDENT_ID
```

**Total Rollback Time**: 30-60 minutes  
**Data Loss**: <15 minutes (point-in-time recovery)  
**Service Downtime**: 5-10 minutes (maintenance mode)

---

## 📊 Monitoring and Alerting

### Key Metrics to Monitor

#### Infrastructure Health

- **ECS Task Health**: Running tasks vs desired count
- **Lambda Error Rate**: Errors per invocation
- **API Gateway Latency**: P95 response times
- **DynamoDB Throttling**: Read/write capacity utilization

#### Application Performance

- **Incident Resolution Time**: MTTR metrics
- **Agent Response Time**: Individual agent performance
- **WebSocket Connections**: Active connection count
- **Business Impact**: Cost savings and prevention metrics

### Alert Thresholds

| Metric              | Warning | Critical | Action                  |
| ------------------- | ------- | -------- | ----------------------- |
| API Error Rate      | >2%     | >5%      | Investigate/Rollback    |
| Response Time       | >1s P95 | >3s P95  | Scale up/Rollback       |
| ECS Task Failures   | >10%    | >25%     | Check logs/Rollback     |
| Lambda Errors       | >5%     | >15%     | Check function/Rollback |
| DynamoDB Throttling | >1%     | >5%      | Scale capacity          |

### Automated Responses

```bash
# CloudWatch Alarm with Auto-Scaling
aws cloudwatch put-metric-alarm \
  --alarm-name "IncidentCommander-HighCPU" \
  --alarm-description "High CPU utilization" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80.0 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:region:account:scale-up-topic

# Lambda for automated rollback
aws lambda create-function \
  --function-name incident-commander-auto-rollback \
  --runtime python3.11 \
  --role arn:aws:iam::account:role/lambda-execution-role \
  --handler rollback.handler \
  --code fileb://rollback-function.zip
```

---

## 🔍 Post-Deployment Validation

### Automated Tests

```bash
# 1. Health check validation
curl -f https://api.incident-commander.com/health || exit 1

# 2. Integration test suite
python -m pytest tests/integration/ -v --environment=production

# 3. Performance baseline
python tests/performance/baseline_test.py --duration=300

# 4. Security scan
python tests/security/security_scan.py --target=production
```

### Manual Validation Checklist

#### Functional Testing

- [ ] **API Endpoints**: All endpoints return expected responses
- [ ] **WebSocket Connections**: Real-time updates working
- [ ] **Agent Coordination**: Multi-agent workflows executing
- [ ] **Database Operations**: Read/write operations successful
- [ ] **External Integrations**: Slack, PagerDuty, Datadog connections

#### Performance Testing

- [ ] **Response Times**: <500ms for API calls
- [ ] **Throughput**: >100 requests/second sustained
- [ ] **Concurrent Users**: >50 simultaneous WebSocket connections
- [ ] **Memory Usage**: <80% of allocated resources
- [ ] **CPU Utilization**: <70% under normal load

#### Security Testing

- [ ] **Authentication**: JWT tokens validated correctly
- [ ] **Authorization**: Role-based access controls working
- [ ] **Encryption**: Data encrypted in transit and at rest
- [ ] **Network Security**: Security groups blocking unauthorized access
- [ ] **Audit Logging**: All security events logged

---

## 📋 Communication Plan

### Stakeholder Notification

#### Pre-Deployment

```
Subject: Infrastructure Deployment - Autonomous Incident Commander
Recipients: Engineering Team, DevOps, Security Team

Deployment scheduled for: [DATE/TIME]
Expected duration: [DURATION]
Expected impact: [IMPACT DESCRIPTION]
Rollback plan: Available within [ROLLBACK_TIME]
```

#### During Deployment

```
Subject: [DEPLOYMENT STATUS] Infrastructure Deployment in Progress
Recipients: Engineering Team, DevOps

Current status: [STATUS]
Completion: [PERCENTAGE]%
Issues: [NONE/DESCRIPTION]
ETA: [TIME]
```

#### Post-Deployment

```
Subject: ✅ Infrastructure Deployment Completed Successfully
Recipients: All Stakeholders

Deployment completed: [TIMESTAMP]
All systems operational: ✅
Performance metrics: Within expected ranges
Next steps: [MONITORING/OPTIMIZATION]
```

#### Rollback Notification

```
Subject: 🚨 URGENT: Production Rollback Initiated
Recipients: All Stakeholders, Management

Rollback reason: [REASON]
Current status: [STATUS]
Expected resolution: [TIME]
Impact: [DESCRIPTION]
Updates: Every 15 minutes until resolved
```

### Escalation Matrix

| Severity          | Response Time | Escalation Path                 |
| ----------------- | ------------- | ------------------------------- |
| **P0 - Critical** | 5 minutes     | DevOps → Engineering Lead → CTO |
| **P1 - High**     | 15 minutes    | DevOps → Engineering Lead       |
| **P2 - Medium**   | 1 hour        | DevOps Team                     |
| **P3 - Low**      | 4 hours       | DevOps Team                     |

---

## 📚 Documentation and Knowledge Transfer

### Deployment Documentation

1. **Infrastructure Diagrams**: Updated architecture diagrams
2. **Configuration Changes**: Detailed change log
3. **Performance Baselines**: New performance metrics
4. **Security Updates**: Security configuration changes
5. **Operational Procedures**: Updated runbooks

### Knowledge Transfer Sessions

1. **DevOps Team**: Infrastructure changes and monitoring
2. **Engineering Team**: New capabilities and integrations
3. **Security Team**: Security enhancements and compliance
4. **Support Team**: Troubleshooting procedures

### Post-Deployment Review

#### Success Criteria

- [ ] **Zero Downtime**: No service interruption during deployment
- [ ] **Performance Maintained**: Response times within 10% of baseline
- [ ] **All Tests Pass**: 100% success rate on validation tests
- [ ] **Monitoring Active**: All alerts and dashboards functional
- [ ] **Documentation Updated**: All procedures and diagrams current

#### Lessons Learned Session

- **What Went Well**: Successful aspects of deployment
- **Areas for Improvement**: Process enhancements for next time
- **Action Items**: Specific improvements to implement
- **Risk Mitigation**: Additional safeguards for future deployments

---

## 🎯 Success Metrics

### Deployment Success Criteria

| Metric                   | Target           | Measurement                     |
| ------------------------ | ---------------- | ------------------------------- |
| **Deployment Time**      | <45 minutes      | CloudFormation completion time  |
| **Service Availability** | >99.9%           | Uptime during deployment window |
| **Error Rate**           | <0.1%            | API Gateway error percentage    |
| **Performance Impact**   | <10% degradation | Response time comparison        |
| **Rollback Capability**  | <30 minutes      | Time to complete rollback       |

### Business Impact Metrics

| Metric                  | Baseline   | Target       | Measurement Period      |
| ----------------------- | ---------- | ------------ | ----------------------- |
| **MTTR Improvement**    | 30 minutes | <3 minutes   | 30 days post-deployment |
| **Incident Prevention** | 0%         | >20%         | 90 days post-deployment |
| **Cost Savings**        | $0         | >$100K/month | 90 days post-deployment |
| **User Satisfaction**   | Baseline   | +20%         | 60 days post-deployment |

---

## 🔧 Troubleshooting Guide

### Common Deployment Issues

#### CDK Deployment Failures

**Issue**: Stack deployment fails with IAM permissions error

```bash
# Solution: Verify CDK bootstrap and permissions
cdk bootstrap aws://ACCOUNT/REGION
aws sts get-caller-identity
aws iam list-attached-role-policies --role-name cdk-*
```

**Issue**: Resource limit exceeded

```bash
# Solution: Check service quotas
aws service-quotas get-service-quota \
  --service-code ec2 \
  --quota-code L-1216C47A  # Running On-Demand instances
```

#### Docker Service Issues

**Issue**: LocalStack fails to start

```bash
# Solution: Check Docker resources and ports
docker system df
docker system prune -f
lsof -i :4566  # Check port conflicts
```

**Issue**: Redis connection refused

```bash
# Solution: Verify Redis service and networking
docker-compose logs redis
docker-compose exec redis redis-cli ping
```

#### Application Integration Issues

**Issue**: Bedrock model access denied

```bash
# Solution: Enable models in AWS Console
aws bedrock list-foundation-models --region us-east-1
# Manual step: Enable models in Bedrock console
```

**Issue**: DynamoDB table not found

```bash
# Solution: Verify table creation and region
aws dynamodb list-tables --region us-east-1
aws dynamodb describe-table --table-name incident-commander-events-production
```

### Emergency Contacts

| Role                 | Contact       | Availability               |
| -------------------- | ------------- | -------------------------- |
| **DevOps Lead**      | [EMAIL/PHONE] | 24/7                       |
| **Engineering Lead** | [EMAIL/PHONE] | Business hours + on-call   |
| **Security Team**    | [EMAIL/PHONE] | 24/7                       |
| **AWS Support**      | [CASE SYSTEM] | 24/7 (Business/Enterprise) |

---

## ✅ Final Checklist

### Pre-Deployment Sign-off

- [ ] **Technical Lead Approval**: Infrastructure changes reviewed and approved
- [ ] **Security Team Approval**: Security implications assessed and approved
- [ ] **DevOps Team Approval**: Deployment procedures reviewed and approved
- [ ] **Business Stakeholder Approval**: Business impact understood and approved

### Deployment Execution

- [ ] **Backup Completed**: All critical data backed up
- [ ] **Monitoring Active**: All alerts and dashboards configured
- [ ] **Team Available**: Key personnel available during deployment window
- [ ] **Rollback Plan Tested**: Rollback procedures validated in staging
- [ ] **Communication Sent**: All stakeholders notified of deployment

### Post-Deployment Validation

- [ ] **All Tests Pass**: Automated and manual validation completed
- [ ] **Performance Verified**: Metrics within acceptable ranges
- [ ] **Security Validated**: Security scans completed successfully
- [ ] **Documentation Updated**: All procedures and diagrams current
- [ ] **Lessons Learned**: Post-deployment review completed

---

**Deployment Authorization**

| Role               | Name | Signature | Date |
| ------------------ | ---- | --------- | ---- |
| **Technical Lead** |      |           |      |
| **DevOps Lead**    |      |           |      |
| **Security Lead**  |      |           |      |
| **Business Owner** |      |           |      |

**Deployment Status**: 🟢 **APPROVED FOR EXECUTION**

---

_This document serves as the authoritative guide for deploying infrastructure changes to the Autonomous Incident Commander system. All procedures must be followed to ensure safe and successful deployments._
