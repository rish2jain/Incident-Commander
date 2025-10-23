"""Agent deployment specifications for AWS Bedrock AgentCore Runtime."""

from infrastructure.agentcore.agent_deployments.base import (
    AgentCoreDeployer,
    AgentCorePackageSpec,
)
from infrastructure.agentcore.agent_deployments.communication_agent import (
    COMMUNICATION_AGENT_SPEC,
)
from infrastructure.agentcore.agent_deployments.detection_agent import DETECTION_AGENT_SPEC
from infrastructure.agentcore.agent_deployments.diagnosis_agent import DIAGNOSIS_AGENT_SPEC
from infrastructure.agentcore.agent_deployments.prediction_agent import PREDICTION_AGENT_SPEC
from infrastructure.agentcore.agent_deployments.resolution_agent import RESOLUTION_AGENT_SPEC

__all__ = [
    "AgentCorePackageSpec",
    "AgentCoreDeployer",
    "DETECTION_AGENT_SPEC",
    "DIAGNOSIS_AGENT_SPEC",
    "PREDICTION_AGENT_SPEC",
    "RESOLUTION_AGENT_SPEC",
    "COMMUNICATION_AGENT_SPEC",
]
