"""
Monitoring Stack for Incident Commander
"""

from aws_cdk import (
    Stack,
    aws_cloudwatch as cloudwatch,
    aws_ecs as ecs,
    aws_apigateway as apigateway,
    aws_dynamodb as dynamodb,
)
from constructs import Construct


class IncidentCommanderMonitoringStack(Stack):
    """Monitoring infrastructure stack."""

    def __init__(self, scope: Construct, construct_id: str, 
                 environment_name: str, env_config: dict,
                 ecs_cluster: ecs.Cluster, api_gateway: apigateway.RestApi,
                 lambda_functions: dict, dynamodb_tables: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create CloudWatch dashboard
        self.dashboard = cloudwatch.Dashboard(
            self, "IncidentCommanderDashboard",
            dashboard_name=f"incident-commander-{environment_name}"
        )