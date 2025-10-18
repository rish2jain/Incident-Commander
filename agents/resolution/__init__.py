"""
Resolution Agent Module

Provides secure, zero-trust resolution capabilities with sandbox validation.
"""

from .agent import SecureResolutionAgent
from .actions import ActionExecutor, ResolutionAction
from .rollback import RollbackManager

__all__ = ["SecureResolutionAgent", "ActionExecutor", "ResolutionAction", "RollbackManager"]