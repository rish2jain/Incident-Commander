"""
Base agent interface and abstract classes.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.models.incident import Incident
from src.models.agent import AgentRecommendation, AgentMessage, AgentType, AgentStatus


class BaseAgent(ABC):
    """Abstract base class for all agents with common functionality."""
    
    def __init__(self, agent_type: AgentType, name: str):
        """Initialize base agent."""
        self.agent_type = agent_type
        self.name = name
        self.is_healthy = True
        self.last_heartbeat = datetime.utcnow()
        self.processing_count = 0
        self.error_count = 0
        self.metadata = {}
        self.status = AgentStatus.HEALTHY
        self.last_activity = datetime.utcnow()
    
    def _update_status_success(self, **kwargs):
        """Update status after successful operation."""
        self.status = AgentStatus.HEALTHY
        self.last_activity = datetime.utcnow()
        self.processing_count += 1
        self.metadata.update(kwargs)
    
    def _update_status_error(self, error: str, **kwargs):
        """Update status after error."""
        self.status = AgentStatus.ERROR
        self.last_activity = datetime.utcnow()
        self.error_count += 1
        self.metadata.update({"last_error": error, **kwargs})
        
        # Mark as unhealthy if too many errors
        if self.error_count > 10:
            self.is_healthy = False
    
    @abstractmethod
    async def process_incident(self, incident: Incident) -> List[AgentRecommendation]:
        """
        Process an incident and return recommendations.
        
        Args:
            incident: The incident to process
            
        Returns:
            List of recommendations from this agent
        """
        pass
    
    @abstractmethod
    async def handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """
        Handle a message from another agent.
        
        Args:
            message: Message from another agent
            
        Returns:
            Optional response message
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Perform health check for this agent.
        
        Returns:
            True if agent is healthy, False otherwise
        """
        pass
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            "agent_type": self.agent_type.value,
            "name": self.name,
            "is_healthy": self.is_healthy,
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "processing_count": self.processing_count,
            "error_count": self.error_count
        }
    
    def update_heartbeat(self) -> None:
        """Update agent heartbeat timestamp."""
        self.last_heartbeat = datetime.utcnow()
    
    def increment_processing_count(self) -> None:
        """Increment processing counter."""
        self.processing_count += 1
    
    def increment_error_count(self) -> None:
        """Increment error counter."""
        self.error_count += 1
        if self.error_count > 10:  # Threshold for unhealthy
            self.is_healthy = False


class DetectionAgent(BaseAgent):
    """Abstract detection agent interface."""
    
    def __init__(self, name: str = "detection"):
        """Initialize detection agent."""
        super().__init__(AgentType.DETECTION, name)
    
    @abstractmethod
    async def analyze_alerts(self, alerts: List[Dict[str, Any]]) -> List[Incident]:
        """
        Analyze incoming alerts and detect incidents.
        
        Args:
            alerts: List of alert data
            
        Returns:
            List of detected incidents
        """
        pass
    
    @abstractmethod
    async def correlate_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Correlate related events and alerts.
        
        Args:
            events: List of events to correlate
            
        Returns:
            List of correlated event groups
        """
        pass


class DiagnosisAgent(BaseAgent):
    """Abstract diagnosis agent interface."""
    
    def __init__(self, name: str = "diagnosis"):
        """Initialize diagnosis agent."""
        super().__init__(AgentType.DIAGNOSIS, name)
    
    @abstractmethod
    async def analyze_logs(self, log_sources: List[str], 
                          time_range: tuple) -> Dict[str, Any]:
        """
        Analyze logs for diagnostic information.
        
        Args:
            log_sources: List of log sources to analyze
            time_range: (start_time, end_time) tuple
            
        Returns:
            Analysis results
        """
        pass
    
    @abstractmethod
    async def trace_root_cause(self, incident: Incident) -> Dict[str, Any]:
        """
        Trace root cause of incident.
        
        Args:
            incident: Incident to analyze
            
        Returns:
            Root cause analysis results
        """
        pass


class PredictionAgent(BaseAgent):
    """Abstract prediction agent interface."""
    
    def __init__(self, name: str = "prediction"):
        """Initialize prediction agent."""
        super().__init__(AgentType.PREDICTION, name)
    
    @abstractmethod
    async def forecast_trends(self, metrics: List[Dict[str, Any]], 
                            forecast_minutes: int = 30) -> Dict[str, Any]:
        """
        Forecast metric trends.
        
        Args:
            metrics: Historical metric data
            forecast_minutes: Minutes to forecast ahead
            
        Returns:
            Forecast results
        """
        pass
    
    @abstractmethod
    async def assess_risk(self, current_state: Dict[str, Any]) -> float:
        """
        Assess risk of incident escalation.
        
        Args:
            current_state: Current system state
            
        Returns:
            Risk score (0.0 to 1.0)
        """
        pass


class ResolutionAgent(BaseAgent):
    """Abstract resolution agent interface."""
    
    def __init__(self, name: str = "resolution"):
        """Initialize resolution agent."""
        super().__init__(AgentType.RESOLUTION, name)
    
    @abstractmethod
    async def execute_action(self, recommendation: AgentRecommendation) -> Dict[str, Any]:
        """
        Execute a resolution action.
        
        Args:
            recommendation: Action to execute
            
        Returns:
            Execution results
        """
        pass
    
    @abstractmethod
    async def validate_action(self, recommendation: AgentRecommendation) -> bool:
        """
        Validate action before execution.
        
        Args:
            recommendation: Action to validate
            
        Returns:
            True if action is valid and safe
        """
        pass
    
    @abstractmethod
    async def rollback_action(self, action_id: str) -> Dict[str, Any]:
        """
        Rollback a previously executed action.
        
        Args:
            action_id: ID of action to rollback
            
        Returns:
            Rollback results
        """
        pass


class CommunicationAgent(BaseAgent):
    """Abstract communication agent interface."""
    
    def __init__(self, name: str = "communication"):
        """Initialize communication agent."""
        super().__init__(AgentType.COMMUNICATION, name)
    
    @abstractmethod
    async def send_notification(self, channel: str, message: str, 
                              severity: str) -> bool:
        """
        Send notification through specified channel.
        
        Args:
            channel: Communication channel (slack, email, pagerduty)
            message: Message to send
            severity: Message severity
            
        Returns:
            True if notification sent successfully
        """
        pass
    
    @abstractmethod
    async def escalate_incident(self, incident: Incident, 
                              escalation_level: str) -> bool:
        """
        Escalate incident to appropriate stakeholders.
        
        Args:
            incident: Incident to escalate
            escalation_level: Level of escalation
            
        Returns:
            True if escalation successful
        """
        pass