"""
Integration Monitoring Service

Provides comprehensive monitoring and observability for all AWS service integrations
and system components. Tracks health status, performance metrics, and provides
real-time dashboards for system observability.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import json

import boto3
from botocore.exceptions import ClientError, BotoCoreError

from src.utils.logging import get_logger
from src.utils.config import config
from src.utils.constants import HEALTH_CONFIG, PERFORMANCE_TARGETS


logger = get_logger("integration_monitor")


class ServiceStatus(str, Enum):
    """Service health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class IntegrationType(str, Enum):
    """Types of integrations being monitored."""
    BEDROCK = "bedrock"
    DYNAMODB = "dynamodb"
    S3 = "s3"
    LAMBDA = "lambda"
    CLOUDWATCH = "cloudwatch"
    KINESIS = "kinesis"
    SECRETS_MANAGER = "secrets_manager"
    PARAMETER_STORE = "parameter_store"
    API_GATEWAY = "api_gateway"
    ECS = "ecs"


@dataclass
class ServiceHealthMetrics:
    """Health metrics for a specific service."""
    service_name: str
    integration_type: IntegrationType
    status: ServiceStatus
    response_time_ms: float
    error_rate: float
    availability: float
    last_check: datetime
    error_details: Optional[str] = None
    performance_trend: List[float] = field(default_factory=list)
    uptime_percentage: float = 100.0
    
    def update_performance_trend(self, response_time: float, max_history: int = 20) -> None:
        """Update performance trend with new response time."""
        self.performance_trend.append(response_time)
        if len(self.performance_trend) > max_history:
            self.performance_trend.pop(0)
    
    def get_average_response_time(self) -> float:
        """Calculate average response time from trend data."""
        if not self.performance_trend:
            return self.response_time_ms
        return sum(self.performance_trend) / len(self.performance_trend)


@dataclass
class IntegrationHealthReport:
    """Comprehensive health report for all integrations."""
    timestamp: datetime
    overall_status: ServiceStatus
    healthy_services: int
    degraded_services: int
    unhealthy_services: int
    total_services: int
    service_details: Dict[str, ServiceHealthMetrics]
    system_uptime: float
    performance_summary: Dict[str, Any]
    
    def calculate_overall_status(self) -> ServiceStatus:
        """Calculate overall system status based on service health."""
        if self.unhealthy_services > 0:
            return ServiceStatus.UNHEALTHY
        elif self.degraded_services > 0:
            return ServiceStatus.DEGRADED
        elif self.healthy_services == self.total_services:
            return ServiceStatus.HEALTHY
        else:
            return ServiceStatus.UNKNOWN


class IntegrationMonitor:
    """
    Comprehensive integration monitoring service for AWS services and system components.
    
    Provides real-time health monitoring, performance tracking, and diagnostic reporting
    for all system integrations.
    """
    
    def __init__(self):
        self.logger = get_logger("integration_monitor")
        self.monitoring_active = False
        self.health_metrics: Dict[str, ServiceHealthMetrics] = {}
        self.monitoring_interval = timedelta(seconds=HEALTH_CONFIG["health_check_interval_seconds"])
        self.start_time = datetime.utcnow()
        self._monitoring_task: Optional[asyncio.Task] = None
        
        # AWS clients for health checks
        self._aws_clients: Dict[str, Any] = {}
        self._initialize_aws_clients()
        
        # Performance thresholds
        self.performance_thresholds = {
            IntegrationType.BEDROCK: {"response_time_ms": 5000, "error_rate": 0.05},
            IntegrationType.DYNAMODB: {"response_time_ms": 100, "error_rate": 0.01},
            IntegrationType.S3: {"response_time_ms": 500, "error_rate": 0.01},
            IntegrationType.LAMBDA: {"response_time_ms": 1000, "error_rate": 0.02},
            IntegrationType.CLOUDWATCH: {"response_time_ms": 2000, "error_rate": 0.03},
        }
    
    def _initialize_aws_clients(self) -> None:
        """Initialize AWS service clients for health monitoring."""
        try:
            session = boto3.Session()
            
            # Get AWS region from config, with fallback
            aws_region = getattr(config, 'aws_region', 'us-east-1')
            
            self._aws_clients = {
                "bedrock": session.client("bedrock-runtime", region_name=aws_region),
                "bedrock_agent": session.client("bedrock-agent", region_name=aws_region),
                "dynamodb": session.client("dynamodb", region_name=aws_region),
                "s3": session.client("s3", region_name=aws_region),
                "lambda": session.client("lambda", region_name=aws_region),
                "cloudwatch": session.client("cloudwatch", region_name=aws_region),
                "kinesis": session.client("kinesis", region_name=aws_region),
                "secretsmanager": session.client("secretsmanager", region_name=aws_region),
                "ssm": session.client("ssm", region_name=aws_region),
            }
            
            self.logger.info("AWS clients initialized for integration monitoring")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AWS clients: {e}")
            self._aws_clients = {}
    
    async def start_monitoring(self) -> None:
        """Start continuous integration monitoring."""
        if self.monitoring_active:
            self.logger.warning("Integration monitoring already active")
            return
        
        self.monitoring_active = True
        self.start_time = datetime.utcnow()
        
        # Start monitoring task
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        self.logger.info("Integration monitoring started")
    
    async def stop_monitoring(self) -> None:
        """Stop integration monitoring."""
        self.monitoring_active = False
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Integration monitoring stopped")
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop that runs health checks periodically."""
        while self.monitoring_active:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.monitoring_interval.total_seconds())
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Brief pause before retrying
    
    async def _perform_health_checks(self) -> None:
        """Perform health checks on all monitored services."""
        check_tasks = [
            self._check_bedrock_health(),
            self._check_dynamodb_health(),
            self._check_s3_health(),
            self._check_lambda_health(),
            self._check_cloudwatch_health(),
            self._check_kinesis_health(),
            self._check_secrets_manager_health(),
        ]
        
        # Run all health checks concurrently
        results = await asyncio.gather(*check_tasks, return_exceptions=True)
        
        # Log any exceptions from health checks
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                service_name = ["bedrock", "dynamodb", "s3", "lambda", "cloudwatch", "kinesis", "secrets_manager"][i]
                self.logger.error(f"Health check failed for {service_name}: {result}")
    
    async def _check_bedrock_health(self) -> None:
        """Check Bedrock service health."""
        service_name = "bedrock"
        start_time = time.time()
        
        try:
            # Test Bedrock runtime availability
            client = self._aws_clients.get("bedrock")
            if not client:
                raise Exception("Bedrock client not available")
            
            # Simple health check - list foundation models
            response = client.list_foundation_models()
            
            response_time = (time.time() - start_time) * 1000
            
            # Check if we have expected models
            models = response.get("modelSummaries", [])
            claude_models = [m for m in models if "claude" in m.get("modelId", "").lower()]
            
            status = ServiceStatus.HEALTHY
            error_details = None
            
            if not claude_models:
                status = ServiceStatus.DEGRADED
                error_details = "No Claude models available"
            elif response_time > self.performance_thresholds[IntegrationType.BEDROCK]["response_time_ms"]:
                status = ServiceStatus.DEGRADED
                error_details = f"High response time: {response_time:.1f}ms"
            
            self._update_service_metrics(
                service_name=service_name,
                integration_type=IntegrationType.BEDROCK,
                status=status,
                response_time_ms=response_time,
                error_rate=0.0,
                error_details=error_details
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self._update_service_metrics(
                service_name=service_name,
                integration_type=IntegrationType.BEDROCK,
                status=ServiceStatus.UNHEALTHY,
                response_time_ms=response_time,
                error_rate=1.0,
                error_details=str(e)
            )
    
    async def _check_dynamodb_health(self) -> None:
        """Check DynamoDB service health."""
        service_name = "dynamodb"
        start_time = time.time()
        
        try:
            client = self._aws_clients.get("dynamodb")
            if not client:
                raise Exception("DynamoDB client not available")
            
            # List tables to check connectivity
            response = client.list_tables(Limit=1)
            
            response_time = (time.time() - start_time) * 1000
            
            status = ServiceStatus.HEALTHY
            error_details = None
            
            if response_time > self.performance_thresholds[IntegrationType.DYNAMODB]["response_time_ms"]:
                status = ServiceStatus.DEGRADED
                error_details = f"High response time: {response_time:.1f}ms"
            
            self._update_service_metrics(
                service_name=service_name,
                integration_type=IntegrationType.DYNAMODB,
                status=status,
                response_time_ms=response_time,
                error_rate=0.0,
                error_details=error_details
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self._update_service_metrics(
                service_name=service_name,
                integration_type=IntegrationType.DYNAMODB,
                status=ServiceStatus.UNHEALTHY,
                response_time_ms=response_time,
                error_rate=1.0,
                error_details=str(e)
            )
    
    async def _check_s3_health(self) -> None:
        """Check S3 service health."""
        service_name = "s3"
        start_time = time.time()
        
        try:
            client = self._aws_clients.get("s3")
            if not client:
                raise Exception("S3 client not available")
            
            # List buckets to check connectivity
            response = client.list_buckets()
            
            response_time = (time.time() - start_time) * 1000
            
            status = ServiceStatus.HEALTHY
            error_details = None
            
            if response_time > self.performance_thresholds[IntegrationType.S3]["response_time_ms"]:
                status = ServiceStatus.DEGRADED
                error_details = f"High response time: {response_time:.1f}ms"
            
            self._update_service_metrics(
                service_name=service_name,
                integration_type=IntegrationType.S3,
                status=status,
                response_time_ms=response_time,
                error_rate=0.0,
                error_details=error_details
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self._update_service_metrics(
                service_name=service_name,
                integration_type=IntegrationType.S3,
                status=ServiceStatus.UNHEALTHY,
                response_time_ms=response_time,
                error_rate=1.0,
                error_details=str(e)
            )
    
    async def _check_lambda_health(self) -> None:
        """Check Lambda service health."""
        service_name = "lambda"
        start_time = time.time()
        
        try:
            client = self._aws_clients.get("lambda")
            if not client:
                raise Exception("Lambda client not available")
            
            # List functions to check connectivity
            response = client.list_functions(MaxItems=1)
            
            response_time = (time.time() - start_time) * 1000
            
            status = ServiceStatus.HEALTHY
            error_details = None
            
            if response_time > self.performance_thresholds[IntegrationType.LAMBDA]["response_time_ms"]:
                status = ServiceStatus.DEGRADED
                error_details = f"High response time: {response_time:.1f}ms"
            
            self._update_service_metrics(
                service_name=service_name,
                integration_type=IntegrationType.LAMBDA,
                status=status,
                response_time_ms=response_time,
                error_rate=0.0,
                error_details=error_details
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self._update_service_metrics(
                service_name=service_name,
                integration_type=IntegrationType.LAMBDA,
                status=ServiceStatus.UNHEALTHY,
                response_time_ms=response_time,
                error_rate=1.0,
                error_details=str(e)
            )
    
    async def _check_cloudwatch_health(self) -> None:
        """Check CloudWatch service health."""
        service_name = "cloudwatch"
        start_time = time.time()
        
        try:
            client = self._aws_clients.get("cloudwatch")
            if not client:
                raise Exception("CloudWatch client not available")
            
            # List metrics to check connectivity
            response = client.list_metrics(MaxRecords=1)
            
            response_time = (time.time() - start_time) * 1000
            
            status = ServiceStatus.HEALTHY
            error_details = None
            
            if response_time > self.performance_thresholds[IntegrationType.CLOUDWATCH]["response_time_ms"]:
                status = ServiceStatus.DEGRADED
                error_details = f"High response time: {response_time:.1f}ms"
            
            self._update_service_metrics(
                service_name=service_name,
                integration_type=IntegrationType.CLOUDWATCH,
                status=status,
                response_time_ms=response_time,
                error_rate=0.0,
                error_details=error_details
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self._update_service_metrics(
                service_name=service_name,
                integration_type=IntegrationType.CLOUDWATCH,
                status=ServiceStatus.UNHEALTHY,
                response_time_ms=response_time,
                error_rate=1.0,
                error_details=str(e)
            )
    
    async def _check_kinesis_health(self) -> None:
        """Check Kinesis service health."""
        service_name = "kinesis"
        start_time = time.time()
        
        try:
            client = self._aws_clients.get("kinesis")
            if not client:
                raise Exception("Kinesis client not available")
            
            # List streams to check connectivity
            response = client.list_streams(Limit=1)
            
            response_time = (time.time() - start_time) * 1000
            
            status = ServiceStatus.HEALTHY
            error_details = None
            
            # Kinesis doesn't have specific thresholds, use CloudWatch as baseline
            if response_time > self.performance_thresholds[IntegrationType.CLOUDWATCH]["response_time_ms"]:
                status = ServiceStatus.DEGRADED
                error_details = f"High response time: {response_time:.1f}ms"
            
            self._update_service_metrics(
                service_name=service_name,
                integration_type=IntegrationType.KINESIS,
                status=status,
                response_time_ms=response_time,
                error_rate=0.0,
                error_details=error_details
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self._update_service_metrics(
                service_name=service_name,
                integration_type=IntegrationType.KINESIS,
                status=ServiceStatus.UNHEALTHY,
                response_time_ms=response_time,
                error_rate=1.0,
                error_details=str(e)
            )
    
    async def _check_secrets_manager_health(self) -> None:
        """Check Secrets Manager service health."""
        service_name = "secrets_manager"
        start_time = time.time()
        
        try:
            client = self._aws_clients.get("secretsmanager")
            if not client:
                raise Exception("Secrets Manager client not available")
            
            # List secrets to check connectivity
            response = client.list_secrets(MaxResults=1)
            
            response_time = (time.time() - start_time) * 1000
            
            status = ServiceStatus.HEALTHY
            error_details = None
            
            # Use CloudWatch threshold as baseline
            if response_time > self.performance_thresholds[IntegrationType.CLOUDWATCH]["response_time_ms"]:
                status = ServiceStatus.DEGRADED
                error_details = f"High response time: {response_time:.1f}ms"
            
            self._update_service_metrics(
                service_name=service_name,
                integration_type=IntegrationType.SECRETS_MANAGER,
                status=status,
                response_time_ms=response_time,
                error_rate=0.0,
                error_details=error_details
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self._update_service_metrics(
                service_name=service_name,
                integration_type=IntegrationType.SECRETS_MANAGER,
                status=ServiceStatus.UNHEALTHY,
                response_time_ms=response_time,
                error_rate=1.0,
                error_details=str(e)
            )
    
    def _update_service_metrics(
        self,
        service_name: str,
        integration_type: IntegrationType,
        status: ServiceStatus,
        response_time_ms: float,
        error_rate: float,
        error_details: Optional[str] = None
    ) -> None:
        """Update health metrics for a service."""
        current_time = datetime.utcnow()
        
        if service_name in self.health_metrics:
            # Update existing metrics
            metrics = self.health_metrics[service_name]
            metrics.status = status
            metrics.response_time_ms = response_time_ms
            metrics.error_rate = error_rate
            metrics.last_check = current_time
            metrics.error_details = error_details
            metrics.update_performance_trend(response_time_ms)
            
            # Update availability based on status
            if status == ServiceStatus.HEALTHY:
                metrics.availability = min(100.0, metrics.availability + 0.1)
            elif status == ServiceStatus.DEGRADED:
                metrics.availability = max(0.0, metrics.availability - 0.05)
            else:  # UNHEALTHY
                metrics.availability = max(0.0, metrics.availability - 0.2)
        else:
            # Create new metrics
            self.health_metrics[service_name] = ServiceHealthMetrics(
                service_name=service_name,
                integration_type=integration_type,
                status=status,
                response_time_ms=response_time_ms,
                error_rate=error_rate,
                availability=100.0 if status == ServiceStatus.HEALTHY else 95.0,
                last_check=current_time,
                error_details=error_details
            )
    
    async def get_integration_health_report(self) -> IntegrationHealthReport:
        """Generate comprehensive integration health report."""
        current_time = datetime.utcnow()
        
        # Count services by status
        healthy_count = sum(1 for m in self.health_metrics.values() if m.status == ServiceStatus.HEALTHY)
        degraded_count = sum(1 for m in self.health_metrics.values() if m.status == ServiceStatus.DEGRADED)
        unhealthy_count = sum(1 for m in self.health_metrics.values() if m.status == ServiceStatus.UNHEALTHY)
        total_count = len(self.health_metrics)
        
        # Calculate overall status
        if unhealthy_count > 0:
            overall_status = ServiceStatus.UNHEALTHY
        elif degraded_count > 0:
            overall_status = ServiceStatus.DEGRADED
        elif healthy_count == total_count and total_count > 0:
            overall_status = ServiceStatus.HEALTHY
        else:
            overall_status = ServiceStatus.UNKNOWN
        
        # Calculate system uptime
        uptime_seconds = (current_time - self.start_time).total_seconds()
        uptime_percentage = min(100.0, (uptime_seconds / 3600) * 100)  # Normalize to hours
        
        # Performance summary
        performance_summary = {
            "average_response_time_ms": sum(m.get_average_response_time() for m in self.health_metrics.values()) / max(1, total_count),
            "average_availability": sum(m.availability for m in self.health_metrics.values()) / max(1, total_count),
            "total_error_rate": sum(m.error_rate for m in self.health_metrics.values()) / max(1, total_count),
            "services_with_errors": sum(1 for m in self.health_metrics.values() if m.error_details),
        }
        
        return IntegrationHealthReport(
            timestamp=current_time,
            overall_status=overall_status,
            healthy_services=healthy_count,
            degraded_services=degraded_count,
            unhealthy_services=unhealthy_count,
            total_services=total_count,
            service_details=dict(self.health_metrics),
            system_uptime=uptime_percentage,
            performance_summary=performance_summary
        )
    
    async def get_service_health(self, service_name: str) -> Optional[ServiceHealthMetrics]:
        """Get health metrics for a specific service."""
        return self.health_metrics.get(service_name)
    
    async def get_unhealthy_services(self) -> List[ServiceHealthMetrics]:
        """Get list of services that are not healthy."""
        return [
            metrics for metrics in self.health_metrics.values()
            if metrics.status in [ServiceStatus.DEGRADED, ServiceStatus.UNHEALTHY]
        ]
    
    async def generate_diagnostic_report(self, service_name: Optional[str] = None) -> Dict[str, Any]:
        """Generate detailed diagnostic report for troubleshooting."""
        current_time = datetime.utcnow()
        
        if service_name and service_name in self.health_metrics:
            # Single service diagnostic
            metrics = self.health_metrics[service_name]
            return {
                "service": service_name,
                "timestamp": current_time.isoformat(),
                "status": metrics.status.value,
                "diagnostics": {
                    "current_response_time_ms": metrics.response_time_ms,
                    "average_response_time_ms": metrics.get_average_response_time(),
                    "error_rate": metrics.error_rate,
                    "availability": metrics.availability,
                    "last_successful_check": metrics.last_check.isoformat(),
                    "error_details": metrics.error_details,
                    "performance_trend": metrics.performance_trend[-10:],  # Last 10 measurements
                    "threshold_violations": self._check_threshold_violations(metrics)
                }
            }
        else:
            # System-wide diagnostic
            unhealthy_services = await self.get_unhealthy_services()
            
            return {
                "system_diagnostic": {
                    "timestamp": current_time.isoformat(),
                    "monitoring_duration_hours": (current_time - self.start_time).total_seconds() / 3600,
                    "total_services_monitored": len(self.health_metrics),
                    "unhealthy_services_count": len(unhealthy_services),
                    "unhealthy_services": [
                        {
                            "service": svc.service_name,
                            "status": svc.status.value,
                            "error": svc.error_details,
                            "response_time_ms": svc.response_time_ms
                        }
                        for svc in unhealthy_services
                    ],
                    "performance_issues": self._identify_performance_issues(),
                    "recommendations": self._generate_recommendations(unhealthy_services)
                }
            }
    
    def _check_threshold_violations(self, metrics: ServiceHealthMetrics) -> List[str]:
        """Check if service metrics violate performance thresholds."""
        violations = []
        
        thresholds = self.performance_thresholds.get(metrics.integration_type, {})
        
        if "response_time_ms" in thresholds:
            if metrics.response_time_ms > thresholds["response_time_ms"]:
                violations.append(f"Response time {metrics.response_time_ms:.1f}ms exceeds threshold {thresholds['response_time_ms']}ms")
        
        if "error_rate" in thresholds:
            if metrics.error_rate > thresholds["error_rate"]:
                violations.append(f"Error rate {metrics.error_rate:.3f} exceeds threshold {thresholds['error_rate']:.3f}")
        
        if metrics.availability < 99.0:
            violations.append(f"Availability {metrics.availability:.1f}% below 99%")
        
        return violations
    
    def _identify_performance_issues(self) -> List[str]:
        """Identify system-wide performance issues."""
        issues = []
        
        # Check for services with consistently high response times
        slow_services = [
            m.service_name for m in self.health_metrics.values()
            if m.get_average_response_time() > 2000  # 2 seconds
        ]
        
        if slow_services:
            issues.append(f"Services with high response times: {', '.join(slow_services)}")
        
        # Check for services with high error rates
        error_prone_services = [
            m.service_name for m in self.health_metrics.values()
            if m.error_rate > 0.1  # 10% error rate
        ]
        
        if error_prone_services:
            issues.append(f"Services with high error rates: {', '.join(error_prone_services)}")
        
        # Check for availability issues
        low_availability_services = [
            m.service_name for m in self.health_metrics.values()
            if m.availability < 95.0
        ]
        
        if low_availability_services:
            issues.append(f"Services with low availability: {', '.join(low_availability_services)}")
        
        return issues
    
    def _generate_recommendations(self, unhealthy_services: List[ServiceHealthMetrics]) -> List[str]:
        """Generate recommendations for improving service health."""
        recommendations = []
        
        if not unhealthy_services:
            recommendations.append("All services are healthy - no immediate action required")
            return recommendations
        
        # Service-specific recommendations
        for service in unhealthy_services:
            if service.integration_type == IntegrationType.BEDROCK:
                recommendations.append(f"Bedrock ({service.service_name}): Check model availability and consider switching to alternative models")
            elif service.integration_type == IntegrationType.DYNAMODB:
                recommendations.append(f"DynamoDB ({service.service_name}): Check table capacity and consider auto-scaling")
            elif service.integration_type == IntegrationType.S3:
                recommendations.append(f"S3 ({service.service_name}): Verify bucket permissions and check for rate limiting")
            elif service.integration_type == IntegrationType.LAMBDA:
                recommendations.append(f"Lambda ({service.service_name}): Check function configuration and concurrent execution limits")
            else:
                recommendations.append(f"{service.service_name}: Investigate service-specific issues and check AWS service health dashboard")
        
        # General recommendations
        if len(unhealthy_services) > 2:
            recommendations.append("Multiple services affected - check AWS region status and network connectivity")
        
        return recommendations


# Global instance for use across the application
_integration_monitor_instance: Optional[IntegrationMonitor] = None


def get_integration_monitor() -> IntegrationMonitor:
    """Get the global integration monitor instance."""
    global _integration_monitor_instance
    
    if _integration_monitor_instance is None:
        _integration_monitor_instance = IntegrationMonitor()
    
    return _integration_monitor_instance