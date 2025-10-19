"""
Integration tests for Documentation API

Tests API endpoints for documentation generation and management.

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

from src.main import app
from src.services.aws import AWSServiceFactory


class TestDocumentationAPI:
    """Integration tests for documentation API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_services(self):
        """Mock service dependencies."""
        with patch('src.api.dependencies.get_services') as mock_get_services:
            mock_container = Mock()
            mock_container.aws_factory = Mock(spec=AWSServiceFactory)
            mock_get_services.return_value = mock_container
            yield mock_container
    
    def test_generate_runbook_endpoint(self, client, mock_services):
        """Test runbook generation endpoint."""
        request_data = {
            "incident_id": "test_incident_123",
            "resolution_actions": [
                "Scale database connection pool",
                "Implement circuit breaker",
                "Monitor system health"
            ],
            "diagnosis_data": {
                "root_cause": "Connection pool exhaustion",
                "confidence": 0.92
            }
        }
        
        with patch('src.services.documentation_generator.get_documentation_generator') as mock_get_doc_gen:
            mock_doc_gen = Mock()
            mock_runbook = Mock()
            mock_runbook.runbook_id = "rb_123"
            mock_runbook.title = "Test Runbook"
            mock_runbook.created_at = datetime.utcnow()
            mock_runbook.estimated_time = "10-15 minutes"
            mock_runbook.difficulty_level = "Medium"
            mock_runbook.success_rate = 95.0
            mock_runbook.diagnosis_steps = ["Step 1", "Step 2"]
            mock_runbook.resolution_steps = ["Fix 1", "Fix 2"]
            mock_runbook.verification_steps = ["Verify 1"]
            mock_runbook.rollback_steps = ["Rollback 1"]
            mock_runbook.prerequisites = ["Access required"]
            mock_runbook.symptoms = ["Symptom 1"]
            
            mock_doc_gen.generate_runbook_from_incident = AsyncMock(return_value=mock_runbook)
            mock_get_doc_gen.return_value = mock_doc_gen
            
            response = client.post("/documentation/runbooks/generate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["runbook_id"] == "rb_123"
        assert data["title"] == "Test Runbook"
        assert "steps" in data
        assert "diagnosis" in data["steps"]
        assert "resolution" in data["steps"]
    
    def test_get_runbook_endpoint(self, client, mock_services):
        """Test get runbook by ID endpoint."""
        runbook_id = "test_runbook_456"
        
        with patch('src.services.documentation_generator.get_documentation_generator') as mock_get_doc_gen:
            mock_doc_gen = Mock()
            mock_runbook = Mock()
            mock_runbook.runbook_id = runbook_id
            mock_runbook.title = "Retrieved Runbook"
            mock_runbook.problem_description = "Test problem"
            mock_runbook.symptoms = ["Symptom A"]
            mock_runbook.diagnosis_steps = ["Diagnose A"]
            mock_runbook.resolution_steps = ["Resolve A"]
            mock_runbook.verification_steps = ["Verify A"]
            mock_runbook.rollback_steps = ["Rollback A"]
            mock_runbook.prerequisites = ["Prereq A"]
            mock_runbook.estimated_time = "5 minutes"
            mock_runbook.difficulty_level = "Low"
            mock_runbook.success_rate = 98.0
            mock_runbook.created_from_incident = "incident_123"
            mock_runbook.created_at = datetime.utcnow()
            mock_runbook.last_updated = datetime.utcnow()
            mock_runbook.version = 1
            
            mock_doc_gen.get_runbook_by_id = AsyncMock(return_value=mock_runbook)
            mock_get_doc_gen.return_value = mock_doc_gen
            
            response = client.get(f"/documentation/runbooks/{runbook_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["runbook_id"] == runbook_id
        assert data["title"] == "Retrieved Runbook"
        assert "symptoms" in data
        assert "diagnosis_steps" in data
    
    def test_runbook_not_found(self, client, mock_services):
        """Test runbook not found scenario."""
        runbook_id = "nonexistent_runbook"
        
        with patch('src.services.documentation_generator.get_documentation_generator') as mock_get_doc_gen:
            mock_doc_gen = Mock()
            mock_doc_gen.get_runbook_by_id = AsyncMock(return_value=None)
            mock_get_doc_gen.return_value = mock_doc_gen
            
            response = client.get(f"/documentation/runbooks/{runbook_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


if __name__ == "__main__":
    pytest.main([__file__])