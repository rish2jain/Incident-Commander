"""
Tests for Demo Metrics and Performance Comparison

Task 12.3: Create demo metrics and performance comparison
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.services.demo_metrics import (
    DemoMetricsAnalyzer,
    MTTRComparison,
    BusinessImpactComparison,
    PerformanceGuarantee,
    get_demo_metrics_analyzer
)


class TestDemoMetricsAnalyzer:
    """Test demo metrics analyzer functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = DemoMetricsAnalyzer()
        
        # Mock demo controller
        self.mock_demo_controller = Mock()
        self.analyzer.demo_controller = self.mock_demo_controller
        
    def test_initialize_baseline_metrics(self):
        """Test baseline metrics initialization."""
        baseline = self.analyzer.baseline_metrics
        
        assert "database_cascade" in baseline
        assert "ddos_attack" in baseline
        assert "memory_leak" in baseline
        
        # Verify structure
        db_cascade = baseline["database_cascade"]
        assert "traditional_mttr_minutes" in db_cascade
        assert "traditional_cost_per_minute" in db_cascade
        assert db_cascade["traditional_mttr_minutes"] == 45
        assert db_cascade["traditional_cost_per_minute"] == 2000.0
        
    def test_calculate_mttr_comparison(self):
        """Test MTTR comparison calculation."""
        session_id = "test_session_123"
        
        # Mock session metrics
        mock_metrics = {
            "scenario_type": "database_cascade",
            "metrics": {
                "mttr_seconds": 180,  # 3 minutes
                "cost_accumulated": 100.0,
                "affected_users": 50000
            }
        }
        self.mock_demo_controller.get_real_time_metrics.return_value = mock_metrics
        
        # Calculate comparison
        comparison = self.analyzer.calculate_mttr_comparison(session_id)
        
        assert isinstance(comparison, MTTRComparison)
        assert comparison.scenario_type == "database_cascade"
        assert comparison.traditional_mttr_minutes == 45
        assert comparison.autonomous_mttr_minutes == 3.0
        assert comparison.reduction_percentage > 90  # Should be ~93.3%
        assert comparison.time_saved_minutes == 42
        assert comparison.improvement_factor == 15.0
        
    def test_calculate_business_impact_comparison(self):
        """Test business impact comparison calculation."""
        session_id = "test_session_123"
        
        # Mock session metrics
        mock_metrics = {
            "scenario_type": "database_cascade",
            "metrics": {
                "mttr_seconds": 180,  # 3 minutes
                "cost_accumulated": 6000.0,  # 3 minutes * 2000/min
                "affected_users": 50000
            }
        }
        self.mock_demo_controller.get_real_time_metrics.return_value = mock_metrics
        
        # Calculate comparison
        comparison = self.analyzer.calculate_business_impact_comparison(session_id)
        
        assert isinstance(comparison, BusinessImpactComparison)
        assert comparison.scenario_type == "database_cascade"
        assert comparison.traditional_cost == 90000.0  # 45 * 2000
        assert comparison.autonomous_cost == 6000.0
        assert comparison.cost_savings == 84000.0
        assert comparison.cost_savings_percentage > 90
        assert comparison.affected_users == 50000
        
    def test_validate_performance_guarantee(self):
        """Test performance guarantee validation."""
        session_id = "test_session_123"
        
        # Mock session metrics
        mock_metrics = {
            "scenario_type": "database_cascade",
            "metrics": {
                "mttr_seconds": 240,  # 4 minutes
                "cost_accumulated": 8000.0,
                "affected_users": 50000
            }
        }
        self.mock_demo_controller.get_real_time_metrics.return_value = mock_metrics
        
        # Validate guarantee
        guarantee = self.analyzer.validate_performance_guarantee(session_id)
        
        assert isinstance(guarantee, PerformanceGuarantee)
        assert guarantee.scenario_type == "database_cascade"
        assert guarantee.guaranteed_completion_minutes == 5
        assert guarantee.actual_completion_minutes == 4.0
        assert guarantee.guarantee_met is True
        assert guarantee.performance_margin == 1.0
        assert guarantee.consistency_score == 1.0  # First run
        
    def test_log_judge_interaction(self):
        """Test judge interaction logging."""
        session_id = "test_session_123"
        judge_id = "judge_001"
        interaction_type = "severity_adjustment"
        interaction_data = {"old_severity": "medium", "new_severity": "high"}
        
        # Mock session state
        mock_state = {"current_phase": "diagnosis", "confidence": 0.85}
        self.mock_demo_controller.get_real_time_metrics.return_value = mock_state
        
        # Log interaction
        interaction_id = self.analyzer.log_judge_interaction(
            session_id, judge_id, interaction_type, interaction_data
        )
        
        assert interaction_id.startswith("interaction_")
        assert len(self.analyzer.judge_interaction_logs) == 1
        
        log = self.analyzer.judge_interaction_logs[0]
        assert log.session_id == session_id
        assert log.judge_id == judge_id
        assert log.interaction_type == interaction_type
        assert log.interaction_data == interaction_data
        assert log.session_state_before == mock_state
        
    def test_generate_comprehensive_demo_report(self):
        """Test comprehensive demo report generation."""
        session_id = "test_session_123"
        
        # Mock session metrics
        mock_metrics = {
            "scenario_type": "database_cascade",
            "metrics": {
                "mttr_seconds": 180,  # 3 minutes
                "cost_accumulated": 6000.0,
                "affected_users": 50000
            }
        }
        self.mock_demo_controller.get_real_time_metrics.return_value = mock_metrics
        
        # Generate report
        report = self.analyzer.generate_comprehensive_demo_report(session_id)
        
        assert report["session_id"] == session_id
        assert "report_timestamp" in report
        assert "mttr_analysis" in report
        assert "business_impact_analysis" in report
        assert "performance_validation" in report
        assert "judge_interactions" in report
        assert "key_achievements" in report
        
        # Verify MTTR analysis
        mttr_analysis = report["mttr_analysis"]
        assert mttr_analysis["traditional_mttr_minutes"] == 45
        assert mttr_analysis["autonomous_mttr_minutes"] == 3.0
        assert mttr_analysis["meets_95_percent_target"] is False  # 93.3% < 95%
        
        # Verify business impact
        business_impact = report["business_impact_analysis"]
        assert business_impact["cost_savings"] == 84000.0
        assert business_impact["affected_users"] == 50000
        
    def test_get_aggregate_performance_metrics(self):
        """Test aggregate performance metrics calculation."""
        # Add some performance history
        self.analyzer.performance_history = {
            "database_cascade": [
                {"completion_time": 3.0, "timestamp": datetime.utcnow()},
                {"completion_time": 3.5, "timestamp": datetime.utcnow()},
                {"completion_time": 2.8, "timestamp": datetime.utcnow()}
            ],
            "ddos_attack": [
                {"completion_time": 2.5, "timestamp": datetime.utcnow()},
                {"completion_time": 2.7, "timestamp": datetime.utcnow()}
            ]
        }
        
        # Get aggregate metrics
        metrics = self.analyzer.get_aggregate_performance_metrics()
        
        assert "aggregate_performance" in metrics
        assert "analysis_timestamp" in metrics
        assert "performance_summary" in metrics
        
        # Verify database_cascade metrics
        db_metrics = metrics["aggregate_performance"]["database_cascade"]
        assert db_metrics["total_runs"] == 3
        assert db_metrics["average_completion_minutes"] == pytest.approx(3.1, abs=0.1)
        assert db_metrics["guarantee_success_rate"] == 1.0  # All under 5 minutes
        
        # Verify overall system metrics
        overall = metrics["aggregate_performance"]["overall_system"]
        assert overall["total_demo_runs"] == 5
        assert overall["overall_guarantee_success_rate"] == 1.0
        
    def test_get_judge_interaction_analytics(self):
        """Test judge interaction analytics."""
        # Add some interaction logs
        from src.services.demo_metrics import JudgeInteractionLog
        
        log1 = JudgeInteractionLog(
            session_id="session_1",
            judge_id="judge_001",
            interaction_timestamp=datetime.utcnow(),
            interaction_type="severity_adjustment",
            interaction_data={"severity": "high"},
            session_state_before={},
            session_state_after={},
            impact_on_metrics={"cost_multiplier": 1.5}
        )
        
        log2 = JudgeInteractionLog(
            session_id="session_2",
            judge_id="judge_001",
            interaction_timestamp=datetime.utcnow(),
            interaction_type="custom_incident",
            interaction_data={"title": "Test incident"},
            session_state_before={},
            session_state_after={},
            impact_on_metrics={"confidence_change": 0.1}
        )
        
        self.analyzer.judge_interaction_logs = [log1, log2]
        
        # Get analytics
        analytics = self.analyzer.get_judge_interaction_analytics("judge_001")
        
        assert analytics["judge_id"] == "judge_001"
        assert analytics["analysis_period"]["total_interactions"] == 2
        assert "interaction_patterns" in analytics
        assert "interaction_impact_analysis" in analytics
        assert "demo_effectiveness" in analytics
        
        # Verify interaction patterns
        patterns = analytics["interaction_patterns"]
        assert patterns["interaction_type_distribution"]["severity_adjustment"] == 1
        assert patterns["interaction_type_distribution"]["custom_incident"] == 1
        
    def test_session_not_found_error(self):
        """Test error handling when session is not found."""
        session_id = "nonexistent_session"
        
        # Mock controller returns None
        self.mock_demo_controller.get_real_time_metrics.return_value = None
        
        # Should raise ValueError
        with pytest.raises(ValueError, match="Session nonexistent_session not found"):
            self.analyzer.calculate_mttr_comparison(session_id)
            
    def test_empty_performance_history(self):
        """Test handling of empty performance history."""
        # Clear performance history
        self.analyzer.performance_history = {}
        
        # Get aggregate metrics
        metrics = self.analyzer.get_aggregate_performance_metrics()
        
        assert metrics["message"] == "No performance history available"
        
    def test_no_interaction_logs(self):
        """Test handling when no interaction logs exist."""
        # Clear interaction logs
        self.analyzer.judge_interaction_logs = []
        
        # Get analytics
        analytics = self.analyzer.get_judge_interaction_analytics("judge_001")
        
        assert "No interaction logs found for judge judge_001" in analytics["message"]


class TestDemoMetricsGlobalInstance:
    """Test global demo metrics analyzer instance."""
    
    def test_get_demo_metrics_analyzer_singleton(self):
        """Test that get_demo_metrics_analyzer returns singleton instance."""
        analyzer1 = get_demo_metrics_analyzer()
        analyzer2 = get_demo_metrics_analyzer()
        
        assert analyzer1 is analyzer2
        assert isinstance(analyzer1, DemoMetricsAnalyzer)


if __name__ == "__main__":
    pytest.main([__file__])