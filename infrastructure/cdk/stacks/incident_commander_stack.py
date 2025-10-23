"""
AWS CDK Stack for Incident Commander Production Infrastructure.

This stack deploys:
- ECS/Fargate services for distributed agents
- EventBridge event bus for event-driven architecture
- DynamoDB tables for state management
- CloudWatch dashboards and alarms
- VPC and networking
- IAM roles and policies
"""

from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    CfnOutput,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_dynamodb as dynamodb,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_logs as logs,
    aws_cloudwatch as cloudwatch,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    aws_secretsmanager as secretsmanager,
    aws_kms as kms,
)
from constructs import Construct


class IncidentCommanderStack(Stack):
    """Main infrastructure stack for Incident Commander."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Tags for all resources
        self.tags.set_tag("Project", "IncidentCommander")
        self.tags.set_tag("Environment", "production")
        self.tags.set_tag("ManagedBy", "CDK")

        # Create networking
        self.vpc = self._create_vpc()

        # Create KMS key for encryption
        self.kms_key = self._create_kms_key()

        # Create DynamoDB tables
        self.incidents_table = self._create_incidents_table()
        self.consensus_table = self._create_consensus_table()
        self.metrics_table = self._create_metrics_table()

        # Create EventBridge bus
        self.event_bus = self._create_event_bus()

        # Create SNS topics
        self.alert_topic = self._create_alert_topic()

        # Create ECS cluster
        self.ecs_cluster = self._create_ecs_cluster()

        # Create agent services
        self._create_agent_services()

        # Create monitoring
        self._create_monitoring()

        # Create outputs
        self._create_outputs()

    def _create_vpc(self) -> ec2.Vpc:
        """Create VPC for ECS services."""
        vpc = ec2.Vpc(
            self,
            "IncidentCommanderVPC",
            max_azs=3,
            nat_gateways=2,
            cidr="10.0.0.0/16",
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="Isolated",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,
                ),
            ],
            enable_dns_hostnames=True,
            enable_dns_support=True,
        )

        # VPC Flow Logs
        log_group = logs.LogGroup(
            self,
            "VPCFlowLogsGroup",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY,
        )

        ec2.FlowLog(
            self,
            "VPCFlowLog",
            resource_type=ec2.FlowLogResourceType.from_vpc(vpc),
            destination=ec2.FlowLogDestination.to_cloud_watch_logs(log_group),
        )

        return vpc

    def _create_kms_key(self) -> kms.Key:
        """Create KMS key for encryption."""
        key = kms.Key(
            self,
            "IncidentCommanderKey",
            description="Encryption key for Incident Commander resources",
            enable_key_rotation=True,
            removal_policy=RemovalPolicy.RETAIN,
        )

        key.add_alias("alias/incident-commander")

        return key

    def _create_incidents_table(self) -> dynamodb.Table:
        """Create DynamoDB table for incidents."""
        table = dynamodb.Table(
            self,
            "IncidentsTable",
            partition_key=dynamodb.Attribute(
                name="incident_id",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
        )

        # Global Secondary Index for status queries
        table.add_global_secondary_index(
            index_name="StatusIndex",
            partition_key=dynamodb.Attribute(
                name="status",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING,
            ),
        )

        # GSI for severity queries
        table.add_global_secondary_index(
            index_name="SeverityIndex",
            partition_key=dynamodb.Attribute(
                name="severity",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING,
            ),
        )

        return table

    def _create_consensus_table(self) -> dynamodb.Table:
        """Create DynamoDB table for consensus history."""
        table = dynamodb.Table(
            self,
            "ConsensusTable",
            partition_key=dynamodb.Attribute(
                name="proposal_id",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="sequence_number",
                type=dynamodb.AttributeType.NUMBER,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN,
            time_to_live_attribute="ttl",
        )

        return table

    def _create_metrics_table(self) -> dynamodb.Table:
        """Create DynamoDB table for metrics."""
        table = dynamodb.Table(
            self,
            "MetricsTable",
            partition_key=dynamodb.Attribute(
                name="metric_name",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            removal_policy=RemovalPolicy.DESTROY,
            time_to_live_attribute="ttl",
        )

        return table

    def _create_event_bus(self) -> events.EventBus:
        """Create EventBridge event bus."""
        bus = events.EventBus(
            self,
            "IncidentCommanderEventBus",
            event_bus_name="incident-commander",
        )

        # Create rules for different event types
        self._create_event_rules(bus)

        return bus

    def _create_event_rules(self, bus: events.EventBus) -> None:
        """Create EventBridge rules."""
        # Rule for incident detection events
        detection_rule = events.Rule(
            self,
            "IncidentDetectionRule",
            event_bus=bus,
            event_pattern=events.EventPattern(
                source=["incident-commander.orchestrator"],
                detail_type=["IncidentDetected"],
            ),
            description="Route incident detection events",
        )

        # Rule for consensus events
        consensus_rule = events.Rule(
            self,
            "ConsensusReachedRule",
            event_bus=bus,
            event_pattern=events.EventPattern(
                source=["incident-commander.consensus"],
                detail_type=["ConsensusReached"],
            ),
            description="Route consensus events",
        )

        # Add SNS target for critical events
        critical_rule = events.Rule(
            self,
            "CriticalIncidentRule",
            event_bus=bus,
            event_pattern=events.EventPattern(
                source=events.Match.prefix("incident-commander"),
                detail={
                    "severity": ["critical"],
                },
            ),
            description="Alert on critical incidents",
        )

        critical_rule.add_target(targets.SnsTopic(self.alert_topic))

    def _create_alert_topic(self) -> sns.Topic:
        """Create SNS topic for alerts."""
        topic = sns.Topic(
            self,
            "IncidentAlertTopic",
            display_name="Incident Commander Alerts",
            master_key=self.kms_key,
        )

        return topic

    def _create_ecs_cluster(self) -> ecs.Cluster:
        """Create ECS cluster."""
        cluster = ecs.Cluster(
            self,
            "IncidentCommanderCluster",
            vpc=self.vpc,
            container_insights=True,
            cluster_name="incident-commander",
        )

        return cluster

    def _create_agent_services(self) -> None:
        """Create ECS services for each agent."""
        agents = [
            ("detection", 512, 1024),
            ("diagnosis", 1024, 2048),
            ("prediction", 1024, 2048),
            ("resolution", 512, 1024),
            ("communication", 512, 1024),
        ]

        for agent_name, cpu, memory in agents:
            self._create_agent_service(agent_name, cpu, memory)

    def _create_agent_service(
        self, agent_name: str, cpu: int, memory: int
    ) -> ecs_patterns.ApplicationLoadBalancedFargateService:
        """Create an ECS Fargate service for an agent."""
        # Task definition
        task_definition = ecs.FargateTaskDefinition(
            self,
            f"{agent_name.title()}AgentTask",
            cpu=cpu,
            memory_limit_mib=memory,
            execution_role=self._create_execution_role(agent_name),
            task_role=self._create_task_role(agent_name),
        )

        # Container
        container = task_definition.add_container(
            f"{agent_name}-container",
            image=ecs.ContainerImage.from_registry(
                f"incident-commander/{agent_name}:latest"
            ),
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix=agent_name,
                log_retention=logs.RetentionDays.ONE_MONTH,
            ),
            environment={
                "AGENT_NAME": agent_name,
                "ENVIRONMENT": "production",
                "EVENTBRIDGE_BUS_NAME": self.event_bus.event_bus_name,
                "INCIDENTS_TABLE": self.incidents_table.table_name,
                "CONSENSUS_TABLE": self.consensus_table.table_name,
            },
            secrets={
                # Add secrets from Secrets Manager as needed
            },
        )

        container.add_port_mappings(
            ecs.PortMapping(container_port=8080, protocol=ecs.Protocol.TCP)
        )

        # Fargate service with ALB
        service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            f"{agent_name.title()}AgentService",
            cluster=self.ecs_cluster,
            task_definition=task_definition,
            desired_count=2,
            public_load_balancer=False,
            enable_execute_command=True,
            circuit_breaker=ecs.DeploymentCircuitBreaker(rollback=True),
            health_check_grace_period=Duration.seconds(60),
        )

        # Auto-scaling
        scalable_target = service.service.auto_scale_task_count(
            min_capacity=2,
            max_capacity=10,
        )

        scalable_target.scale_on_cpu_utilization(
            f"{agent_name}CpuScaling",
            target_utilization_percent=70,
            scale_in_cooldown=Duration.seconds(60),
            scale_out_cooldown=Duration.seconds(60),
        )

        # Grant permissions
        self.incidents_table.grant_read_write_data(service.task_definition.task_role)
        self.consensus_table.grant_read_write_data(service.task_definition.task_role)
        self.metrics_table.grant_read_write_data(service.task_definition.task_role)
        self.event_bus.grant_put_events_to(service.task_definition.task_role)

        return service

    def _create_execution_role(self, agent_name: str) -> iam.Role:
        """Create execution role for ECS task."""
        role = iam.Role(
            self,
            f"{agent_name.title()}ExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonECSTaskExecutionRolePolicy"
                )
            ],
        )

        return role

    def _create_task_role(self, agent_name: str) -> iam.Role:
        """Create task role for ECS task."""
        role = iam.Role(
            self,
            f"{agent_name.title()}TaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )

        # Add Bedrock permissions
        role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                ],
                resources=["arn:aws:bedrock:*::foundation-model/anthropic.claude-*"],
            )
        )

        # Add CloudWatch permissions
        role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                    "cloudwatch:PutMetricData",
                ],
                resources=["*"],
            )
        )

        return role

    def _create_monitoring(self) -> None:
        """Create CloudWatch dashboards and alarms."""
        dashboard = cloudwatch.Dashboard(
            self,
            "IncidentCommanderDashboard",
            dashboard_name="IncidentCommander",
        )

        # Add widgets
        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Incident Processing Rate",
                left=[
                    cloudwatch.Metric(
                        namespace="IncidentCommander",
                        metric_name="IncidentsProcessed",
                        statistic="Sum",
                        period=Duration.minutes(5),
                    )
                ],
            ),
            cloudwatch.GraphWidget(
                title="Consensus Latency",
                left=[
                    cloudwatch.Metric(
                        namespace="IncidentCommander",
                        metric_name="ConsensusLatency",
                        statistic="Average",
                        period=Duration.minutes(5),
                    )
                ],
            ),
        )

        # Create alarms
        high_error_rate = cloudwatch.Alarm(
            self,
            "HighErrorRate",
            metric=cloudwatch.Metric(
                namespace="IncidentCommander",
                metric_name="ErrorRate",
                statistic="Average",
                period=Duration.minutes(5),
            ),
            threshold=0.05,  # 5% error rate
            evaluation_periods=2,
            alarm_description="High error rate detected",
        )

        high_error_rate.add_alarm_action(
            cloudwatch_actions.SnsAction(self.alert_topic)
        )

    def _create_outputs(self) -> None:
        """Create CloudFormation outputs."""
        CfnOutput(
            self,
            "EventBusName",
            value=self.event_bus.event_bus_name,
            description="EventBridge event bus name",
        )

        CfnOutput(
            self,
            "IncidentsTableName",
            value=self.incidents_table.table_name,
            description="Incidents DynamoDB table name",
        )

        CfnOutput(
            self,
            "ConsensusTableName",
            value=self.consensus_table.table_name,
            description="Consensus DynamoDB table name",
        )

        CfnOutput(
            self,
            "AlertTopicArn",
            value=self.alert_topic.topic_arn,
            description="SNS topic for alerts",
        )
