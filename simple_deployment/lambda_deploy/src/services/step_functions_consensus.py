"""
AWS Step Functions integration for Byzantine consensus coordination.

This module provides Step Functions state machine definitions and execution
logic for distributed Byzantine fault tolerant consensus.
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

import boto3
from botocore.exceptions import ClientError

from src.services.aws import AWSServiceFactory
from src.utils.logging import get_logger
from src.utils.exceptions import StepFunctionsExecutionError
from src.utils.constants import CONSENSUS_CONFIG


logger = get_logger("step_functions_consensus")


class StepFunctionsConsensusCoordinator:
    """Coordinates Byzantine consensus using AWS Step Functions."""
    
    def __init__(self, aws_factory: AWSServiceFactory):
        """Initialize Step Functions coordinator."""
        self.aws_factory = aws_factory
        self.state_machine_arn = None  # Will be set from environment
        self.execution_timeout = timedelta(minutes=10)
        
    async def execute_consensus_workflow(self, incident_id: str, 
                                       recommendations: List[Dict[str, Any]],
                                       round_id: str) -> Dict[str, Any]:
        """
        Execute Byzantine consensus workflow using Step Functions.
        
        Args:
            incident_id: ID of the incident
            recommendations: Agent recommendations
            round_id: Consensus round identifier
            
        Returns:
            Consensus execution result
        """
        try:
            # Prepare input for Step Functions
            workflow_input = {
                "incident_id": incident_id,
                "round_id": round_id,
                "recommendations": [self._serialize_recommendation(r) for r in recommendations],
                "timestamp": datetime.utcnow().isoformat(),
                "consensus_config": {
                    "confidence_threshold": CONSENSUS_CONFIG["autonomous_confidence_threshold"],
                    "byzantine_threshold": 0.33,
                    "min_agreement_threshold": 0.67,
                    "timeout_minutes": 5
                }
            }
            
            # Execute Step Functions state machine
            stepfunctions_client = await self.aws_factory.get_stepfunctions_client()
            
            execution_name = f"consensus-{round_id}-{int(datetime.utcnow().timestamp())}"
            
            response = await stepfunctions_client.start_execution(
                stateMachineArn=self.state_machine_arn,
                name=execution_name,
                input=json.dumps(workflow_input)
            )
            
            execution_arn = response['executionArn']
            logger.info(f"Started Step Functions execution: {execution_arn}")
            
            # Wait for execution to complete
            result = await self._wait_for_execution_completion(execution_arn)
            
            return result
            
        except Exception as e:
            logger.error(f"Step Functions consensus execution failed: {e}")
            raise StepFunctionsExecutionError(f"Consensus workflow failed: {e}")
    
    async def _wait_for_execution_completion(self, execution_arn: str) -> Dict[str, Any]:
        """Wait for Step Functions execution to complete."""
        stepfunctions_client = await self.aws_factory.get_stepfunctions_client()
        
        start_time = datetime.utcnow()
        
        while datetime.utcnow() - start_time < self.execution_timeout:
            try:
                response = await stepfunctions_client.describe_execution(
                    executionArn=execution_arn
                )
                
                status = response['status']
                
                if status == 'SUCCEEDED':
                    output = json.loads(response.get('output', '{}'))
                    logger.info(f"Step Functions execution succeeded: {execution_arn}")
                    return output
                
                elif status in ['FAILED', 'TIMED_OUT', 'ABORTED']:
                    error_msg = response.get('error', 'Unknown error')
                    logger.error(f"Step Functions execution failed: {status} - {error_msg}")
                    raise StepFunctionsExecutionError(f"Execution {status}: {error_msg}")
                
                # Still running, wait and check again
                await asyncio.sleep(2)
                
            except ClientError as e:
                logger.error(f"Error checking Step Functions execution: {e}")
                raise StepFunctionsExecutionError(f"Failed to check execution status: {e}")
        
        # Timeout reached
        logger.error(f"Step Functions execution timed out: {execution_arn}")
        raise StepFunctionsExecutionError("Consensus workflow timed out")
    
    def _serialize_recommendation(self, recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize recommendation for Step Functions input."""
        return {
            "agent_name": str(recommendation.get("agent_name", "")),
            "action_id": recommendation.get("action_id", ""),
            "confidence": float(recommendation.get("confidence", 0.0)),
            "urgency": float(recommendation.get("urgency", 0.0)),
            "reasoning": recommendation.get("reasoning", ""),
            "estimated_impact": recommendation.get("estimated_impact", ""),
            "risk_level": recommendation.get("risk_level", "low"),
            "parameters": recommendation.get("parameters", {})
        }
    
    def get_state_machine_definition(self) -> Dict[str, Any]:
        """
        Get the Step Functions state machine definition for Byzantine consensus.
        
        Returns:
            State machine definition in ASL (Amazon States Language)
        """
        return {
            "Comment": "Byzantine Fault Tolerant Consensus State Machine",
            "StartAt": "ValidateInput",
            "States": {
                "ValidateInput": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::lambda:invoke",
                    "Parameters": {
                        "FunctionName": "incident-commander-validate-consensus-input",
                        "Payload.$": "$"
                    },
                    "ResultPath": "$.validation_result",
                    "Next": "CheckValidation",
                    "Retry": [
                        {
                            "ErrorEquals": ["States.TaskFailed"],
                            "IntervalSeconds": 2,
                            "MaxAttempts": 3,
                            "BackoffRate": 2.0
                        }
                    ],
                    "Catch": [
                        {
                            "ErrorEquals": ["States.ALL"],
                            "Next": "ValidationFailed",
                            "ResultPath": "$.error"
                        }
                    ]
                },
                
                "CheckValidation": {
                    "Type": "Choice",
                    "Choices": [
                        {
                            "Variable": "$.validation_result.Payload.is_valid",
                            "BooleanEquals": True,
                            "Next": "DetectByzantineAgents"
                        }
                    ],
                    "Default": "ValidationFailed"
                },
                
                "DetectByzantineAgents": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::lambda:invoke",
                    "Parameters": {
                        "FunctionName": "incident-commander-detect-byzantine-agents",
                        "Payload.$": "$"
                    },
                    "ResultPath": "$.byzantine_detection",
                    "Next": "FilterByzantineRecommendations",
                    "Retry": [
                        {
                            "ErrorEquals": ["States.TaskFailed"],
                            "IntervalSeconds": 2,
                            "MaxAttempts": 3,
                            "BackoffRate": 2.0
                        }
                    ],
                    "Catch": [
                        {
                            "ErrorEquals": ["States.ALL"],
                            "Next": "ByzantineDetectionFailed",
                            "ResultPath": "$.error"
                        }
                    ]
                },
                
                "FilterByzantineRecommendations": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::lambda:invoke",
                    "Parameters": {
                        "FunctionName": "incident-commander-filter-byzantine-recommendations",
                        "Payload.$": "$"
                    },
                    "ResultPath": "$.filtered_recommendations",
                    "Next": "CheckRemainingRecommendations",
                    "Retry": [
                        {
                            "ErrorEquals": ["States.TaskFailed"],
                            "IntervalSeconds": 2,
                            "MaxAttempts": 3,
                            "BackoffRate": 2.0
                        }
                    ]
                },
                
                "CheckRemainingRecommendations": {
                    "Type": "Choice",
                    "Choices": [
                        {
                            "Variable": "$.filtered_recommendations.Payload.valid_count",
                            "NumericGreaterThan": 0,
                            "Next": "CalculateWeightedConsensus"
                        }
                    ],
                    "Default": "AllAgentsByzantine"
                },
                
                "CalculateWeightedConsensus": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::lambda:invoke",
                    "Parameters": {
                        "FunctionName": "incident-commander-calculate-weighted-consensus",
                        "Payload.$": "$"
                    },
                    "ResultPath": "$.consensus_calculation",
                    "Next": "ValidateConsensusThreshold",
                    "Retry": [
                        {
                            "ErrorEquals": ["States.TaskFailed"],
                            "IntervalSeconds": 2,
                            "MaxAttempts": 3,
                            "BackoffRate": 2.0
                        }
                    ]
                },
                
                "ValidateConsensusThreshold": {
                    "Type": "Choice",
                    "Choices": [
                        {
                            "And": [
                                {
                                    "Variable": "$.consensus_calculation.Payload.final_confidence",
                                    "NumericGreaterThanEquals": CONSENSUS_CONFIG["autonomous_confidence_threshold"]
                                },
                                {
                                    "Variable": "$.consensus_calculation.Payload.agreement_ratio",
                                    "NumericGreaterThanEquals": 0.67
                                }
                            ],
                            "Next": "ConsensusReached"
                        }
                    ],
                    "Default": "ConsensusNotReached"
                },
                
                "ConsensusReached": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::lambda:invoke",
                    "Parameters": {
                        "FunctionName": "incident-commander-finalize-consensus",
                        "Payload": {
                            "consensus_reached": True,
                            "input.$": "$"
                        }
                    },
                    "ResultPath": "$.final_result",
                    "Next": "UpdateAgentReputation"
                },
                
                "ConsensusNotReached": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::lambda:invoke",
                    "Parameters": {
                        "FunctionName": "incident-commander-finalize-consensus",
                        "Payload": {
                            "consensus_reached": False,
                            "input.$": "$"
                        }
                    },
                    "ResultPath": "$.final_result",
                    "Next": "UpdateAgentReputation"
                },
                
                "UpdateAgentReputation": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::lambda:invoke",
                    "Parameters": {
                        "FunctionName": "incident-commander-update-agent-reputation",
                        "Payload.$": "$"
                    },
                    "ResultPath": "$.reputation_update",
                    "Next": "ConsensusComplete",
                    "Retry": [
                        {
                            "ErrorEquals": ["States.TaskFailed"],
                            "IntervalSeconds": 1,
                            "MaxAttempts": 2,
                            "BackoffRate": 2.0
                        }
                    ],
                    "Catch": [
                        {
                            "ErrorEquals": ["States.ALL"],
                            "Next": "ConsensusComplete",
                            "ResultPath": "$.reputation_error"
                        }
                    ]
                },
                
                "ConsensusComplete": {
                    "Type": "Pass",
                    "Result": {
                        "status": "completed"
                    },
                    "ResultPath": "$.status",
                    "End": True
                },
                
                "ValidationFailed": {
                    "Type": "Pass",
                    "Result": {
                        "consensus_reached": False,
                        "error": "Input validation failed",
                        "selected_action": "no_action",
                        "final_confidence": 0.0
                    },
                    "End": True
                },
                
                "ByzantineDetectionFailed": {
                    "Type": "Pass",
                    "Result": {
                        "consensus_reached": False,
                        "error": "Byzantine detection failed",
                        "selected_action": "error",
                        "final_confidence": 0.0
                    },
                    "End": True
                },
                
                "AllAgentsByzantine": {
                    "Type": "Pass",
                    "Result": {
                        "consensus_reached": False,
                        "error": "All agents flagged as Byzantine",
                        "selected_action": "no_action",
                        "final_confidence": 0.0
                    },
                    "End": True
                }
            }
        }


# Global Step Functions coordinator instance
step_functions_coordinator: Optional[StepFunctionsConsensusCoordinator] = None


def get_step_functions_coordinator(aws_factory: AWSServiceFactory) -> StepFunctionsConsensusCoordinator:
    """Get or create global Step Functions coordinator instance."""
    global step_functions_coordinator
    if step_functions_coordinator is None:
        step_functions_coordinator = StepFunctionsConsensusCoordinator(aws_factory)
    return step_functions_coordinator