"""
Enhanced Bedrock Stack for Incident Commander with AgentCore Integration
"""

from aws_cdk import (
    Stack,
    Duration,
    aws_iam as iam,
    aws_s3 as s3,
    aws_logs as logs,
    CfnOutput,
)
from constructs import Construct
import json


class IncidentCommanderBedrockStack(Stack):
    """Enhanced Bedrock AI infrastructure stack with AgentCore support."""

    def __init__(self, scope: Construct, construct_id: str, 
                 environment_name: str, env_config: dict,
                 execution_role: iam.Role, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.environment_name = environment_name
        self.execution_role = execution_role
        
        # Create S3 bucket for AgentCore artifacts
        self.agentcore_bucket = self._create_agentcore_bucket()
        
        # Create enhanced IAM roles for multi-agent system
        self.agent_roles = self._create_agent_roles()
        
        # Create Bedrock agent configurations
        self.agent_configs = self._create_agent_configurations()
        
        # Create CloudWatch log groups for agents
        self.log_groups = self._create_log_groups()

    def _create_agentcore_bucket(self) -> s3.Bucket:
        """Create S3 bucket for AgentCore runtime artifacts."""
        bucket = s3.Bucket(
            self, f"AgentCoreBucket-{self.environment_name}",
            bucket_name=f"bedrock-agentcore-{self.environment_name}-{self.account}",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="AgentCoreArtifactCleanup",
                    enabled=True,
                    expiration=Duration.days(90),
                    noncurrent_version_expiration=Duration.days(30)
                )
            ],
            public_read_access=False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL
        )
        
        return bucket

    def _create_agent_roles(self) -> dict:
        """Create IAM roles for different agent types."""
        agent_roles = {}
        
        # Base agent policy document
        base_agent_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeModel",
                        "bedrock:InvokeModelWithResponseStream",
                        "bedrock:GetFoundationModel",
                        "bedrock:ListFoundationModels"
                    ],
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock-agentcore:InvokeAgentRuntime",
                        "bedrock-agentcore:GetAgentRuntime",
                        "bedrock-agentcore:ListAgentRuntimes"
                    ],
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                        "logs:DescribeLogGroups",
                        "logs:DescribeLogStreams"
                    ],
                    "Resource": f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws/bedrock-agentcore/*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:ListBucket"
                    ],
                    "Resource": [
                        self.agentcore_bucket.bucket_arn,
                        f"{self.agentcore_bucket.bucket_arn}/*"
                    ]
                }
            ]
        }
        
        # Agent-specific configurations
        agent_configs = {
            "detection": {
                "additional_actions": [
                    "cloudwatch:GetMetricStatistics",
                    "cloudwatch:ListMetrics",
                    "logs:FilterLogEvents",
                    "logs:GetLogEvents"
                ]
            },
            "diagnosis": {
                "additional_actions": [
                    "xray:GetTraceSummaries",
                    "xray:BatchGetTraces",
                    "dynamodb:GetItem",
                    "dynamodb:Query"
                ]
            },
            "prediction": {
                "additional_actions": [
                    "forecast:CreatePredictor",
                    "forecast:DescribePredictor",
                    "sagemaker:InvokeEndpoint"
                ]
            },
            "resolution": {
                "additional_actions": [
                    "lambda:InvokeFunction",
                    "ecs:UpdateService",
                    "autoscaling:SetDesiredCapacity",
                    "ssm:SendCommand"
                ]
            },
            "communication": {
                "additional_actions": [
                    "sns:Publish",
                    "ses:SendEmail",
                    "secretsmanager:GetSecretValue"
                ]
            }
        }
        
        # Create role for each agent type
        for agent_name, config in agent_configs.items():
            # Create agent-specific policy
            agent_policy = base_agent_policy.copy()
            agent_policy["Statement"].append({
                "Effect": "Allow",
                "Action": config["additional_actions"],
                "Resource": "*"
            })
            
            # Create IAM role
            role = iam.Role(
                self, f"{agent_name.title()}AgentRole-{self.environment_name}",
                role_name=f"IncidentCommander-{agent_name.title()}Agent-{self.environment_name}",
                assumed_by=iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),
                inline_policies={
                    f"{agent_name}AgentPolicy": iam.PolicyDocument.from_json(agent_policy)
                },
                description=f"IAM role for {agent_name} agent in Incident Commander system"
            )
            
            agent_roles[agent_name] = role
        
        return agent_roles

    def _create_agent_configurations(self) -> dict:
        """Create Bedrock agent configurations for multi-agent system."""
        agent_configs = {}
        
        # Agent instructions and capabilities
        agent_instructions = {
            "detection": {
                "instruction": """You are the Detection Agent in the Incident Commander system. Your role is to:
1. Monitor system metrics and logs for anomalies
2. Detect potential incidents using pattern recognition
3. Classify incident severity and type
4. Trigger the incident response workflow
5. Coordinate with other agents through the Byzantine consensus system

Use Claude 4 Sonnet for complex analysis and Nova Micro for fast triage decisions.""",
                "model_id": "anthropic.claude-sonnet-4-20250514-v1:0"
            },
            "diagnosis": {
                "instruction": """You are the Diagnosis Agent in the Incident Commander system. Your role is to:
1. Analyze detected incidents to determine root causes
2. Examine logs, traces, and system state
3. Provide detailed diagnostic information
4. Recommend investigation paths
5. Participate in Byzantine consensus for resolution decisions

Use Claude 4 Opus for deep reasoning and Nova Pro for comprehensive analysis.""",
                "model_id": "anthropic.claude-opus-4-1-20250805-v1:0"
            },
            "prediction": {
                "instruction": """You are the Prediction Agent in the Incident Commander system. Your role is to:
1. Predict incident escalation and impact
2. Forecast system behavior and failure modes
3. Provide proactive recommendations
4. Estimate resolution timelines
5. Support preventive measures through predictive analytics

Use Nova Premier for advanced forecasting and Claude 4 Sonnet for reasoning.""",
                "model_id": "amazon.nova-premier-v1:0"
            },
            "resolution": {
                "instruction": """You are the Resolution Agent in the Incident Commander system. Your role is to:
1. Execute automated remediation actions
2. Coordinate manual intervention when needed
3. Implement rollback procedures if necessary
4. Monitor resolution effectiveness
5. Ensure safe and controlled incident resolution

Use Claude 4 Haiku for fast action decisions and Nova Lite for execution planning.""",
                "model_id": "anthropic.claude-haiku-4-5-20251001-v1:0"
            },
            "communication": {
                "instruction": """You are the Communication Agent in the Incident Commander system. Your role is to:
1. Manage stakeholder notifications
2. Provide status updates and summaries
3. Coordinate with external teams
4. Generate incident reports and documentation
5. Ensure clear and timely communication throughout the incident lifecycle

Use Claude 4 Sonnet for clear communication and Nova Sonic for rapid updates.""",
                "model_id": "anthropic.claude-sonnet-4-20250514-v1:0"
            }
        }
        
        # Store configurations for later use in deployment
        for agent_name, config in agent_instructions.items():
            agent_configs[agent_name] = {
                "name": f"IncidentCommander-{agent_name.title()}Agent-{self.environment_name}",
                "instruction": config["instruction"],
                "model_id": config["model_id"],
                "role_arn": self.agent_roles[agent_name].role_arn,
                "agent_type": agent_name
            }
        
        return agent_configs

    def _create_log_groups(self) -> dict:
        """Create CloudWatch log groups for agent monitoring."""
        log_groups = {}
        
        for agent_name in self.agent_roles.keys():
            log_group = logs.LogGroup(
                self, f"{agent_name.title()}AgentLogGroup-{self.environment_name}",
                log_group_name=f"/aws/bedrock-agentcore/incident-commander/{agent_name}-{self.environment_name}",
                retention=logs.RetentionDays.THREE_MONTHS if self.environment_name == "production" else logs.RetentionDays.ONE_WEEK,
                removal_policy=self.node.try_get_context("@aws-cdk/aws-logs:retentionPolicyRemovalPolicy") or None
            )
            
            log_groups[agent_name] = log_group
        
        return log_groups

    def _create_outputs(self):
        """Create CloudFormation outputs for agent configurations."""
        # Output S3 bucket name
        CfnOutput(
            self, "AgentCoreBucketName",
            value=self.agentcore_bucket.bucket_name,
            description="S3 bucket for AgentCore runtime artifacts"
        )
        
        # Output agent role ARNs
        for agent_name, role in self.agent_roles.items():
            CfnOutput(
                self, f"{agent_name.title()}AgentRoleArn",
                value=role.role_arn,
                description=f"IAM role ARN for {agent_name} agent"
            )
        
        # Output log group names
        for agent_name, log_group in self.log_groups.items():
            CfnOutput(
                self, f"{agent_name.title()}AgentLogGroup",
                value=log_group.log_group_name,
                description=f"CloudWatch log group for {agent_name} agent"
            )