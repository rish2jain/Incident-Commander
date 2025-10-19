"""
Integration tests for Business Impact API endpoints

Tests API functionality, request/response validation, and end-to-end workflows.

Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
"""

import pytest
import asyncio
import json
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

from src.main import app
from src.services.business_impact_calculator import IndustryType, CompanySize
from src.services.executive_reporting import ReportType
from src.services.business_data_export import ExportFormat, ExportScope


class TestBusinessImpactAPI:
    """Integration tests for Business Impact API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_roi_analysis_post_endpoint(self, client):
        """Test POST /business-impact/roi-analysis endpoint."""
        request_data = {
            "industry": "ecommerce",
            "company_size": "mid_market",
            "custom_metrics": {
                "annual_revenue": 100000000,
                "employees": 1000,
                "infrastructure_spend": 5000000
            },
            "industry_metrics": {
                "conversion_rate": 0.025,
                "cart_abandonment_rate": 0.70,
                "seasonal_multiplier": 1.8
            }
        }
        
        response = client.post("/business-impact/roi-analysis", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "roi_analysis" in data
        assert "current_state_costs" in data
        assert "future_state_benefits" in data
        assert "industry_specific_analysis" in data
        assert "competitive_advantages" in data
        
        # Validate ROI analysis structure
        roi = data["roi_analysis"]
        assert "investment_grade" in roi
        assert "payback_period_months" in roi
        assert "net_annual_savings" in roi
        assert roi["net_annual_savings"] > 0
    
    def test_roi_analysis_get_endpoint(self, client):
        """Test GET /business-impact/roi-analysis/{industry}/{company_size} endpoint."""
        response = client.get("/business-impact/roi-analysis/financial_services/enterprise")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["industry"] == "financial_services"
        assert data["company_size"] == "enterprise"
        assert "roi_summary" in data
        assert "key_benefits" in data
        assert "competitive_advantages" in data
        
        # Validate ROI summary
        roi_summary = data["roi_summary"]
        assert "investment_grade" in roi_summary
        assert "payback_months" in roi_summary
        assert "annual_savings" in roi_summary
    
    def test_executive_summary_endpoint(self, client):
        """Test GET /business-impact/executive-summary/{industry}/{company_size} endpoint."""
        response = client.get("/business-impact/executive-summary/saas/smb")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "report_id" in data
        assert "executive_summary" in data
        assert "key_findings" in data
        assert "recommendations" in data
        assert len(data["key_findings"]) > 0
        assert len(data["recommendations"]) > 0
    
    def test_performance_comparison_endpoint(self, client):
        """Test GET /business-impact/performance-comparison/{industry}/{company_size} endpoint."""
        response = client.get("/business-impact/performance-comparison/healthcare/fortune_500")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "traditional_approach" in data
        assert "autonomous_approach" in data
        assert "improvements" in data
        
        # Validate traditional vs autonomous comparison
        traditional = data["traditional_approach"]
        autonomous = data["autonomous_approach"]
        
        assert "average_mttr" in traditional
        assert "average_mttr" in autonomous
        assert "automation_coverage" in autonomous
        
        # Autonomous should be better than traditional
        traditional_mttr = float(traditional["average_mttr"].split()[0])
        autonomous_mttr = float(autonomous["average_mttr"].split()[0])
        assert autonomous_mttr < traditional_mttr
    
    def test_executive_report_endpoint(self, client):
        """Test POST /business-impact/executive-report endpoint."""
        params = {
            "report_type": "executive_summary",
            "industry": "technology",
            "company_size": "mid_market"
        }
        
        response = client.post("/business-impact/executive-report", params=params)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["report_type"] == "executive_summary"
        assert data["industry"] == "technology"
        assert data["company_size"] == "mid_market"
        assert "executive_summary" in data
        assert "financial_impact" in data
        assert "performance_metrics" in data
    
    def test_export_json_endpoint(self, client):
        """Test POST /business-impact/export endpoint with JSON format."""
        params = {
            "industry": "ecommerce",
            "company_size": "enterprise"
        }
        
        export_request = {
            "format": "json",
            "scope": "summary",
            "include_charts": True,
            "include_appendices": False
        }
        
        response = client.post(
            "/business-impact/export",
            params=params,
            json=export_request
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        # Verify it's valid JSON
        data = response.json()
        assert "summary" in data
    
    def test_export_csv_endpoint(self, client):
        """Test POST /business-impact/export endpoint with CSV format."""
        params = {
            "industry": "financial_services",
            "company_size": "mid_market"
        }
        
        export_request = {
            "format": "csv",
            "scope": "detailed"
        }
        
        response = client.post(
            "/business-impact/export",
            params=params,
            json=export_request
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv"
        
        # Verify CSV content
        csv_content = response.content.decode('utf-8')
        assert "Metric,Value" in csv_content or "ROI Analysis" in csv_content
    
    def test_export_formats_endpoint(self, client):
        """Test GET /business-impact/export-formats endpoint."""
        response = client.get("/business-impact/export-formats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "formats" in data
        assert "scopes" in data
        
        # Validate format information
        formats = data["formats"]
        format_names = [f["format"] for f in formats]
        assert "json" in format_names
        assert "csv" in format_names
        assert "excel" in format_names
        assert "pdf" in format_names
    
    def test_start_cost_tracking_endpoint(self, client):
        """Test POST /business-impact/incidents/{incident_id}/start-cost-tracking endpoint."""
        incident_id = "test_incident_123"
        
        request_data = {
            "incident_id": incident_id,
            "industry": "saas",
            "company_size": "enterprise",
            "incident_severity": "high"
        }
        
        response = client.post(
            f"/business-impact/incidents/{incident_id}/start-cost-tracking",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["incident_id"] == incident_id
        assert data["status"] == "tracking_started"
        assert data["industry"] == "saas"
        assert data["company_size"] == "enterprise"
        assert "started_at" in data
    
    def test_get_cost_savings_endpoint(self, client):
        """Test GET /business-impact/incidents/{incident_id}/cost-savings endpoint."""
        incident_id = "test_incident_456"
        
        # First start cost tracking
        request_data = {
            "incident_id": incident_id,
            "industry": "ecommerce",
            "company_size": "mid_market"
        }
        
        start_response = client.post(
            f"/business-impact/incidents/{incident_id}/start-cost-tracking",
            json=request_data
        )
        assert start_response.status_code == 200
        
        # Then get cost savings
        response = client.get(f"/business-impact/incidents/{incident_id}/cost-savings")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["incident_id"] == incident_id
        assert "duration_minutes" in data
        assert "cost_savings_realized" in data
        assert "projected_final_savings" in data
        assert data["cost_savings_realized"] >= 0
    
    def test_finalize_cost_analysis_endpoint(self, client):
        """Test POST /business-impact/incidents/{incident_id}/finalize-cost-analysis endpoint."""
        incident_id = "test_incident_789"
        
        # First start cost tracking
        request_data = {
            "incident_id": incident_id,
            "industry": "healthcare",
            "company_size": "fortune_500"
        }
        
        start_response = client.post(
            f"/business-impact/incidents/{incident_id}/start-cost-tracking",
            json=request_data
        )
        assert start_response.status_code == 200
        
        # Then finalize with actual resolution time
        actual_resolution_time = 3.5
        
        response = client.post(
            f"/business-impact/incidents/{incident_id}/finalize-cost-analysis",
            json=actual_resolution_time
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["incident_id"] == incident_id
        assert data["actual_resolution_time_minutes"] == actual_resolution_time
        assert "final_cost_savings" in data
        assert "mttr_improvement_achieved" in data
        assert data["final_cost_savings"] > 0
    
    def test_calculate_incident_impact_endpoint(self, client):
        """Test POST /business-impact/incidents/calculate-impact endpoint."""
        incident_data = {
            "incident_id": "test_impact_incident",
            "duration_minutes": 12.5,
            "severity": "high",
            "affected_services": ["payment-api", "user-service", "notification-service"]
        }
        
        params = {
            "industry": "financial_services",
            "company_size": "enterprise"
        }
        
        response = client.post(
            "/business-impact/incidents/calculate-impact",
            params=params,
            json=incident_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "incident_impact" in data
        assert "business_metrics" in data
        assert "roi_demonstration" in data
        
        # Validate incident impact
        impact = data["incident_impact"]
        assert "traditional_cost" in impact
        assert "autonomous_cost" in impact
        assert "cost_savings" in impact
        assert impact["cost_savings"] > 0
    
    def test_industries_endpoint(self, client):
        """Test GET /business-impact/industries endpoint."""
        response = client.get("/business-impact/industries")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "industries" in data
        industries = data["industries"]
        
        # Verify all supported industries are listed
        industry_names = [ind["industry"] for ind in industries]
        assert "ecommerce" in industry_names
        assert "financial_services" in industry_names
        assert "saas" in industry_names
        assert "healthcare" in industry_names
        
        # Verify industry details
        for industry in industries:
            assert "name" in industry
            assert "description" in industry
            assert "key_metrics" in industry
            assert "typical_downtime_cost_multiplier" in industry
    
    def test_company_sizes_endpoint(self, client):
        """Test GET /business-impact/company-sizes endpoint."""
        response = client.get("/business-impact/company-sizes")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "company_sizes" in data
        sizes = data["company_sizes"]
        
        # Verify all supported company sizes are listed
        size_names = [size["size"] for size in sizes]
        assert "startup" in size_names
        assert "smb" in size_names
        assert "mid_market" in size_names
        assert "enterprise" in size_names
        assert "fortune_500" in size_names
        
        # Verify size details
        for size in sizes:
            assert "name" in size
            assert "description" in size
            assert "typical_revenue_range" in size
            assert "implementation_cost" in size
    
    def test_health_endpoint(self, client):
        """Test GET /business-impact/health endpoint."""
        response = client.get("/business-impact/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "services" in data
        assert "capabilities" in data
        assert "supported_formats" in data
        
        # Verify service health
        services = data["services"]
        assert services["business_calculator"] == "operational"
        assert services["executive_reporting"] == "operational"
        assert services["data_export"] == "operational"
        
        # Verify capabilities
        capabilities = data["capabilities"]
        assert capabilities["roi_analysis"] is True
        assert capabilities["executive_reporting"] is True
        assert capabilities["data_export"] is True
        assert capabilities["real_time_cost_tracking"] is True


class TestAPIValidation:
    """Test API request validation and error handling."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_invalid_industry_type(self, client):
        """Test API handles invalid industry type."""
        response = client.get("/business-impact/roi-analysis/invalid_industry/enterprise")
        
        assert response.status_code == 422  # Validation error
    
    def test_invalid_company_size(self, client):
        """Test API handles invalid company size."""
        response = client.get("/business-impact/roi-analysis/technology/invalid_size")
        
        assert response.status_code == 422  # Validation error
    
    def test_invalid_export_format(self, client):
        """Test API handles invalid export format."""
        params = {
            "industry": "technology",
            "company_size": "enterprise"
        }
        
        export_request = {
            "format": "invalid_format",
            "scope": "summary"
        }
        
        response = client.post(
            "/business-impact/export",
            params=params,
            json=export_request
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_invalid_report_type(self, client):
        """Test API handles invalid report type."""
        params = {
            "report_type": "invalid_report",
            "industry": "technology",
            "company_size": "enterprise"
        }
        
        response = client.post("/business-impact/executive-report", params=params)
        
        assert response.status_code == 422  # Validation error
    
    def test_missing_required_fields(self, client):
        """Test API handles missing required fields."""
        # Missing industry and company_size
        request_data = {
            "custom_metrics": {
                "annual_revenue": 100000000,
                "employees": 1000
            }
        }
        
        response = client.post("/business-impact/roi-analysis", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_invalid_metric_values(self, client):
        """Test API handles invalid metric values."""
        request_data = {
            "industry": "technology",
            "company_size": "enterprise",
            "custom_metrics": {
                "annual_revenue": -100000,  # Invalid negative value
                "employees": 0,  # Invalid zero value
                "infrastructure_spend": -50000  # Invalid negative value
            }
        }
        
        response = client.post("/business-impact/roi-analysis", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_nonexistent_incident_cost_tracking(self, client):
        """Test API handles nonexistent incident for cost tracking."""
        response = client.get("/business-impact/incidents/nonexistent_incident/cost-savings")
        
        assert response.status_code == 404  # Not found


class TestAPIPerformance:
    """Test API performance and response times."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_roi_analysis_response_time(self, client):
        """Test ROI analysis endpoint response time."""
        import time
        
        start_time = time.time()
        
        response = client.get("/business-impact/roi-analysis/technology/enterprise")
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 5.0  # Should respond within 5 seconds
    
    def test_executive_summary_response_time(self, client):
        """Test executive summary endpoint response time."""
        import time
        
        start_time = time.time()
        
        response = client.get("/business-impact/executive-summary/ecommerce/mid_market")
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 3.0  # Should respond within 3 seconds
    
    def test_concurrent_requests(self, client):
        """Test API handles concurrent requests."""
        import concurrent.futures
        import threading
        
        def make_request():
            return client.get("/business-impact/roi-analysis/saas/smb")
        
        # Make 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            responses = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_complete_roi_analysis_workflow(self, client):
        """Test complete ROI analysis workflow."""
        # 1. Get ROI analysis
        roi_response = client.get("/business-impact/roi-analysis/financial_services/enterprise")
        assert roi_response.status_code == 200
        roi_data = roi_response.json()
        
        # 2. Get executive summary
        summary_response = client.get("/business-impact/executive-summary/financial_services/enterprise")
        assert summary_response.status_code == 200
        summary_data = summary_response.json()
        
        # 3. Export data
        export_request = {
            "format": "json",
            "scope": "summary"
        }
        
        export_response = client.post(
            "/business-impact/export",
            params={"industry": "financial_services", "company_size": "enterprise"},
            json=export_request
        )
        assert export_response.status_code == 200
        
        # Verify consistency across responses
        assert roi_data["industry"] == "financial_services"
        assert roi_data["company_size"] == "enterprise"
    
    def test_complete_incident_cost_tracking_workflow(self, client):
        """Test complete incident cost tracking workflow."""
        incident_id = "workflow_test_incident"
        
        # 1. Start cost tracking
        start_request = {
            "incident_id": incident_id,
            "industry": "ecommerce",
            "company_size": "mid_market",
            "incident_severity": "high"
        }
        
        start_response = client.post(
            f"/business-impact/incidents/{incident_id}/start-cost-tracking",
            json=start_request
        )
        assert start_response.status_code == 200
        
        # 2. Get current cost savings
        savings_response = client.get(f"/business-impact/incidents/{incident_id}/cost-savings")
        assert savings_response.status_code == 200
        savings_data = savings_response.json()
        
        # 3. Finalize cost analysis
        finalize_response = client.post(
            f"/business-impact/incidents/{incident_id}/finalize-cost-analysis",
            json=2.8  # Resolution time in minutes
        )
        assert finalize_response.status_code == 200
        finalize_data = finalize_response.json()
        
        # Verify workflow consistency
        assert savings_data["incident_id"] == incident_id
        assert finalize_data["incident_id"] == incident_id
        assert finalize_data["final_cost_savings"] > 0


if __name__ == "__main__":
    pytest.main([__file__])