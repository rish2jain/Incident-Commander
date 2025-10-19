"""
Prediction Agent

Provides time-series forecasting and predictive incident prevention capabilities.
Implements 15-30 minute advance warning system with 80% accuracy target.
"""

import asyncio
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from src.interfaces.agent import BaseAgent
from src.models.agent import AgentRecommendation, AgentType, AgentMessage, ActionType, RiskLevel
from src.models.incident import Incident
from src.services.aws import AWSServiceFactory
from src.services.rag_memory import ScalableRAGMemory
from src.services.preventive_action_engine import PreventiveActionEngine
from src.utils.logging import get_logger
from src.utils.exceptions import AgentError

from .models import PredictionModel, PredictionResult, TrendData, PredictionHorizon
from .features import FeatureExtractor, MetricFeatures

logger = get_logger(__name__)


class PredictionAgent(BaseAgent):
    """
    Prediction Agent for incident forecasting and prevention
    
    Capabilities:
    - Time-series trend analysis with seasonal decomposition
    - 15-30 minute advance warning system
    - Risk assessment using Monte Carlo simulation
    - Preventive action recommendations
    """
    
    def __init__(
        self,
        aws_factory: AWSServiceFactory,
        rag_memory: ScalableRAGMemory,
        agent_id: str = "prediction-agent"
    ):
        super().__init__(AgentType.PREDICTION, agent_id)
        self.aws_factory = aws_factory
        self.rag_memory = rag_memory
        self.prediction_model = PredictionModel()
        self.feature_extractor = FeatureExtractor()
        self.preventive_action_engine = PreventiveActionEngine(rag_memory)
        
        # Performance targets
        self.target_accuracy = 0.8  # 80% accuracy target
        self.prediction_window = timedelta(minutes=30)  # 30-minute prediction window
        self.max_processing_time = timedelta(seconds=90)  # 90s target, 150s max
        
        # Monitoring data sources
        self.data_sources = {
            "cloudwatch": self._fetch_cloudwatch_metrics,
            "datadog": self._fetch_datadog_metrics,
            "application": self._fetch_application_metrics
        }
        
        logger.info(f"Initialized {self.name} with {len(self.data_sources)} data sources")
    
    async def process_incident(self, incident: Incident) -> List[AgentRecommendation]:
        """
        Process incident for prediction analysis
        
        Args:
            incident: Incident to analyze for prediction patterns
            
        Returns:
            Agent recommendation with prediction insights
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Processing incident {incident.id} for prediction analysis")
            
            # Fetch monitoring data from all sources
            monitoring_data = await self._fetch_monitoring_data(incident)
            
            # Extract features from monitoring data
            features = await self.feature_extractor.extract_features(monitoring_data)
            
            # Get historical incidents for pattern matching
            historical_incidents = await self._get_historical_incidents(incident)
            
            # Convert features to trend data for prediction model
            trend_data = await self._convert_features_to_trends(features)
            
            # Generate predictions
            predictions = await self.prediction_model.predict_incident(
                trend_data, historical_incidents
            )
            
            # Create recommendation based on predictions
            recommendation = await self._create_recommendation(
                incident, predictions, features
            )
            
            # Update agent status
            processing_time = datetime.utcnow() - start_time
            await self._update_status(processing_time, len(predictions))
            
            logger.info(
                f"Completed prediction analysis for {incident.id} in {processing_time.total_seconds():.2f}s"
            )
            
            return [recommendation]
            
        except Exception as e:
            logger.error(f"Error processing incident {incident.id}: {e}")
            await self._update_status_error(str(e))
            
            return [AgentRecommendation(
                agent_name=AgentType.PREDICTION,
                incident_id=incident.id,
                action_type=ActionType.NO_ACTION,
                action_id="prediction_error",
                confidence=0.0,
                risk_level=RiskLevel.LOW,
                estimated_impact="No impact due to error",
                reasoning=f"Prediction analysis failed: {str(e)}",
                urgency=0.0
            )]
    
    async def predict_future_incidents(
        self, 
        time_horizon: timedelta = None
    ) -> List[PredictionResult]:
        """
        Predict future incidents within specified time horizon
        
        Args:
            time_horizon: Time horizon for predictions (default: 30 minutes)
            
        Returns:
            List of prediction results
        """
        try:
            if time_horizon is None:
                time_horizon = self.prediction_window
            
            logger.info(f"Predicting incidents for next {time_horizon}")
            
            # Fetch current system metrics
            monitoring_data = await self._fetch_current_metrics()
            
            # Extract features
            features = await self.feature_extractor.extract_features(monitoring_data)
            
            # Get historical incidents for context
            historical_incidents = await self._get_recent_historical_incidents()
            
            # Convert to trend data
            trend_data = await self._convert_features_to_trends(features)
            
            # Generate predictions
            predictions = await self.prediction_model.predict_incident(
                trend_data, historical_incidents
            )
            
            # Filter predictions within time horizon
            filtered_predictions = [
                p for p in predictions 
                if p.time_to_incident <= time_horizon
            ]
            
            logger.info(f"Generated {len(filtered_predictions)} predictions within {time_horizon}")
            
            return filtered_predictions
            
        except Exception as e:
            logger.error(f"Error predicting future incidents: {e}")
            return []
    
    async def _fetch_monitoring_data(self, incident: Incident) -> Dict[str, Any]:
        """Fetch monitoring data from all configured sources"""
        try:
            monitoring_data = {}
            
            # Fetch data from each source in parallel
            tasks = []
            for source_name, fetch_func in self.data_sources.items():
                task = asyncio.create_task(
                    self._safe_fetch_data(source_name, fetch_func, incident)
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine results
            for i, (source_name, _) in enumerate(self.data_sources.items()):
                result = results[i]
                if not isinstance(result, Exception) and result:
                    monitoring_data[source_name] = result
                else:
                    logger.warning(f"Failed to fetch data from {source_name}: {result}")
            
            return monitoring_data
            
        except Exception as e:
            logger.error(f"Error fetching monitoring data: {e}")
            return {}
    
    async def _safe_fetch_data(
        self, 
        source_name: str, 
        fetch_func, 
        incident: Incident
    ) -> Optional[Dict[str, Any]]:
        """Safely fetch data from a source with timeout"""
        try:
            return await asyncio.wait_for(
                fetch_func(incident), 
                timeout=30.0  # 30-second timeout per source
            )
        except asyncio.TimeoutError:
            logger.warning(f"Timeout fetching data from {source_name}")
            return None
        except Exception as e:
            logger.error(f"Error fetching data from {source_name}: {e}")
            return None
    
    async def _fetch_cloudwatch_metrics(self, incident: Incident) -> Dict[str, Any]:
        """Fetch metrics from CloudWatch"""
        try:
            cloudwatch = await self.aws_factory.get_cloudwatch_client()
            
            # Define key metrics to fetch
            metrics = {
                "cpu_utilization": {
                    "namespace": "AWS/EC2",
                    "metric_name": "CPUUtilization"
                },
                "memory_utilization": {
                    "namespace": "System/Linux",
                    "metric_name": "MemoryUtilization"
                },
                "disk_utilization": {
                    "namespace": "System/Linux",
                    "metric_name": "DiskSpaceUtilization"
                }
            }
            
            # Fetch metrics for the last 24 hours
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=24)
            
            metric_data = {}
            
            for metric_key, metric_config in metrics.items():
                try:
                    response = await cloudwatch.get_metric_statistics(
                        Namespace=metric_config["namespace"],
                        MetricName=metric_config["metric_name"],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=300,  # 5-minute intervals
                        Statistics=["Average"]
                    )
                    
                    if response.get("Datapoints"):
                        datapoints = sorted(
                            response["Datapoints"], 
                            key=lambda x: x["Timestamp"]
                        )
                        
                        metric_data[metric_key] = {
                            "timestamps": [dp["Timestamp"] for dp in datapoints],
                            "values": [dp["Average"] for dp in datapoints],
                            "service": incident.metadata.tags.get("service", "unknown")
                        }
                
                except Exception as e:
                    logger.warning(f"Failed to fetch CloudWatch metric {metric_key}: {e}")
            
            return metric_data
            
        except Exception as e:
            logger.error(f"Error fetching CloudWatch metrics: {e}")
            return {}
    
    async def _fetch_datadog_metrics(self, incident: Incident) -> Dict[str, Any]:
        """Fetch metrics from Datadog (simulated for demo)"""
        try:
            # In a real implementation, this would use Datadog API
            # For now, simulate with synthetic data
            
            import random
            import numpy as np
            
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=24)
            
            # Generate synthetic time series data
            timestamps = []
            current_time = start_time
            while current_time <= end_time:
                timestamps.append(current_time)
                current_time += timedelta(minutes=5)
            
            metric_data = {}
            
            # Simulate error rate metric
            base_error_rate = 0.01
            error_rates = []
            for i, ts in enumerate(timestamps):
                # Add some trend and noise
                trend = 0.0001 * i  # Slight upward trend
                noise = random.gauss(0, 0.005)
                value = max(0, base_error_rate + trend + noise)
                error_rates.append(value)
            
            metric_data["error_rate"] = {
                "timestamps": timestamps,
                "values": error_rates,
                "service": incident.metadata.tags.get("service", "unknown")
            }
            
            # Simulate response time metric
            base_response_time = 100  # ms
            response_times = []
            for i, ts in enumerate(timestamps):
                trend = 0.1 * i  # Gradual increase
                noise = random.gauss(0, 10)
                value = max(0, base_response_time + trend + noise)
                response_times.append(value)
            
            metric_data["response_time"] = {
                "timestamps": timestamps,
                "values": response_times,
                "service": incident.metadata.tags.get("service", "unknown")
            }
            
            return metric_data
            
        except Exception as e:
            logger.error(f"Error fetching Datadog metrics: {e}")
            return {}
    
    async def _fetch_application_metrics(self, incident: Incident) -> Dict[str, Any]:
        """Fetch application-specific metrics"""
        try:
            # In a real implementation, this would fetch from application monitoring
            # For now, simulate with synthetic data
            
            import random
            
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=24)
            
            timestamps = []
            current_time = start_time
            while current_time <= end_time:
                timestamps.append(current_time)
                current_time += timedelta(minutes=5)
            
            metric_data = {}
            
            # Simulate request rate
            base_request_rate = 1000  # requests/min
            request_rates = []
            for i, ts in enumerate(timestamps):
                # Add daily pattern
                hour = ts.hour
                daily_factor = 0.5 + 0.5 * np.sin((hour - 6) * np.pi / 12)
                noise = random.gauss(0, 50)
                value = max(0, base_request_rate * daily_factor + noise)
                request_rates.append(value)
            
            metric_data["request_rate"] = {
                "timestamps": timestamps,
                "values": request_rates,
                "service": incident.metadata.tags.get("service", "unknown")
            }
            
            return metric_data
            
        except Exception as e:
            logger.error(f"Error fetching application metrics: {e}")
            return {}
    
    async def _fetch_current_metrics(self) -> Dict[str, Any]:
        """Fetch current system metrics for proactive prediction"""
        try:
            # Create a dummy incident for metric fetching
            from src.models.incident import BusinessImpact, IncidentMetadata, ServiceTier
            
            dummy_incident = Incident(
                id="prediction_scan",
                title="Proactive Prediction Scan",
                description="Scanning for potential incidents",
                severity="low",
                status="investigating",
                business_impact=BusinessImpact(
                    service_tier=ServiceTier.TIER_3,
                    affected_users=0
                ),
                metadata=IncidentMetadata(
                    source_system="prediction_agent",
                    tags={"service": "system"}
                )
            )
            
            return await self._fetch_monitoring_data(dummy_incident)
            
        except Exception as e:
            logger.error(f"Error fetching current metrics: {e}")
            return {}
    
    async def _get_historical_incidents(self, incident: Incident) -> List[Incident]:
        """Get historical incidents for pattern matching"""
        try:
            # Query RAG memory for similar incidents
            service_name = incident.metadata.tags.get("service", "unknown")
            query = f"service:{service_name} severity:{incident.severity}"
            
            search_results = await self.rag_memory.search_similar_incidents(
                query=query,
                limit=20,
                exclude_incident_id=incident.id
            )
            
            # Convert search results to Incident objects
            historical_incidents = []
            for result in search_results:
                if "incident_data" in result.get("metadata", {}):
                    incident_data = result["metadata"]["incident_data"]
                    historical_incident = Incident(**incident_data)
                    historical_incidents.append(historical_incident)
            
            logger.info(f"Retrieved {len(historical_incidents)} historical incidents")
            return historical_incidents
            
        except Exception as e:
            logger.error(f"Error getting historical incidents: {e}")
            return []
    
    async def _get_recent_historical_incidents(self) -> List[Incident]:
        """Get recent historical incidents for proactive prediction"""
        try:
            # Query for recent incidents (last 30 days)
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            search_results = await self.rag_memory.search_similar_incidents(
                query="*",  # Get all incidents
                limit=50
            )
            
            # Filter by date and convert to Incident objects
            historical_incidents = []
            for result in search_results:
                if "incident_data" in result.get("metadata", {}):
                    incident_data = result["metadata"]["incident_data"]
                    incident_date = datetime.fromisoformat(
                        incident_data.get("created_at", "1970-01-01T00:00:00")
                    )
                    
                    if incident_date >= cutoff_date:
                        historical_incident = Incident(**incident_data)
                        historical_incidents.append(historical_incident)
            
            return historical_incidents
            
        except Exception as e:
            logger.error(f"Error getting recent historical incidents: {e}")
            return []
    
    async def _convert_features_to_trends(
        self, 
        features: Dict[str, MetricFeatures]
    ) -> Dict[str, TrendData]:
        """Convert extracted features to trend data format"""
        try:
            trend_data = {}
            
            for metric_name, metric_features in features.items():
                # Create synthetic trend data from features
                # In a real implementation, this would use the original time series
                
                timestamps = []
                values = []
                
                # Generate synthetic time series based on features
                current_time = datetime.utcnow()
                for i in range(24):  # 24 hours of hourly data
                    timestamp = current_time - timedelta(hours=23-i)
                    
                    # Generate value based on trend
                    base_value = metric_features.mean_value
                    trend_component = metric_features.trend_slope * i
                    noise = np.random.normal(0, metric_features.std_deviation * 0.1)
                    
                    value = base_value + trend_component + noise
                    
                    timestamps.append(timestamp)
                    values.append(max(0, value))  # Ensure non-negative
                
                trend_data[metric_name] = TrendData(
                    timestamps=timestamps,
                    values=values,
                    metric_name=metric_name,
                    service_name="system"
                )
            
            return trend_data
            
        except Exception as e:
            logger.error(f"Error converting features to trends: {e}")
            return {}
    
    async def _create_recommendation(
        self,
        incident: Incident,
        predictions: List[PredictionResult],
        features: Dict[str, MetricFeatures]
    ) -> AgentRecommendation:
        """Create agent recommendation based on predictions"""
        try:
            if not predictions:
                return AgentRecommendation(
                    agent_name=AgentType.PREDICTION,
                    incident_id=incident.id,
                    action_type=ActionType.NO_ACTION,
                    action_id="no_prediction",
                    confidence=0.5,
                    risk_level=RiskLevel.LOW,
                    estimated_impact="No predicted incidents",
                    reasoning="No significant predictions found",
                    urgency=0.0
                )
            
            # Get the highest probability prediction
            top_prediction = predictions[0]
            
            # Calculate overall confidence
            confidence = min(top_prediction.confidence * 0.9, 1.0)  # Slightly conservative
            
            # Create reasoning
            reasoning_parts = [
                f"Predicted {top_prediction.incident_type} with {top_prediction.probability:.1%} probability",
                f"Estimated time to incident: {top_prediction.time_to_incident}",
                f"Risk factors: {', '.join(top_prediction.risk_factors[:3])}"
            ]
            
            if top_prediction.business_impact > 0:
                reasoning_parts.append(
                    f"Estimated business impact: ${top_prediction.business_impact:.0f}/min"
                )
            
            reasoning = ". ".join(reasoning_parts)
            
            # Determine action type based on prediction
            action_type = ActionType.NO_ACTION
            if top_prediction.probability > 0.7:
                action_type = ActionType.ESCALATE_INCIDENT
            elif top_prediction.probability > 0.5:
                action_type = ActionType.NOTIFY_TEAM
            
            # Determine risk level
            risk_level = RiskLevel.LOW
            if top_prediction.probability > 0.8:
                risk_level = RiskLevel.CRITICAL
            elif top_prediction.probability > 0.6:
                risk_level = RiskLevel.HIGH
            elif top_prediction.probability > 0.4:
                risk_level = RiskLevel.MEDIUM
            
            # Create parameters with prediction details
            parameters = {
                "prediction_count": len(predictions),
                "top_prediction": {
                    "type": top_prediction.incident_type,
                    "probability": top_prediction.probability,
                    "time_to_incident_minutes": top_prediction.time_to_incident.total_seconds() / 60,
                    "horizon": top_prediction.prediction_horizon.value
                },
                "preventive_actions": top_prediction.preventive_actions[:3],
                "feature_count": len(features),
                "data_sources": list(self.data_sources.keys())
            }
            
            return AgentRecommendation(
                agent_name=AgentType.PREDICTION,
                incident_id=incident.id,
                action_type=action_type,
                action_id=f"prediction_{top_prediction.incident_type}",
                confidence=confidence,
                risk_level=risk_level,
                estimated_impact=f"${top_prediction.business_impact:.0f}/min potential impact",
                reasoning=reasoning,
                parameters=parameters,
                urgency=top_prediction.probability,
                time_sensitive=True,
                execution_window_minutes=int(top_prediction.time_to_incident.total_seconds() / 60)
            )
            
        except Exception as e:
            logger.error(f"Error creating recommendation: {e}")
            return AgentRecommendation(
                agent_name=AgentType.PREDICTION,
                incident_id=incident.id,
                action_type="no_action",
                action_id="prediction_error",
                confidence=0.0,
                risk_level="low",
                estimated_impact="No impact due to error",
                reasoning=f"Error creating prediction recommendation: {str(e)}",
                parameters={"error": str(e)},
                urgency=0.0
            )
    
    async def _update_status(self, processing_time: timedelta, prediction_count: int):
        """Update agent status after successful processing"""
        try:
            self.is_healthy = True
            self.update_heartbeat()
            self.increment_processing_count()
            
        except Exception as e:
            logger.error(f"Error updating status: {e}")
    
    async def _update_status_error(self, error_message: str):
        """Update agent status after error"""
        try:
            self.increment_error_count()
            self.update_heartbeat()
            
        except Exception as e:
            logger.error(f"Error updating error status: {e}")
    
    async def health_check(self) -> bool:
        """Perform health check for this agent"""
        try:
            # Basic health check - ensure we can access required services
            if not self.aws_factory or not self.rag_memory:
                return False
            
            # Check if we can create prediction model
            if not self.prediction_model or not self.feature_extractor:
                return False
            
            return self.is_healthy
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Handle a message from another agent"""
        try:
            # For now, prediction agent doesn't handle inter-agent messages
            # This could be extended for coordination with other agents
            logger.info(f"Received message from {message.sender_agent}: {message.message_type}")
            return None
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return None
    
    async def health_check(self) -> bool:
        """Perform health check for this agent"""
        try:
            # Basic health check - ensure we can access required services
            if not self.aws_factory or not self.rag_memory:
                return False
            
            # Check if we can create prediction model
            if not self.prediction_model or not self.feature_extractor:
                return False
            
            return self.is_healthy
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def forecast_trends(self, metrics: List[Dict[str, Any]], 
                            forecast_minutes: int = 30) -> Dict[str, Any]:
        """Forecast metric trends"""
        try:
            # Convert metrics to our internal format
            monitoring_data = {"application": {}}
            for i, metric in enumerate(metrics):
                monitoring_data["application"][f"metric_{i}"] = metric
            
            # Extract features
            features = await self.feature_extractor.extract_features(monitoring_data)
            
            # Convert to trend data
            trend_data = await self._convert_features_to_trends(features)
            
            # Generate predictions
            predictions = await self.prediction_model.predict_incident(trend_data, [])
            
            # Format results
            forecast_results = {
                "forecast_horizon_minutes": forecast_minutes,
                "predictions": [
                    {
                        "incident_type": p.incident_type,
                        "probability": p.probability,
                        "time_to_incident_minutes": p.time_to_incident.total_seconds() / 60
                    }
                    for p in predictions
                ]
            }
            
            return forecast_results
            
        except Exception as e:
            logger.error(f"Error forecasting trends: {e}")
            return {"error": str(e)}
    
    async def assess_risk(self, current_state: Dict[str, Any]) -> float:
        """Assess risk of incident escalation"""
        try:
            # Simple risk assessment based on current state
            risk_score = 0.0
            
            # Check for high CPU utilization
            if current_state.get("cpu_utilization", 0) > 80:
                risk_score += 0.3
            
            # Check for high memory utilization
            if current_state.get("memory_utilization", 0) > 85:
                risk_score += 0.3
            
            # Check for high error rate
            if current_state.get("error_rate", 0) > 0.05:  # 5% error rate
                risk_score += 0.4
            
            return min(risk_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error assessing risk: {e}")
            return 0.0
    
    async def generate_preventive_recommendations(
        self,
        predictions: List[PredictionResult]
    ) -> List[Dict[str, Any]]:
        """Generate preventive action recommendations for predictions"""
        try:
            recommendations = []
            
            for prediction in predictions:
                if prediction.probability > 0.5:  # Only for high-probability predictions
                    preventive_recommendation = await self.preventive_action_engine.generate_recommendations(
                        incident_type=prediction.incident_type,
                        predicted_probability=prediction.probability,
                        time_to_incident=prediction.time_to_incident,
                        service_context={"service_tier": "critical"}  # Could be dynamic
                    )
                    
                    recommendations.append({
                        "prediction": {
                            "incident_type": prediction.incident_type,
                            "probability": prediction.probability,
                            "time_to_incident_minutes": prediction.time_to_incident.total_seconds() / 60
                        },
                        "preventive_actions": [
                            {
                                "action_id": action.action_id,
                                "description": action.description,
                                "estimated_cost": action.estimated_cost,
                                "estimated_benefit": action.estimated_benefit,
                                "success_probability": action.success_probability,
                                "expected_value": action.expected_value,
                                "execution_time_minutes": action.execution_time_minutes,
                                "risk_level": action.risk_level,
                                "automation_available": action.automation_available
                            }
                            for action in preventive_recommendation.recommended_actions
                        ],
                        "reasoning": preventive_recommendation.reasoning,
                        "confidence": preventive_recommendation.confidence
                    })
            
            logger.info(f"Generated {len(recommendations)} preventive action recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating preventive recommendations: {e}")
            return []
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get detailed health status of the prediction agent"""
        try:
            status = await self.get_status()
            status["agent_id"] = self.name  # Add agent_id for test compatibility
            status["status"] = "healthy" if self.is_healthy else "unhealthy"  # Add status field
            status.update({
                "capabilities": [
                    "time_series_forecasting",
                    "trend_analysis",
                    "risk_assessment",
                    "preventive_recommendations"
                ],
                "performance_targets": {
                    "accuracy_target": self.target_accuracy,
                    "prediction_window_minutes": self.prediction_window.total_seconds() / 60,
                    "max_processing_time_seconds": self.max_processing_time.total_seconds()
                },
                "data_sources": list(self.data_sources.keys())
            })
            return status
            
        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return {
                "agent_type": "prediction",
                "name": self.name,
                "status": "error",
                "error": str(e)
            }