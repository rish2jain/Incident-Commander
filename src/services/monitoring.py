"""
Monitoring Data Source Interface

Provides interface for monitoring data sources used by detection agents.
This is a minimal implementation to support the detection accuracy testing framework.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import os
import asyncio
import aiohttp


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

    def __init__(self, region: str = "us-east-1"):
        super().__init__("cloudwatch")
        self.region = region
        self._client = None

    def _get_boto3_client(self):
        """Get or create boto3 CloudWatch client."""
        if self._client is None:
            try:
                import boto3
                self._client = boto3.client('cloudwatch', region_name=self.region)
            except ImportError:
                raise ImportError("boto3 is required for CloudWatch integration. Install with: pip install boto3")
        return self._client

    async def get_recent_alerts(self, time_window_minutes: int = 15) -> List[Dict[str, Any]]:
        """Get recent CloudWatch alarms."""
        try:
            client = self._get_boto3_client()
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=time_window_minutes)

            # Get alarm history
            response = client.describe_alarm_history(
                StartDate=start_time,
                EndDate=end_time,
                HistoryItemType='StateUpdate',
                MaxRecords=100
            )

            alerts = []
            for item in response.get('AlarmHistoryItems', []):
                if item.get('HistorySummary', '').startswith('Alarm updated'):
                    alerts.append({
                        'timestamp': item['Timestamp'],
                        'alarm_name': item['AlarmName'],
                        'summary': item.get('HistorySummary', ''),
                        'source': 'cloudwatch',
                        'severity': 'high' if 'ALARM' in item.get('HistorySummary', '') else 'info'
                    })

            return alerts
        except Exception as e:
            logger.error(f"Error fetching CloudWatch alerts: {e}")
            return []

    async def get_metrics(self, metric_name: str, time_window_minutes: int = 15) -> List[Dict[str, Any]]:
        """Get CloudWatch metrics."""
        try:
            client = self._get_boto3_client()
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=time_window_minutes)

            # Parse metric name (format: namespace/metric_name)
            parts = metric_name.split('/')
            namespace = parts[0] if len(parts) > 1 else 'AWS/EC2'
            metric = parts[1] if len(parts) > 1 else metric_name

            response = client.get_metric_statistics(
                Namespace=namespace,
                MetricName=metric,
                StartTime=start_time,
                EndTime=end_time,
                Period=60,  # 1 minute intervals
                Statistics=['Average', 'Maximum', 'Minimum']
            )

            metrics = []
            for datapoint in response.get('Datapoints', []):
                metrics.append({
                    'timestamp': datapoint['Timestamp'],
                    'metric_name': metric,
                    'average': datapoint.get('Average', 0),
                    'maximum': datapoint.get('Maximum', 0),
                    'minimum': datapoint.get('Minimum', 0),
                    'unit': datapoint.get('Unit', ''),
                    'source': 'cloudwatch'
                })

            return sorted(metrics, key=lambda x: x['timestamp'])
        except Exception as e:
            print(f"Error fetching CloudWatch metrics: {e}")
            return []

    async def health_check(self) -> bool:
        """Check CloudWatch connectivity."""
        try:
            client = self._get_boto3_client()
            # Simple test: list alarms (limit to 1 to minimize overhead)
            client.describe_alarms(MaxRecords=1)
            return True
        except Exception as e:
            print(f"CloudWatch health check failed: {e}")
            return False


class DatadogDataSource(MonitoringDataSource):
    """Datadog monitoring data source."""

    def __init__(self, api_key: Optional[str] = None, app_key: Optional[str] = None):
        super().__init__("datadog")
        self.api_key = api_key or os.getenv('DATADOG_API_KEY')
        self.app_key = app_key or os.getenv('DATADOG_APP_KEY')
        self.base_url = "https://api.datadoghq.com/api/v1"

    def _get_headers(self) -> Dict[str, str]:
        """Get authentication headers for Datadog API."""
        return {
            'DD-API-KEY': self.api_key,
            'DD-APPLICATION-KEY': self.app_key,
            'Content-Type': 'application/json'
        }

    async def get_recent_alerts(self, time_window_minutes: int = 15) -> List[Dict[str, Any]]:
        """Get recent Datadog alerts."""
        if not self.api_key or not self.app_key:
            print("Datadog API credentials not configured")
            return []

        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=time_window_minutes)

            async with aiohttp.ClientSession() as session:
                # Get monitor states
                url = f"{self.base_url}/monitor"
                async with session.get(url, headers=self._get_headers()) as response:
                    if response.status != 200:
                        logger.error(f"Datadog API error: {response.status}")
                        return []

                    monitors = await response.json()

            alerts = []
            for monitor in monitors:
                # Check if monitor is in alert state
                if monitor.get('overall_state') in ['Alert', 'Warn', 'No Data']:
                    # Get last triggered time
                    last_triggered = monitor.get('overall_state_modified')
                    if last_triggered:
                        triggered_dt = datetime.fromtimestamp(last_triggered)
                        if triggered_dt >= start_time:
                            alerts.append({
                                'timestamp': triggered_dt,
                                'monitor_id': monitor.get('id'),
                                'monitor_name': monitor.get('name', ''),
                                'state': monitor.get('overall_state', ''),
                                'message': monitor.get('message', ''),
                                'source': 'datadog',
                                'severity': 'high' if monitor.get('overall_state') == 'Alert' else 'medium'
                            })

            return sorted(alerts, key=lambda x: x['timestamp'], reverse=True)
        except Exception as e:
            print(f"Error fetching Datadog alerts: {e}")
            return []

    async def get_metrics(self, metric_name: str, time_window_minutes: int = 15) -> List[Dict[str, Any]]:
        """Get Datadog metrics."""
        if not self.api_key or not self.app_key:
            print("Datadog API credentials not configured")
            return []

        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=time_window_minutes)

            # Convert to Unix timestamps
            from_ts = int(start_time.timestamp())
            to_ts = int(end_time.timestamp())

            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/query"
                params = {
                    'query': metric_name,
                    'from': from_ts,
                    'to': to_ts
                }

                async with session.get(url, headers=self._get_headers(), params=params) as response:
                    if response.status != 200:
                        logger.error(f"Datadog metrics API error: {response.status}")
                        return []

                    data = await response.json()

            metrics = []
            for series in data.get('series', []):
                for point in series.get('pointlist', []):
                    timestamp, value = point
                    metrics.append({
                        'timestamp': datetime.fromtimestamp(timestamp / 1000),  # Datadog uses ms
                        'metric_name': series.get('metric', metric_name),
                        'value': value,
                        'tags': series.get('tag_set', []),
                        'source': 'datadog'
                    })

            return sorted(metrics, key=lambda x: x['timestamp'])
        except Exception as e:
            print(f"Error fetching Datadog metrics: {e}")
            return []

    async def health_check(self) -> bool:
        """Check Datadog connectivity."""
        if not self.api_key or not self.app_key:
            return False

        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/validate"
                async with session.get(url, headers=self._get_headers()) as response:
                    return response.status == 200
        except Exception as e:
            print(f"Datadog health check failed: {e}")
            return False


class PrometheusDataSource(MonitoringDataSource):
    """Prometheus monitoring data source."""

    def __init__(self, prometheus_url: Optional[str] = None):
        super().__init__("prometheus")
        self.prometheus_url = prometheus_url or os.getenv('PROMETHEUS_URL', 'http://localhost:9090')
        self.api_base = f"{self.prometheus_url}/api/v1"

    async def get_recent_alerts(self, time_window_minutes: int = 15) -> List[Dict[str, Any]]:
        """Get recent Prometheus alerts."""
        try:
            async with aiohttp.ClientSession() as session:
                # Get active alerts from Alertmanager
                url = f"{self.api_base}/alerts"
                async with session.get(url) as response:
                    if response.status != 200:
                        print(f"Prometheus alerts API error: {response.status}")
                        return []

                    data = await response.json()

            if data.get('status') != 'success':
                print(f"Prometheus API returned non-success status")
                return []

            alerts = []
            current_time = datetime.utcnow()
            cutoff_time = current_time - timedelta(minutes=time_window_minutes)

            for alert in data.get('data', {}).get('alerts', []):
                # Parse active time
                active_at_str = alert.get('activeAt', '')
                if active_at_str:
                    try:
                        active_at = datetime.fromisoformat(active_at_str.replace('Z', '+00:00'))
                        if active_at >= cutoff_time:
                            labels = alert.get('labels', {})
                            annotations = alert.get('annotations', {})

                            alerts.append({
                                'timestamp': active_at,
                                'alert_name': labels.get('alertname', 'Unknown'),
                                'severity': labels.get('severity', 'info'),
                                'instance': labels.get('instance', ''),
                                'summary': annotations.get('summary', ''),
                                'description': annotations.get('description', ''),
                                'state': alert.get('state', 'firing'),
                                'source': 'prometheus',
                                'labels': labels
                            })
                    except (ValueError, TypeError):
                        continue

            return sorted(alerts, key=lambda x: x['timestamp'], reverse=True)
        except Exception as e:
            print(f"Error fetching Prometheus alerts: {e}")
            return []

    async def get_metrics(self, metric_name: str, time_window_minutes: int = 15) -> List[Dict[str, Any]]:
        """Get Prometheus metrics."""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=time_window_minutes)

            async with aiohttp.ClientSession() as session:
                # Query range for time series data
                url = f"{self.api_base}/query_range"
                params = {
                    'query': metric_name,
                    'start': start_time.timestamp(),
                    'end': end_time.timestamp(),
                    'step': '60s'  # 1 minute resolution
                }

                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        print(f"Prometheus query API error: {response.status}")
                        return []

                    data = await response.json()

            if data.get('status') != 'success':
                print(f"Prometheus query returned non-success status")
                return []

            metrics = []
            for result in data.get('data', {}).get('result', []):
                metric_labels = result.get('metric', {})
                values = result.get('values', [])

                for timestamp, value in values:
                    try:
                        metrics.append({
                            'timestamp': datetime.fromtimestamp(float(timestamp)),
                            'metric_name': metric_name,
                            'value': float(value),
                            'labels': metric_labels,
                            'source': 'prometheus'
                        })
                    except (ValueError, TypeError):
                        continue

            return sorted(metrics, key=lambda x: x['timestamp'])
        except Exception as e:
            print(f"Error fetching Prometheus metrics: {e}")
            return []

    async def health_check(self) -> bool:
        """Check Prometheus connectivity."""
        try:
            async with aiohttp.ClientSession() as session:
                # Simple query to test connectivity
                url = f"{self.api_base}/query"
                params = {'query': 'up'}
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('status') == 'success'
                    return False
        except Exception as e:
            print(f"Prometheus health check failed: {e}")
            return False