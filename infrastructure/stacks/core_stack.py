"""
Core Infrastructure Stack for Incident Commander

Provides foundational AWS resources including IAM roles, KMS keys,
and basic security configurations.
"""

from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_kms as kms,
    RemovalPolicy,
    Duration
)
from constructs import Construct


class IncidentCommanderCoreStack(Stack):
    """Core infrastructure stack with foundational resources."""

    def __init__(self, scope: Construct, construct_id: str, 
                 environment_name: str, env_config: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.environment_name = environment_name
        self.env_config = env_config

        # Create KMS key for encryption
        self.kms_key = kms.Key(
            self, "IncidentCommanderKey",
            description=f"KMS key for Incident Commander {environment_name}",
            enable_key_rotation=True,
            removal_policy=RemovalPolicy.RETAIN if environment_name == "production" else RemovalPolicy.DESTROY
        )

        # Create basic IAM role for services
        self.service_role = iam.Role(
            self, "IncidentCommanderServiceRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy")
            ]
        )

        # Grant KMS permissions to service role
        self.kms_key.grant_encrypt_decrypt(self.service_role)