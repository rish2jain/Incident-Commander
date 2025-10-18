"""
Monitoring Data Source Interface

Provides interface for monitoring data sources used by detection agents.
This is a minimal implementation to support the detection accuracy testing framework.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from datetime import datetime


class MonitoringDataSource(ABC):
    """Abstract base class for monitoring data sources."""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    async def get_recent_alerts(self, time_window_minutes: int = 15) -> List[Dict[str, Any]]:
        """
        Get recent alerts from this monitoring source.
        
        Args:
            time_window_minutes: Time window to look back for alerts
            
        Returns:
            List of alert dictionaries with standardized format
        """
        pass
    
    @abstractmethod
    async def get_metrics(self, metric_name: str, time_window_minutes: int = 15) -> List[Dict[str, Any]]:
        """
        Get metric data from this monitoring source.
        
        Args:
            metric_name: Name of the metric to retrieve
            time_window_minutes: Time window to look back
            
        Returns:
            List of metric data points
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if this monitoring source is healthy and accessible."""
        pass


class CloudWatchDataSource(MonitoringDataSource):
    """CloudWatch monitoring data source."""
    
    def __init__(self):
        super().__init__("cloudwatch")
    
    async def get_recent_alerts(self, time_window_minutes: int = 15) -> List[Dict[str, Any]]:
        """Get recent CloudWatch alarms."""
        # TODO: Implement CloudWatch integration
        return []
    
    async def get_metrics(self, metric_name: str, time_window_minutes: int = 15) -> List[Dict[str, Any]]:
        """Get CloudWatch metrics."""
        # TODO: Implement CloudWatch metrics retrieval
        return []
    
    async def health_check(self) -> bool:
        """Check CloudWatch connectivity."""
        # TODO: Implement health check
        return True


class DatadogDataSource(MonitoringDataSource):
    """Datadog monitoring data source."""
    
    def __init__(self):
        super().__init__("datadog")
    
    async def get_recent_alerts(self, time_window_minutes: int = 15) -> List[Dict[str, Any]]:
        """Get recent Datadog alerts."""
        # TODO: Implement Datadog integration
        return []
    
    async def get_metrics(self, metric_name: str, time_window_minutes: int = 15) -> List[Dict[str, Any]]:
        """Get Datadog metrics."""
        # TODO: Implement Datadog metrics retrieval
        return []
    
    async def health_check(self) -> bool:
        """Check Datadog connectivity."""
        # TODO: Implement health check
        return True


class PrometheusDataSource(MonitoringDataSource):
    """Prometheus monitoring data source."""
    
    def __init__(self):
        super().__init__("prometheus")
    
    async def get_recent_alerts(self, time_window_minutes: int = 15) -> List[Dict[str, Any]]:
        """Get recent Prometheus alerts."""
        # TODO: Implement Prometheus integration
        return []
    
    async def get_metrics(self, metric_name: str, time_window_minutes: int = 15) -> List[Dict[str, Any]]:
        """Get Prometheus metrics."""
        # TODO: Implement Prometheus metrics retrieval
        return []
    
    async def health_check(self) -> bool:
        """Check Prometheus connectivity."""
        # TODO: Implement health check
        return True