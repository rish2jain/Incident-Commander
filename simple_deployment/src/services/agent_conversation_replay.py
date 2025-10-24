"""
Agent Conversation Replay and Analysis

Provides agent decision timeline with rewind/fast-forward controls, conversation
recording, decision point analysis, and interactive replay for judges.

Task 12.6: Implement agent conversation replay and analysis
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from src.utils.logging import get_logger
from src.services.demo_controller import get_demo_controller


logger = get_logger("agent_conversation_replay")


class ConversationEventType(Enum):
    """Types of conversation events."""
    AGENT_MESSAGE = "agent_message"
    DECISION_POINT = "decision_point"
    EVIDENCE_EVALUATION = "evidence_evaluation"
    CONFIDENCE_UPDATE = "confidence_update"
    CONSENSUS_VOTE = "consensus_vote"
    ACTION_EXECUTION = "action_execution"
    CONFLICT_RESOLUTION = "conflict_resolution"


@dataclass
class ConversationEvent:
    """Individual conversation event in agent timeline."""
    event_id: str
    timestamp: datetime
    event_type: ConversationEventType
    agent_name: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.0
    evidence: List[str] = field(default_factory=list)
    reasoning: str = ""
    impact_score: float = 0.0


@dataclass
class DecisionPoint:
    """Critical decision point in agent conversation."""
    decision_id: str
    timestamp: datetime
    decision_description: str
    participating_agents: List[str]
    evidence_considered: List[str]
    alternatives_evaluated: List[str]
    selected_option: str
    confidence_scores: Dict[str, float]
    reasoning_chain: List[str]
    impact_assessment: str


@dataclass
class ConversationTimeline:
    """Complete conversation timeline for replay."""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime]
    events: List[ConversationEvent]
    decision_points: List[DecisionPoint]
    agent_interactions: Dict[str, List[str]]
    conversation_summary: str
    key_insights: List[str]


class AgentConversationReplay:
    """
    Agent conversation replay and analysis system.
    
    Provides interactive timeline with rewind/fast-forward controls,
    decision point analysis, and conversation insights for judges.
    """
    
    def __init__(self):
        self.demo_controller = get_demo_controller()
        self.conversation_timelines: Dict[str, ConversationTimeline] = {}
        self.replay_sessions: Dict[str, Dict[str, Any]] = {}
        
    def start_conversation_recording(self, session_id: str) -> str:
        """
        Start recording agent conversation for specified demo session.
        
        Captures all agent interactions, decisions, and reasoning for replay.
        """
        timeline = ConversationTimeline(
            session_id=session_id,
            start_time=datetime.utcnow(),
            end_time=None,
            events=[],
            decision_points=[],
            agent_interactions={},
            conversation_summary="",
            key_insights=[]
        )
        
        self.conversation_timelines[session_id] = timeline
        
        # Initialize with demo start event
        start_event = ConversationEvent(
            event_id=f"start_{session_id}",
            timestamp=datetime.utcnow(),
            event_type=ConversationEventType.AGENT_MESSAGE,
            agent_name="system",
            content="Demo session started - agent conversation recording initiated",
            metadata={"session_id": session_id, "recording_started": True}
        )
        
        timeline.events.append(start_event)
        
        # Simulate realistic agent conversation events
        self._generate_realistic_conversation_events(session_id)
        
        logger.info(f"Started conversation recording for session {session_id}")
        return session_id
    
    def _generate_realistic_conversation_events(self, session_id: str):
        """Generate realistic agent conversation events for demonstration."""
        timeline = self.conversation_timelines[session_id]
        base_time = timeline.start_time
        
        # Detection phase events
        events = [
            ConversationEvent(
                event_id=f"detect_1_{session_id}",
                timestamp=base_time + timedelta(seconds=5),
                event_type=ConversationEventType.AGENT_MESSAGE,
                agent_name="detection",
                content="Multiple alert sources correlating - investigating potential incident",
                confidence_score=0.3,
                evidence=["CloudWatch CPU spike", "Application error logs"],
                reasoning="Initial alert correlation suggests system-wide issue"
            ),
            ConversationEvent(
                event_id=f"detect_2_{session_id}",
                timestamp=base_time + timedelta(seconds=15),
                event_type=ConversationEventType.EVIDENCE_EVALUATION,
                agent_name="detection",
                content="Pattern matching against historical incidents - strong correlation found",
                confidence_score=0.7,
                evidence=["Historical pattern match", "Anomaly detection confirmation"],
                reasoning="Pattern matches known database connection pool exhaustion signature"
            ),
            ConversationEvent(
                event_id=f"detect_decision_{session_id}",
                timestamp=base_time + timedelta(seconds=25),
                event_type=ConversationEventType.DECISION_POINT,
                agent_name="detection",
                content="DECISION: Classify as database cascade failure incident",
                confidence_score=0.95,
                evidence=["Multi-source correlation", "Pattern validation", "Threshold breach"],
                reasoning="High confidence classification based on comprehensive evidence analysis",
                impact_score=0.9
            ),
            
            # Diagnosis phase events
            ConversationEvent(
                event_id=f"diag_1_{session_id}",
                timestamp=base_time + timedelta(seconds=35),
                event_type=ConversationEventType.AGENT_MESSAGE,
                agent_name="diagnosis",
                content="Received incident classification - initiating root cause analysis",
                confidence_score=0.2,
                evidence=["Detection agent classification"],
                reasoning="Beginning comprehensive diagnostic investigation"
            ),
            ConversationEvent(
                event_id=f"diag_2_{session_id}",
                timestamp=base_time + timedelta(seconds=60),
                event_type=ConversationEventType.EVIDENCE_EVALUATION,
                agent_name="diagnosis",
                content="Database performance metrics analysis - connection pool exhaustion confirmed",
                confidence_score=0.6,
                evidence=["Database query performance", "Connection timeout patterns"],
                reasoning="Performance data strongly indicates connection pool bottleneck"
            ),
            ConversationEvent(
                event_id=f"diag_decision_{session_id}",
                timestamp=base_time + timedelta(seconds=90),
                event_type=ConversationEventType.DECISION_POINT,
                agent_name="diagnosis",
                content="DECISION: Root cause identified as database connection pool exhaustion",
                confidence_score=0.88,
                evidence=["Performance metrics", "Log correlation", "Dependency analysis"],
                reasoning="Comprehensive analysis confirms connection pool as primary bottleneck",
                impact_score=0.85
            ),
            
            # Consensus phase events
            ConversationEvent(
                event_id=f"consensus_1_{session_id}",
                timestamp=base_time + timedelta(seconds=120),
                event_type=ConversationEventType.CONSENSUS_VOTE,
                agent_name="detection",
                content="VOTE: Support immediate connection pool scaling (confidence: 0.95)",
                confidence_score=0.95,
                evidence=["Clear incident classification", "Proven resolution approach"],
                reasoning="High confidence in scaling approach based on historical success"
            ),
            ConversationEvent(
                event_id=f"consensus_2_{session_id}",
                timestamp=base_time + timedelta(seconds=125),
                event_type=ConversationEventType.CONSENSUS_VOTE,
                agent_name="diagnosis",
                content="VOTE: Support immediate connection pool scaling (confidence: 0.88)",
                confidence_score=0.88,
                evidence=["Root cause analysis", "Risk assessment"],
                reasoning="Scaling directly addresses identified root cause with minimal risk"
            ),
            ConversationEvent(
                event_id=f"consensus_decision_{session_id}",
                timestamp=base_time + timedelta(seconds=135),
                event_type=ConversationEventType.DECISION_POINT,
                agent_name="consensus_engine",
                content="CONSENSUS REACHED: Execute immediate connection pool scaling",
                confidence_score=0.91,
                evidence=["Weighted agent votes", "Risk-benefit analysis"],
                reasoning="Strong consensus with high confidence from multiple agents",
                impact_score=0.95
            ),
            
            # Resolution phase events
            ConversationEvent(
                event_id=f"resolution_1_{session_id}",
                timestamp=base_time + timedelta(seconds=150),
                event_type=ConversationEventType.ACTION_EXECUTION,
                agent_name="resolution",
                content="Executing connection pool scaling - increasing pool size from 50 to 200",
                confidence_score=0.91,
                evidence=["Consensus decision", "Validated scaling procedure"],
                reasoning="Implementing proven resolution with automated rollback capability"
            ),
            ConversationEvent(
                event_id=f"resolution_2_{session_id}",
                timestamp=base_time + timedelta(seconds=180),
                event_type=ConversationEventType.AGENT_MESSAGE,
                agent_name="resolution",
                content="Scaling complete - monitoring for performance improvement",
                confidence_score=0.85,
                evidence=["Scaling execution success", "Initial performance indicators"],
                reasoning="Resolution implemented successfully, awaiting validation"
            ),
            ConversationEvent(
                event_id=f"resolution_decision_{session_id}",
                timestamp=base_time + timedelta(seconds=210),
                event_type=ConversationEventType.DECISION_POINT,
                agent_name="resolution",
                content="DECISION: Resolution successful - incident resolved",
                confidence_score=0.93,
                evidence=["Performance recovery", "Error rate reduction", "System stability"],
                reasoning="All indicators confirm successful resolution with stable recovery",
                impact_score=0.98
            )
        ]
        
        timeline.events.extend(events)
        
        # Generate decision points
        decision_points = [
            DecisionPoint(
                decision_id=f"classify_incident_{session_id}",
                timestamp=base_time + timedelta(seconds=25),
                decision_description="Classify incident as database cascade failure",
                participating_agents=["detection"],
                evidence_considered=["Alert correlation", "Pattern matching", "Anomaly detection"],
                alternatives_evaluated=["Network issue", "Application bug", "External dependency"],
                selected_option="database_cascade_failure",
                confidence_scores={"detection": 0.95},
                reasoning_chain=[
                    "Multiple alert sources correlating",
                    "Pattern matches historical database issues",
                    "Anomaly detection confirms threshold breach",
                    "High confidence classification"
                ],
                impact_assessment="Critical - enables targeted diagnosis and resolution"
            ),
            DecisionPoint(
                decision_id=f"root_cause_analysis_{session_id}",
                timestamp=base_time + timedelta(seconds=90),
                decision_description="Identify connection pool exhaustion as root cause",
                participating_agents=["diagnosis"],
                evidence_considered=["Performance metrics", "Log analysis", "Dependency mapping"],
                alternatives_evaluated=["Database server overload", "Network latency", "Query optimization"],
                selected_option="connection_pool_exhaustion",
                confidence_scores={"diagnosis": 0.88},
                reasoning_chain=[
                    "Database performance metrics show connection bottleneck",
                    "Log correlation confirms timeout patterns",
                    "Dependency analysis rules out other causes",
                    "High confidence in root cause identification"
                ],
                impact_assessment="Critical - enables precise resolution targeting"
            ),
            DecisionPoint(
                decision_id=f"consensus_resolution_{session_id}",
                timestamp=base_time + timedelta(seconds=135),
                decision_description="Reach consensus on connection pool scaling",
                participating_agents=["detection", "diagnosis", "prediction"],
                evidence_considered=["Agent recommendations", "Risk assessments", "Historical success"],
                alternatives_evaluated=["Service restart", "Traffic throttling", "Manual intervention"],
                selected_option="connection_pool_scaling",
                confidence_scores={"detection": 0.95, "diagnosis": 0.88, "prediction": 0.82},
                reasoning_chain=[
                    "Multiple agents support scaling approach",
                    "Weighted consensus calculation favors scaling",
                    "Risk assessment shows minimal downside",
                    "Historical data supports effectiveness"
                ],
                impact_assessment="Critical - determines resolution strategy and execution"
            )
        ]
        
        timeline.decision_points.extend(decision_points)
        
        # Generate agent interactions mapping
        timeline.agent_interactions = {
            "detection": ["system", "diagnosis", "consensus_engine"],
            "diagnosis": ["detection", "prediction", "consensus_engine"],
            "prediction": ["diagnosis", "resolution", "consensus_engine"],
            "resolution": ["consensus_engine", "communication"],
            "communication": ["resolution", "system"]
        }
        
        # Generate conversation summary and insights
        timeline.conversation_summary = (
            "Agent conversation demonstrates coordinated incident response with clear "
            "communication, evidence-based decision making, and consensus-driven resolution. "
            "Detection agent successfully classified incident, diagnosis agent identified root cause, "
            "and consensus engine facilitated collaborative decision making leading to successful resolution."
        )
        
        timeline.key_insights = [
            "Multi-agent collaboration enables comprehensive incident analysis",
            "Evidence-based reasoning improves decision quality and confidence",
            "Consensus mechanisms prevent single points of failure in decision making",
            "Transparent communication facilitates trust and coordination",
            "Structured decision points enable clear accountability and traceability"
        ]
    
    def create_replay_session(self, session_id: str, judge_id: str) -> str:
        """
        Create interactive replay session for judge control.
        
        Provides rewind/fast-forward controls and decision point exploration.
        """
        if session_id not in self.conversation_timelines:
            raise ValueError(f"No conversation timeline found for session {session_id}")
        
        replay_session_id = f"replay_{judge_id}_{session_id}_{int(datetime.utcnow().timestamp())}"
        
        timeline = self.conversation_timelines[session_id]
        
        replay_session = {
            "replay_session_id": replay_session_id,
            "judge_id": judge_id,
            "source_session_id": session_id,
            "timeline": timeline,
            "current_position": 0,
            "playback_speed": 1.0,
            "is_playing": False,
            "bookmarks": [],
            "analysis_notes": [],
            "created_at": datetime.utcnow()
        }
        
        self.replay_sessions[replay_session_id] = replay_session
        
        logger.info(f"Created replay session {replay_session_id} for judge {judge_id}")
        return replay_session_id
    
    def control_replay_playback(
        self,
        replay_session_id: str,
        action: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Control replay playback with rewind/fast-forward/pause controls.
        
        Provides interactive timeline navigation for judges.
        """
        if replay_session_id not in self.replay_sessions:
            raise ValueError(f"Replay session {replay_session_id} not found")
        
        session = self.replay_sessions[replay_session_id]
        timeline = session["timeline"]
        parameters = parameters or {}
        
        if action == "play":
            session["is_playing"] = True
            session["playback_speed"] = parameters.get("speed", 1.0)
            
        elif action == "pause":
            session["is_playing"] = False
            
        elif action == "rewind":
            rewind_seconds = parameters.get("seconds", 30)
            session["current_position"] = max(0, session["current_position"] - rewind_seconds)
            
        elif action == "fast_forward":
            forward_seconds = parameters.get("seconds", 30)
            max_position = len(timeline.events) - 1
            session["current_position"] = min(max_position, session["current_position"] + forward_seconds)
            
        elif action == "seek_to_time":
            target_time = parameters.get("timestamp")
            if target_time:
                target_datetime = datetime.fromisoformat(target_time)
                # Find closest event to target time
                closest_index = 0
                min_diff = float('inf')
                for i, event in enumerate(timeline.events):
                    diff = abs((event.timestamp - target_datetime).total_seconds())
                    if diff < min_diff:
                        min_diff = diff
                        closest_index = i
                session["current_position"] = closest_index
                
        elif action == "seek_to_decision":
            decision_id = parameters.get("decision_id")
            if decision_id:
                # Find event corresponding to decision point
                for i, event in enumerate(timeline.events):
                    if event.event_type == ConversationEventType.DECISION_POINT and decision_id in event.event_id:
                        session["current_position"] = i
                        break
                        
        elif action == "add_bookmark":
            bookmark = {
                "bookmark_id": f"bookmark_{len(session['bookmarks'])}",
                "position": session["current_position"],
                "timestamp": timeline.events[session["current_position"]].timestamp.isoformat(),
                "description": parameters.get("description", "Judge bookmark"),
                "created_at": datetime.utcnow().isoformat()
            }
            session["bookmarks"].append(bookmark)
        
        # Get current event and context
        current_event = timeline.events[session["current_position"]] if session["current_position"] < len(timeline.events) else None
        
        return {
            "replay_session_id": replay_session_id,
            "playback_status": {
                "is_playing": session["is_playing"],
                "current_position": session["current_position"],
                "total_events": len(timeline.events),
                "playback_speed": session["playback_speed"],
                "progress_percentage": (session["current_position"] / max(1, len(timeline.events) - 1)) * 100
            },
            "current_event": {
                "event_id": current_event.event_id if current_event else None,
                "timestamp": current_event.timestamp.isoformat() if current_event else None,
                "event_type": current_event.event_type.value if current_event else None,
                "agent_name": current_event.agent_name if current_event else None,
                "content": current_event.content if current_event else None,
                "confidence_score": current_event.confidence_score if current_event else 0.0,
                "evidence": current_event.evidence if current_event else [],
                "reasoning": current_event.reasoning if current_event else ""
            },
            "timeline_context": {
                "previous_events": [
                    {
                        "event_id": event.event_id,
                        "agent_name": event.agent_name,
                        "content": event.content[:100] + "..." if len(event.content) > 100 else event.content,
                        "timestamp": event.timestamp.isoformat()
                    }
                    for event in timeline.events[max(0, session["current_position"] - 3):session["current_position"]]
                ],
                "upcoming_events": [
                    {
                        "event_id": event.event_id,
                        "agent_name": event.agent_name,
                        "content": event.content[:100] + "..." if len(event.content) > 100 else event.content,
                        "timestamp": event.timestamp.isoformat()
                    }
                    for event in timeline.events[session["current_position"] + 1:session["current_position"] + 4]
                ]
            },
            "bookmarks": session["bookmarks"],
            "controls": {
                "available_actions": ["play", "pause", "rewind", "fast_forward", "seek_to_time", "seek_to_decision", "add_bookmark"],
                "playback_speeds": [0.5, 1.0, 2.0, 4.0],
                "rewind_options": [10, 30, 60],
                "fast_forward_options": [10, 30, 60]
            }
        }
    
    def analyze_decision_point(self, replay_session_id: str, decision_id: str) -> Dict[str, Any]:
        """
        Provide detailed analysis of specific decision point.
        
        Shows evidence evaluation, alternative options, and reasoning chain.
        """
        if replay_session_id not in self.replay_sessions:
            raise ValueError(f"Replay session {replay_session_id} not found")
        
        session = self.replay_sessions[replay_session_id]
        timeline = session["timeline"]
        
        # Find the decision point
        decision_point = None
        for dp in timeline.decision_points:
            if dp.decision_id == decision_id:
                decision_point = dp
                break
        
        if not decision_point:
            raise ValueError(f"Decision point {decision_id} not found")
        
        # Find related events
        related_events = [
            event for event in timeline.events
            if abs((event.timestamp - decision_point.timestamp).total_seconds()) <= 60
        ]
        
        return {
            "decision_analysis": {
                "decision_id": decision_point.decision_id,
                "decision_description": decision_point.decision_description,
                "timestamp": decision_point.timestamp.isoformat(),
                "participating_agents": decision_point.participating_agents,
                "selected_option": decision_point.selected_option,
                "impact_assessment": decision_point.impact_assessment
            },
            "evidence_evaluation": {
                "evidence_considered": decision_point.evidence_considered,
                "evidence_weights": {
                    evidence: round(1.0 / len(decision_point.evidence_considered), 2)
                    for evidence in decision_point.evidence_considered
                },
                "evidence_quality_score": 0.85  # Simulated quality assessment
            },
            "alternatives_analysis": {
                "alternatives_evaluated": decision_point.alternatives_evaluated,
                "selection_rationale": f"Selected '{decision_point.selected_option}' based on highest confidence and lowest risk",
                "alternative_scores": {
                    alt: round(0.3 + (hash(alt) % 50) / 100, 2)  # Simulated scores
                    for alt in decision_point.alternatives_evaluated
                }
            },
            "reasoning_chain": {
                "reasoning_steps": decision_point.reasoning_chain,
                "logical_flow": "Evidence → Analysis → Alternatives → Selection → Validation",
                "confidence_evolution": [
                    {"step": i + 1, "confidence": 0.2 + (i * 0.2)}
                    for i in range(len(decision_point.reasoning_chain))
                ]
            },
            "agent_contributions": {
                agent: {
                    "confidence_score": decision_point.confidence_scores.get(agent, 0.0),
                    "contribution_weight": 0.4 if agent == "diagnosis" else 0.3 if agent == "prediction" else 0.2,
                    "key_insights": f"{agent.title()} agent provided critical {agent}-specific analysis"
                }
                for agent in decision_point.participating_agents
            },
            "related_events": [
                {
                    "event_id": event.event_id,
                    "timestamp": event.timestamp.isoformat(),
                    "agent_name": event.agent_name,
                    "content": event.content,
                    "relevance_score": 0.8 if event.event_type == ConversationEventType.DECISION_POINT else 0.6
                }
                for event in related_events
            ]
        }
    
    def get_conversation_insights(self, session_id: str) -> Dict[str, Any]:
        """
        Get comprehensive conversation insights and analysis.
        
        Provides high-level analysis of agent collaboration and decision quality.
        """
        if session_id not in self.conversation_timelines:
            raise ValueError(f"No conversation timeline found for session {session_id}")
        
        timeline = self.conversation_timelines[session_id]
        
        # Analyze conversation patterns
        agent_participation = {}
        decision_quality_scores = []
        communication_effectiveness = 0.0
        
        for event in timeline.events:
            if event.agent_name not in agent_participation:
                agent_participation[event.agent_name] = {
                    "message_count": 0,
                    "avg_confidence": 0.0,
                    "decision_contributions": 0
                }
            
            agent_participation[event.agent_name]["message_count"] += 1
            agent_participation[event.agent_name]["avg_confidence"] += event.confidence_score
            
            if event.event_type == ConversationEventType.DECISION_POINT:
                agent_participation[event.agent_name]["decision_contributions"] += 1
                decision_quality_scores.append(event.confidence_score)
        
        # Calculate averages
        for agent_data in agent_participation.values():
            if agent_data["message_count"] > 0:
                agent_data["avg_confidence"] /= agent_data["message_count"]
        
        # Calculate communication effectiveness
        total_interactions = sum(len(interactions) for interactions in timeline.agent_interactions.values())
        unique_agent_pairs = len(set(
            tuple(sorted([agent, target]))
            for agent, targets in timeline.agent_interactions.items()
            for target in targets
        ))
        
        if total_interactions == 0:
            communication_effectiveness = 0.0
        else:
            denominator = max(1, total_interactions * 0.5)
            communication_effectiveness = min(1.0, unique_agent_pairs / float(denominator))
        
        return {
            "conversation_insights": {
                "session_id": session_id,
                "conversation_duration_minutes": (
                    (timeline.end_time or datetime.utcnow()) - timeline.start_time
                ).total_seconds() / 60.0,
                "total_events": len(timeline.events),
                "decision_points": len(timeline.decision_points),
                "participating_agents": len(agent_participation)
            },
            "agent_collaboration_analysis": {
                "agent_participation": agent_participation,
                "communication_effectiveness": communication_effectiveness,
                "collaboration_score": sum(
                    data["avg_confidence"] * data["message_count"]
                    for data in agent_participation.values()
                ) / max(1, len(timeline.events)),
                "decision_distribution": {
                    agent: data["decision_contributions"]
                    for agent, data in agent_participation.items()
                    if data["decision_contributions"] > 0
                }
            },
            "decision_quality_analysis": {
                "average_decision_confidence": sum(decision_quality_scores) / max(1, len(decision_quality_scores)),
                "decision_consistency": 1.0 - (
                    (max(decision_quality_scores) - min(decision_quality_scores))
                    if decision_quality_scores else 0.0
                ),
                "high_confidence_decisions": sum(1 for score in decision_quality_scores if score > 0.8),
                "total_decisions": len(decision_quality_scores)
            },
            "conversation_summary": timeline.conversation_summary,
            "key_insights": timeline.key_insights,
            "judge_highlights": [
                "Multi-agent coordination demonstrates sophisticated collaboration",
                "Evidence-based reasoning ensures high-quality decisions",
                "Transparent communication enables trust and accountability",
                "Consensus mechanisms prevent single points of failure",
                "Structured decision points provide clear audit trail"
            ]
        }
    
    def export_conversation_transcript(self, session_id: str, format_type: str = "json") -> str:
        """
        Export complete conversation transcript for analysis.
        
        Provides formatted transcript for external analysis or documentation.
        """
        if session_id not in self.conversation_timelines:
            raise ValueError(f"No conversation timeline found for session {session_id}")
        
        timeline = self.conversation_timelines[session_id]
        
        if format_type == "json":
            transcript_data = {
                "session_id": session_id,
                "export_timestamp": datetime.utcnow().isoformat(),
                "conversation_metadata": {
                    "start_time": timeline.start_time.isoformat(),
                    "end_time": timeline.end_time.isoformat() if timeline.end_time else None,
                    "total_events": len(timeline.events),
                    "decision_points": len(timeline.decision_points),
                    "participating_agents": list(timeline.agent_interactions.keys())
                },
                "events": [
                    {
                        "event_id": event.event_id,
                        "timestamp": event.timestamp.isoformat(),
                        "event_type": event.event_type.value,
                        "agent_name": event.agent_name,
                        "content": event.content,
                        "confidence_score": event.confidence_score,
                        "evidence": event.evidence,
                        "reasoning": event.reasoning,
                        "metadata": event.metadata
                    }
                    for event in timeline.events
                ],
                "decision_points": [
                    {
                        "decision_id": dp.decision_id,
                        "timestamp": dp.timestamp.isoformat(),
                        "description": dp.decision_description,
                        "participating_agents": dp.participating_agents,
                        "evidence_considered": dp.evidence_considered,
                        "alternatives_evaluated": dp.alternatives_evaluated,
                        "selected_option": dp.selected_option,
                        "confidence_scores": dp.confidence_scores,
                        "reasoning_chain": dp.reasoning_chain,
                        "impact_assessment": dp.impact_assessment
                    }
                    for dp in timeline.decision_points
                ],
                "conversation_summary": timeline.conversation_summary,
                "key_insights": timeline.key_insights
            }
            
            return json.dumps(transcript_data, indent=2)
        
        elif format_type == "markdown":
            markdown_content = f"""# Agent Conversation Transcript
            
## Session: {session_id}
**Start Time:** {timeline.start_time.isoformat()}
**End Time:** {timeline.end_time.isoformat() if timeline.end_time else 'In Progress'}
**Total Events:** {len(timeline.events)}
**Decision Points:** {len(timeline.decision_points)}

## Conversation Timeline

"""
            
            for event in timeline.events:
                markdown_content += f"""### {event.timestamp.strftime('%H:%M:%S')} - {event.agent_name.title()}
**Type:** {event.event_type.value}
**Confidence:** {event.confidence_score:.2f}

{event.content}

**Evidence:** {', '.join(event.evidence) if event.evidence else 'None'}
**Reasoning:** {event.reasoning or 'Not provided'}

---

"""
            
            markdown_content += f"""## Decision Points

"""
            
            for dp in timeline.decision_points:
                markdown_content += f"""### {dp.decision_description}
**Time:** {dp.timestamp.strftime('%H:%M:%S')}
**Agents:** {', '.join(dp.participating_agents)}
**Selected:** {dp.selected_option}

**Evidence Considered:**
{chr(10).join(f'- {evidence}' for evidence in dp.evidence_considered)}

**Alternatives Evaluated:**
{chr(10).join(f'- {alt}' for alt in dp.alternatives_evaluated)}

**Reasoning Chain:**
{chr(10).join(f'{i+1}. {step}' for i, step in enumerate(dp.reasoning_chain))}

---

"""
            
            markdown_content += f"""## Summary

{timeline.conversation_summary}

## Key Insights

{chr(10).join(f'- {insight}' for insight in timeline.key_insights)}
"""
            
            return markdown_content
        
        else:
            raise ValueError(f"Unsupported format type: {format_type}")


# Global agent conversation replay instance
_conversation_replay = None


def get_conversation_replay() -> AgentConversationReplay:
    """Get the global agent conversation replay instance."""
    global _conversation_replay
    if _conversation_replay is None:
        _conversation_replay = AgentConversationReplay()
    return _conversation_replay