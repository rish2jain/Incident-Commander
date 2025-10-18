#!/usr/bin/env python3
"""
AWS Deployment Script for Incident Commander

Deploys the Incident Commander system to AWS for hackathon demonstration.
Includes infrastructure setup, security configuration, and performance optimization.
"""

import boto3
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional


class AWSDeployer:
    """Handles AWS deployment for hackathon demo."""
    
    def __init__(self, environment: str = "demo"):
        self.environment = environment
        self.project_root = Path(__file__).parent
        self.region = "us-east-1"
        
        # Initialize AWS clients
        self.session = boto3.Session(region_name=self.region)
        self.cloudformation = self.session.client('cloudformation')
        self.s3 = self.session.client('s3')
        self.lambda_client = self.session.client('lambda')
        self.apigateway = self.session.client('apigatewayv2')
        
        # Deployment configuration
        self.stack_name = f"incident-commander-{environment}"
        self.bucket_name = f"incident-commander-{environment}-{int(time.time())}"
        
    def create_deployment_bucket(self) -> bool:
        """Create S3 bucket for deployment artifacts."""
        print(f"📦 Creating deployment bucket: {self.bucket_name}")
        
        try:
            if self.region == 'us-east-1':
                self.s3.create_bucket(Bucket=self.bucket_name)
            else:
                self.s3.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            
            # Enable versioning
            self.s3.put_bucket_versioning(
                Bucket=self.bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            
            print(f"✅ Deployment bucket created: {self.bucket_name}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create deployment bucket: {e}")
            return False
    
    def package_application(self) -> bool:
        """Package application for Lambda deployment."""
        print("📦 Packaging application...")
        
        try:
            # Create deployment package
            package_dir = self.project_root / "deployment_package"
            package_dir.mkdir(exist_ok=True)
            
            # Copy source code
            subprocess.run([
                "cp", "-r", "src/", str(package_dir / "src")
            ], check=True)
            
            subprocess.run([
                "cp", "-r", "agents/", str(package_dir / "agents")
            ], check=True)
            
            # Install dependencies
            subprocess.run([
                sys.executable, "-m", "pip", "install", 
                "-r", "requirements.txt",
                "-t", str(package_dir)
            ], check=True)
            
            # Create ZIP package
            subprocess.run([
                "zip", "-r", "deployment_package.zip", "."
            ], cwd=package_dir, check=True)
            
            print("✅ Application packaged successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to package application: {e}")
            return False
    
    def upload_package(self) -> Optional[str]:
        """Upload deployment package to S3."""
        print("⬆️  Uploading deployment package...")
        
        try:
            package_path = self.project_root / "deployment_package" / "deployment_package.zip"
            
            if not package_path.exists():
                print("❌ Deployment package not found")
                return None
            
            key = f"packages/incident-commander-{int(time.time())}.zip"
            
            self.s3.upload_file(
                str(package_path),
                self.bucket_name,
                key
            )
            
            s3_url = f"s3://{self.bucket_name}/{key}"
            print(f"✅ Package uploaded: {s3_url}")
            return s3_url
            
        except Exception as e:
            print(f"❌ Failed to upload package: {e}")
            return None
    
    def create_cloudformation_template(self) -> Dict[str, Any]:
        """Create CloudFormation template for infrastructure."""
        template = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Description": "Incident Commander - Autonomous Multi-Agent System",
            "Parameters": {
                "Environment": {
                    "Type": "String",
                    "Default": self.environment,
                    "Description": "Deployment environment"
                },
                "DeploymentPackageS3Key": {
                    "Type": "String",
                    "Description": "S3 key for deployment package"
                }
            },
            "Resources": {
                # Lambda Execution Role
                "LambdaExecutionRole": {
                    "Type": "AWS::IAM::Role",
                    "Properties": {
                        "AssumeRolePolicyDocument": {
                            "Version": "2012-10-17",
                            "Statement": [{
                                "Effect": "Allow",
                                "Principal": {"Service": "lambda.amazonaws.com"},
                                "Action": "sts:AssumeRole"
                            }]
                        },
                        "ManagedPolicyArns": [
                            "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
                            "arn:aws:iam::aws:policy/AmazonBedrockFullAccess",
                            "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
                        ],
                        "Policies": [{
                            "PolicyName": "IncidentCommanderPolicy",
                            "PolicyDocument": {
                                "Version": "2012-10-17",
                                "Statement": [{
                                    "Effect": "Allow",
                                    "Action": [
                                        "secretsmanager:GetSecretValue",
                                        "kms:Decrypt",
                                        "logs:CreateLogGroup",
                                        "logs:CreateLogStream",
                                        "logs:PutLogEvents"
                                    ],
                                    "Resource": "*"
                                }]
                            }
                        }]
                    }
                },
                
                # Main Lambda Function
                "IncidentCommanderFunction": {
                    "Type": "AWS::Lambda::Function",
                    "Properties": {
                        "FunctionName": f"incident-commander-{self.environment}",
                        "Runtime": "python3.11",
                        "Handler": "src.lambda_handler.handler",
                        "Role": {"Fn::GetAtt": ["LambdaExecutionRole", "Arn"]},
                        "Code": {
                            "S3Bucket": self.bucket_name,
                            "S3Key": {"Ref": "DeploymentPackageS3Key"}
                        },
                        "Timeout": 300,
                        "MemorySize": 1024,
                        "Environment": {
                            "Variables": {
                                "ENVIRONMENT": {"Ref": "Environment"},
                                "AWS_REGION": self.region
                            }
                        }
                    }
                },
                
                # API Gateway
                "ApiGateway": {
                    "Type": "AWS::ApiGatewayV2::Api",
                    "Properties": {
                        "Name": f"incident-commander-{self.environment}",
                        "ProtocolType": "HTTP",
                        "CorsConfiguration": {
                            "AllowOrigins": ["*"],
                            "AllowMethods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                            "AllowHeaders": ["Content-Type", "Authorization"]
                        }
                    }
                },
                
                # Lambda Integration
                "LambdaIntegration": {
                    "Type": "AWS::ApiGatewayV2::Integration",
                    "Properties": {
                        "ApiId": {"Ref": "ApiGateway"},
                        "IntegrationType": "AWS_PROXY",
                        "IntegrationUri": {
                            "Fn::Sub": "arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${IncidentCommanderFunction.Arn}/invocations"
                        },
                        "PayloadFormatVersion": "2.0"
                    }
                },
                
                # API Routes
                "DefaultRoute": {
                    "Type": "AWS::ApiGatewayV2::Route",
                    "Properties": {
                        "ApiId": {"Ref": "ApiGateway"},
                        "RouteKey": "$default",
                        "Target": {
                            "Fn::Sub": "integrations/${LambdaIntegration}"
                        }
                    }
                },
                
                # API Stage
                "ApiStage": {
                    "Type": "AWS::ApiGatewayV2::Stage",
                    "Properties": {
                        "ApiId": {"Ref": "ApiGateway"},
                        "StageName": "$default",
                        "AutoDeploy": True
                    }
                },
                
                # Lambda Permission
                "LambdaPermission": {
                    "Type": "AWS::Lambda::Permission",
                    "Properties": {
                        "FunctionName": {"Ref": "IncidentCommanderFunction"},
                        "Action": "lambda:InvokeFunction",
                        "Principal": "apigateway.amazonaws.com",
                        "SourceArn": {
                            "Fn::Sub": "arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${ApiGateway}/*/*"
                        }
                    }
                },
                
                # DynamoDB Tables
                "IncidentTable": {
                    "Type": "AWS::DynamoDB::Table",
                    "Properties": {
                        "TableName": f"incident-commander-incidents-{self.environment}",
                        "BillingMode": "PAY_PER_REQUEST",
                        "AttributeDefinitions": [
                            {"AttributeName": "incident_id", "AttributeType": "S"},
                            {"AttributeName": "created_at", "AttributeType": "S"}
                        ],
                        "KeySchema": [
                            {"AttributeName": "incident_id", "KeyType": "HASH"}
                        ],
                        "GlobalSecondaryIndexes": [{
                            "IndexName": "CreatedAtIndex",
                            "KeySchema": [
                                {"AttributeName": "created_at", "KeyType": "HASH"}
                            ],
                            "Projection": {"ProjectionType": "ALL"}
                        }]
                    }
                },
                
                # CloudWatch Dashboard
                "MonitoringDashboard": {
                    "Type": "AWS::CloudWatch::Dashboard",
                    "Properties": {
                        "DashboardName": f"IncidentCommander-{self.environment}",
                        "DashboardBody": json.dumps({
                            "widgets": [
                                {
                                    "type": "metric",
                                    "properties": {
                                        "metrics": [
                                            ["AWS/Lambda", "Duration", "FunctionName", f"incident-commander-{self.environment}"],
                                            ["AWS/Lambda", "Invocations", "FunctionName", f"incident-commander-{self.environment}"],
                                            ["AWS/Lambda", "Errors", "FunctionName", f"incident-commander-{self.environment}"]
                                        ],
                                        "period": 300,
                                        "stat": "Average",
                                        "region": self.region,
                                        "title": "Lambda Performance"
                                    }
                                }
                            ]
                        })
                    }
                }
            },
            
            "Outputs": {
                "ApiEndpoint": {
                    "Description": "API Gateway endpoint URL",
                    "Value": {
                        "Fn::Sub": "https://${ApiGateway}.execute-api.${AWS::Region}.amazonaws.com"
                    }
                },
                "LambdaFunction": {
                    "Description": "Lambda function ARN",
                    "Value": {"Fn::GetAtt": ["IncidentCommanderFunction", "Arn"]}
                },
                "DashboardURL": {
                    "Description": "CloudWatch Dashboard URL",
                    "Value": {
                        "Fn::Sub": "https://console.aws.amazon.com/cloudwatch/home?region=${AWS::Region}#dashboards:name=IncidentCommander-${Environment}"
                    }
                }
            }
        }
        
        return template
    
    def deploy_infrastructure(self, package_s3_key: str) -> bool:
        """Deploy infrastructure using CloudFormation."""
        print("🏗️  Deploying infrastructure...")
        
        try:
            template = self.create_cloudformation_template()
            
            # Deploy stack
            self.cloudformation.create_stack(
                StackName=self.stack_name,
                TemplateBody=json.dumps(template),
                Parameters=[
                    {
                        'ParameterKey': 'Environment',
                        'ParameterValue': self.environment
                    },
                    {
                        'ParameterKey': 'DeploymentPackageS3Key',
                        'ParameterValue': package_s3_key.split('/')[-1]
                    }
                ],
                Capabilities=['CAPABILITY_IAM']
            )
            
            # Wait for deployment to complete
            print("⏳ Waiting for deployment to complete...")
            waiter = self.cloudformation.get_waiter('stack_create_complete')
            waiter.wait(StackName=self.stack_name, WaiterConfig={'Delay': 30, 'MaxAttempts': 60})
            
            print("✅ Infrastructure deployed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to deploy infrastructure: {e}")
            return False
    
    def get_deployment_outputs(self) -> Dict[str, str]:
        """Get deployment outputs."""
        try:
            response = self.cloudformation.describe_stacks(StackName=self.stack_name)
            stack = response['Stacks'][0]
            
            outputs = {}
            for output in stack.get('Outputs', []):
                outputs[output['OutputKey']] = output['OutputValue']
            
            return outputs
            
        except Exception as e:
            print(f"❌ Failed to get deployment outputs: {e}")
            return {}
    
    def create_lambda_handler(self) -> bool:
        """Create Lambda handler for FastAPI."""
        print("⚡ Creating Lambda handler...")
        
        try:
            handler_code = '''"""
Lambda handler for Incident Commander FastAPI application.
"""

from mangum import Mangum
from src.main import app

# Create Lambda handler
handler = Mangum(app, lifespan="off")
'''
            
            handler_path = self.project_root / "src" / "lambda_handler.py"
            with open(handler_path, 'w') as f:
                f.write(handler_code)
            
            print("✅ Lambda handler created")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create Lambda handler: {e}")
            return False
    
    def update_requirements(self) -> bool:
        """Update requirements for Lambda deployment."""
        print("📋 Updating requirements for Lambda...")
        
        try:
            # Add Lambda-specific dependencies
            lambda_requirements = [
                "mangum>=0.17.0",  # ASGI adapter for Lambda
                "boto3>=1.34.0",   # AWS SDK
                "botocore>=1.34.0"
            ]
            
            requirements_path = self.project_root / "requirements.txt"
            
            # Read existing requirements
            with open(requirements_path, 'r') as f:
                existing_requirements = f.read()
            
            # Add Lambda requirements if not present
            updated_requirements = existing_requirements
            for req in lambda_requirements:
                if req.split('>=')[0] not in existing_requirements:
                    updated_requirements += f"\n{req}"
            
            # Write updated requirements
            with open(requirements_path, 'w') as f:
                f.write(updated_requirements)
            
            print("✅ Requirements updated for Lambda")
            return True
            
        except Exception as e:
            print(f"❌ Failed to update requirements: {e}")
            return False
    
    def deploy_to_aws(self) -> Dict[str, Any]:
        """Run complete AWS deployment."""
        print("🚀 Starting AWS Deployment for Hackathon Demo")
        print("=" * 60)
        
        deployment_steps = [
            ("Create Lambda Handler", self.create_lambda_handler),
            ("Update Requirements", self.update_requirements),
            ("Create Deployment Bucket", self.create_deployment_bucket),
            ("Package Application", self.package_application),
        ]
        
        # Execute deployment steps
        for step_name, step_func in deployment_steps:
            print(f"\n📋 {step_name}")
            print("-" * 40)
            
            if not step_func():
                return {
                    'success': False,
                    'failed_step': step_name,
                    'message': f"Deployment failed at: {step_name}"
                }
        
        # Upload package and deploy
        package_s3_key = self.upload_package()
        if not package_s3_key:
            return {
                'success': False,
                'failed_step': 'Upload Package',
                'message': 'Failed to upload deployment package'
            }
        
        if not self.deploy_infrastructure(package_s3_key.split('/')[-1]):
            return {
                'success': False,
                'failed_step': 'Deploy Infrastructure',
                'message': 'Failed to deploy infrastructure'
            }
        
        # Get deployment outputs
        outputs = self.get_deployment_outputs()
        
        print("\n" + "=" * 60)
        print("🎉 AWS DEPLOYMENT COMPLETE!")
        print("=" * 60)
        
        if outputs:
            print("📊 Deployment Information:")
            for key, value in outputs.items():
                print(f"  {key}: {value}")
        
        print(f"\n🌐 API Endpoint: {outputs.get('ApiEndpoint', 'Not available')}")
        print(f"📊 Dashboard: {outputs.get('DashboardURL', 'Not available')}")
        print(f"⚡ Lambda Function: {outputs.get('LambdaFunction', 'Not available')}")
        
        return {
            'success': True,
            'outputs': outputs,
            'stack_name': self.stack_name,
            'bucket_name': self.bucket_name,
            'message': 'Deployment completed successfully'
        }


def main():
    """Deploy to AWS for hackathon demo."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deploy Incident Commander to AWS')
    parser.add_argument('--environment', default='demo', help='Deployment environment')
    args = parser.parse_args()
    
    deployer = AWSDeployer(environment=args.environment)
    
    try:
        result = deployer.deploy_to_aws()
        
        if result['success']:
            print("\n🚀 HACKATHON DEPLOYMENT READY!")
            print("✅ System deployed and ready for demo")
            sys.exit(0)
        else:
            print(f"\n❌ DEPLOYMENT FAILED: {result['message']}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Deployment cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Deployment error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()