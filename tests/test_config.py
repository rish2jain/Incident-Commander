"""
Test environment configuration and utilities.
"""

import os
import asyncio
from typing import Dict, Any
from unittest.mock import patch, MagicMock, AsyncMock


class TestEnvironment:
    """Test environment configuration manager."""
    
    @staticmethod
    def setup_test_env():
        """Set up test environment variables."""
        test_env = {
            # AWS Configuration
            'AWS_ACCESS_KEY_ID': 'test-access-key',
            'AWS_SECRET_ACCESS_KEY': 'test-secret-key',
            'AWS_DEFAULT_REGION': 'us-east-1',
            'AWS_REGION': 'us-east-1',
            'AWS_ENDPOINT_URL': 'http://localhost:4566',
            
            # Application Configuration
            'ENVIRONMENT': 'test',
            'DEBUG': 'true',
            'LOG_LEVEL': 'DEBUG',
            
            # Service Configuration
            'REDIS_URL': 'redis://localhost:6379',
            'DATABASE_URL': 'sqlite:///:memory:',
            
            # External Service Configuration (mocked)
            'DATADOG_API_KEY': 'test-datadog-key',
            'PAGERDUTY_API_KEY': 'test-pagerduty-key',
            'SLACK_BOT_TOKEN': 'test-slack-token',
            'OPENAI_API_KEY': 'test-openai-key',
            
            # OpenSearch Configuration (mocked)
            'OPENSEARCH_ENDPOINT': 'http://localhost:9200',
            'OPENSEARCH_USERNAME': 'test',
            'OPENSEARCH_PASSWORD': 'test',
            
            # Bedrock Configuration (mocked)
            'BEDROCK_REGION': 'us-east-1',
            'BEDROCK_MODEL_ID': 'anthropic.claude-3-sonnet-20240229-v1:0',
            
            # Cost and Performance Limits
            'COST_BUDGET_LIMIT': '200.0',
            'MAX_CONCURRENT_INCIDENTS': '10',
            'AGENT_TIMEOUT_SECONDS': '30',
        }
        
        for key, value in test_env.items():
            os.environ.setdefault(key, value)


class MockServiceManager:
    """Manager for mock services during testing."""
    
    def __init__(self):
        self.active_patches = []
        self.mock_services = {}
    
    def start_mocks(self):
        """Start all service mocks."""
        # Mock external HTTP calls
        self._mock_external_apis()
        
        # Mock AWS services
        self._mock_aws_services()
        
        # Mock Redis
        self._mock_redis()
        
        return self
    
    def stop_mocks(self):
        """Stop all service mocks."""
        for patch_obj in self.active_patches:
            patch_obj.stop()
        self.active_patches.clear()
    
    def _mock_external_apis(self):
        """Mock external API calls."""
        # Mock httpx for external API calls
        httpx_patch = patch('httpx.AsyncClient')
        mock_client = httpx_patch.start()
        
        # Configure mock responses
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_response.text = "OK"
        
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        self.active_patches.append(httpx_patch)
    
    def _mock_aws_services(self):
        """Mock AWS service clients."""
        from tests.mocks.aws_mocks import create_mock_aws_session
        
        # Mock aioboto3.Session
        session_patch = patch('aioboto3.Session')
        mock_session_class = session_patch.start()
        mock_session_class.return_value = create_mock_aws_session()
        
        self.active_patches.append(session_patch)
        
        # Mock opensearch client
        opensearch_patch = patch('opensearchpy.AsyncOpenSearch')
        mock_opensearch = opensearch_patch.start()
        
        # Configure opensearch mock
        mock_opensearch.return_value.indices.exists = AsyncMock(return_value=False)
        mock_opensearch.return_value.indices.create = AsyncMock(return_value={"acknowledged": True})
        mock_opensearch.return_value.index = AsyncMock(return_value={"_id": "test-id"})
        mock_opensearch.return_value.search = AsyncMock(return_value={"hits": {"hits": []}})
        
        self.active_patches.append(opensearch_patch)
    
    def _mock_redis(self):
        """Mock Redis client."""
        redis_patch = patch('redis.asyncio.Redis')
        mock_redis_class = redis_patch.start()
        
        # Create mock Redis instance
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.delete = AsyncMock(return_value=1)
        mock_redis.exists = AsyncMock(return_value=False)
        mock_redis.lpush = AsyncMock(return_value=1)
        mock_redis.rpop = AsyncMock(return_value=None)
        mock_redis.llen = AsyncMock(return_value=0)
        mock_redis.close = AsyncMock()
        mock_redis.aclose = AsyncMock()
        
        mock_redis_class.from_url.return_value = mock_redis
        mock_redis_class.return_value = mock_redis
        
        self.active_patches.append(redis_patch)
    
    def __enter__(self):
        return self.start_mocks()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_mocks()


# Global test configuration
def setup_test_environment():
    """Set up the complete test environment."""
    TestEnvironment.setup_test_env()


# Pytest plugin hooks
def pytest_configure(config):
    """Configure pytest with test environment."""
    setup_test_environment()


def pytest_sessionstart(session):
    """Set up test session."""
    setup_test_environment()