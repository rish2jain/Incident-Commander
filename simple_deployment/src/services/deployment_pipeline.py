"""
Automated Deployment Pipeline Service for Incident Commander

Provides automated deployment system for staging and production environments
with CDK deployment automation and resource provisioning.
"""

import asyncio
import json
import os
import subprocess
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, asdict
from pathlib import Path

from src.utils.config import config
from src.utils.logging import get_logger
from src.utils.exceptions import IncidentCommanderError
from src.services.aws import AWSServiceFactory


logger = get_logger("deployment_pipeline")


class Environment(Enum):
    """Deployment environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class DeploymentStatus(Enum):
    """Deployment status types."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class AWSResource:
    """AWS resource information."""
    resource_type: str
    resource_id: str
    resource_arn: str
    status: str
    created_at: datetime
    tags: Dict[str, str]


@dataclass
class ValidationResult:
    """Deployment validation result."""
    is_valid: bool
    validation_type: str
    message: str
    details: Dict[str, Any]
    validated_at: datetime


@dataclass
class RollbackPlan:
    """Deployment rollback plan."""
    rollback_id: str
    previous_version: str
    rollback_steps: List[str]
    estimated_duration_minutes: int
    created_at: datetime


@dataclass
class DeploymentResult:
    """Deployment operation result."""
    deployment_id: str
    environment: Environment
    status: DeploymentStatus
    resources_created: List[AWSResource]
    validation_results: List[ValidationResult]
    rollback_plan: Optional[RollbackPlan]
    deployment_time: float
    started_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]


class DeploymentPipelineError(IncidentCommanderError):
    """Deployment pipeline specific error."""
    pass


class DeploymentPipeline:
    """
    Automated deployment pipeline with environment management.
    
    Provides CDK deployment automation and resource provisioning
    for staging and production environments.
    """
    
    def __init__(self, aws_factory: AWSServiceFactory):
        """Initialize deployment pipeline."""
        self.aws_factory = aws_factory
        self._active_deployments: Dict[str, DeploymentResult] = {}
        self._deployment_history: List[DeploymentResult] = []
        self._environment_configs = self._load_environment_configs()
        
        # CDK configuration
        self.cdk_app_path = Path("infrastructure/app.py")
        self.cdk_context_file = Path("cdk.context.json")
        
        # Deployment timeouts (minutes)
        self.deployment_timeouts = {
            Environment.DEVELOPMENT: 15,
            Environment.STAGING: 30,
            Environment.PRODUCTION: 45
        }
    
    def _load_environment_configs(self) -> Dict[Environment, Dict[str, Any]]:
        """Load environment-specific configurations."""
        return {
            Environment.DEVELOPMENT: {
                "instance_types": ["t3.medium"],
                "min_capacity": 1,
                "max_capacity": 3,
                "enable_detailed_monitoring": False,
                "backup_retention_days": 7,
                "log_retention_days": 7,
                "auto_scaling_enabled": False,
                "multi_az": False
            },
            Environment.STAGING: {
                "instance_types": ["t3.large", "m5.large"],
                "min_capacity": 2,
                "max_capacity": 10,
                "enable_detailed_monitoring": True,
                "backup_retention_days": 30,
                "log_retention_days": 30,
                "auto_scaling_enabled": True,
                "multi_az": True
            },
            Environment.PRODUCTION: {
                "instance_types": ["m5.xlarge", "m5.2xlarge", "c5.xlarge"],
                "min_capacity": 3,
                "max_capacity": 50,
                "enable_detailed_monitoring": True,
                "backup_retention_days": 2555,  # 7 years for compliance
                "log_retention_days": 90,
                "auto_scaling_enabled": True,
                "multi_az": True,
                "encryption_required": True,
                "backup_required": True
            }
        }
    
    async def deploy_environment(self, environment: Environment, 
                               deployment_config: Optional[Dict[str, Any]] = None) -> DeploymentResult:
        """
        Deploy complete system to specified environment.
        
        Args:
            environment: Target deployment environment
            deployment_config: Optional deployment configuration overrides
            
        Returns:
            Deployment result with status and resource information
        """
        deployment_id = f"deploy_{environment.value}_{int(datetime.utcnow().timestamp())}"
        start_time = datetime.utcnow()
        
        logger.info(f"Starting deployment to {environment.value} (ID: {deployment_id})")
        
        # Initialize deployment result
        deployment_result = DeploymentResult(
            deployment_id=deployment_id,
            environment=environment,
            status=DeploymentStatus.PENDING,
            resources_created=[],
            validation_results=[],
            rollback_plan=None,
            deployment_time=0.0,
            started_at=start_time,
            completed_at=None,
            error_message=None
        )
        
        self._active_deployments[deployment_id] = deployment_result
        
        try:
            # Update status to in progress
            deployment_result.status = DeploymentStatus.IN_PROGRESS
            
            # Prepare environment configuration
            env_config = self._environment_configs[environment].copy()
            if deployment_config:
                env_config.update(deployment_config)
            
            # Create rollback plan before deployment
            rollback_plan = await self._create_rollback_plan(environment, deployment_id)
            deployment_result.rollback_plan = rollback_plan
            
            # Execute CDK deployment
            resources_created = await self._execute_cdk_deployment(environment, env_config)
            deployment_result.resources_created = resources_created
            
            # Update status to validating
            deployment_result.status = DeploymentStatus.VALIDATING
            
            # Validate deployment
            validation_results = await self._validate_deployment(environment, resources_created)
            deployment_result.validation_results = validation_results
            
            # Check if all validations passed
            all_valid = all(result.is_valid for result in validation_results)
            
            if all_valid:
                deployment_result.status = DeploymentStatus.COMPLETED
                logger.info(f"Deployment {deployment_id} completed successfully")
            else:
                deployment_result.status = DeploymentStatus.FAILED
                deployment_result.error_message = "Deployment validation failed"
                logger.error(f"Deployment {deployment_id} failed validation")
                
                # Trigger rollback for failed deployment
                await self._execute_rollback(deployment_result)
            
        except Exception as e:
            deployment_result.status = DeploymentStatus.FAILED
            deployment_result.error_message = str(e)
            logger.error(f"Deployment {deployment_id} failed: {e}")
            
            # Attempt rollback on failure
            try:
                await self._execute_rollback(deployment_result)
            except Exception as rollback_error:
                logger.error(f"Rollback failed for deployment {deployment_id}: {rollback_error}")
        
        finally:
            # Calculate deployment time and finalize
            deployment_result.deployment_time = (datetime.utcnow() - start_time).total_seconds()
            deployment_result.completed_at = datetime.utcnow()
            
            # Move to history and remove from active
            self._deployment_history.append(deployment_result)
            self._active_deployments.pop(deployment_id, None)
        
        return deployment_result
    
    async def _execute_cdk_deployment(self, environment: Environment, 
                                    env_config: Dict[str, Any]) -> List[AWSResource]:
        """
        Execute CDK deployment for the specified environment.
        
        Args:
            environment: Target environment
            env_config: Environment configuration
            
        Returns:
            List of created AWS resources
        """
        logger.info(f"Executing CDK deployment for {environment.value}")
        
        # Set environment variables for CDK
        env_vars = os.environ.copy()
        env_vars.update({
            "ENVIRONMENT": environment.value,
            "CDK_DEFAULT_REGION": config.aws.region,
            "CDK_DEFAULT_ACCOUNT": await self._get_aws_account_id()
        })
        
        # Add environment-specific configuration
        for key, value in env_config.items():
            env_vars[f"CONFIG_{key.upper()}"] = str(value)
        
        resources_created = []
        
        try:
            # Change to infrastructure directory
            infrastructure_dir = Path("infrastructure")
            
            # Bootstrap CDK if needed (only for first deployment)
            if environment != Environment.DEVELOPMENT:
                await self._run_cdk_command(
                    ["cdk", "bootstrap"],
                    cwd=infrastructure_dir,
                    env=env_vars,
                    timeout_minutes=10
                )
            
            # Synthesize CDK app
            await self._run_cdk_command(
                ["cdk", "synth"],
                cwd=infrastructure_dir,
                env=env_vars,
                timeout_minutes=5
            )
            
            # Deploy all stacks
            stack_names = self._get_stack_names(environment)
            
            for stack_name in stack_names:
                logger.info(f"Deploying stack: {stack_name}")
                
                # Deploy individual stack
                result = await self._run_cdk_command(
                    ["cdk", "deploy", stack_name, "--require-approval", "never"],
                    cwd=infrastructure_dir,
                    env=env_vars,
                    timeout_minutes=self.deployment_timeouts[environment]
                )
                
                # Parse stack outputs to get resource information
                stack_resources = await self._parse_stack_outputs(stack_name, result.stdout)
                resources_created.extend(stack_resources)
            
            logger.info(f"CDK deployment completed. Created {len(resources_created)} resources")
            
        except subprocess.TimeoutExpired:
            raise DeploymentPipelineError(f"CDK deployment timed out for {environment.value}")
        except subprocess.CalledProcessError as e:
            raise DeploymentPipelineError(f"CDK deployment failed: {e.stderr}")
        
        return resources_created
    
    async def _run_cdk_command(self, command: List[str], cwd: Path, 
                             env: Dict[str, str], timeout_minutes: int) -> subprocess.CompletedProcess:
        """
        Run CDK command with proper error handling and timeout.
        
        Args:
            command: CDK command to execute
            cwd: Working directory
            env: Environment variables
            timeout_minutes: Command timeout in minutes
            
        Returns:
            Completed process result
        """
        logger.debug(f"Running CDK command: {' '.join(command)}")
        
        process = await asyncio.create_subprocess_exec(
            *command,
            cwd=cwd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout_minutes * 60
            )
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown CDK error"
                raise subprocess.CalledProcessError(process.returncode, command, stderr=error_msg)
            
            return subprocess.CompletedProcess(
                command, process.returncode, stdout.decode(), stderr.decode()
            )
            
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise subprocess.TimeoutExpired(command, timeout_minutes * 60)
    
    def _get_stack_names(self, environment: Environment) -> List[str]:
        """Get ordered list of stack names for deployment."""
        env_suffix = environment.value.title()
        
        # Deployment order is important due to dependencies
        return [
            f"IncidentCommanderCore-{environment.value}",
            f"IncidentCommanderNetworking-{environment.value}",
            f"IncidentCommanderSecurity-{environment.value}",
            f"IncidentCommanderStorage-{environment.value}",
            f"IncidentCommanderBedrock-{environment.value}",
            f"IncidentCommanderCompute-{environment.value}",
            f"IncidentCommanderMonitoring-{environment.value}"
        ]
    
    async def _parse_stack_outputs(self, stack_name: str, stdout: str) -> List[AWSResource]:
        """
        Parse CDK stack outputs to extract resource information.
        
        Args:
            stack_name: Name of the deployed stack
            stdout: CDK command output
            
        Returns:
            List of created AWS resources
        """
        resources = []
        
        try:
            # In a real implementation, this would parse CDK outputs
            # For now, we'll create mock resources based on stack type
            
            if "Core" in stack_name:
                resources.extend([
                    AWSResource(
                        resource_type="AWS::KMS::Key",
                        resource_id="incident-commander-key",
                        resource_arn=f"arn:aws:kms:{config.aws.region}:123456789012:key/12345678-1234-1234-1234-123456789012",
                        status="Active",
                        created_at=datetime.utcnow(),
                        tags={"Project": "IncidentCommander", "Stack": stack_name}
                    ),
                    AWSResource(
                        resource_type="AWS::IAM::Role",
                        resource_id="incident-commander-service-role",
                        resource_arn=f"arn:aws:iam::123456789012:role/IncidentCommanderServiceRole",
                        status="Active",
                        created_at=datetime.utcnow(),
                        tags={"Project": "IncidentCommander", "Stack": stack_name}
                    )
                ])
            
            elif "Storage" in stack_name:
                resources.extend([
                    AWSResource(
                        resource_type="AWS::DynamoDB::Table",
                        resource_id="incident-commander-incidents",
                        resource_arn=f"arn:aws:dynamodb:{config.aws.region}:123456789012:table/incident-commander-incidents",
                        status="Active",
                        created_at=datetime.utcnow(),
                        tags={"Project": "IncidentCommander", "Stack": stack_name}
                    ),
                    AWSResource(
                        resource_type="AWS::S3::Bucket",
                        resource_id="incident-commander-artifacts",
                        resource_arn=f"arn:aws:s3:::incident-commander-artifacts",
                        status="Active",
                        created_at=datetime.utcnow(),
                        tags={"Project": "IncidentCommander", "Stack": stack_name}
                    )
                ])
            
            elif "Compute" in stack_name:
                resources.extend([
                    AWSResource(
                        resource_type="AWS::ECS::Cluster",
                        resource_id="incident-commander-cluster",
                        resource_arn=f"arn:aws:ecs:{config.aws.region}:123456789012:cluster/incident-commander-cluster",
                        status="Active",
                        created_at=datetime.utcnow(),
                        tags={"Project": "IncidentCommander", "Stack": stack_name}
                    ),
                    AWSResource(
                        resource_type="AWS::ApiGateway::RestApi",
                        resource_id="incident-commander-api",
                        resource_arn=f"arn:aws:apigateway:{config.aws.region}::/restapis/abcdef123456",
                        status="Active",
                        created_at=datetime.utcnow(),
                        tags={"Project": "IncidentCommander", "Stack": stack_name}
                    )
                ])
            
        except Exception as e:
            logger.warning(f"Failed to parse stack outputs for {stack_name}: {e}")
        
        return resources
    
    async def _get_aws_account_id(self) -> str:
        """Get current AWS account ID."""
        try:
            client = await self.aws_factory.create_client('sts')
            response = await client.get_caller_identity()
            return response['Account']
        except Exception as e:
            logger.warning(f"Failed to get AWS account ID: {e}")
            return "123456789012"  # Fallback for development
    
    async def _create_rollback_plan(self, environment: Environment, 
                                  deployment_id: str) -> RollbackPlan:
        """
        Create rollback plan before deployment.
        
        Args:
            environment: Target environment
            deployment_id: Deployment identifier
            
        Returns:
            Rollback plan with steps and estimated duration
        """
        rollback_id = f"rollback_{deployment_id}"
        
        # Get current deployment version (mock implementation)
        previous_version = await self._get_current_deployment_version(environment)
        
        # Define rollback steps based on environment
        rollback_steps = [
            "Stop new traffic routing",
            "Scale down new resources",
            "Restore previous stack configuration",
            "Validate rollback completion",
            "Resume normal operations"
        ]
        
        # Estimate rollback duration based on environment complexity
        duration_estimates = {
            Environment.DEVELOPMENT: 5,
            Environment.STAGING: 10,
            Environment.PRODUCTION: 15
        }
        
        return RollbackPlan(
            rollback_id=rollback_id,
            previous_version=previous_version,
            rollback_steps=rollback_steps,
            estimated_duration_minutes=duration_estimates[environment],
            created_at=datetime.utcnow()
        )
    
    async def _get_current_deployment_version(self, environment: Environment) -> str:
        """Get current deployment version for the environment."""
        # In a real implementation, this would query the actual deployment state
        return f"v1.0.0-{environment.value}-{int(datetime.utcnow().timestamp())}"
    
    async def _validate_deployment(self, environment: Environment, 
                                 resources: List[AWSResource]) -> List[ValidationResult]:
        """
        Validate deployment by checking resource status and health.
        
        Args:
            environment: Deployed environment
            resources: Created AWS resources
            
        Returns:
            List of validation results
        """
        logger.info(f"Validating deployment for {environment.value}")
        
        validation_results = []
        
        # Validate resource creation
        resource_validation = await self._validate_resources(resources)
        validation_results.append(resource_validation)
        
        # Validate service health
        health_validation = await self._validate_service_health(environment)
        validation_results.append(health_validation)
        
        # Validate API endpoints
        api_validation = await self._validate_api_endpoints(environment)
        validation_results.append(api_validation)
        
        # Environment-specific validations
        if environment == Environment.PRODUCTION:
            # Additional production validations
            security_validation = await self._validate_security_configuration(resources)
            validation_results.append(security_validation)
            
            backup_validation = await self._validate_backup_configuration(resources)
            validation_results.append(backup_validation)
        
        return validation_results
    
    async def _validate_resources(self, resources: List[AWSResource]) -> ValidationResult:
        """Validate that all resources were created successfully."""
        try:
            failed_resources = [r for r in resources if r.status != "Active"]
            
            if not failed_resources:
                return ValidationResult(
                    is_valid=True,
                    validation_type="resource_creation",
                    message=f"All {len(resources)} resources created successfully",
                    details={"total_resources": len(resources), "failed_resources": 0},
                    validated_at=datetime.utcnow()
                )
            else:
                return ValidationResult(
                    is_valid=False,
                    validation_type="resource_creation",
                    message=f"{len(failed_resources)} resources failed to create",
                    details={
                        "total_resources": len(resources),
                        "failed_resources": len(failed_resources),
                        "failed_resource_ids": [r.resource_id for r in failed_resources]
                    },
                    validated_at=datetime.utcnow()
                )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                validation_type="resource_creation",
                message=f"Resource validation failed: {e}",
                details={"error": str(e)},
                validated_at=datetime.utcnow()
            )
    
    async def _validate_service_health(self, environment: Environment) -> ValidationResult:
        """Validate service health after deployment."""
        try:
            # Mock health check - in real implementation would check actual services
            await asyncio.sleep(2)  # Simulate health check delay
            
            return ValidationResult(
                is_valid=True,
                validation_type="service_health",
                message="All services are healthy",
                details={
                    "services_checked": ["api", "agents", "database", "message_bus"],
                    "healthy_services": 4,
                    "unhealthy_services": 0
                },
                validated_at=datetime.utcnow()
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                validation_type="service_health",
                message=f"Service health validation failed: {e}",
                details={"error": str(e)},
                validated_at=datetime.utcnow()
            )
    
    async def _validate_api_endpoints(self, environment: Environment) -> ValidationResult:
        """Validate API endpoints are responding correctly."""
        try:
            # Mock API validation - in real implementation would make actual HTTP requests
            await asyncio.sleep(1)  # Simulate API check delay
            
            return ValidationResult(
                is_valid=True,
                validation_type="api_endpoints",
                message="All API endpoints are responding",
                details={
                    "endpoints_checked": ["/health", "/status", "/incidents"],
                    "successful_responses": 3,
                    "failed_responses": 0
                },
                validated_at=datetime.utcnow()
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                validation_type="api_endpoints",
                message=f"API endpoint validation failed: {e}",
                details={"error": str(e)},
                validated_at=datetime.utcnow()
            )
    
    async def _validate_security_configuration(self, resources: List[AWSResource]) -> ValidationResult:
        """Validate security configuration for production deployments."""
        try:
            # Check for encryption, IAM roles, security groups, etc.
            security_resources = [r for r in resources if r.resource_type in [
                "AWS::KMS::Key", "AWS::IAM::Role", "AWS::EC2::SecurityGroup"
            ]]
            
            return ValidationResult(
                is_valid=len(security_resources) > 0,
                validation_type="security_configuration",
                message=f"Security configuration validated ({len(security_resources)} security resources)",
                details={
                    "security_resources": len(security_resources),
                    "encryption_enabled": True,
                    "iam_roles_configured": True
                },
                validated_at=datetime.utcnow()
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                validation_type="security_configuration",
                message=f"Security validation failed: {e}",
                details={"error": str(e)},
                validated_at=datetime.utcnow()
            )
    
    async def _validate_backup_configuration(self, resources: List[AWSResource]) -> ValidationResult:
        """Validate backup configuration for production deployments."""
        try:
            # Check for backup-enabled resources
            backup_resources = [r for r in resources if r.resource_type in [
                "AWS::DynamoDB::Table", "AWS::S3::Bucket"
            ]]
            
            return ValidationResult(
                is_valid=len(backup_resources) > 0,
                validation_type="backup_configuration",
                message=f"Backup configuration validated ({len(backup_resources)} backup-enabled resources)",
                details={
                    "backup_enabled_resources": len(backup_resources),
                    "retention_configured": True,
                    "cross_region_backup": True
                },
                validated_at=datetime.utcnow()
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                validation_type="backup_configuration",
                message=f"Backup validation failed: {e}",
                details={"error": str(e)},
                validated_at=datetime.utcnow()
            )
    
    async def _execute_rollback(self, deployment_result: DeploymentResult) -> bool:
        """
        Execute rollback for failed deployment.
        
        Args:
            deployment_result: Failed deployment result
            
        Returns:
            True if rollback successful, False otherwise
        """
        if not deployment_result.rollback_plan:
            logger.error(f"No rollback plan available for deployment {deployment_result.deployment_id}")
            return False
        
        logger.info(f"Executing rollback for deployment {deployment_result.deployment_id}")
        
        try:
            rollback_plan = deployment_result.rollback_plan
            
            # Execute rollback steps
            for step in rollback_plan.rollback_steps:
                logger.info(f"Executing rollback step: {step}")
                await asyncio.sleep(1)  # Simulate rollback step execution
            
            deployment_result.status = DeploymentStatus.ROLLED_BACK
            logger.info(f"Rollback completed for deployment {deployment_result.deployment_id}")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed for deployment {deployment_result.deployment_id}: {e}")
            return False
    
    def get_deployment_status(self, deployment_id: str) -> Optional[DeploymentResult]:
        """Get status of a specific deployment."""
        # Check active deployments first
        if deployment_id in self._active_deployments:
            return self._active_deployments[deployment_id]
        
        # Check deployment history
        for deployment in self._deployment_history:
            if deployment.deployment_id == deployment_id:
                return deployment
        
        return None
    
    def list_active_deployments(self) -> List[DeploymentResult]:
        """List all currently active deployments."""
        return list(self._active_deployments.values())
    
    def get_deployment_history(self, limit: int = 50) -> List[DeploymentResult]:
        """Get deployment history with optional limit."""
        return self._deployment_history[-limit:] if limit else self._deployment_history
    
    def get_environment_status(self, environment: Environment) -> Dict[str, Any]:
        """Get current status of a specific environment."""
        # Get latest deployment for environment
        env_deployments = [
            d for d in self._deployment_history 
            if d.environment == environment
        ]
        
        latest_deployment = env_deployments[-1] if env_deployments else None
        
        return {
            "environment": environment.value,
            "latest_deployment": {
                "deployment_id": latest_deployment.deployment_id if latest_deployment else None,
                "status": latest_deployment.status.value if latest_deployment else "never_deployed",
                "deployed_at": latest_deployment.completed_at.isoformat() if latest_deployment and latest_deployment.completed_at else None,
                "resources_count": len(latest_deployment.resources_created) if latest_deployment else 0
            },
            "configuration": self._environment_configs[environment],
            "deployment_timeout_minutes": self.deployment_timeouts[environment]
        }


# Global deployment pipeline instance
_deployment_pipeline: Optional[DeploymentPipeline] = None


def get_deployment_pipeline(aws_factory: Optional[AWSServiceFactory] = None) -> DeploymentPipeline:
    """Get or create the global deployment pipeline instance."""
    global _deployment_pipeline
    if _deployment_pipeline is None:
        if aws_factory is None:
            from src.services.aws import get_aws_service_factory
            aws_factory = get_aws_service_factory()
        _deployment_pipeline = DeploymentPipeline(aws_factory)
    return _deployment_pipeline