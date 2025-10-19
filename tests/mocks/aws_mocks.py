"""
Comprehensive AWS service mocks for testing.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


class MockOpenSearchClient:
    """Mock OpenSearch client for testing."""
    
    def __init__(self):
        self.indices = {}
        self.documents = {}
    
    async def indices_exists(self, index: str) -> bool:
        """Check if index exists."""
        return index in self.indices
    
    async def indices_create(self, index: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Create index."""
        self.indices[index] = body
        return {"acknowledged": True}
    
    async def index(self, index: str, body: Dict[str, Any], id: Optional[str] = None) -> Dict[str, Any]:
        """Index document."""
        doc_id = id or f"doc_{len(self.documents)}"
        if index not in self.documents:
            self.documents[index] = {}
        self.documents[index][doc_id] = body
        return {"_id": doc_id, "result": "created"}
    
    async def search(self, index: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Search documents."""
        # Return mock search results
        return {
            "hits": {
                "total": {"value": 0},
                "hits": []
            }
        }
    
    async def delete(self, index: str, id: str) -> Dict[str, Any]:
        """Delete document."""
        if index in self.documents and id in self.documents[index]:
            del self.documents[index][id]
        return {"result": "deleted"}


class MockDynamoDBClient:
    """Mock DynamoDB client for testing."""
    
    def __init__(self):
        self.tables = {}
    
    async def create_table(self, **kwargs) -> Dict[str, Any]:
        """Create table."""
        table_name = kwargs.get('TableName')
        self.tables[table_name] = {}
        return {"TableDescription": {"TableStatus": "ACTIVE"}}
    
    async def put_item(self, **kwargs) -> Dict[str, Any]:
        """Put item."""
        table_name = kwargs.get('TableName')
        item = kwargs.get('Item')
        if table_name not in self.tables:
            self.tables[table_name] = {}
        
        # Generate a simple key
        key = f"item_{len(self.tables[table_name])}"
        self.tables[table_name][key] = item
        return {"ResponseMetadata": {"HTTPStatusCode": 200}}
    
    async def get_item(self, **kwargs) -> Dict[str, Any]:
        """Get item."""
        return {"Item": {}}
    
    async def query(self, **kwargs) -> Dict[str, Any]:
        """Query items."""
        return {"Items": [], "Count": 0}
    
    async def scan(self, **kwargs) -> Dict[str, Any]:
        """Scan items."""
        return {"Items": [], "Count": 0}


class MockBedrockClient:
    """Mock Bedrock client for testing."""
    
    async def invoke_model(self, **kwargs) -> Dict[str, Any]:
        """Invoke model."""
        return {
            "body": b'{"completion": "Mock AI response", "stop_reason": "end_turn"}',
            "contentType": "application/json"
        }
    
    async def list_foundation_models(self, **kwargs) -> Dict[str, Any]:
        """List foundation models."""
        return {
            "modelSummaries": [
                {
                    "modelId": "anthropic.claude-3-sonnet-20240229-v1:0",
                    "modelName": "Claude 3 Sonnet"
                }
            ]
        }


class MockS3Client:
    """Mock S3 client for testing."""
    
    def __init__(self):
        self.buckets = {}
    
    async def create_bucket(self, **kwargs) -> Dict[str, Any]:
        """Create bucket."""
        bucket_name = kwargs.get('Bucket')
        self.buckets[bucket_name] = {}
        return {"Location": f"/{bucket_name}"}
    
    async def put_object(self, **kwargs) -> Dict[str, Any]:
        """Put object."""
        bucket = kwargs.get('Bucket')
        key = kwargs.get('Key')
        body = kwargs.get('Body')
        
        if bucket not in self.buckets:
            self.buckets[bucket] = {}
        
        self.buckets[bucket][key] = body
        return {"ETag": "mock-etag"}
    
    async def get_object(self, **kwargs) -> Dict[str, Any]:
        """Get object."""
        return {
            "Body": AsyncMock(),
            "ContentLength": 100,
            "LastModified": datetime.utcnow()
        }


class MockCloudWatchClient:
    """Mock CloudWatch client for testing."""
    
    async def get_metric_statistics(self, **kwargs) -> Dict[str, Any]:
        """Get metric statistics."""
        return {
            "Datapoints": [
                {
                    "Timestamp": datetime.utcnow(),
                    "Average": 50.0,
                    "Unit": "Percent"
                }
            ]
        }
    
    async def put_metric_data(self, **kwargs) -> Dict[str, Any]:
        """Put metric data."""
        return {"ResponseMetadata": {"HTTPStatusCode": 200}}


class MockKinesisClient:
    """Mock Kinesis client for testing."""
    
    def __init__(self):
        self.streams = {}
    
    async def create_stream(self, **kwargs) -> Dict[str, Any]:
        """Create stream."""
        stream_name = kwargs.get('StreamName')
        self.streams[stream_name] = []
        return {"ResponseMetadata": {"HTTPStatusCode": 200}}
    
    async def put_record(self, **kwargs) -> Dict[str, Any]:
        """Put record."""
        stream_name = kwargs.get('StreamName')
        data = kwargs.get('Data')
        
        if stream_name not in self.streams:
            self.streams[stream_name] = []
        
        self.streams[stream_name].append(data)
        return {
            "ShardId": "shardId-000000000000",
            "SequenceNumber": "12345"
        }


class MockAWSServiceFactory:
    """Mock AWS service factory that provides all mocked services."""
    
    def __init__(self):
        self._opensearch_client = MockOpenSearchClient()
        self._dynamodb_client = MockDynamoDBClient()
        self._bedrock_client = MockBedrockClient()
        self._s3_client = MockS3Client()
        self._cloudwatch_client = MockCloudWatchClient()
        self._kinesis_client = MockKinesisClient()
    
    async def get_opensearch_client(self) -> MockOpenSearchClient:
        """Get OpenSearch client."""
        return self._opensearch_client
    
    async def get_dynamodb_client(self) -> MockDynamoDBClient:
        """Get DynamoDB client."""
        return self._dynamodb_client
    
    async def get_bedrock_client(self) -> MockBedrockClient:
        """Get Bedrock client."""
        return self._bedrock_client
    
    async def get_s3_client(self) -> MockS3Client:
        """Get S3 client."""
        return self._s3_client
    
    async def get_cloudwatch_client(self) -> MockCloudWatchClient:
        """Get CloudWatch client."""
        return self._cloudwatch_client
    
    async def get_kinesis_client(self) -> MockKinesisClient:
        """Get Kinesis client."""
        return self._kinesis_client


def create_mock_aws_session():
    """Create a mock aioboto3 session."""
    session = MagicMock()
    
    # Mock client creation
    async def mock_client(service_name, **kwargs):
        if service_name == 'opensearch':
            return MockOpenSearchClient()
        elif service_name == 'dynamodb':
            return MockDynamoDBClient()
        elif service_name == 'bedrock-runtime':
            return MockBedrockClient()
        elif service_name == 's3':
            return MockS3Client()
        elif service_name == 'cloudwatch':
            return MockCloudWatchClient()
        elif service_name == 'kinesis':
            return MockKinesisClient()
        else:
            return AsyncMock()
    
    session.client = mock_client
    return session


# Context managers for patching AWS services
class MockAWSServices:
    """Context manager for mocking all AWS services."""
    
    def __init__(self):
        self.patches = []
    
    def __enter__(self):
        # Patch aioboto3.Session
        session_patch = patch('aioboto3.Session', return_value=create_mock_aws_session())
        self.patches.append(session_patch)
        
        # Patch opensearch client
        opensearch_patch = patch('opensearchpy.AsyncOpenSearch', MockOpenSearchClient)
        self.patches.append(opensearch_patch)
        
        # Start all patches
        for p in self.patches:
            p.start()
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Stop all patches
        for p in self.patches:
            p.stop()