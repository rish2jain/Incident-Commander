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

        # Create CloudWatch alarms for critical metrics
        self._create_alarms(environment_name, ecs_cluster, api_gateway, lambda_functions, dynamodb_tables)

    def _create_alarms(self, environment_name: str, ecs_cluster: ecs.Cluster, 
                      api_gateway: apigateway.RestApi, lambda_functions: dict, 
                      dynamodb_tables: dict):
        """Create CloudWatch alarms for monitoring."""
        
        # API Gateway error rate alarm
        api_error_alarm = cloudwatch.Alarm(
            self, "APIErrorRateAlarm",
            alarm_name=f"incident-commander-api-errors-{environment_name}",
            metric=api_gateway.metric_client_error(),
            threshold=10,
            evaluation_periods=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
        )

        # Lambda function error alarms
        for function_name, function in lambda_functions.items():
            cloudwatch.Alarm(
                self, f"{function_name}ErrorAlarm",
                alarm_name=f"incident-commander-{function_name}-errors-{environment_name}",
                metric=function.metric_errors(),
                threshold=5,
                evaluation_periods=2,
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
            )

        # DynamoDB throttling alarms
        for table_name, table in dynamodb_tables.items():
            cloudwatch.Alarm(
                self, f"{table_name}ThrottleAlarm",
                alarm_name=f"incident-commander-{table_name}-throttles-{environment_name}",
                metric=table.metric_throttled_requests(),
                threshold=1,
                evaluation_periods=1,
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD
            )