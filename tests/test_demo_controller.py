"""
Tests for Demo Controller

Task 12.1: Build demo controller with controlled scenario execution
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.services.demo_controller import (
    DemoController, 
    DemoScenarioType, 
    DemoPhase,
    DemoSession,
    DemoMetrics
)


class TestDemoController:
    """Test suite for Demo Controller functionality."""
    
    @pytest.fixture
    def demo_controller(self):
        """Create demo controller instance for testing."""
        return DemoController()
    
    @pytest.fixture
    def mock_coordinator(self):
        """Mock swarm coordinator for testing."""
        mock = Mock()
        mock.process_incident = Mock(return_value=asyncio.Future())
        mock.process_incident.return_value.set_result(None)
        return mock
    
    def test_scenario_configs_initialization(self, demo_controller):
        """Test that scenario configurations are properly initialized."""
        configs = demo_controller.scenario_configs
        
        # Verify all required scenarios are present
        expected_scenarios = [
            DemoScenarioType.DATABASE_CASCADE,
            DemoScenarioType.DDOS_ATTACK,
            DemoScenarioType.MEMORY_LEAK
        ]
        
        for scenario in expected_scenarios:
            assert scenario in configs
            config = configs[scenario]
            
            # Verify required fields
            assert "title" in config
            assert "description" in config
            assert "severity" in config
            assert "service_tier" in config
            assert "affected_users" in config
            assert "revenue_impact_per_minute" in config
            assert "complexity" in config
            assert "estimated_phases" in config
            assert "sla_target_minutes" in config
            assert "traditional_mttr_minutes" in config
    
    @pytest.mark.asyncio
    async def test_start_demo_scenario(self, demo_controller, mock_coordinator):
        """Test starting a demo scenario."""
        with patch('src.services.demo_controller.get_swarm_coordinator', return_value=mock_coordinator):
            # Start demo scenario
            session = await demo_controller.start_demo_scenario(DemoScenarioType.DATABASE_CASCADE)
            
            # Verify session creation
            assert session.scenario_type == DemoScenarioType.DATABASE_CASCADE
            assert session.current_phase == DemoPhase.INITIALIZING
            assert session.is_active is True
            assert session.completion_guarantee_minutes == 5
            assert session.environment_isolated is True
            
            # Verify session is stored
            assert session.session_id in demo_controller.active_sessions
            
            # Verify metrics initialization
            assert session.metrics.cost_per_minute == 2000.0  # Database cascade config
            assert session.metrics.affected_users == 50000
            assert session.metrics.traditional_mttr_estimate == 45 * 60  # 45 minutes
    
    @pytest.mark.asyncio
    async def test_controlled_scenario_execution(self, demo_controller, mock_coordinator):
        """Test controlled scenario execution with timing guarantees."""
        with patch('src.services.demo_controller.get_swarm_coordinator', return_value=mock_coordinator):
            # Start scenario
            session = await demo_controller.start_demo_scenario(DemoScenarioType.MEMORY_LEAK)
            
            # Wait for execution to begin
            await asyncio.sleep(0.1)
            
            # Verify initial state
            assert session.current_phase in [DemoPhase.INITIALIZING, DemoPhase.DETECTING]
            
            # Wait for some execution (but not full completion)
            await asyncio.sleep(0.5)
            
            # Verify progression through phases
            assert session.current_phase in [
                DemoPhase.DETECTING, 
                DemoPhase.DIAGNOSING, 
                DemoPhase.PREDICTING,
                DemoPhase.RESOLVING,
                DemoPhase.COMMUNICATING,
                DemoPhase.COMPLETED
            ]
    
    def test_real_time_metrics(self, demo_controller):
        """Test real-time metrics calculation."""
        # Create a test session with current time
        start_time = datetime.utcnow()
        session = DemoSession(
            session_id="test_session",
            scenario_type=DemoScenarioType.DDOS_ATTACK,
            incident_id="test_incident",
            start_time=start_time
        )
        session.metrics.cost_per_minute = 1500.0
        session.metrics.traditional_mttr_estimate = 30 * 60  # 30 minutes
        session.metrics.sla_breach_countdown = 10 * 60  # 10 minutes
        
        demo_controller.active_sessions["test_session"] = session
        
        # Wait a small amount to ensure elapsed time
        import time
        time.sleep(0.1)
        
        # Get real-time metrics
        metrics = demo_controller.get_real_time_metrics("test_session")
        
        assert metrics is not None
        assert metrics["session_id"] == "test_session"
        assert metrics["scenario_type"] == "ddos_attack"
        assert metrics["elapsed_time_seconds"] >= 0
        assert metrics["metrics"]["cost_accumulated"] >= 0
        assert metrics["metrics"]["autonomous_improvement_percentage"] >= 0
    
    def test_comparison_metrics(self, demo_controller):
        """Test before/after comparison metrics."""
        # Create a test session
        session = DemoSession(
            session_id="test_comparison",
            scenario_type=DemoScenarioType.DATABASE_CASCADE,
            incident_id="test_incident",
            start_time=datetime.utcnow() - timedelta(seconds=120)  # 2 minutes ago
        )
        session.metrics.cost_per_minute = 2000.0
        session.metrics.affected_users = 50000
        session.metrics.cost_accumulated = 4000.0  # 2 minutes * $2000/min
        session.metrics.traditional_mttr_estimate = 45 * 60  # 45 minutes
        
        demo_controller.active_sessions["test_comparison"] = session
        
        # Get comparison metrics
        comparison = demo_controller.get_comparison_metrics("test_comparison")
        
        assert comparison is not None
        assert "traditional_response" in comparison
        assert "autonomous_response" in comparison
        assert "improvement" in comparison
        assert "business_impact" in comparison
        
        # Verify traditional response
        traditional = comparison["traditional_response"]
        assert traditional["mttr_minutes"] == 45  # Database cascade traditional MTTR
        assert traditional["total_cost"] == 45 * 2000.0  # 45 minutes * $2000/min
        assert traditional["manual_steps_required"] == 15
        
        # Verify autonomous response
        autonomous = comparison["autonomous_response"]
        assert autonomous["mttr_minutes"] >= 1.9  # Approximately 2 minutes elapsed
        assert autonomous["total_cost"] == 4000.0
        assert autonomous["automated_steps"] == 12
        
        # Verify improvement calculations
        improvement = comparison["improvement"]
        assert improvement["cost_savings"] > 0
        assert improvement["time_saved_minutes"] > 0
        assert improvement["mttr_reduction_percentage"] > 0
    
    def test_session_management(self, demo_controller):
        """Test session management operations."""
        # Create test sessions
        session1 = DemoSession(
            session_id="session1",
            scenario_type=DemoScenarioType.MEMORY_LEAK,
            incident_id="incident1",
            start_time=datetime.utcnow()
        )
        session2 = DemoSession(
            session_id="session2",
            scenario_type=DemoScenarioType.DDOS_ATTACK,
            incident_id="incident2",
            start_time=datetime.utcnow()
        )
        session2.is_active = False  # Completed session
        
        demo_controller.active_sessions["session1"] = session1
        demo_controller.active_sessions["session2"] = session2
        
        # Test listing sessions
        sessions = demo_controller.list_active_sessions()
        assert len(sessions) == 2
        
        # Test stopping session
        success = demo_controller.stop_demo_session("session1")
        assert success is True
        assert session1.is_active is False
        assert session1.current_phase == DemoPhase.COMPLETED
        
        # Test stopping non-existent session
        success = demo_controller.stop_demo_session("nonexistent")
        assert success is False
    
    def test_session_cleanup(self, demo_controller):
        """Test cleanup of completed sessions."""
        # Create old completed session
        old_session = DemoSession(
            session_id="old_session",
            scenario_type=DemoScenarioType.MEMORY_LEAK,
            incident_id="old_incident",
            start_time=datetime.utcnow() - timedelta(hours=25)  # 25 hours ago
        )
        old_session.is_active = False
        
        # Create recent completed session
        recent_session = DemoSession(
            session_id="recent_session",
            scenario_type=DemoScenarioType.DDOS_ATTACK,
            incident_id="recent_incident",
            start_time=datetime.utcnow() - timedelta(hours=1)  # 1 hour ago
        )
        recent_session.is_active = False
        
        # Create active session
        active_session = DemoSession(
            session_id="active_session",
            scenario_type=DemoScenarioType.DATABASE_CASCADE,
            incident_id="active_incident",
            start_time=datetime.utcnow()
        )
        
        demo_controller.active_sessions["old_session"] = old_session
        demo_controller.active_sessions["recent_session"] = recent_session
        demo_controller.active_sessions["active_session"] = active_session
        
        # Cleanup with 24-hour threshold
        cleaned_count = demo_controller.cleanup_completed_sessions(max_age_hours=24)
        
        # Verify cleanup results
        assert cleaned_count == 1  # Only old session should be cleaned
        assert "old_session" not in demo_controller.active_sessions
        assert "recent_session" in demo_controller.active_sessions  # Still within 24 hours
        assert "active_session" in demo_controller.active_sessions  # Still active
    
    def test_metrics_not_found(self, demo_controller):
        """Test handling of non-existent sessions."""
        # Test real-time metrics for non-existent session
        metrics = demo_controller.get_real_time_metrics("nonexistent")
        assert metrics is None
        
        # Test comparison metrics for non-existent session
        comparison = demo_controller.get_comparison_metrics("nonexistent")
        assert comparison is None
    
    def test_completion_guarantee(self, demo_controller):
        """Test 5-minute completion guarantee."""
        # All scenarios should have completion guarantee
        for scenario_type in DemoScenarioType:
            config = demo_controller.scenario_configs[scenario_type]
            
            # Calculate total estimated time
            total_estimated = sum(config["estimated_phases"].values())
            
            # Should be well under 5 minutes (300 seconds)
            assert total_estimated < 300, f"Scenario {scenario_type.value} exceeds 5-minute guarantee"
    
    def test_environment_isolation(self, demo_controller):
        """Test demo environment isolation features."""
        # Create session
        session = DemoSession(
            session_id="isolation_test",
            scenario_type=DemoScenarioType.MEMORY_LEAK,
            incident_id="test_incident",
            start_time=datetime.utcnow()
        )
        
        # Verify isolation features
        assert session.environment_isolated is True
        assert session.completion_guarantee_minutes == 5
        
        # Verify demo tags in incident metadata would be set
        # (This would be tested in integration tests with actual incident creation)
    
    @pytest.mark.asyncio
    async def test_concurrent_demo_sessions(self, demo_controller, mock_coordinator):
        """Test running multiple concurrent demo sessions."""
        with patch('src.services.demo_controller.get_swarm_coordinator', return_value=mock_coordinator):
            # Start multiple sessions concurrently
            session1 = await demo_controller.start_demo_scenario(
                DemoScenarioType.DATABASE_CASCADE, 
                session_id="concurrent1"
            )
            session2 = await demo_controller.start_demo_scenario(
                DemoScenarioType.DDOS_ATTACK, 
                session_id="concurrent2"
            )
            session3 = await demo_controller.start_demo_scenario(
                DemoScenarioType.MEMORY_LEAK, 
                session_id="concurrent3"
            )
            
            # Verify all sessions are active
            assert len(demo_controller.active_sessions) == 3
            assert all(session.is_active for session in demo_controller.active_sessions.values())
            
            # Verify each session has unique characteristics
            sessions = list(demo_controller.active_sessions.values())
            scenario_types = [s.scenario_type for s in sessions]
            assert len(set(scenario_types)) == 3  # All different scenarios
            
            # Verify metrics are independent
            metrics1 = demo_controller.get_real_time_metrics("concurrent1")
            metrics2 = demo_controller.get_real_time_metrics("concurrent2")
            metrics3 = demo_controller.get_real_time_metrics("concurrent3")
            
            assert metrics1["metrics"]["cost_per_minute"] == 2000.0  # Database cascade
            assert metrics2["metrics"]["cost_per_minute"] == 1500.0  # DDoS attack
            assert metrics3["metrics"]["cost_per_minute"] == 300.0   # Memory leak


class TestDemoMetrics:
    """Test suite for demo metrics calculations."""
    
    def test_metrics_initialization(self):
        """Test demo metrics initialization."""
        metrics = DemoMetrics()
        
        assert metrics.mttr_seconds == 0.0
        assert metrics.cost_accumulated == 0.0
        assert metrics.cost_per_minute == 0.0
        assert metrics.affected_users == 0
        assert metrics.sla_breach_countdown == 0.0
        assert metrics.reputation_impact_score == 0.0
        assert metrics.traditional_mttr_estimate == 1800.0  # 30 minutes default
        assert metrics.autonomous_improvement_percentage == 0.0
    
    def test_metrics_calculations(self):
        """Test metrics calculation logic."""
        metrics = DemoMetrics()
        metrics.cost_per_minute = 1000.0
        metrics.traditional_mttr_estimate = 1800.0  # 30 minutes
        
        # Simulate 2 minutes elapsed
        elapsed_minutes = 2.0
        metrics.mttr_seconds = elapsed_minutes * 60
        metrics.cost_accumulated = metrics.cost_per_minute * elapsed_minutes
        
        # Calculate improvement percentage
        metrics.autonomous_improvement_percentage = (
            (metrics.traditional_mttr_estimate - metrics.mttr_seconds) / 
            metrics.traditional_mttr_estimate * 100
        )
        
        assert metrics.cost_accumulated == 2000.0  # 2 minutes * $1000/min
        assert abs(metrics.autonomous_improvement_percentage - 93.33) < 0.01  # (1800-120)/1800 * 100


class TestDemoSession:
    """Test suite for demo session management."""
    
    def test_session_creation(self):
        """Test demo session creation."""
        start_time = datetime.utcnow()
        session = DemoSession(
            session_id="test_session",
            scenario_type=DemoScenarioType.DATABASE_CASCADE,
            incident_id="test_incident",
            start_time=start_time
        )
        
        assert session.session_id == "test_session"
        assert session.scenario_type == DemoScenarioType.DATABASE_CASCADE
        assert session.incident_id == "test_incident"
        assert session.start_time == start_time
        assert session.current_phase == DemoPhase.INITIALIZING
        assert session.is_active is True
        assert session.completion_guarantee_minutes == 5
        assert session.environment_isolated is True
        assert isinstance(session.metrics, DemoMetrics)
        assert isinstance(session.phase_timings, dict)
        assert isinstance(session.agent_confidence_scores, dict)
    
    def test_session_phase_progression(self):
        """Test session phase progression."""
        session = DemoSession(
            session_id="phase_test",
            scenario_type=DemoScenarioType.MEMORY_LEAK,
            incident_id="test_incident",
            start_time=datetime.utcnow()
        )
        
        # Test phase progression
        phases = [
            DemoPhase.INITIALIZING,
            DemoPhase.DETECTING,
            DemoPhase.DIAGNOSING,
            DemoPhase.PREDICTING,
            DemoPhase.RESOLVING,
            DemoPhase.COMMUNICATING,
            DemoPhase.COMPLETED
        ]
        
        for phase in phases:
            session.current_phase = phase
            assert session.current_phase == phase
        
        # Test completion
        session.current_phase = DemoPhase.COMPLETED
        session.is_active = False
        assert session.current_phase == DemoPhase.COMPLETED
        assert session.is_active is False


if __name__ == "__main__":
    pytest.main([__file__])