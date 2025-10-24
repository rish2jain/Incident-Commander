"""
Resolution Success Validation and Monitoring Service

Provides automated validation of resolution success and regression monitoring.
Implements 5-minute validation window with automatic rollback triggers.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from src.services.aws import AWSServiceFactory
from src.utils.logging import get_logger
from src.utils.exceptions import ValidationError

logger = get_logger(__name__)


class ValidationStatus(Enum):
    """Status of resolution validation"""
    PENDING = "pending"
    VALIDATING = "validating"
    SUCCESS = "success"
    FAILED = "failed"
    REGRESSION_DETECTED = "regression_detected"
    ROLLBACK_REQUIRED = "rollback_required"


@dataclass
class ValidationMetric:
    """Represents a metric to validate resolution success"""
    metric_name: str
    metric_type: str  # "cloudwatch", "custom", "health_check"
    expected_value: float
    tolerance: float  # Acceptable deviation
    validation_window_minutes: int
    critical: bool  # If true, failure triggers immediate rollback


@dataclass
class ValidationResult:
    """Result of resolution validation"""
    action_id: str
    validation_status: ValidationStatus
    validation_metrics: List[Dict[str, Any]]
    success_score: float  # 0.0 to 1.0
    validation_timestamp: datetime
    regression_detected: bool
    rollback_recommended: bool
    validation_errors: List[str]
    next_validation_time: Optional[datetime]


class ResolutionSuccessValidator:
    """Validates resolution success and monitors for regression"""
    
    def __init__(self, aws_factory: AWSServiceFactory):
        self.aws_factory = aws_factory
        self.active_validations = {}  # Track ongoing validations
        self.validation_history = {}  # Store validation history
        
        # Validation configuration
        self.validation_window = timedelta(minutes=5)
        self.regression_monitoring_window = timedelta(minutes=30)
        self.validation_interval = timedelta(minutes=1)
        
        # Default validation metrics for different action types
        self.default_metrics = self._initialize_default_metrics()
        
        logger.info("Initialized Resolution Success Validator")
    
    def _initialize_default_metrics(self) -> Dict[str, List[ValidationMetric]]:
        """Initialize default validation metrics for different action types"""
        return {
            "scale_up_instances": [
                ValidationMetric(
                    metric_name="CPUUtilization",
                    metric_type="cloudwatch",
                    expected_value=70.0,  # Expect CPU to be under 70% after scaling
                    tolerance=10.0,
                    validation_window_minutes=5,
                    critical=True
                ),
                ValidationMetric(
                    metric_name="InstanceCount",
                    metric_type="custom",
                    expected_value=3.0,  # Expect 3 instances after scaling
                    tolerance=0.0,
                    validation_window_minutes=2,
                    critical=True
                )
            ],
            "restart_service": [
                ValidationMetric(
                    metric_name="ServiceHealth",
                    metric_type="health_check",
                    expected_value=1.0,  # Healthy = 1.0
                    tolerance=0.0,
                    validation_window_minutes=3,
                    critical=True
                ),
                ValidationMetric(
                    metric_name="ResponseTime",
                    metric_type="cloudwatch",
                    expected_value=200.0,  # Expect response time under 200ms
                    tolerance=50.0,
                    validation_window_minutes=5,
                    critical=False
                )
            ],
            "enable_rate_limiting": [
                ValidationMetric(
                    metric_name="RequestRate",
                    metric_type="cloudwatch",
                    expected_value=1000.0,  # Expect request rate under 1000/min
                    tolerance=100.0,
                    validation_window_minutes=3,
                    critical=True
                ),
                ValidationMetric(
                    metric_name="ErrorRate",
                    metric_type="cloudwatch",
                    expected_value=0.01,  # Expect error rate under 1%
                    tolerance=0.005,
                    validation_window_minutes=5,
                    critical=False
                )
            ],
            "clear_cache": [
                ValidationMetric(
                    metric_name="CacheHitRate",
                    metric_type="cloudwatch",
                    expected_value=0.8,  # Expect cache hit rate to recover to 80%
                    tolerance=0.1,
                    validation_window_minutes=10,
                    critical=False
                ),
                ValidationMetric(
                    metric_name="ResponseTime",
                    metric_type="cloudwatch",
                    expected_value=150.0,  # Expect improved response time
                    tolerance=30.0,
                    validation_window_minutes=5,
                    critical=True
                )
            ]
        }
    
    async def start_validation(
        self,
        action_id: str,
        action_type: str,
        target_service: str,
        custom_metrics: List[ValidationMetric] = None
    ) -> str:
        """
        Start validation monitoring for a resolution action
        
        Args:
            action_id: Unique identifier for the action
            action_type: Type of action performed
            target_service: Service that was acted upon
            custom_metrics: Optional custom validation metrics
            
        Returns:
            Validation ID for tracking
        """
        try:
            validation_id = f"validation_{action_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # Get validation metrics
            metrics = custom_metrics or self.default_metrics.get(action_type, [])
            
            if not metrics:
                logger.warning(f"No validation metrics defined for action type: {action_type}")
                return validation_id
            
            # Initialize validation tracking
            self.active_validations[validation_id] = {
                "action_id": action_id,
                "action_type": action_type,
                "target_service": target_service,
                "metrics": metrics,
                "start_time": datetime.utcnow(),
                "status": ValidationStatus.PENDING,
                "validation_results": [],
                "regression_monitoring": True
            }
            
            # Start validation task
            asyncio.create_task(self._run_validation_monitoring(validation_id))
            
            logger.info(f"Started validation monitoring for action {action_id} (validation_id: {validation_id})")
            
            return validation_id
            
        except Exception as e:
            logger.error(f"Error starting validation for action {action_id}: {e}")
            raise ValidationError(f"Failed to start validation: {str(e)}")
    
    async def _run_validation_monitoring(self, validation_id: str):
        """Run continuous validation monitoring for an action"""
        try:
            validation_info = self.active_validations[validation_id]
            action_id = validation_info["action_id"]
            
            logger.info(f"Starting validation monitoring for {validation_id}")
            
            # Initial validation after brief delay
            await asyncio.sleep(30)  # Wait 30 seconds for action to take effect
            
            validation_end_time = datetime.utcnow() + self.validation_window
            regression_end_time = datetime.utcnow() + self.regression_monitoring_window
            
            while datetime.utcnow() < regression_end_time:
                try:
                    # Perform validation
                    result = await self._perform_validation(validation_id)
                    
                    # Store result
                    validation_info["validation_results"].append(result)
                    validation_info["status"] = result.validation_status
                    
                    # Check if rollback is needed
                    if result.rollback_recommended:
                        logger.warning(f"Rollback recommended for action {action_id}")
                        await self._trigger_rollback(validation_id, result)
                        break
                    
                    # Check if validation is complete
                    if datetime.utcnow() > validation_end_time and result.validation_status == ValidationStatus.SUCCESS:
                        logger.info(f"Validation completed successfully for action {action_id}")
                        validation_info["status"] = ValidationStatus.SUCCESS
                        validation_info["regression_monitoring"] = True
                        
                        # Continue regression monitoring
                        await asyncio.sleep(self.validation_interval.total_seconds())
                        continue
                    
                    # Wait before next validation
                    await asyncio.sleep(self.validation_interval.total_seconds())
                    
                except Exception as e:
                    logger.error(f"Error during validation monitoring for {validation_id}: {e}")
                    validation_info["status"] = ValidationStatus.FAILED
                    break
            
            # Clean up completed validation
            if validation_id in self.active_validations:
                final_status = self.active_validations[validation_id]["status"]
                self.validation_history[validation_id] = self.active_validations.pop(validation_id)
                logger.info(f"Validation monitoring completed for {validation_id} with status: {final_status}")
            
        except Exception as e:
            logger.error(f"Error in validation monitoring for {validation_id}: {e}")
            if validation_id in self.active_validations:
                self.active_validations[validation_id]["status"] = ValidationStatus.FAILED
    
    async def _perform_validation(self, validation_id: str) -> ValidationResult:
        """Perform validation check for a specific validation"""
        try:
            validation_info = self.active_validations[validation_id]
            action_id = validation_info["action_id"]
            target_service = validation_info["target_service"]
            metrics = validation_info["metrics"]
            
            validation_metrics = []
            success_count = 0
            critical_failures = 0
            validation_errors = []
            
            # Validate each metric
            for metric in metrics:
                try:
                    metric_result = await self._validate_metric(metric, target_service)
                    validation_metrics.append(metric_result)
                    
                    if metric_result["success"]:
                        success_count += 1
                    elif metric.critical:
                        critical_failures += 1
                        validation_errors.append(
                            f"Critical metric {metric.metric_name} failed validation"
                        )
                    
                except Exception as e:
                    logger.error(f"Error validating metric {metric.metric_name}: {e}")
                    validation_errors.append(f"Metric validation error: {str(e)}")
                    if metric.critical:
                        critical_failures += 1
            
            # Calculate success score
            success_score = success_count / len(metrics) if metrics else 0.0
            
            # Determine validation status
            if critical_failures > 0:
                status = ValidationStatus.FAILED
                rollback_recommended = True
            elif success_score >= 0.8:
                status = ValidationStatus.SUCCESS
                rollback_recommended = False
            elif success_score >= 0.6:
                status = ValidationStatus.VALIDATING
                rollback_recommended = False
            else:
                status = ValidationStatus.FAILED
                rollback_recommended = True
            
            # Check for regression
            regression_detected = await self._detect_regression(validation_id, validation_metrics)
            if regression_detected:
                status = ValidationStatus.REGRESSION_DETECTED
                rollback_recommended = True
            
            result = ValidationResult(
                action_id=action_id,
                validation_status=status,
                validation_metrics=validation_metrics,
                success_score=success_score,
                validation_timestamp=datetime.utcnow(),
                regression_detected=regression_detected,
                rollback_recommended=rollback_recommended,
                validation_errors=validation_errors,
                next_validation_time=datetime.utcnow() + self.validation_interval
            )
            
            logger.info(
                f"Validation result for {action_id}: status={status.value}, "
                f"score={success_score:.2f}, rollback={rollback_recommended}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error performing validation for {validation_id}: {e}")
            return ValidationResult(
                action_id=validation_info["action_id"],
                validation_status=ValidationStatus.FAILED,
                validation_metrics=[],
                success_score=0.0,
                validation_timestamp=datetime.utcnow(),
                regression_detected=False,
                rollback_recommended=True,
                validation_errors=[f"Validation error: {str(e)}"],
                next_validation_time=None
            )
    
    async def _validate_metric(
        self,
        metric: ValidationMetric,
        target_service: str
    ) -> Dict[str, Any]:
        """Validate a specific metric"""
        try:
            if metric.metric_type == "cloudwatch":
                actual_value = await self._get_cloudwatch_metric(metric.metric_name, target_service)
            elif metric.metric_type == "health_check":
                actual_value = await self._perform_health_check(target_service)
            elif metric.metric_type == "custom":
                actual_value = await self._get_custom_metric(metric.metric_name, target_service)
            else:
                raise ValueError(f"Unknown metric type: {metric.metric_type}")
            
            # Check if value is within tolerance
            deviation = abs(actual_value - metric.expected_value)
            success = deviation <= metric.tolerance
            
            result = {
                "metric_name": metric.metric_name,
                "metric_type": metric.metric_type,
                "expected_value": metric.expected_value,
                "actual_value": actual_value,
                "tolerance": metric.tolerance,
                "deviation": deviation,
                "success": success,
                "critical": metric.critical,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error validating metric {metric.metric_name}: {e}")
            return {
                "metric_name": metric.metric_name,
                "metric_type": metric.metric_type,
                "expected_value": metric.expected_value,
                "actual_value": None,
                "tolerance": metric.tolerance,
                "deviation": float('inf'),
                "success": False,
                "critical": metric.critical,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _get_cloudwatch_metric(self, metric_name: str, service: str) -> float:
        """Get metric value from CloudWatch"""
        try:
            cloudwatch = await self.aws_factory.get_cloudwatch_client()
            
            # Get metric data for the last 5 minutes
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=5)
            
            response = await cloudwatch.get_metric_statistics(
                Namespace="AWS/ApplicationELB",  # Example namespace
                MetricName=metric_name,
                Dimensions=[
                    {
                        'Name': 'LoadBalancer',
                        'Value': service
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,  # 5-minute period
                Statistics=['Average']
            )
            
            if response.get('Datapoints'):
                # Get the most recent datapoint
                latest_datapoint = max(response['Datapoints'], key=lambda x: x['Timestamp'])
                return latest_datapoint['Average']
            else:
                logger.warning(f"No CloudWatch data found for metric {metric_name}")
                return 0.0
                
        except Exception as e:
            logger.error(f"Error getting CloudWatch metric {metric_name}: {e}")
            raise
    
    async def _perform_health_check(self, service: str) -> float:
        """Perform health check on service"""
        try:
            # In a real implementation, this would make HTTP requests to health endpoints
            # For now, simulate health check
            import random
            
            # Simulate health check with 90% success rate
            is_healthy = random.random() > 0.1
            return 1.0 if is_healthy else 0.0
            
        except Exception as e:
            logger.error(f"Error performing health check for {service}: {e}")
            return 0.0
    
    async def _get_custom_metric(self, metric_name: str, service: str) -> float:
        """Get custom metric value"""
        try:
            # In a real implementation, this would query custom metrics
            # For now, simulate based on metric name
            if metric_name == "InstanceCount":
                # Simulate getting instance count
                return 3.0
            elif metric_name == "RequestRate":
                # Simulate request rate
                return 800.0
            else:
                return 1.0
                
        except Exception as e:
            logger.error(f"Error getting custom metric {metric_name}: {e}")
            raise
    
    async def _detect_regression(
        self,
        validation_id: str,
        current_metrics: List[Dict[str, Any]]
    ) -> bool:
        """Detect if there's a regression in metrics"""
        try:
            validation_info = self.active_validations[validation_id]
            previous_results = validation_info.get("validation_results", [])
            
            if len(previous_results) < 2:
                return False  # Need at least 2 data points
            
            # Check for degrading trends
            for current_metric in current_metrics:
                metric_name = current_metric["metric_name"]
                current_value = current_metric.get("actual_value")
                
                if current_value is None:
                    continue
                
                # Get previous values for this metric
                previous_values = []
                for prev_result in previous_results[-3:]:  # Last 3 results
                    for prev_metric in prev_result.validation_metrics:
                        if prev_metric["metric_name"] == metric_name:
                            prev_value = prev_metric.get("actual_value")
                            if prev_value is not None:
                                previous_values.append(prev_value)
                
                if len(previous_values) >= 2:
                    # Check for degrading trend
                    avg_previous = sum(previous_values) / len(previous_values)
                    
                    # Define regression thresholds based on metric type
                    if metric_name in ["CPUUtilization", "ResponseTime", "ErrorRate"]:
                        # For these metrics, higher values are worse
                        regression_threshold = 1.2  # 20% increase is regression
                        if current_value > avg_previous * regression_threshold:
                            logger.warning(f"Regression detected in {metric_name}: {current_value} > {avg_previous * regression_threshold}")
                            return True
                    else:
                        # For other metrics, lower values might be worse
                        regression_threshold = 0.8  # 20% decrease is regression
                        if current_value < avg_previous * regression_threshold:
                            logger.warning(f"Regression detected in {metric_name}: {current_value} < {avg_previous * regression_threshold}")
                            return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error detecting regression for {validation_id}: {e}")
            return False
    
    async def _trigger_rollback(self, validation_id: str, result: ValidationResult):
        """Trigger rollback for failed validation"""
        try:
            validation_info = self.active_validations[validation_id]
            action_id = validation_info["action_id"]
            
            logger.warning(f"Triggering rollback for action {action_id} due to validation failure")
            
            # In a real implementation, this would trigger the rollback mechanism
            # For now, just log the rollback trigger
            rollback_info = {
                "action_id": action_id,
                "validation_id": validation_id,
                "rollback_reason": "validation_failure",
                "validation_errors": result.validation_errors,
                "success_score": result.success_score,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Rollback triggered: {json.dumps(rollback_info, indent=2)}")
            
            # Update validation status
            validation_info["status"] = ValidationStatus.ROLLBACK_REQUIRED
            
        except Exception as e:
            logger.error(f"Error triggering rollback for {validation_id}: {e}")
    
    async def get_validation_status(self, validation_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a validation"""
        try:
            if validation_id in self.active_validations:
                return self.active_validations[validation_id]
            elif validation_id in self.validation_history:
                return self.validation_history[validation_id]
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting validation status for {validation_id}: {e}")
            return None
    
    async def get_validation_statistics(self) -> Dict[str, Any]:
        """Get statistics about validation performance"""
        try:
            active_count = len(self.active_validations)
            completed_count = len(self.validation_history)
            
            # Calculate success rate from history
            successful_validations = sum(
                1 for v in self.validation_history.values()
                if v["status"] == ValidationStatus.SUCCESS
            )
            
            success_rate = successful_validations / completed_count if completed_count > 0 else 0.0
            
            stats = {
                "active_validations": active_count,
                "completed_validations": completed_count,
                "success_rate": success_rate,
                "validation_window_minutes": self.validation_window.total_seconds() / 60,
                "regression_monitoring_minutes": self.regression_monitoring_window.total_seconds() / 60,
                "supported_action_types": list(self.default_metrics.keys())
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting validation statistics: {e}")
            return {"error": str(e)}