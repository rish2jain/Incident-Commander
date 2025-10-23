"""
AWS CDK Stack for Incident Commander Production Deployment

Provisions all infrastructure required for production deployment including:
- ECS Fargate for backend service
- Application Load Balancer with WebSocket support
- DynamoDB for persistence
- CloudWatch for monitoring
- Auto-scaling policies
"""

from aws_cdk import (
    Stack,
    Duration,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_elasticloadbalancingv2 as elbv2,
    aws_dynamodb as dynamodb,
    aws_logs as logs,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cw_actions,
    aws_sns as sns,
    aws_iam as iam,
    aws_s3 as s3,
    RemovalPolicy,
    CfnOutput,
)
from constructs import Construct


class IncidentCommanderStack(Stack):
    """
    Complete infrastructure stack for Incident Commander system.

    Provisions:
    - VPC with public/private subnets
    - ECS Fargate cluster
    - Application Load Balancer (WebSocket capable)
    - DynamoDB tables for persistence
    - CloudWatch dashboards and alarms
    - Auto-scaling policies
    - S3 for static assets
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ==========================================
        # VPC Configuration
        # ==========================================
        vpc = ec2.Vpc(
            self,
            "IncidentCommanderVPC",
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PUBLIC,
                    name="Public",
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    name="Private",
                    cidr_mask=24,
                ),
            ],
        )

        # ==========================================
        # DynamoDB Tables
        # ==========================================

        # Incidents table
        incidents_table = dynamodb.Table(
            self,
            "IncidentsTable",
            partition_key=dynamodb.Attribute(
                name="incident_id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # Business metrics table
        metrics_table = dynamodb.Table(
            self,
            "BusinessMetricsTable",
            partition_key=dynamodb.Attribute(
                name="metric_date", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="metric_timestamp", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # AWS service usage table
        aws_usage_table = dynamodb.Table(
            self,
            "AWSServiceUsageTable",
            partition_key=dynamodb.Attribute(
                name="service_name", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="usage_timestamp", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # ==========================================
        # S3 Buckets
        # ==========================================

        # Static assets bucket
        assets_bucket = s3.Bucket(
            self,
            "AssetsBucket",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.RETAIN,
            lifecycle_rules=[
                s3.LifecycleRule(
                    expiration=Duration.days(90),
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(30),
                        )
                    ],
                )
            ],
        )

        # ==========================================
        # ECS Cluster
        # ==========================================

        cluster = ecs.Cluster(
            self, "IncidentCommanderCluster", vpc=vpc, enable_fargate_capacity_providers=True
        )

        # ==========================================
        # Task Definition
        # ==========================================

        task_definition = ecs.FargateTaskDefinition(
            self,
            "TaskDef",
            memory_limit_mib=2048,
            cpu=1024,
        )

        # Grant permissions to access AWS services with least privilege
        task_definition.add_to_task_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                    "bedrock:GetFoundationModel",
                    "bedrock:ListFoundationModels",
                ],
                resources=[
                    f"arn:aws:bedrock:{self.region}::foundation-model/*",
                ],
            )
        )
        
        task_definition.add_to_task_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeAgent",
                    "bedrock:GetAgent",
                    "bedrock:ListAgents",
                ],
                resources=[
                    f"arn:aws:bedrock:{self.region}:{self.account}:agent/*",
                ],
            )
        )
        
        task_definition.add_to_task_role_policy(
            iam.PolicyStatement(
                actions=[
                    "qbusiness:ChatSync",
                    "qbusiness:GetApplication",
                ],
                resources=[
                    f"arn:aws:qbusiness:{self.region}:{self.account}:application/*",
                ],
            )
        )

        # Grant DynamoDB permissions
        incidents_table.grant_read_write_data(task_definition.task_role)
        metrics_table.grant_read_write_data(task_definition.task_role)
        aws_usage_table.grant_read_write_data(task_definition.task_role)
        
        # Grant S3 permissions for assets bucket
        assets_bucket.grant_read_write(task_definition.task_role)

        # Container definition
        container = task_definition.add_container(
            "FastAPIContainer",
            image=ecs.ContainerImage.from_registry("incident-commander:latest"),
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="incident-commander",
                log_retention=logs.RetentionDays.ONE_WEEK,
            ),
            environment={
                "INCIDENTS_TABLE": incidents_table.table_name,
                "METRICS_TABLE": metrics_table.table_name,
                "AWS_USAGE_TABLE": aws_usage_table.table_name,
                "AWS_REGION": self.region,
                "ASSETS_BUCKET": assets_bucket.bucket_name,
            },
            health_check=ecs.HealthCheck(
                command=["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
                interval=Duration.seconds(30),
                timeout=Duration.seconds(5),
                retries=3,
                start_period=Duration.seconds(60),
            ),
        )

        container.add_port_mappings(ecs.PortMapping(container_port=8000, protocol=ecs.Protocol.TCP))

        # ==========================================
        # Application Load Balancer
        # ==========================================

        # Load balanced Fargate service
        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "IncidentCommanderService",
            cluster=cluster,
            task_definition=task_definition,
            desired_count=2,
            public_load_balancer=True,
            listener_port=80,
            protocol=elbv2.ApplicationProtocol.HTTP,
            health_check_grace_period=Duration.seconds(60),
        )

        # Configure WebSocket support
        fargate_service.target_group.configure_health_check(
            path="/health",
            interval=Duration.seconds(30),
            timeout=Duration.seconds(5),
            healthy_threshold_count=2,
            unhealthy_threshold_count=3,
        )

        # Enable WebSocket connections
        fargate_service.target_group.set_attribute(
            key="deregistration_delay.timeout_seconds", value="30"
        )
        # Note: deregistration_delay.connection_termination.enabled is NLB-only, removed for ALB

        # Enable stickiness for WebSocket connections
        fargate_service.target_group.enable_cookie_stickiness(Duration.hours(1))

        # ==========================================
        # Auto Scaling
        # ==========================================

        scaling = fargate_service.service.auto_scale_task_count(max_capacity=10, min_capacity=2)

        # CPU-based scaling
        scaling.scale_on_cpu_utilization(
            "CpuScaling",
            target_utilization_percent=70,
            scale_in_cooldown=Duration.seconds(60),
            scale_out_cooldown=Duration.seconds(60),
        )

        # Request count based scaling
        scaling.scale_on_request_count(
            "RequestScaling",
            requests_per_target=1000,
            target_group=fargate_service.target_group,
            scale_in_cooldown=Duration.seconds(60),
            scale_out_cooldown=Duration.seconds(60),
        )

        # ==========================================
        # CloudWatch Dashboard
        # ==========================================

        dashboard = cloudwatch.Dashboard(self, "IncidentCommanderDashboard", dashboard_name="IncidentCommander")

        # Service metrics
        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Service Metrics",
                left=[
                    fargate_service.service.metric_cpu_utilization(),
                    fargate_service.service.metric_memory_utilization(),
                ],
            ),
            cloudwatch.GraphWidget(
                title="Request Metrics",
                left=[
                    fargate_service.load_balancer.metric_request_count(),
                    fargate_service.target_group.metric_target_response_time(),
                ],
            ),
        )

        # ==========================================
        # CloudWatch Alarms
        # ==========================================

        # SNS topic for alerts
        alarm_topic = sns.Topic(self, "AlarmTopic", display_name="Incident Commander Alerts")

        # High CPU alarm
        cpu_alarm = cloudwatch.Alarm(
            self,
            "HighCpuAlarm",
            metric=fargate_service.service.metric_cpu_utilization(),
            threshold=80,
            evaluation_periods=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
        )
        cpu_alarm.add_alarm_action(cw_actions.SnsAction(alarm_topic))

        # High memory alarm
        memory_alarm = cloudwatch.Alarm(
            self,
            "HighMemoryAlarm",
            metric=fargate_service.service.metric_memory_utilization(),
            threshold=80,
            evaluation_periods=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
        )
        memory_alarm.add_alarm_action(cw_actions.SnsAction(alarm_topic))

        # Target response time alarm
        response_time_alarm = cloudwatch.Alarm(
            self,
            "HighResponseTimeAlarm",
            metric=fargate_service.target_group.metric_target_response_time(),
            threshold=1.0,  # 1 second
            evaluation_periods=3,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
        )
        response_time_alarm.add_alarm_action(cw_actions.SnsAction(alarm_topic))

        # ==========================================
        # Outputs
        # ==========================================

        CfnOutput(self, "LoadBalancerDNS", value=fargate_service.load_balancer.load_balancer_dns_name)
        CfnOutput(self, "ClusterName", value=cluster.cluster_name)
        CfnOutput(self, "ServiceName", value=fargate_service.service.service_name)
        CfnOutput(self, "IncidentsTableName", value=incidents_table.table_name)
        CfnOutput(self, "MetricsTableName", value=metrics_table.table_name)
        CfnOutput(self, "AssetsBucketName", value=assets_bucket.bucket_name)
        CfnOutput(self, "AlarmTopicArn", value=alarm_topic.topic_arn)
