#!/usr/bin/env python3
"""
Core System Deployment for Autonomous Incident Commander

Simplified deployment focusing on essential AWS resources and validation.
This script deploys the core system without complex CDK infrastructure.

Usage:
    python deploy_core_system.py --environment production
"""

import os
import sys
import json
import time
import asyncio
import argparse
import subprocess
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add src to path for imports
sys.path.append('src')

from src.utils.logging import get_logger


logger = get_logger("core_deployment")


class CoreSystemDeployer:
    """Core system deployer focusing on essential AWS resources."""
    
    def __init__(self, environment: str = "production", region: str = "us-east-1"):
        self.environment = environment
        self.region = region
        self.account_id = None
        self.deployment_id = f"core-deploy-{int(time.time())}"
        
        # Get AWS account ID
        self._get_aws_account_id()
        
        logger.info(f"🚀 Starting core system deployment")
        logger.info(f"   Deployment ID: {self.deployment_id}")
        logger.info(f"   Environment: {environment}")
        logger.info(f"   Region: {region}")
        logger.info(f"   Account: {self.account_id}")
    
    def _get_aws_account_id(self):
        """Get AWS account ID."""
        try:
            result = subprocess.run(['aws', 'sts', 'get-caller-identity'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                identity = json.loads(result.stdout)
                self.account_id = identity['Account']
        except Exception as e:
            logger.error(f"Failed to get AWS account ID: {e}")
            self.account_id = "unknown"
    
    def create_dynamodb_tables(self) -> Dict[str, str]:
        """Create essential DynamoDB tables."""
        logger.info("📊 Creating DynamoDB tables...")
        
        tables = {}
        table_configs = [
            {
                'name': f'incident-commander-incidents-{self.environment}',
                'key': 'incident_id',
                'description': 'Main incidents table'
            },
            {
                'name': f'incident-commander-agent-states-{self.environment}',
                'key': 'agent_id',
                'description': 'Agent state tracking'
            },
            {
                'name': f'incident-commander-consensus-{self.environment}',
                'key': 'consensus_id',
                'description': 'Byzantine consensus decisions'
            }
        ]
        
        for config in table_configs:
            try:
                # Check if table exists
                check_result = subprocess.run([
                    'aws', 'dynamodb', 'describe-table',
                    '--table-name', config['name'],
                    '--region', self.region
                ], capture_output=True, text=True)
                
                if check_result.returncode == 0:
                    logger.info(f"✅ Table {config['name']} already exists")
                    tables[config['name']] = 'exists'
                    continue
                
                # Create table
                create_result = subprocess.run([
                    'aws', 'dynamodb', 'create-table',
                    '--table-name', config['name'],
                    '--attribute-definitions', f'AttributeName={config["key"]},AttributeType=S',
                    '--key-schema', f'AttributeName={config["key"]},KeyType=HASH',
                    '--billing-mode', 'PAY_PER_REQUEST',
                    '--region', self.region
                ], capture_output=True, text=True)
                
                if create_result.returncode == 0:
                    logger.info(f"✅ Created table {config['name']}")
                    tables[config['name']] = 'created'
                else:
                    logger.error(f"❌ Failed to create table {config['name']}: {create_result.stderr}")
                    tables[config['name']] = 'failed'
                    
            except Exception as e:
                logger.error(f"❌ Error creating table {config['name']}: {e}")
                tables[config['name']] = 'error'
        
        return tables
    
    def create_s3_buckets(self) -> Dict[str, str]:
        """Create essential S3 buckets."""
        logger.info("🪣 Creating S3 buckets...")
        
        buckets = {}
        bucket_configs = [
            {
                'name': f'incident-commander-{self.environment}-{self.account_id}',
                'description': 'Main data bucket'
            },
            {
                'name': f'incident-commander-logs-{self.environment}-{self.account_id}',
                'description': 'Logs bucket'
            }
        ]
        
        for config in bucket_configs:
            try:
                # Check if bucket exists
                check_result = subprocess.run([
                    'aws', 's3api', 'head-bucket',
                    '--bucket', config['name'],
                    '--region', self.region
                ], capture_output=True, text=True)
                
                if check_result.returncode == 0:
                    logger.info(f"✅ Bucket {config['name']} already exists")
                    buckets[config['name']] = 'exists'
                    continue
                
                # Create bucket
                if self.region == 'us-east-1':
                    create_result = subprocess.run([
                        'aws', 's3api', 'create-bucket',
                        '--bucket', config['name']
                    ], capture_output=True, text=True)
                else:
                    create_result = subprocess.run([
                        'aws', 's3api', 'create-bucket',
                        '--bucket', config['name'],
                        '--region', self.region,
                        '--create-bucket-configuration', f'LocationConstraint={self.region}'
                    ], capture_output=True, text=True)
                
                if create_result.returncode == 0:
                    logger.info(f"✅ Created bucket {config['name']}")
                    buckets[config['name']] = 'created'
                    
                    # Enable versioning
                    subprocess.run([
                        'aws', 's3api', 'put-bucket-versioning',
                        '--bucket', config['name'],
                        '--versioning-configuration', 'Status=Enabled'
                    ], capture_output=True)
                    
                else:
                    logger.error(f"❌ Failed to create bucket {config['name']}: {create_result.stderr}")
                    buckets[config['name']] = 'failed'
                    
            except Exception as e:
                logger.error(f"❌ Error creating bucket {config['name']}: {e}")
                buckets[config['name']] = 'error'
        
        return buckets
    
    def create_iam_roles(self) -> Dict[str, str]:
        """Create essential IAM roles."""
        logger.info("🔐 Creating IAM roles...")
        
        roles = {}
        
        # Lambda execution role
        lambda_role_name = f'IncidentCommander-Lambda-{self.environment}'
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
        
        lambda_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": "arn:aws:logs:*:*:*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "dynamodb:GetItem",
                        "dynamodb:PutItem",
                        "dynamodb:UpdateItem",
                        "dynamodb:DeleteItem",
                        "dynamodb:Query",
                        "dynamodb:Scan"
                    ],
                    "Resource": f"arn:aws:dynamodb:{self.region}:{self.account_id}:table/incident-commander-*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeModel",
                        "bedrock:InvokeModelWithResponseStream"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        try:
            # Check if role exists
            check_result = subprocess.run([
                'aws', 'iam', 'get-role',
                '--role-name', lambda_role_name
            ], capture_output=True, text=True)
            
            if check_result.returncode == 0:
                logger.info(f"✅ Role {lambda_role_name} already exists")
                roles[lambda_role_name] = 'exists'
            else:
                # Create role
                create_result = subprocess.run([
                    'aws', 'iam', 'create-role',
                    '--role-name', lambda_role_name,
                    '--assume-role-policy-document', json.dumps(lambda_trust_policy)
                ], capture_output=True, text=True)
                
                if create_result.returncode == 0:
                    logger.info(f"✅ Created role {lambda_role_name}")
                    
                    # Attach policy
                    policy_result = subprocess.run([
                        'aws', 'iam', 'put-role-policy',
                        '--role-name', lambda_role_name,
                        '--policy-name', 'IncidentCommanderPolicy',
                        '--policy-document', json.dumps(lambda_policy)
                    ], capture_output=True, text=True)
                    
                    if policy_result.returncode == 0:
                        roles[lambda_role_name] = 'created'
                    else:
                        roles[lambda_role_name] = 'policy_failed'
                else:
                    logger.error(f"❌ Failed to create role {lambda_role_name}: {create_result.stderr}")
                    roles[lambda_role_name] = 'failed'
                    
        except Exception as e:
            logger.error(f"❌ Error creating role {lambda_role_name}: {e}")
            roles[lambda_role_name] = 'error'
        
        return roles
    
    def create_cloudwatch_resources(self) -> Dict[str, str]:
        """Create CloudWatch log groups and dashboards."""
        logger.info("📊 Creating CloudWatch resources...")
        
        resources = {}
        
        # Create log groups
        log_groups = [
            f'/aws/lambda/incident-commander-{self.environment}',
            f'/incident-commander/{self.environment}/agents',
            f'/incident-commander/{self.environment}/api'
        ]
        
        for log_group in log_groups:
            try:
                # Check if log group exists
                check_result = subprocess.run([
                    'aws', 'logs', 'describe-log-groups',
                    '--log-group-name-prefix', log_group,
                    '--region', self.region
                ], capture_output=True, text=True)
                
                if check_result.returncode == 0:
                    response = json.loads(check_result.stdout)
                    if response.get('logGroups'):
                        logger.info(f"✅ Log group {log_group} already exists")
                        resources[log_group] = 'exists'
                        continue
                
                # Create log group
                create_result = subprocess.run([
                    'aws', 'logs', 'create-log-group',
                    '--log-group-name', log_group,
                    '--region', self.region
                ], capture_output=True, text=True)
                
                if create_result.returncode == 0:
                    logger.info(f"✅ Created log group {log_group}")
                    resources[log_group] = 'created'
                else:
                    logger.error(f"❌ Failed to create log group {log_group}: {create_result.stderr}")
                    resources[log_group] = 'failed'
                    
            except Exception as e:
                logger.error(f"❌ Error creating log group {log_group}: {e}")
                resources[log_group] = 'error'
        
        return resources
    
    def setup_environment_file(self):
        """Set up production environment file."""
        logger.info("⚙️ Setting up environment configuration...")
        
        # Copy production environment file if it doesn't exist
        if not os.path.exists('.env'):
            if os.path.exists('.env.production'):
                subprocess.run(['cp', '.env.production', '.env'], check=True)
                logger.info("✅ Copied .env.production to .env")
            else:
                subprocess.run(['cp', '.env.example', '.env'], check=True)
                logger.info("⚠️  Copied .env.example to .env")
        
        # Update with account ID
        if os.path.exists('.env') and self.account_id:
            with open('.env', 'r') as f:
                content = f.read()
            
            # Update AWS_ACCOUNT_ID
            if 'AWS_ACCOUNT_ID=' in content:
                content = content.replace('AWS_ACCOUNT_ID=', f'AWS_ACCOUNT_ID={self.account_id}')
            else:
                content += f'\nAWS_ACCOUNT_ID={self.account_id}\n'
            
            with open('.env', 'w') as f:
                f.write(content)
            
            logger.info(f"✅ Updated .env with account ID: {self.account_id}")
    
    def validate_bedrock_access(self) -> bool:
        """Validate Bedrock model access."""
        logger.info("🤖 Validating Bedrock access...")
        
        try:
            # Test Claude 4 Sonnet access
            test_result = subprocess.run([
                'aws', 'bedrock-runtime', 'invoke-model',
                '--model-id', 'anthropic.claude-sonnet-4-20250514-v1:0',
                '--body', json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 10,
                    "messages": [{"role": "user", "content": "Hello"}]
                }),
                '--region', self.region,
                '/tmp/bedrock_test_output.json'
            ], capture_output=True, text=True)
            
            if test_result.returncode == 0:
                logger.info("✅ Bedrock Claude 4 Sonnet access confirmed")
                return True
            else:
                logger.warning(f"⚠️  Bedrock access test failed: {test_result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Bedrock validation error: {e}")
            return False
    
    def deploy_core_system(self) -> Dict[str, Any]:
        """Deploy the core system components."""
        logger.info("\n🚀 Starting core system deployment...")
        
        deployment_results = {
            'start_time': datetime.utcnow().isoformat(),
            'environment': self.environment,
            'region': self.region,
            'account_id': self.account_id
        }
        
        # 1. Set up environment
        self.setup_environment_file()
        
        # 2. Create DynamoDB tables
        deployment_results['dynamodb_tables'] = self.create_dynamodb_tables()
        
        # 3. Create S3 buckets
        deployment_results['s3_buckets'] = self.create_s3_buckets()
        
        # 4. Create IAM roles
        deployment_results['iam_roles'] = self.create_iam_roles()
        
        # 5. Create CloudWatch resources
        deployment_results['cloudwatch_resources'] = self.create_cloudwatch_resources()
        
        # 6. Validate Bedrock access
        deployment_results['bedrock_access'] = self.validate_bedrock_access()
        
        deployment_results['end_time'] = datetime.utcnow().isoformat()
        deployment_results['status'] = 'completed'
        
        return deployment_results
    
    def generate_deployment_report(self, results: Dict[str, Any]) -> str:
        """Generate deployment report."""
        
        # Calculate duration
        start_time = datetime.fromisoformat(results['start_time'])
        end_time = datetime.fromisoformat(results['end_time'])
        duration = (end_time - start_time).total_seconds()
        
        report = f"""
# Core System Deployment Report

**Deployment ID:** {self.deployment_id}
**Environment:** {self.environment}
**Region:** {self.region}
**Account:** {self.account_id}
**Duration:** {duration:.1f} seconds
**Status:** {results['status']}

## AWS Resources Created

### DynamoDB Tables
"""
        
        for table, status in results.get('dynamodb_tables', {}).items():
            status_emoji = "✅" if status in ['created', 'exists'] else "❌"
            report += f"- {status_emoji} {table}: {status}\n"
        
        report += "\n### S3 Buckets\n"
        for bucket, status in results.get('s3_buckets', {}).items():
            status_emoji = "✅" if status in ['created', 'exists'] else "❌"
            report += f"- {status_emoji} {bucket}: {status}\n"
        
        report += "\n### IAM Roles\n"
        for role, status in results.get('iam_roles', {}).items():
            status_emoji = "✅" if status in ['created', 'exists'] else "❌"
            report += f"- {status_emoji} {role}: {status}\n"
        
        report += "\n### CloudWatch Resources\n"
        for resource, status in results.get('cloudwatch_resources', {}).items():
            status_emoji = "✅" if status in ['created', 'exists'] else "❌"
            report += f"- {status_emoji} {resource}: {status}\n"
        
        bedrock_status = "✅ Operational" if results.get('bedrock_access') else "❌ Access Issues"
        report += f"\n### Bedrock Access\n- {bedrock_status}\n"
        
        report += f"""

## Next Steps

1. **Start the Application**
   ```bash
   python src/main.py
   ```

2. **Start the Dashboard**
   ```bash
   cd dashboard && npm install && npm run dev
   ```

3. **Test the System**
   ```bash
   curl http://localhost:8000/health
   ```

4. **Run Integration Tests**
   ```bash
   python test_aws_integration.py --environment {self.environment}
   ```

## System Endpoints

- **API:** http://localhost:8000
- **Dashboard:** http://localhost:3000
- **Health Check:** http://localhost:8000/health
- **Metrics:** http://localhost:8000/metrics

---
*Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC*
"""
        
        # Save report
        report_file = f'core-deployment-report-{self.deployment_id}.md'
        with open(report_file, 'w') as f:
            f.write(report)
        
        # Save detailed results
        results_file = f'core-deployment-results-{self.deployment_id}.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"\n📄 Deployment report saved to: {report_file}")
        logger.info(f"📄 Detailed results saved to: {results_file}")
        
        return report_file


async def main():
    """Main deployment entry point."""
    parser = argparse.ArgumentParser(description='Deploy core Incident Commander system')
    parser.add_argument('--environment', '-e', default='production',
                       choices=['development', 'staging', 'production'],
                       help='Deployment environment')
    parser.add_argument('--region', '-r', default='us-east-1',
                       help='AWS region')
    
    args = parser.parse_args()
    
    # Initialize deployer
    deployer = CoreSystemDeployer(args.environment, args.region)
    
    try:
        # Deploy core system
        results = deployer.deploy_core_system()
        
        # Generate report
        report_file = deployer.generate_deployment_report(results)
        
        # Check for failures
        all_resources = {}
        all_resources.update(results.get('dynamodb_tables', {}))
        all_resources.update(results.get('s3_buckets', {}))
        all_resources.update(results.get('iam_roles', {}))
        all_resources.update(results.get('cloudwatch_resources', {}))
        
        failed_resources = [name for name, status in all_resources.items() 
                          if status in ['failed', 'error']]
        
        if failed_resources:
            logger.warning(f"\n⚠️  Deployment completed with some failures:")
            for resource in failed_resources:
                logger.warning(f"   - {resource}")
            logger.info(f"   Review the deployment report: {report_file}")
            sys.exit(1)
        else:
            logger.info(f"\n🎉 Core system deployment completed successfully!")
            logger.info(f"   All AWS resources are ready")
            logger.info(f"   Review the deployment report: {report_file}")
            logger.info(f"\n🚀 Ready to start the application:")
            logger.info(f"   python src/main.py")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"\n❌ Core deployment failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())