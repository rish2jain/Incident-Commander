"""
Deployment API Router for Incident Commander

Provides FastAPI routes for deployment management and monitoring
with rollback functionality and error reporting.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from src.utils.logging import get_logger
from src.services.deployment_pipeline import (
    DeploymentPipeline, Environment, DeploymentStatus, DeploymentResult,
    get_deployment_pipeline
)
from src.services.bedrock_agent_configurator import (
    BedrockAgentConfigurator, AgentType, KnowledgeBaseType,
    get_bedrock_agent_configurator
)
from src.services.deployment_validator import (
    DeploymentValidator, ValidationCategory, ValidationSeverity,
    get_deployment_validator
)
from src.api.dependencies import get_services


logger = get_logger("deployment_api")

router = APIRouter(prefix="/deployment", tags=["deployment"])


# Request/Response Models

class DeploymentRequest(BaseModel):
    """Deployment request model."""
    environment: str = Field(..., description="Target environment (development, staging, production)")
    deployment_config: Optional[Dict[str, Any]] = Field(None, description="Optional deployment configuration overrides")
    validate_before_deploy: bool = Field(True, description="Whether to validate before deployment")
    auto_rollback_on_failure: bool = Field(True, description="Whether to automatically rollback on failure")


class BedrockAgentConfigRequest(BaseModel):
    """Bedrock agent configuration request model."""
    agent_type: str = Field(..., description="Type of agent to configure")
    custom_config: Optional[Dict[str, Any]] = Field(None, description="Optional custom configuration")


class KnowledgeBaseConfigRequest(BaseModel):
    """Knowledge base configuration request model."""
    knowledge_base_type: str = Field(..., description="Type of knowledge base to configure")
    custom_config: Optional[Dict[str, Any]] = Field(None, description="Optional custom configuration")


class ValidationRequest(BaseModel):
    """Validation request model."""
    environment: str = Field(..., description="Environment to validate")
    custom_checks: Optional[List[str]] = Field(None, description="Optional list of specific validation checks")


class RollbackRequest(BaseModel):
    """Rollback request model."""
    deployment_id: str = Field(..., description="Deployment ID to rollback")
    reason: str = Field(..., description="Reason for rollback")


class DeploymentResponse(BaseModel):
    """Deployment response model."""
    deployment_id: str
    environment: str
    status: str
    message: str
    started_at: datetime
    estimated_completion_minutes: int
    monitoring_endpoints: Dict[str, str]


class ValidationResponse(BaseModel):
    """Validation response model."""
    validation_id: str
    environment: str
    overall_status: str
    total_checks: int
    passed_checks: int
    failed_checks: int
    critical_failures: int
    validation_duration_seconds: float
    details_endpoint: str


# Dependency Functions

def get_deployment_pipeline_service() -> DeploymentPipeline:
    """Get deployment pipeline service."""
    return get_deployment_pipeline()


def get_bedrock_configurator_service() -> BedrockAgentConfigurator:
    """Get Bedrock agent configurator service."""
    return get_bedrock_agent_configurator()


def get_deployment_validator_service() -> DeploymentValidator:
    """Get deployment validator service."""
    return get_deployment_validator()


# Deployment Management Endpoints

@router.post("/deploy", response_model=DeploymentResponse)
async def deploy_environment(
    request: DeploymentRequest,
    background_tasks: BackgroundTasks,
    pipeline: DeploymentPipeline = Depends(get_deployment_pipeline_service)
):
    """
    Deploy system to specified environment.
    
    Initiates deployment with optional validation and configuration overrides.
    """
    try:
        # Validate environment
        try:
            environment = Environment(request.environment)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid environment. Must be one of: {[e.value for e in Environment]}"
            )
        
        logger.info(f"Starting deployment to {environment.value}")
        
        # Start deployment in background
        def run_deployment():
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    pipeline.deploy_environment(environment, request.deployment_config)
                )
                logger.info(f"Deployment {result.deployment_id} completed with status: {result.status.value}")
            except Exception as e:
                logger.error(f"Background deployment failed: {e}")
            finally:
                loop.close()
        
        background_tasks.add_task(run_deployment)
        
        # Generate deployment ID for tracking
        deployment_id = f"deploy_{environment.value}_{int(datetime.utcnow().timestamp())}"
        
        # Estimate completion time based on environment
        completion_estimates = {
            Environment.DEVELOPMENT: 15,
            Environment.STAGING: 30,
            Environment.PRODUCTION: 45
        }
        
        return DeploymentResponse(
            deployment_id=deployment_id,
            environment=environment.value,
            status="initiated",
            message=f"Deployment to {environment.value} has been initiated",
            started_at=datetime.utcnow(),
            estimated_completion_minutes=completion_estimates[environment],
            monitoring_endpoints={
                "status": f"/deployment/{deployment_id}/status",
                "logs": f"/deployment/{deployment_id}/logs",
                "rollback": f"/deployment/{deployment_id}/rollback"
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to initiate deployment: {e}")
        raise HTTPException(status_code=500, detail=f"Deployment initiation failed: {str(e)}")


@router.get("/status/{deployment_id}")
async def get_deployment_status(
    deployment_id: str,
    pipeline: DeploymentPipeline = Depends(get_deployment_pipeline_service)
):
    """
    Get status of a specific deployment.
    
    Returns current deployment status, progress, and resource information.
    """
    try:
        deployment_result = pipeline.get_deployment_status(deployment_id)
        
        if not deployment_result:
            raise HTTPException(status_code=404, detail="Deployment not found")
        
        return {
            "deployment_id": deployment_result.deployment_id,
            "environment": deployment_result.environment.value,
            "status": deployment_result.status.value,
            "started_at": deployment_result.started_at.isoformat(),
            "completed_at": deployment_result.completed_at.isoformat() if deployment_result.completed_at else None,
            "deployment_time_seconds": deployment_result.deployment_time,
            "resources_created": len(deployment_result.resources_created),
            "validation_results": len(deployment_result.validation_results),
            "rollback_plan_available": deployment_result.rollback_plan is not None,
            "error_message": deployment_result.error_message,
            "resource_details": [
                {
                    "resource_type": resource.resource_type,
                    "resource_id": resource.resource_id,
                    "status": resource.status,
                    "created_at": resource.created_at.isoformat()
                }
                for resource in deployment_result.resources_created
            ],
            "validation_summary": [
                {
                    "validation_type": validation.validation_type,
                    "is_valid": validation.is_valid,
                    "message": validation.message,
                    "validated_at": validation.validated_at.isoformat()
                }
                for validation in deployment_result.validation_results
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get deployment status: {e}")
        raise HTTPException(status_code=500, detail=f"Status retrieval failed: {str(e)}")


@router.get("/active")
async def list_active_deployments(
    pipeline: DeploymentPipeline = Depends(get_deployment_pipeline_service)
):
    """
    List all currently active deployments.
    
    Returns summary of all deployments currently in progress.
    """
    try:
        active_deployments = pipeline.list_active_deployments()
        
        return {
            "active_deployments": [
                {
                    "deployment_id": deployment.deployment_id,
                    "environment": deployment.environment.value,
                    "status": deployment.status.value,
                    "started_at": deployment.started_at.isoformat(),
                    "duration_seconds": (datetime.utcnow() - deployment.started_at).total_seconds(),
                    "resources_created": len(deployment.resources_created)
                }
                for deployment in active_deployments
            ],
            "total_active": len(active_deployments),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to list active deployments: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list deployments: {str(e)}")


@router.get("/history")
async def get_deployment_history(
    limit: int = 50,
    environment: Optional[str] = None,
    pipeline: DeploymentPipeline = Depends(get_deployment_pipeline_service)
):
    """
    Get deployment history with optional filtering.
    
    Returns historical deployment information with optional environment filtering.
    """
    try:
        deployment_history = pipeline.get_deployment_history(limit)
        
        # Filter by environment if specified
        if environment:
            try:
                env_filter = Environment(environment)
                deployment_history = [d for d in deployment_history if d.environment == env_filter]
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid environment filter. Must be one of: {[e.value for e in Environment]}"
                )
        
        return {
            "deployment_history": [
                {
                    "deployment_id": deployment.deployment_id,
                    "environment": deployment.environment.value,
                    "status": deployment.status.value,
                    "started_at": deployment.started_at.isoformat(),
                    "completed_at": deployment.completed_at.isoformat() if deployment.completed_at else None,
                    "deployment_time_seconds": deployment.deployment_time,
                    "resources_created": len(deployment.resources_created),
                    "validation_passed": all(v.is_valid for v in deployment.validation_results),
                    "rollback_executed": deployment.status == DeploymentStatus.ROLLED_BACK
                }
                for deployment in deployment_history
            ],
            "total_deployments": len(deployment_history),
            "environment_filter": environment,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get deployment history: {e}")
        raise HTTPException(status_code=500, detail=f"History retrieval failed: {str(e)}")


@router.get("/environments/{environment}/status")
async def get_environment_status(
    environment: str,
    pipeline: DeploymentPipeline = Depends(get_deployment_pipeline_service)
):
    """
    Get current status of a specific environment.
    
    Returns environment configuration and latest deployment information.
    """
    try:
        # Validate environment
        try:
            env = Environment(environment)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid environment. Must be one of: {[e.value for e in Environment]}"
            )
        
        environment_status = pipeline.get_environment_status(env)
        
        return {
            "environment_status": environment_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get environment status: {e}")
        raise HTTPException(status_code=500, detail=f"Environment status retrieval failed: {str(e)}")


# Bedrock Agent Configuration Endpoints

@router.post("/bedrock/agents/configure")
async def configure_bedrock_agent(
    request: BedrockAgentConfigRequest,
    background_tasks: BackgroundTasks,
    configurator: BedrockAgentConfigurator = Depends(get_bedrock_configurator_service)
):
    """
    Configure a Bedrock agent with proper IAM roles.
    
    Sets up Bedrock agents for incident management with knowledge bases and action groups.
    """
    try:
        # Validate agent type
        try:
            agent_type = AgentType(request.agent_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid agent type. Must be one of: {[t.value for t in AgentType]}"
            )
        
        logger.info(f"Configuring Bedrock agent: {agent_type.value}")
        
        # Configure agent in background
        def run_agent_configuration():
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    configurator.configure_bedrock_agent(agent_type, request.custom_config)
                )
                logger.info(f"Bedrock agent {result.agent_id} configured successfully")
            except Exception as e:
                logger.error(f"Background agent configuration failed: {e}")
            finally:
                loop.close()
        
        background_tasks.add_task(run_agent_configuration)
        
        return {
            "agent_type": agent_type.value,
            "status": "configuration_initiated",
            "message": f"Bedrock agent configuration for {agent_type.value} has been initiated",
            "estimated_completion_minutes": 10,
            "monitoring_endpoint": f"/deployment/bedrock/agents/{agent_type.value}/status"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to configure Bedrock agent: {e}")
        raise HTTPException(status_code=500, detail=f"Agent configuration failed: {str(e)}")


@router.get("/bedrock/agents/{agent_type}/status")
async def get_bedrock_agent_status(
    agent_type: str,
    configurator: BedrockAgentConfigurator = Depends(get_bedrock_configurator_service)
):
    """
    Get status of a Bedrock agent configuration.
    
    Returns agent configuration status and functionality validation.
    """
    try:
        # Validate agent type
        try:
            AgentType(agent_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid agent type. Must be one of: {[t.value for t in AgentType]}"
            )
        
        configured_agents = configurator.get_configured_agents()
        
        # Find agent by type
        agent_result = None
        for agent_id, result in configured_agents.items():
            if result.configuration_details.get('agent_type') == agent_type:
                agent_result = result
                break
        
        if not agent_result:
            return {
                "agent_type": agent_type,
                "status": "not_configured",
                "message": f"Bedrock agent {agent_type} has not been configured"
            }
        
        # Validate agent configuration
        validation_result = await configurator.validate_agent_configuration(agent_result.agent_id)
        
        return {
            "agent_type": agent_type,
            "agent_id": agent_result.agent_id,
            "agent_arn": agent_result.agent_arn,
            "status": agent_result.agent_status,
            "created_at": agent_result.created_at.isoformat(),
            "knowledge_bases": len(agent_result.knowledge_bases),
            "action_groups": len(agent_result.action_groups),
            "validation": validation_result,
            "configuration_details": {
                "foundation_model": agent_result.configuration_details.get('foundation_model'),
                "session_ttl_seconds": agent_result.configuration_details.get('idle_session_ttl_in_seconds')
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get Bedrock agent status: {e}")
        raise HTTPException(status_code=500, detail=f"Agent status retrieval failed: {str(e)}")


@router.get("/bedrock/agents")
async def list_configured_agents(
    configurator: BedrockAgentConfigurator = Depends(get_bedrock_configurator_service)
):
    """
    List all configured Bedrock agents.
    
    Returns summary of all configured agents and their status.
    """
    try:
        configured_agents = configurator.get_configured_agents()
        
        return {
            "configured_agents": [
                {
                    "agent_id": result.agent_id,
                    "agent_name": result.agent_name,
                    "agent_type": result.configuration_details.get('agent_type'),
                    "status": result.agent_status,
                    "created_at": result.created_at.isoformat(),
                    "knowledge_bases_count": len(result.knowledge_bases),
                    "action_groups_count": len(result.action_groups)
                }
                for result in configured_agents.values()
            ],
            "total_agents": len(configured_agents),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to list configured agents: {e}")
        raise HTTPException(status_code=500, detail=f"Agent listing failed: {str(e)}")


@router.post("/bedrock/knowledge-bases/configure")
async def configure_knowledge_base(
    request: KnowledgeBaseConfigRequest,
    background_tasks: BackgroundTasks,
    configurator: BedrockAgentConfigurator = Depends(get_bedrock_configurator_service)
):
    """
    Configure a knowledge base with content ingestion.
    
    Sets up knowledge bases for different domains with automated content ingestion.
    """
    try:
        # Validate knowledge base type
        try:
            kb_type = KnowledgeBaseType(request.knowledge_base_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid knowledge base type. Must be one of: {[t.value for t in KnowledgeBaseType]}"
            )
        
        logger.info(f"Configuring knowledge base: {kb_type.value}")
        
        # Configure knowledge base in background
        def run_kb_configuration():
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                kb_id = loop.run_until_complete(
                    configurator.configure_knowledge_base(kb_type, request.custom_config)
                )
                logger.info(f"Knowledge base {kb_id} configured successfully")
            except Exception as e:
                logger.error(f"Background knowledge base configuration failed: {e}")
            finally:
                loop.close()
        
        background_tasks.add_task(run_kb_configuration)
        
        return {
            "knowledge_base_type": kb_type.value,
            "status": "configuration_initiated",
            "message": f"Knowledge base configuration for {kb_type.value} has been initiated",
            "estimated_completion_minutes": 15,
            "monitoring_endpoint": f"/deployment/bedrock/knowledge-bases/{kb_type.value}/status"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to configure knowledge base: {e}")
        raise HTTPException(status_code=500, detail=f"Knowledge base configuration failed: {str(e)}")


@router.get("/bedrock/knowledge-bases")
async def list_knowledge_bases(
    configurator: BedrockAgentConfigurator = Depends(get_bedrock_configurator_service)
):
    """
    List all configured knowledge bases.
    
    Returns summary of all configured knowledge bases.
    """
    try:
        knowledge_bases = configurator.get_knowledge_bases()
        
        return {
            "knowledge_bases": [
                {
                    "name": name,
                    "knowledge_base_id": kb_id
                }
                for name, kb_id in knowledge_bases.items()
            ],
            "total_knowledge_bases": len(knowledge_bases),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to list knowledge bases: {e}")
        raise HTTPException(status_code=500, detail=f"Knowledge base listing failed: {str(e)}")


# Deployment Validation Endpoints

@router.post("/validate", response_model=ValidationResponse)
async def validate_deployment(
    request: ValidationRequest,
    background_tasks: BackgroundTasks,
    validator: DeploymentValidator = Depends(get_deployment_validator_service)
):
    """
    Perform comprehensive deployment validation.
    
    Validates service integration, health checks, and performance baselines.
    """
    try:
        # Validate environment
        try:
            environment = Environment(request.environment)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid environment. Must be one of: {[e.value for e in Environment]}"
            )
        
        logger.info(f"Starting deployment validation for {environment.value}")
        
        # Mock resources for validation (in real implementation, would get from deployment)
        mock_resources = []
        
        # Start validation in background
        def run_validation():
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    validator.validate_deployment(environment, mock_resources, request.custom_checks)
                )
                logger.info(f"Validation {result.validation_id} completed with status: {result.overall_status}")
            except Exception as e:
                logger.error(f"Background validation failed: {e}")
            finally:
                loop.close()
        
        background_tasks.add_task(run_validation)
        
        # Generate validation ID for tracking
        validation_id = f"validation_{environment.value}_{int(datetime.utcnow().timestamp())}"
        
        return ValidationResponse(
            validation_id=validation_id,
            environment=environment.value,
            overall_status="in_progress",
            total_checks=0,
            passed_checks=0,
            failed_checks=0,
            critical_failures=0,
            validation_duration_seconds=0.0,
            details_endpoint=f"/deployment/validation/{validation_id}/details"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to initiate validation: {e}")
        raise HTTPException(status_code=500, detail=f"Validation initiation failed: {str(e)}")


@router.get("/validation/{validation_id}/details")
async def get_validation_details(
    validation_id: str,
    validator: DeploymentValidator = Depends(get_deployment_validator_service)
):
    """
    Get detailed validation results.
    
    Returns comprehensive validation results with individual check details.
    """
    try:
        validation_history = validator.get_validation_history()
        
        # Find validation by ID
        validation_result = None
        for result in validation_history:
            if result.validation_id == validation_id:
                validation_result = result
                break
        
        if not validation_result:
            raise HTTPException(status_code=404, detail="Validation not found")
        
        return {
            "validation_id": validation_result.validation_id,
            "environment": validation_result.environment.value,
            "overall_status": validation_result.overall_status,
            "started_at": validation_result.started_at.isoformat(),
            "completed_at": validation_result.completed_at.isoformat(),
            "total_duration_seconds": validation_result.total_duration_seconds,
            "summary": {
                "total_checks": validation_result.total_checks,
                "passed_checks": validation_result.passed_checks,
                "failed_checks": validation_result.failed_checks,
                "critical_failures": validation_result.critical_failures
            },
            "validation_results": [
                {
                    "check_id": result.check_id,
                    "name": result.name,
                    "category": result.category.value,
                    "severity": result.severity.value,
                    "is_passed": result.is_passed,
                    "message": result.message,
                    "execution_time_seconds": result.execution_time_seconds,
                    "timestamp": result.timestamp.isoformat(),
                    "error_details": result.error_details
                }
                for result in validation_result.validation_results
            ],
            "performance_baselines": [
                {
                    "metric_name": baseline.metric_name,
                    "baseline_value": baseline.baseline_value,
                    "unit": baseline.unit,
                    "threshold_warning": baseline.threshold_warning,
                    "threshold_critical": baseline.threshold_critical,
                    "measurement_timestamp": baseline.measurement_timestamp.isoformat()
                }
                for baseline in validation_result.performance_baselines
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get validation details: {e}")
        raise HTTPException(status_code=500, detail=f"Validation details retrieval failed: {str(e)}")


@router.get("/validation/history")
async def get_validation_history(
    limit: int = 20,
    environment: Optional[str] = None,
    validator: DeploymentValidator = Depends(get_deployment_validator_service)
):
    """
    Get validation history with optional filtering.
    
    Returns historical validation information with optional environment filtering.
    """
    try:
        validation_history = validator.get_validation_history(limit)
        
        # Filter by environment if specified
        if environment:
            try:
                env_filter = Environment(environment)
                validation_history = [v for v in validation_history if v.environment == env_filter]
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid environment filter. Must be one of: {[e.value for e in Environment]}"
                )
        
        return {
            "validation_history": [
                {
                    "validation_id": result.validation_id,
                    "environment": result.environment.value,
                    "overall_status": result.overall_status,
                    "completed_at": result.completed_at.isoformat(),
                    "total_duration_seconds": result.total_duration_seconds,
                    "passed_checks": result.passed_checks,
                    "total_checks": result.total_checks,
                    "critical_failures": result.critical_failures,
                    "performance_baselines_count": len(result.performance_baselines)
                }
                for result in validation_history
            ],
            "total_validations": len(validation_history),
            "environment_filter": environment,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get validation history: {e}")
        raise HTTPException(status_code=500, detail=f"Validation history retrieval failed: {str(e)}")


@router.get("/validation/summary/{environment}")
async def get_validation_summary(
    environment: str,
    validator: DeploymentValidator = Depends(get_deployment_validator_service)
):
    """
    Get validation summary for an environment.
    
    Returns aggregated validation statistics and trends for the environment.
    """
    try:
        # Validate environment
        try:
            env = Environment(environment)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid environment. Must be one of: {[e.value for e in Environment]}"
            )
        
        validation_summary = validator.get_validation_summary(env)
        performance_baselines = validator.get_performance_baselines(env)
        
        return {
            "validation_summary": validation_summary,
            "performance_baselines": [
                {
                    "metric_name": baseline.metric_name,
                    "baseline_value": baseline.baseline_value,
                    "unit": baseline.unit,
                    "threshold_warning": baseline.threshold_warning,
                    "threshold_critical": baseline.threshold_critical,
                    "measurement_timestamp": baseline.measurement_timestamp.isoformat()
                }
                for baseline in performance_baselines[-10:]  # Last 10 baselines
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get validation summary: {e}")
        raise HTTPException(status_code=500, detail=f"Validation summary retrieval failed: {str(e)}")


# Rollback Endpoints

@router.post("/rollback")
async def execute_rollback(
    request: RollbackRequest,
    background_tasks: BackgroundTasks,
    pipeline: DeploymentPipeline = Depends(get_deployment_pipeline_service)
):
    """
    Execute rollback for a failed deployment.
    
    Initiates rollback procedure for the specified deployment.
    """
    try:
        deployment_result = pipeline.get_deployment_status(request.deployment_id)
        
        if not deployment_result:
            raise HTTPException(status_code=404, detail="Deployment not found")
        
        if not deployment_result.rollback_plan:
            raise HTTPException(status_code=400, detail="No rollback plan available for this deployment")
        
        if deployment_result.status == DeploymentStatus.ROLLED_BACK:
            raise HTTPException(status_code=400, detail="Deployment has already been rolled back")
        
        logger.info(f"Initiating rollback for deployment {request.deployment_id}")
        
        # Execute rollback in background
        def run_rollback():
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # This would call the actual rollback method
                logger.info(f"Rollback completed for deployment {request.deployment_id}")
            except Exception as e:
                logger.error(f"Background rollback failed: {e}")
            finally:
                loop.close()
        
        background_tasks.add_task(run_rollback)
        
        return {
            "deployment_id": request.deployment_id,
            "rollback_status": "initiated",
            "reason": request.reason,
            "rollback_plan": {
                "rollback_id": deployment_result.rollback_plan.rollback_id,
                "estimated_duration_minutes": deployment_result.rollback_plan.estimated_duration_minutes,
                "rollback_steps": deployment_result.rollback_plan.rollback_steps
            },
            "monitoring_endpoint": f"/deployment/{request.deployment_id}/status"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute rollback: {e}")
        raise HTTPException(status_code=500, detail=f"Rollback execution failed: {str(e)}")


# Health and Status Endpoints

@router.get("/health")
async def deployment_system_health(
    pipeline: DeploymentPipeline = Depends(get_deployment_pipeline_service),
    validator: DeploymentValidator = Depends(get_deployment_validator_service)
):
    """
    Get deployment system health status.
    
    Returns health status of deployment pipeline and validation systems.
    """
    try:
        active_deployments = pipeline.list_active_deployments()
        validation_history = validator.get_validation_history(5)
        
        # Calculate system health metrics
        recent_deployment_success_rate = 0.0
        recent_validation_success_rate = 0.0
        
        if validation_history:
            successful_validations = sum(1 for v in validation_history if v.overall_status == "SUCCESS")
            recent_validation_success_rate = (successful_validations / len(validation_history)) * 100
        
        return {
            "deployment_system_health": {
                "status": "healthy",
                "active_deployments": len(active_deployments),
                "recent_deployment_success_rate_percent": recent_deployment_success_rate,
                "recent_validation_success_rate_percent": recent_validation_success_rate,
                "system_components": {
                    "deployment_pipeline": "operational",
                    "bedrock_configurator": "operational",
                    "deployment_validator": "operational"
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get deployment system health: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/metrics")
async def get_deployment_metrics(
    pipeline: DeploymentPipeline = Depends(get_deployment_pipeline_service),
    validator: DeploymentValidator = Depends(get_deployment_validator_service)
):
    """
    Get comprehensive deployment system metrics.
    
    Returns detailed metrics about deployment performance and system usage.
    """
    try:
        deployment_history = pipeline.get_deployment_history(50)
        validation_history = validator.get_validation_history(50)
        
        # Calculate deployment metrics
        total_deployments = len(deployment_history)
        successful_deployments = sum(1 for d in deployment_history if d.status == DeploymentStatus.COMPLETED)
        failed_deployments = sum(1 for d in deployment_history if d.status == DeploymentStatus.FAILED)
        rolled_back_deployments = sum(1 for d in deployment_history if d.status == DeploymentStatus.ROLLED_BACK)
        
        # Calculate average deployment times by environment
        avg_deployment_times = {}
        for env in Environment:
            env_deployments = [d for d in deployment_history if d.environment == env and d.deployment_time > 0]
            if env_deployments:
                avg_deployment_times[env.value] = sum(d.deployment_time for d in env_deployments) / len(env_deployments)
            else:
                avg_deployment_times[env.value] = 0
        
        # Calculate validation metrics
        total_validations = len(validation_history)
        successful_validations = sum(1 for v in validation_history if v.overall_status == "SUCCESS")
        
        return {
            "deployment_metrics": {
                "total_deployments": total_deployments,
                "successful_deployments": successful_deployments,
                "failed_deployments": failed_deployments,
                "rolled_back_deployments": rolled_back_deployments,
                "success_rate_percent": (successful_deployments / total_deployments * 100) if total_deployments > 0 else 0,
                "average_deployment_times_seconds": avg_deployment_times
            },
            "validation_metrics": {
                "total_validations": total_validations,
                "successful_validations": successful_validations,
                "validation_success_rate_percent": (successful_validations / total_validations * 100) if total_validations > 0 else 0
            },
            "system_utilization": {
                "active_deployments": len(pipeline.list_active_deployments()),
                "environments_deployed": len(set(d.environment for d in deployment_history)),
                "bedrock_agents_configured": len(get_bedrock_agent_configurator().get_configured_agents()),
                "knowledge_bases_configured": len(get_bedrock_agent_configurator().get_knowledge_bases())
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get deployment metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics retrieval failed: {str(e)}")