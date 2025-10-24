"""
Bedrock Agent Configuration Service for Incident Commander

Provides automated Bedrock agent setup with proper IAM roles
and knowledge base configuration and content ingestion.
"""

import asyncio
import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, asdict

from src.utils.config import config
from src.utils.logging import get_logger
from src.utils.exceptions import IncidentCommanderError
from src.services.aws import AWSServiceFactory


logger = get_logger("bedrock_agent_configurator")


class AgentType(Enum):
    """Bedrock agent types for incident management."""
    DETECTION_AGENT = "detection"
    DIAGNOSIS_AGENT = "diagnosis"
    PREDICTION_AGENT = "prediction"
    RESOLUTION_AGENT = "resolution"
    COMMUNICATION_AGENT = "communication"


class KnowledgeBaseType(Enum):
    """Knowledge base types for different domains."""
    INCIDENT_PATTERNS = "incident_patterns"
    RESOLUTION_PROCEDURES = "resolution_procedures"
    SYSTEM_DOCUMENTATION = "system_documentation"
    TROUBLESHOOTING_GUIDES = "troubleshooting_guides"
    BEST_PRACTICES = "best_practices"


@dataclass
class BedrockAgentConfig:
    """Bedrock agent configuration."""
    agent_name: str
    agent_type: AgentType
    description: str
    instruction: str
    foundation_model: str
    idle_session_ttl_in_seconds: int
    agent_resource_role_arn: str
    customer_encryption_key_arn: Optional[str]
    tags: Dict[str, str]


@dataclass
class KnowledgeBaseConfig:
    """Knowledge base configuration."""
    knowledge_base_name: str
    knowledge_base_type: KnowledgeBaseType
    description: str
    role_arn: str
    storage_configuration: Dict[str, Any]
    vector_ingestion_configuration: Dict[str, Any]
    tags: Dict[str, str]


@dataclass
class AgentActionGroup:
    """Agent action group configuration."""
    action_group_name: str
    description: str
    action_group_executor: Dict[str, Any]
    action_group_state: str
    api_schema: Dict[str, Any]


@dataclass
class BedrockAgentResult:
    """Result of Bedrock agent configuration."""
    agent_id: str
    agent_arn: str
    agent_name: str
    agent_status: str
    knowledge_bases: List[str]
    action_groups: List[str]
    created_at: datetime
    configuration_details: Dict[str, Any]


class BedrockAgentConfigurationError(IncidentCommanderError):
    """Bedrock agent configuration specific error."""
    pass


class BedrockAgentConfigurator:
    """
    Automated Bedrock agent setup with proper IAM roles.
    
    Provides knowledge base configuration and content ingestion
    for incident management agents.
    """
    
    def __init__(self, aws_factory: AWSServiceFactory):
        """Initialize Bedrock agent configurator."""
        self.aws_factory = aws_factory
        self._configured_agents: Dict[str, BedrockAgentResult] = {}
        self._knowledge_bases: Dict[str, str] = {}  # name -> knowledge_base_id
        
        # Default configurations
        self.default_foundation_model = "anthropic.claude-3-sonnet-20240229-v1:0"
        self.default_session_ttl = 3600  # 1 hour
        
        # Agent-specific configurations
        self.agent_configurations = self._get_agent_configurations()
        self.knowledge_base_configurations = self._get_knowledge_base_configurations()
    
    def _get_agent_configurations(self) -> Dict[AgentType, BedrockAgentConfig]:
        """Get predefined agent configurations."""
        base_role_arn = f"arn:aws:iam::{config.aws.region}:role/IncidentCommanderBedrockAgentRole"
        
        return {
            AgentType.DETECTION_AGENT: BedrockAgentConfig(
                agent_name="incident-commander-detection-agent",
                agent_type=AgentType.DETECTION_AGENT,
                description="Autonomous incident detection and anomaly identification agent",
                instruction="""You are an expert incident detection agent for the Autonomous Incident Commander system.
                
Your primary responsibilities:
1. Monitor system metrics and logs for anomalies
2. Identify potential incidents before they impact users
3. Classify incident severity and urgency
4. Trigger appropriate response workflows
5. Provide initial incident context and metadata

Key capabilities:
- Pattern recognition for known incident types
- Anomaly detection using statistical analysis
- Real-time monitoring of critical system components
- Integration with monitoring tools (CloudWatch, Datadog, etc.)
- False positive reduction through intelligent filtering

Always provide clear, actionable incident reports with:
- Incident type and severity classification
- Affected systems and services
- Potential business impact
- Recommended immediate actions
- Confidence score for your assessment

Maintain high accuracy and minimize false positives while ensuring no critical incidents are missed.""",
                foundation_model=self.default_foundation_model,
                idle_session_ttl_in_seconds=self.default_session_ttl,
                agent_resource_role_arn=base_role_arn,
                customer_encryption_key_arn=None,
                tags={
                    "Project": "IncidentCommander",
                    "AgentType": "Detection",
                    "Environment": config.environment
                }
            ),
            
            AgentType.DIAGNOSIS_AGENT: BedrockAgentConfig(
                agent_name="incident-commander-diagnosis-agent",
                agent_type=AgentType.DIAGNOSIS_AGENT,
                description="Intelligent incident diagnosis and root cause analysis agent",
                instruction="""You are an expert incident diagnosis agent for the Autonomous Incident Commander system.

Your primary responsibilities:
1. Perform deep root cause analysis of detected incidents
2. Correlate symptoms across multiple systems and services
3. Identify the underlying cause of incidents
4. Provide detailed diagnostic reports with evidence
5. Recommend specific resolution strategies

Key capabilities:
- Multi-system correlation and analysis
- Log analysis and pattern matching
- Dependency mapping and impact analysis
- Historical incident pattern recognition
- Integration with observability tools (traces, metrics, logs)

Analysis methodology:
- Gather comprehensive incident data from all relevant sources
- Apply systematic diagnostic frameworks
- Use knowledge base of previous incidents and resolutions
- Validate hypotheses with additional data collection
- Provide confidence-weighted diagnostic conclusions

Always provide thorough diagnostic reports including:
- Root cause identification with supporting evidence
- Contributing factors and conditions
- System dependencies and impact scope
- Recommended resolution approach
- Preventive measures to avoid recurrence
- Confidence level and alternative hypotheses if applicable

Focus on accuracy and completeness while maintaining rapid response times.""",
                foundation_model=self.default_foundation_model,
                idle_session_ttl_in_seconds=self.default_session_ttl,
                agent_resource_role_arn=base_role_arn,
                customer_encryption_key_arn=None,
                tags={
                    "Project": "IncidentCommander",
                    "AgentType": "Diagnosis",
                    "Environment": config.environment
                }
            ),
            
            AgentType.PREDICTION_AGENT: BedrockAgentConfig(
                agent_name="incident-commander-prediction-agent",
                agent_type=AgentType.PREDICTION_AGENT,
                description="Predictive incident analysis and prevention agent",
                instruction="""You are an expert predictive analysis agent for the Autonomous Incident Commander system.

Your primary responsibilities:
1. Predict potential incidents before they occur
2. Analyze trends and patterns that lead to incidents
3. Provide early warning systems for degrading conditions
4. Recommend preventive actions to avoid incidents
5. Optimize system performance to prevent future issues

Key capabilities:
- Time series analysis and trend prediction
- Machine learning model integration for forecasting
- Capacity planning and resource optimization
- Performance degradation detection
- Proactive alerting and recommendation systems

Prediction methodology:
- Analyze historical incident patterns and precursors
- Monitor leading indicators and early warning signals
- Apply predictive models to current system state
- Identify risk factors and vulnerability windows
- Generate actionable prevention recommendations

Always provide forward-looking analysis including:
- Incident probability assessments with timeframes
- Risk factors and contributing conditions
- Recommended preventive actions with priority levels
- Resource optimization suggestions
- Monitoring recommendations for early detection
- Confidence intervals for predictions

Focus on preventing incidents rather than just responding to them, while maintaining practical and actionable recommendations.""",
                foundation_model=self.default_foundation_model,
                idle_session_ttl_in_seconds=self.default_session_ttl,
                agent_resource_role_arn=base_role_arn,
                customer_encryption_key_arn=None,
                tags={
                    "Project": "IncidentCommander",
                    "AgentType": "Prediction",
                    "Environment": config.environment
                }
            ),
            
            AgentType.RESOLUTION_AGENT: BedrockAgentConfig(
                agent_name="incident-commander-resolution-agent",
                agent_type=AgentType.RESOLUTION_AGENT,
                description="Autonomous incident resolution and remediation agent",
                instruction="""You are an expert incident resolution agent for the Autonomous Incident Commander system.

Your primary responsibilities:
1. Execute automated resolution procedures for diagnosed incidents
2. Implement safe and effective remediation strategies
3. Coordinate complex multi-step resolution workflows
4. Validate resolution effectiveness and completeness
5. Implement rollback procedures if resolutions fail

Key capabilities:
- Automated remediation action execution
- Multi-system coordination and orchestration
- Safety validation and risk assessment
- Rollback and recovery procedures
- Integration with infrastructure automation tools

Resolution methodology:
- Analyze diagnosis results and recommended resolution strategies
- Validate resolution safety and potential impact
- Execute resolution steps with proper sequencing and dependencies
- Monitor resolution progress and effectiveness
- Implement rollback if resolution causes additional issues
- Verify complete incident resolution and system stability

Safety and validation protocols:
- Always validate actions before execution in production
- Implement circuit breakers for high-risk operations
- Maintain rollback plans for all resolution actions
- Monitor system health during and after resolution
- Escalate to human operators for high-risk scenarios

Always provide comprehensive resolution reports including:
- Resolution strategy and execution plan
- Step-by-step action log with timestamps
- Validation results and system health checks
- Rollback procedures if needed
- Post-resolution system state and stability confirmation
- Lessons learned and process improvements

Prioritize system stability and safety while achieving rapid incident resolution.""",
                foundation_model=self.default_foundation_model,
                idle_session_ttl_in_seconds=self.default_session_ttl,
                agent_resource_role_arn=base_role_arn,
                customer_encryption_key_arn=None,
                tags={
                    "Project": "IncidentCommander",
                    "AgentType": "Resolution",
                    "Environment": config.environment
                }
            ),
            
            AgentType.COMMUNICATION_AGENT: BedrockAgentConfig(
                agent_name="incident-commander-communication-agent",
                agent_type=AgentType.COMMUNICATION_AGENT,
                description="Intelligent incident communication and stakeholder notification agent",
                instruction="""You are an expert communication agent for the Autonomous Incident Commander system.

Your primary responsibilities:
1. Manage stakeholder communication throughout incident lifecycle
2. Generate clear, accurate incident status updates
3. Coordinate notifications across multiple channels
4. Provide executive summaries and technical details as appropriate
5. Maintain communication audit trails and documentation

Key capabilities:
- Multi-channel communication (Slack, email, PagerDuty, etc.)
- Audience-appropriate message formatting and content
- Real-time status updates and progress reporting
- Escalation management and stakeholder coordination
- Post-incident communication and documentation

Communication principles:
- Provide timely, accurate, and relevant information
- Tailor communication style and detail level to audience
- Maintain transparency while avoiding unnecessary alarm
- Ensure consistent messaging across all channels
- Document all communications for audit and review

Message types and audiences:
- Technical teams: Detailed technical information, logs, and resolution steps
- Management: Business impact, timeline, and resolution progress
- Customers: Service status, expected resolution time, and workarounds
- Executives: High-level summary, business impact, and strategic implications

Always provide professional communication including:
- Clear incident status and current situation
- Business impact and affected services
- Resolution progress and expected timeline
- Actions being taken and next steps
- Contact information for questions and updates
- Appropriate urgency level and tone

Maintain calm, professional communication while ensuring all stakeholders have the information they need to make informed decisions.""",
                foundation_model=self.default_foundation_model,
                idle_session_ttl_in_seconds=self.default_session_ttl,
                agent_resource_role_arn=base_role_arn,
                customer_encryption_key_arn=None,
                tags={
                    "Project": "IncidentCommander",
                    "AgentType": "Communication",
                    "Environment": config.environment
                }
            )
        }
    
    def _get_knowledge_base_configurations(self) -> Dict[KnowledgeBaseType, KnowledgeBaseConfig]:
        """Get predefined knowledge base configurations."""
        base_role_arn = f"arn:aws:iam::{config.aws.region}:role/IncidentCommanderKnowledgeBaseRole"
        
        return {
            KnowledgeBaseType.INCIDENT_PATTERNS: KnowledgeBaseConfig(
                knowledge_base_name="incident-commander-incident-patterns",
                knowledge_base_type=KnowledgeBaseType.INCIDENT_PATTERNS,
                description="Historical incident patterns and signatures for pattern recognition",
                role_arn=base_role_arn,
                storage_configuration={
                    "type": "OPENSEARCH_SERVERLESS",
                    "opensearchServerlessConfiguration": {
                        "collectionArn": f"arn:aws:aoss:{config.aws.region}:123456789012:collection/incident-patterns",
                        "vectorIndexName": "incident-patterns-index",
                        "fieldMapping": {
                            "vectorField": "embedding",
                            "textField": "content",
                            "metadataField": "metadata"
                        }
                    }
                },
                vector_ingestion_configuration={
                    "chunkingConfiguration": {
                        "chunkingStrategy": "FIXED_SIZE",
                        "fixedSizeChunkingConfiguration": {
                            "maxTokens": 512,
                            "overlapPercentage": 20
                        }
                    }
                },
                tags={
                    "Project": "IncidentCommander",
                    "KnowledgeBaseType": "IncidentPatterns",
                    "Environment": config.environment
                }
            ),
            
            KnowledgeBaseType.RESOLUTION_PROCEDURES: KnowledgeBaseConfig(
                knowledge_base_name="incident-commander-resolution-procedures",
                knowledge_base_type=KnowledgeBaseType.RESOLUTION_PROCEDURES,
                description="Documented resolution procedures and remediation steps",
                role_arn=base_role_arn,
                storage_configuration={
                    "type": "OPENSEARCH_SERVERLESS",
                    "opensearchServerlessConfiguration": {
                        "collectionArn": f"arn:aws:aoss:{config.aws.region}:123456789012:collection/resolution-procedures",
                        "vectorIndexName": "resolution-procedures-index",
                        "fieldMapping": {
                            "vectorField": "embedding",
                            "textField": "content",
                            "metadataField": "metadata"
                        }
                    }
                },
                vector_ingestion_configuration={
                    "chunkingConfiguration": {
                        "chunkingStrategy": "FIXED_SIZE",
                        "fixedSizeChunkingConfiguration": {
                            "maxTokens": 1024,
                            "overlapPercentage": 15
                        }
                    }
                },
                tags={
                    "Project": "IncidentCommander",
                    "KnowledgeBaseType": "ResolutionProcedures",
                    "Environment": config.environment
                }
            ),
            
            KnowledgeBaseType.SYSTEM_DOCUMENTATION: KnowledgeBaseConfig(
                knowledge_base_name="incident-commander-system-documentation",
                knowledge_base_type=KnowledgeBaseType.SYSTEM_DOCUMENTATION,
                description="System architecture and operational documentation",
                role_arn=base_role_arn,
                storage_configuration={
                    "type": "OPENSEARCH_SERVERLESS",
                    "opensearchServerlessConfiguration": {
                        "collectionArn": f"arn:aws:aoss:{config.aws.region}:123456789012:collection/system-docs",
                        "vectorIndexName": "system-docs-index",
                        "fieldMapping": {
                            "vectorField": "embedding",
                            "textField": "content",
                            "metadataField": "metadata"
                        }
                    }
                },
                vector_ingestion_configuration={
                    "chunkingConfiguration": {
                        "chunkingStrategy": "SEMANTIC",
                        "semanticChunkingConfiguration": {
                            "maxTokens": 800,
                            "bufferSize": 100,
                            "breakpointPercentileThreshold": 95
                        }
                    }
                },
                tags={
                    "Project": "IncidentCommander",
                    "KnowledgeBaseType": "SystemDocumentation",
                    "Environment": config.environment
                }
            ),
            
            KnowledgeBaseType.TROUBLESHOOTING_GUIDES: KnowledgeBaseConfig(
                knowledge_base_name="incident-commander-troubleshooting-guides",
                knowledge_base_type=KnowledgeBaseType.TROUBLESHOOTING_GUIDES,
                description="Step-by-step troubleshooting guides and diagnostic procedures",
                role_arn=base_role_arn,
                storage_configuration={
                    "type": "OPENSEARCH_SERVERLESS",
                    "opensearchServerlessConfiguration": {
                        "collectionArn": f"arn:aws:aoss:{config.aws.region}:123456789012:collection/troubleshooting",
                        "vectorIndexName": "troubleshooting-index",
                        "fieldMapping": {
                            "vectorField": "embedding",
                            "textField": "content",
                            "metadataField": "metadata"
                        }
                    }
                },
                vector_ingestion_configuration={
                    "chunkingConfiguration": {
                        "chunkingStrategy": "FIXED_SIZE",
                        "fixedSizeChunkingConfiguration": {
                            "maxTokens": 768,
                            "overlapPercentage": 25
                        }
                    }
                },
                tags={
                    "Project": "IncidentCommander",
                    "KnowledgeBaseType": "TroubleshootingGuides",
                    "Environment": config.environment
                }
            ),
            
            KnowledgeBaseType.BEST_PRACTICES: KnowledgeBaseConfig(
                knowledge_base_name="incident-commander-best-practices",
                knowledge_base_type=KnowledgeBaseType.BEST_PRACTICES,
                description="Industry best practices and operational excellence guidelines",
                role_arn=base_role_arn,
                storage_configuration={
                    "type": "OPENSEARCH_SERVERLESS",
                    "opensearchServerlessConfiguration": {
                        "collectionArn": f"arn:aws:aoss:{config.aws.region}:123456789012:collection/best-practices",
                        "vectorIndexName": "best-practices-index",
                        "fieldMapping": {
                            "vectorField": "embedding",
                            "textField": "content",
                            "metadataField": "metadata"
                        }
                    }
                },
                vector_ingestion_configuration={
                    "chunkingConfiguration": {
                        "chunkingStrategy": "SEMANTIC",
                        "semanticChunkingConfiguration": {
                            "maxTokens": 600,
                            "bufferSize": 80,
                            "breakpointPercentileThreshold": 90
                        }
                    }
                },
                tags={
                    "Project": "IncidentCommander",
                    "KnowledgeBaseType": "BestPractices",
                    "Environment": config.environment
                }
            )
        }
    
    async def configure_bedrock_agent(self, agent_type: AgentType, 
                                    custom_config: Optional[Dict[str, Any]] = None) -> BedrockAgentResult:
        """
        Configure a Bedrock agent with proper IAM roles.
        
        Args:
            agent_type: Type of agent to configure
            custom_config: Optional custom configuration overrides
            
        Returns:
            Bedrock agent configuration result
        """
        logger.info(f"Configuring Bedrock agent: {agent_type.value}")
        
        # Get base configuration
        agent_config = self.agent_configurations[agent_type]
        
        # Apply custom configuration if provided
        if custom_config:
            for key, value in custom_config.items():
                if hasattr(agent_config, key):
                    setattr(agent_config, key, value)
        
        try:
            # Create Bedrock agent
            bedrock_client = await self.aws_factory.create_client('bedrock-agent')
            
            # Create agent
            create_response = await bedrock_client.create_agent(
                agentName=agent_config.agent_name,
                description=agent_config.description,
                instruction=agent_config.instruction,
                foundationModel=agent_config.foundation_model,
                idleSessionTTLInSeconds=agent_config.idle_session_ttl_in_seconds,
                agentResourceRoleArn=agent_config.agent_resource_role_arn,
                customerEncryptionKeyArn=agent_config.customer_encryption_key_arn,
                tags=agent_config.tags
            )
            
            agent_id = create_response['agent']['agentId']
            agent_arn = create_response['agent']['agentArn']
            
            logger.info(f"Created Bedrock agent {agent_id} for {agent_type.value}")
            
            # Configure knowledge bases for the agent
            knowledge_bases = await self._configure_agent_knowledge_bases(agent_id, agent_type)
            
            # Configure action groups for the agent
            action_groups = await self._configure_agent_action_groups(agent_id, agent_type)
            
            # Prepare and alias the agent
            await self._prepare_agent(agent_id)
            
            # Create agent result
            agent_result = BedrockAgentResult(
                agent_id=agent_id,
                agent_arn=agent_arn,
                agent_name=agent_config.agent_name,
                agent_status="PREPARED",
                knowledge_bases=knowledge_bases,
                action_groups=action_groups,
                created_at=datetime.utcnow(),
                configuration_details=asdict(agent_config)
            )
            
            # Store configured agent
            self._configured_agents[agent_id] = agent_result
            
            logger.info(f"Successfully configured Bedrock agent {agent_id}")
            return agent_result
            
        except Exception as e:
            logger.error(f"Failed to configure Bedrock agent {agent_type.value}: {e}")
            raise BedrockAgentConfigurationError(f"Agent configuration failed: {e}")
    
    async def configure_knowledge_base(self, kb_type: KnowledgeBaseType,
                                     custom_config: Optional[Dict[str, Any]] = None) -> str:
        """
        Configure a knowledge base with content ingestion.
        
        Args:
            kb_type: Type of knowledge base to configure
            custom_config: Optional custom configuration overrides
            
        Returns:
            Knowledge base ID
        """
        logger.info(f"Configuring knowledge base: {kb_type.value}")
        
        # Get base configuration
        kb_config = self.knowledge_base_configurations[kb_type]
        
        # Apply custom configuration if provided
        if custom_config:
            for key, value in custom_config.items():
                if hasattr(kb_config, key):
                    setattr(kb_config, key, value)
        
        try:
            # Create Bedrock knowledge base
            bedrock_client = await self.aws_factory.create_client('bedrock-agent')
            
            # Create knowledge base
            create_response = await bedrock_client.create_knowledge_base(
                name=kb_config.knowledge_base_name,
                description=kb_config.description,
                roleArn=kb_config.role_arn,
                knowledgeBaseConfiguration={
                    "type": "VECTOR",
                    "vectorKnowledgeBaseConfiguration": {
                        "embeddingModelArn": f"arn:aws:bedrock:{config.aws.region}::foundation-model/amazon.titan-embed-text-v1"
                    }
                },
                storageConfiguration=kb_config.storage_configuration,
                tags=kb_config.tags
            )
            
            knowledge_base_id = create_response['knowledgeBase']['knowledgeBaseId']
            
            logger.info(f"Created knowledge base {knowledge_base_id} for {kb_type.value}")
            
            # Create data source for the knowledge base
            data_source_id = await self._create_knowledge_base_data_source(
                knowledge_base_id, kb_type, kb_config
            )
            
            # Ingest initial content
            await self._ingest_knowledge_base_content(knowledge_base_id, data_source_id, kb_type)
            
            # Store knowledge base mapping
            self._knowledge_bases[kb_config.knowledge_base_name] = knowledge_base_id
            
            logger.info(f"Successfully configured knowledge base {knowledge_base_id}")
            return knowledge_base_id
            
        except Exception as e:
            logger.error(f"Failed to configure knowledge base {kb_type.value}: {e}")
            raise BedrockAgentConfigurationError(f"Knowledge base configuration failed: {e}")
    
    async def _configure_agent_knowledge_bases(self, agent_id: str, 
                                             agent_type: AgentType) -> List[str]:
        """Configure knowledge bases for a specific agent type."""
        knowledge_bases = []
        
        # Define which knowledge bases each agent type should have access to
        agent_kb_mapping = {
            AgentType.DETECTION_AGENT: [
                KnowledgeBaseType.INCIDENT_PATTERNS,
                KnowledgeBaseType.SYSTEM_DOCUMENTATION
            ],
            AgentType.DIAGNOSIS_AGENT: [
                KnowledgeBaseType.INCIDENT_PATTERNS,
                KnowledgeBaseType.TROUBLESHOOTING_GUIDES,
                KnowledgeBaseType.SYSTEM_DOCUMENTATION
            ],
            AgentType.PREDICTION_AGENT: [
                KnowledgeBaseType.INCIDENT_PATTERNS,
                KnowledgeBaseType.BEST_PRACTICES,
                KnowledgeBaseType.SYSTEM_DOCUMENTATION
            ],
            AgentType.RESOLUTION_AGENT: [
                KnowledgeBaseType.RESOLUTION_PROCEDURES,
                KnowledgeBaseType.TROUBLESHOOTING_GUIDES,
                KnowledgeBaseType.BEST_PRACTICES
            ],
            AgentType.COMMUNICATION_AGENT: [
                KnowledgeBaseType.BEST_PRACTICES,
                KnowledgeBaseType.SYSTEM_DOCUMENTATION
            ]
        }
        
        required_kbs = agent_kb_mapping.get(agent_type, [])
        
        bedrock_client = await self.aws_factory.create_client('bedrock-agent')
        
        for kb_type in required_kbs:
            try:
                # Ensure knowledge base exists
                if kb_type.value not in [kb.knowledge_base_type.value for kb in self.knowledge_base_configurations.values()]:
                    kb_id = await self.configure_knowledge_base(kb_type)
                else:
                    kb_config = self.knowledge_base_configurations[kb_type]
                    kb_id = self._knowledge_bases.get(kb_config.knowledge_base_name)
                    
                    if not kb_id:
                        kb_id = await self.configure_knowledge_base(kb_type)
                
                # Associate knowledge base with agent
                await bedrock_client.associate_agent_knowledge_base(
                    agentId=agent_id,
                    agentVersion="DRAFT",
                    knowledgeBaseId=kb_id,
                    description=f"Knowledge base for {kb_type.value}",
                    knowledgeBaseState="ENABLED"
                )
                
                knowledge_bases.append(kb_id)
                logger.info(f"Associated knowledge base {kb_id} with agent {agent_id}")
                
            except Exception as e:
                logger.warning(f"Failed to associate knowledge base {kb_type.value} with agent {agent_id}: {e}")
        
        return knowledge_bases
    
    async def _configure_agent_action_groups(self, agent_id: str, 
                                           agent_type: AgentType) -> List[str]:
        """Configure action groups for a specific agent type."""
        action_groups = []
        
        # Define action groups for each agent type
        agent_actions = self._get_agent_action_groups(agent_type)
        
        bedrock_client = await self.aws_factory.create_client('bedrock-agent')
        
        for action_group in agent_actions:
            try:
                # Create action group
                response = await bedrock_client.create_agent_action_group(
                    agentId=agent_id,
                    agentVersion="DRAFT",
                    actionGroupName=action_group.action_group_name,
                    description=action_group.description,
                    actionGroupExecutor=action_group.action_group_executor,
                    actionGroupState=action_group.action_group_state,
                    apiSchema=action_group.api_schema
                )
                
                action_group_id = response['agentActionGroup']['actionGroupId']
                action_groups.append(action_group_id)
                
                logger.info(f"Created action group {action_group_id} for agent {agent_id}")
                
            except Exception as e:
                logger.warning(f"Failed to create action group {action_group.action_group_name} for agent {agent_id}: {e}")
        
        return action_groups
    
    def _get_agent_action_groups(self, agent_type: AgentType) -> List[AgentActionGroup]:
        """Get action groups configuration for agent type."""
        base_lambda_arn = f"arn:aws:lambda:{config.aws.region}:123456789012:function"
        
        action_groups = {
            AgentType.DETECTION_AGENT: [
                AgentActionGroup(
                    action_group_name="monitoring-actions",
                    description="Actions for monitoring and metric collection",
                    action_group_executor={
                        "lambda": f"{base_lambda_arn}:incident-commander-detection-actions"
                    },
                    action_group_state="ENABLED",
                    api_schema={
                        "payload": json.dumps({
                            "openapi": "3.0.0",
                            "info": {"title": "Detection Actions API", "version": "1.0.0"},
                            "paths": {
                                "/collect-metrics": {
                                    "post": {
                                        "description": "Collect system metrics for analysis",
                                        "parameters": [
                                            {"name": "metric_type", "in": "query", "required": True, "schema": {"type": "string"}},
                                            {"name": "time_range", "in": "query", "required": True, "schema": {"type": "string"}}
                                        ]
                                    }
                                },
                                "/analyze-logs": {
                                    "post": {
                                        "description": "Analyze log patterns for anomalies",
                                        "parameters": [
                                            {"name": "log_source", "in": "query", "required": True, "schema": {"type": "string"}},
                                            {"name": "pattern", "in": "query", "required": False, "schema": {"type": "string"}}
                                        ]
                                    }
                                }
                            }
                        })
                    }
                )
            ],
            
            AgentType.DIAGNOSIS_AGENT: [
                AgentActionGroup(
                    action_group_name="diagnostic-actions",
                    description="Actions for incident diagnosis and analysis",
                    action_group_executor={
                        "lambda": f"{base_lambda_arn}:incident-commander-diagnosis-actions"
                    },
                    action_group_state="ENABLED",
                    api_schema={
                        "payload": json.dumps({
                            "openapi": "3.0.0",
                            "info": {"title": "Diagnosis Actions API", "version": "1.0.0"},
                            "paths": {
                                "/correlate-events": {
                                    "post": {
                                        "description": "Correlate events across systems",
                                        "parameters": [
                                            {"name": "incident_id", "in": "query", "required": True, "schema": {"type": "string"}},
                                            {"name": "time_window", "in": "query", "required": True, "schema": {"type": "string"}}
                                        ]
                                    }
                                },
                                "/analyze-dependencies": {
                                    "post": {
                                        "description": "Analyze system dependencies and impact",
                                        "parameters": [
                                            {"name": "service_name", "in": "query", "required": True, "schema": {"type": "string"}}
                                        ]
                                    }
                                }
                            }
                        })
                    }
                )
            ],
            
            AgentType.RESOLUTION_AGENT: [
                AgentActionGroup(
                    action_group_name="resolution-actions",
                    description="Actions for incident resolution and remediation",
                    action_group_executor={
                        "lambda": f"{base_lambda_arn}:incident-commander-resolution-actions"
                    },
                    action_group_state="ENABLED",
                    api_schema={
                        "payload": json.dumps({
                            "openapi": "3.0.0",
                            "info": {"title": "Resolution Actions API", "version": "1.0.0"},
                            "paths": {
                                "/execute-remediation": {
                                    "post": {
                                        "description": "Execute automated remediation actions",
                                        "parameters": [
                                            {"name": "action_type", "in": "query", "required": True, "schema": {"type": "string"}},
                                            {"name": "target_resource", "in": "query", "required": True, "schema": {"type": "string"}},
                                            {"name": "safety_check", "in": "query", "required": False, "schema": {"type": "boolean"}}
                                        ]
                                    }
                                },
                                "/rollback-changes": {
                                    "post": {
                                        "description": "Rollback previous changes if resolution fails",
                                        "parameters": [
                                            {"name": "rollback_id", "in": "query", "required": True, "schema": {"type": "string"}}
                                        ]
                                    }
                                }
                            }
                        })
                    }
                )
            ]
        }
        
        return action_groups.get(agent_type, [])
    
    async def _create_knowledge_base_data_source(self, knowledge_base_id: str,
                                               kb_type: KnowledgeBaseType,
                                               kb_config: KnowledgeBaseConfig) -> str:
        """Create data source for knowledge base."""
        bedrock_client = await self.aws_factory.create_client('bedrock-agent')
        
        # Create S3 data source
        data_source_name = f"{kb_config.knowledge_base_name}-data-source"
        s3_bucket = f"incident-commander-kb-{kb_type.value}"
        
        response = await bedrock_client.create_data_source(
            knowledgeBaseId=knowledge_base_id,
            name=data_source_name,
            description=f"Data source for {kb_type.value} knowledge base",
            dataSourceConfiguration={
                "type": "S3",
                "s3Configuration": {
                    "bucketArn": f"arn:aws:s3:::{s3_bucket}",
                    "inclusionPrefixes": [f"{kb_type.value}/"]
                }
            },
            vectorIngestionConfiguration=kb_config.vector_ingestion_configuration
        )
        
        return response['dataSource']['dataSourceId']
    
    async def _ingest_knowledge_base_content(self, knowledge_base_id: str,
                                           data_source_id: str,
                                           kb_type: KnowledgeBaseType) -> None:
        """Ingest initial content into knowledge base."""
        logger.info(f"Starting content ingestion for knowledge base {knowledge_base_id}")
        
        bedrock_client = await self.aws_factory.create_client('bedrock-agent')
        
        try:
            # Start ingestion job
            response = await bedrock_client.start_ingestion_job(
                knowledgeBaseId=knowledge_base_id,
                dataSourceId=data_source_id,
                description=f"Initial content ingestion for {kb_type.value}"
            )
            
            ingestion_job_id = response['ingestionJob']['ingestionJobId']
            
            # Wait for ingestion to complete (with timeout)
            max_wait_time = 300  # 5 minutes
            wait_interval = 10   # 10 seconds
            elapsed_time = 0
            
            while elapsed_time < max_wait_time:
                job_response = await bedrock_client.get_ingestion_job(
                    knowledgeBaseId=knowledge_base_id,
                    dataSourceId=data_source_id,
                    ingestionJobId=ingestion_job_id
                )
                
                status = job_response['ingestionJob']['status']
                
                if status == 'COMPLETE':
                    logger.info(f"Content ingestion completed for knowledge base {knowledge_base_id}")
                    return
                elif status == 'FAILED':
                    raise BedrockAgentConfigurationError(f"Content ingestion failed for knowledge base {knowledge_base_id}")
                
                await asyncio.sleep(wait_interval)
                elapsed_time += wait_interval
            
            logger.warning(f"Content ingestion timed out for knowledge base {knowledge_base_id}")
            
        except Exception as e:
            logger.error(f"Failed to ingest content for knowledge base {knowledge_base_id}: {e}")
            # Don't raise exception as this is not critical for agent functionality
    
    async def _prepare_agent(self, agent_id: str) -> None:
        """Prepare agent for use."""
        bedrock_client = await self.aws_factory.create_client('bedrock-agent')
        
        try:
            # Prepare agent
            await bedrock_client.prepare_agent(
                agentId=agent_id
            )
            
            # Create agent alias
            await bedrock_client.create_agent_alias(
                agentId=agent_id,
                agentAliasName="PRODUCTION",
                description="Production alias for incident commander agent"
            )
            
            logger.info(f"Successfully prepared agent {agent_id}")
            
        except Exception as e:
            logger.error(f"Failed to prepare agent {agent_id}: {e}")
            raise BedrockAgentConfigurationError(f"Agent preparation failed: {e}")
    
    def get_configured_agents(self) -> Dict[str, BedrockAgentResult]:
        """Get all configured agents."""
        return self._configured_agents.copy()
    
    def get_knowledge_bases(self) -> Dict[str, str]:
        """Get all configured knowledge bases."""
        return self._knowledge_bases.copy()
    
    async def validate_agent_configuration(self, agent_id: str) -> Dict[str, Any]:
        """Validate agent configuration and functionality."""
        if agent_id not in self._configured_agents:
            return {
                "is_valid": False,
                "error": "Agent not found in configured agents"
            }
        
        try:
            bedrock_client = await self.aws_factory.create_client('bedrock-agent')
            
            # Get agent details
            response = await bedrock_client.get_agent(agentId=agent_id)
            agent_status = response['agent']['agentStatus']
            
            # Validate agent is prepared
            if agent_status != 'PREPARED':
                return {
                    "is_valid": False,
                    "error": f"Agent status is {agent_status}, expected PREPARED"
                }
            
            # Test agent invocation (basic test)
            runtime_client = await self.aws_factory.create_client('bedrock-agent-runtime')
            
            test_response = await runtime_client.invoke_agent(
                agentId=agent_id,
                agentAliasId="PRODUCTION",
                sessionId="validation-session",
                inputText="Hello, this is a validation test."
            )
            
            return {
                "is_valid": True,
                "agent_status": agent_status,
                "test_response_received": True,
                "validation_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "is_valid": False,
                "error": f"Validation failed: {e}"
            }


# Global Bedrock agent configurator instance
_bedrock_configurator: Optional[BedrockAgentConfigurator] = None


def get_bedrock_agent_configurator(aws_factory: Optional[AWSServiceFactory] = None) -> BedrockAgentConfigurator:
    """Get or create the global Bedrock agent configurator instance."""
    global _bedrock_configurator
    if _bedrock_configurator is None:
        if aws_factory is None:
            from src.services.aws import get_aws_service_factory
            aws_factory = get_aws_service_factory()
        _bedrock_configurator = BedrockAgentConfigurator(aws_factory)
    return _bedrock_configurator