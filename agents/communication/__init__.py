"""
Communication Agent Module

Provides resilient communication capabilities with deduplication and stakeholder routing.
"""

from .templates import MessageTemplateManager
from .agent import ResilientCommunicationAgent
from .channels import NotificationChannelManager

__all__ = [
    "MessageTemplateManager",
    "ResilientCommunicationAgent", 
    "NotificationChannelManager"
]