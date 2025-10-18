"""
Message Templates

Manages message templates for different notification types and channels.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from src.models.incident import Incident
from src.utils.logging import get_logger

logger = get_logger(__name__)


class MessageType(Enum):
    """Types of messages"""
    INCIDENT_DETECTED = "incident_detected"
    INCIDENT_ANALYZING = "incident_analyzing"
    INCIDENT_RESOLVED = "incident_resolved"
    INCIDENT_ESCALATED = "incident_escalated"
    RESOLUTION_STARTED = "resolution_started"
    RESOLUTION_COMPLETED = "resolution_completed"
    RESOLUTION_FAILED = "resolution_failed"
    HUMAN_APPROVAL_REQUIRED = "human_approval_required"
    POST_INCIDENT_SUMMARY = "post_incident_summary"


class NotificationChannel(Enum):
    """Notification channels"""
    SLACK = "slack"
    EMAIL = "email"
    PAGERDUTY = "pagerduty"
    SMS = "sms"
    WEBHOOK = "webhook"


@dataclass
class MessageTemplate:
    """Template for generating messages"""
    message_type: MessageType
    channel: NotificationChannel
    subject_template: str
    body_template: str
    priority: str
    requires_acknowledgment: bool = False
    escalation_delay: Optional[timedelta] = None


@dataclass
class RenderedMessage:
    """A rendered message ready for sending"""
    message_type: MessageType
    channel: NotificationChannel
    subject: str
    body: str
    priority: str
    recipients: List[str]
    metadata: Dict[str, Any]
    requires_acknowledgment: bool = False
    escalation_delay: Optional[timedelta] = None


class MessageTemplateManager:
    """Manages message templates for different channels and scenarios"""
    
    def __init__(self):
        self.templates = self._initialize_templates()
        
    def _initialize_templates(self) -> Dict[str, MessageTemplate]:
        """Initialize default message templates"""
        templates = {}
        
        # Slack templates
        templates["incident_detected_slack"] = MessageTemplate(
            message_type=MessageType.INCIDENT_DETECTED,
            channel=NotificationChannel.SLACK,
            subject_template="🚨 Incident Detected: {incident_title}",
            body_template="""
🚨 **INCIDENT DETECTED**

**Title:** {incident_title}
**Severity:** {incident_severity}
**Service:** {incident_service}
**Status:** {incident_status}

**Description:** {incident_description}

**Business Impact:** ${business_impact_per_minute}/min
**Estimated Users Affected:** {users_affected:,}

**Autonomous Response:** Detection and diagnosis agents activated
**Expected Resolution Time:** <3 minutes

**Incident ID:** {incident_id}
**Detected At:** {detected_at}
            """.strip(),
            priority="high"
        )
        
        templates["incident_analyzing_slack"] = MessageTemplate(
            message_type=MessageType.INCIDENT_ANALYZING,
            channel=NotificationChannel.SLACK,
            subject_template="🔍 Analyzing: {incident_title}",
            body_template="""
🔍 **INCIDENT ANALYSIS IN PROGRESS**

**Incident:** {incident_title}
**Status:** Analysis in progress
**Agent Activity:** {active_agents}

**Current Findings:**
{analysis_summary}

**Next Steps:** {next_steps}

**Time Elapsed:** {time_elapsed}
**Incident ID:** {incident_id}
            """.strip(),
            priority="medium"
        )
        
        templates["resolution_started_slack"] = MessageTemplate(
            message_type=MessageType.RESOLUTION_STARTED,
            channel=NotificationChannel.SLACK,
            subject_template="🔧 Resolution Started: {incident_title}",
            body_template="""
🔧 **AUTOMATED RESOLUTION STARTED**

**Incident:** {incident_title}
**Resolution Actions:** {action_count} actions initiated

**Actions Being Executed:**
{action_list}

**Estimated Completion:** {estimated_completion}
**Risk Level:** {risk_level}

**Incident ID:** {incident_id}
            """.strip(),
            priority="medium"
        )
        
        templates["incident_resolved_slack"] = MessageTemplate(
            message_type=MessageType.INCIDENT_RESOLVED,
            channel=NotificationChannel.SLACK,
            subject_template="✅ Resolved: {incident_title}",
            body_template="""
✅ **INCIDENT RESOLVED**

**Incident:** {incident_title}
**Resolution Time:** {resolution_time}
**Resolution Method:** {resolution_method}

**Actions Taken:**
{actions_taken}

**Business Impact Prevented:** ${impact_prevented}
**Users Affected:** {users_affected:,}

**Post-Incident Actions:**
- Automated learning from incident patterns
- Knowledge base updated
- Monitoring enhanced

**Incident ID:** {incident_id}
**Resolved At:** {resolved_at}
            """.strip(),
            priority="low"
        )
        
        templates["human_approval_required_slack"] = MessageTemplate(
            message_type=MessageType.HUMAN_APPROVAL_REQUIRED,
            channel=NotificationChannel.SLACK,
            subject_template="⚠️ Approval Required: {incident_title}",
            body_template="""
⚠️ **HUMAN APPROVAL REQUIRED**

**Incident:** {incident_title}
**Severity:** {incident_severity}

**Proposed Action:** {proposed_action}
**Risk Level:** {risk_level}
**Estimated Impact:** {estimated_impact}

**Reason for Approval:** {approval_reason}

**Options:**
- ✅ Approve and execute
- ❌ Reject and escalate
- 🔄 Request alternative action

**Time Sensitive:** Response needed within {approval_timeout}

**Incident ID:** {incident_id}
            """.strip(),
            priority="critical",
            requires_acknowledgment=True,
            escalation_delay=timedelta(minutes=5)
        )
        
        # Email templates
        templates["incident_detected_email"] = MessageTemplate(
            message_type=MessageType.INCIDENT_DETECTED,
            channel=NotificationChannel.EMAIL,
            subject_template="[INCIDENT] {incident_severity}: {incident_title}",
            body_template="""
INCIDENT DETECTED

Incident Details:
- Title: {incident_title}
- Severity: {incident_severity}
- Service: {incident_service}
- Status: {incident_status}
- Description: {incident_description}

Business Impact:
- Cost per minute: ${business_impact_per_minute}
- Users affected: {users_affected:,}

Autonomous Response:
The Autonomous Incident Commander has been activated and is currently:
1. Analyzing the incident with detection and diagnosis agents
2. Correlating with historical patterns
3. Preparing resolution recommendations

Expected resolution time: <3 minutes

Incident ID: {incident_id}
Detected at: {detected_at}

This is an automated notification from the Autonomous Incident Commander.
            """.strip(),
            priority="high"
        )
        
        templates["post_incident_summary_email"] = MessageTemplate(
            message_type=MessageType.POST_INCIDENT_SUMMARY,
            channel=NotificationChannel.EMAIL,
            subject_template="[POST-INCIDENT] Summary: {incident_title}",
            body_template="""
POST-INCIDENT SUMMARY

Incident Overview:
- Title: {incident_title}
- Severity: {incident_severity}
- Service: {incident_service}
- Duration: {incident_duration}
- Resolution Method: {resolution_method}

Timeline:
{incident_timeline}

Business Impact:
- Total cost: ${total_cost}
- Users affected: {users_affected:,}
- Revenue impact: ${revenue_impact}

Resolution Actions:
{resolution_actions}

Lessons Learned:
{lessons_learned}

Preventive Measures:
{preventive_measures}

Knowledge Base Updates:
- {knowledge_updates_count} new patterns learned
- Detection accuracy improved by {accuracy_improvement}%

Next Steps:
{next_steps}

Incident ID: {incident_id}
Report generated at: {report_generated_at}

This summary was automatically generated by the Autonomous Incident Commander.
            """.strip(),
            priority="low"
        )
        
        # PagerDuty templates
        templates["incident_escalated_pagerduty"] = MessageTemplate(
            message_type=MessageType.INCIDENT_ESCALATED,
            channel=NotificationChannel.PAGERDUTY,
            subject_template="ESCALATION: {incident_title}",
            body_template="""
INCIDENT ESCALATION

The Autonomous Incident Commander was unable to resolve this incident automatically.

Incident: {incident_title}
Severity: {incident_severity}
Service: {incident_service}
Duration: {incident_duration}

Attempted Actions:
{attempted_actions}

Escalation Reason: {escalation_reason}

Manual intervention required.

Incident ID: {incident_id}
            """.strip(),
            priority="critical",
            requires_acknowledgment=True
        )
        
        return templates
    
    def render_message(
        self,
        message_type: MessageType,
        channel: NotificationChannel,
        incident: Incident,
        context: Dict[str, Any],
        recipients: List[str]
    ) -> Optional[RenderedMessage]:
        """
        Render a message using the appropriate template
        
        Args:
            message_type: Type of message to render
            channel: Target notification channel
            incident: Incident data
            context: Additional context for template rendering
            recipients: List of recipients
            
        Returns:
            Rendered message or None if template not found
        """
        try:
            template_key = f"{message_type.value}_{channel.value}"
            template = self.templates.get(template_key)
            
            if not template:
                logger.warning(f"No template found for {template_key}")
                return None
            
            # Prepare template variables
            template_vars = self._prepare_template_variables(incident, context)
            
            # Render subject and body
            subject = template.subject_template.format(**template_vars)
            body = template.body_template.format(**template_vars)
            
            return RenderedMessage(
                message_type=message_type,
                channel=channel,
                subject=subject,
                body=body,
                priority=template.priority,
                recipients=recipients,
                metadata={
                    "incident_id": incident.id,
                    "template_key": template_key,
                    "rendered_at": datetime.utcnow().isoformat()
                },
                requires_acknowledgment=template.requires_acknowledgment,
                escalation_delay=template.escalation_delay
            )
            
        except Exception as e:
            logger.error(f"Error rendering message {template_key}: {e}")
            return None
    
    def _prepare_template_variables(
        self, 
        incident: Incident, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare variables for template rendering"""
        try:
            # Base incident variables
            severity_value = incident.severity.value if hasattr(incident.severity, 'value') else str(incident.severity)
            status_value = incident.status.value if hasattr(incident.status, 'value') else str(incident.status)
            
            variables = {
                "incident_id": incident.id,
                "incident_title": incident.title,
                "incident_description": incident.description,
                "incident_severity": severity_value.upper(),
                "incident_service": incident.metadata.tags.get("service", "unknown"),
                "incident_status": status_value,
                "detected_at": incident.detected_at.strftime("%Y-%m-%d %H:%M:%S UTC") if incident.detected_at else "Unknown",
                "resolved_at": incident.resolved_at.strftime("%Y-%m-%d %H:%M:%S UTC") if incident.resolved_at else "Not resolved"
            }
            
            # Business impact variables
            business_impact = context.get("business_impact", {})
            variables.update({
                "business_impact_per_minute": business_impact.get("cost_per_minute", 0),
                "users_affected": business_impact.get("users_affected", 0),
                "revenue_impact": business_impact.get("revenue_impact", 0),
                "total_cost": business_impact.get("total_cost", 0)
            })
            
            # Time-related variables
            if incident.detected_at:
                if incident.resolved_at:
                    duration = incident.resolved_at - incident.detected_at
                    variables["incident_duration"] = self._format_duration(duration)
                    variables["resolution_time"] = self._format_duration(duration)
                else:
                    duration = datetime.utcnow() - incident.detected_at
                    variables["time_elapsed"] = self._format_duration(duration)
                    variables["incident_duration"] = self._format_duration(duration)  # For ongoing incidents
            else:
                variables["incident_duration"] = "Unknown"
                variables["resolution_time"] = "Unknown"
                variables["time_elapsed"] = "Unknown"
            
            # Agent and action variables
            variables.update({
                "active_agents": ", ".join(context.get("active_agents", [])),
                "action_count": len(context.get("actions", [])),
                "action_list": self._format_action_list(context.get("actions", [])),
                "actions_taken": self._format_actions_taken(context.get("completed_actions", [])),
                "attempted_actions": self._format_attempted_actions(context.get("attempted_actions", [])),
                "resolution_method": context.get("resolution_method", "Automated"),
                "risk_level": context.get("risk_level", "Unknown").upper()
            })
            
            # Analysis and escalation variables
            variables.update({
                "analysis_summary": context.get("analysis_summary", "Analysis in progress..."),
                "next_steps": context.get("next_steps", "Continuing automated resolution"),
                "escalation_reason": context.get("escalation_reason", "Automated resolution failed"),
                "approval_reason": context.get("approval_reason", "High-risk action requires approval"),
                "approval_timeout": context.get("approval_timeout", "10 minutes"),
                "proposed_action": context.get("proposed_action", "Unknown action"),
                "estimated_impact": context.get("estimated_impact", "Unknown impact"),
                "estimated_completion": context.get("estimated_completion", "Unknown")
            })
            
            # Post-incident variables
            variables.update({
                "incident_timeline": self._format_timeline(context.get("timeline", [])),
                "resolution_actions": self._format_actions_taken(context.get("completed_actions", [])),
                "lessons_learned": self._format_lessons_learned(context.get("lessons_learned", [])),
                "preventive_measures": self._format_preventive_measures(context.get("preventive_measures", [])),
                "knowledge_updates_count": context.get("knowledge_updates_count", 0),
                "accuracy_improvement": context.get("accuracy_improvement", 0),
                "impact_prevented": context.get("impact_prevented", 0),
                "next_steps": self._format_preventive_measures(context.get("next_steps", [])),
                "report_generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            })
            
            return variables
            
        except Exception as e:
            logger.error(f"Error preparing template variables: {e}")
            return {
                "incident_id": incident.id if incident else "unknown",
                "incident_title": incident.title if incident else "Unknown Incident",
                "error": "Template variable preparation failed"
            }
    
    def _format_duration(self, duration: timedelta) -> str:
        """Format duration for display"""
        try:
            total_seconds = int(duration.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            if hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"
                
        except Exception:
            return "Unknown duration"
    
    def _format_action_list(self, actions: List[Dict[str, Any]]) -> str:
        """Format list of actions for display"""
        try:
            if not actions:
                return "No actions"
            
            formatted_actions = []
            for action in actions[:5]:  # Limit to 5 actions
                action_type = action.get("type", "Unknown")
                target = action.get("target_service", "Unknown")
                formatted_actions.append(f"• {action_type} on {target}")
            
            if len(actions) > 5:
                formatted_actions.append(f"• ... and {len(actions) - 5} more actions")
            
            return "\n".join(formatted_actions)
            
        except Exception:
            return "Error formatting actions"
    
    def _format_actions_taken(self, actions: List[Dict[str, Any]]) -> str:
        """Format completed actions for display"""
        try:
            if not actions:
                return "No actions completed"
            
            formatted_actions = []
            for action in actions:
                action_type = action.get("type", "Unknown")
                target = action.get("target_service", "Unknown")
                success = action.get("success", False)
                status = "✅" if success else "❌"
                formatted_actions.append(f"{status} {action_type} on {target}")
            
            return "\n".join(formatted_actions)
            
        except Exception:
            return "Error formatting completed actions"
    
    def _format_attempted_actions(self, actions: List[Dict[str, Any]]) -> str:
        """Format attempted actions for display"""
        try:
            if not actions:
                return "No actions attempted"
            
            formatted_actions = []
            for action in actions:
                action_type = action.get("type", "Unknown")
                result = action.get("result", "Unknown")
                formatted_actions.append(f"• {action_type}: {result}")
            
            return "\n".join(formatted_actions)
            
        except Exception:
            return "Error formatting attempted actions"
    
    def _format_timeline(self, timeline: List[Dict[str, Any]]) -> str:
        """Format incident timeline for display"""
        try:
            if not timeline:
                return "No timeline available"
            
            formatted_timeline = []
            for event in timeline:
                timestamp = event.get("timestamp", "Unknown time")
                description = event.get("description", "Unknown event")
                formatted_timeline.append(f"• {timestamp}: {description}")
            
            return "\n".join(formatted_timeline)
            
        except Exception:
            return "Error formatting timeline"
    
    def _format_lessons_learned(self, lessons: List[str]) -> str:
        """Format lessons learned for display"""
        try:
            if not lessons:
                return "No specific lessons identified"
            
            return "\n".join(f"• {lesson}" for lesson in lessons)
            
        except Exception:
            return "Error formatting lessons learned"
    
    def _format_preventive_measures(self, measures: List[str]) -> str:
        """Format preventive measures for display"""
        try:
            if not measures:
                return "No preventive measures identified"
            
            return "\n".join(f"• {measure}" for measure in measures)
            
        except Exception:
            return "Error formatting preventive measures"
    
    def get_available_templates(self) -> Dict[str, List[str]]:
        """Get list of available templates by channel"""
        templates_by_channel = {}
        
        for template_key, template in self.templates.items():
            channel = template.channel.value
            if channel not in templates_by_channel:
                templates_by_channel[channel] = []
            templates_by_channel[channel].append(template.message_type.value)
        
        return templates_by_channel