#!/usr/bin/env python3
"""
AWS CDK Infrastructure for Incident Commander

Deploys complete production infrastructure:
- ECS/Fargate for backend
- ALB with WebSocket support
- DynamoDB for incident storage
- S3 + CloudFront for dashboards
- CloudWatch for monitoring
- VPC with proper security groups

Usage:
    cdk deploy
"""

import os
import aws_cdk as cdk
from constructs import Construct
from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_elasticloadbalancingv2 as elbv2,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_dynamodb as dynamodb,
    aws_cloudwatch as cloudwatch,
    aws_logs as logs,
    aws_iam as iam,
    aws_certificatemanager as acm,
)


class IncidentCommanderStack(Stack):
    """Main infrastructure stack for Incident Commander"""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ===== VPC =====
        vpc = ec2.Vpc(
            self, "IncidentCommanderVPC",
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                ),
            ]
        )

        # ===== DynamoDB Tables =====

        # Incidents table
        incidents_table = dynamodb.Table(
            self, "IncidentsTable",
            partition_key=dynamodb.Attribute(
                name="incident_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True,
            removal_policy=cdk.RemovalPolicy.RETAIN
        )

        # Add GSI for status queries
        incidents_table.add_global_secondary_index(
            index_name="status-index",
            partition_key=dynamodb.Attribute(
                name="status",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            )
        )

        # Agent state table
        agent_state_table = dynamodb.Table(
            self, "AgentStateTable",
            partition_key=dynamodb.Attribute(
                name="agent_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=cdk.RemovalPolicy.RETAIN
        )

        # ===== ECS Cluster =====
        cluster = ecs.Cluster(
            self, "IncidentCommanderCluster",
            vpc=vpc,
            container_insights=True
        )

        # ===== Task Definition =====
        task_definition = ecs.FargateTaskDefinition(
            self, "BackendTaskDef",
            memory_limit_mib=2048,
            cpu=1024,
            runtime_platform=ecs.RuntimePlatform(
                cpu_architecture=ecs.CpuArchitecture.X86_64,
                operating_system_family=ecs.OperatingSystemFamily.LINUX
            )
        )

        # Grant table permissions
        incidents_table.grant_read_write_data(task_definition.task_role)
        agent_state_table.grant_read_write_data(task_definition.task_role)

        # Grant AWS AI service permissions
        task_definition.task_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonBedrockFullAccess")
        )
        task_definition.task_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonQFullAccess")
        )

        # Add CloudWatch Logs permissions
        task_definition.task_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                resources=["*"]
            )
        )

        # Container definition
        container = task_definition.add_container(
            "BackendContainer",
            image=ecs.ContainerImage.from_asset("../.."),  # Build from root directory
            environment={
                "AWS_REGION": self.region,
                "INCIDENTS_TABLE": incidents_table.table_name,
                "AGENT_STATE_TABLE": agent_state_table.table_name,
                "LOG_LEVEL": "INFO",
                "ENVIRONMENT": "production"
            },
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="incident-commander",
                log_retention=logs.RetentionDays.ONE_WEEK
            ),
            health_check=ecs.HealthCheck(
                command=["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
                interval=Duration.seconds(30),
                timeout=Duration.seconds(5),
                retries=3,
                start_period=Duration.seconds(60)
            )
        )

        container.add_port_mappings(
            ecs.PortMapping(
                container_port=8000,
                protocol=ecs.Protocol.TCP
            )
        )

        # ===== Application Load Balancer =====
        alb = elbv2.ApplicationLoadBalancer(
            self, "ALB",
            vpc=vpc,
            internet_facing=True
        )

        listener = alb.add_listener(
            "Listener",
            port=80,
            open=True
        )

        # ===== Fargate Service =====
        fargate_service = ecs.FargateService(
            self, "BackendService",
            cluster=cluster,
            task_definition=task_definition,
            desired_count=2,  # Start with 2 instances for HA
            assign_public_ip=False,  # Private subnets
            health_check_grace_period=Duration.seconds(60),
            circuit_breaker=ecs.DeploymentCircuitBreaker(rollback=True)
        )

        # Target group with WebSocket support
        target_group = listener.add_targets(
            "BackendTarget",
            port=8000,
            targets=[fargate_service],
            health_check=elbv2.HealthCheck(
                path="/health",
                interval=Duration.seconds(30),
                timeout=Duration.seconds(5),
                healthy_threshold_count=2,
                unhealthy_threshold_count=3
            ),
            deregistration_delay=Duration.seconds(30),
            stickiness_cookie_duration=Duration.hours(1),  # WebSocket sticky sessions
            protocol=elbv2.ApplicationProtocol.HTTP
        )

        # ===== Auto Scaling =====
        scaling = fargate_service.auto_scale_task_count(
            min_capacity=2,
            max_capacity=10
        )

        # Scale on CPU
        scaling.scale_on_cpu_utilization(
            "CpuScaling",
            target_utilization_percent=70,
            scale_in_cooldown=Duration.seconds(60),
            scale_out_cooldown=Duration.seconds(60)
        )

        # Scale on memory
        scaling.scale_on_memory_utilization(
            "MemoryScaling",
            target_utilization_percent=80,
            scale_in_cooldown=Duration.seconds(60),
            scale_out_cooldown=Duration.seconds(60)
        )

        # ===== S3 for Dashboards =====
        dashboard_bucket = s3.Bucket(
            self, "DashboardBucket",
            website_index_document="index.html",
            public_read_access=True,
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=False,
                block_public_policy=False,
                ignore_public_acls=False,
                restrict_public_buckets=False
            ),
            removal_policy=cdk.RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # ===== CloudFront Distribution =====
        distribution = cloudfront.Distribution(
            self, "DashboardDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(dashboard_bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD,
                cached_methods=cloudfront.CachedMethods.CACHE_GET_HEAD,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED
            ),
            default_root_object="index.html",
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.minutes(5)
                )
            ]
        )

        # ===== CloudWatch Dashboard =====
        cw_dashboard = cloudwatch.Dashboard(
            self, "OperationalDashboard",
            dashboard_name="IncidentCommander"
        )

        # Add widgets
        cw_dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Backend Service Health",
                left=[
                    fargate_service.metric_cpu_utilization(),
                    fargate_service.metric_memory_utilization()
                ]
            ),
            cloudwatch.GraphWidget(
                title="ALB Metrics",
                left=[
                    alb.metric_target_response_time(),
                    alb.metric_request_count()
                ]
            )
        )

        cw_dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="DynamoDB Metrics",
                left=[
                    incidents_table.metric_consumed_read_capacity_units(),
                    incidents_table.metric_consumed_write_capacity_units()
                ]
            )
        )

        # ===== CloudWatch Alarms =====

        # High CPU alarm
        cloudwatch.Alarm(
            self, "HighCpuAlarm",
            metric=fargate_service.metric_cpu_utilization(),
            threshold=90,
            evaluation_periods=2,
            datapoints_to_alarm=2,
            alarm_description="Backend CPU usage is too high",
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )

        # High error rate alarm
        cloudwatch.Alarm(
            self, "HighErrorRateAlarm",
            metric=alb.metric_http_code_target(
                code=elbv2.HttpCodeTarget.TARGET_5XX_COUNT
            ),
            threshold=10,
            evaluation_periods=2,
            datapoints_to_alarm=2,
            alarm_description="Too many 5xx errors from backend",
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )

        # ===== Outputs =====
        CfnOutput(
            self, "LoadBalancerDNS",
            value=alb.load_balancer_dns_name,
            description="Backend API URL"
        )

        CfnOutput(
            self, "DashboardURL",
            value=f"https://{distribution.distribution_domain_name}",
            description="Dashboard URL (CloudFront)"
        )

        CfnOutput(
            self, "DashboardBucketName",
            value=dashboard_bucket.bucket_name,
            description="S3 bucket for dashboard deployment"
        )

        CfnOutput(
            self, "IncidentsTableName",
            value=incidents_table.table_name,
            description="DynamoDB incidents table"
        )

        CfnOutput(
            self, "CloudWatchDashboard",
            value=f"https://console.aws.amazon.com/cloudwatch/home?region={self.region}#dashboards:name=IncidentCommander",
            description="CloudWatch operational dashboard"
        )


# App
app = cdk.App()
IncidentCommanderStack(
    app,
    "IncidentCommanderStack",
    env=cdk.Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'),
        region=os.getenv('CDK_DEFAULT_REGION', 'us-west-2')
    )
)

app.synth()
