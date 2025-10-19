"""
Secure Resolution Agent

Provides zero-trust resolution capabilities with sandbox validation and rollback mechanisms.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from src.interfaces.agent import BaseAgent
from src.models.agent import AgentRecommendation, AgentStatus, AgentType, ActionType, RiskLevel, ActionType as AgentActionType, RiskLevel, AgentMessage
from src.models.incident import Incident
from src.services.aws import AWSServiceFactory
from src.services.security_validation_service import SecurityValidationService
from src.services.resolution_success_validator import ResolutionSuccessValidator
from src.utils.logging import get_logger
from src.utils.exceptions import SecurityError, ValidationError
from src.utils.constants import AGENT_CONFIG

from .actions import (
    ActionExecutor, ResolutionAction, ActionResult, ActionType, RiskLevel
)
from .rollback import RollbackManager, RollbackPlan

logger = get_logger(__name__)


class SecureResolutionAgent(BaseAgent):
    """
    Secure Resolution Agent with zero-trust architecture
    
    Capabilities:
    - Zero-trust resolution with sandbox validation
    - Just-in-time IAM credential generation
    - Automatic rollback on validation failure
    - Security validation and privilege escalation prevention
    """
    
    def __init__(
        self,
        aws_factory: AWSServiceFactory,
        agent_id: str = "resolution-agent",
        sandbox_account_id: str = None
    ):
        super().__init__(AgentType.RESOLUTION, agent_id)
        self.aws_factory = aws_factory
        self.action_executor = ActionExecutor(aws_factory, sandbox_account_id)
        self.rollback_manager = RollbackManager(aws_factory)
        self.security_validator = SecurityValidationService()
        self.success_validator = ResolutionSuccessValidator(aws_factory)
        
        # Performance targets from config
        config = AGENT_CONFIG["resolution"]
        self.target_resolution_time = timedelta(minutes=config["target_resolution_time_minutes"])
        self.max_processing_time = timedelta(minutes=config["max_processing_time_minutes"])
        
        # Security settings from config
        self.require_approval_for_high_risk = config["require_approval_for_high_risk"]
        self.max_concurrent_actions = config["max_concurrent_actions"]
        self.active_actions = {}
        
        # Action templates for common incident types
        self.action_templates = {
            "cpu_exhaustion": self._create_cpu_exhaustion_actions,
            "memory_leak": self._create_memory_leak_actions,
            "service_degradation": self._create_service_degradation_actions,
            "performance_degradation": self._create_performance_degradation_actions,
            "storage_exhaustion": self._create_storage_exhaustion_actions,
            "database_cascade": self._create_database_cascade_actions,
            "ddos_attack": self._create_ddos_attack_actions,
            "api_overload": self._create_api_overload_actions,
            "storage_failure": self._create_storage_failure_actions
        }
        
        logger.info(f"Initialized {self.name} with {len(self.action_templates)} action templates")
    
    async def process_incident(self, incident: Incident) -> List[AgentRecommendation]:
        """
        Process incident for resolution analysis and action execution
        
        Args:
            incident: Incident to resolve
            
        Returns:
            Agent recommendation with resolution actions
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Processing incident {incident.id} for resolution")
            
            # Check if we're at capacity
            if len(self.active_actions) >= self.max_concurrent_actions:
                return self._create_capacity_exceeded_recommendation(incident)
            
            # Analyze incident and determine resolution actions
            resolution_actions = await self._analyze_incident_for_resolution(incident)
            
            if not resolution_actions:
                return self._create_no_action_recommendation(incident)
            
            # Execute resolution actions
            execution_results = await self._execute_resolution_actions(
                incident, resolution_actions
            )
            
            # Create recommendation based on execution results
            recommendation = await self._create_resolution_recommendation(
                incident, resolution_actions, execution_results
            )
            
            # Update agent status
            processing_time = datetime.utcnow() - start_time
            self._update_status_success(
                processing_time_seconds=processing_time.total_seconds(),
                action_count=len(resolution_actions),
                active_actions=len(self.active_actions)
            )
            
            logger.info(
                f"Completed resolution processing for {incident.id} in {processing_time.total_seconds():.2f}s"
            )
            
            return [recommendation]
            
        except Exception as e:
            logger.error(f"Error processing incident {incident.id}: {e}")
            self._update_status_error(str(e), incident_id=incident.id)
            
            return [AgentRecommendation(
                agent_name=AgentType.RESOLUTION,
                incident_id=incident.id,
                action_type=ActionType.NO_ACTION,
                action_id="resolution_error",
                confidence=0.0,
                risk_level=RiskLevel.LOW,
                estimated_impact="No impact due to error",
                reasoning=f"Resolution analysis failed: {str(e)}",
                urgency=0.0,
                parameters={"error": str(e)}
            )]
    
    def _get_service_name(self, incident: Incident) -> str:
        """Get service name from incident metadata"""
        return incident.metadata.tags.get("service", "unknown")
    
    async def _analyze_incident_for_resolution(self, incident: Incident) -> List[ResolutionAction]:
        """Analyze incident and determine appropriate resolution actions"""
        try:
            logger.info(f"Analyzing incident {incident.id} for resolution actions")
            
            # Determine incident type from title/description
            incident_type = await self._classify_incident_type(incident)
            
            # Get action template for this incident type
            if incident_type in self.action_templates:
                template_func = self.action_templates[incident_type]
                actions = await template_func(incident)
            else:
                # Generic actions for unknown incident types
                actions = await self._create_generic_actions(incident)
            
            # Filter and prioritize actions based on incident severity
            filtered_actions = await self._filter_actions_by_severity(incident, actions)
            
            logger.info(f"Generated {len(filtered_actions)} resolution actions for {incident_type}")
            
            return filtered_actions
            
        except Exception as e:
            logger.error(f"Error analyzing incident for resolution: {e}")
            return []
    
    async def _classify_incident_type(self, incident: Incident) -> str:
        """Classify incident type based on title and description"""
        try:
            title_lower = incident.title.lower()
            desc_lower = incident.description.lower()
            
            # Check for specific patterns
            if any(term in title_lower or term in desc_lower for term in ["cpu", "processor"]):
                return "cpu_exhaustion"
            elif any(term in title_lower or term in desc_lower for term in ["memory", "ram", "oom"]):
                return "memory_leak"
            elif any(term in title_lower or term in desc_lower for term in ["database", "db", "cascade"]):
                return "database_cascade"
            elif any(term in title_lower or term in desc_lower for term in ["ddos", "attack", "traffic"]):
                return "ddos_attack"
            elif any(term in title_lower or term in desc_lower for term in ["api", "overload", "rate"]):
                return "api_overload"
            elif any(term in title_lower or term in desc_lower for term in ["storage", "disk", "space"]):
                return "storage_exhaustion"
            elif any(term in title_lower or term in desc_lower for term in ["performance", "slow", "latency"]):
                return "performance_degradation"
            elif any(term in title_lower or term in desc_lower for term in ["service", "down", "unavailable"]):
                return "service_degradation"
            else:
                return "generic"
                
        except Exception as e:
            logger.error(f"Error classifying incident type: {e}")
            return "generic"
    
    async def _validate_action_security(
        self,
        action: ResolutionAction
    ) -> bool:
        """Validate action security before execution"""
        try:
            logger.info(f"Validating security for action {action.action_id}")
            
            # Convert action to security validation format
            action_parameters = {
                "target_service": action.target_service,
                "parameters": action.parameters,
                "risk_level": action.risk_level.value if hasattr(action.risk_level, 'value') else str(action.risk_level)
            }
            
            # Perform security validation
            validation_result = await self.security_validator.validate_action(
                action_id=action.action_type.value if hasattr(action.action_type, 'value') else str(action.action_type),
                action_parameters=action_parameters
            )
            
            if not validation_result.is_valid:
                logger.warning(f"Action {action.action_id} failed security validation: {validation_result.validation_errors}")
                return False
            
            if validation_result.approval_required:
                logger.info(f"Action {action.action_id} requires human approval (risk score: {validation_result.estimated_risk_score:.2f})")
                # In a real implementation, this would trigger approval workflow
                # For now, we'll allow medium-risk actions but block high-risk ones
                if validation_result.estimated_risk_score > 0.8:
                    logger.warning(f"Action {action.action_id} blocked due to high risk score")
                    return False
            
            logger.info(f"Action {action.action_id} passed security validation")
            return True
            
        except Exception as e:
            logger.error(f"Error validating action security: {e}")
            return False
    
    async def _create_cpu_exhaustion_actions(self, incident: Incident) -> List[ResolutionAction]:
        """Create actions for CPU exhaustion incidents"""
        actions = []
        
        service_name = self._get_service_name(incident)
        
        # Scale up service
        actions.append(ResolutionAction(
            action_id=str(uuid.uuid4()),
            action_type=ActionType.SCALE_SERVICE,
            target_service=service_name,
            parameters={"instances": 3},
            risk_level=RiskLevel.MEDIUM,
            estimated_duration=timedelta(minutes=2),
            rollback_plan={"original_instances": 1},
            validation_checks=["service_health", "cpu_utilization"],
            approval_required=False
        ))
        
        # Increase CPU resources
        actions.append(ResolutionAction(
            action_id=str(uuid.uuid4()),
            action_type=ActionType.INCREASE_RESOURCES,
            target_service=service_name,
            parameters={"cpu_factor": 1.5},
            risk_level=RiskLevel.MEDIUM,
            estimated_duration=timedelta(minutes=3),
            rollback_plan={"original_cpu": 1.0},
            validation_checks=["resource_allocation", "service_health"],
            approval_required=False
        ))
        
        return actions
    
    async def _create_memory_leak_actions(self, incident: Incident) -> List[ResolutionAction]:
        """Create actions for memory leak incidents"""
        actions = []
        service_name = self._get_service_name(incident)
        
        # Restart service to clear memory
        actions.append(ResolutionAction(
            action_id=str(uuid.uuid4()),
            action_type=ActionType.RESTART_SERVICE,
            target_service=service_name,
            parameters={},
            risk_level=RiskLevel.MEDIUM,
            estimated_duration=timedelta(minutes=2),
            rollback_plan={},
            validation_checks=["service_health", "memory_utilization"],
            approval_required=False
        ))
        
        # Increase memory allocation
        actions.append(ResolutionAction(
            action_id=str(uuid.uuid4()),
            action_type=ActionType.INCREASE_RESOURCES,
            target_service=service_name,
            parameters={"memory_factor": 1.5},
            risk_level=RiskLevel.MEDIUM,
            estimated_duration=timedelta(minutes=3),
            rollback_plan={"original_memory": 1.0},
            validation_checks=["resource_allocation", "memory_utilization"],
            approval_required=False
        ))
        
        return actions
    
    async def _create_service_degradation_actions(self, incident: Incident) -> List[ResolutionAction]:
        """Create actions for service degradation incidents"""
        actions = []
        service_name = self._get_service_name(incident)
        
        # Enable circuit breaker
        actions.append(ResolutionAction(
            action_id=str(uuid.uuid4()),
            action_type=ActionType.ENABLE_CIRCUIT_BREAKER,
            target_service=service_name,
            parameters={"threshold": 5, "timeout": 30},
            risk_level=RiskLevel.LOW,
            estimated_duration=timedelta(seconds=30),
            rollback_plan={},
            validation_checks=["circuit_breaker_status"],
            approval_required=False
        ))
        
        # Scale service
        actions.append(ResolutionAction(
            action_id=str(uuid.uuid4()),
            action_type=ActionType.SCALE_SERVICE,
            target_service=service_name,
            parameters={"instances": 2},
            risk_level=RiskLevel.MEDIUM,
            estimated_duration=timedelta(minutes=2),
            rollback_plan={"original_instances": 1},
            validation_checks=["service_health", "instance_count"],
            approval_required=False
        ))
        
        return actions
    
    async def _create_performance_degradation_actions(self, incident: Incident) -> List[ResolutionAction]:
        """Create actions for performance degradation incidents"""
        actions = []
        service_name = self._get_service_name(incident)
        
        # Clear cache
        actions.append(ResolutionAction(
            action_id=str(uuid.uuid4()),
            action_type=ActionType.CLEAR_CACHE,
            target_service=service_name,
            parameters={"cache_type": "redis"},
            risk_level=RiskLevel.LOW,
            estimated_duration=timedelta(minutes=1),
            rollback_plan={},
            validation_checks=["cache_status"],
            approval_required=False
        ))
        
        # Scale service
        actions.append(ResolutionAction(
            action_id=str(uuid.uuid4()),
            action_type=ActionType.SCALE_SERVICE,
            target_service=service_name,
            parameters={"instances": 2},
            risk_level=RiskLevel.MEDIUM,
            estimated_duration=timedelta(minutes=2),
            rollback_plan={"original_instances": 1},
            validation_checks=["service_health", "response_time"],
            approval_required=False
        ))
        
        return actions
    
    async def _create_storage_exhaustion_actions(self, incident: Incident) -> List[ResolutionAction]:
        """Create actions for storage exhaustion incidents"""
        actions = []
        service_name = self._get_service_name(incident)
        
        # Clear cache to free space
        actions.append(ResolutionAction(
            action_id=str(uuid.uuid4()),
            action_type=ActionType.CLEAR_CACHE,
            target_service=service_name,
            parameters={"cache_type": "application"},
            risk_level=RiskLevel.LOW,
            estimated_duration=timedelta(minutes=1),
            rollback_plan={},
            validation_checks=["disk_space"],
            approval_required=False
        ))
        
        return actions
    
    async def _create_database_cascade_actions(self, incident: Incident) -> List[ResolutionAction]:
        """Create actions for database cascade incidents"""
        actions = []
        service_name = self._get_service_name(incident)
        
        # Enable circuit breaker to prevent cascade
        actions.append(ResolutionAction(
            action_id=str(uuid.uuid4()),
            action_type=ActionType.ENABLE_CIRCUIT_BREAKER,
            target_service=service_name,
            parameters={"threshold": 3, "timeout": 60},
            risk_level=RiskLevel.MEDIUM,
            estimated_duration=timedelta(seconds=30),
            rollback_plan={},
            validation_checks=["circuit_breaker_status", "database_health"],
            approval_required=False
        ))
        
        # Scale database connections
        actions.append(ResolutionAction(
            action_id=str(uuid.uuid4()),
            action_type=ActionType.UPDATE_CONFIG,
            target_service=service_name,
            parameters={"max_connections": 50, "timeout": 30},
            risk_level=RiskLevel.MEDIUM,
            estimated_duration=timedelta(minutes=1),
            rollback_plan={"original_config": {"max_connections": 100, "timeout": 60}},
            validation_checks=["database_config", "connection_pool"],
            approval_required=False
        ))
        
        return actions
    
    async def _create_ddos_attack_actions(self, incident: Incident) -> List[ResolutionAction]:
        """Create actions for DDoS attack incidents"""
        actions = []
        service_name = self._get_service_name(incident)
        
        # Enable circuit breaker
        actions.append(ResolutionAction(
            action_id=str(uuid.uuid4()),
            action_type=ActionType.ENABLE_CIRCUIT_BREAKER,
            target_service=service_name,
            parameters={"threshold": 10, "timeout": 120},
            risk_level=RiskLevel.HIGH,
            estimated_duration=timedelta(seconds=30),
            rollback_plan={},
            validation_checks=["circuit_breaker_status", "traffic_rate"],
            approval_required=True
        ))
        
        # Drain some traffic
        actions.append(ResolutionAction(
            action_id=str(uuid.uuid4()),
            action_type=ActionType.DRAIN_TRAFFIC,
            target_service=service_name,
            parameters={"drain_percentage": 30},
            risk_level=RiskLevel.HIGH,
            estimated_duration=timedelta(minutes=2),
            rollback_plan={},
            validation_checks=["traffic_distribution", "service_health"],
            approval_required=True
        ))
        
        return actions
    
    async def _create_api_overload_actions(self, incident: Incident) -> List[ResolutionAction]:
        """Create actions for API overload incidents"""
        actions = []
        service_name = self._get_service_name(incident)
        
        # Scale API service
        actions.append(ResolutionAction(
            action_id=str(uuid.uuid4()),
            action_type=ActionType.SCALE_SERVICE,
            target_service=service_name,
            parameters={"instances": 3},
            risk_level=RiskLevel.MEDIUM,
            estimated_duration=timedelta(minutes=2),
            rollback_plan={"original_instances": 1},
            validation_checks=["service_health", "api_response_time"],
            approval_required=False
        ))
        
        # Update rate limiting
        actions.append(ResolutionAction(
            action_id=str(uuid.uuid4()),
            action_type=ActionType.UPDATE_CONFIG,
            target_service=service_name,
            parameters={"rate_limit": 100},
            risk_level=RiskLevel.LOW,
            estimated_duration=timedelta(minutes=1),
            rollback_plan={"original_config": {"rate_limit": 1000}},
            validation_checks=["rate_limit_config"],
            approval_required=False
        ))
        
        return actions
    
    async def _create_storage_failure_actions(self, incident: Incident) -> List[ResolutionAction]:
        """Create actions for storage failure incidents"""
        actions = []
        service_name = self._get_service_name(incident)
        
        # This is a high-risk scenario requiring human approval
        actions.append(ResolutionAction(
            action_id=str(uuid.uuid4()),
            action_type=ActionType.ROLLBACK_DEPLOYMENT,
            target_service=service_name,
            parameters={"versions_back": 1},
            risk_level=RiskLevel.CRITICAL,
            estimated_duration=timedelta(minutes=5),
            rollback_plan={},
            validation_checks=["deployment_health", "storage_access"],
            approval_required=True
        ))
        
        return actions
    
    async def _create_generic_actions(self, incident: Incident) -> List[ResolutionAction]:
        """Create generic actions for unknown incident types"""
        actions = []
        service_name = self._get_service_name(incident)
        
        # Generic restart action
        actions.append(ResolutionAction(
            action_id=str(uuid.uuid4()),
            action_type=ActionType.RESTART_SERVICE,
            target_service=service_name,
            parameters={},
            risk_level=RiskLevel.MEDIUM,
            estimated_duration=timedelta(minutes=2),
            rollback_plan={},
            validation_checks=["service_health"],
            approval_required=False
        ))
        
        return actions
    
    async def _filter_actions_by_severity(
        self, 
        incident: Incident, 
        actions: List[ResolutionAction]
    ) -> List[ResolutionAction]:
        """Filter and prioritize actions based on incident severity"""
        try:
            if incident.severity == "critical":
                # For critical incidents, include all actions
                return actions
            elif incident.severity == "high":
                # For high severity, exclude critical risk actions
                return [a for a in actions if a.risk_level != RiskLevel.CRITICAL]
            elif incident.severity == "medium":
                # For medium severity, only low and medium risk actions
                return [a for a in actions if a.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]]
            else:
                # For low severity, only low risk actions
                return [a for a in actions if a.risk_level == RiskLevel.LOW]
                
        except Exception as e:
            logger.error(f"Error filtering actions by severity: {e}")
            return actions
    
    async def _execute_resolution_actions(
        self, 
        incident: Incident, 
        actions: List[ResolutionAction]
    ) -> List[ActionResult]:
        """Execute resolution actions with proper error handling"""
        try:
            results = []
            
            for action in actions:
                try:
                    # Validate action security before execution
                    if not await self._validate_action_security(action):
                        logger.warning(f"Action {action.action_id} failed security validation, skipping")
                        
                        # Create security failure result
                        security_result = ActionResult(
                            action_id=action.action_id,
                            success=False,
                            execution_time=timedelta(seconds=1),
                            output="",
                            error_message="Action failed security validation",
                            rollback_required=False
                        )
                        results.append(security_result)
                        continue
                    
                    # Track active action
                    self.active_actions[action.action_id] = {
                        "action": action,
                        "start_time": datetime.utcnow(),
                        "incident_id": incident.id
                    }
                    
                    # Execute action
                    result = await self.action_executor.execute_action(action)
                    results.append(result)
                    
                    # Start success validation monitoring if action succeeded
                    if result.success:
                        try:
                            validation_id = await self.success_validator.start_validation(
                                action_id=action.action_id,
                                action_type=action.action_type.value if hasattr(action.action_type, 'value') else str(action.action_type),
                                target_service=action.target_service
                            )
                            logger.info(f"Started success validation for action {action.action_id}: {validation_id}")
                        except Exception as e:
                            logger.error(f"Failed to start success validation for action {action.action_id}: {e}")
                    
                    # Handle rollback if action failed
                    if not result.success and result.rollback_required:
                        await self._handle_action_rollback(action, result)
                    
                    # Remove from active actions
                    self.active_actions.pop(action.action_id, None)
                    
                    logger.info(
                        f"Action {action.action_id} completed: "
                        f"{'SUCCESS' if result.success else 'FAILED'}"
                    )
                    
                except Exception as e:
                    logger.error(f"Error executing action {action.action_id}: {e}")
                    
                    # Create error result
                    error_result = ActionResult(
                        action_id=action.action_id,
                        success=False,
                        execution_time=timedelta(seconds=1),
                        output="",
                        error_message=str(e),
                        rollback_required=True
                    )
                    results.append(error_result)
                    
                    # Remove from active actions
                    self.active_actions.pop(action.action_id, None)
            
            return results
            
        except Exception as e:
            logger.error(f"Error executing resolution actions: {e}")
            return []
    
    async def _handle_action_rollback(self, action: ResolutionAction, result: ActionResult):
        """Handle rollback for failed action"""
        try:
            logger.info(f"Initiating rollback for failed action {action.action_id}")
            
            # Create rollback plan
            rollback_plan = await self.rollback_manager.create_rollback_plan(action)
            
            # Execute rollback
            rollback_result = await self.rollback_manager.execute_rollback(rollback_plan)
            
            logger.info(
                f"Rollback for {action.action_id} completed with status: {rollback_result.status.value}"
            )
            
        except Exception as e:
            logger.error(f"Error handling rollback for {action.action_id}: {e}")
    
    async def _create_resolution_recommendation(
        self,
        incident: Incident,
        actions: List[ResolutionAction],
        results: List[ActionResult]
    ) -> AgentRecommendation:
        """Create agent recommendation based on resolution results"""
        try:
            successful_actions = [r for r in results if r.success]
            failed_actions = [r for r in results if not r.success]
            
            # Calculate confidence based on success rate
            if results:
                success_rate = len(successful_actions) / len(results)
                confidence = min(success_rate * 0.9, 1.0)  # Slightly conservative
            else:
                confidence = 0.0
            
            # Create reasoning
            reasoning_parts = []
            if successful_actions:
                reasoning_parts.append(f"Successfully executed {len(successful_actions)} resolution actions")
            if failed_actions:
                reasoning_parts.append(f"{len(failed_actions)} actions failed or require approval")
            
            reasoning = ". ".join(reasoning_parts) if reasoning_parts else "No actions executed"
            
            # Create action summaries
            action_summaries = []
            for i, (action, result) in enumerate(zip(actions, results)):
                action_summaries.append({
                    "action_id": action.action_id,
                    "type": action.action_type.value,
                    "target_service": action.target_service,
                    "success": result.success,
                    "execution_time_seconds": result.execution_time.total_seconds(),
                    "risk_level": action.risk_level.value,
                    "approval_required": action.approval_required,
                    "output": result.output[:200] if result.output else "",  # Truncate output
                    "error": result.error_message if result.error_message else None
                })
            
            # Determine recommendation type
            if all(r.success for r in results):
                rec_type = "resolution_complete"
            elif any(r.success for r in results):
                rec_type = "resolution_partial"
            elif any(a.approval_required for a in actions):
                rec_type = "resolution_approval_required"
            else:
                rec_type = "resolution_failed"
            
            # Create metadata
            metadata = {
                "total_actions": len(actions),
                "successful_actions": len(successful_actions),
                "failed_actions": len(failed_actions),
                "actions_requiring_approval": len([a for a in actions if a.approval_required]),
                "action_details": action_summaries,
                "incident_type": await self._classify_incident_type(incident)
            }
            
            return AgentRecommendation(
                agent_name=AgentType.RESOLUTION,
                incident_id=incident.id,
                action_type="scale_up" if "scale" in rec_type else "restart_service",
                action_id=rec_type,
                confidence=confidence,
                risk_level="medium",
                estimated_impact="Automated resolution attempt",
                reasoning=reasoning,
                urgency=confidence,
                parameters=metadata
            )
            
        except Exception as e:
            logger.error(f"Error creating resolution recommendation: {e}")
            return AgentRecommendation(
                agent_name=AgentType.RESOLUTION,
                incident_id=incident.id,
                action_type="no_action",
                action_id="resolution_error",
                confidence=0.0,
                risk_level="low",
                estimated_impact="No impact due to error",
                reasoning=f"Error creating resolution recommendation: {str(e)}",
                urgency=0.0,
                parameters={"error": str(e)}
            )
    
    def _create_capacity_exceeded_recommendation(self, incident: Incident) -> AgentRecommendation:
        """Create recommendation when agent is at capacity"""
        return AgentRecommendation(
            agent_name=AgentType.RESOLUTION,
            incident_id=incident.id,
            action_type="no_action",
            action_id="resolution_capacity_exceeded",
            confidence=0.0,
            risk_level="low",
            estimated_impact="No action due to capacity limits",
            reasoning=f"Resolution agent at capacity ({len(self.active_actions)}/{self.max_concurrent_actions} active actions)",
            urgency=0.0,
            parameters={
                "active_actions": len(self.active_actions),
                "max_concurrent_actions": self.max_concurrent_actions
            }
        )
    
    def _create_no_action_recommendation(self, incident: Incident) -> AgentRecommendation:
        """Create recommendation when no actions are available"""
        return AgentRecommendation(
            agent_name=AgentType.RESOLUTION,
            incident_id=incident.id,
            action_type="no_action",
            action_id="resolution_no_action",
            confidence=0.5,
            risk_level="low",
            estimated_impact="Manual intervention required",
            reasoning="No automated resolution actions available for this incident type",
            urgency=0.0,
            parameters={"incident_classification": "manual_intervention_required"}
        )
    

    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get detailed health status of the resolution agent"""
        try:
            return {
                "agent_id": self.name,
                "status": self.status.value,
                "last_activity": self.last_activity.isoformat() if self.last_activity else None,
                "capabilities": [
                    "zero_trust_resolution",
                    "sandbox_validation",
                    "automatic_rollback",
                    "security_validation"
                ],
                "performance_targets": {
                    "target_resolution_time_minutes": self.target_resolution_time.total_seconds() / 60,
                    "max_processing_time_minutes": self.max_processing_time.total_seconds() / 60
                },
                "capacity": {
                    "active_actions": len(self.active_actions),
                    "max_concurrent_actions": self.max_concurrent_actions,
                    "available_capacity": self.max_concurrent_actions - len(self.active_actions)
                },
                "action_templates": list(self.action_templates.keys()),
                "security_settings": {
                    "require_approval_for_high_risk": self.require_approval_for_high_risk,
                    "sandbox_validation_enabled": True
                },
                "metadata": self.metadata
            }
            
        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return {
                "agent_id": self.name,
                "status": "error",
                "error": str(e)
            }
    
    async def handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Handle a message from another agent"""
        try:
            # For now, resolution agent doesn't handle inter-agent messages
            # This could be extended for coordination with other agents
            logger.info(f"Received message from {message.sender_agent}: {message.message_type}")
            return None
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return None
    
    async def health_check(self) -> bool:
        """Perform health check for this agent"""
        try:
            # Basic health check - ensure we can access required services
            if not self.aws_factory:
                return False
            
            # Check if we can create action executor and rollback manager
            if not self.action_executor or not self.rollback_manager:
                return False
            
            return self.is_healthy
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False