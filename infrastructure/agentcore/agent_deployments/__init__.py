"""AgentCore deployment specifications for Incident Commander agents."""

from .base import AgentCoreDeployer, AgentCorePackageSpec
from .communication_agent import COMMUNICATION_AGENT_SPEC
from .diagnosis_agent import DIAGNOSIS_AGENT_SPEC
from .detection_agent import DETECTION_AGENT_SPEC
from .prediction_agent import PREDICTION_AGENT_SPEC
from .resolution_agent import RESOLUTION_AGENT_SPEC

__all__ = [
    "AgentCoreDeployer",
    "AgentCorePackageSpec",
    "COMMUNICATION_AGENT_SPEC",
    "DIAGNOSIS_AGENT_SPEC",
    "DETECTION_AGENT_SPEC",
    "PREDICTION_AGENT_SPEC",
    "RESOLUTION_AGENT_SPEC",
]

