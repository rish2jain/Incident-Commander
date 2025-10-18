"""
Prediction Models

Time-series forecasting models for incident prediction.
"""

import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from src.models.incident import Incident
from src.utils.logging import get_logger

logger = get_logger(__name__)


class PredictionHorizon(Enum):
    """Prediction time horizons"""
    SHORT_TERM = "15_minutes"  # 15 minutes ahead
    MEDIUM_TERM = "30_minutes"  # 30 minutes ahead
    LONG_TERM = "60_minutes"   # 1 hour ahead


@dataclass
class PredictionResult:
    """Result of a prediction analysis"""
    incident_type: str
    probability: float
    confidence: float
    time_to_incident: timedelta
    risk_factors: List[str]
    preventive_actions: List[str]
    business_impact: float
    prediction_horizon: PredictionHorizon


@dataclass
class TrendData:
    """Time-series trend data"""
    timestamps: List[datetime]
    values: List[float]
    metric_name: str
    service_name: str


class TrendAnalyzer:
    """Analyzes time-series trends for incident prediction"""
    
    def __init__(self):
        self.seasonal_window = 24 * 7  # 7 days for seasonal patterns
        self.trend_window = 24  # 24 hours for trend analysis
        
    async def analyze_trend(self, trend_data: TrendData) -> Dict[str, float]:
        """
        Analyze trend data for anomalies and patterns
        
        Args:
            trend_data: Time-series data to analyze
            
        Returns:
            Dictionary with trend analysis results
        """
        try:
            if len(trend_data.values) < 10:
                logger.warning(f"Insufficient data for trend analysis: {len(trend_data.values)} points")
                return {"trend_score": 0.0, "anomaly_score": 0.0, "seasonal_score": 0.0}
            
            values = np.array(trend_data.values)
            
            # Calculate trend score (rate of change)
            trend_score = await self._calculate_trend_score(values)
            
            # Calculate anomaly score (deviation from normal)
            anomaly_score = await self._calculate_anomaly_score(values)
            
            # Calculate seasonal score (pattern deviation)
            seasonal_score = await self._calculate_seasonal_score(values)
            
            return {
                "trend_score": trend_score,
                "anomaly_score": anomaly_score,
                "seasonal_score": seasonal_score,
                "volatility": np.std(values),
                "mean_value": np.mean(values)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing trend for {trend_data.metric_name}: {e}")
            return {"trend_score": 0.0, "anomaly_score": 0.0, "seasonal_score": 0.0}
    
    async def _calculate_trend_score(self, values: np.ndarray) -> float:
        """Calculate trend score based on rate of change"""
        try:
            # Use linear regression to find trend
            x = np.arange(len(values))
            coeffs = np.polyfit(x, values, 1)
            trend_slope = coeffs[0]
            
            # Normalize trend score to [0, 1]
            mean_val = np.mean(values)
            if mean_val > 0:
                normalized_slope = abs(trend_slope) / mean_val
                return min(normalized_slope, 1.0)
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating trend score: {e}")
            return 0.0
    
    async def _calculate_anomaly_score(self, values: np.ndarray) -> float:
        """Calculate anomaly score based on statistical deviation"""
        try:
            if len(values) < 5:
                return 0.0
                
            # Use z-score for anomaly detection
            mean_val = np.mean(values)
            std_val = np.std(values)
            
            if std_val == 0:
                return 0.0
            
            # Check recent values for anomalies
            recent_values = values[-5:]  # Last 5 data points
            z_scores = np.abs((recent_values - mean_val) / std_val)
            max_z_score = np.max(z_scores)
            
            # Normalize to [0, 1] (z-score > 3 is highly anomalous)
            return min(max_z_score / 3.0, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating anomaly score: {e}")
            return 0.0
    
    async def _calculate_seasonal_score(self, values: np.ndarray) -> float:
        """Calculate seasonal pattern deviation score"""
        try:
            if len(values) < self.seasonal_window:
                return 0.0
            
            # Simple seasonal analysis - compare current pattern to historical
            current_pattern = values[-24:]  # Last 24 hours
            if len(current_pattern) < 24:
                return 0.0
            
            # Compare with historical patterns (simplified)
            historical_mean = np.mean(values[:-24])
            current_mean = np.mean(current_pattern)
            
            if historical_mean > 0:
                deviation = abs(current_mean - historical_mean) / historical_mean
                return min(deviation, 1.0)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating seasonal score: {e}")
            return 0.0


class MonteCarloSimulator:
    """Monte Carlo simulation for risk assessment"""
    
    def __init__(self, num_simulations: int = 1000):
        self.num_simulations = num_simulations
    
    async def simulate_incident_risk(
        self, 
        trend_data: Dict[str, TrendData],
        historical_incidents: List[Incident]
    ) -> Dict[str, float]:
        """
        Run Monte Carlo simulation to assess incident risk
        
        Args:
            trend_data: Current trend data
            historical_incidents: Historical incident patterns
            
        Returns:
            Risk assessment results
        """
        try:
            simulations = []
            
            for _ in range(self.num_simulations):
                # Simulate future metric values with noise
                simulated_risk = await self._simulate_single_scenario(
                    trend_data, historical_incidents
                )
                simulations.append(simulated_risk)
            
            # Calculate statistics
            simulations = np.array(simulations)
            
            return {
                "mean_risk": float(np.mean(simulations)),
                "std_risk": float(np.std(simulations)),
                "percentile_95": float(np.percentile(simulations, 95)),
                "percentile_99": float(np.percentile(simulations, 99)),
                "probability_high_risk": float(np.mean(simulations > 0.7)),
                "probability_critical_risk": float(np.mean(simulations > 0.9))
            }
            
        except Exception as e:
            logger.error(f"Error in Monte Carlo simulation: {e}")
            return {"mean_risk": 0.0, "std_risk": 0.0, "percentile_95": 0.0, 
                   "percentile_99": 0.0, "probability_high_risk": 0.0, 
                   "probability_critical_risk": 0.0}
    
    async def _simulate_single_scenario(
        self, 
        trend_data: Dict[str, TrendData],
        historical_incidents: List[Incident]
    ) -> float:
        """Simulate a single risk scenario"""
        try:
            total_risk = 0.0
            
            for metric_name, data in trend_data.items():
                if len(data.values) < 5:
                    continue
                
                # Calculate trend and volatility
                values = np.array(data.values)
                trend = np.polyfit(range(len(values)), values, 1)[0]
                volatility = np.std(values)
                current_value = values[-1]
                
                # Simulate future value with random walk
                future_steps = 6  # 30 minutes in 5-minute intervals
                simulated_value = current_value
                
                for _ in range(future_steps):
                    noise = np.random.normal(0, volatility * 0.1)
                    simulated_value += trend + noise
                
                # Calculate risk based on simulated value
                if "cpu" in metric_name.lower():
                    risk = min(simulated_value / 100.0, 1.0)  # CPU percentage
                elif "memory" in metric_name.lower():
                    risk = min(simulated_value / 100.0, 1.0)  # Memory percentage
                elif "error" in metric_name.lower():
                    risk = min(simulated_value * 10, 1.0)  # Error rate
                else:
                    risk = min(simulated_value / 1000.0, 1.0)  # Generic normalization
                
                total_risk += max(0, risk)
            
            # Normalize by number of metrics
            if len(trend_data) > 0:
                total_risk /= len(trend_data)
            
            return min(total_risk, 1.0)
            
        except Exception as e:
            logger.error(f"Error simulating single scenario: {e}")
            return 0.0


class SeasonalDecomposer:
    """Seasonal decomposition for time-series analysis"""
    
    def __init__(self):
        self.seasonal_period = 24  # 24 hours for daily patterns
    
    async def decompose_trend(self, trend_data: TrendData) -> Dict[str, np.ndarray]:
        """
        Decompose time series into trend, seasonal, and residual components
        
        Args:
            trend_data: Time series data to decompose
            
        Returns:
            Dictionary with trend, seasonal, and residual components
        """
        try:
            if len(trend_data.values) < self.seasonal_period * 2:
                # Not enough data for seasonal decomposition
                return await self._simple_decomposition(trend_data)
            
            values = np.array(trend_data.values)
            
            # Calculate trend using moving average
            trend = await self._calculate_trend_component(values)
            
            # Calculate seasonal component
            seasonal = await self._calculate_seasonal_component(values, trend)
            
            # Calculate residual
            residual = values - trend - seasonal
            
            return {
                "original": values,
                "trend": trend,
                "seasonal": seasonal,
                "residual": residual,
                "seasonal_strength": float(np.std(seasonal) / np.std(values)) if np.std(values) > 0 else 0.0,
                "trend_strength": float(np.std(trend) / np.std(values)) if np.std(values) > 0 else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error in seasonal decomposition: {e}")
            return await self._simple_decomposition(trend_data)
    
    async def _simple_decomposition(self, trend_data: TrendData) -> Dict[str, np.ndarray]:
        """Simple decomposition for insufficient data"""
        values = np.array(trend_data.values)
        
        # Simple linear trend
        x = np.arange(len(values))
        trend_coeff = np.polyfit(x, values, 1)
        trend = np.polyval(trend_coeff, x)
        
        # No seasonal component
        seasonal = np.zeros_like(values)
        
        # Residual
        residual = values - trend
        
        return {
            "original": values,
            "trend": trend,
            "seasonal": seasonal,
            "residual": residual,
            "seasonal_strength": 0.0,
            "trend_strength": float(np.std(trend) / np.std(values)) if np.std(values) > 0 else 0.0
        }
    
    async def _calculate_trend_component(self, values: np.ndarray) -> np.ndarray:
        """Calculate trend component using moving average"""
        try:
            # Use centered moving average
            window_size = min(self.seasonal_period, len(values) // 4)
            if window_size < 3:
                window_size = 3
            
            trend = np.zeros_like(values)
            half_window = window_size // 2
            
            for i in range(len(values)):
                start_idx = max(0, i - half_window)
                end_idx = min(len(values), i + half_window + 1)
                trend[i] = np.mean(values[start_idx:end_idx])
            
            return trend
            
        except Exception as e:
            logger.error(f"Error calculating trend component: {e}")
            return np.zeros_like(values)
    
    async def _calculate_seasonal_component(self, values: np.ndarray, trend: np.ndarray) -> np.ndarray:
        """Calculate seasonal component"""
        try:
            detrended = values - trend
            seasonal = np.zeros_like(values)
            
            # Calculate seasonal pattern
            for i in range(self.seasonal_period):
                # Get all values at this seasonal position
                seasonal_indices = list(range(i, len(values), self.seasonal_period))
                if seasonal_indices:
                    seasonal_values = detrended[seasonal_indices]
                    seasonal_mean = np.mean(seasonal_values)
                    
                    # Apply seasonal mean to all positions
                    for idx in seasonal_indices:
                        seasonal[idx] = seasonal_mean
            
            # Center seasonal component (mean should be 0)
            seasonal -= np.mean(seasonal)
            
            return seasonal
            
        except Exception as e:
            logger.error(f"Error calculating seasonal component: {e}")
            return np.zeros_like(values)


class PredictionModel:
    """Enhanced machine learning model for incident prediction with time-series forecasting"""
    
    def __init__(self):
        self.model_weights = {
            "cpu_utilization": 0.3,
            "memory_utilization": 0.25,
            "error_rate": 0.2,
            "response_time": 0.15,
            "disk_utilization": 0.1
        }
        self.risk_thresholds = {
            "high": 0.8,
            "medium": 0.6,
            "low": 0.4
        }
        
        # Enhanced components
        self.monte_carlo = MonteCarloSimulator()
        self.seasonal_decomposer = SeasonalDecomposer()
        
        # Forecasting parameters
        self.forecast_horizon_minutes = 30
        self.accuracy_target = 0.8
        
    async def predict_incident(
        self, 
        metrics: Dict[str, TrendData],
        historical_incidents: List[Incident]
    ) -> List[PredictionResult]:
        """
        Predict potential incidents based on current metrics with enhanced forecasting
        
        Args:
            metrics: Current system metrics
            historical_incidents: Historical incident data for pattern matching
            
        Returns:
            List of prediction results
        """
        try:
            predictions = []
            trend_analyzer = TrendAnalyzer()
            
            # Run Monte Carlo simulation for overall risk assessment
            monte_carlo_results = await self.monte_carlo.simulate_incident_risk(
                metrics, historical_incidents
            )
            
            # Analyze each metric with enhanced forecasting
            for metric_name, trend_data in metrics.items():
                # Basic trend analysis
                trend_analysis = await trend_analyzer.analyze_trend(trend_data)
                
                # Seasonal decomposition
                seasonal_decomp = await self.seasonal_decomposer.decompose_trend(trend_data)
                
                # Time-series forecasting
                forecast_results = await self._forecast_metric_values(
                    trend_data, seasonal_decomp
                )
                
                # Enhanced prediction probability calculation
                probability = await self._calculate_enhanced_prediction_probability(
                    metric_name, trend_analysis, seasonal_decomp, 
                    forecast_results, monte_carlo_results, historical_incidents
                )
                
                if probability > 0.3:  # Only include significant predictions
                    prediction = await self._create_enhanced_prediction_result(
                        metric_name, probability, trend_analysis, seasonal_decomp,
                        forecast_results, monte_carlo_results, historical_incidents
                    )
                    predictions.append(prediction)
            
            # Add ensemble prediction combining all metrics
            if len(predictions) > 1:
                ensemble_prediction = await self._create_ensemble_prediction(
                    predictions, monte_carlo_results, historical_incidents
                )
                if ensemble_prediction.probability > 0.4:
                    predictions.insert(0, ensemble_prediction)
            
            # Sort by probability (highest first)
            predictions.sort(key=lambda p: p.probability, reverse=True)
            
            return predictions[:5]  # Return top 5 predictions
            
        except Exception as e:
            logger.error(f"Error predicting incidents: {e}")
            return []
    
    async def _forecast_metric_values(
        self, 
        trend_data: TrendData, 
        seasonal_decomp: Dict[str, np.ndarray]
    ) -> Dict[str, Any]:
        """Forecast future metric values using trend and seasonal components"""
        try:
            if len(trend_data.values) < 10:
                return {"forecast_values": [], "confidence_intervals": []}
            
            # Extract components
            trend = seasonal_decomp["trend"]
            seasonal = seasonal_decomp["seasonal"]
            residual = seasonal_decomp["residual"]
            
            # Forecast trend component
            forecast_steps = 6  # 30 minutes in 5-minute intervals
            trend_forecast = await self._forecast_trend_component(trend, forecast_steps)
            
            # Forecast seasonal component
            seasonal_forecast = await self._forecast_seasonal_component(
                seasonal, forecast_steps, len(trend_data.values)
            )
            
            # Estimate residual variance for confidence intervals
            residual_std = np.std(residual) if len(residual) > 0 else 0.1
            
            # Combine forecasts
            forecast_values = trend_forecast + seasonal_forecast
            
            # Calculate confidence intervals (95%)
            confidence_intervals = []
            for i, forecast_val in enumerate(forecast_values):
                # Confidence interval widens with forecast horizon
                interval_width = residual_std * 1.96 * np.sqrt(i + 1)
                confidence_intervals.append({
                    "lower": forecast_val - interval_width,
                    "upper": forecast_val + interval_width,
                    "width": interval_width * 2
                })
            
            return {
                "forecast_values": forecast_values.tolist(),
                "confidence_intervals": confidence_intervals,
                "trend_component": trend_forecast.tolist(),
                "seasonal_component": seasonal_forecast.tolist(),
                "residual_std": residual_std
            }
            
        except Exception as e:
            logger.error(f"Error forecasting metric values: {e}")
            return {"forecast_values": [], "confidence_intervals": []}
    
    async def _forecast_trend_component(self, trend: np.ndarray, steps: int) -> np.ndarray:
        """Forecast trend component using linear extrapolation"""
        try:
            if len(trend) < 2:
                return np.zeros(steps)
            
            # Use last few points to estimate trend slope
            recent_points = min(12, len(trend))  # Last hour of data
            x = np.arange(recent_points)
            y = trend[-recent_points:]
            
            # Linear regression for trend
            coeffs = np.polyfit(x, y, 1)
            slope, intercept = coeffs
            
            # Extrapolate trend
            future_x = np.arange(len(trend), len(trend) + steps)
            trend_forecast = slope * future_x + intercept
            
            return trend_forecast
            
        except Exception as e:
            logger.error(f"Error forecasting trend component: {e}")
            return np.zeros(steps)
    
    async def _forecast_seasonal_component(
        self, 
        seasonal: np.ndarray, 
        steps: int, 
        current_position: int
    ) -> np.ndarray:
        """Forecast seasonal component by repeating pattern"""
        try:
            if len(seasonal) == 0:
                return np.zeros(steps)
            
            seasonal_period = 24  # Daily pattern
            seasonal_forecast = np.zeros(steps)
            
            for i in range(steps):
                # Find corresponding seasonal position
                seasonal_idx = (current_position + i) % seasonal_period
                if seasonal_idx < len(seasonal):
                    seasonal_forecast[i] = seasonal[seasonal_idx]
                else:
                    # Use average seasonal value if index out of bounds
                    seasonal_forecast[i] = np.mean(seasonal)
            
            return seasonal_forecast
            
        except Exception as e:
            logger.error(f"Error forecasting seasonal component: {e}")
            return np.zeros(steps)
    
    async def _calculate_enhanced_prediction_probability(
        self,
        metric_name: str,
        trend_analysis: Dict[str, float],
        seasonal_decomp: Dict[str, np.ndarray],
        forecast_results: Dict[str, Any],
        monte_carlo_results: Dict[str, float],
        historical_incidents: List[Incident]
    ) -> float:
        """Calculate enhanced incident prediction probability with multiple factors"""
        try:
            # Base probability from trend analysis (30%)
            trend_prob = (
                trend_analysis.get("trend_score", 0) * 0.4 +
                trend_analysis.get("anomaly_score", 0) * 0.4 +
                trend_analysis.get("seasonal_score", 0) * 0.2
            ) * 0.3
            
            # Seasonal strength factor (20%)
            seasonal_strength = seasonal_decomp.get("seasonal_strength", 0)
            seasonal_prob = min(seasonal_strength * 2, 1.0) * 0.2
            
            # Forecast confidence factor (25%)
            forecast_prob = 0.0
            if forecast_results.get("forecast_values"):
                forecast_values = forecast_results["forecast_values"]
                confidence_intervals = forecast_results.get("confidence_intervals", [])
                
                # Check if forecast shows concerning trends
                if len(forecast_values) > 0:
                    current_val = forecast_values[0] if len(forecast_values) > 0 else 0
                    future_val = forecast_values[-1] if len(forecast_values) > 0 else 0
                    
                    # Calculate rate of change in forecast
                    if current_val > 0:
                        change_rate = abs(future_val - current_val) / current_val
                        forecast_prob = min(change_rate, 1.0) * 0.25
                    
                    # Adjust based on confidence interval width
                    if confidence_intervals:
                        avg_width = np.mean([ci["width"] for ci in confidence_intervals])
                        # Wider intervals reduce confidence
                        confidence_factor = max(0.5, 1.0 - avg_width / 100.0)
                        forecast_prob *= confidence_factor
            
            # Monte Carlo risk factor (15%)
            mc_prob = monte_carlo_results.get("mean_risk", 0) * 0.15
            
            # Historical pattern factor (10%)
            historical_factor = await self._get_historical_factor(metric_name, historical_incidents)
            historical_prob = (historical_factor - 1.0) * 0.1  # Convert factor to probability component
            
            # Combine all factors
            total_prob = trend_prob + seasonal_prob + forecast_prob + mc_prob + historical_prob
            
            # Apply metric importance weighting
            weight = self.model_weights.get(metric_name, 0.1)
            weighted_prob = total_prob * (0.5 + weight)  # Base 0.5 + metric weight
            
            return min(weighted_prob, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating enhanced prediction probability: {e}")
            return 0.0
    
    async def _create_ensemble_prediction(
        self,
        individual_predictions: List[PredictionResult],
        monte_carlo_results: Dict[str, float],
        historical_incidents: List[Incident]
    ) -> PredictionResult:
        """Create ensemble prediction combining multiple metric predictions"""
        try:
            if not individual_predictions:
                return None
            
            # Calculate ensemble probability using weighted voting
            total_weight = 0.0
            weighted_prob_sum = 0.0
            
            for pred in individual_predictions:
                # Weight by confidence and probability
                weight = pred.confidence * pred.probability
                weighted_prob_sum += pred.probability * weight
                total_weight += weight
            
            ensemble_prob = weighted_prob_sum / total_weight if total_weight > 0 else 0.0
            
            # Boost probability if Monte Carlo shows high risk
            mc_boost = monte_carlo_results.get("probability_high_risk", 0) * 0.2
            ensemble_prob = min(ensemble_prob + mc_boost, 1.0)
            
            # Determine dominant incident type
            incident_types = [pred.incident_type for pred in individual_predictions]
            dominant_type = max(set(incident_types), key=incident_types.count)
            
            # Combine risk factors
            all_risk_factors = []
            for pred in individual_predictions:
                all_risk_factors.extend(pred.risk_factors)
            
            # Remove duplicates and take top factors
            unique_factors = list(dict.fromkeys(all_risk_factors))[:5]
            
            # Combine preventive actions
            all_actions = []
            for pred in individual_predictions:
                all_actions.extend(pred.preventive_actions)
            
            unique_actions = list(dict.fromkeys(all_actions))[:5]
            
            # Calculate ensemble business impact
            max_impact = max(pred.business_impact for pred in individual_predictions)
            ensemble_impact = max_impact * ensemble_prob
            
            # Determine time to incident (minimum from all predictions)
            min_time = min(pred.time_to_incident for pred in individual_predictions)
            
            return PredictionResult(
                incident_type=f"ensemble_{dominant_type}",
                probability=ensemble_prob,
                confidence=min(ensemble_prob * 1.1, 1.0),
                time_to_incident=min_time,
                risk_factors=unique_factors,
                preventive_actions=unique_actions,
                business_impact=ensemble_impact,
                prediction_horizon=self._determine_prediction_horizon(min_time)
            )
            
        except Exception as e:
            logger.error(f"Error creating ensemble prediction: {e}")
            return None
    
    async def _get_historical_factor(
        self, 
        metric_name: str, 
        historical_incidents: List[Incident]
    ) -> float:
        """Get historical factor based on past incidents"""
        try:
            if not historical_incidents:
                return 1.0
            
            # Count incidents related to this metric type
            related_incidents = 0
            total_incidents = len(historical_incidents)
            
            for incident in historical_incidents:
                if metric_name in incident.description.lower():
                    related_incidents += 1
            
            if total_incidents > 0:
                # Higher factor if this metric has caused incidents before
                factor = 1.0 + (related_incidents / total_incidents)
                return min(factor, 2.0)
            
            return 1.0
            
        except Exception as e:
            logger.error(f"Error calculating historical factor: {e}")
            return 1.0
    
    async def _create_enhanced_prediction_result(
        self,
        metric_name: str,
        probability: float,
        trend_analysis: Dict[str, float],
        seasonal_decomp: Dict[str, np.ndarray],
        forecast_results: Dict[str, Any],
        monte_carlo_results: Dict[str, float],
        historical_incidents: List[Incident]
    ) -> PredictionResult:
        """Create an enhanced prediction result object with forecasting data"""
        try:
            # Determine incident type based on metric
            incident_type = self._map_metric_to_incident_type(metric_name)
            
            # Enhanced confidence calculation
            confidence = await self._calculate_enhanced_confidence(
                probability, trend_analysis, seasonal_decomp, 
                forecast_results, monte_carlo_results
            )
            
            # Enhanced time to incident estimation
            time_to_incident = await self._estimate_enhanced_time_to_incident(
                probability, forecast_results, monte_carlo_results
            )
            
            # Enhanced risk factors generation
            risk_factors = await self._generate_enhanced_risk_factors(
                metric_name, trend_analysis, seasonal_decomp, 
                forecast_results, monte_carlo_results
            )
            
            # Generate preventive actions (enhanced with forecast data)
            preventive_actions = await self._generate_enhanced_preventive_actions(
                incident_type, forecast_results, monte_carlo_results
            )
            
            # Enhanced business impact estimation
            business_impact = await self._estimate_enhanced_business_impact(
                incident_type, probability, time_to_incident, monte_carlo_results
            )
            
            # Determine prediction horizon
            horizon = self._determine_prediction_horizon(time_to_incident)
            
            return PredictionResult(
                incident_type=incident_type,
                probability=probability,
                confidence=confidence,
                time_to_incident=time_to_incident,
                risk_factors=risk_factors,
                preventive_actions=preventive_actions,
                business_impact=business_impact,
                prediction_horizon=horizon
            )
            
        except Exception as e:
            logger.error(f"Error creating prediction result: {e}")
            return PredictionResult(
                incident_type="unknown",
                probability=0.0,
                confidence=0.0,
                time_to_incident=timedelta(hours=1),
                risk_factors=[],
                preventive_actions=[],
                business_impact=0.0,
                prediction_horizon=PredictionHorizon.LONG_TERM
            )
    
    async def _calculate_enhanced_confidence(
        self,
        probability: float,
        trend_analysis: Dict[str, float],
        seasonal_decomp: Dict[str, np.ndarray],
        forecast_results: Dict[str, Any],
        monte_carlo_results: Dict[str, float]
    ) -> float:
        """Calculate enhanced confidence based on multiple factors"""
        try:
            base_confidence = probability * 0.9  # Start conservative
            
            # Boost confidence if trend is strong
            trend_strength = trend_analysis.get("trend_strength", 0)
            if trend_strength > 0.7:
                base_confidence += 0.1
            
            # Boost confidence if seasonal pattern is strong
            seasonal_strength = seasonal_decomp.get("seasonal_strength", 0)
            if seasonal_strength > 0.5:
                base_confidence += 0.05
            
            # Reduce confidence if forecast has wide intervals
            if forecast_results.get("confidence_intervals"):
                avg_width = np.mean([ci["width"] for ci in forecast_results["confidence_intervals"]])
                if avg_width > 50:  # Wide intervals reduce confidence
                    base_confidence -= 0.1
            
            # Boost confidence if Monte Carlo shows consistent risk
            mc_std = monte_carlo_results.get("std_risk", 1.0)
            if mc_std < 0.2:  # Low variance in simulations
                base_confidence += 0.05
            
            return min(max(base_confidence, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating enhanced confidence: {e}")
            return probability * 0.8
    
    async def _estimate_enhanced_time_to_incident(
        self,
        probability: float,
        forecast_results: Dict[str, Any],
        monte_carlo_results: Dict[str, float]
    ) -> timedelta:
        """Estimate time to incident using forecast data"""
        try:
            # Base estimation
            if probability > 0.9:
                base_time = timedelta(minutes=10)
            elif probability > 0.8:
                base_time = timedelta(minutes=15)
            elif probability > 0.6:
                base_time = timedelta(minutes=25)
            else:
                base_time = timedelta(minutes=45)
            
            # Adjust based on forecast trend
            if forecast_results.get("forecast_values"):
                forecast_values = forecast_results["forecast_values"]
                if len(forecast_values) >= 2:
                    # Check rate of change in forecast
                    initial_val = forecast_values[0]
                    final_val = forecast_values[-1]
                    
                    if initial_val > 0:
                        change_rate = (final_val - initial_val) / initial_val
                        if change_rate > 0.5:  # Rapid increase
                            base_time = timedelta(minutes=max(5, base_time.total_seconds() / 60 - 10))
                        elif change_rate < -0.2:  # Decreasing trend
                            base_time = timedelta(minutes=min(60, base_time.total_seconds() / 60 + 15))
            
            # Adjust based on Monte Carlo percentiles
            percentile_99 = monte_carlo_results.get("percentile_99", 0)
            if percentile_99 > 0.95:  # Very high risk in simulations
                base_time = timedelta(minutes=max(5, base_time.total_seconds() / 60 - 5))
            
            return base_time
            
        except Exception as e:
            logger.error(f"Error estimating enhanced time to incident: {e}")
            return timedelta(minutes=30)
    
    async def _generate_enhanced_risk_factors(
        self,
        metric_name: str,
        trend_analysis: Dict[str, float],
        seasonal_decomp: Dict[str, np.ndarray],
        forecast_results: Dict[str, Any],
        monte_carlo_results: Dict[str, float]
    ) -> List[str]:
        """Generate enhanced risk factors with forecast insights"""
        try:
            factors = []
            
            # Traditional risk factors
            if trend_analysis.get("trend_score", 0) > 0.7:
                factors.append(f"Rapidly increasing {metric_name}")
            
            if trend_analysis.get("anomaly_score", 0) > 0.7:
                factors.append(f"Anomalous {metric_name} patterns detected")
            
            # Seasonal risk factors
            seasonal_strength = seasonal_decomp.get("seasonal_strength", 0)
            if seasonal_strength > 0.6:
                factors.append(f"Strong seasonal deviation in {metric_name}")
            
            # Forecast-based risk factors
            if forecast_results.get("forecast_values"):
                forecast_values = forecast_results["forecast_values"]
                if len(forecast_values) > 0:
                    max_forecast = max(forecast_values)
                    if "cpu" in metric_name.lower() and max_forecast > 90:
                        factors.append("Forecast shows CPU approaching critical levels")
                    elif "memory" in metric_name.lower() and max_forecast > 85:
                        factors.append("Forecast shows memory exhaustion risk")
                    elif "error" in metric_name.lower() and max_forecast > 0.1:
                        factors.append("Forecast shows increasing error rates")
            
            # Monte Carlo risk factors
            prob_high_risk = monte_carlo_results.get("probability_high_risk", 0)
            if prob_high_risk > 0.7:
                factors.append(f"Monte Carlo simulation shows {prob_high_risk:.0%} chance of high-risk scenario")
            
            prob_critical = monte_carlo_results.get("probability_critical_risk", 0)
            if prob_critical > 0.3:
                factors.append(f"Monte Carlo simulation shows {prob_critical:.0%} chance of critical scenario")
            
            return factors[:5]  # Limit to top 5 factors
            
        except Exception as e:
            logger.error(f"Error generating enhanced risk factors: {e}")
            return [f"Risk detected in {metric_name}"]
    
    async def _generate_enhanced_preventive_actions(
        self,
        incident_type: str,
        forecast_results: Dict[str, Any],
        monte_carlo_results: Dict[str, float]
    ) -> List[str]:
        """Generate enhanced preventive actions based on forecast data"""
        try:
            # Base actions
            base_actions = self._generate_preventive_actions(incident_type)
            
            # Enhanced actions based on forecast
            enhanced_actions = base_actions.copy()
            
            # Add urgency-based actions
            prob_critical = monte_carlo_results.get("probability_critical_risk", 0)
            if prob_critical > 0.5:
                enhanced_actions.insert(0, "Immediate escalation to senior SRE team")
                enhanced_actions.insert(1, "Activate emergency response procedures")
            
            # Add forecast-specific actions
            if forecast_results.get("forecast_values"):
                forecast_trend = forecast_results.get("trend_component", [])
                if len(forecast_trend) > 1 and forecast_trend[-1] > forecast_trend[0]:
                    enhanced_actions.append("Implement proactive scaling before threshold breach")
            
            return enhanced_actions[:5]  # Limit to top 5 actions
            
        except Exception as e:
            logger.error(f"Error generating enhanced preventive actions: {e}")
            return self._generate_preventive_actions(incident_type)
    
    async def _estimate_enhanced_business_impact(
        self,
        incident_type: str,
        probability: float,
        time_to_incident: timedelta,
        monte_carlo_results: Dict[str, float]
    ) -> float:
        """Estimate enhanced business impact with time and risk factors"""
        try:
            # Base impact
            base_impact = self._estimate_business_impact(incident_type, probability)
            
            # Time urgency multiplier
            minutes_to_incident = time_to_incident.total_seconds() / 60
            if minutes_to_incident < 15:
                urgency_multiplier = 1.5  # 50% higher impact for urgent incidents
            elif minutes_to_incident < 30:
                urgency_multiplier = 1.2  # 20% higher impact
            else:
                urgency_multiplier = 1.0
            
            # Monte Carlo risk multiplier
            percentile_95 = monte_carlo_results.get("percentile_95", 0)
            if percentile_95 > 0.8:
                risk_multiplier = 1.3  # 30% higher impact for high-risk scenarios
            elif percentile_95 > 0.6:
                risk_multiplier = 1.1  # 10% higher impact
            else:
                risk_multiplier = 1.0
            
            enhanced_impact = base_impact * urgency_multiplier * risk_multiplier
            
            return enhanced_impact
            
        except Exception as e:
            logger.error(f"Error estimating enhanced business impact: {e}")
            return self._estimate_business_impact(incident_type, probability)
    
    def _map_metric_to_incident_type(self, metric_name: str) -> str:
        """Map metric name to incident type"""
        mapping = {
            "cpu_utilization": "cpu_exhaustion",
            "memory_utilization": "memory_leak",
            "error_rate": "service_degradation",
            "response_time": "performance_degradation",
            "disk_utilization": "storage_exhaustion"
        }
        return mapping.get(metric_name, "system_anomaly")
    
    def _estimate_time_to_incident(self, probability: float) -> timedelta:
        """Estimate time until incident occurs"""
        if probability > 0.8:
            return timedelta(minutes=15)
        elif probability > 0.6:
            return timedelta(minutes=30)
        else:
            return timedelta(minutes=60)
    
    def _generate_risk_factors(self, metric_name: str, trend_analysis: Dict[str, float]) -> List[str]:
        """Generate risk factors based on analysis"""
        factors = []
        
        if trend_analysis.get("trend_score", 0) > 0.7:
            factors.append(f"Rapidly increasing {metric_name}")
        
        if trend_analysis.get("anomaly_score", 0) > 0.7:
            factors.append(f"Anomalous {metric_name} patterns detected")
        
        if trend_analysis.get("seasonal_score", 0) > 0.7:
            factors.append(f"Unusual seasonal pattern in {metric_name}")
        
        return factors
    
    def _generate_preventive_actions(self, incident_type: str) -> List[str]:
        """Generate preventive actions for incident type"""
        actions = {
            "cpu_exhaustion": [
                "Scale up compute resources",
                "Optimize CPU-intensive processes",
                "Enable auto-scaling policies"
            ],
            "memory_leak": [
                "Restart affected services",
                "Increase memory allocation",
                "Deploy memory leak fixes"
            ],
            "service_degradation": [
                "Review recent deployments",
                "Check dependency health",
                "Enable circuit breakers"
            ],
            "performance_degradation": [
                "Optimize database queries",
                "Scale backend services",
                "Enable caching layers"
            ],
            "storage_exhaustion": [
                "Clean up temporary files",
                "Archive old data",
                "Expand storage capacity"
            ]
        }
        return actions.get(incident_type, ["Monitor system closely"])
    
    def _estimate_business_impact(self, incident_type: str, probability: float) -> float:
        """Estimate business impact in dollars per minute"""
        base_impacts = {
            "cpu_exhaustion": 500.0,
            "memory_leak": 300.0,
            "service_degradation": 800.0,
            "performance_degradation": 400.0,
            "storage_exhaustion": 600.0
        }
        
        base_impact = base_impacts.get(incident_type, 200.0)
        return base_impact * probability
    
    def _determine_prediction_horizon(self, time_to_incident: timedelta) -> PredictionHorizon:
        """Determine prediction horizon based on time estimate"""
        if time_to_incident <= timedelta(minutes=15):
            return PredictionHorizon.SHORT_TERM
        elif time_to_incident <= timedelta(minutes=30):
            return PredictionHorizon.MEDIUM_TERM
        else:
            return PredictionHorizon.LONG_TERM