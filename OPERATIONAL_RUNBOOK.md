# Operational Runbook: Incident Commander

Day-to-day operations guide for running Incident Commander in production.

---

## Daily Operations

### Morning Checklist
```bash
# 1. Check system health
curl https://<backend-url>/health

# 2. Verify all dashboards accessible
curl -I https://<cloudfront-url>/demo
curl -I https://<cloudfront-url>/transparency
curl -I https://<cloudfront-url>/ops

# 3. Check CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=backend \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average

# 4. Review overnight incidents (if any)
aws dynamodb scan \
  --table-name incident-commander-incidents \
  --filter-expression "created_at > :yesterday" \
  --expression-attribute-values '{":yesterday":{"S":"2025-10-21"}}'

# 5. Check for alarms
aws cloudwatch describe-alarms --state-value ALARM
```

---

## Common Operations

### Scaling the Backend

#### Manual Scaling
```bash
# Scale up
aws ecs update-service \
  --cluster incident-commander \
  --service backend \
  --desired-count 5

# Scale down
aws ecs update-service \
  --cluster incident-commander \
  --service backend \
  --desired-count 2

# Verify
aws ecs describe-services \
  --cluster incident-commander \
  --services backend
```

#### Auto-Scaling Settings
```bash
# View current auto-scaling
aws application-autoscaling describe-scalable-targets \
  --service-namespace ecs \
  --resource-ids service/incident-commander/backend

# Update auto-scaling limits
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/incident-commander/backend \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 20  # Increased max
```

### Deploying Updates

#### Backend Update
```bash
# 1. Build new image
docker build -t incident-commander:v2 .

# 2. Tag and push
docker tag incident-commander:v2 <ecr-repo>:v2
docker push <ecr-repo>:v2

# 3. Update task definition
aws ecs register-task-definition \
  --cli-input-json file://task-definition-v2.json

# 4. Update service
aws ecs update-service \
  --cluster incident-commander \
  --service backend \
  --task-definition incident-commander:2

# 5. Monitor deployment
aws ecs wait services-stable \
  --cluster incident-commander \
  --services backend
```

#### Dashboard Update
```bash
# 1. Build
cd dashboard && npm run build

# 2. Deploy to S3
aws s3 sync out/ s3://<dashboard-bucket>/ --delete

# 3. Invalidate CloudFront
aws cloudfront create-invalidation \
  --distribution-id <dist-id> \
  --paths "/*"

# 4. Verify
curl -I https://<cloudfront-url>/
```

### Database Maintenance

#### Backup DynamoDB Tables
```bash
# Create on-demand backup
aws dynamodb create-backup \
  --table-name incident-commander-incidents \
  --backup-name incidents-backup-$(date +%Y%m%d)

# List backups
aws dynamodb list-backups \
  --table-name incident-commander-incidents
```

#### Restore from Backup
```bash
# Restore to new table
aws dynamodb restore-table-from-backup \
  --target-table-name incident-commander-incidents-restored \
  --backup-arn arn:aws:dynamodb:...
```

#### Query Incidents
```bash
# Get active incidents
aws dynamodb query \
  --table-name incident-commander-incidents \
  --index-name status-index \
  --key-condition-expression "status = :s" \
  --expression-attribute-values '{":s":{"S":"active"}}'

# Get incidents by time range
aws dynamodb scan \
  --table-name incident-commander-incidents \
  --filter-expression "created_at BETWEEN :start AND :end" \
  --expression-attribute-values \
    '{":start":{"S":"2025-10-22T00:00:00Z"},":end":{"S":"2025-10-22T23:59:59Z"}}'
```

---

## Monitoring and Alerts

### View CloudWatch Logs
```bash
# Tail live logs
aws logs tail /ecs/incident-commander --follow

# Search logs
aws logs filter-log-events \
  --log-group-name /ecs/incident-commander \
  --filter-pattern "ERROR" \
  --start-time $(date -d '1 hour ago' +%s)000

# Download logs
aws logs get-log-events \
  --log-group-name /ecs/incident-commander \
  --log-stream-name <stream-name> \
  --start-time $(date -d '1 hour ago' +%s)000 \
  > logs.json
```

### Check Metrics
```bash
# ECS Service metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name MemoryUtilization \
  --dimensions Name=ServiceName,Value=backend \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum

# ALB metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name TargetResponseTime \
  --dimensions Name=LoadBalancer,Value=app/... \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Average,Maximum
```

### Alarm Management
```bash
# List active alarms
aws cloudwatch describe-alarms --state-value ALARM

# Acknowledge alarm (disable temporarily)
aws cloudwatch disable-alarm-actions --alarm-names "incident-commander-high-cpu"

# Re-enable
aws cloudwatch enable-alarm-actions --alarm-names "incident-commander-high-cpu"
```

---

## Incident Response

### High CPU Usage

**Symptoms**: CPU utilization > 90%

**Investigation**:
```bash
# 1. Check current CPU
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=backend \
  --start-time $(date -u -d '10 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Average

# 2. Check task count
aws ecs describe-services \
  --cluster incident-commander \
  --services backend \
  --query 'services[0].{desired:desiredCount,running:runningCount,pending:pendingCount}'

# 3. Review logs for errors
aws logs filter-log-events \
  --log-group-name /ecs/incident-commander \
  --filter-pattern "ERROR" \
  --start-time $(date -d '10 minutes ago' +%s)000
```

**Resolution**:
```bash
# Option 1: Scale up immediately
aws ecs update-service \
  --cluster incident-commander \
  --service backend \
  --desired-count 5

# Option 2: Increase auto-scaling max
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/incident-commander/backend \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 15  # Increased
```

---

### High Error Rate

**Symptoms**: 5xx errors > 10/minute

**Investigation**:
```bash
# 1. Check error count
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name HTTPCode_Target_5XX_Count \
  --dimensions Name=LoadBalancer,Value=app/... \
  --start-time $(date -u -d '10 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Sum

# 2. Check target health
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:...

# 3. Check application logs
aws logs filter-log-events \
  --log-group-name /ecs/incident-commander \
  --filter-pattern "500" \
  --start-time $(date -d '10 minutes ago' +%s)000
```

**Resolution**:
```bash
# 1. Restart unhealthy tasks
aws ecs update-service \
  --cluster incident-commander \
  --service backend \
  --force-new-deployment

# 2. If issues persist, rollback
aws ecs update-service \
  --cluster incident-commander \
  --service backend \
  --task-definition incident-commander:1  # Previous version
```

---

### WebSocket Connection Issues

**Symptoms**: Dashboard 3 shows "Disconnected"

**Investigation**:
```bash
# 1. Test WebSocket endpoint
wscat -c ws://<alb-dns>/ws?client_id=test

# 2. Check ALB target health
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:...

# 3. Verify sticky sessions
aws elbv2 describe-target-group-attributes \
  --target-group-arn ... \
  --query 'Attributes[?Key==`stickiness.enabled`]'

# 4. Check WebSocket logs
aws logs filter-log-events \
  --log-group-name /ecs/incident-commander \
  --filter-pattern "websocket" \
  --start-time $(date -d '10 minutes ago' +%s)000
```

**Resolution**:
```bash
# 1. Ensure sticky sessions enabled
aws elbv2 modify-target-group-attributes \
  --target-group-arn ... \
  --attributes Key=stickiness.enabled,Value=true \
               Key=stickiness.type,Value=lb_cookie \
               Key=stickiness.lb_cookie.duration_seconds,Value=3600

# 2. Restart service if needed
aws ecs update-service \
  --cluster incident-commander \
  --service backend \
  --force-new-deployment
```

---

### Database Throttling

**Symptoms**: DynamoDB throttling errors in logs

**Investigation**:
```bash
# Check throttle metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name UserErrors \
  --dimensions Name=TableName,Value=incident-commander-incidents \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

**Resolution**:
```bash
# DynamoDB is on-demand mode, should auto-scale
# If issues persist, check for hot partition keys

# Review access patterns
aws dynamodb describe-table --table-name incident-commander-incidents
```

---

## Backup and Recovery

### Create Full System Backup
```bash
#!/bin/bash
# backup.sh - Create full system backup

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)

# 1. Backup DynamoDB tables
for table in incident-commander-incidents incident-commander-agent-state; do
  aws dynamodb create-backup \
    --table-name $table \
    --backup-name ${table}-${BACKUP_DATE}
done

# 2. Backup S3 dashboard
aws s3 sync s3://<dashboard-bucket>/ ./backups/dashboard-${BACKUP_DATE}/

# 3. Export CloudWatch logs
aws logs create-export-task \
  --log-group-name /ecs/incident-commander \
  --from $(date -d '7 days ago' +%s)000 \
  --to $(date +%s)000 \
  --destination s3://<backup-bucket>/logs-${BACKUP_DATE}

echo "Backup complete: ${BACKUP_DATE}"
```

### Disaster Recovery
```bash
# 1. Restore DynamoDB
aws dynamodb restore-table-from-backup \
  --target-table-name incident-commander-incidents \
  --backup-arn <backup-arn>

# 2. Redeploy infrastructure
cd infrastructure/cdk && cdk deploy

# 3. Restore dashboard
aws s3 sync ./backups/dashboard-<date>/ s3://<new-bucket>/

# 4. Verify
curl https://<new-alb-dns>/health
```

---

## Performance Optimization

### Database Query Optimization
```bash
# Add GSI for frequently queried fields
aws dynamodb update-table \
  --table-name incident-commander-incidents \
  --attribute-definitions AttributeName=severity,AttributeType=S \
  --global-secondary-index-updates \
    "[{\"Create\":{\"IndexName\":\"severity-index\",\"KeySchema\":[{\"AttributeName\":\"severity\",\"KeyType\":\"HASH\"}],\"Projection\":{\"ProjectionType\":\"ALL\"}}}]"
```

### Cache Optimization
```bash
# Enable CloudFront caching for static assets
aws cloudfront update-distribution \
  --id <dist-id> \
  --distribution-config file://cloudfront-config.json
```

### Connection Pool Tuning
Edit `src/main.py`:
```python
# Adjust based on load
uvicorn.run(
    app,
    host="0.0.0.0",
    port=8000,
    workers=4,  # Increase for more concurrency
    limit_concurrency=1000
)
```

---

## Security Operations

### Rotate Credentials
```bash
# 1. Generate new credentials
aws iam create-access-key --user-name incident-commander

# 2. Update task definition with new secrets
aws ecs register-task-definition --cli-input-json file://task-def-new-creds.json

# 3. Update service
aws ecs update-service \
  --cluster incident-commander \
  --service backend \
  --task-definition incident-commander:3

# 4. Delete old credentials
aws iam delete-access-key --access-key-id <old-key> --user-name incident-commander
```

### Review Security Groups
```bash
# List security groups
aws ec2 describe-security-groups \
  --filters Name=group-name,Values=incident-commander*

# Review inbound rules
aws ec2 describe-security-groups \
  --group-ids sg-xxx \
  --query 'SecurityGroups[0].IpPermissions'
```

### Enable VPC Flow Logs
```bash
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids vpc-xxx \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs \
  --log-destination arn:aws:logs:us-west-2:ACCOUNT:log-group:/aws/vpc/flowlogs
```

---

## Cost Management

### View Current Costs
```bash
# Get cost for last 7 days
aws ce get-cost-and-usage \
  --time-period Start=$(date -d '7 days ago' +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity DAILY \
  --metrics BlendedCost \
  --filter file://cost-filter.json
```

### Cost Optimization
```bash
# 1. Stop unused resources (non-prod)
aws ecs update-service \
  --cluster incident-commander-dev \
  --service backend \
  --desired-count 0

# 2. Enable S3 lifecycle policies
aws s3api put-bucket-lifecycle-configuration \
  --bucket <backup-bucket> \
  --lifecycle-configuration file://lifecycle.json

# 3. Review CloudWatch log retention
aws logs put-retention-policy \
  --log-group-name /ecs/incident-commander \
  --retention-in-days 7  # Reduce from default
```

---

## Weekly Maintenance

### Weekly Checklist
- [ ] Review CloudWatch costs
- [ ] Check for unused resources
- [ ] Update dependencies (security patches)
- [ ] Review and archive old incidents
- [ ] Backup critical data
- [ ] Review alarms and metrics
- [ ] Check auto-scaling effectiveness

### Generate Weekly Report
```bash
#!/bin/bash
# weekly-report.sh

echo "=== Incident Commander Weekly Report ==="
echo "Week of: $(date)"
echo

echo "System Health:"
aws ecs describe-services \
  --cluster incident-commander \
  --services backend \
  --query 'services[0].{RunningTasks:runningCount,DesiredTasks:desiredCount}'

echo
echo "Incident Stats (last 7 days):"
aws dynamodb scan \
  --table-name incident-commander-incidents \
  --filter-expression "created_at > :week_ago" \
  --expression-attribute-values '{":week_ago":{"S":"'$(date -d '7 days ago' +%Y-%m-%d)'"}}' \
  --select COUNT

echo
echo "Cost (last 7 days):"
aws ce get-cost-and-usage \
  --time-period Start=$(date -d '7 days ago' +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity DAILY \
  --metrics BlendedCost
```

---

## Contact Information

- **On-Call Engineer**: [Your contact]
- **AWS Support**: Premium Support Ticket
- **Escalation**: [Team lead contact]
- **Documentation**: `/documentation` directory

---

**Happy Operations!** 🚀
