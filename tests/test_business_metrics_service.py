"""
Integration tests for Business Metrics Service.

Tests real business metrics calculation from system performance data
including MTTR, cost savings, efficiency scores, and trend analysis.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from src.services.business_metrics_service import BusinessMetricsService, get_business_metrics_service
from src.models.real_time_models import BusinessMetrics


@pytest.fixture
def metrics_service():
    """Create business metrics service for testing."""
    return BusinessMetricsService(max_history=100)


@pytest.fixture
def sample_incidents(metrics_service):
    """Create sample incident data for testing."""
    base_time = datetime.utcnow()

    # Record 10 completed incidents
    for i in range(10):
        detection_time = base_time - timedelta(minutes=30 + i)
        resolution_time = base_time - timedelta(minutes=i)
        duration_minutes = 30

        metrics_service.record_incident_completion(
            incident_id=f"inc-{i}",
            detection_time=detection_time,
            resolution_time=resolution_time,
            severity="medium",
            was_prevented=False
        )

    # Record 5 prevented incidents
    for i in range(5):
        detection_time = base_time - timedelta(minutes=10 + i)
        resolution_time = base_time - timedelta(minutes=i)

        metrics_service.record_incident_completion(
            incident_id=f"prev-{i}",
            detection_time=detection_time,
            resolution_time=resolution_time,
            severity="low",
            was_prevented=True
        )

    return metrics_service


class TestBusinessMetricsInitialization:
    """Test business metrics service initialization."""

    def test_service_initialization(self, metrics_service):
        """Test service initializes correctly."""
        assert metrics_service.max_history == 100
        assert len(metrics_service.incident_history) == 0
        assert len(metrics_service.prevention_history) == 0
        assert metrics_service.start_time is not None

    def test_cost_assumptions_configured(self, metrics_service):
        """Test cost assumptions are configured."""
        assert metrics_service.cost_per_minute_downtime == 1000.0
        assert metrics_service.cost_per_incident_prevented == 5000.0

    def test_singleton_pattern(self):
        """Test singleton pattern for global service."""
        service1 = get_business_metrics_service()
        service2 = get_business_metrics_service()

        assert service1 is service2


class TestIncidentRecording:
    """Test incident completion recording."""

    def test_record_completed_incident(self, metrics_service):
        """Test recording a completed incident."""
        detection_time = datetime.utcnow() - timedelta(minutes=30)
        resolution_time = datetime.utcnow()

        metrics_service.record_incident_completion(
            incident_id="inc-test-1",
            detection_time=detection_time,
            resolution_time=resolution_time,
            severity="high",
            was_prevented=False
        )

        assert len(metrics_service.incident_history) == 1
        assert len(metrics_service.prevention_history) == 0

        incident = metrics_service.incident_history[0]
        assert incident["incident_id"] == "inc-test-1"
        assert incident["severity"] == "high"
        assert incident["duration_seconds"] > 0

    def test_record_prevented_incident(self, metrics_service):
        """Test recording a prevented incident."""
        detection_time = datetime.utcnow() - timedelta(minutes=5)
        resolution_time = datetime.utcnow()

        metrics_service.record_incident_completion(
            incident_id="prev-test-1",
            detection_time=detection_time,
            resolution_time=resolution_time,
            severity="medium",
            was_prevented=True
        )

        assert len(metrics_service.incident_history) == 0
        assert len(metrics_service.prevention_history) == 1

        incident = metrics_service.prevention_history[0]
        assert incident["incident_id"] == "prev-test-1"
        assert incident["was_prevented"] is True

    def test_history_limit_enforcement(self):
        """Test history size limit is enforced."""
        service = BusinessMetricsService(max_history=5)

        detection_time = datetime.utcnow() - timedelta(minutes=10)

        # Add 10 incidents (should only keep last 5)
        for i in range(10):
            resolution_time = datetime.utcnow() - timedelta(minutes=i)
            service.record_incident_completion(
                incident_id=f"inc-{i}",
                detection_time=detection_time,
                resolution_time=resolution_time,
                severity="medium",
                was_prevented=False
            )

        assert len(service.incident_history) == 5


class TestMTTRCalculation:
    """Test MTTR calculation with confidence intervals."""

    @pytest.mark.asyncio
    async def test_mttr_calculation(self, sample_incidents):
        """Test MTTR calculation from incident history."""
        metrics = await sample_incidents.calculate_current_metrics()

        assert metrics.mttr_seconds > 0
        assert metrics.mttr_confidence_lower > 0
        assert metrics.mttr_confidence_upper > metrics.mttr_seconds
        assert metrics.incidents_handled == 10

    @pytest.mark.asyncio
    async def test_mttr_with_no_incidents(self, metrics_service):
        """Test MTTR calculation with no incident data."""
        metrics = await metrics_service.calculate_current_metrics()

        assert metrics.mttr_seconds == 0.0
        assert metrics.mttr_confidence_lower == 0.0
        assert metrics.mttr_confidence_upper == 0.0

    @pytest.mark.asyncio
    async def test_mttr_confidence_intervals(self, sample_incidents):
        """Test MTTR confidence interval calculation."""
        metrics = await sample_incidents.calculate_current_metrics()

        # Confidence interval should bracket the mean
        assert metrics.mttr_confidence_lower <= metrics.mttr_seconds
        assert metrics.mttr_confidence_upper >= metrics.mttr_seconds

        # Confidence interval should be reasonable (not too wide)
        interval_width = metrics.mttr_confidence_upper - metrics.mttr_confidence_lower
        assert interval_width < metrics.mttr_seconds * 2


class TestCostSavingsCalculation:
    """Test cost savings calculation."""

    @pytest.mark.asyncio
    async def test_cost_savings_from_prevention(self, sample_incidents):
        """Test cost savings from prevented incidents."""
        metrics = await sample_incidents.calculate_current_metrics()

        # 5 prevented incidents * $5000 each = $25,000+
        assert metrics.cost_savings_usd >= 25000.0
        assert metrics.incidents_prevented == 5

    @pytest.mark.asyncio
    async def test_cost_savings_from_faster_resolution(self, metrics_service):
        """Test cost savings from faster resolution times."""
        # Record incidents with fast resolution (< 30 min baseline)
        base_time = datetime.utcnow()

        for i in range(10):
            detection_time = base_time - timedelta(minutes=10)
            resolution_time = base_time - timedelta(minutes=5)

            metrics_service.record_incident_completion(
                incident_id=f"fast-{i}",
                detection_time=detection_time,
                resolution_time=resolution_time,
                severity="medium",
                was_prevented=False
            )

        metrics = await metrics_service.calculate_current_metrics()

        # Should have savings from faster resolution
        assert metrics.cost_savings_usd > 0

    @pytest.mark.asyncio
    async def test_cost_savings_confidence_intervals(self, sample_incidents):
        """Test cost savings confidence intervals."""
        metrics = await sample_incidents.calculate_current_metrics()

        assert metrics.cost_savings_confidence_lower > 0
        assert metrics.cost_savings_confidence_upper > metrics.cost_savings_usd
        assert metrics.cost_savings_confidence_lower <= metrics.cost_savings_usd


class TestEfficiencyMetrics:
    """Test efficiency score and success rate calculations."""

    @pytest.mark.asyncio
    async def test_efficiency_score_calculation(self, sample_incidents):
        """Test efficiency score calculation."""
        metrics = await sample_incidents.calculate_current_metrics()

        assert 0.0 <= metrics.efficiency_score <= 1.0

    @pytest.mark.asyncio
    async def test_efficiency_with_fast_resolution(self, metrics_service):
        """Test high efficiency with fast resolution."""
        base_time = datetime.utcnow()

        # Record fast incidents (< 5 minutes)
        for i in range(10):
            detection_time = base_time - timedelta(minutes=5)
            resolution_time = base_time

            metrics_service.record_incident_completion(
                incident_id=f"fast-{i}",
                detection_time=detection_time,
                resolution_time=resolution_time,
                severity="medium",
                was_prevented=False
            )

        metrics = await metrics_service.calculate_current_metrics()

        # Fast resolution should yield high efficiency
        assert metrics.efficiency_score > 0.7

    @pytest.mark.asyncio
    async def test_success_rate_calculation(self, sample_incidents):
        """Test success rate calculation."""
        metrics = await sample_incidents.calculate_current_metrics()

        # All completed incidents are successful
        assert metrics.success_rate == 1.0


class TestTrendAnalysis:
    """Test trend analysis and historical comparison."""

    @pytest.mark.asyncio
    async def test_trend_calculation(self, metrics_service):
        """Test trend calculation vs previous period."""
        base_time = datetime.utcnow()

        # Add older incidents (slower resolution)
        for i in range(10):
            detection_time = base_time - timedelta(days=10, minutes=60)
            resolution_time = base_time - timedelta(days=10)

            metrics_service.record_incident_completion(
                incident_id=f"old-{i}",
                detection_time=detection_time,
                resolution_time=resolution_time,
                severity="medium",
                was_prevented=False
            )

        # Add recent incidents (faster resolution)
        for i in range(10):
            detection_time = base_time - timedelta(minutes=10)
            resolution_time = base_time

            metrics_service.record_incident_completion(
                incident_id=f"recent-{i}",
                detection_time=detection_time,
                resolution_time=resolution_time,
                severity="medium",
                was_prevented=False
            )

        metrics = await metrics_service.calculate_current_metrics()

        # Should show improving trend (negative MTTR trend)
        assert metrics.mttr_trend is not None
        assert metrics.efficiency_trend is not None

    @pytest.mark.asyncio
    async def test_trend_with_insufficient_data(self, metrics_service):
        """Test trend calculation with insufficient data."""
        # Add only a few incidents
        base_time = datetime.utcnow()

        for i in range(3):
            detection_time = base_time - timedelta(minutes=10)
            resolution_time = base_time

            metrics_service.record_incident_completion(
                incident_id=f"inc-{i}",
                detection_time=detection_time,
                resolution_time=resolution_time,
                severity="medium",
                was_prevented=False
            )

        metrics = await metrics_service.calculate_current_metrics()

        # Should return None for trends with insufficient data
        assert metrics.mttr_trend is None
        assert metrics.efficiency_trend is None


class TestDataQuality:
    """Test data quality scoring."""

    @pytest.mark.asyncio
    async def test_data_quality_with_small_sample(self, metrics_service):
        """Test data quality score with small sample size."""
        base_time = datetime.utcnow()

        # Add only 5 incidents
        for i in range(5):
            detection_time = base_time - timedelta(minutes=10)
            resolution_time = base_time

            metrics_service.record_incident_completion(
                incident_id=f"inc-{i}",
                detection_time=detection_time,
                resolution_time=resolution_time,
                severity="medium",
                was_prevented=False
            )

        metrics = await metrics_service.calculate_current_metrics()

        # Data quality should reflect small sample
        assert metrics.data_quality_score < 0.1
        assert metrics.sample_size == 5

    @pytest.mark.asyncio
    async def test_data_quality_with_large_sample(self, metrics_service):
        """Test data quality score with large sample size."""
        base_time = datetime.utcnow()

        # Add 100+ incidents
        for i in range(150):
            detection_time = base_time - timedelta(minutes=10 + i)
            resolution_time = base_time - timedelta(minutes=i)

            metrics_service.record_incident_completion(
                incident_id=f"inc-{i}",
                detection_time=detection_time,
                resolution_time=resolution_time,
                severity="medium",
                was_prevented=False
            )

        metrics = await metrics_service.calculate_current_metrics()

        # Data quality should be high with large sample
        assert metrics.data_quality_score == 1.0
        assert metrics.sample_size >= 100


class TestWebSocketIntegration:
    """Test WebSocket broadcasting of metrics."""

    @pytest.mark.asyncio
    async def test_broadcast_metrics_update(self, sample_incidents):
        """Test broadcasting metrics via WebSocket."""
        mock_ws_manager = AsyncMock()

        await sample_incidents.broadcast_metrics_update(mock_ws_manager)

        # Verify broadcast was called
        mock_ws_manager.broadcast_message.assert_called_once()

        call_args = mock_ws_manager.broadcast_message.call_args[0][0]
        assert call_args["event_type"] == "business_metrics"
        assert call_args["target_dashboard"] == "ops"


class TestIncidentHistory:
    """Test incident history retrieval."""

    def test_get_incident_history_summary(self, sample_incidents):
        """Test retrieving recent incident history."""
        history = sample_incidents.get_incident_history_summary(limit=5)

        assert len(history) <= 5
        assert all("incident_id" in inc for inc in history)
        assert all("duration_seconds" in inc for inc in history)
        assert all("severity" in inc for inc in history)

    def test_incident_history_ordering(self, sample_incidents):
        """Test incident history is ordered correctly."""
        history = sample_incidents.get_incident_history_summary(limit=10)

        # Should return most recent incidents
        assert len(history) == 10


class TestRealSystemData:
    """Test metrics calculation from real system data."""

    @pytest.mark.asyncio
    async def test_metrics_reflect_real_performance(self, sample_incidents):
        """Test metrics accurately reflect system performance."""
        metrics = await sample_incidents.calculate_current_metrics()

        # Verify all required fields
        assert metrics.mttr_seconds > 0
        assert metrics.incidents_handled > 0
        assert metrics.efficiency_score > 0
        assert metrics.success_rate > 0
        assert metrics.sample_size > 0

        # Verify calculation method is documented
        assert metrics.calculation_method == "real_system_data"
        assert metrics.confidence_level == 0.95

    @pytest.mark.asyncio
    async def test_metrics_update_with_new_incidents(self, sample_incidents):
        """Test metrics update as new incidents complete."""
        initial_metrics = await sample_incidents.calculate_current_metrics()
        initial_count = initial_metrics.incidents_handled

        # Add new incident
        base_time = datetime.utcnow()
        sample_incidents.record_incident_completion(
            incident_id="new-inc-1",
            detection_time=base_time - timedelta(minutes=10),
            resolution_time=base_time,
            severity="medium",
            was_prevented=False
        )

        updated_metrics = await sample_incidents.calculate_current_metrics()

        # Metrics should reflect new incident
        assert updated_metrics.incidents_handled == initial_count + 1


# Run tests with: pytest tests/test_business_metrics_service.py -v
