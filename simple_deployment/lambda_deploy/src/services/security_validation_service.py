"""
Security Validation Service

Provides comprehensive security validation for resolution actions including:
- Action whitelist validation
- Permission validation against allowed action mappings
- Cryptographic action verification
- Privilege escalation prevention
"""

import asyncio
import hashlib
import hmac
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum

from src.utils.logging import get_logger
from src.utils.exceptions import SecurityError, ValidationError

logger = get_logger(__name__)


class SecurityLevel(Enum):
    """Security levels for actions"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ActionPermission:
    """Represents a permission required for an action"""
    service: str
    action: str
    resource: str
    conditions: Dict[str, Any] = None
    
    def to_arn_pattern(self) -> str:
        """Convert to AWS ARN pattern"""
        return f"arn:aws:{self.service}:*:*:{self.resource}"


@dataclass
class SecurityValidationResult:
    """Result of security validation"""
    is_valid: bool
    security_level: SecurityLevel
    required_permissions: List[ActionPermission]
    validation_errors: List[str]
    approval_required: bool
    estimated_risk_score: float
    validation_timestamp: datetime
    
    @property
    def is_approved(self) -> bool:
        """Check if action is approved for execution"""
        return self.is_valid and not self.approval_required


class ActionWhitelist:
    """Manages whitelist of pre-approved resolution actions"""
    
    def __init__(self):
        self.whitelisted_actions = self._initialize_whitelist()
        self.permission_mappings = self._initialize_permission_mappings()
        logger.info(f"Initialized action whitelist with {len(self.whitelisted_actions)} approved actions")
    
    def _initialize_whitelist(self) -> Dict[str, Dict[str, Any]]:
        """Initialize the whitelist of approved actions"""
        return {
            # Auto-scaling actions
            "scale_up_instances": {
                "description": "Scale up EC2 instances",
                "security_level": SecurityLevel.LOW,
                "max_instances": 10,
                "allowed_instance_types": ["t3.micro", "t3.small", "t3.medium"],
                "requires_approval": False
            },
            "scale_down_instances": {
                "description": "Scale down EC2 instances",
                "security_level": SecurityLevel.LOW,
                "min_instances": 1,
                "requires_approval": False
            },
            
            # Service management actions
            "restart_service": {
                "description": "Restart application service",
                "security_level": SecurityLevel.MEDIUM,
                "allowed_services": ["web-app", "api-service", "worker-service"],
                "requires_approval": False
            },
            "stop_service": {
                "description": "Stop application service",
                "security_level": SecurityLevel.HIGH,
                "allowed_services": ["worker-service", "batch-processor"],
                "requires_approval": True
            },
            
            # Database actions
            "restart_database_replica": {
                "description": "Restart database read replica",
                "security_level": SecurityLevel.MEDIUM,
                "allowed_db_types": ["read-replica"],
                "requires_approval": False
            },
            "scale_database_connections": {
                "description": "Adjust database connection pool",
                "security_level": SecurityLevel.LOW,
                "max_connections": 1000,
                "requires_approval": False
            },
            
            # Network actions
            "enable_rate_limiting": {
                "description": "Enable API rate limiting",
                "security_level": SecurityLevel.LOW,
                "max_rate_limit": 1000,
                "requires_approval": False
            },
            "block_ip_range": {
                "description": "Block suspicious IP range",
                "security_level": SecurityLevel.HIGH,
                "max_block_duration_hours": 24,
                "requires_approval": True
            },
            
            # Storage actions
            "clear_cache": {
                "description": "Clear application cache",
                "security_level": SecurityLevel.LOW,
                "allowed_cache_types": ["redis", "memcached", "application"],
                "requires_approval": False
            },
            "cleanup_logs": {
                "description": "Clean up old log files",
                "security_level": SecurityLevel.LOW,
                "min_retention_days": 7,
                "requires_approval": False
            },
            
            # Load balancer actions
            "drain_unhealthy_instances": {
                "description": "Drain traffic from unhealthy instances",
                "security_level": SecurityLevel.MEDIUM,
                "requires_approval": False
            },
            "adjust_health_check": {
                "description": "Adjust health check parameters",
                "security_level": SecurityLevel.LOW,
                "requires_approval": False
            }
        }
    
    def _initialize_permission_mappings(self) -> Dict[str, List[ActionPermission]]:
        """Initialize permission mappings for each action"""
        return {
            "scale_up_instances": [
                ActionPermission("ec2", "RunInstances", "instance/*"),
                ActionPermission("autoscaling", "UpdateAutoScalingGroup", "autoScalingGroup/*")
            ],
            "scale_down_instances": [
                ActionPermission("ec2", "TerminateInstances", "instance/*"),
                ActionPermission("autoscaling", "UpdateAutoScalingGroup", "autoScalingGroup/*")
            ],
            "restart_service": [
                ActionPermission("ecs", "UpdateService", "service/*"),
                ActionPermission("ecs", "StopTask", "task/*"),
                ActionPermission("ecs", "StartTask", "task/*")
            ],
            "stop_service": [
                ActionPermission("ecs", "UpdateService", "service/*"),
                ActionPermission("ecs", "StopTask", "task/*")
            ],
            "restart_database_replica": [
                ActionPermission("rds", "RebootDBInstance", "db/*"),
                ActionPermission("rds", "DescribeDBInstances", "db/*")
            ],
            "scale_database_connections": [
                ActionPermission("rds", "ModifyDBParameterGroup", "pg/*"),
                ActionPermission("rds", "DescribeDBParameterGroups", "pg/*")
            ],
            "enable_rate_limiting": [
                ActionPermission("apigateway", "UpdateStage", "stage/*"),
                ActionPermission("apigateway", "CreateUsagePlan", "usageplan/*")
            ],
            "block_ip_range": [
                ActionPermission("ec2", "AuthorizeSecurityGroupIngress", "security-group/*"),
                ActionPermission("ec2", "RevokeSecurityGroupIngress", "security-group/*")
            ],
            "clear_cache": [
                ActionPermission("elasticache", "RebootCacheCluster", "cluster/*"),
                ActionPermission("elasticache", "DescribeCacheClusters", "cluster/*")
            ],
            "cleanup_logs": [
                ActionPermission("logs", "DeleteLogGroup", "log-group/*"),
                ActionPermission("logs", "DescribeLogGroups", "log-group/*")
            ],
            "drain_unhealthy_instances": [
                ActionPermission("elbv2", "ModifyTargetGroup", "targetgroup/*"),
                ActionPermission("elbv2", "DeregisterTargets", "targetgroup/*")
            ],
            "adjust_health_check": [
                ActionPermission("elbv2", "ModifyTargetGroup", "targetgroup/*"),
                ActionPermission("elbv2", "DescribeTargetHealth", "targetgroup/*")
            ]
        }
    
    def is_action_whitelisted(self, action_id: str) -> bool:
        """Check if an action is in the whitelist"""
        return action_id in self.whitelisted_actions
    
    def get_action_config(self, action_id: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a whitelisted action"""
        return self.whitelisted_actions.get(action_id)
    
    def get_required_permissions(self, action_id: str) -> List[ActionPermission]:
        """Get required permissions for an action"""
        return self.permission_mappings.get(action_id, [])


class CryptographicValidator:
    """Handles cryptographic verification of actions"""
    
    def __init__(self, secret_key: str = None):
        # In production, this would come from AWS Secrets Manager
        self.secret_key = secret_key or "default-secret-key-change-in-production"
        self.algorithm = "sha256"
    
    def generate_action_signature(self, action_data: Dict[str, Any]) -> str:
        """Generate cryptographic signature for an action"""
        try:
            # Create canonical representation of action data
            canonical_data = self._canonicalize_action_data(action_data)
            
            # Generate HMAC signature
            signature = hmac.new(
                self.secret_key.encode(),
                canonical_data.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return signature
            
        except Exception as e:
            logger.error(f"Error generating action signature: {e}")
            raise SecurityError(f"Failed to generate action signature: {str(e)}")
    
    def verify_action_signature(self, action_data: Dict[str, Any], signature: str) -> bool:
        """Verify cryptographic signature of an action"""
        try:
            expected_signature = self.generate_action_signature(action_data)
            
            # Use constant-time comparison to prevent timing attacks
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            logger.error(f"Error verifying action signature: {e}")
            return False
    
    def _canonicalize_action_data(self, action_data: Dict[str, Any]) -> str:
        """Create canonical string representation of action data"""
        try:
            # Sort keys and create deterministic JSON
            canonical_json = json.dumps(action_data, sort_keys=True, separators=(',', ':'))
            return canonical_json
            
        except Exception as e:
            logger.error(f"Error canonicalizing action data: {e}")
            raise SecurityError(f"Failed to canonicalize action data: {str(e)}")


class PrivilegeEscalationDetector:
    """Detects potential privilege escalation attempts"""
    
    def __init__(self):
        self.suspicious_patterns = [
            # IAM-related escalations
            "iam:CreateRole",
            "iam:AttachRolePolicy",
            "iam:PutRolePolicy",
            "iam:CreateUser",
            "iam:AttachUserPolicy",
            
            # Administrative actions
            "sts:AssumeRole",
            "*:*",  # Wildcard permissions
            
            # Security group modifications
            "ec2:AuthorizeSecurityGroupIngress",
            "ec2:CreateSecurityGroup",
            
            # Lambda function modifications
            "lambda:UpdateFunctionCode",
            "lambda:CreateFunction",
            
            # S3 bucket policy changes
            "s3:PutBucketPolicy",
            "s3:PutBucketAcl"
        ]
        
        self.high_risk_resources = [
            "arn:aws:iam::*:role/*",
            "arn:aws:iam::*:user/*",
            "arn:aws:iam::*:policy/*",
            "*"  # Wildcard resources
        ]
    
    def detect_privilege_escalation(self, permissions: List[ActionPermission]) -> List[str]:
        """Detect potential privilege escalation attempts"""
        try:
            escalation_risks = []
            
            for permission in permissions:
                # Check for suspicious action patterns
                action_key = f"{permission.service}:{permission.action}"
                if any(pattern in action_key for pattern in self.suspicious_patterns):
                    escalation_risks.append(
                        f"Suspicious action detected: {action_key}"
                    )
                
                # Check for high-risk resources
                resource_arn = permission.to_arn_pattern()
                if any(risk_pattern in resource_arn for risk_pattern in self.high_risk_resources):
                    escalation_risks.append(
                        f"High-risk resource access: {resource_arn}"
                    )
                
                # Check for overly broad permissions
                if "*" in permission.action or "*" in permission.resource:
                    escalation_risks.append(
                        f"Overly broad permission: {action_key} on {resource_arn}"
                    )
            
            return escalation_risks
            
        except Exception as e:
            logger.error(f"Error detecting privilege escalation: {e}")
            return [f"Error in privilege escalation detection: {str(e)}"]


class SecurityValidationService:
    """Main security validation service"""
    
    def __init__(self, secret_key: str = None):
        self.whitelist = ActionWhitelist()
        self.crypto_validator = CryptographicValidator(secret_key)
        self.escalation_detector = PrivilegeEscalationDetector()
        
        # Risk scoring weights
        self.risk_weights = {
            SecurityLevel.LOW: 0.1,
            SecurityLevel.MEDIUM: 0.3,
            SecurityLevel.HIGH: 0.7,
            SecurityLevel.CRITICAL: 1.0
        }
        
        logger.info("Initialized Security Validation Service")
    
    async def validate_action(
        self,
        action_id: str,
        action_parameters: Dict[str, Any],
        signature: str = None
    ) -> SecurityValidationResult:
        """
        Comprehensive security validation of a resolution action
        
        Args:
            action_id: Identifier of the action to validate
            action_parameters: Parameters for the action
            signature: Optional cryptographic signature
            
        Returns:
            SecurityValidationResult with validation details
        """
        try:
            logger.info(f"Validating action: {action_id}")
            
            validation_errors = []
            
            # 1. Check if action is whitelisted
            if not self.whitelist.is_action_whitelisted(action_id):
                validation_errors.append(f"Action {action_id} is not in the approved whitelist")
                return SecurityValidationResult(
                    is_valid=False,
                    security_level=SecurityLevel.CRITICAL,
                    required_permissions=[],
                    validation_errors=validation_errors,
                    approval_required=True,
                    estimated_risk_score=1.0,
                    validation_timestamp=datetime.utcnow()
                )
            
            # 2. Get action configuration
            action_config = self.whitelist.get_action_config(action_id)
            security_level = action_config["security_level"]
            
            # 3. Validate action parameters against configuration
            param_errors = await self._validate_action_parameters(
                action_id, action_parameters, action_config
            )
            validation_errors.extend(param_errors)
            
            # 4. Get required permissions
            required_permissions = self.whitelist.get_required_permissions(action_id)
            
            # 5. Check for privilege escalation
            escalation_risks = self.escalation_detector.detect_privilege_escalation(
                required_permissions
            )
            validation_errors.extend(escalation_risks)
            
            # 6. Verify cryptographic signature if provided
            if signature:
                action_data = {
                    "action_id": action_id,
                    "parameters": action_parameters,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                if not self.crypto_validator.verify_action_signature(action_data, signature):
                    validation_errors.append("Invalid cryptographic signature")
            
            # 7. Calculate risk score
            risk_score = self._calculate_risk_score(
                security_level, validation_errors, escalation_risks
            )
            
            # 8. Determine if approval is required
            approval_required = (
                action_config.get("requires_approval", False) or
                len(escalation_risks) > 0 or
                risk_score > 0.7
            )
            
            # 9. Final validation decision
            is_valid = len(validation_errors) == 0
            
            result = SecurityValidationResult(
                is_valid=is_valid,
                security_level=security_level,
                required_permissions=required_permissions,
                validation_errors=validation_errors,
                approval_required=approval_required,
                estimated_risk_score=risk_score,
                validation_timestamp=datetime.utcnow()
            )
            
            logger.info(
                f"Action {action_id} validation: valid={is_valid}, "
                f"risk={risk_score:.2f}, approval_required={approval_required}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error validating action {action_id}: {e}")
            return SecurityValidationResult(
                is_valid=False,
                security_level=SecurityLevel.CRITICAL,
                required_permissions=[],
                validation_errors=[f"Validation error: {str(e)}"],
                approval_required=True,
                estimated_risk_score=1.0,
                validation_timestamp=datetime.utcnow()
            )
    
    async def _validate_action_parameters(
        self,
        action_id: str,
        parameters: Dict[str, Any],
        config: Dict[str, Any]
    ) -> List[str]:
        """Validate action parameters against configuration constraints"""
        try:
            errors = []
            
            # Validate based on action type
            if action_id == "scale_up_instances":
                instance_count = parameters.get("instance_count", 0)
                max_instances = config.get("max_instances", 10)
                
                if instance_count > max_instances:
                    errors.append(f"Instance count {instance_count} exceeds maximum {max_instances}")
                
                instance_type = parameters.get("instance_type", "")
                allowed_types = config.get("allowed_instance_types", [])
                
                if instance_type and instance_type not in allowed_types:
                    errors.append(f"Instance type {instance_type} not in allowed types: {allowed_types}")
            
            elif action_id == "block_ip_range":
                duration_hours = parameters.get("duration_hours", 0)
                max_duration = config.get("max_block_duration_hours", 24)
                
                if duration_hours > max_duration:
                    errors.append(f"Block duration {duration_hours}h exceeds maximum {max_duration}h")
            
            elif action_id == "restart_service":
                service_name = parameters.get("service_name", "")
                allowed_services = config.get("allowed_services", [])
                
                if service_name and service_name not in allowed_services:
                    errors.append(f"Service {service_name} not in allowed services: {allowed_services}")
            
            # Add more parameter validations as needed
            
            return errors
            
        except Exception as e:
            logger.error(f"Error validating parameters for {action_id}: {e}")
            return [f"Parameter validation error: {str(e)}"]
    
    def _calculate_risk_score(
        self,
        security_level: SecurityLevel,
        validation_errors: List[str],
        escalation_risks: List[str]
    ) -> float:
        """Calculate overall risk score for the action"""
        try:
            # Base risk from security level
            base_risk = self.risk_weights[security_level]
            
            # Add risk for validation errors
            error_risk = len(validation_errors) * 0.2
            
            # Add risk for escalation attempts
            escalation_risk = len(escalation_risks) * 0.3
            
            # Calculate total risk (capped at 1.0)
            total_risk = min(base_risk + error_risk + escalation_risk, 1.0)
            
            return total_risk
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            return 1.0  # Maximum risk on error
    
    async def create_emergency_rollback_plan(
        self,
        action_id: str,
        action_parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create emergency rollback plan for an action"""
        try:
            rollback_plan = {
                "action_id": action_id,
                "rollback_actions": [],
                "dependencies": [],
                "estimated_rollback_time_minutes": 5,
                "requires_manual_intervention": False
            }
            
            # Define rollback actions based on original action
            if action_id == "scale_up_instances":
                rollback_plan["rollback_actions"] = [
                    {
                        "action": "scale_down_instances",
                        "parameters": {
                            "instance_count": action_parameters.get("instance_count", 0)
                        }
                    }
                ]
            
            elif action_id == "restart_service":
                rollback_plan["rollback_actions"] = [
                    {
                        "action": "check_service_health",
                        "parameters": {
                            "service_name": action_parameters.get("service_name")
                        }
                    }
                ]
                rollback_plan["requires_manual_intervention"] = True
            
            elif action_id == "block_ip_range":
                rollback_plan["rollback_actions"] = [
                    {
                        "action": "unblock_ip_range",
                        "parameters": {
                            "ip_range": action_parameters.get("ip_range")
                        }
                    }
                ]
            
            # Add more rollback plans as needed
            
            return rollback_plan
            
        except Exception as e:
            logger.error(f"Error creating rollback plan for {action_id}: {e}")
            return {
                "action_id": action_id,
                "rollback_actions": [],
                "error": str(e),
                "requires_manual_intervention": True
            }
    
    async def get_validation_statistics(self) -> Dict[str, Any]:
        """Get statistics about security validation"""
        try:
            stats = {
                "whitelisted_actions": len(self.whitelist.whitelisted_actions),
                "permission_mappings": len(self.whitelist.permission_mappings),
                "security_levels": {
                    level.value: sum(
                        1 for config in self.whitelist.whitelisted_actions.values()
                        if config["security_level"] == level
                    )
                    for level in SecurityLevel
                },
                "approval_required_actions": sum(
                    1 for config in self.whitelist.whitelisted_actions.values()
                    if config.get("requires_approval", False)
                ),
                "suspicious_patterns": len(self.escalation_detector.suspicious_patterns),
                "high_risk_resources": len(self.escalation_detector.high_risk_resources)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting validation statistics: {e}")
            return {"error": str(e)}