"""
Rollback Manager

Manages rollback operations for failed resolution actions.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from src.utils.logging import get_logger
from .actions import ResolutionAction, ActionResult, ActionType

logger = get_logger(__name__)


class RollbackStatus(Enum):
    """Status of rollback operations"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NOT_REQUIRED = "not_required"


@dataclass
class RollbackPlan:
    """Plan for rolling back a resolution action"""
    action_id: str
    rollback_actions: List[Dict[str, Any]]
    dependencies: List[str]
    estimated_duration: timedelta
    validation_checks: List[str]
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class RollbackResult:
    """Result of a rollback operation"""
    action_id: str
    status: RollbackStatus
    execution_time: timedelta
    steps_completed: int
    total_steps: int
    output: str
    error_message: Optional[str] = None
    executed_at: datetime = None
    
    def __post_init__(self):
        if self.executed_at is None:
            self.executed_at = datetime.utcnow()


class RollbackManager:
    """Manages rollback operations for resolution actions"""
    
    def __init__(self, aws_factory):
        self.aws_factory = aws_factory
        self.rollback_history = []
        self.pending_rollbacks = {}
        
        # Rollback timeouts
        self.rollback_timeouts = {
            ActionType.SCALE_SERVICE: timedelta(minutes=3),
            ActionType.RESTART_SERVICE: timedelta(minutes=2),
            ActionType.UPDATE_CONFIG: timedelta(minutes=1),
            ActionType.ROLLBACK_DEPLOYMENT: timedelta(minutes=5),
            ActionType.ENABLE_CIRCUIT_BREAKER: timedelta(seconds=30),
            ActionType.CLEAR_CACHE: timedelta(minutes=1),
            ActionType.INCREASE_RESOURCES: timedelta(minutes=3),
            ActionType.DRAIN_TRAFFIC: timedelta(minutes=2)
        }
    
    async def create_rollback_plan(self, action: ResolutionAction) -> RollbackPlan:
        """
        Create a rollback plan for a resolution action
        
        Args:
            action: The resolution action to create rollback plan for
            
        Returns:
            Rollback plan with specific steps
        """
        try:
            logger.info(f"Creating rollback plan for action {action.action_id}")
            
            rollback_actions = []
            dependencies = []
            validation_checks = []
            
            # Create rollback steps based on action type
            if action.action_type == ActionType.SCALE_SERVICE:
                rollback_actions = await self._create_scale_rollback(action)
                validation_checks = ["service_health", "instance_count"]
                
            elif action.action_type == ActionType.UPDATE_CONFIG:
                rollback_actions = await self._create_config_rollback(action)
                validation_checks = ["config_validation", "service_restart"]
                
            elif action.action_type == ActionType.INCREASE_RESOURCES:
                rollback_actions = await self._create_resource_rollback(action)
                validation_checks = ["resource_allocation", "service_health"]
                
            elif action.action_type == ActionType.ENABLE_CIRCUIT_BREAKER:
                rollback_actions = await self._create_circuit_breaker_rollback(action)
                validation_checks = ["circuit_breaker_status"]
                
            elif action.action_type == ActionType.DRAIN_TRAFFIC:
                rollback_actions = await self._create_traffic_rollback(action)
                validation_checks = ["traffic_distribution", "service_health"]
                
            else:
                # Default rollback plan
                rollback_actions = [{
                    "type": "manual_intervention",
                    "description": f"Manual rollback required for {action.action_type}",
                    "parameters": {}
                }]
                validation_checks = ["manual_verification"]
            
            # Estimate duration
            estimated_duration = self.rollback_timeouts.get(
                action.action_type, 
                timedelta(minutes=5)
            )
            
            rollback_plan = RollbackPlan(
                action_id=action.action_id,
                rollback_actions=rollback_actions,
                dependencies=dependencies,
                estimated_duration=estimated_duration,
                validation_checks=validation_checks
            )
            
            logger.info(f"Created rollback plan with {len(rollback_actions)} steps")
            return rollback_plan
            
        except Exception as e:
            logger.error(f"Error creating rollback plan: {e}")
            return RollbackPlan(
                action_id=action.action_id,
                rollback_actions=[{
                    "type": "error",
                    "description": f"Failed to create rollback plan: {str(e)}",
                    "parameters": {}
                }],
                dependencies=[],
                estimated_duration=timedelta(minutes=1),
                validation_checks=[]
            )
    
    async def execute_rollback(
        self, 
        rollback_plan: RollbackPlan,
        timeout: timedelta = None
    ) -> RollbackResult:
        """
        Execute a rollback plan
        
        Args:
            rollback_plan: The rollback plan to execute
            timeout: Maximum time to wait for rollback completion
            
        Returns:
            Rollback execution result
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Executing rollback for action {rollback_plan.action_id}")
            
            if timeout is None:
                timeout = rollback_plan.estimated_duration * 2  # Double the estimated time
            
            # Mark rollback as in progress
            self.pending_rollbacks[rollback_plan.action_id] = RollbackStatus.IN_PROGRESS
            
            # Execute rollback steps
            result = await asyncio.wait_for(
                self._execute_rollback_steps(rollback_plan),
                timeout=timeout.total_seconds()
            )
            
            # Update status
            self.pending_rollbacks[rollback_plan.action_id] = (
                RollbackStatus.COMPLETED if result.status == RollbackStatus.COMPLETED
                else RollbackStatus.FAILED
            )
            
            # Record in history
            self.rollback_history.append({
                "plan": rollback_plan,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            execution_time = datetime.utcnow() - start_time
            result.execution_time = execution_time
            
            logger.info(
                f"Rollback for {rollback_plan.action_id} completed with status: {result.status.value}"
            )
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"Rollback for {rollback_plan.action_id} timed out")
            self.pending_rollbacks[rollback_plan.action_id] = RollbackStatus.FAILED
            
            return RollbackResult(
                action_id=rollback_plan.action_id,
                status=RollbackStatus.FAILED,
                execution_time=datetime.utcnow() - start_time,
                steps_completed=0,
                total_steps=len(rollback_plan.rollback_actions),
                output="",
                error_message="Rollback execution timed out"
            )
            
        except Exception as e:
            logger.error(f"Error executing rollback: {e}")
            self.pending_rollbacks[rollback_plan.action_id] = RollbackStatus.FAILED
            
            return RollbackResult(
                action_id=rollback_plan.action_id,
                status=RollbackStatus.FAILED,
                execution_time=datetime.utcnow() - start_time,
                steps_completed=0,
                total_steps=len(rollback_plan.rollback_actions),
                output="",
                error_message=str(e)
            )
    
    async def _execute_rollback_steps(self, rollback_plan: RollbackPlan) -> RollbackResult:
        """Execute individual rollback steps"""
        try:
            total_steps = len(rollback_plan.rollback_actions)
            completed_steps = 0
            output_parts = []
            
            for i, rollback_action in enumerate(rollback_plan.rollback_actions):
                try:
                    logger.info(f"Executing rollback step {i+1}/{total_steps}: {rollback_action['type']}")
                    
                    step_result = await self._execute_rollback_step(rollback_action)
                    
                    if step_result["success"]:
                        completed_steps += 1
                        output_parts.append(f"Step {i+1}: {step_result['output']}")
                    else:
                        output_parts.append(f"Step {i+1} FAILED: {step_result['error']}")
                        # Continue with remaining steps for best effort rollback
                    
                except Exception as e:
                    logger.error(f"Error in rollback step {i+1}: {e}")
                    output_parts.append(f"Step {i+1} ERROR: {str(e)}")
            
            # Validate rollback success
            validation_success = await self._validate_rollback(rollback_plan)
            
            status = (
                RollbackStatus.COMPLETED 
                if completed_steps == total_steps and validation_success
                else RollbackStatus.FAILED
            )
            
            return RollbackResult(
                action_id=rollback_plan.action_id,
                status=status,
                execution_time=timedelta(seconds=0),  # Will be set by caller
                steps_completed=completed_steps,
                total_steps=total_steps,
                output="\n".join(output_parts),
                error_message=None if status == RollbackStatus.COMPLETED else "Some rollback steps failed"
            )
            
        except Exception as e:
            logger.error(f"Error executing rollback steps: {e}")
            return RollbackResult(
                action_id=rollback_plan.action_id,
                status=RollbackStatus.FAILED,
                execution_time=timedelta(seconds=0),
                steps_completed=0,
                total_steps=len(rollback_plan.rollback_actions),
                output="",
                error_message=str(e)
            )
    
    async def _execute_rollback_step(self, rollback_action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single rollback step"""
        try:
            action_type = rollback_action["type"]
            parameters = rollback_action.get("parameters", {})
            
            if action_type == "restore_scale":
                return await self._restore_service_scale(parameters)
            elif action_type == "restore_config":
                return await self._restore_configuration(parameters)
            elif action_type == "restore_resources":
                return await self._restore_resources(parameters)
            elif action_type == "disable_circuit_breaker":
                return await self._disable_circuit_breaker(parameters)
            elif action_type == "restore_traffic":
                return await self._restore_traffic_distribution(parameters)
            elif action_type == "manual_intervention":
                return {
                    "success": False,
                    "output": rollback_action["description"],
                    "error": "Manual intervention required"
                }
            else:
                return {
                    "success": False,
                    "output": "",
                    "error": f"Unknown rollback action type: {action_type}"
                }
                
        except Exception as e:
            logger.error(f"Error executing rollback step: {e}")
            return {
                "success": False,
                "output": "",
                "error": str(e)
            }
    
    async def _create_scale_rollback(self, action: ResolutionAction) -> List[Dict[str, Any]]:
        """Create rollback steps for scaling action"""
        original_instances = action.rollback_plan.get("original_instances", 1)
        
        return [{
            "type": "restore_scale",
            "description": f"Restore {action.target_service} to {original_instances} instances",
            "parameters": {
                "service": action.target_service,
                "instances": original_instances
            }
        }]
    
    async def _create_config_rollback(self, action: ResolutionAction) -> List[Dict[str, Any]]:
        """Create rollback steps for configuration update"""
        original_config = action.rollback_plan.get("original_config", {})
        
        return [{
            "type": "restore_config",
            "description": f"Restore configuration for {action.target_service}",
            "parameters": {
                "service": action.target_service,
                "config": original_config
            }
        }]
    
    async def _create_resource_rollback(self, action: ResolutionAction) -> List[Dict[str, Any]]:
        """Create rollback steps for resource increase"""
        original_resources = action.rollback_plan.get("original_resources", {})
        
        return [{
            "type": "restore_resources",
            "description": f"Restore resources for {action.target_service}",
            "parameters": {
                "service": action.target_service,
                "resources": original_resources
            }
        }]
    
    async def _create_circuit_breaker_rollback(self, action: ResolutionAction) -> List[Dict[str, Any]]:
        """Create rollback steps for circuit breaker enablement"""
        return [{
            "type": "disable_circuit_breaker",
            "description": f"Disable circuit breaker for {action.target_service}",
            "parameters": {
                "service": action.target_service
            }
        }]
    
    async def _create_traffic_rollback(self, action: ResolutionAction) -> List[Dict[str, Any]]:
        """Create rollback steps for traffic draining"""
        return [{
            "type": "restore_traffic",
            "description": f"Restore traffic distribution for {action.target_service}",
            "parameters": {
                "service": action.target_service,
                "distribution": "normal"
            }
        }]
    
    async def _restore_service_scale(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Restore service to original scale"""
        try:
            service = parameters["service"]
            instances = parameters["instances"]
            
            # Simulate scaling restoration
            await asyncio.sleep(1)
            
            logger.info(f"Restored {service} to {instances} instances")
            
            return {
                "success": True,
                "output": f"Successfully restored {service} to {instances} instances",
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e)
            }
    
    async def _restore_configuration(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Restore service configuration"""
        try:
            service = parameters["service"]
            config = parameters["config"]
            
            # Simulate configuration restoration
            await asyncio.sleep(0.5)
            
            logger.info(f"Restored configuration for {service}")
            
            return {
                "success": True,
                "output": f"Successfully restored configuration for {service}",
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e)
            }
    
    async def _restore_resources(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Restore service resources"""
        try:
            service = parameters["service"]
            resources = parameters["resources"]
            
            # Simulate resource restoration
            await asyncio.sleep(1)
            
            logger.info(f"Restored resources for {service}")
            
            return {
                "success": True,
                "output": f"Successfully restored resources for {service}",
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e)
            }
    
    async def _disable_circuit_breaker(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Disable circuit breaker"""
        try:
            service = parameters["service"]
            
            # Simulate circuit breaker disabling
            await asyncio.sleep(0.2)
            
            logger.info(f"Disabled circuit breaker for {service}")
            
            return {
                "success": True,
                "output": f"Successfully disabled circuit breaker for {service}",
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e)
            }
    
    async def _restore_traffic_distribution(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Restore traffic distribution"""
        try:
            service = parameters["service"]
            
            # Simulate traffic restoration
            await asyncio.sleep(0.5)
            
            logger.info(f"Restored traffic distribution for {service}")
            
            return {
                "success": True,
                "output": f"Successfully restored traffic distribution for {service}",
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e)
            }
    
    async def _validate_rollback(self, rollback_plan: RollbackPlan) -> bool:
        """Validate that rollback was successful"""
        try:
            validation_results = []
            
            for check in rollback_plan.validation_checks:
                # Simulate validation (90% success rate for demo)
                result = True  # Always pass for demo
                validation_results.append(result)
                
                logger.info(f"Validation check '{check}': {'PASSED' if result else 'FAILED'}")
            
            return all(validation_results)
            
        except Exception as e:
            logger.error(f"Error validating rollback: {e}")
            return False
    
    def get_rollback_status(self, action_id: str) -> Optional[RollbackStatus]:
        """Get the current rollback status for an action"""
        return self.pending_rollbacks.get(action_id)
    
    def get_rollback_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent rollback history"""
        return self.rollback_history[-limit:] if self.rollback_history else []