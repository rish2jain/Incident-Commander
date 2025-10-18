"""
Compute Stack for Incident Commander
"""

from aws_cdk import (
    Stack,
    aws_ecs as ecs,
    aws_lambda as lambda_,
    aws_apigateway as apigateway,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
)
from constructs import Construct


class IncidentCommanderComputeStack(Stack):
    """Compute infrastructure stack."""

    def __init__(self, scope: Construct, construct_id: str, 
                 environment_name: str, env_config: dict,
                 vpc: ec2.Vpc, security_groups: dict,
                 task_role: iam.Role, execution_role: iam.Role,
                 lambda_role: iam.Role,
                 dynamodb_tables: dict, s3_buckets: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create ECS cluster
        self.ecs_cluster = ecs.Cluster(
            self, "IncidentCommanderCluster",
            vpc=vpc,
            cluster_name=f"incident-commander-{environment_name}"
        )

        # Create Lambda functions first
        self.lambda_functions = self._create_lambda_functions(
            environment_name, vpc, security_groups, lambda_role,
            dynamodb_tables, s3_buckets
        )

        # Create API Gateway with methods
        self.api_gateway = self._create_api_gateway(
            environment_name, self.lambda_functions
        )

    def _create_lambda_functions(self, environment_name: str, vpc: ec2.Vpc, 
                                security_groups: dict, lambda_role: iam.Role,
                                dynamodb_tables: dict, s3_buckets: dict) -> dict:
        """Create Lambda functions for the incident commander."""
        
        # Create Lambda security group if not provided
        lambda_sg = security_groups.get('lambda')
        if not lambda_sg:
            lambda_sg = ec2.SecurityGroup(
                self, "LambdaSecurityGroup",
                vpc=vpc,
                description="Security group for Lambda functions",
                allow_all_outbound=True
            )
        
        # Detection Agent Lambda
        detection_function = lambda_.Function(
            self, "DetectionAgentFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="detection_agent.handler",
            code=lambda_.Code.from_asset("src"),
            function_name=f"incident-commander-detection-agent-{environment_name}",
            role=lambda_role,
            vpc=vpc,
            security_groups=[lambda_sg],
            environment={
                'ENVIRONMENT': environment_name,
                'DYNAMODB_TABLE': f'incident-commander-events-{environment_name}',
                'S3_BUCKET': f'incident-commander-artifacts-{environment_name}'
            }
        )

        # Health Check Lambda
        health_function = lambda_.Function(
            self, "HealthCheckFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="health_check.handler",
            code=lambda_.Code.from_asset("src"),
            function_name=f"incident-commander-health-{environment_name}",
            role=lambda_role,
            environment={
                'ENVIRONMENT': environment_name
            }
        )

        return {
            'detection': detection_function,
            'health': health_function
        }

    def _create_api_gateway(self, environment_name: str, lambda_functions: dict) -> apigateway.RestApi:
        """Create API Gateway with proper methods."""
        
        api = apigateway.RestApi(
            self, "IncidentCommanderAPI",
            rest_api_name=f"incident-commander-{environment_name}",
            description="Incident Commander API",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "Authorization"]
            )
        )

        # Health endpoint
        health_resource = api.root.add_resource("health")
        health_integration = apigateway.LambdaIntegration(lambda_functions['health'])
        health_resource.add_method("GET", health_integration)

        # Demo endpoints
        demo_resource = api.root.add_resource("demo")
        
        # Demo status endpoint
        status_resource = demo_resource.add_resource("status")
        status_integration = apigateway.LambdaIntegration(lambda_functions['health'])
        status_resource.add_method("GET", status_integration)

        # Demo scenarios endpoint
        scenarios_resource = demo_resource.add_resource("scenarios")
        scenarios_integration = apigateway.LambdaIntegration(lambda_functions['health'])
        scenarios_resource.add_method("GET", scenarios_integration)

        # Incidents endpoint
        incidents_resource = api.root.add_resource("incidents")
        incidents_integration = apigateway.LambdaIntegration(lambda_functions['detection'])
        incidents_resource.add_method("POST", incidents_integration)

        return api