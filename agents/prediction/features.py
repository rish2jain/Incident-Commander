"""
Feature Extraction for Prediction Agent

Extracts and processes features from monitoring data for incident prediction.
"""

import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from src.utils.logging import get_logger
from .models import TrendData

logger = get_logger(__name__)


@dataclass
class MetricFeatures:
    """Extracted features from a metric"""
    metric_name: str
    current_value: float
    mean_value: float
    std_deviation: float
    min_value: float
    max_value: float
    trend_slope: float
    volatility: float
    z_score: float
    percentile_95: float
    rate_of_change: float


class FeatureExtractor:
    """Extracts features from monitoring data for prediction models"""
    
    def __init__(self):
        self.feature_window = 24  # Hours of data to use for feature extraction
        self.min_data_points = 10  # Minimum data points required
        
    async def extract_features(
        self, 
        monitoring_data: Dict[str, Any]
    ) -> Dict[str, MetricFeatures]:
        """
        Extract features from monitoring data
        
        Args:
            monitoring_data: Raw monitoring data from various sources
            
        Returns:
            Dictionary of extracted features by metric name
        """
        try:
            features = {}
            
            # Process CloudWatch metrics
            if "cloudwatch" in monitoring_data:
                cw_features = await self._extract_cloudwatch_features(
                    monitoring_data["cloudwatch"]
                )
                features.update(cw_features)
            
            # Process Datadog metrics
            if "datadog" in monitoring_data:
                dd_features = await self._extract_datadog_features(
                    monitoring_data["datadog"]
                )
                features.update(dd_features)
            
            # Process application metrics
            if "application" in monitoring_data:
                app_features = await self._extract_application_features(
                    monitoring_data["application"]
                )
                features.update(app_features)
            
            logger.info(f"Extracted features for {len(features)} metrics")
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return {}
    
    async def _extract_cloudwatch_features(
        self, 
        cloudwatch_data: Dict[str, Any]
    ) -> Dict[str, MetricFeatures]:
        """Extract features from CloudWatch metrics"""
        try:
            features = {}
            
            for metric_name, metric_data in cloudwatch_data.items():
                if not self._validate_metric_data(metric_data):
                    continue
                
                trend_data = self._convert_to_trend_data(metric_name, metric_data)
                metric_features = await self._calculate_metric_features(trend_data)
                
                if metric_features:
                    features[f"cloudwatch_{metric_name}"] = metric_features
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting CloudWatch features: {e}")
            return {}
    
    async def _extract_datadog_features(
        self, 
        datadog_data: Dict[str, Any]
    ) -> Dict[str, MetricFeatures]:
        """Extract features from Datadog metrics"""
        try:
            features = {}
            
            for metric_name, metric_data in datadog_data.items():
                if not self._validate_metric_data(metric_data):
                    continue
                
                trend_data = self._convert_to_trend_data(metric_name, metric_data)
                metric_features = await self._calculate_metric_features(trend_data)
                
                if metric_features:
                    features[f"datadog_{metric_name}"] = metric_features
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting Datadog features: {e}")
            return {}
    
    async def _extract_application_features(
        self, 
        app_data: Dict[str, Any]
    ) -> Dict[str, MetricFeatures]:
        """Extract features from application metrics"""
        try:
            features = {}
            
            for metric_name, metric_data in app_data.items():
                if not self._validate_metric_data(metric_data):
                    continue
                
                trend_data = self._convert_to_trend_data(metric_name, metric_data)
                metric_features = await self._calculate_metric_features(trend_data)
                
                if metric_features:
                    features[f"app_{metric_name}"] = metric_features
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting application features: {e}")
            return {}
    
    def _validate_metric_data(self, metric_data: Any) -> bool:
        """Validate metric data has required structure"""
        try:
            if not isinstance(metric_data, dict):
                return False
            
            if "timestamps" not in metric_data or "values" not in metric_data:
                return False
            
            timestamps = metric_data["timestamps"]
            values = metric_data["values"]
            
            if not isinstance(timestamps, list) or not isinstance(values, list):
                return False
            
            if len(timestamps) != len(values):
                return False
            
            if len(values) < self.min_data_points:
                return False
            
            return True
            
        except Exception:
            return False
    
    def _convert_to_trend_data(self, metric_name: str, metric_data: Dict[str, Any]) -> TrendData:
        """Convert metric data to TrendData format"""
        try:
            timestamps = [
                datetime.fromisoformat(ts.replace('Z', '+00:00')) 
                if isinstance(ts, str) else ts
                for ts in metric_data["timestamps"]
            ]
            
            values = [float(v) for v in metric_data["values"]]
            service_name = metric_data.get("service", "unknown")
            
            return TrendData(
                timestamps=timestamps,
                values=values,
                metric_name=metric_name,
                service_name=service_name
            )
            
        except Exception as e:
            logger.error(f"Error converting to trend data: {e}")
            return TrendData(
                timestamps=[],
                values=[],
                metric_name=metric_name,
                service_name="unknown"
            )
    
    async def _calculate_metric_features(self, trend_data: TrendData) -> Optional[MetricFeatures]:
        """Calculate statistical features for a metric"""
        try:
            if len(trend_data.values) < self.min_data_points:
                return None
            
            values = np.array(trend_data.values)
            
            # Basic statistical features
            current_value = values[-1]
            mean_value = np.mean(values)
            std_deviation = np.std(values)
            min_value = np.min(values)
            max_value = np.max(values)
            
            # Trend analysis
            trend_slope = await self._calculate_trend_slope(values)
            
            # Volatility (coefficient of variation)
            volatility = std_deviation / mean_value if mean_value != 0 else 0
            
            # Z-score of current value
            z_score = (current_value - mean_value) / std_deviation if std_deviation != 0 else 0
            
            # 95th percentile
            percentile_95 = np.percentile(values, 95)
            
            # Rate of change (recent vs historical)
            rate_of_change = await self._calculate_rate_of_change(values)
            
            return MetricFeatures(
                metric_name=trend_data.metric_name,
                current_value=current_value,
                mean_value=mean_value,
                std_deviation=std_deviation,
                min_value=min_value,
                max_value=max_value,
                trend_slope=trend_slope,
                volatility=volatility,
                z_score=z_score,
                percentile_95=percentile_95,
                rate_of_change=rate_of_change
            )
            
        except Exception as e:
            logger.error(f"Error calculating metric features for {trend_data.metric_name}: {e}")
            return None
    
    async def _calculate_trend_slope(self, values: np.ndarray) -> float:
        """Calculate trend slope using linear regression"""
        try:
            x = np.arange(len(values))
            coeffs = np.polyfit(x, values, 1)
            return float(coeffs[0])
            
        except Exception as e:
            logger.error(f"Error calculating trend slope: {e}")
            return 0.0
    
    async def _calculate_rate_of_change(self, values: np.ndarray) -> float:
        """Calculate rate of change between recent and historical values"""
        try:
            if len(values) < 10:
                return 0.0
            
            # Compare last 25% of data with first 25%
            split_point = len(values) // 4
            historical_mean = np.mean(values[:split_point])
            recent_mean = np.mean(values[-split_point:])
            
            if historical_mean != 0:
                return (recent_mean - historical_mean) / historical_mean
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating rate of change: {e}")
            return 0.0
    
    async def create_feature_vector(
        self, 
        features: Dict[str, MetricFeatures]
    ) -> np.ndarray:
        """
        Create a feature vector for machine learning models
        
        Args:
            features: Dictionary of metric features
            
        Returns:
            Numpy array of normalized features
        """
        try:
            if not features:
                return np.array([])
            
            # Define feature order for consistency
            feature_names = [
                "current_value", "mean_value", "std_deviation",
                "trend_slope", "volatility", "z_score", "rate_of_change"
            ]
            
            feature_vector = []
            
            for metric_name, metric_features in features.items():
                for feature_name in feature_names:
                    value = getattr(metric_features, feature_name, 0.0)
                    feature_vector.append(float(value))
            
            # Normalize features to [0, 1] range
            feature_array = np.array(feature_vector)
            if len(feature_array) > 0:
                # Simple min-max normalization
                min_val = np.min(feature_array)
                max_val = np.max(feature_array)
                
                if max_val != min_val:
                    feature_array = (feature_array - min_val) / (max_val - min_val)
                else:
                    feature_array = np.zeros_like(feature_array)
            
            return feature_array
            
        except Exception as e:
            logger.error(f"Error creating feature vector: {e}")
            return np.array([])
    
    async def get_feature_importance(
        self, 
        features: Dict[str, MetricFeatures]
    ) -> Dict[str, float]:
        """
        Calculate feature importance scores
        
        Args:
            features: Dictionary of metric features
            
        Returns:
            Dictionary of feature importance scores
        """
        try:
            importance_scores = {}
            
            for metric_name, metric_features in features.items():
                # Calculate importance based on statistical significance
                importance = 0.0
                
                # Z-score importance (higher absolute z-score = more important)
                importance += min(abs(metric_features.z_score) / 3.0, 1.0) * 0.3
                
                # Trend importance (steeper trend = more important)
                if metric_features.mean_value != 0:
                    normalized_slope = abs(metric_features.trend_slope) / metric_features.mean_value
                    importance += min(normalized_slope, 1.0) * 0.3
                
                # Volatility importance (higher volatility = more important)
                importance += min(metric_features.volatility, 1.0) * 0.2
                
                # Rate of change importance
                importance += min(abs(metric_features.rate_of_change), 1.0) * 0.2
                
                importance_scores[metric_name] = min(importance, 1.0)
            
            return importance_scores
            
        except Exception as e:
            logger.error(f"Error calculating feature importance: {e}")
            return {}