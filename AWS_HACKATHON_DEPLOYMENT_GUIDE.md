# 🚀 AWS Hackathon Deployment Guide

## Autonomous Incident Commander - Complete AWS Setup

**Target**: AWS Bedrock AgentCore Hackathon Submission  
**Deployment Time**: 45-60 minutes  
**Prerequisites**: AWS Account with appropriate permissions

---

## 📋 Pre-Deployment Requirements

### 1. AWS Account Setup

- AWS Account with admin permissions (or sufficient IAM permissions)
- AWS CLI installed and configured
- AWS CDK v2 installed (`npm install -g aws-cdk`)
- Docker installed and running
- Python 3.11+ installed

### 2. Required AWS Services Access

Ensure your AWS account has access to:

- ✅ **AWS Bedrock** (with Claude-3 and GPT-4 model access)
- ✅ **AWS Lambda** (for agent execution)
- ✅ **Amazon DynamoDB** (for state management)
- ✅ **Amazon ECS** (for container orchestration)
- ✅ **Amazon API Gateway** (for REST APIs)
- ✅ **Amazon CloudWatch** (for monitoring)
- ✅ **AWS Secrets Manager** (for secure configuration)
- ✅ **Amazon VPC** (for networking)

### 3. Service Quotas Check

```bash
# Check critical service quotas
aws service-quotas get-service-quota --service-code lambda --quota-code L-B99A9384
aws service-quotas get-service-quota --service-code dynamodb --quota-code L-F98FE922
aws service-quotas get-service-quota --service-code bedrock --quota-code L-3E8C9B8A
```

---

## 🛠️ Step 1: Environment Setup (5 minutes)

### Clone and Setup Project

```bash
# Clone the repository (if not already done)
git clone <your-repo-url>
cd incident-commander

# Create Python virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configure AWS Credentials

```bash
# Configure AWS CLI (if not already done)
aws configure

# Verify AWS access
aws sts get-caller-identity
aws bedrock list-foundation-models --region us-east-1
```

### Environment Variables Setup

```bash
# Copy environment template
cp .env.example .env.hackathon

# Edit .env.hackathon with your AWS settings
cat > .env.hackathon << EOF
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ENVIRONMENT=hackathon

# Application Configuration
APP_NAME=incident-commander-hackathon
LOG_LEVEL=INFO
DEBUG=false

# Bedrock Configuration
BEDROCK_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Demo Configuration
DEMO_MODE=true
ENABLE_INTERACTIVE_DEMO=true
HACKATHON_FEATURES=true
EOF

# Load environment variables
export $(cat .env.hackathon | xargs)
```

---

## 🏗️ Step 2: Local Development Setup (10 minutes)

### Start Local Services

```bash
# Start LocalStack and supporting services
docker-compose up -d

# Wait for services to be ready
echo "Waiting for LocalStack to be ready..."
sleep 30

# Verify services are running
docker-compose ps
curl -s http://localhost:4566/health | jq '.'
```

### Initialize Local AWS Resources

```bash
# Create DynamoDB tables
awslocal dynamodb create-table \
  --table-name incident-commander-events \
  --attribute-definitions \
    AttributeName=incident_id,AttributeType=S \
    AttributeName=timestamp,AttributeType=S \
  --key-schema \
    AttributeName=incident_id,KeyType=HASH \
    AttributeName=timestamp,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST

awslocal dynamodb create-table \
  --table-name incident-commander-state \
  --attribute-definitions AttributeName=incident_id,AttributeType=S \
  --key-schema AttributeName=incident_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# Create S3 buckets
awslocal s3 mb s3://incident-commander-artifacts
awslocal s3 mb s3://incident-commander-logs

# Create Kinesis streams
awslocal kinesis create-stream \
  --stream-name incident-events \
  --shard-count 1

# Verify resources
awslocal dynamodb list-tables
awslocal s3 ls
awslocal kinesis list-streams
```

### Test Local Application

```bash
# Start the application locally
uvicorn src.main:app --reload --port 8000 &
APP_PID=$!

# Wait for startup
sleep 10

# Test health endpoint
curl http://localhost:8000/health

# Test demo endpoints
curl http://localhost:8000/demo/scenarios
curl http://localhost:8000/demo/status

# Stop local app for now
kill $APP_PID
```

---

## ☁️ Step 3: AWS Infrastructure Deployment (20 minutes)

### CDK Bootstrap (First Time Only)

```bash
# Bootstrap CDK in your AWS account
cd infrastructure
cdk bootstrap aws://$AWS_ACCOUNT_ID/$AWS_REGION

# Install CDK dependencies
pip install -r requirements.txt
```

### Deploy Core Infrastructure

```bash
# Set deployment environment
export ENVIRONMENT=hackathon
export CDK_DEFAULT_ACCOUNT=$AWS_ACCOUNT_ID
export CDK_DEFAULT_REGION=$AWS_REGION

# Synthesize CloudFormation templates
cdk synth --all

# Deploy infrastructure stacks in order
echo "🚀 Deploying Core Stack..."
cdk deploy IncidentCommanderCoreStack --require-approval never

echo "🚀 Deploying Networking Stack..."
cdk deploy IncidentCommanderNetworkingStack --require-approval never

echo "🚀 Deploying Security Stack..."
cdk deploy IncidentCommanderSecurityStack --require-approval never

echo "🚀 Deploying Storage Stack..."
cdk deploy IncidentCommanderStorageStack --require-approval never

echo "🚀 Deploying Bedrock Stack..."
cdk deploy IncidentCommanderBedrockStack --require-approval never

echo "🚀 Deploying Compute Stack..."
cdk deploy IncidentCommanderComputeStack --require-approval never

echo "🚀 Deploying Monitoring Stack..."
cdk deploy IncidentCommanderMonitoringStack --require-approval never
```

### Verify Infrastructure Deployment

```bash
# Check CloudFormation stacks
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
  --query 'StackSummaries[?contains(StackName, `IncidentCommander`)].{Name:StackName,Status:StackStatus}'

# Get API Gateway URL
API_URL=$(aws cloudformation describe-stacks \
  --stack-name IncidentCommanderComputeStack \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
  --output text)

echo "API Gateway URL: $API_URL"

# Get ECS Cluster name
ECS_CLUSTER=$(aws cloudformation describe-stacks \
  --stack-name IncidentCommanderComputeStack \
  --query 'Stacks[0].Outputs[?OutputKey==`EcsClusterName`].OutputValue' \
  --output text)

echo "ECS Cluster: $ECS_CLUSTER"
```

---

## 🤖 Step 4: Bedrock Agent Configuration (10 minutes)

### Create Bedrock Agents

```bash
# Create Detection Agent
DETECTION_AGENT_ID=$(aws bedrock-agent create-agent \
  --agent-name "incident-detection-agent" \
  --description "Detects infrastructure incidents using monitoring data" \
  --foundation-model "anthropic.claude-3-sonnet-20240229-v1:0" \
  --instruction "You are an expert incident detection agent. Analyze monitoring data to identify potential infrastructure issues." \
  --query 'agent.agentId' --output text)

echo "Detection Agent ID: $DETECTION_AGENT_ID"

# Create Diagnosis Agent
DIAGNOSIS_AGENT_ID=$(aws bedrock-agent create-agent \
  --agent-name "incident-diagnosis-agent" \
  --description "Performs root cause analysis for detected incidents" \
  --foundation-model "anthropic.claude-3-sonnet-20240229-v1:0" \
  --instruction "You are an expert incident diagnosis agent. Perform thorough root cause analysis using logs, metrics, and traces." \
  --query 'agent.agentId' --output text)

echo "Diagnosis Agent ID: $DIAGNOSIS_AGENT_ID"

# Create Resolution Agent
RESOLUTION_AGENT_ID=$(aws bedrock-agent create-agent \
  --agent-name "incident-resolution-agent" \
  --description "Executes automated remediation actions for incidents" \
  --foundation-model "anthropic.claude-3-sonnet-20240229-v1:0" \
  --instruction "You are an expert incident resolution agent. Execute safe, automated remediation actions based on diagnosis results." \
  --query 'agent.agentId' --output text)

echo "Resolution Agent ID: $RESOLUTION_AGENT_ID"

# Store agent IDs in Secrets Manager
aws secretsmanager create-secret \
  --name "incident-commander/bedrock-agents" \
  --description "Bedrock Agent IDs for Incident Commander" \
  --secret-string "{
    \"detection_agent_id\": \"$DETECTION_AGENT_ID\",
    \"diagnosis_agent_id\": \"$DIAGNOSIS_AGENT_ID\",
    \"resolution_agent_id\": \"$RESOLUTION_AGENT_ID\"
  }"
```

### Configure Agent Knowledge Bases

```bash
# Create knowledge base for incident patterns
KNOWLEDGE_BASE_ID=$(aws bedrock-agent create-knowledge-base \
  --name "incident-patterns-kb" \
  --description "Knowledge base of common incident patterns and solutions" \
  --role-arn "arn:aws:iam::$AWS_ACCOUNT_ID:role/IncidentCommanderBedrockRole" \
  --knowledge-base-configuration '{
    "type": "VECTOR",
    "vectorKnowledgeBaseConfiguration": {
      "embeddingModelArn": "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v1"
    }
  }' \
  --storage-configuration '{
    "type": "OPENSEARCH_SERVERLESS",
    "opensearchServerlessConfiguration": {
      "collectionArn": "arn:aws:aoss:us-east-1:'$AWS_ACCOUNT_ID':collection/incident-patterns",
      "vectorIndexName": "incident-patterns-index",
      "fieldMapping": {
        "vectorField": "vector",
        "textField": "text",
        "metadataField": "metadata"
      }
    }
  }' \
  --query 'knowledgeBase.knowledgeBaseId' --output text)

echo "Knowledge Base ID: $KNOWLEDGE_BASE_ID"
```

---

## 🚀 Step 5: Application Deployment (10 minutes)

### Build and Deploy Container Images

```bash
# Build application container
docker build -t incident-commander:hackathon .

# Tag for ECR
ECR_REPO=$(aws cloudformation describe-stacks \
  --stack-name IncidentCommanderComputeStack \
  --query 'Stacks[0].Outputs[?OutputKey==`EcrRepositoryUri`].OutputValue' \
  --output text)

docker tag incident-commander:hackathon $ECR_REPO:latest

# Login to ECR and push
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $ECR_REPO

docker push $ECR_REPO:latest
```

### Deploy ECS Service

```bash
# Update ECS service with new image
aws ecs update-service \
  --cluster $ECS_CLUSTER \
  --service incident-commander-service \
  --force-new-deployment

# Wait for deployment to complete
aws ecs wait services-stable \
  --cluster $ECS_CLUSTER \
  --services incident-commander-service

# Check service status
aws ecs describe-services \
  --cluster $ECS_CLUSTER \
  --services incident-commander-service \
  --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount}'
```

### Deploy Lambda Functions

```bash
# Package and deploy agent functions
cd ../src

# Create deployment package
zip -r agent-functions.zip . -x "*.pyc" "__pycache__/*" "tests/*"

# Deploy detection agent function
aws lambda update-function-code \
  --function-name incident-commander-detection-agent \
  --zip-file fileb://agent-functions.zip

# Deploy diagnosis agent function
aws lambda update-function-code \
  --function-name incident-commander-diagnosis-agent \
  --zip-file fileb://agent-functions.zip

# Deploy resolution agent function
aws lambda update-function-code \
  --function-name incident-commander-resolution-agent \
  --zip-file fileb://agent-functions.zip

cd ..
```

---

## 🔧 Step 6: Configuration and Testing (5 minutes)

### Configure Application Settings

```bash
# Update application configuration in Secrets Manager
aws secretsmanager update-secret \
  --secret-id "incident-commander/app-config" \
  --secret-string "{
    \"api_gateway_url\": \"$API_URL\",
    \"ecs_cluster\": \"$ECS_CLUSTER\",
    \"knowledge_base_id\": \"$KNOWLEDGE_BASE_ID\",
    \"environment\": \"hackathon\",
    \"demo_mode\": true,
    \"hackathon_features\": true
  }"

# Update Bedrock agent configurations
aws secretsmanager update-secret \
  --secret-id "incident-commander/bedrock-agents" \
  --secret-string "{
    \"detection_agent_id\": \"$DETECTION_AGENT_ID\",
    \"diagnosis_agent_id\": \"$DIAGNOSIS_AGENT_ID\",
    \"resolution_agent_id\": \"$RESOLUTION_AGENT_ID\",
    \"knowledge_base_id\": \"$KNOWLEDGE_BASE_ID\"
  }"
```

### Test Deployment

```bash
# Test API Gateway health endpoint
curl $API_URL/health

# Test demo endpoints
curl $API_URL/demo/scenarios
curl $API_URL/demo/status

# Test WebSocket connection (if available)
curl -i -N -H "Connection: Upgrade" \
     -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Key: test" \
     -H "Sec-WebSocket-Version: 13" \
     $API_URL/ws

# Test agent invocation
curl -X POST $API_URL/incidents/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "incident_type": "high_cpu_usage",
    "severity": "medium",
    "description": "CPU usage above 80% for 5 minutes",
    "source": "cloudwatch"
  }'
```

---

## 📊 Step 7: Monitoring and Validation (5 minutes)

### Setup CloudWatch Dashboards

```bash
# Create custom dashboard
aws cloudwatch put-dashboard \
  --dashboard-name "IncidentCommanderHackathon" \
  --dashboard-body '{
    "widgets": [
      {
        "type": "metric",
        "properties": {
          "metrics": [
            ["AWS/Lambda", "Duration", "FunctionName", "incident-commander-detection-agent"],
            ["AWS/Lambda", "Invocations", "FunctionName", "incident-commander-detection-agent"],
            ["AWS/Lambda", "Errors", "FunctionName", "incident-commander-detection-agent"]
          ],
          "period": 300,
          "stat": "Average",
          "region": "'$AWS_REGION'",
          "title": "Detection Agent Metrics"
        }
      },
      {
        "type": "metric",
        "properties": {
          "metrics": [
            ["AWS/ECS", "CPUUtilization", "ServiceName", "incident-commander-service"],
            ["AWS/ECS", "MemoryUtilization", "ServiceName", "incident-commander-service"]
          ],
          "period": 300,
          "stat": "Average",
          "region": "'$AWS_REGION'",
          "title": "ECS Service Metrics"
        }
      }
    ]
  }'

# Set up alarms
aws cloudwatch put-metric-alarm \
  --alarm-name "IncidentCommander-HighErrorRate" \
  --alarm-description "High error rate in incident commander" \
  --metric-name "Errors" \
  --namespace "AWS/Lambda" \
  --statistic "Sum" \
  --period 300 \
  --threshold 5 \
  --comparison-operator "GreaterThanThreshold" \
  --dimensions Name=FunctionName,Value=incident-commander-detection-agent \
  --evaluation-periods 2
```

### Validate Deployment

```bash
# Run comprehensive validation
python validate_infrastructure.py --environment hackathon

# Check all services are healthy
echo "🔍 Validating deployment..."

# Check ECS service
ECS_STATUS=$(aws ecs describe-services \
  --cluster $ECS_CLUSTER \
  --services incident-commander-service \
  --query 'services[0].status' --output text)

echo "ECS Service Status: $ECS_STATUS"

# Check Lambda functions
for func in detection-agent diagnosis-agent resolution-agent; do
  STATUS=$(aws lambda get-function \
    --function-name incident-commander-$func \
    --query 'Configuration.State' --output text)
  echo "Lambda $func Status: $STATUS"
done

# Check API Gateway
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $API_URL/health)
echo "API Gateway Status: $API_STATUS"

# Check DynamoDB tables
aws dynamodb describe-table --table-name incident-commander-events \
  --query 'Table.TableStatus' --output text

aws dynamodb describe-table --table-name incident-commander-state \
  --query 'Table.TableStatus' --output text
```

---

## 🎯 Step 8: Hackathon Demo Preparation (5 minutes)

### Load Demo Data

```bash
# Load sample incident scenarios
python scripts/load_demo_data.py --environment hackathon

# Create sample incidents for demonstration
curl -X POST $API_URL/demo/scenarios/load \
  -H "Content-Type: application/json" \
  -d '{
    "scenarios": [
      "high_cpu_usage",
      "database_connection_failure",
      "memory_leak_detection",
      "network_latency_spike",
      "disk_space_critical"
    ]
  }'
```

### Test Interactive Demo

```bash
# Test interactive demo features
curl $API_URL/demo/interactive/start

# Test real-time updates
curl $API_URL/demo/websocket/test

# Verify dashboard accessibility
curl $API_URL/dashboard/

# Test judge demo endpoints
curl $API_URL/demo/judge/scenarios
curl $API_URL/demo/judge/metrics
```

### Final Validation

```bash
# Run end-to-end test
python tests/test_hackathon_demo.py

# Generate deployment report
python scripts/generate_deployment_report.py --output hackathon_deployment_report.json

# Verify all hackathon requirements
python scripts/verify_hackathon_requirements.py
```

---

## 📋 Deployment Summary

### 🎉 Deployment Complete!

Your Autonomous Incident Commander is now deployed and ready for the hackathon demo:

#### 🔗 **Access URLs**

- **API Gateway**: `$API_URL`
- **Health Check**: `$API_URL/health`
- **Demo Dashboard**: `$API_URL/dashboard/`
- **Interactive Demo**: `$API_URL/demo/interactive/`
- **Judge Demo**: `$API_URL/demo/judge/`

#### 🤖 **Bedrock Agents**

- **Detection Agent**: `$DETECTION_AGENT_ID`
- **Diagnosis Agent**: `$DIAGNOSIS_AGENT_ID`
- **Resolution Agent**: `$RESOLUTION_AGENT_ID`
- **Knowledge Base**: `$KNOWLEDGE_BASE_ID`

#### 📊 **Monitoring**

- **CloudWatch Dashboard**: [IncidentCommanderHackathon](https://console.aws.amazon.com/cloudwatch/home?region=$AWS_REGION#dashboards:name=IncidentCommanderHackathon)
- **ECS Cluster**: `$ECS_CLUSTER`
- **Lambda Functions**: 3 agent functions deployed

#### 🔒 **Security**

- All secrets stored in AWS Secrets Manager
- VPC isolation enabled
- IAM roles with least privilege
- Encryption at rest and in transit

---

## 🚨 Troubleshooting

### Common Issues and Solutions

#### 1. CDK Deployment Fails

```bash
# Check CDK version
cdk --version

# Clean and retry
cdk destroy --all
cdk bootstrap aws://$AWS_ACCOUNT_ID/$AWS_REGION
cdk deploy --all --require-approval never
```

#### 2. Bedrock Access Issues

```bash
# Check Bedrock model access
aws bedrock list-foundation-models --region us-east-1

# Request model access if needed (may take time)
aws bedrock put-model-invocation-logging-configuration \
  --logging-config '{
    "cloudWatchConfig": {
      "logGroupName": "/aws/bedrock/modelinvocations",
      "roleArn": "arn:aws:iam::'$AWS_ACCOUNT_ID':role/service-role/AmazonBedrockExecutionRoleForKnowledgeBase"
    }
  }'
```

#### 3. ECS Service Won't Start

```bash
# Check ECS service events
aws ecs describe-services \
  --cluster $ECS_CLUSTER \
  --services incident-commander-service \
  --query 'services[0].events[0:5]'

# Check task definition
aws ecs describe-task-definition \
  --task-definition incident-commander-task \
  --query 'taskDefinition.containerDefinitions[0].{Image:image,Memory:memory,Cpu:cpu}'
```

#### 4. API Gateway 5xx Errors

```bash
# Check Lambda function logs
aws logs tail /aws/lambda/incident-commander-detection-agent --follow

# Check ECS service logs
aws logs tail /aws/ecs/incident-commander --follow
```

#### 5. WebSocket Connection Issues

```bash
# Check API Gateway WebSocket logs
aws logs describe-log-groups --log-group-name-prefix "/aws/apigateway"

# Test WebSocket endpoint
wscat -c wss://$(echo $API_URL | sed 's/https:/wss:/')/ws
```

---

## 📞 Support and Next Steps

### For Hackathon Demo

1. **Test all demo scenarios** before presentation
2. **Prepare backup data** in case of issues
3. **Have monitoring dashboards ready** to show real-time metrics
4. **Practice the demo flow** to ensure smooth presentation

### Post-Hackathon

1. **Scale down resources** to minimize costs
2. **Export demo data** for future presentations
3. **Document lessons learned** for production deployment
4. **Plan production architecture** based on feedback

### Emergency Contacts

- **AWS Support**: Use AWS Support Center for critical issues
- **Bedrock Issues**: Check AWS Bedrock documentation and limits
- **CDK Issues**: Refer to AWS CDK troubleshooting guide

---

## 💰 Cost Management

### Estimated Hackathon Costs

- **Bedrock Model Invocations**: $50-100
- **Lambda Executions**: $10-20
- **ECS Tasks**: $20-40
- **DynamoDB**: $5-15
- **API Gateway**: $5-10
- **CloudWatch**: $5-10
- **Total Estimated**: $95-195 for hackathon period

### Cost Optimization

```bash
# Set up billing alerts
aws budgets create-budget \
  --account-id $AWS_ACCOUNT_ID \
  --budget '{
    "BudgetName": "IncidentCommanderHackathon",
    "BudgetLimit": {
      "Amount": "200",
      "Unit": "USD"
    },
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST"
  }'

# Clean up after hackathon
# cdk destroy --all  # Uncomment when ready to clean up
```

---

**🎉 Your Autonomous Incident Commander is now live on AWS and ready to impress the hackathon judges!**

**Good luck with your presentation! 🚀**
