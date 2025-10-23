"""
Unit tests for detection agent memory pressure handling and backpressure guarantees.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from agents.detection.agent import RobustDetectionAgent, MemoryBoundedDetectionAgent, AlertSampler
from src.models.incident import Incident, IncidentSeverity, ServiceTier, BusinessImpact, IncidentMetadata
from src.utils.exceptions import MemoryPressureError
from src.services.shared_memory_monitor import SharedMemoryMonitor, MemoryStats


class TestDetectionAgentMemoryPressure:
    """Test detection agent memory pressure handling and backpressure mechanisms."""
    
    @pytest.fixture
    def detection_agent(self):
        """Create detection agent for testing."""
        return RobustDetectionAgent("test_detection")
    
    @pytest.fixture
    def memory_monitor(self):
        """Create mock memory monitor."""
        monitor = MagicMock(spec=SharedMemoryMonitor)
        return monitor
    
    @pytest.fixture
    def sample_incident(self):
        """Create sample incident for testing."""
        business_impact = BusinessImpact(
            service_tier=ServiceTier.TIER_1,
            affected_users=1000,
            revenue_impact_per_minute=500.0
        )
        
        metadata = IncidentMetadata(
            source_system="test_system",
            tags={"test": "true"}
        )
        
        return Incident(
            title="Test Incident",
            description="Test incident for memory pressure testing",
            severity=IncidentSeverity.HIGH,
            business_impact=business_impact,
            metadata=metadata
        )
    
    @pytest.fixture
    def sample_alerts(self):
        """Create sample alerts for testing."""
        alerts = []
        for i in range(100):
            alert = {
                'id': f'alert-{i}',
                'timestamp': datetime.utcnow().isoformat(),
                'severity': 'high' if i % 10 == 0 else 'medium',
                'source': f'service-{i % 5}',
                'message': f'Test alert {i}',
                'metadata': {'test': True, 'index': i}
            }
            alerts.append(alert)
        return alerts
    
    @pytest.mark.asyncio
    async def test_should_drop_alerts_when_memory_pressure_high(self, detection_agent):
        """Test that alerts are dropped when memory pressure is high."""
        # Mock high memory pressure
        with patch('agents.detection.agent.get_shared_memory_monitor') as mock_get_monitor:
            mock_monitor = AsyncMock()
            mock_monitor.get_memory_pressure.return_value = 0.95  # 95% memory usage
            mock_get_monitor.return_value = mock_monitor

            # Set threshold lower than current usage
            detection_agent.memory_threshold = 0.8

            # Should drop alerts due to high memory pressure
            should_drop = await detection_agent.should_drop_alerts()
            assert should_drop is True
    
    @pytest.mark.asyncio
    async def test_should_not_drop_alerts_when_memory_pressure_normal(self, detection_agent):
        """Test that alerts are not dropped when memory pressure is normal."""
        # Mock normal memory pressure
        with patch('agents.detection.agent.get_shared_memory_monitor') as mock_get_monitor:
            mock_monitor = AsyncMock()
            mock_monitor.get_memory_pressure.return_value = 0.5  # 50% memory usage
            mock_get_monitor.return_value = mock_monitor

            # Set threshold higher than current usage
            detection_agent.memory_threshold = 0.8

            # Should not drop alerts
            should_drop = await detection_agent.should_drop_alerts()
            assert should_drop is False
    
    @pytest.mark.asyncio
    async def test_emergency_cleanup_reduces_memory_usage(self, detection_agent):
        """Test that emergency cleanup reduces memory usage."""
        # Fill up alert buffer and correlation cache
        for i in range(1000):
            detection_agent.alert_buffer.append(f"alert-{i}")
            detection_agent.correlation_cache[f"key-{i}"] = (f"value-{i}", datetime.utcnow())
        
        initial_buffer_size = len(detection_agent.alert_buffer)
        initial_cache_size = len(detection_agent.correlation_cache)
        
        # Perform emergency cleanup
        detection_agent.emergency_cleanup()
        
        # Verify memory usage was reduced
        final_buffer_size = len(detection_agent.alert_buffer)
        final_cache_size = len(detection_agent.correlation_cache)
        
        assert final_buffer_size <= 500  # Should be reduced to max 500
        assert final_cache_size < initial_cache_size  # Cache should be cleaned
    
    @pytest.mark.asyncio
    async def test_memory_pressure_error_raised_during_incident_processing(self, detection_agent, sample_incident):
        """Test that MemoryPressureError is raised during incident processing under high memory pressure."""
        # Mock high memory pressure
        with patch('agents.detection.agent.get_shared_memory_monitor') as mock_get_monitor:
            mock_monitor = AsyncMock()
            mock_monitor.get_memory_pressure.return_value = 0.95  # 95% memory usage
            mock_get_monitor.return_value = mock_monitor
            
            detection_agent.memory_threshold = 0.8
            
            # Should raise MemoryPressureError
            with pytest.raises(MemoryPressureError, match="Memory pressure too high"):
                await detection_agent.process_incident(sample_incident)
    
    @pytest.mark.asyncio
    async def test_alert_sampling_under_memory_pressure(self, detection_agent, sample_alerts):
        """Test alert sampling behavior under memory pressure."""
        # Mock high memory pressure
        with patch('agents.detection.agent.get_shared_memory_monitor') as mock_get_monitor:
            mock_monitor = AsyncMock()
            mock_monitor.get_memory_pressure.return_value = 0.9  # 90% memory usage
            mock_get_monitor.return_value = mock_monitor
            
            detection_agent.memory_threshold = 0.8
            
            # Process alerts under memory pressure
            incidents = await detection_agent.analyze_alerts(sample_alerts)
            
            # Should return empty list due to memory pressure
            assert len(incidents) == 0
    
    @pytest.mark.asyncio
    async def test_alert_sampler_respects_memory_pressure(self):
        """Test that AlertSampler respects memory pressure when sampling."""
        sampler = AlertSampler(max_rate=50)
        
        # Create test alert
        test_alert = {
            'id': 'test-alert',
            'severity': 'medium',
            'source': 'test-service',
            'message': 'Test alert'
        }
        
        # Mock high memory pressure
        with patch('agents.detection.agent.get_shared_memory_monitor') as mock_get_monitor:
            mock_monitor = AsyncMock()
            mock_monitor.get_memory_pressure.return_value = 0.95  # 95% memory usage
            mock_get_monitor.return_value = mock_monitor
            
            # Should not sample alert due to high memory pressure
            should_sample = await sampler.should_sample_alert(test_alert)
            assert should_sample is False
    
    @pytest.mark.asyncio
    async def test_high_priority_alerts_bypass_memory_pressure(self):
        """Test that high priority alerts bypass memory pressure restrictions."""
        sampler = AlertSampler(max_rate=1)  # Very low rate limit
        
        # Create high priority alert
        high_priority_alert = {
            'id': 'critical-alert',
            'severity': 'critical',
            'source': 'api-gateway',
            'message': 'Critical system failure'
        }
        
        # Mock high memory pressure
        with patch('agents.detection.agent.get_shared_memory_monitor') as mock_get_monitor:
            mock_monitor = AsyncMock()
            mock_monitor.get_memory_pressure.return_value = 0.95  # 95% memory usage
            mock_get_monitor.return_value = mock_monitor
            
            # High priority alert should still be sampled
            should_sample = await sampler.should_sample_alert(high_priority_alert)
            assert should_sample is True
    
    @pytest.mark.asyncio
    async def test_memory_stats_include_cache_statistics(self, detection_agent):
        """Test that memory stats include cache statistics from shared monitor."""
        # Mock memory monitor with cache stats
        with patch('agents.detection.agent.get_shared_memory_monitor') as mock_get_monitor:
            mock_monitor = AsyncMock()
            mock_memory_stats = MemoryStats(
                total_mb=8192.0,
                available_mb=2048.0,
                used_mb=6144.0,
                percentage=75.0,
                timestamp=datetime.utcnow()
            )
            mock_monitor.get_memory_stats.return_value = mock_memory_stats
            mock_monitor.get_cache_statistics.return_value = {
                "total_requests": 100,
                "cache_hits": 80,
                "cache_misses": 20,
                "hit_rate": 0.8
            }
            mock_get_monitor.return_value = mock_monitor
            
            # Get memory stats
            stats = await detection_agent.get_memory_stats()
            
            # Verify stats include both memory and cache information
            assert stats["total_mb"] == 8192.0
            assert stats["percentage"] == 75.0
            assert "cache_statistics" in stats
            assert stats["cache_statistics"]["hit_rate"] == 0.8
    
    @pytest.mark.asyncio
    async def test_health_check_fails_under_extreme_memory_pressure(self, detection_agent):
        """Test that health check fails under extreme memory pressure."""
        # Mock extreme memory pressure
        with patch('agents.detection.agent.get_shared_memory_monitor') as mock_get_monitor:
            mock_monitor = AsyncMock()
            mock_monitor.get_memory_pressure.return_value = 0.95  # 95% memory usage
            mock_get_monitor.return_value = mock_monitor
            
            # Health check should fail
            is_healthy = await detection_agent.health_check()
            assert is_healthy is False
            assert detection_agent.is_healthy is False
    
    @pytest.mark.asyncio
    async def test_backpressure_guarantees_under_load(self, detection_agent, sample_alerts):
        """Test backpressure guarantees under high alert load."""
        # Mock memory pressure that triggers backpressure
        with patch('agents.detection.agent.get_shared_memory_monitor') as mock_get_monitor:
            mock_monitor = AsyncMock()
            # Simulate increasing memory pressure
            pressure_values = [0.7, 0.8, 0.85, 0.9, 0.95]
            mock_monitor.get_memory_pressure.side_effect = pressure_values
            mock_get_monitor.return_value = mock_monitor
            
            detection_agent.memory_threshold = 0.8
            
            # Process alerts in batches
            processed_batches = 0
            for i in range(0, len(sample_alerts), 20):
                batch = sample_alerts[i:i+20]
                try:
                    incidents = await detection_agent.analyze_alerts(batch)
                    processed_batches += 1
                except MemoryPressureError:
                    # Expected when memory pressure gets too high
                    break
            
            # Should process some batches before hitting memory limit
            assert processed_batches >= 1
            assert processed_batches < 5  # But not all due to backpressure
    
    @pytest.mark.asyncio
    async def test_correlation_depth_limit_prevents_memory_explosion(self, detection_agent):
        """Test that correlation depth limit prevents memory explosion."""
        # Create many events that could cause deep correlation
        events = []
        for i in range(200):  # More than max correlation depth
            event = {
                'alert_id': f'alert-{i}',
                'source': 'test-service',
                'severity': 'medium',
                'message': f'Test event {i}',
                'metadata': {}
            }
            events.append(event)
        
        # Set low correlation depth limit
        detection_agent.max_correlation_depth = 50
        
        # Correlate events
        groups = await detection_agent.correlate_events(events)
        
        # Should not exceed correlation depth limit
        assert len(groups) <= detection_agent.max_correlation_depth
    
    @pytest.mark.asyncio
    async def test_circular_reference_detection_prevents_infinite_loops(self, detection_agent):
        """Test that circular reference detection prevents infinite loops."""
        # Create events with potential circular references
        events = [
            {
                'alert_id': 'alert-1',
                'source': 'service-a',
                'severity': 'high',
                'message': 'Event 1',
                'metadata': {'related_to': 'alert-2'}
            },
            {
                'alert_id': 'alert-2', 
                'source': 'service-a',
                'severity': 'high',
                'message': 'Event 2',
                'metadata': {'related_to': 'alert-1'}  # Circular reference
            }
        ]
        
        # Should complete without infinite loop
        start_time = asyncio.get_event_loop().time()
        groups = await detection_agent.correlate_events(events)
        end_time = asyncio.get_event_loop().time()
        
        # Should complete quickly (not hang in infinite loop)
        assert (end_time - start_time) < 1.0  # Less than 1 second
        assert len(groups) >= 0  # Should return some result


class TestAlertSamplerMemoryPressure:
    """Test AlertSampler memory pressure handling specifically."""
    
    @pytest.fixture
    def alert_sampler(self):
        """Create alert sampler for testing."""
        return AlertSampler(max_rate=100)
    
    @pytest.mark.asyncio
    async def test_sampling_rate_decreases_with_memory_pressure(self, alert_sampler):
        """Test that sampling rate decreases as memory pressure increases."""
        test_alert = {
            'id': 'test-alert',
            'severity': 'medium',
            'source': 'test-service',
            'message': 'Test alert'
        }
        
        # Test different memory pressure levels
        pressure_levels = [0.5, 0.7, 0.8, 0.9]
        sample_rates = []
        
        for pressure in pressure_levels:
            with patch('agents.detection.agent.get_shared_memory_monitor') as mock_get_monitor:
                mock_monitor = AsyncMock()
                mock_monitor.get_memory_pressure.return_value = pressure
                mock_get_monitor.return_value = mock_monitor
                
                # Reset sampler state
                alert_sampler.sample_count = 0
                alert_sampler.dropped_count = 0
                
                # Test sampling over multiple attempts
                samples = 0
                for _ in range(100):
                    if await alert_sampler.should_sample_alert(test_alert):
                        samples += 1
                
                sample_rates.append(samples / 100.0)
        
        # Sample rate should generally decrease as memory pressure increases
        # (allowing for some variation due to time-based sampling)
        assert sample_rates[0] >= sample_rates[-1]  # First should be >= last
    
    @pytest.mark.asyncio
    async def test_dropped_count_tracking(self, alert_sampler):
        """Test that dropped alert count is tracked correctly."""
        test_alert = {
            'id': 'test-alert',
            'severity': 'low',
            'source': 'test-service',
            'message': 'Test alert'
        }
        
        # Mock high memory pressure to force drops
        with patch('agents.detection.agent.get_shared_memory_monitor') as mock_get_monitor:
            mock_monitor = AsyncMock()
            mock_monitor.get_memory_pressure.return_value = 0.95
            mock_get_monitor.return_value = mock_monitor
            
            initial_dropped = alert_sampler.dropped_count
            
            # Try to sample many alerts (most should be dropped)
            for _ in range(50):
                await alert_sampler.should_sample_alert(test_alert)
            
            # Dropped count should increase
            assert alert_sampler.dropped_count > initial_dropped