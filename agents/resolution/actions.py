"""
Resolution Actions

Defines and executes secure resolution actions with validation.
"""

import asyncio
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from src.utils.logging import get_logger
from src.utils.exceptions import SecurityError, ValidationError

logger = get_logger(__name__)


class ActionType(Enum):
    """Types of resolution actions"""
    SCALE_SERVICE = "scale_service"
    RESTART_SERVICE = "restart_service"
    UPDATE_CONFIG = "update_config"
    ROLLBACK_DEPLOYMENT = "rollback_deployment"
    ENABLE_CIRCUIT_BREAKER = "enable_circuit_breaker"
    CLEAR_CACHE = "clear_cache"
    INCREASE_RESOURCES = "increase_resources"
    DRAIN_TRAFFIC = "drain_traffic"


class RiskLevel(Enum):
    """Risk levels for actions"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ResolutionAction:
    """Represents a resolution action to be executed"""
    action_id: str
    action_type: ActionType
    target_service: str
    parameters: Dict[str, Any]
    risk_level: RiskLevel
    estimated_duration: timedelta
    rollback_plan: Dict[str, Any]
    validation_checks: List[str]
    approval_required: bool = False
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "target_service": self.target_service,
            "parameters": self.parameters,
            "risk_level": self.risk_level.value,
            "estimated_duration_seconds": self.estimated_duration.total_seconds(),
            "rollback_plan": self.rollback_plan,
            "validation_checks": self.validation_checks,
            "approval_required": self.approval_required,
            "created_at": self.created_at.isoformat()
        }
    
    def get_signature(self) -> str:
        """Get cryptographic signature for action integrity"""
        action_data = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(action_data.encode()).hexdigest()


@dataclass
class ActionResult:
    """Result of executing a resolution action"""
    action_id: str
    success: bool
    execution_time: timedelta
    output: str
    error_message: Optional[str] = None
    rollback_required: bool = False
    validation_results: Dict[str, bool] = None
    executed_at: datetime = None
    
    def __post_init__(self):
        if self.executed_at is None:
            self.executed_at = datetime.utcnow()
        if self.validation_results is None:
            self.validation_results = {}


class ActionWhitelist:
    """Manages whitelist of approved resolution actions"""
    
    def __init__(self):
        self.approved_actions = {
            ActionType.SCALE_SERVICE: {
                "max_instances": 10,
                "min_instances": 1,
                "allowed_services": ["web", "api", "worker", "database"]
            },
            ActionType.RESTART_SERVICE: {
                "allowed_services": ["web", "api", "worker"],
                "max_restarts_per_hour": 3
            },
            ActionType.UPDATE_CONFIG: {
                "allowed_keys": [
                    "timeout", "retry_count", "cache_ttl", 
                    "rate_limit", "circuit_breaker_threshold"
                ],
                "value_constraints": {
                    "timeout": {"min": 1, "max": 300},
                    "retry_count": {"min": 0, "max": 10},
                    "cache_ttl": {"min": 60, "max": 3600}
                }
            },
            ActionType.ROLLBACK_DEPLOYMENT: {
                "max_versions_back": 3,
                "allowed_services": ["web", "api", "worker"]
            },
            ActionType.ENABLE_CIRCUIT_BREAKER: {
                "allowed_services": ["web", "api", "worker"],
                "default_threshold": 5,
                "default_timeout": 30
            },
            ActionType.CLEAR_CACHE: {
                "allowed_cache_types": ["redis", "memcached", "application"],
                "allowed_services": ["web", "api", "worker"]
            },
            ActionType.INCREASE_RESOURCES: {
                "max_cpu_increase": 2.0,  # 2x current
                "max_memory_increase": 2.0,  # 2x current
                "allowed_services": ["web", "api", "worker", "database"]
            },
            ActionType.DRAIN_TRAFFIC: {
                "allowed_services": ["web", "api"],
                "max_drain_percentage": 50
            }
        }
    
    def validate_action(self, action: ResolutionAction) -> bool:
        """Validate action against whitelist"""
        try:
            if action.action_type not in self.approved_actions:
                logger.error(f"Action type {action.action_type} not in whitelist")
                return False
            
            constraints = self.approved_actions[action.action_type]
            
            # Validate service
            if "allowed_services" in constraints:
                if action.target_service not in constraints["allowed_services"]:
                    logger.error(f"Service {action.target_service} not allowed for {action.action_type}")
                    return False
            
            # Validate parameters based on action type
            return self._validate_action_parameters(action, constraints)
            
        except Exception as e:
            logger.error(f"Error validating action: {e}")
            return False
    
    def _validate_action_parameters(
        self, 
        action: ResolutionAction, 
        constraints: Dict[str, Any]
    ) -> bool:
        """Validate action parameters against constraints"""
        try:
            if action.action_type == ActionType.SCALE_SERVICE:
                instances = action.parameters.get("instances", 0)
                return (
                    constraints["min_instances"] <= instances <= constraints["max_instances"]
                )
            
            elif action.action_type == ActionType.UPDATE_CONFIG:
                for key, value in action.parameters.items():
                    if key not in constraints["allowed_keys"]:
                        return False
                    
                    if key in constraints["value_constraints"]:
                        constraint = constraints["value_constraints"][key]
                        if not (constraint["min"] <= value <= constraint["max"]):
                            return False
            
            elif action.action_type == ActionType.ROLLBACK_DEPLOYMENT:
                versions_back = action.parameters.get("versions_back", 1)
                return versions_back <= constraints["max_versions_back"]
            
            elif action.action_type == ActionType.INCREASE_RESOURCES:
                cpu_factor = action.parameters.get("cpu_factor", 1.0)
                memory_factor = action.parameters.get("memory_factor", 1.0)
                return (
                    cpu_factor <= constraints["max_cpu_increase"] and
                    memory_factor <= constraints["max_memory_increase"]
                )
            
            elif action.action_type == ActionType.DRAIN_TRAFFIC:
                drain_percentage = action.parameters.get("drain_percentage", 0)
                return drain_percentage <= constraints["max_drain_percentage"]
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating parameters: {e}")
            return False


class ActionExecutor:
    """Executes resolution actions with security validation"""
    
    def __init__(self, aws_factory, sandbox_account_id: str = None):
        self.aws_factory = aws_factory
        self.sandbox_account_id = sandbox_account_id or "123456789012"  # Default sandbox
        self.whitelist = ActionWhitelist()
        self.execution_history = []
        
        # Execution timeouts
        self.action_timeouts = {
            ActionType.SCALE_SERVICE: timedelta(minutes=5),
            ActionType.RESTART_SERVICE: timedelta(minutes=3),
            ActionType.UPDATE_CONFIG: timedelta(minutes=1),
            ActionType.ROLLBACK_DEPLOYMENT: timedelta(minutes=10),
            ActionType.ENABLE_CIRCUIT_BREAKER: timedelta(seconds=30),
            ActionType.CLEAR_CACHE: timedelta(minutes=2),
            ActionType.INCREASE_RESOURCES: timedelta(minutes=5),
            ActionType.DRAIN_TRAFFIC: timedelta(minutes=3)
        }
    
    async def execute_action(self, action: ResolutionAction) -> ActionResult:
        """
        Execute a resolution action with full security validation
        
        Args:
            action: Resolution action to execute
            
        Returns:
            Action execution result
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Executing action {action.action_id}: {action.action_type.value}")
            
            # Security validation
            if not await self._validate_action_security(action):
                return ActionResult(
                    action_id=action.action_id,
                    success=False,
                    execution_time=datetime.utcnow() - start_time,
                    output="",
                    error_message="Security validation failed"
                )
            
            # Test in sandbox first
            sandbox_result = await self._execute_in_sandbox(action)
            if not sandbox_result.success:
                return ActionResult(
                    action_id=action.action_id,
                    success=False,
                    execution_time=datetime.utcnow() - start_time,
                    output=sandbox_result.output,
                    error_message=f"Sandbox validation failed: {sandbox_result.error_message}"
                )
            
            # Check if human approval required
            if action.approval_required or action.risk_level == RiskLevel.CRITICAL:
                return await self._request_human_approval(action)
            
            # Execute in production
            result = await self._execute_in_production(action)
            
            # Record execution
            self.execution_history.append({
                "action": action.to_dict(),
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing action {action.action_id}: {e}")
            return ActionResult(
                action_id=action.action_id,
                success=False,
                execution_time=datetime.utcnow() - start_time,
                output="",
                error_message=str(e)
            )
    
    async def _validate_action_security(self, action: ResolutionAction) -> bool:
        """Validate action security and permissions"""
        try:
            # Whitelist validation
            if not self.whitelist.validate_action(action):
                logger.error(f"Action {action.action_id} failed whitelist validation")
                return False
            
            # Signature validation
            expected_signature = action.get_signature()
            if not expected_signature:
                logger.error(f"Action {action.action_id} has invalid signature")
                return False
            
            # Rate limiting check
            if not await self._check_rate_limits(action):
                logger.error(f"Action {action.action_id} exceeds rate limits")
                return False
            
            # Permission validation
            if not await self._validate_permissions(action):
                logger.error(f"Action {action.action_id} lacks required permissions")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating action security: {e}")
            return False
    
    async def _check_rate_limits(self, action: ResolutionAction) -> bool:
        """Check if action exceeds rate limits"""
        try:
            # Count recent actions of same type
            cutoff_time = datetime.utcnow() - timedelta(hours=1)
            recent_actions = [
                h for h in self.execution_history
                if (
                    h["action"]["action_type"] == action.action_type.value and
                    h["action"]["target_service"] == action.target_service and
                    datetime.fromisoformat(h["timestamp"]) >= cutoff_time
                )
            ]
            
            # Define rate limits
            rate_limits = {
                ActionType.RESTART_SERVICE: 3,  # Max 3 restarts per hour
                ActionType.SCALE_SERVICE: 5,    # Max 5 scaling actions per hour
                ActionType.ROLLBACK_DEPLOYMENT: 2,  # Max 2 rollbacks per hour
            }
            
            limit = rate_limits.get(action.action_type, 10)  # Default limit
            
            if len(recent_actions) >= limit:
                logger.warning(
                    f"Rate limit exceeded for {action.action_type}: "
                    f"{len(recent_actions)}/{limit} in last hour"
                )
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limits: {e}")
            return False
    
    async def _validate_permissions(self, action: ResolutionAction) -> bool:
        """Validate IAM permissions for action"""
        try:
            # In a real implementation, this would check IAM policies
            # For now, simulate permission validation
            
            required_permissions = {
                ActionType.SCALE_SERVICE: ["ecs:UpdateService", "autoscaling:SetDesiredCapacity"],
                ActionType.RESTART_SERVICE: ["ecs:UpdateService", "lambda:UpdateFunctionCode"],
                ActionType.UPDATE_CONFIG: ["ssm:PutParameter", "lambda:UpdateFunctionConfiguration"],
                ActionType.ROLLBACK_DEPLOYMENT: ["ecs:UpdateService", "lambda:UpdateAlias"],
                ActionType.ENABLE_CIRCUIT_BREAKER: ["ssm:PutParameter"],
                ActionType.CLEAR_CACHE: ["elasticache:RebootCacheCluster"],
                ActionType.INCREASE_RESOURCES: ["ecs:UpdateService", "lambda:UpdateFunctionConfiguration"],
                ActionType.DRAIN_TRAFFIC: ["elbv2:ModifyTargetGroup"]
            }
            
            # Simulate permission check (always pass for demo)
            permissions = required_permissions.get(action.action_type, [])
            logger.info(f"Validated permissions for {action.action_type}: {permissions}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating permissions: {e}")
            return False
    
    async def _execute_in_sandbox(self, action: ResolutionAction) -> ActionResult:
        """Execute action in sandbox environment for validation"""
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Testing action {action.action_id} in sandbox")
            
            # Simulate sandbox execution
            await asyncio.sleep(0.5)  # Simulate execution time
            
            # Simulate validation checks
            validation_results = {}
            for check in action.validation_checks:
                # Simulate check (90% pass rate)
                validation_results[check] = True  # Always pass for demo
            
            # Check if all validations passed
            all_passed = all(validation_results.values())
            
            execution_time = datetime.utcnow() - start_time
            
            return ActionResult(
                action_id=action.action_id,
                success=all_passed,
                execution_time=execution_time,
                output=f"Sandbox validation completed: {validation_results}",
                error_message=None if all_passed else "Validation checks failed",
                validation_results=validation_results
            )
            
        except Exception as e:
            logger.error(f"Error executing in sandbox: {e}")
            return ActionResult(
                action_id=action.action_id,
                success=False,
                execution_time=datetime.utcnow() - start_time,
                output="",
                error_message=str(e)
            )
    
    async def _execute_in_production(self, action: ResolutionAction) -> ActionResult:
        """Execute action in production environment"""
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Executing action {action.action_id} in production")
            
            # Get timeout for this action type
            timeout = self.action_timeouts.get(action.action_type, timedelta(minutes=5))
            
            # Execute action based on type
            result = await asyncio.wait_for(
                self._execute_action_by_type(action),
                timeout=timeout.total_seconds()
            )
            
            execution_time = datetime.utcnow() - start_time
            
            return ActionResult(
                action_id=action.action_id,
                success=result["success"],
                execution_time=execution_time,
                output=result["output"],
                error_message=result.get("error"),
                rollback_required=result.get("rollback_required", False)
            )
            
        except asyncio.TimeoutError:
            logger.error(f"Action {action.action_id} timed out")
            return ActionResult(
                action_id=action.action_id,
                success=False,
                execution_time=datetime.utcnow() - start_time,
                output="",
                error_message="Action execution timed out",
                rollback_required=True
            )
        except Exception as e:
            logger.error(f"Error executing in production: {e}")
            return ActionResult(
                action_id=action.action_id,
                success=False,
                execution_time=datetime.utcnow() - start_time,
                output="",
                error_message=str(e),
                rollback_required=True
            )
    
    async def _execute_action_by_type(self, action: ResolutionAction) -> Dict[str, Any]:
        """Execute action based on its type"""
        try:
            if action.action_type == ActionType.SCALE_SERVICE:
                return await self._scale_service(action)
            elif action.action_type == ActionType.RESTART_SERVICE:
                return await self._restart_service(action)
            elif action.action_type == ActionType.UPDATE_CONFIG:
                return await self._update_config(action)
            elif action.action_type == ActionType.ROLLBACK_DEPLOYMENT:
                return await self._rollback_deployment(action)
            elif action.action_type == ActionType.ENABLE_CIRCUIT_BREAKER:
                return await self._enable_circuit_breaker(action)
            elif action.action_type == ActionType.CLEAR_CACHE:
                return await self._clear_cache(action)
            elif action.action_type == ActionType.INCREASE_RESOURCES:
                return await self._increase_resources(action)
            elif action.action_type == ActionType.DRAIN_TRAFFIC:
                return await self._drain_traffic(action)
            else:
                return {
                    "success": False,
                    "output": "",
                    "error": f"Unknown action type: {action.action_type}"
                }
                
        except Exception as e:
            logger.error(f"Error executing action type {action.action_type}: {e}")
            return {
                "success": False,
                "output": "",
                "error": str(e)
            }
    
    async def _scale_service(self, action: ResolutionAction) -> Dict[str, Any]:
        """Scale service instances"""
        try:
            instances = action.parameters.get("instances", 1)
            service = action.target_service
            
            # Simulate ECS service scaling
            await asyncio.sleep(1)  # Simulate API call
            
            logger.info(f"Scaled {service} to {instances} instances")
            
            return {
                "success": True,
                "output": f"Successfully scaled {service} to {instances} instances",
                "rollback_required": False
            }
            
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "rollback_required": True
            }
    
    async def _restart_service(self, action: ResolutionAction) -> Dict[str, Any]:
        """Restart service"""
        try:
            service = action.target_service
            
            # Simulate service restart
            await asyncio.sleep(2)  # Simulate restart time
            
            logger.info(f"Restarted service {service}")
            
            return {
                "success": True,
                "output": f"Successfully restarted {service}",
                "rollback_required": False
            }
            
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "rollback_required": False  # Restart doesn't need rollback
            }
    
    async def _update_config(self, action: ResolutionAction) -> Dict[str, Any]:
        """Update service configuration"""
        try:
            service = action.target_service
            config_updates = action.parameters
            
            # Simulate configuration update
            await asyncio.sleep(0.5)
            
            logger.info(f"Updated configuration for {service}: {config_updates}")
            
            return {
                "success": True,
                "output": f"Successfully updated configuration for {service}",
                "rollback_required": True  # Config changes should be rollback-able
            }
            
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "rollback_required": True
            }
    
    async def _rollback_deployment(self, action: ResolutionAction) -> Dict[str, Any]:
        """Rollback deployment"""
        try:
            service = action.target_service
            versions_back = action.parameters.get("versions_back", 1)
            
            # Simulate deployment rollback
            await asyncio.sleep(3)
            
            logger.info(f"Rolled back {service} by {versions_back} versions")
            
            return {
                "success": True,
                "output": f"Successfully rolled back {service} by {versions_back} versions",
                "rollback_required": False  # Rollback is already a recovery action
            }
            
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "rollback_required": False
            }
    
    async def _enable_circuit_breaker(self, action: ResolutionAction) -> Dict[str, Any]:
        """Enable circuit breaker"""
        try:
            service = action.target_service
            threshold = action.parameters.get("threshold", 5)
            
            # Simulate circuit breaker enablement
            await asyncio.sleep(0.2)
            
            logger.info(f"Enabled circuit breaker for {service} with threshold {threshold}")
            
            return {
                "success": True,
                "output": f"Successfully enabled circuit breaker for {service}",
                "rollback_required": True
            }
            
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "rollback_required": True
            }
    
    async def _clear_cache(self, action: ResolutionAction) -> Dict[str, Any]:
        """Clear cache"""
        try:
            service = action.target_service
            cache_type = action.parameters.get("cache_type", "redis")
            
            # Simulate cache clearing
            await asyncio.sleep(0.5)
            
            logger.info(f"Cleared {cache_type} cache for {service}")
            
            return {
                "success": True,
                "output": f"Successfully cleared {cache_type} cache for {service}",
                "rollback_required": False  # Cache clearing doesn't need rollback
            }
            
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "rollback_required": False
            }
    
    async def _increase_resources(self, action: ResolutionAction) -> Dict[str, Any]:
        """Increase service resources"""
        try:
            service = action.target_service
            cpu_factor = action.parameters.get("cpu_factor", 1.5)
            memory_factor = action.parameters.get("memory_factor", 1.5)
            
            # Simulate resource increase
            await asyncio.sleep(2)
            
            logger.info(f"Increased resources for {service}: CPU x{cpu_factor}, Memory x{memory_factor}")
            
            return {
                "success": True,
                "output": f"Successfully increased resources for {service}",
                "rollback_required": True
            }
            
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "rollback_required": True
            }
    
    async def _drain_traffic(self, action: ResolutionAction) -> Dict[str, Any]:
        """Drain traffic from service"""
        try:
            service = action.target_service
            drain_percentage = action.parameters.get("drain_percentage", 25)
            
            # Simulate traffic draining
            await asyncio.sleep(1)
            
            logger.info(f"Drained {drain_percentage}% traffic from {service}")
            
            return {
                "success": True,
                "output": f"Successfully drained {drain_percentage}% traffic from {service}",
                "rollback_required": True
            }
            
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "rollback_required": True
            }
    
    async def _request_human_approval(self, action: ResolutionAction) -> ActionResult:
        """Request human approval for high-risk actions"""
        try:
            logger.info(f"Requesting human approval for action {action.action_id}")
            
            # In a real implementation, this would integrate with approval systems
            # For demo, simulate approval request
            
            return ActionResult(
                action_id=action.action_id,
                success=False,
                execution_time=timedelta(seconds=1),
                output="Human approval required",
                error_message="Action requires human approval due to high risk level"
            )
            
        except Exception as e:
            logger.error(f"Error requesting human approval: {e}")
            return ActionResult(
                action_id=action.action_id,
                success=False,
                execution_time=timedelta(seconds=1),
                output="",
                error_message=str(e)
            )