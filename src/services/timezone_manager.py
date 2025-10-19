"""
Timezone Manager Service

Provides timezone-aware communication and stakeholder routing capabilities.
Handles do-not-disturb policies and business hours management.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import pytz

from src.utils.logging import get_logger

logger = get_logger(__name__)


class EscalationLevel(Enum):
    """Escalation levels based on severity and time"""
    NORMAL = "normal"
    URGENT = "urgent"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class BusinessHours:
    """Represents business hours for a timezone"""
    start_hour: int  # 24-hour format
    end_hour: int
    days_of_week: List[int]  # 0=Monday, 6=Sunday
    timezone: str


@dataclass
class DoNotDisturbPolicy:
    """Do-not-disturb policy for a stakeholder"""
    enabled: bool
    start_hour: int  # 24-hour format
    end_hour: int
    days_of_week: List[int]  # Days when DND is active
    exceptions: List[str]  # Severity levels that override DND


@dataclass
class StakeholderProfile:
    """Complete stakeholder profile with timezone and preferences"""
    stakeholder_id: str
    name: str
    timezone: str
    business_hours: BusinessHours
    dnd_policy: DoNotDisturbPolicy
    preferred_channels: Dict[str, List[str]]  # Channel type -> addresses
    escalation_threshold: str  # Minimum severity for notification
    contact_methods: Dict[EscalationLevel, List[str]]  # Escalation -> channels


class TimezoneManager:
    """Manages timezone-aware communication and escalation"""
    
    def __init__(self):
        self.stakeholder_profiles = self._initialize_stakeholder_profiles()
        self.escalation_rules = self._initialize_escalation_rules()
        
        logger.info(f"Initialized Timezone Manager with {len(self.stakeholder_profiles)} stakeholder profiles")
    
    def _initialize_stakeholder_profiles(self) -> Dict[str, StakeholderProfile]:
        """Initialize stakeholder profiles with timezone information"""
        return {
            "sre_team_us": StakeholderProfile(
                stakeholder_id="sre_team_us",
                name="SRE Team (US)",
                timezone="America/New_York",
                business_hours=BusinessHours(
                    start_hour=9,
                    end_hour=17,
                    days_of_week=[0, 1, 2, 3, 4],  # Monday-Friday
                    timezone="America/New_York"
                ),
                dnd_policy=DoNotDisturbPolicy(
                    enabled=True,
                    start_hour=22,  # 10 PM
                    end_hour=7,     # 7 AM
                    days_of_week=[0, 1, 2, 3, 4, 5, 6],  # All days
                    exceptions=["critical", "emergency"]
                ),
                preferred_channels={
                    "slack": ["#sre-alerts-us"],
                    "email": ["sre-us@company.com"],
                    "pagerduty": ["sre-us-oncall"]
                },
                escalation_threshold="medium",
                contact_methods={
                    EscalationLevel.NORMAL: ["slack"],
                    EscalationLevel.URGENT: ["slack", "email"],
                    EscalationLevel.CRITICAL: ["slack", "email", "pagerduty"],
                    EscalationLevel.EMERGENCY: ["slack", "email", "pagerduty", "sms"]
                }
            ),
            "sre_team_eu": StakeholderProfile(
                stakeholder_id="sre_team_eu",
                name="SRE Team (EU)",
                timezone="Europe/London",
                business_hours=BusinessHours(
                    start_hour=9,
                    end_hour=17,
                    days_of_week=[0, 1, 2, 3, 4],  # Monday-Friday
                    timezone="Europe/London"
                ),
                dnd_policy=DoNotDisturbPolicy(
                    enabled=True,
                    start_hour=22,  # 10 PM
                    end_hour=7,     # 7 AM
                    days_of_week=[0, 1, 2, 3, 4, 5, 6],  # All days
                    exceptions=["critical", "emergency"]
                ),
                preferred_channels={
                    "slack": ["#sre-alerts-eu"],
                    "email": ["sre-eu@company.com"],
                    "pagerduty": ["sre-eu-oncall"]
                },
                escalation_threshold="medium",
                contact_methods={
                    EscalationLevel.NORMAL: ["slack"],
                    EscalationLevel.URGENT: ["slack", "email"],
                    EscalationLevel.CRITICAL: ["slack", "email", "pagerduty"],
                    EscalationLevel.EMERGENCY: ["slack", "email", "pagerduty", "sms"]
                }
            ),
            "engineering_leads": StakeholderProfile(
                stakeholder_id="engineering_leads",
                name="Engineering Leadership",
                timezone="America/Los_Angeles",
                business_hours=BusinessHours(
                    start_hour=8,
                    end_hour=18,
                    days_of_week=[0, 1, 2, 3, 4],  # Monday-Friday
                    timezone="America/Los_Angeles"
                ),
                dnd_policy=DoNotDisturbPolicy(
                    enabled=True,
                    start_hour=21,  # 9 PM
                    end_hour=8,     # 8 AM
                    days_of_week=[0, 1, 2, 3, 4, 5, 6],  # All days
                    exceptions=["critical", "emergency"]
                ),
                preferred_channels={
                    "slack": ["#eng-leads"],
                    "email": ["eng-leads@company.com"]
                },
                escalation_threshold="high",
                contact_methods={
                    EscalationLevel.NORMAL: ["slack"],
                    EscalationLevel.URGENT: ["slack", "email"],
                    EscalationLevel.CRITICAL: ["slack", "email"],
                    EscalationLevel.EMERGENCY: ["slack", "email", "sms"]
                }
            ),
            "executives": StakeholderProfile(
                stakeholder_id="executives",
                name="Executive Team",
                timezone="America/New_York",
                business_hours=BusinessHours(
                    start_hour=9,
                    end_hour=17,
                    days_of_week=[0, 1, 2, 3, 4],  # Monday-Friday
                    timezone="America/New_York"
                ),
                dnd_policy=DoNotDisturbPolicy(
                    enabled=True,
                    start_hour=20,  # 8 PM
                    end_hour=8,     # 8 AM
                    days_of_week=[5, 6],  # Weekends only
                    exceptions=["emergency"]
                ),
                preferred_channels={
                    "email": ["executives@company.com"],
                    "sms": ["+1-555-0001", "+1-555-0002"]
                },
                escalation_threshold="critical",
                contact_methods={
                    EscalationLevel.NORMAL: [],
                    EscalationLevel.URGENT: [],
                    EscalationLevel.CRITICAL: ["email"],
                    EscalationLevel.EMERGENCY: ["email", "sms"]
                }
            ),
            "customer_success": StakeholderProfile(
                stakeholder_id="customer_success",
                name="Customer Success Team",
                timezone="America/Chicago",
                business_hours=BusinessHours(
                    start_hour=8,
                    end_hour=20,  # Extended hours for customer support
                    days_of_week=[0, 1, 2, 3, 4, 5, 6],  # 7 days a week
                    timezone="America/Chicago"
                ),
                dnd_policy=DoNotDisturbPolicy(
                    enabled=True,
                    start_hour=22,  # 10 PM
                    end_hour=6,     # 6 AM
                    days_of_week=[0, 1, 2, 3, 4, 5, 6],  # All days
                    exceptions=["critical", "emergency"]
                ),
                preferred_channels={
                    "slack": ["#customer-success"],
                    "email": ["cs-team@company.com"]
                },
                escalation_threshold="high",
                contact_methods={
                    EscalationLevel.NORMAL: ["slack"],
                    EscalationLevel.URGENT: ["slack", "email"],
                    EscalationLevel.CRITICAL: ["slack", "email"],
                    EscalationLevel.EMERGENCY: ["slack", "email"]
                }
            )
        }
    
    def _initialize_escalation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize escalation rules based on incident severity and time"""
        return {
            "critical": {
                "immediate_escalation": True,
                "escalation_intervals": [0, 5, 15],  # Minutes
                "override_dnd": True,
                "required_acknowledgment": True,
                "escalation_level": EscalationLevel.CRITICAL
            },
            "high": {
                "immediate_escalation": True,
                "escalation_intervals": [0, 10, 30],  # Minutes
                "override_dnd": False,
                "required_acknowledgment": True,
                "escalation_level": EscalationLevel.URGENT
            },
            "medium": {
                "immediate_escalation": False,
                "escalation_intervals": [0, 30, 60],  # Minutes
                "override_dnd": False,
                "required_acknowledgment": False,
                "escalation_level": EscalationLevel.NORMAL
            },
            "low": {
                "immediate_escalation": False,
                "escalation_intervals": [0, 60, 120],  # Minutes
                "override_dnd": False,
                "required_acknowledgment": False,
                "escalation_level": EscalationLevel.NORMAL
            }
        }
    
    def get_local_time(self, timezone_str: str) -> datetime:
        """Get current local time for a timezone"""
        try:
            tz = pytz.timezone(timezone_str)
            return datetime.now(tz)
        except Exception as e:
            logger.error(f"Error getting local time for timezone {timezone_str}: {e}")
            return datetime.utcnow()
    
    def is_business_hours(self, stakeholder_id: str, check_time: datetime = None) -> bool:
        """Check if it's currently business hours for a stakeholder"""
        try:
            if stakeholder_id not in self.stakeholder_profiles:
                return False
            
            profile = self.stakeholder_profiles[stakeholder_id]
            
            if check_time is None:
                check_time = self.get_local_time(profile.timezone)
            
            # Check day of week
            if check_time.weekday() not in profile.business_hours.days_of_week:
                return False
            
            # Check hour
            current_hour = check_time.hour
            return profile.business_hours.start_hour <= current_hour < profile.business_hours.end_hour
            
        except Exception as e:
            logger.error(f"Error checking business hours for {stakeholder_id}: {e}")
            return False
    
    def is_dnd_active(self, stakeholder_id: str, incident_severity: str, check_time: datetime = None) -> bool:
        """Check if do-not-disturb is active for a stakeholder"""
        try:
            if stakeholder_id not in self.stakeholder_profiles:
                return False
            
            profile = self.stakeholder_profiles[stakeholder_id]
            dnd_policy = profile.dnd_policy
            
            if not dnd_policy.enabled:
                return False
            
            # Check if severity overrides DND
            if incident_severity in dnd_policy.exceptions:
                return False
            
            if check_time is None:
                check_time = self.get_local_time(profile.timezone)
            
            # Check day of week
            if check_time.weekday() not in dnd_policy.days_of_week:
                return False
            
            # Check DND hours
            current_hour = check_time.hour
            
            # Handle overnight DND periods (e.g., 22:00 to 07:00)
            if dnd_policy.start_hour > dnd_policy.end_hour:
                return current_hour >= dnd_policy.start_hour or current_hour < dnd_policy.end_hour
            else:
                return dnd_policy.start_hour <= current_hour < dnd_policy.end_hour
            
        except Exception as e:
            logger.error(f"Error checking DND status for {stakeholder_id}: {e}")
            return False
    
    def get_relevant_stakeholders(
        self,
        incident_severity: str,
        business_impact: str = None,
        affected_services: List[str] = None
    ) -> List[str]:
        """Get list of stakeholders who should be notified"""
        try:
            relevant_stakeholders = []
            
            for stakeholder_id, profile in self.stakeholder_profiles.items():
                # Check if stakeholder should be notified based on severity threshold
                severity_levels = ["low", "medium", "high", "critical"]
                
                try:
                    incident_level = severity_levels.index(incident_severity)
                    threshold_level = severity_levels.index(profile.escalation_threshold)
                    
                    if incident_level >= threshold_level:
                        relevant_stakeholders.append(stakeholder_id)
                except ValueError:
                    # If severity levels don't match, include stakeholder to be safe
                    relevant_stakeholders.append(stakeholder_id)
            
            logger.info(f"Found {len(relevant_stakeholders)} relevant stakeholders for {incident_severity} incident")
            return relevant_stakeholders
            
        except Exception as e:
            logger.error(f"Error getting relevant stakeholders: {e}")
            return list(self.stakeholder_profiles.keys())  # Return all on error
    
    def calculate_escalation_level(
        self,
        incident_severity: str,
        stakeholder_id: str,
        incident_age_minutes: int = 0
    ) -> EscalationLevel:
        """Calculate appropriate escalation level"""
        try:
            if incident_severity not in self.escalation_rules:
                return EscalationLevel.NORMAL
            
            rules = self.escalation_rules[incident_severity]
            base_level = rules["escalation_level"]
            
            # Check if we should escalate based on time
            escalation_intervals = rules["escalation_intervals"]
            
            for i, interval in enumerate(escalation_intervals):
                if incident_age_minutes >= interval:
                    # Escalate level based on time
                    if i == 0:
                        return base_level
                    elif i == 1:
                        return EscalationLevel.URGENT if base_level == EscalationLevel.NORMAL else EscalationLevel.CRITICAL
                    else:
                        return EscalationLevel.EMERGENCY
            
            return base_level
            
        except Exception as e:
            logger.error(f"Error calculating escalation level: {e}")
            return EscalationLevel.NORMAL
    
    def get_notification_channels(
        self,
        stakeholder_id: str,
        escalation_level: EscalationLevel,
        respect_dnd: bool = True,
        incident_severity: str = "medium"
    ) -> Dict[str, List[str]]:
        """Get appropriate notification channels for a stakeholder"""
        try:
            if stakeholder_id not in self.stakeholder_profiles:
                return {}
            
            profile = self.stakeholder_profiles[stakeholder_id]
            
            # Check if DND is active and should be respected
            if respect_dnd and self.is_dnd_active(stakeholder_id, incident_severity):
                logger.info(f"DND active for {stakeholder_id}, limiting notifications")
                # During DND, only use less intrusive channels
                return {"email": profile.preferred_channels.get("email", [])}
            
            # Get channels based on escalation level
            allowed_channel_types = profile.contact_methods.get(escalation_level, [])
            
            channels = {}
            for channel_type in allowed_channel_types:
                if channel_type in profile.preferred_channels:
                    channels[channel_type] = profile.preferred_channels[channel_type]
            
            return channels
            
        except Exception as e:
            logger.error(f"Error getting notification channels for {stakeholder_id}: {e}")
            return {}
    
    def create_escalation_plan(
        self,
        incident_severity: str,
        business_impact: str = None,
        affected_services: List[str] = None
    ) -> Dict[str, Any]:
        """Create a complete escalation plan for an incident"""
        try:
            relevant_stakeholders = self.get_relevant_stakeholders(
                incident_severity, business_impact, affected_services
            )
            
            escalation_plan = {
                "incident_severity": incident_severity,
                "escalation_intervals": self.escalation_rules[incident_severity]["escalation_intervals"],
                "stakeholder_routing": {},
                "created_at": datetime.utcnow().isoformat()
            }
            
            for stakeholder_id in relevant_stakeholders:
                profile = self.stakeholder_profiles[stakeholder_id]
                
                # Calculate initial escalation level
                escalation_level = self.calculate_escalation_level(incident_severity, stakeholder_id)
                
                # Get notification channels
                channels = self.get_notification_channels(
                    stakeholder_id, escalation_level, True, incident_severity
                )
                
                escalation_plan["stakeholder_routing"][stakeholder_id] = {
                    "name": profile.name,
                    "timezone": profile.timezone,
                    "escalation_level": escalation_level.value,
                    "channels": channels,
                    "business_hours": self.is_business_hours(stakeholder_id),
                    "dnd_active": self.is_dnd_active(stakeholder_id, incident_severity),
                    "local_time": self.get_local_time(profile.timezone).isoformat()
                }
            
            return escalation_plan
            
        except Exception as e:
            logger.error(f"Error creating escalation plan: {e}")
            return {
                "incident_severity": incident_severity,
                "error": str(e),
                "stakeholder_routing": {}
            }
    
    def should_escalate(
        self,
        incident_severity: str,
        incident_age_minutes: int,
        acknowledgment_received: bool = False
    ) -> bool:
        """Determine if incident should be escalated"""
        try:
            if incident_severity not in self.escalation_rules:
                return False
            
            rules = self.escalation_rules[incident_severity]
            
            # Check if acknowledgment is required and received
            if rules["required_acknowledgment"] and not acknowledgment_received:
                # Escalate if no acknowledgment after first interval
                first_interval = rules["escalation_intervals"][0] if rules["escalation_intervals"] else 5
                return incident_age_minutes > first_interval
            
            # Check escalation intervals
            escalation_intervals = rules["escalation_intervals"]
            if len(escalation_intervals) > 1:
                # Escalate if we've passed the second interval
                return incident_age_minutes >= escalation_intervals[1]
            
            return False
            
        except Exception as e:
            logger.error(f"Error determining escalation: {e}")
            return False
    
    def get_timezone_statistics(self) -> Dict[str, Any]:
        """Get statistics about timezone coverage and stakeholder distribution"""
        try:
            timezone_distribution = {}
            business_hours_coverage = {}
            
            for stakeholder_id, profile in self.stakeholder_profiles.items():
                tz = profile.timezone
                if tz not in timezone_distribution:
                    timezone_distribution[tz] = []
                timezone_distribution[tz].append(stakeholder_id)
                
                # Check current business hours coverage
                is_business_hours = self.is_business_hours(stakeholder_id)
                if tz not in business_hours_coverage:
                    business_hours_coverage[tz] = {"in_hours": 0, "out_of_hours": 0}
                
                if is_business_hours:
                    business_hours_coverage[tz]["in_hours"] += 1
                else:
                    business_hours_coverage[tz]["out_of_hours"] += 1
            
            stats = {
                "total_stakeholders": len(self.stakeholder_profiles),
                "timezone_distribution": timezone_distribution,
                "business_hours_coverage": business_hours_coverage,
                "escalation_rules": list(self.escalation_rules.keys()),
                "supported_timezones": list(timezone_distribution.keys())
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting timezone statistics: {e}")
            return {"error": str(e)}