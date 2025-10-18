"""
Networking Stack for Incident Commander
"""

from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
)
from constructs import Construct


class IncidentCommanderNetworkingStack(Stack):
    """Networking infrastructure stack."""

    def __init__(self, scope: Construct, construct_id: str, 
                 environment_name: str, env_config: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create VPC
        self.vpc = ec2.Vpc(
            self, "IncidentCommanderVPC",
            max_azs=2,
            nat_gateways=1 if environment_name == "development" else 2
        )