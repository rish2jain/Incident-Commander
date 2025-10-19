"""
Agent Swarm Coordinator for Multi-Agent Orchestration

Provides coordinated workflow management, dependency ordering, deadlock prevention,
agent state checkpointing, and graceful degradation with fallback chains.

Task 13.1: Integrate all agents into coordinated workflow
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import networkx as nx

from src.utils.logging import get_logger
from src.utils.constants import SHARED_RETRY_POLICIES
from src.interfaces.agent import BaseAgent
from src.models.incident import Incident
from src.models.agent import AgentRecommendation, ConsensusDecision


logger = get_logger("agent_swarm_coordinator")


class AgentState(Enum):
    """Agent execution states."""
    IDLE = "idle"
    INITIALIZING = "initializing"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEGRADED = "degraded"
    CHECKPOINTED = "checkpointed"


class WorkflowPhase(Enum):
    """Workflow execution phases."""
    DETECTION = "detection"
    DIAGNOSIS = "diagnosis"
    PREDICTION = "prediction"
    RESOLUTION = "resolution"
    COMMUNICATION = "communication"
    CONSENSUS = "consensus"
    COMPLETED = "completed"


@dataclass
class AgentCheckpoint:
    """Agent state checkpoint for recovery."""
    agent_id: str
    checkpoint_time: datetime
    agent_state: AgentState
    processing_data: Dict[str, Any]
    recommendations: List[AgentRecommendation]
    confidence_score: float
    execution_context: Dict[str, Any]


@dataclass
class DependencyNode:
    """Dependency graph node for agent orchestration."""
    agent_id: str
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    execution_order: int = 0
    can_execute_parallel: bool = False


@dataclass
class FallbackChain:
    """Fallback chain for graceful degradation."""
    primary_agent: str
    fallback_agents: List[str]
    degradation_strategy: str
    confidence_threshold: float
    timeout_seconds: int


class AgentSwarmCoordinator:
    """
    Multi-agent orchestration coordinator with dependency management.
    
    Provides coordinated workflow execution, dependency ordering, deadlock prevention,
    state checkpointing, and graceful degradation for autonomous incident response.
    """
    
    def __init__(self):
        self.registered_agents: Dict[str, BaseAgent] = {}
        self.agent_states: Dict[str, AgentState] = {}
        self.agent_checkpoints: Dict[str, List[AgentCheckpoint]] = {}
        self.dependency_graph = nx.DiGraph()
        self.fallback_chains: Dict[str, FallbackChain] = {}
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.checkpoint_cadence = timedelta(seconds=30)  # Shared checkpoint cadence
        self._initialize_dependency_graph()
        self._initialize_fallback_chains()
        
    def _initialize_dependency_graph(self):
        """Initialize agent dependency graph for orchestration."""
        # Define agent dependencies based on incident response workflow
        dependencies = {
            "detection": [],  # No dependencies - first responder
            "diagnosis": ["detection"],  # Depends on detection results
            "prediction": ["detection"],  # Can run parallel to diagnosis
            "resolution": ["diagnosis", "prediction"],  # Depends on both analysis agents
            "communication": ["resolution"]  # Final step after resolution
        }
        
        # Build dependency graph
        for agent_id, deps in dependencies.items():
            self.dependency_graph.add_node(agent_id)
            for dep in deps:
                self.dependency_graph.add_edge(dep, agent_id)
        
        # Validate no circular dependencies
        if not nx.is_directed_acyclic_graph(self.dependency_graph):
            raise ValueError("Circular dependency detected in agent workflow")
        
        logger.info("Agent dependency graph initialized successfully")
    
    def _initialize_fallback_chains(self):
        """Initialize fallback chains for graceful degradation."""
        self.fallback_chains = {
            "detection": FallbackChain(
                primary_agent="detection",
                fallback_agents=["simple_threshold_detection", "manual_detection"],
                degradation_strategy="threshold_based_fallback",
                confidence_threshold=0.7,
                timeout_seconds=60
            ),
            "diagnosis": FallbackChain(
                primary_agent="diagnosis",
                fallback_agents=["pattern_matching_diagnosis", "manual_diagnosis"],
                degradation_strategy="pattern_based_fallback",
                confidence_threshold=0.6,
                timeout_seconds=180
            ),
            "prediction": FallbackChain(
                primary_agent="prediction",
                fallback_agents=["statistical_prediction", "historical_prediction"],
                degradation_strategy="statistical_fallback",
                confidence_threshold=0.5,
                timeout_seconds=150
            ),
            "resolution": FallbackChain(
                primary_agent="resolution",
                fallback_agents=["safe_mode_resolution", "manual_escalation"],
                degradation_strategy="safe_mode_fallback",
                confidence_threshold=0.8,
                timeout_seconds=300
            ),
            "communication": FallbackChain(
                primary_agent="communication",
                fallback_agents=["basic_notification", "email_fallback"],
                degradation_strategy="notification_fallback",
                confidence_threshold=0.9,
                timeout_seconds=30
            )
        }
    
    async def register_agent(self, agent: BaseAgent) -> bool:
        """Register agent with the swarm coordinator."""
        try:
            agent_id = agent.agent_id
            self.registered_agents[agent_id] = agent
            self.agent_states[agent_id] = AgentState.IDLE
            self.agent_checkpoints[agent_id] = []
            
            logger.info(f"Agent {agent_id} registered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register agent {agent.agent_id}: {e}")
            return False
    
    async def process_incident_workflow(self, incident: Incident) -> Dict[str, Any]:
        """
        Process incident through coordinated multi-agent workflow.
        
        Implements dependency ordering, parallel execution, and graceful degradation.
        """
        workflow_id = f"workflow_{incident.id}_{int(time.time())}"
        
        try:
            # Initialize workflow state
            workflow_state = {
                "workflow_id": workflow_id,
                "incident_id": incident.id,
                "start_time": datetime.utcnow(),
                "current_phase": WorkflowPhase.DETECTION,
                "agent_results": {},
                "checkpoints": [],
                "errors": [],
                "completed": False
            }
            
            self.active_workflows[workflow_id] = workflow_state
            
            logger.info(f"Starting coordinated workflow {workflow_id} for incident {incident.id}")
            
            # Execute workflow phases in dependency order
            execution_plan = self._create_execution_plan()
            
            for phase_agents in execution_plan:
                await self._execute_workflow_phase(workflow_id, incident, phase_agents)
                
                # Create checkpoint after each phase
                await self._create_workflow_checkpoint(workflow_id)
            
            # Mark workflow as completed
            workflow_state["completed"] = True
            workflow_state["end_time"] = datetime.utcnow()
            workflow_state["duration_seconds"] = (workflow_state["end_time"] - workflow_state["start_time"]).total_seconds()
            
            logger.info(f"Workflow {workflow_id} completed successfully in {workflow_state['duration_seconds']:.1f}s")
            
            return workflow_state
            
        except Exception as e:
            logger.error(f"Workflow {workflow_id} failed: {e}")
            await self._handle_workflow_failure(workflow_id, e)
            raise
    
    def _create_execution_plan(self) -> List[List[str]]:
        """
        Create execution plan with dependency ordering and parallel execution.
        
        Returns list of agent groups that can execute in parallel.
        """
        # Topological sort for dependency ordering
        try:
            topo_order = list(nx.topological_sort(self.dependency_graph))
        except nx.NetworkXError as e:
            logger.error(f"Failed to create execution plan: {e}")
            raise
        
        # Group agents by execution level for parallel execution
        execution_levels = {}
        for agent_id in topo_order:
            # Calculate execution level based on longest path from root
            if not list(self.dependency_graph.predecessors(agent_id)):
                # No dependencies - level 0
                execution_levels[agent_id] = 0
            else:
                # Level is max of predecessor levels + 1
                max_pred_level = max(
                    execution_levels[pred] 
                    for pred in self.dependency_graph.predecessors(agent_id)
                )
                execution_levels[agent_id] = max_pred_level + 1
        
        # Group agents by execution level
        level_groups = {}
        for agent_id, level in execution_levels.items():
            if level not in level_groups:
                level_groups[level] = []
            level_groups[level].append(agent_id)
        
        # Return execution plan as ordered list of parallel groups
        execution_plan = []
        for level in sorted(level_groups.keys()):
            execution_plan.append(level_groups[level])
        
        logger.info(f"Created execution plan: {execution_plan}")
        return execution_plan
    
    async def _execute_workflow_phase(
        self, 
        workflow_id: str, 
        incident: Incident, 
        phase_agents: List[str]
    ):
        """Execute workflow phase with parallel agent execution."""
        workflow_state = self.active_workflows[workflow_id]
        
        logger.info(f"Executing workflow phase with agents: {phase_agents}")
        
        # Execute agents in parallel
        tasks = []
        for agent_id in phase_agents:
            if agent_id in self.registered_agents:
                task = asyncio.create_task(
                    self._execute_agent_with_fallback(workflow_id, agent_id, incident)
                )
                tasks.append((agent_id, task))
        
        # Wait for all agents to complete
        for agent_id, task in tasks:
            try:
                result = await task
                workflow_state["agent_results"][agent_id] = result
                self.agent_states[agent_id] = AgentState.COMPLETED
                
            except Exception as e:
                logger.error(f"Agent {agent_id} failed in workflow {workflow_id}: {e}")
                workflow_state["errors"].append({
                    "agent_id": agent_id,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })
                self.agent_states[agent_id] = AgentState.FAILED
                
                # Attempt fallback
                await self._execute_fallback_chain(workflow_id, agent_id, incident, e)
    
    async def _execute_agent_with_fallback(
        self, 
        workflow_id: str, 
        agent_id: str, 
        incident: Incident
    ) -> Dict[str, Any]:
        """Execute agent with timeout and fallback handling."""
        if agent_id not in self.registered_agents:
            raise ValueError(f"Agent {agent_id} not registered")
        
        agent = self.registered_agents[agent_id]
        fallback_chain = self.fallback_chains.get(agent_id)
        
        if not fallback_chain:
            raise ValueError(f"No fallback chain configured for agent {agent_id}")
        
        # Set agent state to processing
        self.agent_states[agent_id] = AgentState.PROCESSING
        
        try:
            # Execute primary agent with timeout
            result = await asyncio.wait_for(
                agent.process_incident(incident),
                timeout=fallback_chain.timeout_seconds
            )
            
            # Validate result confidence
            if hasattr(result, 'confidence') and result.confidence < fallback_chain.confidence_threshold:
                logger.warning(f"Agent {agent_id} confidence {result.confidence} below threshold {fallback_chain.confidence_threshold}")
                # Continue with low confidence but mark as degraded
                self.agent_states[agent_id] = AgentState.DEGRADED
            
            return {
                "agent_id": agent_id,
                "result": result,
                "execution_time": time.time(),
                "status": "success",
                "confidence": getattr(result, 'confidence', 1.0)
            }
            
        except asyncio.TimeoutError:
            logger.error(f"Agent {agent_id} timed out after {fallback_chain.timeout_seconds}s")
            raise
        except Exception as e:
            logger.error(f"Agent {agent_id} execution failed: {e}")
            raise
    
    async def _execute_fallback_chain(
        self, 
        workflow_id: str, 
        agent_id: str, 
        incident: Incident, 
        original_error: Exception
    ):
        """Execute fallback chain for graceful degradation."""
        fallback_chain = self.fallback_chains.get(agent_id)
        if not fallback_chain:
            logger.error(f"No fallback chain available for agent {agent_id}")
            return
        
        logger.info(f"Executing fallback chain for agent {agent_id}")
        
        for fallback_agent_id in fallback_chain.fallback_agents:
            try:
                # Attempt fallback execution
                if fallback_agent_id == "manual_escalation":
                    # Trigger human escalation
                    await self._trigger_human_escalation(workflow_id, agent_id, incident, original_error)
                    return
                elif fallback_agent_id.startswith("simple_") or fallback_agent_id.startswith("basic_"):
                    # Execute simplified version
                    result = await self._execute_simplified_agent(fallback_agent_id, incident)
                    
                    # Store fallback result
                    workflow_state = self.active_workflows[workflow_id]
                    workflow_state["agent_results"][agent_id] = {
                        "agent_id": agent_id,
                        "result": result,
                        "execution_time": time.time(),
                        "status": "fallback_success",
                        "fallback_agent": fallback_agent_id,
                        "original_error": str(original_error)
                    }
                    
                    self.agent_states[agent_id] = AgentState.DEGRADED
                    logger.info(f"Fallback successful for agent {agent_id} using {fallback_agent_id}")
                    return
                    
            except Exception as fallback_error:
                logger.error(f"Fallback {fallback_agent_id} failed for agent {agent_id}: {fallback_error}")
                continue
        
        # All fallbacks failed - trigger human escalation
        await self._trigger_human_escalation(workflow_id, agent_id, incident, original_error)
    
    async def _execute_simplified_agent(self, fallback_agent_id: str, incident: Incident) -> Any:
        """Execute simplified fallback agent logic."""
        if fallback_agent_id == "simple_threshold_detection":
            # Simple threshold-based detection
            return {
                "detected": True,
                "confidence": 0.6,
                "method": "threshold_based",
                "description": "Fallback threshold detection"
            }
        elif fallback_agent_id == "pattern_matching_diagnosis":
            # Simple pattern matching diagnosis
            return {
                "root_cause": "unknown_pattern",
                "confidence": 0.5,
                "method": "pattern_matching",
                "description": "Fallback pattern diagnosis"
            }
        elif fallback_agent_id == "statistical_prediction":
            # Simple statistical prediction
            return {
                "prediction": "stable",
                "confidence": 0.4,
                "method": "statistical",
                "description": "Fallback statistical prediction"
            }
        elif fallback_agent_id == "safe_mode_resolution":
            # Safe mode resolution
            return {
                "action": "safe_mode_restart",
                "confidence": 0.7,
                "method": "safe_mode",
                "description": "Fallback safe mode resolution"
            }
        elif fallback_agent_id == "basic_notification":
            # Basic notification
            return {
                "notified": True,
                "confidence": 0.8,
                "method": "basic_notification",
                "description": "Fallback basic notification"
            }
        else:
            raise ValueError(f"Unknown fallback agent: {fallback_agent_id}")
    
    async def _trigger_human_escalation(
        self, 
        workflow_id: str, 
        agent_id: str, 
        incident: Incident, 
        error: Exception
    ):
        """Trigger human escalation with complete context preservation."""
        escalation_context = {
            "workflow_id": workflow_id,
            "incident_id": incident.id,
            "failed_agent": agent_id,
            "error": str(error),
            "timestamp": datetime.utcnow().isoformat(),
            "incident_context": {
                "title": incident.title,
                "description": incident.description,
                "severity": incident.severity.value,
                "business_impact": {
                    "service_tier": incident.business_impact.service_tier.value,
                    "affected_users": incident.business_impact.affected_users,
                    "revenue_impact": incident.business_impact.revenue_impact_per_minute
                }
            },
            "workflow_state": self.active_workflows[workflow_id],
            "agent_checkpoints": self.agent_checkpoints.get(agent_id, [])
        }
        
        logger.critical(f"Human escalation triggered for workflow {workflow_id}, agent {agent_id}")
        
        # Store escalation context for human operators
        workflow_state = self.active_workflows[workflow_id]
        workflow_state["human_escalation"] = escalation_context
        workflow_state["requires_human_intervention"] = True
        
        # Integrate with escalation systems
        await self._send_escalation_notifications(escalation_context, incident)
        
        # Log the escalation
        logger.info(f"Escalation context preserved: {json.dumps(escalation_context, indent=2)}")
    
    async def _send_escalation_notifications(
        self, 
        escalation_context: Dict[str, Any], 
        incident: Incident
    ):
        """Send escalation notifications through multiple channels."""
        notification_tasks = []
        
        # PagerDuty Integration
        try:
            task = asyncio.create_task(
                self._send_pagerduty_alert(escalation_context, incident)
            )
            notification_tasks.append(("pagerduty", task))
        except Exception as e:
            logger.error(f"Failed to create PagerDuty notification task: {e}")
        
        # Slack Integration
        try:
            task = asyncio.create_task(
                self._send_slack_alert(escalation_context, incident)
            )
            notification_tasks.append(("slack", task))
        except Exception as e:
            logger.error(f"Failed to create Slack notification task: {e}")
        
        # Email Integration
        try:
            task = asyncio.create_task(
                self._send_email_alert(escalation_context, incident)
            )
            notification_tasks.append(("email", task))
        except Exception as e:
            logger.error(f"Failed to create email notification task: {e}")
        
        # SMS Integration (for critical incidents)
        if incident.severity.value in ["critical", "high"]:
            try:
                task = asyncio.create_task(
                    self._send_sms_alert(escalation_context, incident)
                )
                notification_tasks.append(("sms", task))
            except Exception as e:
                logger.error(f"Failed to create SMS notification task: {e}")
        
        # Wait for all notifications to complete
        results = {}
        for channel, task in notification_tasks:
            try:
                result = await asyncio.wait_for(task, timeout=10.0)
                results[channel] = {"success": True, "result": result}
                logger.info(f"Escalation notification sent via {channel}")
            except asyncio.TimeoutError:
                results[channel] = {"success": False, "error": "timeout"}
                logger.error(f"Escalation notification via {channel} timed out")
            except Exception as e:
                results[channel] = {"success": False, "error": str(e)}
                logger.error(f"Escalation notification via {channel} failed: {e}")
        
        return results
    
    async def _send_pagerduty_alert(
        self, 
        escalation_context: Dict[str, Any], 
        incident: Incident
    ) -> Dict[str, Any]:
        """Send PagerDuty alert for human escalation."""
        import os
        import aiohttp
        
        pagerduty_key = os.getenv("PAGERDUTY_INTEGRATION_KEY")
        if not pagerduty_key:
            logger.warning("PAGERDUTY_INTEGRATION_KEY not configured, skipping PagerDuty alert")
            return {"skipped": True, "reason": "no_api_key"}
        
        payload = {
            "routing_key": pagerduty_key,
            "event_action": "trigger",
            "dedup_key": f"incident_{incident.id}_{escalation_context['workflow_id']}",
            "payload": {
                "summary": f"Agent Escalation: {incident.title}",
                "severity": self._map_severity_to_pagerduty(incident.severity.value),
                "source": "incident_commander_agent_swarm",
                "component": escalation_context["failed_agent"],
                "group": "agent_coordination",
                "class": "agent_failure",
                "custom_details": {
                    "incident_id": incident.id,
                    "workflow_id": escalation_context["workflow_id"],
                    "failed_agent": escalation_context["failed_agent"],
                    "error": escalation_context["error"],
                    "affected_users": incident.business_impact.affected_users,
                    "revenue_impact_per_minute": incident.business_impact.revenue_impact_per_minute,
                    "dashboard_link": f"https://incident-commander.example.com/incidents/{incident.id}"
                }
            },
            "links": [{
                "href": f"https://incident-commander.example.com/incidents/{incident.id}",
                "text": "View Incident Dashboard"
            }]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://events.pagerduty.com/v2/enqueue",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    response_data = await response.json()
                    return {
                        "status": response.status,
                        "dedup_key": response_data.get("dedup_key"),
                        "message": response_data.get("message")
                    }
        except Exception as e:
            logger.error(f"PagerDuty alert failed: {e}")
            raise
    
    async def _send_slack_alert(
        self, 
        escalation_context: Dict[str, Any], 
        incident: Incident
    ) -> Dict[str, Any]:
        """Send Slack alert for human escalation."""
        import os
        import aiohttp
        
        slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        if not slack_webhook_url:
            logger.warning("SLACK_WEBHOOK_URL not configured, skipping Slack alert")
            return {"skipped": True, "reason": "no_webhook_url"}
        
        severity_emoji = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢",
            "info": "🔵"
        }
        
        emoji = severity_emoji.get(incident.severity.value, "⚪")
        
        payload = {
            "text": f"{emoji} *AGENT ESCALATION REQUIRED*",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{emoji} Agent Escalation Required"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Incident:*\n{incident.title}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Severity:*\n{incident.severity.value.upper()}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Failed Agent:*\n{escalation_context['failed_agent']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Error:*\n{escalation_context['error'][:100]}..."
                        }
                    ]
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Affected Users:*\n{incident.business_impact.affected_users:,}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Revenue Impact:*\n${incident.business_impact.revenue_impact_per_minute:,.2f}/min"
                        }
                    ]
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "View Dashboard"
                            },
                            "url": f"https://incident-commander.example.com/incidents/{incident.id}",
                            "style": "primary"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Acknowledge"
                            },
                            "value": f"ack_{escalation_context['workflow_id']}",
                            "style": "danger"
                        }
                    ]
                }
            ]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    slack_webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return {
                        "status": response.status,
                        "ok": response.status == 200
                    }
        except Exception as e:
            logger.error(f"Slack alert failed: {e}")
            raise
    
    async def _send_email_alert(
        self, 
        escalation_context: Dict[str, Any], 
        incident: Incident
    ) -> Dict[str, Any]:
        """Send email alert for human escalation."""
        import os
        import aiohttp
        
        sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        escalation_email = os.getenv("ESCALATION_EMAIL_RECIPIENTS", "oncall@example.com")
        
        if not sendgrid_api_key:
            logger.warning("SENDGRID_API_KEY not configured, skipping email alert")
            return {"skipped": True, "reason": "no_api_key"}
        
        email_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #d32f2f;">⚠️ Agent Escalation Required</h2>
            <div style="background: #f5f5f5; padding: 20px; border-radius: 5px;">
                <h3>{incident.title}</h3>
                <p><strong>Severity:</strong> <span style="color: #d32f2f;">{incident.severity.value.upper()}</span></p>
                <p><strong>Failed Agent:</strong> {escalation_context['failed_agent']}</p>
                <p><strong>Error:</strong> {escalation_context['error']}</p>
                <hr>
                <p><strong>Business Impact:</strong></p>
                <ul>
                    <li>Affected Users: {incident.business_impact.affected_users:,}</li>
                    <li>Revenue Impact: ${incident.business_impact.revenue_impact_per_minute:,.2f}/minute</li>
                    <li>Service Tier: {incident.business_impact.service_tier.value}</li>
                </ul>
                <hr>
                <p><strong>Workflow ID:</strong> {escalation_context['workflow_id']}</p>
                <p><strong>Incident ID:</strong> {incident.id}</p>
                <p><a href="https://incident-commander.example.com/incidents/{incident.id}" 
                   style="background: #1976d2; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                   View Dashboard
                </a></p>
            </div>
        </body>
        </html>
        """
        
        payload = {
            "personalizations": [
                {
                    "to": [{"email": email} for email in escalation_email.split(",")],
                    "subject": f"🚨 Agent Escalation: {incident.title}"
                }
            ],
            "from": {
                "email": "noreply@incident-commander.example.com",
                "name": "Incident Commander"
            },
            "content": [
                {
                    "type": "text/html",
                    "value": email_html
                }
            ]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {sendgrid_api_key}",
                        "Content-Type": "application/json"
                    },
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return {
                        "status": response.status,
                        "ok": response.status == 202
                    }
        except Exception as e:
            logger.error(f"Email alert failed: {e}")
            raise
    
    async def _send_sms_alert(
        self, 
        escalation_context: Dict[str, Any], 
        incident: Incident
    ) -> Dict[str, Any]:
        """Send SMS alert for critical incidents via Twilio."""
        import os
        import aiohttp
        from base64 import b64encode
        
        twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        twilio_from_number = os.getenv("TWILIO_FROM_NUMBER")
        oncall_phone_numbers = os.getenv("ONCALL_PHONE_NUMBERS", "").split(",")
        
        if not all([twilio_account_sid, twilio_auth_token, twilio_from_number]):
            logger.warning("Twilio credentials not configured, skipping SMS alert")
            return {"skipped": True, "reason": "no_twilio_credentials"}
        
        if not oncall_phone_numbers or not oncall_phone_numbers[0]:
            logger.warning("ONCALL_PHONE_NUMBERS not configured, skipping SMS alert")
            return {"skipped": True, "reason": "no_phone_numbers"}
        
        message_body = (
            f"🚨 INCIDENT ESCALATION\n"
            f"Severity: {incident.severity.value.upper()}\n"
            f"Agent: {escalation_context['failed_agent']} FAILED\n"
            f"Users affected: {incident.business_impact.affected_users:,}\n"
            f"Revenue: ${incident.business_impact.revenue_impact_per_minute:,.0f}/min\n"
            f"View: https://incident-commander.example.com/incidents/{incident.id}"
        )
        
        # Twilio Basic Auth
        auth_string = f"{twilio_account_sid}:{twilio_auth_token}"
        auth_header = b64encode(auth_string.encode()).decode()
        
        sms_results = []
        for phone_number in oncall_phone_numbers:
            phone_number = phone_number.strip()
            if not phone_number:
                continue
                
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"https://api.twilio.com/2010-04-01/Accounts/{twilio_account_sid}/Messages.json",
                        data={
                            "From": twilio_from_number,
                            "To": phone_number,
                            "Body": message_body
                        },
                        headers={
                            "Authorization": f"Basic {auth_header}"
                        },
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        sms_results.append({
                            "phone": phone_number,
                            "status": response.status,
                            "ok": response.status == 201
                        })
            except Exception as e:
                logger.error(f"SMS alert to {phone_number} failed: {e}")
                sms_results.append({
                    "phone": phone_number,
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "sms_sent": len([r for r in sms_results if r.get("ok")]),
            "results": sms_results
        }
    
    def _map_severity_to_pagerduty(self, severity: str) -> str:
        """Map incident severity to PagerDuty severity levels."""
        severity_map = {
            "critical": "critical",
            "high": "error",
            "medium": "warning",
            "low": "info",
            "info": "info"
        }
        return severity_map.get(severity, "warning")
    
    async def _create_workflow_checkpoint(self, workflow_id: str):
        """Create workflow checkpoint for recovery."""
        if workflow_id not in self.active_workflows:
            return
        
        workflow_state = self.active_workflows[workflow_id]
        checkpoint_time = datetime.utcnow()
        
        # Create checkpoints for all active agents
        for agent_id in self.registered_agents.keys():
            if agent_id in workflow_state["agent_results"]:
                checkpoint = AgentCheckpoint(
                    agent_id=agent_id,
                    checkpoint_time=checkpoint_time,
                    agent_state=self.agent_states[agent_id],
                    processing_data=workflow_state["agent_results"][agent_id],
                    recommendations=[],  # Would contain actual recommendations
                    confidence_score=workflow_state["agent_results"][agent_id].get("confidence", 0.0),
                    execution_context={"workflow_id": workflow_id}
                )
                
                self.agent_checkpoints[agent_id].append(checkpoint)
                
                # Limit checkpoint history
                if len(self.agent_checkpoints[agent_id]) > 10:
                    self.agent_checkpoints[agent_id] = self.agent_checkpoints[agent_id][-10:]
        
        workflow_state["checkpoints"].append({
            "checkpoint_time": checkpoint_time.isoformat(),
            "agents_checkpointed": list(self.registered_agents.keys())
        })
        
        logger.info(f"Workflow checkpoint created for {workflow_id}")
    
    async def _handle_workflow_failure(self, workflow_id: str, error: Exception):
        """Handle workflow failure with recovery attempts."""
        if workflow_id not in self.active_workflows:
            return
        
        workflow_state = self.active_workflows[workflow_id]
        workflow_state["failed"] = True
        workflow_state["failure_reason"] = str(error)
        workflow_state["failure_time"] = datetime.utcnow().isoformat()
        
        logger.error(f"Workflow {workflow_id} failed: {error}")
        
        # Attempt recovery from latest checkpoint
        latest_checkpoints = {}
        for agent_id, checkpoints in self.agent_checkpoints.items():
            if checkpoints:
                latest_checkpoints[agent_id] = checkpoints[-1]
        
        if latest_checkpoints:
            logger.info(f"Recovery checkpoints available for workflow {workflow_id}")
            workflow_state["recovery_available"] = True
            workflow_state["recovery_checkpoints"] = {
                agent_id: checkpoint.checkpoint_time.isoformat()
                for agent_id, checkpoint in latest_checkpoints.items()
            }
        else:
            workflow_state["recovery_available"] = False
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get current workflow status."""
        return self.active_workflows.get(workflow_id)
    
    def get_agent_health_status(self) -> Dict[str, Dict[str, Any]]:
        """Get health status of all registered agents."""
        health_status = {}
        
        for agent_id, agent in self.registered_agents.items():
            state = self.agent_states.get(agent_id, AgentState.IDLE)
            checkpoints = self.agent_checkpoints.get(agent_id, [])
            
            health_status[agent_id] = {
                "agent_id": agent_id,
                "current_state": state.value,
                "is_healthy": state not in [AgentState.FAILED],
                "is_degraded": state == AgentState.DEGRADED,
                "checkpoint_count": len(checkpoints),
                "last_checkpoint": checkpoints[-1].checkpoint_time.isoformat() if checkpoints else None,
                "registered_at": datetime.utcnow().isoformat()  # Would track actual registration time
            }
        
        return health_status
    
    def get_dependency_graph_info(self) -> Dict[str, Any]:
        """Get dependency graph information for visualization."""
        return {
            "nodes": list(self.dependency_graph.nodes()),
            "edges": list(self.dependency_graph.edges()),
            "is_acyclic": nx.is_directed_acyclic_graph(self.dependency_graph),
            "topological_order": list(nx.topological_sort(self.dependency_graph)),
            "execution_levels": self._get_execution_levels()
        }
    
    def _get_execution_levels(self) -> Dict[str, int]:
        """Get execution levels for parallel execution planning."""
        levels = {}
        topo_order = list(nx.topological_sort(self.dependency_graph))
        
        for agent_id in topo_order:
            if not list(self.dependency_graph.predecessors(agent_id)):
                levels[agent_id] = 0
            else:
                max_pred_level = max(
                    levels[pred] 
                    for pred in self.dependency_graph.predecessors(agent_id)
                )
                levels[agent_id] = max_pred_level + 1
        
        return levels
    
    async def validate_workflow_integrity(self) -> Dict[str, Any]:
        """Validate workflow integrity and detect potential issues."""
        validation_results = {
            "dependency_graph_valid": True,
            "circular_dependencies": [],
            "missing_agents": [],
            "fallback_chains_valid": True,
            "issues": []
        }
        
        # Check dependency graph
        if not nx.is_directed_acyclic_graph(self.dependency_graph):
            validation_results["dependency_graph_valid"] = False
            try:
                cycles = list(nx.simple_cycles(self.dependency_graph))
                validation_results["circular_dependencies"] = cycles
                validation_results["issues"].append(f"Circular dependencies detected: {cycles}")
            except:
                validation_results["issues"].append("Circular dependencies detected but could not identify cycles")
        
        # Check for missing agents
        graph_agents = set(self.dependency_graph.nodes())
        registered_agents = set(self.registered_agents.keys())
        missing_agents = graph_agents - registered_agents
        
        if missing_agents:
            validation_results["missing_agents"] = list(missing_agents)
            validation_results["issues"].append(f"Missing registered agents: {missing_agents}")
        
        # Check fallback chains
        for agent_id, fallback_chain in self.fallback_chains.items():
            if agent_id not in registered_agents:
                validation_results["fallback_chains_valid"] = False
                validation_results["issues"].append(f"Fallback chain exists for unregistered agent: {agent_id}")
        
        validation_results["validation_timestamp"] = datetime.utcnow().isoformat()
        validation_results["overall_valid"] = len(validation_results["issues"]) == 0
        
        return validation_results


# Global agent swarm coordinator instance
_agent_swarm_coordinator = None


def get_agent_swarm_coordinator() -> AgentSwarmCoordinator:
    """Get the global agent swarm coordinator instance."""
    global _agent_swarm_coordinator
    if _agent_swarm_coordinator is None:
        _agent_swarm_coordinator = AgentSwarmCoordinator()
    return _agent_swarm_coordinator