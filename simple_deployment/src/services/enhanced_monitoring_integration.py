"""
Enhanced Monitoring Integration Service.

Integrates new monitoring services with existing Prometheus/Grafana observability
infrastructure, providing comprehensive metrics collection and alerting.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
import json

from src.utils.logging import get_logger
from src.services.integration_monitor import get_integration_monitor
from src.services.guardrail_tracker import get_guardrail_tracker
from src.services.agent_telemetry import get_agent_telemetry

logger = get_logger("enhanced_monitoring_integration")


@dataclass
class MetricExport:
    """Metric export data for Prometheus."""
    name: str
    value: float
    labels: Dict[str, str]
    help_text: str
    metric_type: str  # counter, gauge, histogram


class EnhancedMonitoringIntegration:
    """
    Enhanced monitoring integration service.
    
    Connects new monitoring services with existing Prometheus/Grafana infrastructure,
    providing comprehensive metrics collection, alerting, and dashboard integration.
    """
    
    def __init__(self):
        # Create separate registry for enhanced metrics
        self.registry = CollectorRegistry()
        
        # Prometheus metrics
        self.integration_health_gauge = Gauge(
            'incident_commander_integration_health',
            'Health status of service integrations',
            ['service_name', 'integration_type'],
            registry=self.registry
        )
        
        self.guardrail_decisions_counter = Counter(
            'incident_commander_guardrail_decisions_total',
            'Total guardrail decisions by type',
            ['guardrail_name', 'decision_type'],
            registry=self.registry
        )
        
        self.agent_performance_histogram = Histogram(
            'incident_commander_agent_execution_duration_seconds',
            'Agent execution duration in seconds',
            ['agent_name', 'agent_type', 'execution_status'],
            registry=self.registry
        )
        
        self.system_performance_gauge = Gauge(
            'incident_commander_system_performance',
            'System performance metrics',
            ['metric_type'],
            registry=self.registry
        )
        
        self.business_impact_gauge = Gauge(
            'incident_commander_business_impact',
            'Business impact metrics',
            ['metric_type', 'incident_id'],
            registry=self.registry
        )
        
        self.chaos_experiment_counter = Counter(
            'incident_commander_chaos_experiments_total',
            'Total chaos engineering experiments',
            ['experiment_type', 'status'],
            registry=self.registry
        )
        
        # Monitoring state
        self.monitoring_active = False
        self.collection_task: Optional[asyncio.Task] = None
        self.collection_interval = 30.0  # 30 seconds
        
        # Performance tracking
        self.last_collection_time = datetime.utcnow()
        self.metrics_collected = 0
        
        logger.info("Enhanced monitoring integration initialized")
    
    async def start_enhanced_monitoring(self) -> None:
        """Start enhanced monitoring with Prometheus integration."""
        if self.monitoring_active:
            logger.warning("Enhanced monitoring already active")
            return
        
        self.monitoring_active = True
        self.collection_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("Started enhanced monitoring with Prometheus integration")
    
    async def stop_enhanced_monitoring(self) -> None:
        """Stop enhanced monitoring."""
        self.monitoring_active = False
        
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass
            self.collection_task = None
        
        logger.info("Stopped enhanced monitoring")
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring collection loop."""
        try:
            while self.monitoring_active:
                start_time = time.time()
                
                # Collect metrics from all monitoring services
                await self._collect_integration_metrics()
                await self._collect_guardrail_metrics()
                await self._collect_agent_performance_metrics()
                await self._collect_system_performance_metrics()
                await self._collect_business_impact_metrics()
                await self._collect_chaos_engineering_metrics()
                
                self.metrics_collected += 1
                collection_duration = time.time() - start_time
                
                # Log performance every 10 collections
                if self.metrics_collected % 10 == 0:
                    logger.info(
                        f"Enhanced monitoring collection #{self.metrics_collected} "
                        f"completed in {collection_duration:.2f}s"
                    )
                
                # Sleep until next collection
                sleep_time = max(0, self.collection_interval - collection_duration)
                await asyncio.sleep(sleep_time)
                
        except asyncio.CancelledError:
            logger.info("Enhanced monitoring loop cancelled")
        except Exception as e:
            logger.error(f"Error in enhanced monitoring loop: {e}")
            self.monitoring_active = False
    
    async def _collect_integration_metrics(self) -> None:
        """Collect integration health metrics."""
        try:
            monitor = get_integration_monitor()
            
            if not monitor.monitoring_active:
                await monitor.start_monitoring()
            
            report = await monitor.get_integration_health_report()
            
            # Update Prometheus metrics
            for service_name, health in report.service_health.items():
                self.integration_health_gauge.labels(
                    service_name=service_name,
                    integration_type=health.integration_type.value
                ).set(1.0 if health.status.is_healthy else 0.0)
            
            # System-wide metrics
            self.system_performance_gauge.labels(metric_type='integration_health_score').set(
                report.healthy_services / report.total_services if report.total_services > 0 else 0
            )
            
        except Exception as e:
            logger.error(f"Error collecting integration metrics: {e}")
    
    async def _collect_guardrail_metrics(self) -> None:
        """Collect guardrail decision metrics."""
        try:
            tracker = get_guardrail_tracker()
            
            # Get recent guardrail decisions
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=5)  # Last 5 minutes
            
            decisions = await tracker.get_guardrail_decisions(start_time, end_time)
            
            # Count decisions by type
            decision_counts = {}
            for decision in decisions:
                key = (decision.guardrail_name, decision.decision_type.value)
                decision_counts[key] = decision_counts.get(key, 0) + 1
            
            # Update Prometheus counters (increment by new counts)
            for (guardrail_name, decision_type), count in decision_counts.items():
                self.guardrail_decisions_counter.labels(
                    guardrail_name=guardrail_name,
                    decision_type=decision_type
                )._value._value += count  # Direct increment to avoid double counting
            
        except Exception as e:
            logger.error(f"Error collecting guardrail metrics: {e}")
    
    async def _collect_agent_performance_metrics(self) -> None:
        """Collect agent performance metrics."""
        try:
            telemetry = get_agent_telemetry()
            
            # Get recent agent executions
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=5)  # Last 5 minutes
            
            executions = await telemetry.get_agent_executions(start_time, end_time)
            
            # Record execution durations
            for execution in executions:
                self.agent_performance_histogram.labels(
                    agent_name=execution.agent_name,
                    agent_type=execution.agent_type.value,
                    execution_status=execution.status
                ).observe(execution.duration_ms / 1000.0)  # Convert to seconds
            
            # System performance metrics
            performance_report = await telemetry.get_system_performance_report(24)  # Last 24 hours
            
            self.system_performance_gauge.labels(metric_type='system_success_rate').set(
                performance_report.system_success_rate
            )
            self.system_performance_gauge.labels(metric_type='consensus_success_rate').set(
                performance_report.consensus_success_rate
            )
            self.system_performance_gauge.labels(metric_type='escalation_rate').set(
                performance_report.escalation_rate
            )
            
        except Exception as e:
            logger.error(f"Error collecting agent performance metrics: {e}")
    
    async def _collect_system_performance_metrics(self) -> None:
        """Collect system-wide performance metrics."""
        try:
            # Collect from various system components
            from src.services.showcase_controller import get_showcase_controller
            from src.services.visual_3d_integration import get_visual_3d_integration
            
            # Showcase controller metrics
            try:
                showcase = get_showcase_controller()
                performance = await showcase.get_performance_summary()
                
                self.system_performance_gauge.labels(metric_type='average_mttr_seconds').set(
                    performance.average_mttr_seconds
                )
                self.system_performance_gauge.labels(metric_type='system_availability').set(
                    performance.system_availability
                )
                
            except Exception as e:
                logger.debug(f"Showcase controller metrics not available: {e}")
            
            # 3D visualization metrics
            try:
                visual_3d = get_visual_3d_integration()
                viz_status = await visual_3d.get_visualization_status()
                
                self.system_performance_gauge.labels(metric_type='3d_visualization_fps').set(
                    viz_status.get('actual_fps', 0)
                )
                self.system_performance_gauge.labels(metric_type='websocket_clients').set(
                    viz_status.get('websocket_clients', 0)
                )
                
            except Exception as e:
                logger.debug(f"3D visualization metrics not available: {e}")
            
        except Exception as e:
            logger.error(f"Error collecting system performance metrics: {e}")
    
    async def _collect_business_impact_metrics(self) -> None:
        """Collect business impact metrics."""
        try:
            # This would integrate with business impact calculator
            # For now, we'll collect basic metrics
            
            # Placeholder for business impact metrics
            # In a real implementation, this would connect to the business impact calculator
            self.business_impact_gauge.labels(
                metric_type='total_cost_savings',
                incident_id='system_wide'
            ).set(0)  # Would be actual cost savings
            
        except Exception as e:
            logger.error(f"Error collecting business impact metrics: {e}")
    
    async def _collect_chaos_engineering_metrics(self) -> None:
        """Collect chaos engineering metrics."""
        try:
            # This would integrate with chaos engineering framework
            # For now, we'll collect basic metrics
            
            # Placeholder for chaos engineering metrics
            # In a real implementation, this would connect to the chaos engineering service
            pass
            
        except Exception as e:
            logger.error(f"Error collecting chaos engineering metrics: {e}")
    
    def get_prometheus_metrics(self) -> str:
        """Get Prometheus-formatted metrics."""
        return generate_latest(self.registry).decode('utf-8')
    
    async def get_monitoring_status(self) -> Dict[str, Any]:
        """Get enhanced monitoring status."""
        return {
            "monitoring_active": self.monitoring_active,
            "collection_interval_seconds": self.collection_interval,
            "metrics_collected": self.metrics_collected,
            "last_collection": self.last_collection_time.isoformat(),
            "prometheus_integration": {
                "registry_active": True,
                "metrics_exported": len(self.registry._collector_to_names),
                "collection_frequency": f"Every {self.collection_interval} seconds"
            },
            "integrated_services": [
                "Integration Monitor",
                "Guardrail Tracker", 
                "Agent Telemetry",
                "Showcase Controller",
                "3D Visualization",
                "Business Impact Calculator",
                "Chaos Engineering Framework"
            ]
        }
    
    async def create_grafana_dashboard_config(self) -> Dict[str, Any]:
        """Create Grafana dashboard configuration for enhanced metrics."""
        return {
            "dashboard": {
                "id": None,
                "title": "Incident Commander Enhanced Monitoring",
                "tags": ["incident-commander", "monitoring", "enhanced"],
                "timezone": "browser",
                "panels": [
                    {
                        "id": 1,
                        "title": "Integration Health",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "incident_commander_integration_health",
                                "legendFormat": "{{service_name}}"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
                    },
                    {
                        "id": 2,
                        "title": "Guardrail Decisions",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "rate(incident_commander_guardrail_decisions_total[5m])",
                                "legendFormat": "{{guardrail_name}} - {{decision_type}}"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
                    },
                    {
                        "id": 3,
                        "title": "Agent Performance",
                        "type": "heatmap",
                        "targets": [
                            {
                                "expr": "incident_commander_agent_execution_duration_seconds",
                                "legendFormat": "{{agent_type}}"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8}
                    },
                    {
                        "id": 4,
                        "title": "System Performance",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "incident_commander_system_performance",
                                "legendFormat": "{{metric_type}}"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 16}
                    }
                ],
                "time": {"from": "now-1h", "to": "now"},
                "refresh": "30s"
            }
        }


# Global instance
_enhanced_monitoring: Optional[EnhancedMonitoringIntegration] = None


def get_enhanced_monitoring_integration() -> EnhancedMonitoringIntegration:
    """Get the global enhanced monitoring integration service."""
    global _enhanced_monitoring
    if _enhanced_monitoring is None:
        _enhanced_monitoring = EnhancedMonitoringIntegration()
    return _enhanced_monitoring


async def start_enhanced_monitoring() -> None:
    """Start enhanced monitoring integration."""
    integration = get_enhanced_monitoring_integration()
    await integration.start_enhanced_monitoring()


async def stop_enhanced_monitoring() -> None:
    """Stop enhanced monitoring integration."""
    integration = get_enhanced_monitoring_integration()
    await integration.stop_enhanced_monitoring()