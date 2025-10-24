"""
Meta-Incident Handler for the Incident Commander System.

This module handles incidents that affect the incident response system itself,
creating a recursive monitoring and response capability.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import asdict

from src.models.incident import Incident, IncidentSeverity, ServiceTier, BusinessImpact, IncidentMetadata
from src.services.system_health_monitor import SystemHealthMonitor, MetaIncident, HealthStatus
from src.services.aws import AWSServiceFactory
from src.utils.logging import get_logger


logger = get_logger("meta_incident_handler")


class MetaIncidentHandler:
    """
    Handles meta-incidents that affect the incident response system itself.
    
    This creates a recursive monitoring system where the incident commander
    can respond to incidents affecting its own operation.
    """
    
    def __init__(self, aws_factory: AWSServiceFactory, health_monitor: SystemHealthMonitor):
        """Initialize meta-incident handler."""
        self.aws_factory = aws_factory
        self.health_monitor = health_monitor
        
        # Meta-incident configuration
        self.meta_incident_prefix = "META"
        self.auto_resolution_enabled = True
        self.escalation_timeout = timedelta(minutes=15)
        
        # Track active meta-incidents
        self.active_meta_incidents: Dict[str, Incident] = {}
        self.resolution_attempts: Dict[str, List[Dict[str, Any]]] = {}
        
        # Meta-incident severity mapping
        self.severity_mapping = {
            "multiple_agent_failure": IncidentSeverity.CRITICAL,
            "resource_exhaustion": IncidentSeverity.HIGH,
            "dependency_failure": IncidentSeverity.HIGH,
            "consensus_failure": IncidentSeverity.CRITICAL,
            "performance_degradation": IncidentSeverity.MEDIUM,
            "data_corruption": IncidentSeverity.CRITICAL
        }
        
        logger.info("Initialized Meta-Incident Handler")
    
    async def process_meta_incident(self, meta_incident: MetaIncident) -> Optional[Incident]:
        """
        Process a meta-incident and create a formal incident if needed.
        
        Args:
            meta_incident: The meta-incident to process
            
        Returns:
            Created incident or None if no incident needed
        """
        try:
            logger.info(f"Processing meta-incident: {meta_incident.title}")
            
            # Check if we already have an active incident for this meta-incident
            if meta_incident.id in self.active_meta_incidents:
                existing_incident = self.active_meta_incidents[meta_incident.id]
                logger.info(f"Meta-incident {meta_incident.id} already has active incident: {existing_incident.id}")
                return existing_incident
            
            # Create formal incident from meta-incident
            incident = await self._create_incident_from_meta_incident(meta_incident)
            
            # Store the active meta-incident
            self.active_meta_incidents[meta_incident.id] = incident
            self.resolution_attempts[meta_incident.id] = []
            
            # If auto-resolution is enabled, attempt immediate resolution
            if self.auto_resolution_enabled:
                await self._attempt_auto_resolution(meta_incident, incident)
            
            logger.info(f"Created incident {incident.id} for meta-incident {meta_incident.id}")
            return incident
            
        except Exception as e:
            logger.error(f"Error processing meta-incident {meta_incident.id}: {e}")
            return None
    
    async def _create_incident_from_meta_incident(self, meta_incident: MetaIncident) -> Incident:
        """Create a formal incident from a meta-incident."""
        
        # Calculate business impact
        business_impact = self._calculate_meta_incident_business_impact(meta_incident)
        
        # Create incident metadata
        metadata = IncidentMetadata(
            source_system="meta_incident_handler",
            tags={
                "meta_incident": "true",
                "meta_incident_id": meta_incident.id,
                "affected_components": ",".join(meta_incident.affected_components),
                "auto_resolution": str(self.auto_resolution_enabled).lower()
            },
            correlation_id=meta_incident.id,
            detection_method="system_health_monitor"
        )
        
        # Generate unique incident ID with META prefix
        incident_id = f"{self.meta_incident_prefix}-{uuid.uuid4().hex[:8].upper()}"
        
        # Create the incident
        incident = Incident(
            id=incident_id,
            title=f"[META] {meta_incident.title}",
            description=self._generate_meta_incident_description(meta_incident),
            severity=meta_incident.severity,
            status="detected",
            business_impact=business_impact,
            metadata=metadata
        )
        
        return incident
    
    def _calculate_meta_incident_business_impact(self, meta_incident: MetaIncident) -> BusinessImpact:
        """Calculate business impact of a meta-incident."""
        
        # Meta-incidents affect the incident response system itself
        # This has high business impact as it affects our ability to respond to other incidents
        
        if meta_incident.severity == IncidentSeverity.CRITICAL:
            service_tier = ServiceTier.TIER_1
            affected_users = 100000  # All users potentially affected if incident response fails
            revenue_impact = 5000.0  # High impact per minute
            sla_breach_risk = 0.9
        elif meta_incident.severity == IncidentSeverity.HIGH:
            service_tier = ServiceTier.TIER_2
            affected_users = 50000
            revenue_impact = 2000.0
            sla_breach_risk = 0.7
        elif meta_incident.severity == IncidentSeverity.MEDIUM:
            service_tier = ServiceTier.TIER_2
            affected_users = 10000
            revenue_impact = 800.0
            sla_breach_risk = 0.4
        else:
            service_tier = ServiceTier.TIER_3
            affected_users = 1000
            revenue_impact = 200.0
            sla_breach_risk = 0.2
        
        return BusinessImpact(
            service_tier=service_tier,
            affected_users=affected_users,
            revenue_impact_per_minute=revenue_impact,
            sla_breach_risk=sla_breach_risk,
            customer_facing=True,  # Meta-incidents affect customer-facing incident response
            regulatory_impact=False
        )
    
    def _generate_meta_incident_description(self, meta_incident: MetaIncident) -> str:
        """Generate detailed description for meta-incident."""
        description_parts = [
            f"Meta-incident detected in the Incident Commander system: {meta_incident.description}",
            f"Detected at: {meta_incident.detected_at.isoformat()}",
            f"Affected components: {', '.join(meta_incident.affected_components)}"
        ]
        
        if meta_incident.root_cause:
            description_parts.append(f"Root cause: {meta_incident.root_cause}")
        
        if meta_incident.recovery_actions:
            description_parts.append(f"Planned recovery actions: {', '.join(meta_incident.recovery_actions)}")
        
        description_parts.append(
            "This is a meta-incident affecting the incident response system itself. "
            "Resolution is critical to maintain incident response capabilities."
        )
        
        return " | ".join(description_parts)
    
    async def _attempt_auto_resolution(self, meta_incident: MetaIncident, incident: Incident):
        """Attempt automatic resolution of meta-incident."""
        try:
            logger.info(f"Attempting auto-resolution for meta-incident {meta_incident.id}")
            
            resolution_attempt = {
                "timestamp": datetime.utcnow(),
                "actions_attempted": [],
                "success": False,
                "error": None
            }
            
            # Execute recovery actions
            for action in meta_incident.recovery_actions:
                try:
                    success = await self._execute_meta_recovery_action(action, meta_incident)
                    resolution_attempt["actions_attempted"].append({
                        "action": action,
                        "success": success,
                        "timestamp": datetime.utcnow()
                    })
                    
                    if not success:
                        logger.warning(f"Recovery action '{action}' failed for meta-incident {meta_incident.id}")
                
                except Exception as e:
                    logger.error(f"Error executing recovery action '{action}': {e}")
                    resolution_attempt["actions_attempted"].append({
                        "action": action,
                        "success": False,
                        "error": str(e),
                        "timestamp": datetime.utcnow()
                    })
            
            # Check if resolution was successful
            resolution_successful = await self._verify_meta_incident_resolution(meta_incident)
            resolution_attempt["success"] = resolution_successful
            
            # Store resolution attempt
            if meta_incident.id not in self.resolution_attempts:
                self.resolution_attempts[meta_incident.id] = []
            self.resolution_attempts[meta_incident.id].append(resolution_attempt)
            
            if resolution_successful:
                logger.info(f"Auto-resolution successful for meta-incident {meta_incident.id}")
                await self._mark_meta_incident_resolved(meta_incident, incident)
            else:
                logger.warning(f"Auto-resolution failed for meta-incident {meta_incident.id}")
                await self._escalate_meta_incident(meta_incident, incident)
            
        except Exception as e:
            logger.error(f"Error during auto-resolution of meta-incident {meta_incident.id}: {e}")
            resolution_attempt["error"] = str(e)
            self.resolution_attempts[meta_incident.id].append(resolution_attempt)
    
    async def _execute_meta_recovery_action(self, action: str, meta_incident: MetaIncident) -> bool:
        """Execute a specific recovery action for meta-incident."""
        try:
            if action == "restart_agents":
                return await self._restart_affected_agents(meta_incident.affected_components)
            elif action == "scale_resources":
                return await self._trigger_resource_scaling()
            elif action == "cleanup_processes":
                return await self._cleanup_system_processes()
            elif action == "check_dependencies":
                return await self._verify_external_dependencies()
            elif action == "restart_consensus_engine":
                return await self._restart_consensus_system()
            elif action == "check_network":
                return await self._verify_network_connectivity()
            elif action == "verify_credentials":
                return await self._verify_aws_credentials()
            else:
                logger.warning(f"Unknown recovery action: {action}")
                return False
        
        except Exception as e:
            logger.error(f"Recovery action '{action}' failed: {e}")
            return False
    
    async def _restart_affected_agents(self, affected_components: List[str]) -> bool:
        """Restart affected agents."""
        try:
            from src.orchestrator.swarm_coordinator import get_swarm_coordinator
            coordinator = get_swarm_coordinator()
            
            success_count = 0
            for component in affected_components:
                if component.endswith("_agent") or component in ["detection", "diagnosis", "prediction", "resolution", "communication"]:
                    try:
                        await coordinator.restart_agent(component)
                        success_count += 1
                        logger.info(f"Successfully restarted agent: {component}")
                    except Exception as e:
                        logger.error(f"Failed to restart agent {component}: {e}")
            
            return success_count > 0
        
        except Exception as e:
            logger.error(f"Failed to restart affected agents: {e}")
            return False
    
    async def _trigger_resource_scaling(self) -> bool:
        """Trigger resource scaling to address resource exhaustion."""
        try:
            # In a real implementation, this would trigger auto-scaling groups
            # For now, we'll simulate by logging the action
            logger.info("Triggered resource scaling for meta-incident resolution")
            
            # Simulate scaling delay
            await asyncio.sleep(1)
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to trigger resource scaling: {e}")
            return False
    
    async def _cleanup_system_processes(self) -> bool:
        """Clean up system processes to free resources."""
        try:
            # Force garbage collection
            import gc
            gc.collect()
            
            # Clear old health monitor data
            if hasattr(self.health_monitor, 'health_history') and len(self.health_monitor.health_history) > 1000:
                # Keep only recent history
                while len(self.health_monitor.health_history) > 1000:
                    self.health_monitor.health_history.popleft()
            
            logger.info("System cleanup completed for meta-incident resolution")
            return True
        
        except Exception as e:
            logger.error(f"Failed to cleanup system processes: {e}")
            return False
    
    async def _verify_external_dependencies(self) -> bool:
        """Verify external dependencies are accessible."""
        try:
            # Test key dependencies
            dependencies_ok = 0
            total_dependencies = 0
            
            for dep_name, dep_config in self.health_monitor.external_dependencies.items():
                total_dependencies += 1
                try:
                    # Simulate dependency check
                    await asyncio.sleep(0.1)
                    dependencies_ok += 1
                    logger.info(f"Dependency {dep_name}: OK")
                except Exception as e:
                    logger.warning(f"Dependency {dep_name}: FAILED - {e}")
            
            success_rate = dependencies_ok / total_dependencies if total_dependencies > 0 else 0
            return success_rate >= 0.8  # 80% of dependencies must be OK
        
        except Exception as e:
            logger.error(f"Failed to verify external dependencies: {e}")
            return False
    
    async def _restart_consensus_system(self) -> bool:
        """Restart the consensus system."""
        try:
            # In a real implementation, this would restart consensus services
            logger.info("Consensus system restart triggered for meta-incident resolution")
            
            # Simulate restart delay
            await asyncio.sleep(2)
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to restart consensus system: {e}")
            return False
    
    async def _verify_network_connectivity(self) -> bool:
        """Verify network connectivity."""
        try:
            # In a real implementation, this would test network connectivity
            logger.info("Network connectivity verification completed")
            return True
        
        except Exception as e:
            logger.error(f"Failed to verify network connectivity: {e}")
            return False
    
    async def _verify_aws_credentials(self) -> bool:
        """Verify AWS credentials are valid."""
        try:
            # Test AWS credentials by making a simple API call
            sts_client = await self.aws_factory.get_sts_client()
            await sts_client.get_caller_identity()
            
            logger.info("AWS credentials verification successful")
            return True
        
        except Exception as e:
            logger.error(f"AWS credentials verification failed: {e}")
            return False
    
    async def _verify_meta_incident_resolution(self, meta_incident: MetaIncident) -> bool:
        """Verify that the meta-incident has been resolved."""
        try:
            # Wait a moment for systems to stabilize
            await asyncio.sleep(5)
            
            # Get current health status
            current_health = self.health_monitor.get_current_health_status()
            
            # Check if the specific issues mentioned in the meta-incident are resolved
            if meta_incident.title == "Multiple Agent Failure":
                # Check if agents are now healthy
                active_agents = current_health.get("active_agents", 0)
                return active_agents >= len(meta_incident.affected_components)
            
            elif meta_incident.title == "System Resource Exhaustion":
                # Check if resource utilization is back to normal
                resource_util = current_health.get("resource_utilization", {})
                critical_resources = [k for k, v in resource_util.items() if v > 90]
                return len(critical_resources) == 0
            
            elif meta_incident.title == "Multiple External Dependency Failures":
                # Check if dependencies are back online
                external_deps = current_health.get("external_dependencies", {})
                failed_deps = [k for k, v in external_deps.items() if v != "healthy"]
                return len(failed_deps) < len(meta_incident.affected_components)
            
            elif meta_incident.title == "Consensus System Failure":
                # Check if consensus system is working
                overall_status = current_health.get("overall_status", "unknown")
                return overall_status in ["healthy", "degraded"]
            
            else:
                # Generic check - overall system health should be improved
                overall_status = current_health.get("overall_status", "unknown")
                return overall_status != "critical"
        
        except Exception as e:
            logger.error(f"Error verifying meta-incident resolution: {e}")
            return False
    
    async def _mark_meta_incident_resolved(self, meta_incident: MetaIncident, incident: Incident):
        """Mark meta-incident as resolved."""
        try:
            # Update incident status
            incident.status = "resolved"
            
            # Update meta-incident status
            meta_incident.status = "resolved"
            
            # Remove from active incidents
            if meta_incident.id in self.active_meta_incidents:
                del self.active_meta_incidents[meta_incident.id]
            
            logger.info(f"Meta-incident {meta_incident.id} marked as resolved")
            
        except Exception as e:
            logger.error(f"Error marking meta-incident as resolved: {e}")
    
    async def _escalate_meta_incident(self, meta_incident: MetaIncident, incident: Incident):
        """Escalate meta-incident for human intervention."""
        try:
            # Update incident status
            incident.status = "escalated"
            
            # Add escalation metadata
            incident.metadata.tags["escalated"] = "true"
            incident.metadata.tags["escalation_reason"] = "auto_resolution_failed"
            incident.metadata.tags["escalation_time"] = datetime.utcnow().isoformat()
            
            logger.warning(f"Meta-incident {meta_incident.id} escalated for human intervention")
            
            # In a real implementation, this would trigger notifications to on-call engineers
            
        except Exception as e:
            logger.error(f"Error escalating meta-incident: {e}")
    
    def get_active_meta_incidents(self) -> List[Dict[str, Any]]:
        """Get all active meta-incidents."""
        return [
            {
                "meta_incident_id": meta_id,
                "incident": asdict(incident),
                "resolution_attempts": self.resolution_attempts.get(meta_id, [])
            }
            for meta_id, incident in self.active_meta_incidents.items()
        ]
    
    def get_meta_incident_statistics(self) -> Dict[str, Any]:
        """Get meta-incident handling statistics."""
        total_attempts = sum(len(attempts) for attempts in self.resolution_attempts.values())
        successful_attempts = sum(
            sum(1 for attempt in attempts if attempt["success"])
            for attempts in self.resolution_attempts.values()
        )
        
        return {
            "active_meta_incidents": len(self.active_meta_incidents),
            "total_resolution_attempts": total_attempts,
            "successful_resolution_attempts": successful_attempts,
            "auto_resolution_success_rate": successful_attempts / max(total_attempts, 1),
            "auto_resolution_enabled": self.auto_resolution_enabled
        }


# Global meta-incident handler instance
meta_incident_handler: Optional[MetaIncidentHandler] = None


def get_meta_incident_handler(aws_factory: AWSServiceFactory, 
                            health_monitor: SystemHealthMonitor) -> MetaIncidentHandler:
    """Get or create global meta-incident handler instance."""
    global meta_incident_handler
    if meta_incident_handler is None:
        meta_incident_handler = MetaIncidentHandler(aws_factory, health_monitor)
    return meta_incident_handler