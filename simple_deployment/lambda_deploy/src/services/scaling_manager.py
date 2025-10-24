"""
Scaling Manager Service

Implements horizontal scaling and load balancing including:
- Auto-scaling for agent replicas based on incident volume
- Load balancing strategies for concurrent incident processing
- Geographic distribution for global incident response
- Cross-region failover and disaster recovery mechanisms

Requirements: 10.1, 10.2
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum

import aioboto3
from botocore.exceptions import ClientError

from src.utils.config import config
from src.utils.logging import get_logger
from src.utils.constants import HEALTH_CONFIG, PERFORMANCE_TARGETS, AGENT_DEPENDENCY_ORDER
from src.utils.exceptions import ScalingError


logger = get_logger(__name__)


class ScalingStrategy(Enum):
    """Scaling strategy types."""
    REACTIVE = "reactive"
    PREDICTIVE = "predictive"
    SCHEDULED = "scheduled"
    HYBRID = "hybrid"


class LoadBalancingStrategy(Enum):
    """Load balancing strategy types."""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    GEOGRAPHIC = "geographic"
    INCIDENT_SEVERITY = "incident_severity"


@dataclass
class AgentReplica:
    """Agent replica information."""
    replica_id: str
    agent_type: str
    region: str
    status: str  # "healthy", "unhealthy", "scaling"
    current_load: int = 0
    max_capacity: int = 10
    last_health_check: datetime = field(default_factory=datetime.utcnow)
    performance_score: float = 1.0


@dataclass
class ScalingMetrics:
    """Scaling and load balancing metrics."""
    total_incidents_per_minute: float = 0.0
    agent_utilization: Dict[str, float] = field(default_factory=dict)
    scaling_actions: List[str] = field(default_factory=list)
    load_distribution: Dict[str, int] = field(default_factory=dict)
    cross_region_latency: Dict[str, float] = field(default_factory=dict)
    failover_events: int = 0


@dataclass
class ScalingPolicy:
    """Auto-scaling policy configuration."""
    min_replicas: int
    max_replicas: int
    target_utilization: float
    scale_up_threshold: float
    scale_down_threshold: float
    cooldown_period: int  # seconds
    scale_up_increment: int = 1
    scale_down_increment: int = 1


class ScalingManager:
    """
    Horizontal scaling and load balancing manager for enterprise-scale
    incident processing with geographic distribution and failover.
    """
    
    def __init__(self):
        self.logger = logger
        
        # Agent replicas tracking
        self.agent_replicas: Dict[str, List[AgentReplica]] = defaultdict(list)
        self.replica_counter = 0
        
        # Scaling policies per agent type
        self.scaling_policies = {
            "detection": ScalingPolicy(
                min_replicas=2, max_replicas=10, target_utilization=0.7,
                scale_up_threshold=0.8, scale_down_threshold=0.3, cooldown_period=300
            ),
            "diagnosis": ScalingPolicy(
                min_replicas=2, max_replicas=8, target_utilization=0.7,
                scale_up_threshold=0.8, scale_down_threshold=0.3, cooldown_period=300
            ),
            "prediction": ScalingPolicy(
                min_replicas=1, max_replicas=5, target_utilization=0.7,
                scale_up_threshold=0.8, scale_down_threshold=0.3, cooldown_period=300
            ),
            "resolution": ScalingPolicy(
                min_replicas=1, max_replicas=6, target_utilization=0.7,
                scale_up_threshold=0.8, scale_down_threshold=0.3, cooldown_period=300
            ),
            "communication": ScalingPolicy(
                min_replicas=1, max_replicas=4, target_utilization=0.7,
                scale_up_threshold=0.8, scale_down_threshold=0.3, cooldown_period=300
            )
        }
        
        # Load balancing configuration
        self.load_balancing_strategy = LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN
        self.round_robin_counters: Dict[str, int] = defaultdict(int)
        
        # Geographic distribution
        self.regions = ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]
        self.primary_region = config.aws.region
        self.region_weights = {
            "us-east-1": 1.0,
            "us-west-2": 0.8,
            "eu-west-1": 0.9,
            "ap-southeast-1": 0.7
        }
        
        # Metrics and monitoring
        self.metrics = ScalingMetrics()
        self.incident_history = deque(maxlen=1000)  # Last 1000 incidents
        self.scaling_history = deque(maxlen=100)   # Last 100 scaling actions
        
        # AWS clients for scaling operations (lazy initialization)
        self.aws_session = None
        self.ecs_client = None
        self.lambda_client = None
        self.cloudwatch_client = None
        
        # Scaling state
        self.last_scaling_action: Dict[str, datetime] = {}
        self.scaling_in_progress: Dict[str, bool] = defaultdict(bool)
    
    def _get_aws_session(self) -> aioboto3.Session:
        """Get or create AWS session lazily."""
        if self.aws_session is None:
            self.aws_session = aioboto3.Session(region_name=config.aws.region or "us-east-1")
        return self.aws_session
        
    async def initialize(self) -> None:
        """Initialize scaling manager with AWS clients and initial replicas."""
        try:
            # Initialize AWS clients
            await self._initialize_aws_clients()
            
            # Initialize agent replicas
            await self._initialize_agent_replicas()
            
            # Start monitoring and scaling loops
            asyncio.create_task(self._scaling_loop())
            asyncio.create_task(self._health_monitoring_loop())
            
            self.logger.info("Scaling manager initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize scaling manager: {e}")
            raise ScalingError(f"Initialization failed: {e}")
    
    async def _initialize_aws_clients(self) -> None:
        """Initialize AWS service clients for scaling operations."""
        session = self._get_aws_session()
        async with session.client('ecs') as client:
            self.ecs_client = client
        
        async with session.client('lambda') as client:
            self.lambda_client = client
        
        async with session.client('cloudwatch') as client:
            self.cloudwatch_client = client
        
        self.logger.info("AWS clients initialized for scaling operations")
    
    async def _initialize_agent_replicas(self) -> None:
        """Initialize minimum required agent replicas."""
        for agent_type, policy in self.scaling_policies.items():
            for i in range(policy.min_replicas):
                replica = await self._create_agent_replica(agent_type, self.primary_region)
                self.agent_replicas[agent_type].append(replica)
        
        self.logger.info(f"Initialized agent replicas: {dict(self.agent_replicas)}")
    
    async def _create_agent_replica(self, agent_type: str, region: str) -> AgentReplica:
        """Create a new agent replica."""
        self.replica_counter += 1
        replica_id = f"{agent_type}-replica-{self.replica_counter}"
        
        replica = AgentReplica(
            replica_id=replica_id,
            agent_type=agent_type,
            region=region,
            status="healthy",
            max_capacity=self._get_agent_capacity(agent_type)
        )
        
        # In a real implementation, this would create actual ECS tasks or Lambda functions
        await self._deploy_replica(replica)
        
        self.logger.info(f"Created agent replica: {replica_id} in {region}")
        return replica
    
    def _get_agent_capacity(self, agent_type: str) -> int:
        """Get maximum capacity for agent type."""
        capacities = {
            "detection": 20,      # Can handle 20 concurrent detections
            "diagnosis": 10,      # Can handle 10 concurrent diagnoses
            "prediction": 15,     # Can handle 15 concurrent predictions
            "resolution": 5,      # Can handle 5 concurrent resolutions
            "communication": 25   # Can handle 25 concurrent communications
        }
        return capacities.get(agent_type, 10)
    
    async def _deploy_replica(self, replica: AgentReplica) -> None:
        """Deploy agent replica (placeholder for actual deployment)."""
        # In a real implementation, this would:
        # 1. Create ECS task definition for the agent
        # 2. Deploy to specified region
        # 3. Configure health checks
        # 4. Register with load balancer
        
        self.logger.debug(f"Deploying replica {replica.replica_id} to {replica.region}")
        
        # Simulate deployment time
        await asyncio.sleep(0.1)
        
        replica.status = "healthy"
    
    async def select_agent_replica(self, agent_type: str, incident_data: Dict[str, Any] = None) -> Optional[AgentReplica]:
        """Select best agent replica using load balancing strategy."""
        available_replicas = [
            replica for replica in self.agent_replicas[agent_type]
            if replica.status == "healthy" and replica.current_load < replica.max_capacity
        ]
        
        if not available_replicas:
            # Try to scale up if no replicas available
            await self._scale_up_agent(agent_type)
            return None
        
        # Apply load balancing strategy
        if self.load_balancing_strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._select_round_robin(agent_type, available_replicas)
        elif self.load_balancing_strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return self._select_least_connections(available_replicas)
        elif self.load_balancing_strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            return self._select_weighted_round_robin(available_replicas)
        elif self.load_balancing_strategy == LoadBalancingStrategy.GEOGRAPHIC:
            return self._select_geographic(available_replicas, incident_data)
        elif self.load_balancing_strategy == LoadBalancingStrategy.INCIDENT_SEVERITY:
            return self._select_by_severity(available_replicas, incident_data)
        else:
            return available_replicas[0]  # Default to first available
    
    def _select_round_robin(self, agent_type: str, replicas: List[AgentReplica]) -> AgentReplica:
        """Select replica using round-robin strategy."""
        counter = self.round_robin_counters[agent_type]
        selected = replicas[counter % len(replicas)]
        self.round_robin_counters[agent_type] = (counter + 1) % len(replicas)
        return selected
    
    def _select_least_connections(self, replicas: List[AgentReplica]) -> AgentReplica:
        """Select replica with least current load."""
        return min(replicas, key=lambda r: r.current_load)
    
    def _select_weighted_round_robin(self, replicas: List[AgentReplica]) -> AgentReplica:
        """Select replica using weighted round-robin based on performance."""
        # Weight by performance score and available capacity
        weights = []
        for replica in replicas:
            available_capacity = replica.max_capacity - replica.current_load
            weight = replica.performance_score * available_capacity
            weights.append(weight)
        
        # Select based on weights
        total_weight = sum(weights)
        if total_weight == 0:
            return replicas[0]
        
        import random
        r = random.uniform(0, total_weight)
        cumulative = 0
        for i, weight in enumerate(weights):
            cumulative += weight
            if r <= cumulative:
                return replicas[i]
        
        return replicas[-1]
    
    def _select_geographic(self, replicas: List[AgentReplica], incident_data: Dict[str, Any]) -> AgentReplica:
        """Select replica based on geographic proximity."""
        if not incident_data or "region" not in incident_data:
            return self._select_least_connections(replicas)
        
        incident_region = incident_data["region"]
        
        # Prefer replicas in the same region
        same_region_replicas = [r for r in replicas if r.region == incident_region]
        if same_region_replicas:
            return self._select_least_connections(same_region_replicas)
        
        # Fall back to least connections
        return self._select_least_connections(replicas)
    
    def _select_by_severity(self, replicas: List[AgentReplica], incident_data: Dict[str, Any]) -> AgentReplica:
        """Select replica based on incident severity."""
        if not incident_data or "severity" not in incident_data:
            return self._select_least_connections(replicas)
        
        severity = incident_data["severity"]
        
        # For high severity incidents, prefer replicas with better performance
        if severity in ["critical", "high"]:
            return max(replicas, key=lambda r: r.performance_score)
        else:
            return self._select_least_connections(replicas)
    
    async def assign_incident_to_replica(self, replica: AgentReplica, incident_id: str) -> None:
        """Assign incident to replica and update load."""
        replica.current_load += 1
        self.metrics.load_distribution[replica.replica_id] = replica.current_load
        
        self.logger.debug(f"Assigned incident {incident_id} to replica {replica.replica_id} (load: {replica.current_load}/{replica.max_capacity})")
    
    async def release_incident_from_replica(self, replica: AgentReplica, incident_id: str) -> None:
        """Release incident from replica and update load."""
        replica.current_load = max(0, replica.current_load - 1)
        self.metrics.load_distribution[replica.replica_id] = replica.current_load
        
        self.logger.debug(f"Released incident {incident_id} from replica {replica.replica_id} (load: {replica.current_load}/{replica.max_capacity})")
    
    async def _scale_up_agent(self, agent_type: str) -> bool:
        """Scale up agent replicas."""
        if self.scaling_in_progress[agent_type]:
            return False
        
        policy = self.scaling_policies[agent_type]
        current_replicas = len(self.agent_replicas[agent_type])
        
        if current_replicas >= policy.max_replicas:
            self.logger.warning(f"Cannot scale up {agent_type}: at maximum replicas ({policy.max_replicas})")
            return False
        
        # Check cooldown period
        last_action = self.last_scaling_action.get(agent_type)
        if last_action and (datetime.utcnow() - last_action).total_seconds() < policy.cooldown_period:
            return False
        
        self.scaling_in_progress[agent_type] = True
        
        try:
            # Create new replicas
            new_replicas = min(policy.scale_up_increment, policy.max_replicas - current_replicas)
            
            for i in range(new_replicas):
                # Select region for new replica (prefer less loaded regions)
                region = self._select_region_for_scaling()
                replica = await self._create_agent_replica(agent_type, region)
                self.agent_replicas[agent_type].append(replica)
            
            self.last_scaling_action[agent_type] = datetime.utcnow()
            self.metrics.scaling_actions.append(f"Scaled up {agent_type} by {new_replicas} replicas")
            
            self.logger.info(f"Scaled up {agent_type}: {current_replicas} -> {current_replicas + new_replicas}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to scale up {agent_type}: {e}")
            return False
        finally:
            self.scaling_in_progress[agent_type] = False
    
    async def _scale_down_agent(self, agent_type: str) -> bool:
        """Scale down agent replicas."""
        if self.scaling_in_progress[agent_type]:
            return False
        
        policy = self.scaling_policies[agent_type]
        current_replicas = len(self.agent_replicas[agent_type])
        
        if current_replicas <= policy.min_replicas:
            return False
        
        # Check cooldown period
        last_action = self.last_scaling_action.get(agent_type)
        if last_action and (datetime.utcnow() - last_action).total_seconds() < policy.cooldown_period:
            return False
        
        self.scaling_in_progress[agent_type] = True
        
        try:
            # Remove least loaded replicas
            replicas_to_remove = min(policy.scale_down_increment, current_replicas - policy.min_replicas)
            
            # Sort by current load (ascending) to remove least loaded first
            sorted_replicas = sorted(self.agent_replicas[agent_type], key=lambda r: r.current_load)
            
            for i in range(replicas_to_remove):
                replica = sorted_replicas[i]
                if replica.current_load == 0:  # Only remove if no active load
                    await self._remove_agent_replica(replica)
                    self.agent_replicas[agent_type].remove(replica)
            
            self.last_scaling_action[agent_type] = datetime.utcnow()
            self.metrics.scaling_actions.append(f"Scaled down {agent_type} by {replicas_to_remove} replicas")
            
            self.logger.info(f"Scaled down {agent_type}: {current_replicas} -> {len(self.agent_replicas[agent_type])}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to scale down {agent_type}: {e}")
            return False
        finally:
            self.scaling_in_progress[agent_type] = False
    
    def _select_region_for_scaling(self) -> str:
        """Select region for new replica based on current distribution."""
        # Count replicas per region
        region_counts = defaultdict(int)
        for agent_type, replicas in self.agent_replicas.items():
            for replica in replicas:
                region_counts[replica.region] += 1
        
        # Select region with least replicas
        if not region_counts:
            return self.primary_region
        
        return min(self.regions, key=lambda r: region_counts.get(r, 0))
    
    async def _remove_agent_replica(self, replica: AgentReplica) -> None:
        """Remove agent replica."""
        replica.status = "terminating"
        
        # In a real implementation, this would:
        # 1. Drain connections
        # 2. Terminate ECS task or Lambda function
        # 3. Remove from load balancer
        
        self.logger.info(f"Removed agent replica: {replica.replica_id}")
    
    async def _scaling_loop(self) -> None:
        """Background scaling loop."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Calculate current utilization
                for agent_type in self.scaling_policies.keys():
                    utilization = await self._calculate_agent_utilization(agent_type)
                    self.metrics.agent_utilization[agent_type] = utilization
                    
                    policy = self.scaling_policies[agent_type]
                    
                    # Scale up if utilization is high
                    if utilization > policy.scale_up_threshold:
                        await self._scale_up_agent(agent_type)
                    
                    # Scale down if utilization is low
                    elif utilization < policy.scale_down_threshold:
                        await self._scale_down_agent(agent_type)
                
            except Exception as e:
                self.logger.error(f"Scaling loop error: {e}")
    
    async def _calculate_agent_utilization(self, agent_type: str) -> float:
        """Calculate current utilization for agent type."""
        replicas = self.agent_replicas[agent_type]
        if not replicas:
            return 0.0
        
        total_capacity = sum(r.max_capacity for r in replicas)
        total_load = sum(r.current_load for r in replicas)
        
        return total_load / total_capacity if total_capacity > 0 else 0.0
    
    async def _health_monitoring_loop(self) -> None:
        """Background health monitoring loop."""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                # Check health of all replicas
                for agent_type, replicas in self.agent_replicas.items():
                    for replica in replicas:
                        await self._check_replica_health(replica)
                
            except Exception as e:
                self.logger.error(f"Health monitoring loop error: {e}")
    
    async def _check_replica_health(self, replica: AgentReplica) -> None:
        """Check health of individual replica."""
        try:
            # In a real implementation, this would:
            # 1. Check ECS task health
            # 2. Perform health check HTTP request
            # 3. Check CloudWatch metrics
            
            # Simulate health check
            replica.last_health_check = datetime.utcnow()
            
            # Update performance score based on recent performance
            # (This would be based on actual metrics in production)
            
        except Exception as e:
            self.logger.warning(f"Health check failed for replica {replica.replica_id}: {e}")
            replica.status = "unhealthy"
    
    async def handle_replica_failure(self, replica: AgentReplica) -> None:
        """Handle replica failure with automatic replacement."""
        self.logger.warning(f"Handling failure for replica {replica.replica_id}")
        
        replica.status = "unhealthy"
        self.metrics.failover_events += 1
        
        # Create replacement replica
        try:
            replacement = await self._create_agent_replica(replica.agent_type, replica.region)
            self.agent_replicas[replica.agent_type].append(replacement)
            
            # Remove failed replica
            self.agent_replicas[replica.agent_type].remove(replica)
            
            self.logger.info(f"Replaced failed replica {replica.replica_id} with {replacement.replica_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to replace replica {replica.replica_id}: {e}")
    
    async def get_scaling_metrics(self) -> ScalingMetrics:
        """Get current scaling metrics."""
        # Update incident rate
        current_time = time.time()
        recent_incidents = [
            timestamp for timestamp in self.incident_history
            if current_time - timestamp < 60  # Last minute
        ]
        self.metrics.total_incidents_per_minute = len(recent_incidents)
        
        return self.metrics
    
    async def get_replica_status(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get status of all replicas."""
        status = {}
        for agent_type, replicas in self.agent_replicas.items():
            status[agent_type] = [
                {
                    "replica_id": r.replica_id,
                    "region": r.region,
                    "status": r.status,
                    "current_load": r.current_load,
                    "max_capacity": r.max_capacity,
                    "utilization": r.current_load / r.max_capacity if r.max_capacity > 0 else 0,
                    "performance_score": r.performance_score
                }
                for r in replicas
            ]
        return status
    
    async def record_incident(self, incident_id: str) -> None:
        """Record incident for scaling metrics."""
        self.incident_history.append(time.time())
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        try:
            # Remove all replicas
            for agent_type, replicas in self.agent_replicas.items():
                for replica in replicas:
                    await self._remove_agent_replica(replica)
            
            self.logger.info("Scaling manager cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")


# Global scaling manager instance
_scaling_manager: Optional[ScalingManager] = None


async def get_scaling_manager() -> ScalingManager:
    """Get global scaling manager instance."""
    global _scaling_manager
    
    if _scaling_manager is None:
        _scaling_manager = ScalingManager()
        await _scaling_manager.initialize()
    
    return _scaling_manager