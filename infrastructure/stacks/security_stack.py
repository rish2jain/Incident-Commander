"""
Security Stack for Incident Commander
"""

from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_kms as kms,
    aws_ec2 as ec2,
)
from constructs import Construct


class IncidentCommanderSecurityStack(Stack):
    """Security infrastructure stack."""

    def __init__(self, scope: Construct, construct_id: str, 
                 environment_name: str, env_config: dict, vpc: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.vpc = vpc

        # Create KMS key
        self.kms_key = kms.Key(
            self, "SecurityKey",
            description="Security key for Incident Commander"
        )

        # Create security groups
        self.security_groups = self._create_security_groups()

        # Create IAM roles
        self.ecs_task_role = iam.Role(
            self, "ECSTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com")
        )

        self.ecs_execution_role = iam.Role(
            self, "ECSExecutionRole", 
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy")
            ]
        )

        self.bedrock_execution_role = iam.Role(
            self, "BedrockExecutionRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com")
        )

        # Lambda execution role
        self.lambda_execution_role = iam.Role(
            self, "LambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )

        # Add S3 permissions to ECS task role
        self.ecs_task_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject",
                    "s3:ListBucket"
                ],
                resources=[
                    f"arn:aws:s3:::incident-commander-artifacts-{environment_name}",
                    f"arn:aws:s3:::incident-commander-artifacts-{environment_name}/*"
                ]
            )
        )

        # Add AWS AI services permissions to ECS task role
        self.ecs_task_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:*",
                    "bedrock-runtime:*",
                    "bedrock-agent:*",
                    "bedrock-agent-runtime:*",
                    "qbusiness:*",
                    "comprehend:*",
                    "textract:*"
                ],
                resources=["*"]
            )
        )

        # Add CloudTrail permissions for audit logging
        self.ecs_task_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "cloudtrail:LookupEvents",
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                    "logs:DescribeLogGroups",
                    "logs:DescribeLogStreams"
                ],
                resources=["*"]
            )
        )

    def _create_security_groups(self) -> dict:
        """Create security groups for different services."""
        
        # ECS security group
        ecs_sg = ec2.SecurityGroup(
            self, "ECSSecurityGroup",
            vpc=self.vpc,
            description="Security group for ECS tasks",
            allow_all_outbound=True
        )
        
        # Lambda security group
        lambda_sg = ec2.SecurityGroup(
            self, "LambdaSecurityGroup", 
            vpc=self.vpc,
            description="Security group for Lambda functions",
            allow_all_outbound=True
        )
        
        # Database security group
        db_sg = ec2.SecurityGroup(
            self, "DatabaseSecurityGroup",
            vpc=self.vpc,
            description="Security group for databases",
            allow_all_outbound=False
        )
        
        # Allow ECS and Lambda to access database
        db_sg.add_ingress_rule(
            peer=ecs_sg,
            connection=ec2.Port.tcp(443),
            description="HTTPS from ECS"
        )
        
        db_sg.add_ingress_rule(
            peer=lambda_sg,
            connection=ec2.Port.tcp(443),
            description="HTTPS from Lambda"
        )
        
        return {
            'ecs': ecs_sg,
            'lambda': lambda_sg,
            'database': db_sg
        }