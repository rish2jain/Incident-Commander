# Deployment Guide: Incident Commander

Complete guide for deploying Incident Commander to AWS production.

---

## Prerequisites

### 1. AWS Account Setup
```bash
# Configure AWS credentials
aws configure
# Or export environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_REGION=us-west-2
```

### 2. Install Dependencies
```bash
# CDK
npm install -g aws-cdk
pip install -r infrastructure/cdk/requirements.txt

# Backend
pip install -r requirements.txt

# Dashboard
cd dashboard && npm install
```

### 3. Configure AWS Services

#### Amazon Q Business (Optional - $3K Prize)
```bash
# Create Q Business application
aws qbusiness create-application \
  --display-name "Incident-Commander" \
  --region us-west-2

# Get application ID
export Q_BUSINESS_APP_ID=<your-app-id>
```

#### Bedrock Agents (Optional - $3K Prize)
```bash
# Create diagnosis agent
aws bedrock-agent create-agent \
  --agent-name incident-diagnosis-agent \
  --foundation-model anthropic.claude-3-5-sonnet-20241022-v2:0 \
  --instruction "You are an incident diagnosis specialist..."

# Get agent details
export DIAGNOSIS_AGENT_ID=<agent-id>
export DIAGNOSIS_AGENT_ALIAS=<alias-id>
```

---

## Deployment Options

### Option 1: AWS CDK (Recommended)

#### Step 1: Bootstrap CDK
```bash
cd infrastructure/cdk
cdk bootstrap aws://ACCOUNT-ID/us-west-2
```

#### Step 2: Deploy Infrastructure
```bash
# Review changes
cdk diff

# Deploy
cdk deploy

# Save outputs
cdk deploy --outputs-file outputs.json
```

#### Step 3: Deploy Dashboard
```bash
cd ../../dashboard
npm run build

# Get bucket name from CDK outputs
BUCKET_NAME=$(cat ../infrastructure/cdk/outputs.json | jq -r '.IncidentCommanderStack.DashboardBucketName')

# Deploy to S3
aws s3 sync out/ s3://$BUCKET_NAME/

# Invalidate CloudFront cache
DIST_ID=$(cat ../infrastructure/cdk/outputs.json | jq -r '.IncidentCommanderStack.DistributionId')
aws cloudfront create-invalidation --distribution-id $DIST_ID --paths "/*"
```

#### Step 4: Verify Deployment
```bash
# Get URLs from outputs
cat infrastructure/cdk/outputs.json

# Test backend
curl https://<ALB-DNS>/health

# Test WebSocket
wscat -c ws://<ALB-DNS>/ws?client_id=test

# Visit dashboards
open https://<CloudFront-URL>/demo
open https://<CloudFront-URL>/transparency
open https://<CloudFront-URL>/ops
```

---

### Option 2: Manual Deployment

#### Step 1: Create VPC and Security Groups
```bash
# Create VPC
aws ec2 create-vpc --cidr-block 10.0.0.0/16

# Create subnets
aws ec2 create-subnet --vpc-id vpc-xxx --cidr-block 10.0.1.0/24
aws ec2 create-subnet --vpc-id vpc-xxx --cidr-block 10.0.2.0/24
```

#### Step 2: Create ECS Cluster
```bash
aws ecs create-cluster --cluster-name incident-commander
```

#### Step 3: Build and Push Docker Image
```bash
# Build
docker build -t incident-commander:latest .

# Tag for ECR
docker tag incident-commander:latest <account-id>.dkr.ecr.us-west-2.amazonaws.com/incident-commander:latest

# Login to ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-west-2.amazonaws.com

# Push
docker push <account-id>.dkr.ecr.us-west-2.amazonaws.com/incident-commander:latest
```

#### Step 4: Create Task Definition
```bash
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

#### Step 5: Create Service
```bash
aws ecs create-service \
  --cluster incident-commander \
  --service-name backend \
  --task-definition incident-commander:1 \
  --desired-count 2 \
  --launch-type FARGATE
```

---

## Environment Variables

### Backend
```bash
# Required
export AWS_REGION=us-west-2
export INCIDENTS_TABLE=incident-commander-incidents
export AGENT_STATE_TABLE=incident-commander-agent-state

# Optional (Prize Services)
export Q_BUSINESS_APP_ID=<app-id>
export DIAGNOSIS_AGENT_ID=<agent-id>
export DIAGNOSIS_AGENT_ALIAS=<alias-id>

# Optional (Configuration)
export LOG_LEVEL=INFO
export MAX_WEBSOCKET_CONNECTIONS=1000
export ENVIRONMENT=production
```

### Frontend
```bash
# Required
export NEXT_PUBLIC_WEBSOCKET_URL=ws://<backend-url>/ws
export NEXT_PUBLIC_API_URL=https://<backend-url>
```

---

## Post-Deployment Configuration

### 1. Configure Auto-Scaling
```bash
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/incident-commander/backend \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10

aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/incident-commander/backend \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name cpu-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration file://scaling-policy.json
```

### 2. Configure CloudWatch Alarms
```bash
# High CPU alarm
aws cloudwatch put-metric-alarm \
  --alarm-name incident-commander-high-cpu \
  --alarm-description "Backend CPU usage too high" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 90 \
  --comparison-operator GreaterThanThreshold

# High error rate alarm
aws cloudwatch put-metric-alarm \
  --alarm-name incident-commander-high-errors \
  --alarm-description "Too many 5xx errors" \
  --metric-name HTTPCode_Target_5XX_Count \
  --namespace AWS/ApplicationELB \
  --statistic Sum \
  --period 60 \
  --evaluation-periods 2 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold
```

### 3. Enable Logging
```bash
# Create log group
aws logs create-log-group --log-group-name /ecs/incident-commander

# Set retention
aws logs put-retention-policy \
  --log-group-name /ecs/incident-commander \
  --retention-in-days 7
```

---

## Verification Checklist

- [ ] Backend health endpoint responds: `curl https://<backend>/health`
- [ ] WebSocket connections work: `wscat -c ws://<backend>/ws`
- [ ] Dashboard 1 loads: `/demo`
- [ ] Dashboard 2 loads: `/transparency`
- [ ] Dashboard 3 connects to WebSocket: `/ops`
- [ ] DynamoDB tables created
- [ ] CloudWatch metrics flowing
- [ ] Auto-scaling configured
- [ ] Alarms created
- [ ] Logs streaming to CloudWatch

---

## Troubleshooting

### Backend Not Starting
```bash
# Check ECS task logs
aws logs tail /ecs/incident-commander --follow

# Check task status
aws ecs describe-tasks --cluster incident-commander --tasks <task-id>

# Check security groups
aws ec2 describe-security-groups --group-ids sg-xxx
```

### WebSocket Connection Failing
```bash
# Check ALB target health
aws elbv2 describe-target-health --target-group-arn arn:aws:elasticloadbalancing:...

# Check ALB access logs
aws s3 ls s3://alb-logs-bucket/

# Verify sticky sessions enabled
aws elbv2 describe-target-group-attributes --target-group-arn ...
```

### Dashboard Not Loading
```bash
# Check S3 bucket
aws s3 ls s3://<dashboard-bucket>/

# Check CloudFront distribution
aws cloudfront get-distribution --id <dist-id>

# Clear CloudFront cache
aws cloudfront create-invalidation --distribution-id <dist-id> --paths "/*"
```

---

## Rollback Procedure

### CDK Deployment
```bash
# Rollback to previous version
cdk deploy --rollback

# Or delete and redeploy
cdk destroy
cdk deploy
```

### ECS Service
```bash
# Update service to previous task definition
aws ecs update-service \
  --cluster incident-commander \
  --service backend \
  --task-definition incident-commander:1  # Previous version
```

---

## Monitoring

### CloudWatch Dashboard
```bash
# View operational dashboard
https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#dashboards:name=IncidentCommander
```

### Key Metrics
- ECS Service: CPU, Memory, Task Count
- ALB: Request Count, Response Time, 5xx Errors
- DynamoDB: Read/Write Capacity, Throttles
- CloudFront: Requests, Error Rate, Cache Hit Ratio

---

## Cost Optimization

### Estimate Monthly Costs
- ECS Fargate (2 tasks): ~$50/month
- ALB: ~$20/month
- DynamoDB (on-demand): ~$10/month
- S3 + CloudFront: ~$5/month
- Data transfer: Variable

**Total: ~$85-100/month** (low traffic)

### Cost Reduction Tips
1. Use reserved capacity for predictable workloads
2. Enable S3 lifecycle policies
3. Use DynamoDB reserved capacity
4. Set up CloudWatch alarm to stop idle resources

---

## Security Checklist

- [ ] IAM roles follow least privilege
- [ ] Security groups restrict access
- [ ] ALB uses HTTPS (if certificate configured)
- [ ] S3 bucket policies reviewed
- [ ] CloudWatch Logs enabled
- [ ] DynamoDB encryption at rest enabled
- [ ] VPC flow logs enabled
- [ ] AWS WAF rules configured (optional)

---

## Next Steps After Deployment

1. **Test All 3 Dashboards**
   - Dashboard 1 (`/demo`): Executive presentation
   - Dashboard 2 (`/transparency`): Technical deep-dive
   - Dashboard 3 (`/ops`): Live WebSocket operations

2. **Configure AWS Prize Services**
   - Set up Q Business application
   - Create Bedrock Agents
   - Test Nova inference

3. **Load Testing**
   - Run performance tests
   - Verify auto-scaling works
   - Test WebSocket under load

4. **Documentation**
   - Update runbooks with actual URLs
   - Document custom configurations
   - Create user guides

---

## Support

- **Issues**: https://github.com/rish2jain/Incident-Commander/issues
- **Docs**: See `/documentation` directory
- **CloudWatch Logs**: `/ecs/incident-commander`

---

**Deployment Complete!** 🚀

Your Incident Commander system is now running in AWS production.
