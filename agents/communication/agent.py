"""
Resilient Communication Agent

Provides resilient communication capabilities with deduplication, stakeholder routing,
and timezone-aware escalation.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from src.interfaces.agent import BaseAgent
from src.models.agent import AgentType
from src.models.agent import AgentRecommendation, AgentStatus, ActionType, RiskLevel, ActionType as AgentActionType, RiskLevel, AgentMessage
from src.models.incident import Incident
from src.utils.logging import get_logger
from src.utils.exceptions import CommunicationError

from .templates import (
    MessageTemplateManager, MessageType, NotificationChannel, RenderedMessage
)
from .channels import NotificationChannelManager, DeliveryResult, DeliveryStatus

logger = get_logger(__name__)


class StakeholderManager:
    """Manages stakeholder information and routing"""
    
    def __init__(self):
        self.stakeholders = self._initialize_stakeholders()
        self.escalation_policies = self._initialize_escalation_policies()
    
    def _initialize_stakeholders(self) -> Dict[str, Dict[str, Any]]:
        """Initialize stakeholder database"""
        return {
            "sre_team": {
                "name": "SRE Team",
                "channels": {
                    NotificationChannel.SLACK: ["#sre-alerts"],
                    NotificationChannel.EMAIL: ["sre-team@company.com"],
                    NotificationChannel.PAGERDUTY: ["sre-oncall"]
                },
                "timezone": "UTC",
                "business_hours": {"start": 9, "end": 17},
                "severity_threshold": "medium"
            },
            "engineering_leads": {
                "name": "Engineering Leads",
                "channels": {
                    NotificationChannel.SLACK: ["#eng-leads"],
                    NotificationChannel.EMAIL: ["eng-leads@company.com"]
                },
                "timezone": "UTC",
                "business_hours": {"start": 8, "end": 18},
                "severity_threshold": "high"
            },
            "executives": {
                "name": "Executive Team",
                "channels": {
                    NotificationChannel.EMAIL: ["executives@company.com"],
                    NotificationChannel.SMS: ["+1-555-0001", "+1-555-0002"]
                },
                "timezone": "UTC",
                "business_hours": {"start": 9, "end": 17},
                "severity_threshold": "critical"
            },
            "customer_success": {
                "name": "Customer Success",
                "channels": {
                    NotificationChannel.SLACK: ["#customer-success"],
                    NotificationChannel.EMAIL: ["cs-team@company.com"]
                },
                "timezone": "UTC",
                "business_hours": {"start": 8, "end": 20},
                "severity_threshold": "high"
            }
        }
    
    def _initialize_escalation_policies(self) -> Dict[str, Dict[str, Any]]:
        """Initialize escalation policies"""
        return {
            "critical": {
                "immediate": ["sre_team", "engineering_leads"],
                "5_minutes": ["executives"],
                "15_minutes": ["customer_success"],
                "channels": [NotificationChannel.SLACK, NotificationChannel.PAGERDUTY, NotificationChannel.EMAIL]
            },
            "high": {
                "immediate": ["sre_team"],
                "10_minutes": ["engineering_leads"],
                "30_minutes": ["customer_success"],
                "channels": [NotificationChannel.SLACK, NotificationChannel.EMAIL]
            },
            "medium": {
                "immediate": ["sre_team"],
                "30_minutes": ["engineering_leads"],
                "channels": [NotificationChannel.SLACK]
            },
            "low": {
                "immediate": ["sre_team"],
                "channels": [NotificationChannel.SLACK]
            }
        }
    
    def get_recipients_for_severity(
        self, 
        severity: str, 
        escalation_level: str = "immediate"
    ) -> Dict[NotificationChannel, List[str]]:
        """Get recipients for a given severity and escalation level"""
        try:
            policy = self.escalation_policies.get(severity, self.escalation_policies["medium"])
            stakeholder_groups = policy.get(escalation_level, [])
            allowed_channels = policy.get("channels", [NotificationChannel.SLACK])
            
            recipients = {}
            
            for channel in allowed_channels:
                recipients[channel] = []
                
                for group_id in stakeholder_groups:
                    group = self.stakeholders.get(group_id, {})
                    group_channels = group.get("channels", {})
                    
                    if channel in group_channels:
                        recipients[channel].extend(group_channels[channel])
            
            return recipients
            
        except Exception as e:
            logger.error(f"Error getting recipients for severity {severity}: {e}")
            return {NotificationChannel.SLACK: ["#sre-alerts"]}
    
    def should_notify_during_hours(self, stakeholder_id: str, current_time: datetime) -> bool:
        """Check if stakeholder should be notified during current time"""
        try:
            stakeholder = self.stakeholders.get(stakeholder_id, {})
            business_hours = stakeholder.get("business_hours", {"start": 0, "end": 24})
            
            current_hour = current_time.hour
            return business_hours["start"] <= current_hour <= business_hours["end"]
            
        except Exception as e:
            logger.error(f"Error checking business hours for {stakeholder_id}: {e}")
            return True  # Default to always notify


class ResilientCommunicationAgent(BaseAgent):
    """
    Resilient Communication Agent with deduplication and stakeholder routing
    
    Capabilities:
    - Channel-specific rate limiting with intelligent batching
    - Timezone-aware escalation and stakeholder routing
    - Message deduplication and ordered delivery
    - Post-incident communication and reporting
    """
    
    def __init__(self, agent_id: str = "communication-agent"):
        super().__init__(AgentType.COMMUNICATION, agent_id)
        self.template_manager = MessageTemplateManager()
        self.channel_manager = NotificationChannelManager()
        self.stakeholder_manager = StakeholderManager()
        
        # Performance targets
        self.target_delivery_time = timedelta(seconds=10)  # 10s target, 30s max
        self.max_processing_time = timedelta(seconds=30)
        
        # Communication tracking
        self.active_notifications = {}
        self.escalation_timers = {}
        self.acknowledgments = {}
        
        logger.info(f"Initialized {self.name} with multi-channel communication")
    
    async def process_incident(self, incident: Incident) -> List[AgentRecommendation]:
        """
        Process incident for communication needs
        
        Args:
            incident: Incident to communicate about
            
        Returns:
            Agent recommendation with communication actions
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Processing incident {incident.id} for communication")
            
            # Determine message type based on incident status
            message_type = self._determine_message_type(incident)
            
            # Get context for message rendering
            context = await self._gather_communication_context(incident)
            
            # Send notifications
            delivery_results = await self._send_incident_notifications(
                incident, message_type, context
            )
            
            # Set up escalation if needed
            if incident.severity in ["critical", "high"]:
                await self._setup_escalation_timers(incident)
            
            # Create recommendation
            recommendation = await self._create_communication_recommendation(
                incident, message_type, delivery_results, context
            )
            
            # Update agent status
            processing_time = datetime.utcnow() - start_time
            await self._update_status(processing_time, len(delivery_results))
            
            logger.info(
                f"Completed communication processing for {incident.id} in {processing_time.total_seconds():.2f}s"
            )
            
            return [recommendation]
            
        except Exception as e:
            logger.error(f"Error processing incident {incident.id}: {e}")
            await self._update_status_error(str(e))
            
            return [AgentRecommendation(
                agent_name=AgentType.COMMUNICATION,
                incident_id=incident.id,
                action_type=ActionType.NO_ACTION,
                action_id="communication_error",
                confidence=0.0,
                risk_level=RiskLevel.LOW,
                estimated_impact="No impact due to error",
                reasoning=f"Communication processing failed: {str(e)}",
                urgency=0.0,
                parameters={"error": str(e)}
            )]
    
    async def send_resolution_update(
        self, 
        incident: Incident, 
        resolution_actions: List[Dict[str, Any]]
    ) -> List[DeliveryResult]:
        """Send update about resolution actions being taken"""
        try:
            logger.info(f"Sending resolution update for incident {incident.id}")
            
            context = {
                "actions": resolution_actions,
                "action_count": len(resolution_actions),
                "risk_level": self._determine_risk_level(resolution_actions),
                "estimated_completion": self._estimate_completion_time(resolution_actions)
            }
            
            return await self._send_incident_notifications(
                incident, MessageType.RESOLUTION_STARTED, context
            )
            
        except Exception as e:
            logger.error(f"Error sending resolution update: {e}")
            return []
    
    async def send_resolution_complete(
        self, 
        incident: Incident, 
        resolution_summary: Dict[str, Any]
    ) -> List[DeliveryResult]:
        """Send notification that incident has been resolved"""
        try:
            logger.info(f"Sending resolution complete for incident {incident.id}")
            
            context = {
                "resolution_method": resolution_summary.get("method", "Automated"),
                "actions_taken": resolution_summary.get("actions", []),
                "resolution_time": resolution_summary.get("duration", "Unknown"),
                "impact_prevented": resolution_summary.get("impact_prevented", 0),
                "users_affected": resolution_summary.get("users_affected", 0)
            }
            
            return await self._send_incident_notifications(
                incident, MessageType.INCIDENT_RESOLVED, context
            )
            
        except Exception as e:
            logger.error(f"Error sending resolution complete: {e}")
            return []
    
    async def request_human_approval(
        self, 
        incident: Incident, 
        proposed_action: Dict[str, Any]
    ) -> List[DeliveryResult]:
        """Request human approval for high-risk actions"""
        try:
            logger.info(f"Requesting human approval for incident {incident.id}")
            
            context = {
                "proposed_action": proposed_action.get("description", "Unknown action"),
                "risk_level": proposed_action.get("risk_level", "Unknown"),
                "estimated_impact": proposed_action.get("estimated_impact", "Unknown"),
                "approval_reason": proposed_action.get("approval_reason", "High-risk action"),
                "approval_timeout": "10 minutes"
            }
            
            # Send to appropriate stakeholders with escalation
            results = await self._send_incident_notifications(
                incident, MessageType.HUMAN_APPROVAL_REQUIRED, context
            )
            
            # Set up approval timeout
            await self._setup_approval_timeout(incident, proposed_action)
            
            return results
            
        except Exception as e:
            logger.error(f"Error requesting human approval: {e}")
            return []
    
    async def send_post_incident_summary(
        self, 
        incident: Incident, 
        summary_data: Dict[str, Any]
    ) -> List[DeliveryResult]:
        """Send post-incident summary report"""
        try:
            logger.info(f"Sending post-incident summary for incident {incident.id}")
            
            context = {
                "incident_duration": summary_data.get("duration", "Unknown"),
                "resolution_method": summary_data.get("resolution_method", "Automated"),
                "total_cost": summary_data.get("total_cost", 0),
                "revenue_impact": summary_data.get("revenue_impact", 0),
                "users_affected": summary_data.get("users_affected", 0),
                "incident_timeline": summary_data.get("timeline", []),
                "resolution_actions": summary_data.get("actions", []),
                "lessons_learned": summary_data.get("lessons_learned", []),
                "preventive_measures": summary_data.get("preventive_measures", []),
                "knowledge_updates_count": summary_data.get("knowledge_updates", 0),
                "accuracy_improvement": summary_data.get("accuracy_improvement", 0),
                "next_steps": summary_data.get("next_steps", [])
            }
            
            # Send summary via email to stakeholders
            recipients = self.stakeholder_manager.get_recipients_for_severity(
                incident.severity, "immediate"
            )
            
            messages = []
            for channel, recipient_list in recipients.items():
                if channel == NotificationChannel.EMAIL:  # Post-incident summaries via email
                    message = self.template_manager.render_message(
                        MessageType.POST_INCIDENT_SUMMARY,
                        channel,
                        incident,
                        context,
                        recipient_list
                    )
                    if message:
                        messages.append(message)
            
            return await self.channel_manager.batch_send_messages(messages)
            
        except Exception as e:
            logger.error(f"Error sending post-incident summary: {e}")
            return []
    
    def _determine_message_type(self, incident: Incident) -> MessageType:
        """Determine message type based on incident status"""
        status_mapping = {
            "detected": MessageType.INCIDENT_DETECTED,
            "analyzing": MessageType.INCIDENT_ANALYZING,
            "resolved": MessageType.INCIDENT_RESOLVED,
            "escalated": MessageType.INCIDENT_ESCALATED
        }
        return status_mapping.get(incident.status, MessageType.INCIDENT_DETECTED)
    
    async def _gather_communication_context(self, incident: Incident) -> Dict[str, Any]:
        """Gather context information for message rendering"""
        try:
            context = {
                "business_impact": {
                    "cost_per_minute": self._calculate_cost_per_minute(incident),
                    "users_affected": self._estimate_users_affected(incident),
                    "revenue_impact": self._calculate_revenue_impact(incident)
                },
                "active_agents": ["detection", "diagnosis"],  # Default agents
                "analysis_summary": "Automated analysis in progress",
                "next_steps": "Continuing with automated resolution"
            }
            
            # Add incident-specific context
            if incident.severity == "critical":
                context["active_agents"].extend(["prediction", "resolution"])
                context["next_steps"] = "Executing automated resolution actions"
            
            return context
            
        except Exception as e:
            logger.error(f"Error gathering communication context: {e}")
            return {}
    
    def _calculate_cost_per_minute(self, incident: Incident) -> float:
        """Calculate business cost per minute for incident"""
        severity_costs = {
            "critical": 2000.0,
            "high": 800.0,
            "medium": 300.0,
            "low": 100.0
        }
        return severity_costs.get(incident.severity, 300.0)
    
    def _estimate_users_affected(self, incident: Incident) -> int:
        """Estimate number of users affected"""
        severity_users = {
            "critical": 50000,
            "high": 10000,
            "medium": 1000,
            "low": 100
        }
        return severity_users.get(incident.severity, 1000)
    
    def _calculate_revenue_impact(self, incident: Incident) -> float:
        """Calculate revenue impact per minute"""
        cost_per_minute = self._calculate_cost_per_minute(incident)
        return cost_per_minute * 0.8  # 80% of cost is revenue impact
    
    async def _send_incident_notifications(
        self,
        incident: Incident,
        message_type: MessageType,
        context: Dict[str, Any]
    ) -> List[DeliveryResult]:
        """Send notifications for an incident"""
        try:
            # Get recipients based on severity
            recipients = self.stakeholder_manager.get_recipients_for_severity(incident.severity)
            
            # Create messages for each channel
            messages = []
            for channel, recipient_list in recipients.items():
                if recipient_list:  # Only create message if there are recipients
                    message = self.template_manager.render_message(
                        message_type,
                        channel,
                        incident,
                        context,
                        recipient_list
                    )
                    if message:
                        messages.append(message)
            
            # Send messages
            if messages:
                return await self.channel_manager.batch_send_messages(messages)
            else:
                logger.warning(f"No messages created for incident {incident.id}")
                return []
                
        except Exception as e:
            logger.error(f"Error sending incident notifications: {e}")
            return []
    
    def _determine_risk_level(self, actions: List[Dict[str, Any]]) -> str:
        """Determine overall risk level of resolution actions"""
        risk_levels = [action.get("risk_level", "low") for action in actions]
        
        if "critical" in risk_levels:
            return "critical"
        elif "high" in risk_levels:
            return "high"
        elif "medium" in risk_levels:
            return "medium"
        else:
            return "low"
    
    def _estimate_completion_time(self, actions: List[Dict[str, Any]]) -> str:
        """Estimate completion time for resolution actions"""
        total_duration = sum(
            action.get("estimated_duration_seconds", 60) 
            for action in actions
        )
        
        if total_duration < 60:
            return f"{total_duration} seconds"
        elif total_duration < 3600:
            return f"{total_duration // 60} minutes"
        else:
            return f"{total_duration // 3600} hours"
    
    async def _setup_escalation_timers(self, incident: Incident):
        """Set up escalation timers for incident"""
        try:
            policy = self.stakeholder_manager.escalation_policies.get(incident.severity, {})
            
            for escalation_time, stakeholder_groups in policy.items():
                if escalation_time.endswith("_minutes"):
                    minutes = int(escalation_time.split("_")[0])
                    
                    # Schedule escalation
                    escalation_key = f"{incident.id}_{escalation_time}"
                    self.escalation_timers[escalation_key] = {
                        "incident": incident,
                        "escalation_level": escalation_time,
                        "scheduled_at": datetime.utcnow() + timedelta(minutes=minutes)
                    }
                    
                    logger.info(f"Scheduled escalation for {incident.id} in {minutes} minutes")
            
        except Exception as e:
            logger.error(f"Error setting up escalation timers: {e}")
    
    async def _setup_approval_timeout(self, incident: Incident, proposed_action: Dict[str, Any]):
        """Set up timeout for approval requests"""
        try:
            timeout_key = f"{incident.id}_approval_timeout"
            self.escalation_timers[timeout_key] = {
                "incident": incident,
                "action": proposed_action,
                "type": "approval_timeout",
                "scheduled_at": datetime.utcnow() + timedelta(minutes=10)
            }
            
            logger.info(f"Set approval timeout for {incident.id} in 10 minutes")
            
        except Exception as e:
            logger.error(f"Error setting up approval timeout: {e}")
    
    async def _create_communication_recommendation(
        self,
        incident: Incident,
        message_type: MessageType,
        delivery_results: List[DeliveryResult],
        context: Dict[str, Any]
    ) -> AgentRecommendation:
        """Create agent recommendation based on communication results"""
        try:
            successful_deliveries = [r for r in delivery_results if r.status == DeliveryStatus.SENT]
            failed_deliveries = [r for r in delivery_results if r.status == DeliveryStatus.FAILED]
            
            # Calculate confidence based on delivery success rate
            if delivery_results:
                success_rate = len(successful_deliveries) / len(delivery_results)
                confidence = min(success_rate * 0.95, 1.0)  # Slightly conservative
            else:
                confidence = 0.0
            
            # Create reasoning
            reasoning_parts = []
            if successful_deliveries:
                channels = set(r.channel.value for r in successful_deliveries)
                reasoning_parts.append(f"Successfully sent notifications via {', '.join(channels)}")
            
            if failed_deliveries:
                failed_channels = set(r.channel.value for r in failed_deliveries)
                reasoning_parts.append(f"Failed to send via {', '.join(failed_channels)}")
            
            reasoning = ". ".join(reasoning_parts) if reasoning_parts else "No notifications sent"
            
            # Create action summaries
            action_summaries = []
            for result in delivery_results:
                action_summaries.append({
                    "type": "notification",
                    "channel": result.channel.value,
                    "recipients": len(result.recipients),
                    "status": result.status.value,
                    "message_type": message_type.value,
                    "sent_at": result.sent_at.isoformat(),
                    "error": result.error_message if result.error_message else None
                })
            
            # Determine recommendation type
            if all(r.status == DeliveryStatus.SENT for r in delivery_results):
                rec_type = "communication_complete"
            elif any(r.status == DeliveryStatus.SENT for r in delivery_results):
                rec_type = "communication_partial"
            elif any(r.status == DeliveryStatus.RATE_LIMITED for r in delivery_results):
                rec_type = "communication_rate_limited"
            else:
                rec_type = "communication_failed"
            
            # Create metadata
            metadata = {
                "message_type": message_type.value,
                "total_notifications": len(delivery_results),
                "successful_notifications": len(successful_deliveries),
                "failed_notifications": len(failed_deliveries),
                "channels_used": list(set(r.channel.value for r in delivery_results)),
                "escalation_scheduled": incident.severity in ["critical", "high"],
                "notification_details": action_summaries
            }
            
            return AgentRecommendation(
                agent_name=AgentType.COMMUNICATION,
                incident_id=incident.id,
                action_type="notify_team",
                action_id=rec_type,
                confidence=confidence,
                risk_level="low",
                estimated_impact="Stakeholder notification",
                reasoning=reasoning,
                urgency=confidence,
                parameters=metadata
            )
            
        except Exception as e:
            logger.error(f"Error creating communication recommendation: {e}")
            return AgentRecommendation(
                agent_name=AgentType.COMMUNICATION,
                incident_id=incident.id,
                action_type="no_action",
                action_id="communication_error",
                confidence=0.0,
                risk_level="low",
                estimated_impact="No impact due to error",
                reasoning=f"Error creating communication recommendation: {str(e)}",
                urgency=0.0,
                parameters={"error": str(e)}
            )
    
    async def _update_status(self, processing_time: timedelta, notification_count: int):
        """Update agent status after successful processing"""
        try:
            self.status = AgentStatus.HEALTHY
            self.last_activity = datetime.utcnow()
            self.metadata.update({
                "last_processing_time_seconds": processing_time.total_seconds(),
                "last_notification_count": notification_count,
                "active_notifications": len(self.active_notifications),
                "escalation_timers": len(self.escalation_timers),
                "target_delivery_time_seconds": self.target_delivery_time.total_seconds()
            })
            
        except Exception as e:
            logger.error(f"Error updating status: {e}")
    
    async def _update_status_error(self, error_message: str):
        """Update agent status after error"""
        try:
            self.status = AgentStatus.ERROR
            self.last_activity = datetime.utcnow()
            self.metadata.update({
                "last_error": error_message,
                "error_timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error updating error status: {e}")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get detailed health status of the communication agent"""
        try:
            # Get channel status
            channel_status = self.channel_manager.get_channel_status()
            
            # Get delivery stats
            delivery_stats = self.channel_manager.get_delivery_stats(hours=1)
            
            return {
                "agent_id": self.name,
                "status": self.status.value,
                "last_activity": self.last_activity.isoformat() if self.last_activity else None,
                "capabilities": [
                    "multi_channel_notifications",
                    "rate_limiting",
                    "message_deduplication",
                    "stakeholder_routing",
                    "escalation_management"
                ],
                "performance_targets": {
                    "target_delivery_time_seconds": self.target_delivery_time.total_seconds(),
                    "max_processing_time_seconds": self.max_processing_time.total_seconds()
                },
                "channel_status": channel_status,
                "delivery_stats": delivery_stats,
                "active_notifications": len(self.active_notifications),
                "escalation_timers": len(self.escalation_timers),
                "available_templates": self.template_manager.get_available_templates(),
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
            # For now, communication agent doesn't handle inter-agent messages
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
            if not self.template_manager or not self.channel_manager:
                return False
            
            # Check if stakeholder manager is available
            if not self.stakeholder_manager:
                return False
            
            return self.is_healthy
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False