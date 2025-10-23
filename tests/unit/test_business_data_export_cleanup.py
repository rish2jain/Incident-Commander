"""
Unit tests for BusinessDataExportService cleanup functionality.
"""

import pytest
from datetime import datetime

from src.services.business_data_export import BusinessDataExportService, RealTimeCostAnalysis
from src.services.business_impact_calculator import IndustryType, CompanySize


class TestBusinessDataExportServiceCleanup:
    """Test cleanup functionality to prevent memory leaks."""

    def test_cleanup_incident_analysis_removes_entry(self):
        """Test that cleanup_incident_analysis removes the specified incident from memory."""
        service = BusinessDataExportService()
        incident_id = "test_incident_123"
        
        # Add a mock analysis to the service
        mock_analysis = RealTimeCostAnalysis(
            incident_id=incident_id,
            start_time=datetime.utcnow(),
            current_time=datetime.utcnow(),
            duration_minutes=5.0,
            traditional_cost_accumulated=1000.0,
            autonomous_cost_accumulated=50.0,
            cost_savings_realized=950.0,
            projected_final_savings=950.0,
            mttr_improvement_percentage=95.0,
            business_impact_prevented={}
        )
        
        service.real_time_analyses[incident_id] = {
            "analysis": mock_analysis,
            "metrics": {},
            "industry": IndustryType.TECHNOLOGY,
            "company_size": CompanySize.ENTERPRISE,
            "severity": "medium"
        }
        
        # Verify the incident is in memory
        assert incident_id in service.real_time_analyses
        
        # Call cleanup
        service.cleanup_incident_analysis(incident_id)
        
        # Verify the incident has been removed
        assert incident_id not in service.real_time_analyses

    def test_cleanup_incident_analysis_handles_missing_incident(self):
        """Test that cleanup_incident_analysis handles missing incident gracefully."""
        service = BusinessDataExportService()
        non_existent_id = "non_existent_incident"
        
        # Should not raise an exception
        service.cleanup_incident_analysis(non_existent_id)
        
        # Verify no side effects
        assert len(service.real_time_analyses) == 0

    def test_cleanup_incident_analysis_preserves_other_incidents(self):
        """Test that cleanup only removes the specified incident, leaving others intact."""
        service = BusinessDataExportService()
        incident_id_1 = "incident_1"
        incident_id_2 = "incident_2"
        
        # Add two mock analyses
        for incident_id in [incident_id_1, incident_id_2]:
            mock_analysis = RealTimeCostAnalysis(
                incident_id=incident_id,
                start_time=datetime.utcnow(),
                current_time=datetime.utcnow(),
                duration_minutes=5.0,
                traditional_cost_accumulated=1000.0,
                autonomous_cost_accumulated=50.0,
                cost_savings_realized=950.0,
                projected_final_savings=950.0,
                mttr_improvement_percentage=95.0,
                business_impact_prevented={}
            )
            
            service.real_time_analyses[incident_id] = {
                "analysis": mock_analysis,
                "metrics": {},
                "industry": IndustryType.TECHNOLOGY,
                "company_size": CompanySize.ENTERPRISE,
                "severity": "medium"
            }
        
        # Verify both incidents are in memory
        assert incident_id_1 in service.real_time_analyses
        assert incident_id_2 in service.real_time_analyses
        
        # Clean up only the first incident
        service.cleanup_incident_analysis(incident_id_1)
        
        # Verify only the first incident was removed
        assert incident_id_1 not in service.real_time_analyses
        assert incident_id_2 in service.real_time_analyses