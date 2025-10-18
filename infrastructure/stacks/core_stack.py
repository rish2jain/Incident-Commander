"""
Core Infrastructure Stack

Defines foundational AWS resources including VPC, IAM roles,
KMS keys, and other core infrastructure components.
"""

from aws_cdk import (
    Stack, Duration, RemovalPolicy,
    aws_iam as iam,
    aws_kms as kms,
    aws_ssm as ssm,
    aws_logs as logs
)
from constructs import Construct


class IncidentCommanderCoreStack(Stack):
    """Core infrastructure stack for Incident Commander."""
    
    def __init__(self, scope: Construct, construct_id: str, 
                 environment_name: str, env_config: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.environment_name = environment_name
        self.env_config = env_config
        
        # Create core resources
        self._create_kms_keys()
        self._create_iam_roles()
        self._create_log_groups()
        self._create_ssm_parameters()
    
    def _create_kms_keys(self):
        """Create KMS keys for encryption."""
        # Main encryption key for the application
        self.main_kms_key = kms.Key(
            self, "MainEncryptionKey",
            description=f"Main encryption key for Incident Commander {self.environment_name}",
            enable_key_rotation=True,
            removal_policy=RemovalPolicy.RETAIN if self.environment_name == 'production' else RemovalPolicy.DESTROY
        )
        
        # Create alias for the key
        kms.Alias(
            self, "MainEncryptionKeyAlias",
            alias_name=f"alias/incident-commander-{self.environment_name}",
            target_key=self.main_kms_key
        )
        
        # Separate key for audit logs (compliance requirement)
        self.audit_kms_key = kms.Key(
            self, "AuditEncryptionKey",
            description=f"Audit log encryption key for Incident Commander {self.environment_name}",
            enable_key_rotation=True,
            removal_policy=RemovalPolicy.RETAIN  # Always retain audit keys
        )
        
        kms.Alias(
            self, "AuditEncryptionKeyAlias",
            alias_name=f"alias/incident-commander-audit-{self.environment_name}",
            target_key=self.audit_kms_key
        )
    
    def _create_iam_roles(self):
        """Create core IAM roles."""
        # Cross-service access role
        self.cross_service_role = iam.Role(
            self, "CrossServiceRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            description="Role for cross-service communication",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy")
            ]
        )
        
        # Add permissions for core services
        self.cross_service_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "kms:Decrypt",
                    "kms:DescribeKey",
                    "ssm:GetParameter",
                    "ssm:GetParameters",
                    "ssm:GetParametersByPath"
                ],
                resources=[
                    self.main_kms_key.key_arn,
                    f"arn:aws:ssm:{self.region}:{self.account}:parameter/incident-commander/{self.environment_name}/*"
                ]
            )
        )
        
        # CloudWatch logging permissions
        self.cross_service_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                    "logs:DescribeLogStreams"
                ],
                resources=[
                    f"arn:aws:logs:{self.region}:{self.account}:log-group:/incident-commander/{self.environment_name}/*"
                ]
            )
        )
    
    def _create_log_groups(self):
        """Create CloudWatch log groups."""
        log_groups = [
            "application",
            "agents",
            "consensus",
            "performance",
            "security",
            "audit"
        ]
        
        self.log_groups = {}
        
        for log_group_name in log_groups:
            # Use audit key for audit logs, main key for others
            encryption_key = self.audit_kms_key if log_group_name == "audit" else self.main_kms_key
            
            log_group = logs.LogGroup(
                self, f"LogGroup{log_group_name.title()}",
                log_group_name=f"/incident-commander/{self.environment_name}/{log_group_name}",
                retention=logs.RetentionDays(self.env_config['log_retention_days']),
                encryption_key=encryption_key,
                removal_policy=RemovalPolicy.RETAIN if self.environment_name == 'production' else RemovalPolicy.DESTROY
            )
            
            self.log_groups[log_group_name] = log_group
    
    def _create_ssm_parameters(self):
        """Create SSM parameters for configuration."""
        # Application configuration parameters
        config_parameters = {
            "environment": self.environment_name,
            "log-level": "INFO" if self.environment_name == "production" else "DEBUG",
            "api-rate-limit": "1000" if self.environment_name == "production" else "100",
            "enable-detailed-monitoring": str(self.env_config['enable_detailed_monitoring']).lower(),
            "backup-retention-days": str(self.env_config['backup_retention_days']),
            "cost-budget-hourly": "200.0" if self.environment_name == "production" else "50.0",
            "emergency-cost-limit": "1000.0" if self.environment_name == "production" else "200.0"
        }
        
        self.ssm_parameters = {}
        
        for param_name, param_value in config_parameters.items():
            parameter = ssm.StringParameter(
                self, f"Parameter{param_name.replace('-', '').title()}",
                parameter_name=f"/incident-commander/{self.environment_name}/config/{param_name}",
                string_value=param_value,
                description=f"Configuration parameter: {param_name}",
                tier=ssm.ParameterTier.STANDARD
            )
            
            self.ssm_parameters[param_name] = parameter
        
        # Bedrock model configuration
        bedrock_models = {
            "development": ["claude-3-haiku"],
            "staging": ["claude-3-sonnet", "claude-3-haiku"],
            "production": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"]
        }
        
        models_param = ssm.StringListParameter(
            self, "BedrockModelsParameter",
            parameter_name=f"/incident-commander/{self.environment_name}/bedrock/models",
            string_list_value=bedrock_models[self.environment_name],
            description="Available Bedrock models for this environment"
        )
        
        self.ssm_parameters["bedrock-models"] = models_param
        
        # Performance configuration
        performance_config = {
            "connection-pool-size": "50" if self.environment_name == "production" else "20",
            "cache-ttl-seconds": "300",
            "memory-threshold": "0.8",
            "gc-threshold": "0.85"
        }
        
        for param_name, param_value in performance_config.items():
            parameter = ssm.StringParameter(
                self, f"PerformanceParameter{param_name.replace('-', '').title()}",
                parameter_name=f"/incident-commander/{self.environment_name}/performance/{param_name}",
                string_value=param_value,
                description=f"Performance configuration: {param_name}"
            )
            
            self.ssm_parameters[f"performance-{param_name}"] = parameter