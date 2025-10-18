"""
Communication Agent Module

Provides resilient communication capabilities with deduplication and stakeholder routing.
"""

from .templates import MessageTemplateManager
# from .agent import ResilientCommunicationAgent  # TODO: Implement communication agent
# from .channels import NotificationChannelManager  # TODO: Implement channel manager

__all__ = ["MessageTemplateManager"]