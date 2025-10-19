"""
Comprehensive patches for external services during testing.
"""

import os
from unittest.mock import patch, AsyncMock, MagicMock
from contextlib import contextmanager


@contextmanager
def patch_all_external_services():
    """Context manager that patches all external services for testing."""
    patches = []
    
    # Store original environment values
    original_env = {}
    env_keys = ['ENVIRONMENT', 'OPENSEARCH_ENDPOINT', 'AWS_ENDPOINT_URL', 'REDIS_URL']
    for key in env_keys:
        original_env[key] = os.environ.get(key)
    
    try:
        # Set test environment variables first
        os.environ.update({
            'ENVIRONMENT': 'test',
            'OPENSEARCH_ENDPOINT': 'http://localhost:9200',
            'AWS_ENDPOINT_URL': 'http://localhost:4566',
            'REDIS_URL': 'redis://localhost:6379',
        })
        
        # Patch OpenSearch
        opensearch_patch = patch('opensearchpy.AsyncOpenSearch')
        mock_opensearch = opensearch_patch.start()
        
        # Configure OpenSearch mock
        mock_os_instance = AsyncMock()
        mock_os_instance.indices.exists = AsyncMock(return_value=False)
        mock_os_instance.indices.create = AsyncMock(return_value={"acknowledged": True})
        mock_os_instance.index = AsyncMock(return_value={"_id": "test-id", "result": "created"})
        mock_os_instance.search = AsyncMock(return_value={
            "hits": {
                "total": {"value": 0},
                "hits": []
            }
        })
        mock_opensearch.return_value = mock_os_instance
        patches.append(opensearch_patch)
        
        # Patch aioboto3
        boto3_patch = patch('aioboto3.Session')
        mock_session_class = boto3_patch.start()
        
        # Create mock session
        mock_session = AsyncMock()
        
        # Mock client creation
        async def mock_client(service_name, **kwargs):
            client = AsyncMock()
            
            if service_name == 'dynamodb':
                client.create_table = AsyncMock(return_value={"TableDescription": {"TableStatus": "ACTIVE"}})
                client.put_item = AsyncMock(return_value={"ResponseMetadata": {"HTTPStatusCode": 200}})
                client.get_item = AsyncMock(return_value={"Item": {}})
                client.query = AsyncMock(return_value={"Items": [], "Count": 0})
                client.scan = AsyncMock(return_value={"Items": [], "Count": 0})
            
            elif service_name == 'bedrock-runtime':
                client.invoke_model = AsyncMock(return_value={
                    "body": AsyncMock(),
                    "contentType": "application/json"
                })
            
            elif service_name == 's3':
                client.create_bucket = AsyncMock(return_value={"Location": "/test-bucket"})
                client.put_object = AsyncMock(return_value={"ETag": "test-etag"})
                client.get_object = AsyncMock(return_value={
                    "Body": AsyncMock(),
                    "ContentLength": 100
                })
            
            elif service_name == 'cloudwatch':
                client.get_metric_statistics = AsyncMock(return_value={
                    "Datapoints": [{"Timestamp": "2023-01-01", "Average": 50.0}]
                })
                client.put_metric_data = AsyncMock(return_value={"ResponseMetadata": {"HTTPStatusCode": 200}})
            
            return client
        
        mock_session.client = mock_client
        mock_session_class.return_value = mock_session
        patches.append(boto3_patch)
        
        # Patch Redis
        redis_patch = patch('redis.asyncio.Redis')
        mock_redis_class = redis_patch.start()
        
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
        patches.append(redis_patch)
        
        # Patch httpx for external API calls
        httpx_patch = patch('httpx.AsyncClient')
        mock_httpx = httpx_patch.start()
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_response.text = "OK"
        
        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client_instance.post.return_value = mock_response
        mock_client_instance.put.return_value = mock_response
        mock_client_instance.delete.return_value = mock_response
        
        mock_httpx.return_value.__aenter__.return_value = mock_client_instance
        patches.append(httpx_patch)
        
        yield
        
    finally:
        # Stop all patches
        for p in patches:
            p.stop()
        
        # Restore original environment variables
        for key, original_value in original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value


def apply_test_patches():
    """Apply test patches as a decorator or context manager."""
    return patch_all_external_services()