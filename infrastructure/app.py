#!/usr/bin/env python3
"""
AWS CDK Infrastructure as Code for Autonomous Incident Commander

This CDK application defines all AWS infrastructure required for the
Incident Commander system including compute, storage, networking,
monitoring, and security components.
"""

import os
from aws_cdk import (
    App, Environment, Tags,
    aws_ec2 as ec2,
    aws_iam as iam
)

from stacks.core_stack import IncidentCommanderCoreStack
from stacks.compute_stack import IncidentCommanderComputeStack
from stacks.storage_stack import IncidentCommanderStorageStack
from stacks.bedrock_stack import IncidentCommanderBedrockStack
from stacks.monitoring_stack import IncidentCommanderMonitoringStack
from stacks.security_stack import IncidentCommanderSecurityStack
from stacks.networking_stack import IncidentCommanderNetworkingStack
from stacks.dashboard_stack import IncidentCommanderDashboardStack


def get_environment_config():
    """Get environment-specific configuration."""
    env_name = os.getenv('ENVIRONMENT', 'development')
    
    configs = {
        'development': {
            'instance_types': ['t3.medium'],
            'min_capacity': 1,
            'max_capacity': 3,
            'enable_detailed_monitoring': False,
            'backup_retention_days': 7,
            'log_retention_days': 7
        },
        'staging': {
            'instance_types': ['t3.large', 'm5.large'],
            'min_capacity': 2,
            'max_capacity': 10,
            'enable_detailed_monitoring': True,
            'backup_retention_days': 30,
            'log_retention_days': 30
        },
        'production': {
            'instance_types': ['m5.xlarge', 'm5.2xlarge', 'c5.xlarge'],
            'min_capacity': 3,
            'max_capacity': 50,
            'enable_detailed_monitoring': True,
            'backup_retention_days': 2555,  # 7 years for compliance
            'log_retention_days': 90
        }
    }
    
    return configs.get(env_name, configs['development'])


def main():
    """Main CDK application entry point."""
    app = App()
    
    # Get environment configuration
    env_config = get_environment_config()
    environment_name = os.getenv('ENVIRONMENT', 'development')
    
    # Define AWS environment
    aws_env = Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'),
        region=os.getenv('CDK_DEFAULT_REGION', 'us-east-1')
    )
    
    # Common tags for all resources
    common_tags = {
        'Project': 'IncidentCommander',
        'Environment': environment_name,
        'Owner': 'DevOps',
        'CostCenter': 'Engineering',
        'Backup': 'Required' if environment_name == 'production' else 'Optional'
    }
    
    # Core infrastructure stack (VPC, IAM, KMS)
    core_stack = IncidentCommanderCoreStack(
        app, 
        f"IncidentCommanderCore-{environment_name}",
        env=aws_env,
        environment_name=environment_name,
        env_config=env_config
    )
    
    # Networking stack (VPC, subnets, security groups)
    networking_stack = IncidentCommanderNetworkingStack(
        app,
        f"IncidentCommanderNetworking-{environment_name}",
        env=aws_env,
        environment_name=environment_name,
        env_config=env_config
    )
    
    # Security stack (KMS, IAM roles, security groups)
    security_stack = IncidentCommanderSecurityStack(
        app,
        f"IncidentCommanderSecurity-{environment_name}",
        env=aws_env,
        environment_name=environment_name,
        env_config=env_config,
        vpc=networking_stack.vpc
    )
    
    # Storage stack (DynamoDB, S3, OpenSearch)
    storage_stack = IncidentCommanderStorageStack(
        app,
        f"IncidentCommanderStorage-{environment_name}",
        env=aws_env,
        environment_name=environment_name,
        env_config=env_config,
        vpc=networking_stack.vpc,
        kms_key=security_stack.kms_key
    )
    
    # Bedrock stack (AI models, agent configurations)
    bedrock_stack = IncidentCommanderBedrockStack(
        app,
        f"IncidentCommanderBedrock-{environment_name}",
        env=aws_env,
        environment_name=environment_name,
        env_config=env_config,
        execution_role=security_stack.bedrock_execution_role
    )
    
    # Compute stack (ECS, Lambda, API Gateway)
    compute_stack = IncidentCommanderComputeStack(
        app,
        f"IncidentCommanderCompute-{environment_name}",
        env=aws_env,
        environment_name=environment_name,
        env_config=env_config,
        vpc=networking_stack.vpc,
        security_groups=security_stack.security_groups,
        task_role=security_stack.ecs_task_role,
        execution_role=security_stack.ecs_execution_role,
        lambda_role=security_stack.lambda_execution_role,
        dynamodb_tables=storage_stack.dynamodb_tables,
        s3_buckets=storage_stack.s3_buckets
    )
    
    # Monitoring stack (CloudWatch, alarms, dashboards)
    monitoring_stack = IncidentCommanderMonitoringStack(
        app,
        f"IncidentCommanderMonitoring-{environment_name}",
        env=aws_env,
        environment_name=environment_name,
        env_config=env_config,
        ecs_cluster=compute_stack.ecs_cluster,
        api_gateway=compute_stack.api_gateway,
        lambda_functions=compute_stack.lambda_functions,
        dynamodb_tables=storage_stack.dynamodb_tables
    )

    # Dashboard stack (CloudFront + S3 for static dashboard hosting)
    dashboard_stack = IncidentCommanderDashboardStack(
        app,
        f"IncidentCommanderDashboard-{environment_name}",
        env=aws_env,
        environment_name=environment_name,
        env_config=env_config,
        kms_key=security_stack.kms_key
    )

    # Add dependencies between stacks
    networking_stack.add_dependency(core_stack)
    security_stack.add_dependency(networking_stack)
    storage_stack.add_dependency(security_stack)
    bedrock_stack.add_dependency(security_stack)
    compute_stack.add_dependency(storage_stack)
    compute_stack.add_dependency(bedrock_stack)
    monitoring_stack.add_dependency(compute_stack)
    dashboard_stack.add_dependency(security_stack)
    
    # Apply common tags to all stacks
    for stack in [core_stack, networking_stack, security_stack, storage_stack,
                  bedrock_stack, compute_stack, monitoring_stack, dashboard_stack]:
        for key, value in common_tags.items():
            Tags.of(stack).add(key, value)
    
    # Environment-specific tags
    if environment_name == 'production':
        Tags.of(app).add('Compliance', 'SOC2')
        Tags.of(app).add('DataClassification', 'Confidential')
        Tags.of(app).add('BackupRequired', 'True')
    
    app.synth()


if __name__ == '__main__':
    main()