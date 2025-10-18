"""
Bedrock Stack for Incident Commander
"""

from aws_cdk import (
    Stack,
    aws_iam as iam,
)
from constructs import Construct


class IncidentCommanderBedrockStack(Stack):
    """Bedrock AI infrastructure stack."""

    def __init__(self, scope: Construct, construct_id: str, 
                 environment_name: str, env_config: dict,
                 execution_role: iam.Role, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.execution_role = execution_role

        # Bedrock model access policies
        bedrock_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            resources=["*"]
        )

        self.execution_role.add_to_policy(bedrock_policy)