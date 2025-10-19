"""
LocalStack fixtures and offline testing infrastructure for AWS-dependent services.
"""

import asyncio
import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

import aioboto3
from botocore.exceptions import ClientError

from src.utils.config import config
from src.utils.logging import get_logger
from src.services.aws import AWSServiceFactory

logger = get_logger("localstack_fixtures")


class LocalStackManager:
    """Manages LocalStack services and fixtures for offline testing."""
    
    def __init__(self):
        """Initialize LocalStack manager."""
        self.localstack_endpoint = os.getenv('AWS_ENDPOINT_URL', 'http://localhost:4566')
        self.is_localstack = 'localhost' in self.localstack_endpoint or '127.0.0.1' in self.localstack_endpoint
        self._initialized_services: set = set()
        self._service_factory: Optional[AWSServiceFactory] = None
    
    def get_service_factory(self) -> AWSServiceFactory:
        """Get AWS service factory configured for LocalStack."""
        if not self._service_factory:
            self._service_factory = AWSServiceFactory()
        return self._service_factory
    
    async def initialize_all_services(self):
        """Initialize all AWS services in LocalStack."""
        if not self.is_localstack:
            logger.info("Not using LocalStack, skipping initialization")
            return
        
        logger.info("Initializing LocalStack services...")
        
        # Initialize services in dependency order
        await self.initialize_dynamodb()
        await self.initialize_kinesis()
        await self.initialize_s3()
        await self.initialize_step_functions()
        await self.initialize_bedrock_stubs()
        await self.initialize_opensearch()
        
        logger.info("LocalStack services initialized successfully")
    
    async def initialize_dynamodb(self):
        """Initialize DynamoDB tables in LocalStack."""
        if 'dynamodb' in self._initialized_services:
            return
        
        try:
            service_factory = self.get_service_factory()
            client = await service_factory.get_dynamodb_client()
            
            # Create incident events table
            await self._create_table_if_not_exists(
                client,
                table_name='incident-commander-events',
                key_schema=[
                    {'AttributeName': 'partition_key', 'KeyType': 'HASH'},
                    {'AttributeName': 'sort_key', 'KeyType': 'RANGE'}
                ],
                attribute_definitions=[
                    {'AttributeName': 'partition_key', 'AttributeType': 'S'},
                    {'AttributeName': 'sort_key', 'AttributeType': 'S'},
                    {'AttributeName': 'incident_id', 'AttributeType': 'S'},
                    {'AttributeName': 'timestamp', 'AttributeType': 'S'}
                ],
                global_secondary_indexes=[
                    {
                        'IndexName': 'incident-id-index',
                        'KeySchema': [
                            {'AttributeName': 'incident_id', 'KeyType': 'HASH'},
                            {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'}
                    }
                ]
            )
            
            # Create agent state table
            await self._create_table_if_not_exists(
                client,
                table_name='agent-state',
                key_schema=[
                    {'AttributeName': 'agent_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                attribute_definitions=[
                    {'AttributeName': 'agent_id', 'AttributeType': 'S'},
                    {'AttributeName': 'timestamp', 'AttributeType': 'S'}
                ]
            )
            
            # Create audit logs table
            await self._create_table_if_not_exists(
                client,
                table_name='audit-logs',
                key_schema=[
                    {'AttributeName': 'log_id', 'KeyType': 'HASH'}
                ],
                attribute_definitions=[
                    {'AttributeName': 'log_id', 'AttributeType': 'S'},
                    {'AttributeName': 'timestamp', 'AttributeType': 'S'}
                ],
                global_secondary_indexes=[
                    {
                        'IndexName': 'timestamp-index',
                        'KeySchema': [
                            {'AttributeName': 'timestamp', 'KeyType': 'HASH'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'}
                    }
                ]
            )
            
            self._initialized_services.add('dynamodb')
            logger.info("DynamoDB tables initialized in LocalStack")
            
        except Exception as e:
            logger.error(f"Failed to initialize DynamoDB in LocalStack: {e}")
            raise
    
    async def initialize_kinesis(self):
        """Initialize Kinesis streams in LocalStack."""
        if 'kinesis' in self._initialized_services:
            return
        
        try:
            service_factory = self.get_service_factory()
            client = await service_factory.get_kinesis_client()
            
            # Create incident event stream
            await self._create_stream_if_not_exists(
                client,
                stream_name='incident-event-stream',
                shard_count=2
            )
            
            # Create agent communication stream
            await self._create_stream_if_not_exists(
                client,
                stream_name='agent-communication-stream',
                shard_count=1
            )
            
            self._initialized_services.add('kinesis')
            logger.info("Kinesis streams initialized in LocalStack")
            
        except Exception as e:
            logger.error(f"Failed to initialize Kinesis in LocalStack: {e}")
            raise
    
    async def initialize_s3(self):
        """Initialize S3 buckets in LocalStack."""
        if 's3' in self._initialized_services:
            return
        
        try:
            service_factory = self.get_service_factory()
            client = await service_factory.get_s3_client()
            
            # Create buckets
            buckets = [
                'incident-commander-archive',
                'incident-commander-artifacts',
                'incident-commander-backups'
            ]
            
            for bucket_name in buckets:
                await self._create_bucket_if_not_exists(client, bucket_name)
            
            self._initialized_services.add('s3')
            logger.info("S3 buckets initialized in LocalStack")
            
        except Exception as e:
            logger.error(f"Failed to initialize S3 in LocalStack: {e}")
            raise
    
    async def initialize_step_functions(self):
        """Initialize Step Functions state machines in LocalStack."""
        if 'stepfunctions' in self._initialized_services:
            return
        
        try:
            service_factory = self.get_service_factory()
            client = await service_factory.get_stepfunctions_client()
            
            # Create consensus state machine
            consensus_definition = {
                "Comment": "Consensus coordination state machine",
                "StartAt": "InitiateConsensus",
                "States": {
                    "InitiateConsensus": {
                        "Type": "Task",
                        "Resource": "arn:aws:states:::lambda:invoke",
                        "Parameters": {
                            "FunctionName": "consensus-coordinator",
                            "Payload.$": "$"
                        },
                        "Next": "EvaluateConsensus"
                    },
                    "EvaluateConsensus": {
                        "Type": "Choice",
                        "Choices": [
                            {
                                "Variable": "$.consensus_reached",
                                "BooleanEquals": True,
                                "Next": "ConsensusSuccess"
                            }
                        ],
                        "Default": "ConsensusTimeout"
                    },
                    "ConsensusSuccess": {
                        "Type": "Succeed"
                    },
                    "ConsensusTimeout": {
                        "Type": "Fail",
                        "Cause": "Consensus timeout"
                    }
                }
            }
            
            await self._create_state_machine_if_not_exists(
                client,
                name='consensus-coordinator',
                definition=consensus_definition,
                role_arn='arn:aws:iam::000000000000:role/StepFunctionsRole'
            )
            
            self._initialized_services.add('stepfunctions')
            logger.info("Step Functions state machines initialized in LocalStack")
            
        except Exception as e:
            logger.error(f"Failed to initialize Step Functions in LocalStack: {e}")
            raise
    
    async def initialize_bedrock_stubs(self):
        """Initialize Bedrock service stubs in LocalStack."""
        if 'bedrock' in self._initialized_services:
            return
        
        try:
            # LocalStack doesn't fully support Bedrock, so we create mock responses
            # This is handled by the BedrockMockClient class below
            self._initialized_services.add('bedrock')
            logger.info("Bedrock stubs initialized in LocalStack")
            
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock stubs in LocalStack: {e}")
            raise
    
    async def initialize_opensearch(self):
        """Initialize OpenSearch collections in LocalStack."""
        if 'opensearch' in self._initialized_services:
            return
        
        try:
            service_factory = self.get_service_factory()
            client = await service_factory.get_opensearch_client()
            
            # Create incident patterns collection
            await self._create_collection_if_not_exists(
                client,
                name='incident-patterns',
                type='SEARCH'
            )
            
            self._initialized_services.add('opensearch')
            logger.info("OpenSearch collections initialized in LocalStack")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenSearch in LocalStack: {e}")
            # OpenSearch Serverless might not be fully supported in LocalStack
            logger.warning("OpenSearch initialization failed, continuing without it")
    
    async def _create_table_if_not_exists(self, client, table_name: str, key_schema: List[Dict], 
                                        attribute_definitions: List[Dict], 
                                        global_secondary_indexes: List[Dict] = None):
        """Create DynamoDB table if it doesn't exist."""
        try:
            await client.describe_table(TableName=table_name)
            logger.debug(f"Table {table_name} already exists")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                create_params = {
                    'TableName': table_name,
                    'KeySchema': key_schema,
                    'AttributeDefinitions': attribute_definitions,
                    'BillingMode': 'PAY_PER_REQUEST'
                }
                
                if global_secondary_indexes:
                    create_params['GlobalSecondaryIndexes'] = global_secondary_indexes
                
                await client.create_table(**create_params)
                logger.info(f"Created table: {table_name}")
            else:
                raise
    
    async def _create_stream_if_not_exists(self, client, stream_name: str, shard_count: int):
        """Create Kinesis stream if it doesn't exist."""
        try:
            await client.describe_stream(StreamName=stream_name)
            logger.debug(f"Stream {stream_name} already exists")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                await client.create_stream(
                    StreamName=stream_name,
                    ShardCount=shard_count
                )
                logger.info(f"Created stream: {stream_name}")
            else:
                raise
    
    async def _create_bucket_if_not_exists(self, client, bucket_name: str):
        """Create S3 bucket if it doesn't exist."""
        try:
            await client.head_bucket(Bucket=bucket_name)
            logger.debug(f"Bucket {bucket_name} already exists")
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                await client.create_bucket(Bucket=bucket_name)
                logger.info(f"Created bucket: {bucket_name}")
            else:
                raise
    
    async def _create_state_machine_if_not_exists(self, client, name: str, definition: Dict, role_arn: str):
        """Create Step Functions state machine if it doesn't exist."""
        try:
            await client.describe_state_machine(stateMachineArn=f"arn:aws:states:us-east-1:000000000000:stateMachine:{name}")
            logger.debug(f"State machine {name} already exists")
        except ClientError as e:
            if e.response['Error']['Code'] == 'StateMachineDoesNotExist':
                await client.create_state_machine(
                    name=name,
                    definition=json.dumps(definition),
                    roleArn=role_arn
                )
                logger.info(f"Created state machine: {name}")
            else:
                raise
    
    async def _create_collection_if_not_exists(self, client, name: str, type: str):
        """Create OpenSearch collection if it doesn't exist."""
        try:
            collections = await client.list_collections()
            existing_names = [col['name'] for col in collections.get('collectionSummaries', [])]
            
            if name not in existing_names:
                await client.create_collection(
                    name=name,
                    type=type
                )
                logger.info(f"Created collection: {name}")
            else:
                logger.debug(f"Collection {name} already exists")
        except Exception as e:
            logger.warning(f"Failed to create collection {name}: {e}")
    
    async def cleanup(self):
        """Clean up LocalStack resources."""
        if not self.is_localstack:
            return
        
        logger.info("Cleaning up LocalStack resources...")
        self._initialized_services.clear()
        
        if self._service_factory:
            await self._service_factory.cleanup()


class BedrockMockClient:
    """Mock Bedrock client for LocalStack testing."""
    
    def __init__(self):
        """Initialize mock Bedrock client."""
        self.model_responses = {
            'anthropic.claude-3-5-sonnet-20241022-v2:0': {
                'completion': 'This is a mock response from Claude 3.5 Sonnet for testing purposes.'
            },
            'anthropic.claude-3-haiku-20240307-v1:0': {
                'completion': 'This is a mock response from Claude 3 Haiku for testing purposes.'
            },
            'amazon.titan-embed-text-v1': {
                'embedding': [0.1] * 1536  # Mock embedding vector
            }
        }
    
    async def invoke_model(self, modelId: str, body: str, contentType: str = 'application/json'):
        """Mock model invocation."""
        await asyncio.sleep(0.1)  # Simulate network delay
        
        if modelId in self.model_responses:
            response_body = self.model_responses[modelId]
        else:
            response_body = {'completion': f'Mock response for {modelId}'}
        
        class MockResponse:
            def __init__(self, body_content):
                self._body = json.dumps(body_content).encode()
            
            def read(self):
                return self._body
        
        return {
            'body': MockResponse(response_body),
            'contentType': 'application/json'
        }


# Global LocalStack manager instance
_localstack_manager: Optional[LocalStackManager] = None

def get_localstack_manager() -> LocalStackManager:
    """Get or create the global LocalStack manager instance."""
    global _localstack_manager
    if _localstack_manager is None:
        _localstack_manager = LocalStackManager()
    return _localstack_manager


async def initialize_localstack_for_testing():
    """Initialize LocalStack services for testing."""
    manager = get_localstack_manager()
    if manager.is_localstack:
        await manager.initialize_all_services()
        logger.info("LocalStack initialized for testing")
    else:
        logger.info("Not using LocalStack, skipping initialization")


async def cleanup_localstack():
    """Clean up LocalStack resources."""
    manager = get_localstack_manager()
    await manager.cleanup()