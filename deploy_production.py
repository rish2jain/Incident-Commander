#!/usr/bin/env python3
"""
Production Deployment Script for Autonomous Incident Commander

This script provisions all AWS resources including:
- Amazon Q Business application
- DynamoDB tables for event sourcing
- EventBridge for event-driven architecture
- IAM roles and permissions
- Bedrock agents and models
- API Gateway and Lambda functions
- Monitoring and observability

Usage:
    python deploy_production.py --environment production
    python deploy_production.py --environment staging --dry-run
"""

import os
import sys
import json
import time
import boto3
import argparse
from typing import Dict, List, Any
from botocore.exceptions import ClientError, NoCredentialsError


class ProductionDeployer:
    """Handles AWS resource provisioning for Incident Commander."""
    
    def __init__(self, environment: str = "production", region: str = "us-east-1"):
        self.environment = environment
        self.region = region
        self.account_id = None
        
        # Initialize AWS clients
        try:
            self.session = boto3.Session(region_name=region)
            self.sts = self.session.client('sts')
            self.account_id = self.sts.get_caller_identity()['Account']
            
            self.dynamodb = self.session.client('dynamodb')
            self.events = self.session.client('events')
            self.iam = self.session.client('iam')
            self.bedrock = self.session.client('bedrock')
            self.bedrock_agent = self.session.client('bedrock-agent')
            self.lambda_client = self.session.client('lambda')
            self.apigateway = self.session.client('apigatewayv2')
            self.cloudwatch = self.session.client('cloudwatch')
            self.logs = self.session.client('logs')
            
            print(f"✅ AWS clients initialized for account {self.account_id} in {region}")
            
        except NoCredentialsError:
            print("❌ AWS credentials not found. Please configure AWS CLI.")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Failed to initialize AWS clients: {e}")
            sys.exit(1)
    
    def create_dynamodb_tables(self) -> Dict[str, str]:
        """Create DynamoDB tables for event sourcing and state management."""
        print("\n🗄️  Creating DynamoDB tables...")
        
        tables = {
            'incident-events': {
                'AttributeDefinitions': [
                    {'AttributeName': 'incident_id', 'AttributeType': 'S'},
                    {'AttributeName': 'version', 'AttributeType': 'N'},
                    {'AttributeName': 'timestamp', 'AttributeType': 'S'}
                ],
                'KeySchema': [
                    {'AttributeName': 'incident_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'version', 'KeyType': 'RANGE'}
                ],
                'GlobalSecondaryIndexes': [
                    {
                        'IndexName': 'timestamp-index',
                        'KeySchema': [
                            {'AttributeName': 'timestamp', 'KeyType': 'HASH'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'}
                    }
                ]
            },
            'agent-state': {
                'AttributeDefinitions': [
                    {'AttributeName': 'agent_id', 'AttributeType': 'S'},
                    {'AttributeName': 'incident_id', 'AttributeType': 'S'}
                ],
                'KeySchema': [
                    {'AttributeName': 'agent_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'incident_id', 'KeyType': 'RANGE'}
                ]
            },
            'consensus-decisions': {
                'AttributeDefinitions': [
                    {'AttributeName': 'decision_id', 'AttributeType': 'S'},
                    {'AttributeName': 'created_at', 'AttributeType': 'S'}
                ],
                'KeySchema': [
                    {'AttributeName': 'decision_id', 'KeyType': 'HASH'}
                ],
                'GlobalSecondaryIndexes': [
                    {
                        'IndexName': 'created-at-index',
                        'KeySchema': [
                            {'AttributeName': 'created_at', 'KeyType': 'HASH'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'}
                    }
                ]
            }
        }
        
        created_tables = {}
        
        for table_name, config in tables.items():
            full_table_name = f"incident-commander-{table_name}-{self.environment}"
            
            try:
                # Check if table exists
                self.dynamodb.describe_table(TableName=full_table_name)
                print(f"  ✅ Table {full_table_name} already exists")
                created_tables[table_name] = full_table_name
                continue
                
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceNotFoundException':
                    raise
            
            # Create table
            create_params = {
                'TableName': full_table_name,
                'AttributeDefinitions': config['AttributeDefinitions'],
                'KeySchema': config['KeySchema'],
                'BillingMode': 'PAY_PER_REQUEST',
                'Tags': [
                    {'Key': 'Project', 'Value': 'IncidentCommander'},
                    {'Key': 'Environment', 'Value': self.environment}
                ]
            }
            
            if 'GlobalSecondaryIndexes' in config:
                create_params['GlobalSecondaryIndexes'] = config['GlobalSecondaryIndexes']
            
            self.dynamodb.create_table(**create_params)
            print(f"  ⏳ Creating table {full_table_name}...")
            
            # Wait for table to be active
            waiter = self.dynamodb.get_waiter('table_exists')
            waiter.wait(TableName=full_table_name, WaiterConfig={'Delay': 5, 'MaxAttempts': 60})
            
            print(f"  ✅ Table {full_table_name} created successfully")
            created_tables[table_name] = full_table_name
        
        return created_tables
    
    def create_eventbridge_rules(self) -> Dict[str, str]:
        """Create EventBridge rules for event-driven architecture."""
        print("\n📡 Creating EventBridge rules...")
        
        # Create custom event bus
        bus_name = f"incident-commander-{self.environment}"
        
        try:
            self.events.create_event_bus(Name=bus_name)
            print(f"  ✅ Event bus {bus_name} created")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceAlreadyExistsException':
                print(f"  ✅ Event bus {bus_name} already exists")
            else:
                raise
        
        # Define event rules
        rules = {
            'incident-detected': {
                'EventPattern': json.dumps({
                    'source': ['incident-commander'],
                    'detail-type': ['Incident Detected'],
                    'detail': {
                        'severity': ['HIGH', 'CRITICAL']
                    }
                }),
                'Description': 'Route high-severity incident detection events'
            },
            'agent-consensus': {
                'EventPattern': json.dumps({
                    'source': ['incident-commander'],
                    'detail-type': ['Agent Consensus'],
                    'detail': {
                        'consensus_reached': [True]
                    }
                }),
                'Description': 'Route successful agent consensus events'
            },
            'resolution-completed': {
                'EventPattern': json.dumps({
                    'source': ['incident-commander'],
                    'detail-type': ['Resolution Completed'],
                    'detail': {
                        'status': ['SUCCESS', 'PARTIAL_SUCCESS']
                    }
                }),
                'Description': 'Route successful resolution events'
            }
        }
        
        created_rules = {}
        
        for rule_name, config in rules.items():
            full_rule_name = f"incident-commander-{rule_name}-{self.environment}"
            
            try:
                self.events.put_rule(
                    Name=full_rule_name,
                    EventPattern=config['EventPattern'],
                    Description=config['Description'],
                    EventBusName=bus_name,
                    State='ENABLED'
                )
                print(f"  ✅ Rule {full_rule_name} created")
                created_rules[rule_name] = full_rule_name
                
            except ClientError as e:
                print(f"  ❌ Failed to create rule {full_rule_name}: {e}")
        
        return created_rules
    
    def create_iam_roles(self) -> Dict[str, str]:
        """Create IAM roles and policies for the system."""
        print("\n🔐 Creating IAM roles and policies...")
        
        # Trust policy for Lambda execution
        lambda_trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        # Trust policy for Bedrock agents
        bedrock_trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "bedrock.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        roles = {
            'incident-commander-lambda-role': {
                'trust_policy': lambda_trust_policy,
                'policies': [
                    'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
                    'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess',
                    'arn:aws:iam::aws:policy/AmazonEventBridgeFullAccess',
                    'arn:aws:iam::aws:policy/AmazonBedrockFullAccess'
                ]
            },
            'incident-commander-bedrock-role': {
                'trust_policy': bedrock_trust_policy,
                'policies': [
                    'arn:aws:iam::aws:policy/AmazonBedrockFullAccess',
                    'arn:aws:iam::aws:policy/AmazonDynamoDBReadOnlyAccess'
                ]
            }
        }
        
        created_roles = {}
        
        for role_name, config in roles.items():
            full_role_name = f"{role_name}-{self.environment}"
            
            try:
                # Check if role exists
                self.iam.get_role(RoleName=full_role_name)
                print(f"  ✅ Role {full_role_name} already exists")
                created_roles[role_name] = f"arn:aws:iam::{self.account_id}:role/{full_role_name}"
                continue
                
            except ClientError as e:
                if e.response['Error']['Code'] != 'NoSuchEntity':
                    raise
            
            # Create role
            self.iam.create_role(
                RoleName=full_role_name,
                AssumeRolePolicyDocument=json.dumps(config['trust_policy']),
                Description=f"IAM role for Incident Commander {role_name}",
                Tags=[
                    {'Key': 'Project', 'Value': 'IncidentCommander'},
                    {'Key': 'Environment', 'Value': self.environment}
                ]
            )
            
            # Attach policies
            for policy_arn in config['policies']:
                self.iam.attach_role_policy(
                    RoleName=full_role_name,
                    PolicyArn=policy_arn
                )
            
            print(f"  ✅ Role {full_role_name} created with policies")
            created_roles[role_name] = f"arn:aws:iam::{self.account_id}:role/{full_role_name}"
        
        return created_roles
    
    def create_amazon_q_application(self) -> str:
        """Create Amazon Q Business application for intelligent analysis."""
        print("\n🤖 Creating Amazon Q Business application...")
        
        # Note: Amazon Q Business requires specific setup through the console
        # This is a placeholder for the Q application creation
        app_name = f"incident-commander-q-{self.environment}"
        
        print(f"  ⚠️  Amazon Q Business application '{app_name}' requires manual setup")
        print("     Please create the application through the AWS Console:")
        print("     1. Go to Amazon Q Business console")
        print("     2. Create new application")
        print(f"     3. Name: {app_name}")
        print("     4. Configure data sources and permissions")
        
        return app_name
    
    def create_bedrock_agents(self, iam_roles: Dict[str, str]) -> Dict[str, str]:
        """Create Bedrock agents for the multi-agent system."""
        print("\n🧠 Creating Bedrock agents...")
        
        bedrock_role_arn = iam_roles.get('incident-commander-bedrock-role')
        if not bedrock_role_arn:
            print("  ❌ Bedrock IAM role not found")
            return {}
        
        agents = {
            'detection-agent': {
                'description': 'Detects incidents from monitoring data and alerts',
                'instruction': 'You are a detection agent responsible for identifying incidents from monitoring data, logs, and alerts. Analyze patterns and anomalies to detect potential issues.',
                'foundation_model': 'anthropic.claude-3-haiku-20240307-v1:0'
            },
            'diagnosis-agent': {
                'description': 'Diagnoses root causes of detected incidents',
                'instruction': 'You are a diagnosis agent responsible for analyzing incidents and determining root causes. Use logs, traces, and system data to identify the underlying issues.',
                'foundation_model': 'anthropic.claude-3-5-sonnet-20241022-v2:0'
            },
            'prediction-agent': {
                'description': 'Predicts incident impact and progression',
                'instruction': 'You are a prediction agent responsible for forecasting incident impact and progression. Analyze trends and patterns to predict future states.',
                'foundation_model': 'anthropic.claude-3-haiku-20240307-v1:0'
            },
            'resolution-agent': {
                'description': 'Executes automated resolution actions',
                'instruction': 'You are a resolution agent responsible for executing automated remediation actions. Plan and execute safe resolution strategies.',
                'foundation_model': 'anthropic.claude-3-5-sonnet-20241022-v2:0'
            }
        }
        
        created_agents = {}
        
        for agent_name, config in agents.items():
            full_agent_name = f"incident-commander-{agent_name}-{self.environment}"
            
            try:
                response = self.bedrock_agent.create_agent(
                    agentName=full_agent_name,
                    description=config['description'],
                    instruction=config['instruction'],
                    foundationModel=config['foundation_model'],
                    agentResourceRoleArn=bedrock_role_arn,
                    tags={
                        'Project': 'IncidentCommander',
                        'Environment': self.environment,
                        'AgentType': agent_name
                    }
                )
                
                agent_id = response['agent']['agentId']
                print(f"  ✅ Agent {full_agent_name} created with ID: {agent_id}")
                created_agents[agent_name] = agent_id
                
                # Prepare the agent
                self.bedrock_agent.prepare_agent(agentId=agent_id)
                print(f"  ⏳ Preparing agent {full_agent_name}...")
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'ConflictException':
                    print(f"  ✅ Agent {full_agent_name} already exists")
                else:
                    print(f"  ❌ Failed to create agent {full_agent_name}: {e}")
        
        return created_agents
    
    def create_api_gateway(self, lambda_role_arn: str) -> str:
        """Create API Gateway for the REST API."""
        print("\n🌐 Creating API Gateway...")
        
        api_name = f"incident-commander-api-{self.environment}"
        
        try:
            # Create HTTP API
            response = self.apigateway.create_api(
                Name=api_name,
                Description="Incident Commander REST API",
                ProtocolType='HTTP',
                Tags={
                    'Project': 'IncidentCommander',
                    'Environment': self.environment
                }
            )
            
            api_id = response['ApiId']
            api_endpoint = response['ApiEndpoint']
            
            print(f"  ✅ API Gateway created: {api_endpoint}")
            return api_endpoint
            
        except ClientError as e:
            print(f"  ❌ Failed to create API Gateway: {e}")
            return ""
    
    def create_cloudwatch_dashboard(self) -> str:
        """Create CloudWatch dashboard for monitoring."""
        print("\n📊 Creating CloudWatch dashboard...")
        
        dashboard_name = f"IncidentCommander-{self.environment}"
        
        dashboard_body = {
            "widgets": [
                {
                    "type": "metric",
                    "properties": {
                        "metrics": [
                            ["AWS/Lambda", "Invocations", "FunctionName", f"incident-commander-detection-{self.environment}"],
                            ["AWS/Lambda", "Duration", "FunctionName", f"incident-commander-detection-{self.environment}"],
                            ["AWS/Lambda", "Errors", "FunctionName", f"incident-commander-detection-{self.environment}"]
                        ],
                        "period": 300,
                        "stat": "Average",
                        "region": self.region,
                        "title": "Detection Agent Metrics"
                    }
                },
                {
                    "type": "metric",
                    "properties": {
                        "metrics": [
                            ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", f"incident-commander-incident-events-{self.environment}"],
                            ["AWS/DynamoDB", "ConsumedWriteCapacityUnits", "TableName", f"incident-commander-incident-events-{self.environment}"]
                        ],
                        "period": 300,
                        "stat": "Sum",
                        "region": self.region,
                        "title": "DynamoDB Metrics"
                    }
                }
            ]
        }
        
        try:
            self.cloudwatch.put_dashboard(
                DashboardName=dashboard_name,
                DashboardBody=json.dumps(dashboard_body)
            )
            print(f"  ✅ CloudWatch dashboard '{dashboard_name}' created")
            return dashboard_name
            
        except ClientError as e:
            print(f"  ❌ Failed to create CloudWatch dashboard: {e}")
            return ""
    
    def run_integration_tests(self, resources: Dict[str, Any]) -> bool:
        """Run integration tests against deployed AWS resources."""
        print("\n🧪 Running integration tests...")
        
        tests_passed = 0
        total_tests = 0
        
        # Test DynamoDB connectivity
        total_tests += 1
        try:
            table_name = resources['dynamodb_tables']['incident-events']
            self.dynamodb.describe_table(TableName=table_name)
            print(f"  ✅ DynamoDB table {table_name} accessible")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ DynamoDB test failed: {e}")
        
        # Test EventBridge connectivity
        total_tests += 1
        try:
            bus_name = f"incident-commander-{self.environment}"
            self.events.describe_event_bus(Name=bus_name)
            print(f"  ✅ EventBridge bus {bus_name} accessible")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ EventBridge test failed: {e}")
        
        # Test Bedrock model access
        total_tests += 1
        try:
            self.bedrock.list_foundation_models()
            print("  ✅ Bedrock models accessible")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ Bedrock test failed: {e}")
        
        success_rate = (tests_passed / total_tests) * 100
        print(f"\n📈 Integration tests: {tests_passed}/{total_tests} passed ({success_rate:.1f}%)")
        
        return tests_passed == total_tests
    
    def deploy(self, dry_run: bool = False) -> Dict[str, Any]:
        """Execute the complete deployment process."""
        print(f"🚀 Starting {'DRY RUN' if dry_run else 'PRODUCTION'} deployment...")
        print(f"   Environment: {self.environment}")
        print(f"   Region: {self.region}")
        print(f"   Account: {self.account_id}")
        
        if dry_run:
            print("\n⚠️  DRY RUN MODE - No resources will be created")
            return {}
        
        resources = {}
        
        try:
            # 1. Create IAM roles first (required by other services)
            resources['iam_roles'] = self.create_iam_roles()
            
            # 2. Create DynamoDB tables
            resources['dynamodb_tables'] = self.create_dynamodb_tables()
            
            # 3. Create EventBridge rules
            resources['eventbridge_rules'] = self.create_eventbridge_rules()
            
            # 4. Create Amazon Q application (manual step)
            resources['amazon_q_app'] = self.create_amazon_q_application()
            
            # 5. Create Bedrock agents
            resources['bedrock_agents'] = self.create_bedrock_agents(resources['iam_roles'])
            
            # 6. Create API Gateway
            resources['api_gateway'] = self.create_api_gateway(
                resources['iam_roles'].get('incident-commander-lambda-role', '')
            )
            
            # 7. Create CloudWatch dashboard
            resources['cloudwatch_dashboard'] = self.create_cloudwatch_dashboard()
            
            # 8. Run integration tests
            tests_passed = self.run_integration_tests(resources)
            
            print(f"\n🎉 Deployment {'COMPLETED' if tests_passed else 'COMPLETED WITH ISSUES'}")
            print(f"   Resources created: {len([r for r in resources.values() if r])}")
            print(f"   Integration tests: {'PASSED' if tests_passed else 'FAILED'}")
            
            # Save deployment info
            deployment_info = {
                'environment': self.environment,
                'region': self.region,
                'account_id': self.account_id,
                'timestamp': time.time(),
                'resources': resources,
                'tests_passed': tests_passed
            }
            
            with open(f'deployment-{self.environment}.json', 'w') as f:
                json.dump(deployment_info, f, indent=2, default=str)
            
            print(f"   Deployment info saved to: deployment-{self.environment}.json")
            
            return resources
            
        except Exception as e:
            print(f"\n❌ Deployment failed: {e}")
            raise


def main():
    """Main deployment script entry point."""
    parser = argparse.ArgumentParser(description='Deploy Incident Commander to AWS')
    parser.add_argument('--environment', '-e', default='production',
                       choices=['development', 'staging', 'production'],
                       help='Deployment environment')
    parser.add_argument('--region', '-r', default='us-east-1',
                       help='AWS region')
    parser.add_argument('--dry-run', action='store_true',
                       help='Perform a dry run without creating resources')
    
    args = parser.parse_args()
    
    # Validate AWS credentials
    try:
        session = boto3.Session()
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS credentials validated for account: {identity['Account']}")
    except Exception as e:
        print(f"❌ AWS credentials validation failed: {e}")
        sys.exit(1)
    
    # Initialize deployer and run deployment
    deployer = ProductionDeployer(args.environment, args.region)
    resources = deployer.deploy(args.dry_run)
    
    if not args.dry_run and resources:
        print("\n📋 Next Steps:")
        print("1. Complete Amazon Q Business application setup in AWS Console")
        print("2. Deploy Lambda functions using CDK or SAM")
        print("3. Configure monitoring alerts and thresholds")
        print("4. Run end-to-end system tests")
        print("5. Update DNS records if using custom domain")


if __name__ == '__main__':
    main()