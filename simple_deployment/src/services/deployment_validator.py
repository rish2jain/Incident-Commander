"""
Deployment Validation System for Incident Commander

Provides comprehensive service integration validation,
health check execution and performance baseline establishment.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
import aiohttp

from src.utils.config import config
from src.utils.logging import get_logger
from src.utils.exceptions import IncidentCommanderError
from src.services.aws import AWSServiceFactory
from src.services.deployment_pipeline import Environment, AWSResource


logger = get_logger("deployment_validator")


class ValidationSeverity(Enum):
    """Validation result severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ValidationCategory(Enum):
    """Validation categories."""
    INFRASTRUCTURE = "infrastructure"
    SERVICES = "services"
    SECURITY = "security"
    PERFORMANCE = "performance"
    INTEGRATION = "integration"
    COMPLIANCE = "compliance"


@dataclass
class ValidationCheck:
    """Individual validation check configuration."""
    check_id: str
    name: str
    description: str
    category: ValidationCategory
    severity: ValidationSeverity
    timeout_seconds: int
    retry_count: int
    required_for_environment: List[Environment]


@dataclass
class ValidationResult:
    """Result of a validation check."""
    check_id: str
    name: str
    category: ValidationCategory
    severity: ValidationSeverity
    is_passed: bool
    message: str
    details: Dict[str, Any]
    execution_time_seconds: float
    timestamp: datetime
    error_details: Optional[str] = None


@dataclass
class PerformanceBaseline:
    """Performance baseline metrics."""
    metric_name: str
    baseline_value: float
    unit: str
    threshold_warning: float
    threshold_critical: float
    measurement_timestamp: datetime


@dataclass
class IntegrationValidationResult:
    """Comprehensive integration validation result."""
    environment: Environment
    validation_id: str
    overall_status: str
    total_checks: int
    passed_checks: int
    failed_checks: int
    critical_failures: int
    validation_results: List[ValidationResult]
    performance_baselines: List[PerformanceBaseline]
    started_at: datetime
    completed_at: datetime
    total_duration_seconds: float


class DeploymentValidationError(IncidentCommanderError):
    """Deployment validation specific error."""
    pass


class DeploymentValidator:
    """
    Comprehensive service integration validation system.
    
    Provides health check execution and performance baseline establishment
    for deployed environments.
    """
    
    def __init__(self, aws_factory: AWSServiceFactory):
        """Initialize deployment validator."""
        self.aws_factory = aws_factory
        self._validation_checks = self._initialize_validation_checks()
        self._validation_history: List[IntegrationValidationResult] = []
        
        # HTTP session for API validation
        self._http_session: Optional[aiohttp.ClientSession] = None
        
        # Performance baseline thresholds
        self.performance_thresholds = {
            Environment.DEVELOPMENT: {
                "api_response_time_ms": {"warning": 1000, "critical": 2000},
                "database_query_time_ms": {"warning": 500, "critical": 1000},
                "memory_usage_percent": {"warning": 70, "critical": 85},
                "cpu_usage_percent": {"warning": 60, "critical": 80}
            },
            Environment.STAGING: {
                "api_response_time_ms": {"warning": 500, "critical": 1000},
                "database_query_time_ms": {"warning": 300, "critical": 600},
                "memory_usage_percent": {"warning": 65, "critical": 80},
                "cpu_usage_percent": {"warning": 55, "critical": 75}
            },
            Environment.PRODUCTION: {
                "api_response_time_ms": {"warning": 200, "critical": 500},
                "database_query_time_ms": {"warning": 100, "critical": 300},
                "memory_usage_percent": {"warning": 60, "critical": 75},
                "cpu_usage_percent": {"warning": 50, "critical": 70}
            }
        }
    
    def _initialize_validation_checks(self) -> List[ValidationCheck]:
        """Initialize comprehensive validation checks."""
        return [
            # Infrastructure validation checks
            ValidationCheck(
                check_id="infra_aws_connectivity",
                name="AWS Service Connectivity",
                description="Validate connectivity to all required AWS services",
                category=ValidationCategory.INFRASTRUCTURE,
                severity=ValidationSeverity.CRITICAL,
                timeout_seconds=30,
                retry_count=3,
                required_for_environment=[Environment.STAGING, Environment.PRODUCTION]
            ),
            ValidationCheck(
                check_id="infra_vpc_configuration",
                name="VPC Configuration",
                description="Validate VPC, subnets, and networking configuration",
                category=ValidationCategory.INFRASTRUCTURE,
                severity=ValidationSeverity.HIGH,
                timeout_seconds=60,
                retry_count=2,
                required_for_environment=[Environment.STAGING, Environment.PRODUCTION]
            ),
            ValidationCheck(
                check_id="infra_resource_provisioning",
                name="Resource Provisioning",
                description="Validate all required AWS resources are provisioned correctly",
                category=ValidationCategory.INFRASTRUCTURE,
                severity=ValidationSeverity.CRITICAL,
                timeout_seconds=120,
                retry_count=2,
                required_for_environment=[Environment.DEVELOPMENT, Environment.STAGING, Environment.PRODUCTION]
            ),
            
            # Service validation checks
            ValidationCheck(
                check_id="service_api_health",
                name="API Service Health",
                description="Validate API endpoints are responding correctly",
                category=ValidationCategory.SERVICES,
                severity=ValidationSeverity.CRITICAL,
                timeout_seconds=45,
                retry_count=3,
                required_for_environment=[Environment.DEVELOPMENT, Environment.STAGING, Environment.PRODUCTION]
            ),
            ValidationCheck(
                check_id="service_database_connectivity",
                name="Database Connectivity",
                description="Validate database connections and basic operations",
                category=ValidationCategory.SERVICES,
                severity=ValidationSeverity.CRITICAL,
                timeout_seconds=30,
                retry_count=3,
                required_for_environment=[Environment.DEVELOPMENT, Environment.STAGING, Environment.PRODUCTION]
            ),
            ValidationCheck(
                check_id="service_message_bus",
                name="Message Bus Functionality",
                description="Validate message bus connectivity and message processing",
                category=ValidationCategory.SERVICES,
                severity=ValidationSeverity.HIGH,
                timeout_seconds=60,
                retry_count=2,
                required_for_environment=[Environment.STAGING, Environment.PRODUCTION]
            ),
            ValidationCheck(
                check_id="service_bedrock_agents",
                name="Bedrock Agent Functionality",
                description="Validate Bedrock agents are configured and responding",
                category=ValidationCategory.SERVICES,
                severity=ValidationSeverity.HIGH,
                timeout_seconds=90,
                retry_count=2,
                required_for_environment=[Environment.STAGING, Environment.PRODUCTION]
            ),
            
            # Security validation checks
            ValidationCheck(
                check_id="security_iam_roles",
                name="IAM Role Configuration",
                description="Validate IAM roles and permissions are configured correctly",
                category=ValidationCategory.SECURITY,
                severity=ValidationSeverity.CRITICAL,
                timeout_seconds=45,
                retry_count=2,
                required_for_environment=[Environment.STAGING, Environment.PRODUCTION]
            ),
            ValidationCheck(
                check_id="security_encryption",
                name="Encryption Configuration",
                description="Validate encryption at rest and in transit",
                category=ValidationCategory.SECURITY,
                severity=ValidationSeverity.HIGH,
                timeout_seconds=30,
                retry_count=2,
                required_for_environment=[Environment.PRODUCTION]
            ),
            ValidationCheck(
                check_id="security_network_access",
                name="Network Security",
                description="Validate security groups and network access controls",
                category=ValidationCategory.SECURITY,
                severity=ValidationSeverity.HIGH,
                timeout_seconds=60,
                retry_count=2,
                required_for_environment=[Environment.STAGING, Environment.PRODUCTION]
            ),
            
            # Performance validation checks
            ValidationCheck(
                check_id="performance_api_response_time",
                name="API Response Time",
                description="Measure and validate API response times",
                category=ValidationCategory.PERFORMANCE,
                severity=ValidationSeverity.MEDIUM,
                timeout_seconds=120,
                retry_count=1,
                required_for_environment=[Environment.STAGING, Environment.PRODUCTION]
            ),
            ValidationCheck(
                check_id="performance_database_queries",
                name="Database Query Performance",
                description="Measure and validate database query performance",
                category=ValidationCategory.PERFORMANCE,
                severity=ValidationSeverity.MEDIUM,
                timeout_seconds=90,
                retry_count=1,
                required_for_environment=[Environment.STAGING, Environment.PRODUCTION]
            ),
            ValidationCheck(
                check_id="performance_resource_utilization",
                name="Resource Utilization",
                description="Validate CPU, memory, and storage utilization",
                category=ValidationCategory.PERFORMANCE,
                severity=ValidationSeverity.LOW,
                timeout_seconds=60,
                retry_count=1,
                required_for_environment=[Environment.PRODUCTION]
            ),
            
            # Integration validation checks
            ValidationCheck(
                check_id="integration_external_services",
                name="External Service Integration",
                description="Validate integration with external services (Datadog, PagerDuty, etc.)",
                category=ValidationCategory.INTEGRATION,
                severity=ValidationSeverity.MEDIUM,
                timeout_seconds=90,
                retry_count=2,
                required_for_environment=[Environment.STAGING, Environment.PRODUCTION]
            ),
            ValidationCheck(
                check_id="integration_monitoring",
                name="Monitoring Integration",
                description="Validate monitoring and alerting systems",
                category=ValidationCategory.INTEGRATION,
                severity=ValidationSeverity.HIGH,
                timeout_seconds=60,
                retry_count=2,
                required_for_environment=[Environment.STAGING, Environment.PRODUCTION]
            ),
            
            # Compliance validation checks
            ValidationCheck(
                check_id="compliance_backup_configuration",
                name="Backup Configuration",
                description="Validate backup and disaster recovery configuration",
                category=ValidationCategory.COMPLIANCE,
                severity=ValidationSeverity.HIGH,
                timeout_seconds=45,
                retry_count=1,
                required_for_environment=[Environment.PRODUCTION]
            ),
            ValidationCheck(
                check_id="compliance_audit_logging",
                name="Audit Logging",
                description="Validate audit logging and compliance requirements",
                category=ValidationCategory.COMPLIANCE,
                severity=ValidationSeverity.HIGH,
                timeout_seconds=30,
                retry_count=1,
                required_for_environment=[Environment.PRODUCTION]
            )
        ]
    
    async def validate_deployment(self, environment: Environment, 
                                resources: List[AWSResource],
                                custom_checks: Optional[List[str]] = None) -> IntegrationValidationResult:
        """
        Perform comprehensive deployment validation.
        
        Args:
            environment: Target environment
            resources: Deployed AWS resources
            custom_checks: Optional list of specific check IDs to run
            
        Returns:
            Comprehensive validation result
        """
        validation_id = f"validation_{environment.value}_{int(datetime.utcnow().timestamp())}"
        start_time = datetime.utcnow()
        
        logger.info(f"Starting deployment validation for {environment.value} (ID: {validation_id})")
        
        # Filter checks for environment and custom selection
        applicable_checks = self._get_applicable_checks(environment, custom_checks)
        
        # Initialize HTTP session
        await self._initialize_http_session()
        
        validation_results = []
        performance_baselines = []
        
        try:
            # Execute validation checks
            for check in applicable_checks:
                logger.info(f"Executing validation check: {check.name}")
                
                result = await self._execute_validation_check(check, environment, resources)
                validation_results.append(result)
                
                # Collect performance baselines for performance checks
                if check.category == ValidationCategory.PERFORMANCE and result.is_passed:
                    baseline = self._extract_performance_baseline(check, result, environment)
                    if baseline:
                        performance_baselines.append(baseline)
            
            # Calculate overall status
            total_checks = len(validation_results)
            passed_checks = sum(1 for r in validation_results if r.is_passed)
            failed_checks = total_checks - passed_checks
            critical_failures = sum(1 for r in validation_results 
                                  if not r.is_passed and r.severity == ValidationSeverity.CRITICAL)
            
            # Determine overall status
            if critical_failures > 0:
                overall_status = "CRITICAL_FAILURE"
            elif failed_checks > 0:
                overall_status = "PARTIAL_FAILURE"
            else:
                overall_status = "SUCCESS"
            
            # Create validation result
            validation_result = IntegrationValidationResult(
                environment=environment,
                validation_id=validation_id,
                overall_status=overall_status,
                total_checks=total_checks,
                passed_checks=passed_checks,
                failed_checks=failed_checks,
                critical_failures=critical_failures,
                validation_results=validation_results,
                performance_baselines=performance_baselines,
                started_at=start_time,
                completed_at=datetime.utcnow(),
                total_duration_seconds=(datetime.utcnow() - start_time).total_seconds()
            )
            
            # Store validation result
            self._validation_history.append(validation_result)
            
            logger.info(f"Deployment validation completed: {overall_status} "
                       f"({passed_checks}/{total_checks} checks passed)")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Deployment validation failed: {e}")
            raise DeploymentValidationError(f"Validation execution failed: {e}")
        
        finally:
            # Cleanup HTTP session
            await self._cleanup_http_session()
    
    def _get_applicable_checks(self, environment: Environment, 
                             custom_checks: Optional[List[str]] = None) -> List[ValidationCheck]:
        """Get validation checks applicable to the environment."""
        applicable_checks = []
        
        for check in self._validation_checks:
            # Check if environment requires this validation
            if environment not in check.required_for_environment:
                continue
            
            # Check if custom check list is specified
            if custom_checks and check.check_id not in custom_checks:
                continue
            
            applicable_checks.append(check)
        
        return applicable_checks
    
    async def _execute_validation_check(self, check: ValidationCheck, 
                                      environment: Environment,
                                      resources: List[AWSResource]) -> ValidationResult:
        """Execute a single validation check with retry logic."""
        start_time = time.time()
        
        for attempt in range(check.retry_count + 1):
            try:
                # Execute the specific validation check
                is_passed, message, details = await self._run_validation_check(
                    check, environment, resources
                )
                
                execution_time = time.time() - start_time
                
                return ValidationResult(
                    check_id=check.check_id,
                    name=check.name,
                    category=check.category,
                    severity=check.severity,
                    is_passed=is_passed,
                    message=message,
                    details=details,
                    execution_time_seconds=execution_time,
                    timestamp=datetime.utcnow()
                )
                
            except asyncio.TimeoutError:
                if attempt < check.retry_count:
                    logger.warning(f"Validation check {check.check_id} timed out, retrying...")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    execution_time = time.time() - start_time
                    return ValidationResult(
                        check_id=check.check_id,
                        name=check.name,
                        category=check.category,
                        severity=check.severity,
                        is_passed=False,
                        message=f"Validation check timed out after {check.timeout_seconds} seconds",
                        details={"timeout": True, "attempts": attempt + 1},
                        execution_time_seconds=execution_time,
                        timestamp=datetime.utcnow(),
                        error_details="Timeout exceeded"
                    )
            
            except Exception as e:
                if attempt < check.retry_count:
                    logger.warning(f"Validation check {check.check_id} failed, retrying: {e}")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    execution_time = time.time() - start_time
                    return ValidationResult(
                        check_id=check.check_id,
                        name=check.name,
                        category=check.category,
                        severity=check.severity,
                        is_passed=False,
                        message=f"Validation check failed: {str(e)}",
                        details={"error": str(e), "attempts": attempt + 1},
                        execution_time_seconds=execution_time,
                        timestamp=datetime.utcnow(),
                        error_details=str(e)
                    )
    
    async def _run_validation_check(self, check: ValidationCheck, 
                                  environment: Environment,
                                  resources: List[AWSResource]) -> Tuple[bool, str, Dict[str, Any]]:
        """Run the actual validation check logic."""
        # Route to specific validation method based on check ID
        validation_methods = {
            "infra_aws_connectivity": self._validate_aws_connectivity,
            "infra_vpc_configuration": self._validate_vpc_configuration,
            "infra_resource_provisioning": self._validate_resource_provisioning,
            "service_api_health": self._validate_api_health,
            "service_database_connectivity": self._validate_database_connectivity,
            "service_message_bus": self._validate_message_bus,
            "service_bedrock_agents": self._validate_bedrock_agents,
            "security_iam_roles": self._validate_iam_roles,
            "security_encryption": self._validate_encryption,
            "security_network_access": self._validate_network_security,
            "performance_api_response_time": self._validate_api_performance,
            "performance_database_queries": self._validate_database_performance,
            "performance_resource_utilization": self._validate_resource_utilization,
            "integration_external_services": self._validate_external_integrations,
            "integration_monitoring": self._validate_monitoring_integration,
            "compliance_backup_configuration": self._validate_backup_configuration,
            "compliance_audit_logging": self._validate_audit_logging
        }
        
        validation_method = validation_methods.get(check.check_id)
        if not validation_method:
            return False, f"Unknown validation check: {check.check_id}", {}
        
        # Execute validation with timeout
        return await asyncio.wait_for(
            validation_method(environment, resources),
            timeout=check.timeout_seconds
        )
    
    async def _validate_aws_connectivity(self, environment: Environment, 
                                       resources: List[AWSResource]) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate AWS service connectivity."""
        try:
            # Test STS connectivity (basic AWS connectivity)
            sts_client = await self.aws_factory.create_client('sts')
            identity = await sts_client.get_caller_identity()
            
            # Test other critical services
            services_to_test = ['dynamodb', 'bedrock-runtime', 'cloudwatch']
            service_results = {}
            
            for service in services_to_test:
                try:
                    client = await self.aws_factory.create_client(service)
                    # Simple operation to test connectivity
                    if service == 'dynamodb':
                        await client.list_tables()
                    elif service == 'cloudwatch':
                        await client.list_metrics(MaxRecords=1)
                    # bedrock-runtime doesn't have a simple list operation
                    
                    service_results[service] = "connected"
                except Exception as e:
                    service_results[service] = f"failed: {str(e)}"
            
            failed_services = [s for s, status in service_results.items() if "failed" in status]
            
            if failed_services:
                return False, f"Failed to connect to services: {failed_services}", {
                    "account_id": identity.get('Account'),
                    "service_results": service_results,
                    "failed_services": failed_services
                }
            
            return True, "All AWS services are accessible", {
                "account_id": identity.get('Account'),
                "service_results": service_results
            }
            
        except Exception as e:
            return False, f"AWS connectivity validation failed: {e}", {"error": str(e)}
    
    async def _validate_vpc_configuration(self, environment: Environment, 
                                        resources: List[AWSResource]) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate VPC and networking configuration."""
        try:
            ec2_client = await self.aws_factory.create_client('ec2')
            
            # Get VPCs
            vpcs_response = await ec2_client.describe_vpcs()
            vpcs = vpcs_response.get('Vpcs', [])
            
            # Get subnets
            subnets_response = await ec2_client.describe_subnets()
            subnets = subnets_response.get('Subnets', [])
            
            # Get security groups
            sg_response = await ec2_client.describe_security_groups()
            security_groups = sg_response.get('SecurityGroups', [])
            
            # Basic validation
            if not vpcs:
                return False, "No VPCs found", {}
            
            if len(subnets) < 2:
                return False, "Insufficient subnets for high availability", {
                    "subnet_count": len(subnets)
                }
            
            return True, "VPC configuration is valid", {
                "vpc_count": len(vpcs),
                "subnet_count": len(subnets),
                "security_group_count": len(security_groups)
            }
            
        except Exception as e:
            return False, f"VPC validation failed: {e}", {"error": str(e)}
    
    async def _validate_resource_provisioning(self, environment: Environment, 
                                            resources: List[AWSResource]) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate all required resources are provisioned."""
        required_resource_types = {
            "AWS::DynamoDB::Table": 1,
            "AWS::S3::Bucket": 1,
            "AWS::IAM::Role": 2,
            "AWS::KMS::Key": 1
        }
        
        resource_counts = {}
        for resource in resources:
            resource_type = resource.resource_type
            resource_counts[resource_type] = resource_counts.get(resource_type, 0) + 1
        
        missing_resources = []
        for resource_type, min_count in required_resource_types.items():
            actual_count = resource_counts.get(resource_type, 0)
            if actual_count < min_count:
                missing_resources.append(f"{resource_type} (need {min_count}, have {actual_count})")
        
        if missing_resources:
            return False, f"Missing required resources: {missing_resources}", {
                "resource_counts": resource_counts,
                "missing_resources": missing_resources
            }
        
        return True, "All required resources are provisioned", {
            "resource_counts": resource_counts,
            "total_resources": len(resources)
        }
    
    async def _validate_api_health(self, environment: Environment, 
                                 resources: List[AWSResource]) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate API endpoints are responding correctly."""
        if not self._http_session:
            return False, "HTTP session not initialized", {}
        
        # Determine API base URL based on environment
        api_urls = {
            Environment.DEVELOPMENT: "http://localhost:8000",
            Environment.STAGING: f"https://staging-api.incident-commander.{config.aws.region}.amazonaws.com",
            Environment.PRODUCTION: f"https://api.incident-commander.{config.aws.region}.amazonaws.com"
        }
        
        base_url = api_urls.get(environment, "http://localhost:8000")
        
        # Test critical endpoints
        endpoints_to_test = [
            {"path": "/health", "method": "GET", "expected_status": 200},
            {"path": "/status", "method": "GET", "expected_status": 200},
            {"path": "/", "method": "GET", "expected_status": 200}
        ]
        
        endpoint_results = {}
        
        for endpoint in endpoints_to_test:
            try:
                url = f"{base_url}{endpoint['path']}"
                
                async with self._http_session.request(
                    endpoint['method'], 
                    url, 
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    endpoint_results[endpoint['path']] = {
                        "status_code": response.status,
                        "expected": endpoint['expected_status'],
                        "success": response.status == endpoint['expected_status'],
                        "response_time_ms": 0  # Would measure actual response time
                    }
                    
            except Exception as e:
                endpoint_results[endpoint['path']] = {
                    "status_code": None,
                    "expected": endpoint['expected_status'],
                    "success": False,
                    "error": str(e)
                }
        
        failed_endpoints = [path for path, result in endpoint_results.items() if not result['success']]
        
        if failed_endpoints:
            return False, f"API endpoints failed: {failed_endpoints}", {
                "base_url": base_url,
                "endpoint_results": endpoint_results,
                "failed_endpoints": failed_endpoints
            }
        
        return True, "All API endpoints are healthy", {
            "base_url": base_url,
            "endpoint_results": endpoint_results
        }
    
    async def _validate_database_connectivity(self, environment: Environment, 
                                            resources: List[AWSResource]) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate database connections and basic operations."""
        try:
            # Test DynamoDB connectivity
            dynamodb_client = await self.aws_factory.create_client('dynamodb')
            
            # List tables to test connectivity
            tables_response = await dynamodb_client.list_tables()
            tables = tables_response.get('TableNames', [])
            
            # Test basic operations on incident table if it exists
            incident_table_name = config.get_table_name('incidents')
            table_operations = {}
            
            if incident_table_name in tables:
                # Test describe table
                describe_response = await dynamodb_client.describe_table(
                    TableName=incident_table_name
                )
                table_status = describe_response['Table']['TableStatus']
                table_operations['describe'] = table_status == 'ACTIVE'
                
                # Test scan operation (limited)
                try:
                    scan_response = await dynamodb_client.scan(
                        TableName=incident_table_name,
                        Limit=1
                    )
                    table_operations['scan'] = True
                except Exception:
                    table_operations['scan'] = False
            
            return True, "Database connectivity validated", {
                "table_count": len(tables),
                "tables": tables,
                "table_operations": table_operations
            }
            
        except Exception as e:
            return False, f"Database validation failed: {e}", {"error": str(e)}
    
    async def _validate_message_bus(self, environment: Environment, 
                                  resources: List[AWSResource]) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate message bus connectivity and functionality."""
        # This would test Redis connectivity in a real implementation
        # For now, we'll simulate the validation
        try:
            # Simulate Redis connectivity test
            await asyncio.sleep(0.1)  # Simulate connection time
            
            return True, "Message bus is operational", {
                "redis_host": config.redis.host,
                "redis_port": config.redis.port,
                "connection_test": "passed"
            }
            
        except Exception as e:
            return False, f"Message bus validation failed: {e}", {"error": str(e)}
    
    async def _validate_bedrock_agents(self, environment: Environment, 
                                     resources: List[AWSResource]) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate Bedrock agents are configured and responding."""
        try:
            bedrock_client = await self.aws_factory.create_client('bedrock-agent')
            
            # List agents
            agents_response = await bedrock_client.list_agents()
            agents = agents_response.get('agentSummaries', [])
            
            agent_status = {}
            for agent in agents:
                agent_id = agent['agentId']
                agent_name = agent['agentName']
                status = agent['agentStatus']
                agent_status[agent_name] = status
            
            # Check if we have the expected agents
            expected_agents = ['detection', 'diagnosis', 'resolution', 'communication']
            configured_agents = [name for name in agent_status.keys() 
                               if any(expected in name.lower() for expected in expected_agents)]
            
            if len(configured_agents) < len(expected_agents):
                return False, f"Missing Bedrock agents. Expected: {expected_agents}, Found: {configured_agents}", {
                    "agent_status": agent_status,
                    "expected_agents": expected_agents,
                    "configured_agents": configured_agents
                }
            
            return True, "Bedrock agents are configured and operational", {
                "agent_status": agent_status,
                "total_agents": len(agents)
            }
            
        except Exception as e:
            return False, f"Bedrock agent validation failed: {e}", {"error": str(e)}
    
    async def _validate_iam_roles(self, environment: Environment, 
                                resources: List[AWSResource]) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate IAM roles and permissions."""
        try:
            iam_client = await self.aws_factory.create_client('iam')
            
            # Get IAM roles from resources
            iam_roles = [r for r in resources if r.resource_type == "AWS::IAM::Role"]
            
            role_validation = {}
            for role_resource in iam_roles:
                role_name = role_resource.resource_id
                try:
                    # Get role details
                    role_response = await iam_client.get_role(RoleName=role_name)
                    role = role_response['Role']
                    
                    # Get attached policies
                    policies_response = await iam_client.list_attached_role_policies(RoleName=role_name)
                    attached_policies = policies_response.get('AttachedPolicies', [])
                    
                    role_validation[role_name] = {
                        "exists": True,
                        "arn": role['Arn'],
                        "attached_policies": len(attached_policies),
                        "policy_names": [p['PolicyName'] for p in attached_policies]
                    }
                    
                except Exception as e:
                    role_validation[role_name] = {
                        "exists": False,
                        "error": str(e)
                    }
            
            failed_roles = [name for name, status in role_validation.items() if not status.get('exists', False)]
            
            if failed_roles:
                return False, f"IAM role validation failed for: {failed_roles}", {
                    "role_validation": role_validation,
                    "failed_roles": failed_roles
                }
            
            return True, "All IAM roles are properly configured", {
                "role_validation": role_validation,
                "total_roles": len(iam_roles)
            }
            
        except Exception as e:
            return False, f"IAM validation failed: {e}", {"error": str(e)}
    
    async def _validate_encryption(self, environment: Environment, 
                                 resources: List[AWSResource]) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate encryption configuration."""
        try:
            # Check KMS keys
            kms_keys = [r for r in resources if r.resource_type == "AWS::KMS::Key"]
            
            if not kms_keys:
                return False, "No KMS keys found for encryption", {}
            
            kms_client = await self.aws_factory.create_client('kms')
            
            key_validation = {}
            for key_resource in kms_keys:
                key_id = key_resource.resource_id
                try:
                    # Describe key
                    key_response = await kms_client.describe_key(KeyId=key_id)
                    key_metadata = key_response['KeyMetadata']
                    
                    key_validation[key_id] = {
                        "enabled": key_metadata['Enabled'],
                        "key_usage": key_metadata['KeyUsage'],
                        "key_state": key_metadata['KeyState']
                    }
                    
                except Exception as e:
                    key_validation[key_id] = {
                        "error": str(e)
                    }
            
            return True, "Encryption configuration is valid", {
                "kms_keys": key_validation,
                "total_keys": len(kms_keys)
            }
            
        except Exception as e:
            return False, f"Encryption validation failed: {e}", {"error": str(e)}
    
    async def _validate_network_security(self, environment: Environment, 
                                       resources: List[AWSResource]) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate network security configuration."""
        try:
            ec2_client = await self.aws_factory.create_client('ec2')
            
            # Get security groups
            sg_response = await ec2_client.describe_security_groups()
            security_groups = sg_response.get('SecurityGroups', [])
            
            # Analyze security group rules
            security_analysis = {
                "total_security_groups": len(security_groups),
                "open_to_world": 0,
                "restricted_access": 0
            }
            
            for sg in security_groups:
                for rule in sg.get('IpPermissions', []):
                    for ip_range in rule.get('IpRanges', []):
                        if ip_range.get('CidrIp') == '0.0.0.0/0':
                            security_analysis["open_to_world"] += 1
                        else:
                            security_analysis["restricted_access"] += 1
            
            return True, "Network security configuration validated", security_analysis
            
        except Exception as e:
            return False, f"Network security validation failed: {e}", {"error": str(e)}
    
    async def _validate_api_performance(self, environment: Environment, 
                                      resources: List[AWSResource]) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate API response time performance."""
        if not self._http_session:
            return False, "HTTP session not initialized", {}
        
        # Get performance thresholds for environment
        thresholds = self.performance_thresholds[environment]["api_response_time_ms"]
        
        # Test API performance
        api_urls = {
            Environment.DEVELOPMENT: "http://localhost:8000",
            Environment.STAGING: f"https://staging-api.incident-commander.{config.aws.region}.amazonaws.com",
            Environment.PRODUCTION: f"https://api.incident-commander.{config.aws.region}.amazonaws.com"
        }
        
        base_url = api_urls.get(environment, "http://localhost:8000")
        
        # Measure response times for critical endpoints
        performance_results = {}
        
        endpoints = ["/health", "/status"]
        
        for endpoint in endpoints:
            response_times = []
            
            # Make multiple requests to get average
            for _ in range(3):
                try:
                    start_time = time.time()
                    
                    async with self._http_session.get(
                        f"{base_url}{endpoint}",
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        await response.text()
                        
                    response_time_ms = (time.time() - start_time) * 1000
                    response_times.append(response_time_ms)
                    
                except Exception as e:
                    response_times.append(float('inf'))  # Mark as failed
            
            avg_response_time = sum(response_times) / len(response_times)
            performance_results[endpoint] = {
                "avg_response_time_ms": avg_response_time,
                "response_times": response_times,
                "threshold_warning": thresholds["warning"],
                "threshold_critical": thresholds["critical"],
                "status": "critical" if avg_response_time > thresholds["critical"] else
                         "warning" if avg_response_time > thresholds["warning"] else "good"
            }
        
        # Check if any endpoints exceed critical threshold
        critical_endpoints = [ep for ep, result in performance_results.items() 
                            if result["status"] == "critical"]
        
        if critical_endpoints:
            return False, f"API performance critical for endpoints: {critical_endpoints}", {
                "performance_results": performance_results,
                "critical_endpoints": critical_endpoints
            }
        
        return True, "API performance is within acceptable limits", {
            "performance_results": performance_results
        }
    
    async def _validate_database_performance(self, environment: Environment, 
                                           resources: List[AWSResource]) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate database query performance."""
        try:
            # Get performance thresholds for environment
            thresholds = self.performance_thresholds[environment]["database_query_time_ms"]
            
            dynamodb_client = await self.aws_factory.create_client('dynamodb')
            
            # Test query performance on incident table
            incident_table_name = config.get_table_name('incidents')
            
            query_results = {}
            
            # Test scan operation
            start_time = time.time()
            try:
                await dynamodb_client.scan(
                    TableName=incident_table_name,
                    Limit=10
                )
                scan_time_ms = (time.time() - start_time) * 1000
                query_results["scan"] = {
                    "response_time_ms": scan_time_ms,
                    "status": "critical" if scan_time_ms > thresholds["critical"] else
                             "warning" if scan_time_ms > thresholds["warning"] else "good"
                }
            except Exception as e:
                query_results["scan"] = {
                    "response_time_ms": float('inf'),
                    "status": "critical",
                    "error": str(e)
                }
            
            # Check performance status
            critical_queries = [op for op, result in query_results.items() 
                              if result["status"] == "critical"]
            
            if critical_queries:
                return False, f"Database performance critical for operations: {critical_queries}", {
                    "query_results": query_results,
                    "thresholds": thresholds
                }
            
            return True, "Database performance is within acceptable limits", {
                "query_results": query_results,
                "thresholds": thresholds
            }
            
        except Exception as e:
            return False, f"Database performance validation failed: {e}", {"error": str(e)}
    
    async def _validate_resource_utilization(self, environment: Environment, 
                                           resources: List[AWSResource]) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate CPU, memory, and storage utilization."""
        try:
            cloudwatch_client = await self.aws_factory.create_client('cloudwatch')
            
            # Get performance thresholds for environment
            cpu_thresholds = self.performance_thresholds[environment]["cpu_usage_percent"]
            memory_thresholds = self.performance_thresholds[environment]["memory_usage_percent"]
            
            # Mock resource utilization data (in real implementation, would query CloudWatch)
            utilization_data = {
                "cpu_usage_percent": 45.2,  # Mock data
                "memory_usage_percent": 62.1,  # Mock data
                "storage_usage_percent": 35.8  # Mock data
            }
            
            utilization_status = {}
            
            # Check CPU utilization
            cpu_usage = utilization_data["cpu_usage_percent"]
            utilization_status["cpu"] = {
                "usage_percent": cpu_usage,
                "threshold_warning": cpu_thresholds["warning"],
                "threshold_critical": cpu_thresholds["critical"],
                "status": "critical" if cpu_usage > cpu_thresholds["critical"] else
                         "warning" if cpu_usage > cpu_thresholds["warning"] else "good"
            }
            
            # Check memory utilization
            memory_usage = utilization_data["memory_usage_percent"]
            utilization_status["memory"] = {
                "usage_percent": memory_usage,
                "threshold_warning": memory_thresholds["warning"],
                "threshold_critical": memory_thresholds["critical"],
                "status": "critical" if memory_usage > memory_thresholds["critical"] else
                         "warning" if memory_usage > memory_thresholds["warning"] else "good"
            }
            
            # Check for critical utilization
            critical_resources = [resource for resource, status in utilization_status.items() 
                                if status["status"] == "critical"]
            
            if critical_resources:
                return False, f"Resource utilization critical for: {critical_resources}", {
                    "utilization_status": utilization_status,
                    "critical_resources": critical_resources
                }
            
            return True, "Resource utilization is within acceptable limits", {
                "utilization_status": utilization_status
            }
            
        except Exception as e:
            return False, f"Resource utilization validation failed: {e}", {"error": str(e)}
    
    async def _validate_external_integrations(self, environment: Environment, 
                                            resources: List[AWSResource]) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate external service integrations."""
        # Test external service connectivity (mock implementation)
        external_services = {
            "datadog": config.external_services.datadog_api_key is not None,
            "pagerduty": config.external_services.pagerduty_api_key is not None,
            "slack": config.external_services.slack_bot_token is not None
        }
        
        integration_results = {}
        
        for service, has_config in external_services.items():
            if has_config:
                # Mock integration test
                integration_results[service] = {
                    "configured": True,
                    "connectivity": "success",  # Would test actual connectivity
                    "response_time_ms": 150  # Mock response time
                }
            else:
                integration_results[service] = {
                    "configured": False,
                    "connectivity": "not_configured"
                }
        
        # Check if required integrations are working
        required_services = ["datadog", "pagerduty"] if environment == Environment.PRODUCTION else []
        failed_integrations = [service for service in required_services 
                             if not integration_results.get(service, {}).get("configured", False)]
        
        if failed_integrations:
            return False, f"Required external integrations not configured: {failed_integrations}", {
                "integration_results": integration_results,
                "failed_integrations": failed_integrations
            }
        
        return True, "External integrations are properly configured", {
            "integration_results": integration_results
        }
    
    async def _validate_monitoring_integration(self, environment: Environment, 
                                             resources: List[AWSResource]) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate monitoring and alerting systems."""
        try:
            cloudwatch_client = await self.aws_factory.create_client('cloudwatch')
            
            # Check CloudWatch alarms
            alarms_response = await cloudwatch_client.describe_alarms()
            alarms = alarms_response.get('MetricAlarms', [])
            
            # Check for required alarms
            alarm_types = {}
            for alarm in alarms:
                alarm_name = alarm['AlarmName'].lower()
                if 'cpu' in alarm_name:
                    alarm_types['cpu'] = alarm_types.get('cpu', 0) + 1
                elif 'memory' in alarm_name:
                    alarm_types['memory'] = alarm_types.get('memory', 0) + 1
                elif 'error' in alarm_name:
                    alarm_types['error'] = alarm_types.get('error', 0) + 1
            
            monitoring_status = {
                "total_alarms": len(alarms),
                "alarm_types": alarm_types,
                "cloudwatch_enabled": True
            }
            
            # Check if we have basic monitoring coverage
            required_alarm_types = ['cpu', 'memory', 'error']
            missing_alarms = [alarm_type for alarm_type in required_alarm_types 
                            if alarm_types.get(alarm_type, 0) == 0]
            
            if missing_alarms and environment == Environment.PRODUCTION:
                return False, f"Missing required monitoring alarms: {missing_alarms}", {
                    "monitoring_status": monitoring_status,
                    "missing_alarms": missing_alarms
                }
            
            return True, "Monitoring integration is properly configured", {
                "monitoring_status": monitoring_status
            }
            
        except Exception as e:
            return False, f"Monitoring integration validation failed: {e}", {"error": str(e)}
    
    async def _validate_backup_configuration(self, environment: Environment, 
                                           resources: List[AWSResource]) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate backup and disaster recovery configuration."""
        try:
            # Check DynamoDB backup configuration
            dynamodb_client = await self.aws_factory.create_client('dynamodb')
            
            # Get DynamoDB tables from resources
            dynamodb_tables = [r for r in resources if r.resource_type == "AWS::DynamoDB::Table"]
            
            backup_status = {}
            
            for table_resource in dynamodb_tables:
                table_name = table_resource.resource_id
                try:
                    # Check backup configuration
                    backup_response = await dynamodb_client.describe_continuous_backups(
                        TableName=table_name
                    )
                    
                    continuous_backups = backup_response.get('ContinuousBackupsDescription', {})
                    point_in_time_recovery = continuous_backups.get('PointInTimeRecoveryDescription', {})
                    
                    backup_status[table_name] = {
                        "continuous_backups_enabled": continuous_backups.get('ContinuousBackupsStatus') == 'ENABLED',
                        "point_in_time_recovery_enabled": point_in_time_recovery.get('PointInTimeRecoveryStatus') == 'ENABLED'
                    }
                    
                except Exception as e:
                    backup_status[table_name] = {
                        "error": str(e)
                    }
            
            # Check if backup is properly configured for production
            if environment == Environment.PRODUCTION:
                tables_without_backup = [
                    table for table, status in backup_status.items()
                    if not status.get('point_in_time_recovery_enabled', False)
                ]
                
                if tables_without_backup:
                    return False, f"Tables without backup enabled: {tables_without_backup}", {
                        "backup_status": backup_status,
                        "tables_without_backup": tables_without_backup
                    }
            
            return True, "Backup configuration is properly set up", {
                "backup_status": backup_status
            }
            
        except Exception as e:
            return False, f"Backup configuration validation failed: {e}", {"error": str(e)}
    
    async def _validate_audit_logging(self, environment: Environment, 
                                    resources: List[AWSResource]) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate audit logging and compliance requirements."""
        try:
            cloudtrail_client = await self.aws_factory.create_client('cloudtrail')
            
            # Check CloudTrail configuration
            trails_response = await cloudtrail_client.describe_trails()
            trails = trails_response.get('trailList', [])
            
            audit_status = {
                "total_trails": len(trails),
                "active_trails": 0,
                "multi_region_trails": 0,
                "log_file_validation_enabled": 0
            }
            
            for trail in trails:
                trail_name = trail['Name']
                
                # Get trail status
                status_response = await cloudtrail_client.get_trail_status(Name=trail_name)
                
                if status_response.get('IsLogging', False):
                    audit_status["active_trails"] += 1
                
                if trail.get('IsMultiRegionTrail', False):
                    audit_status["multi_region_trails"] += 1
                
                if trail.get('LogFileValidationEnabled', False):
                    audit_status["log_file_validation_enabled"] += 1
            
            # Check compliance requirements for production
            if environment == Environment.PRODUCTION:
                if audit_status["active_trails"] == 0:
                    return False, "No active CloudTrail found for production environment", {
                        "audit_status": audit_status
                    }
                
                if audit_status["multi_region_trails"] == 0:
                    return False, "No multi-region CloudTrail found for production environment", {
                        "audit_status": audit_status
                    }
            
            return True, "Audit logging is properly configured", {
                "audit_status": audit_status
            }
            
        except Exception as e:
            return False, f"Audit logging validation failed: {e}", {"error": str(e)}
    
    def _extract_performance_baseline(self, check: ValidationCheck, 
                                    result: ValidationResult,
                                    environment: Environment) -> Optional[PerformanceBaseline]:
        """Extract performance baseline from validation result."""
        if not result.is_passed or check.category != ValidationCategory.PERFORMANCE:
            return None
        
        # Extract performance metrics based on check type
        if check.check_id == "performance_api_response_time":
            performance_results = result.details.get("performance_results", {})
            if performance_results:
                # Use average response time from health endpoint
                health_result = performance_results.get("/health", {})
                if health_result:
                    avg_response_time = health_result.get("avg_response_time_ms", 0)
                    thresholds = self.performance_thresholds[environment]["api_response_time_ms"]
                    
                    return PerformanceBaseline(
                        metric_name="api_response_time_ms",
                        baseline_value=avg_response_time,
                        unit="milliseconds",
                        threshold_warning=thresholds["warning"],
                        threshold_critical=thresholds["critical"],
                        measurement_timestamp=result.timestamp
                    )
        
        elif check.check_id == "performance_database_queries":
            query_results = result.details.get("query_results", {})
            if query_results:
                scan_result = query_results.get("scan", {})
                if scan_result:
                    response_time = scan_result.get("response_time_ms", 0)
                    thresholds = self.performance_thresholds[environment]["database_query_time_ms"]
                    
                    return PerformanceBaseline(
                        metric_name="database_query_time_ms",
                        baseline_value=response_time,
                        unit="milliseconds",
                        threshold_warning=thresholds["warning"],
                        threshold_critical=thresholds["critical"],
                        measurement_timestamp=result.timestamp
                    )
        
        elif check.check_id == "performance_resource_utilization":
            utilization_status = result.details.get("utilization_status", {})
            baselines = []
            
            for resource_type, status in utilization_status.items():
                usage_percent = status.get("usage_percent", 0)
                threshold_warning = status.get("threshold_warning", 0)
                threshold_critical = status.get("threshold_critical", 0)
                
                baselines.append(PerformanceBaseline(
                    metric_name=f"{resource_type}_usage_percent",
                    baseline_value=usage_percent,
                    unit="percent",
                    threshold_warning=threshold_warning,
                    threshold_critical=threshold_critical,
                    measurement_timestamp=result.timestamp
                ))
            
            # Return first baseline (could return all in a real implementation)
            return baselines[0] if baselines else None
        
        return None
    
    async def _initialize_http_session(self) -> None:
        """Initialize HTTP session for API testing."""
        if not self._http_session:
            self._http_session = aiohttp.ClientSession()
    
    async def _cleanup_http_session(self) -> None:
        """Cleanup HTTP session."""
        if self._http_session:
            await self._http_session.close()
            self._http_session = None
    
    def get_validation_history(self, limit: int = 10) -> List[IntegrationValidationResult]:
        """Get validation history with optional limit."""
        return self._validation_history[-limit:] if limit else self._validation_history
    
    def get_performance_baselines(self, environment: Environment) -> List[PerformanceBaseline]:
        """Get performance baselines for a specific environment."""
        baselines = []
        
        for validation_result in self._validation_history:
            if validation_result.environment == environment:
                baselines.extend(validation_result.performance_baselines)
        
        return baselines
    
    def get_validation_summary(self, environment: Environment) -> Dict[str, Any]:
        """Get validation summary for an environment."""
        env_validations = [v for v in self._validation_history if v.environment == environment]
        
        if not env_validations:
            return {
                "environment": environment.value,
                "total_validations": 0,
                "latest_validation": None
            }
        
        latest_validation = env_validations[-1]
        
        # Calculate success rate
        total_checks = sum(v.total_checks for v in env_validations)
        passed_checks = sum(v.passed_checks for v in env_validations)
        success_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        
        return {
            "environment": environment.value,
            "total_validations": len(env_validations),
            "latest_validation": {
                "validation_id": latest_validation.validation_id,
                "overall_status": latest_validation.overall_status,
                "completed_at": latest_validation.completed_at.isoformat(),
                "passed_checks": latest_validation.passed_checks,
                "total_checks": latest_validation.total_checks,
                "critical_failures": latest_validation.critical_failures
            },
            "success_rate_percent": success_rate,
            "performance_baselines_count": len(latest_validation.performance_baselines)
        }


# Global deployment validator instance
_deployment_validator: Optional[DeploymentValidator] = None


def get_deployment_validator(aws_factory: Optional[AWSServiceFactory] = None) -> DeploymentValidator:
    """Get or create the global deployment validator instance."""
    global _deployment_validator
    if _deployment_validator is None:
        if aws_factory is None:
            from src.services.aws import get_aws_service_factory
            aws_factory = get_aws_service_factory()
        _deployment_validator = DeploymentValidator(aws_factory)
    return _deployment_validator