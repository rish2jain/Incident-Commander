"""
AWS service clients and authentication management.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Set, Callable, TypeVar
import json
import random
import time

import aioboto3
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.config import Config

from src.utils.config import config
from src.utils.logging import get_logger
from src.utils.exceptions import AuthenticationError, ConfigurationError

T = TypeVar('T')


logger = get_logger("aws_services")


class RetryConfig:
    """Configuration for retry and backoff behavior."""
    
    def __init__(self, 
                 max_retries: int = 3,
                 base_delay: float = 1.0,
                 max_delay: float = 60.0,
                 exponential_base: float = 2.0,
                 jitter: bool = True):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt with exponential backoff and jitter."""
        delay = min(self.base_delay * (self.exponential_base ** attempt), self.max_delay)
        
        if self.jitter:
            # Add jitter to prevent thundering herd
            delay = delay * (0.5 + random.random() * 0.5)
        
        return delay


async def retry_with_backoff(
    func: Callable[..., T],
    retry_config: RetryConfig = None,
    timeout: float = None,
    retryable_exceptions: tuple = None
) -> T:
    """
    Execute function with exponential backoff retry logic.
    
    Args:
        func: Async function to execute
        retry_config: Retry configuration
        timeout: Overall timeout for all attempts
        retryable_exceptions: Tuple of exceptions that should trigger retry
        
    Returns:
        Function result
        
    Raises:
        Last exception if all retries exhausted
    """
    if retry_config is None:
        retry_config = RetryConfig()
    
    if retryable_exceptions is None:
        retryable_exceptions = (ClientError, ConnectionError, TimeoutError)
    
    start_time = time.time()
    last_exception = None
    
    for attempt in range(retry_config.max_retries + 1):
        try:
            if timeout:
                remaining_time = timeout - (time.time() - start_time)
                if remaining_time <= 0:
                    raise TimeoutError("Overall timeout exceeded")
                
                return await asyncio.wait_for(func(), timeout=remaining_time)
            else:
                return await func()
                
        except retryable_exceptions as e:
            last_exception = e
            
            if attempt == retry_config.max_retries:
                logger.error(f"All retry attempts exhausted. Last error: {e}")
                raise
            
            # Check if this is a throttling error that we should retry
            if isinstance(e, ClientError):
                error_code = e.response.get('Error', {}).get('Code', '')
                if error_code in ['Throttling', 'ThrottlingException', 'RequestLimitExceeded']:
                    delay = retry_config.get_delay(attempt)
                    logger.warning(f"AWS throttling detected, retrying in {delay:.2f}s (attempt {attempt + 1})")
                    await asyncio.sleep(delay)
                    continue
                elif error_code in ['ServiceUnavailable', 'InternalError']:
                    delay = retry_config.get_delay(attempt)
                    logger.warning(f"AWS service error, retrying in {delay:.2f}s (attempt {attempt + 1})")
                    await asyncio.sleep(delay)
                    continue
                else:
                    # Non-retryable error
                    raise
            
            delay = retry_config.get_delay(attempt)
            logger.warning(f"Retrying after error: {e}. Waiting {delay:.2f}s (attempt {attempt + 1})")
            await asyncio.sleep(delay)
    
    # Should never reach here, but just in case
    if last_exception:
        raise last_exception


class AWSCredentialManager:
    """Manages AWS credentials with automatic rotation."""
    
    def __init__(self):
        """Initialize credential manager."""
        self._session: Optional[aioboto3.Session] = None
        self._credentials: Optional[Dict[str, Any]] = None
        self._credentials_expiry: Optional[datetime] = None
        self._role_arn: Optional[str] = None
        self._requested_duration = max(60, min(43200, config.aws.role_session_duration))
    
    def _get_session(self) -> aioboto3.Session:
        """Get or create aioboto3 session lazily."""
        if self._session is None:
            # Only create session when actually needed
            self._session = aioboto3.Session()
        return self._session
    
    async def assume_role(self, role_arn: str, session_name: str) -> Dict[str, Any]:
        """
        Assume IAM role and get temporary credentials.
        
        Args:
            role_arn: ARN of role to assume
            session_name: Session name for the role assumption
            
        Returns:
            Temporary credentials
        """
        try:
            session = self._get_session()
            async with session.client('sts', 
                                          region_name=config.aws.region,
                                          endpoint_url=config.aws.endpoint_url) as sts:
                duration = self._requested_duration

                try:
                    response = await sts.assume_role(
                        RoleArn=role_arn,
                        RoleSessionName=session_name,
                        DurationSeconds=duration
                    )
                except ClientError as e:
                    error_code = e.response.get('Error', {}).get('Code')
                    error_message = e.response.get('Error', {}).get('Message', '')
                    if error_code == 'ValidationError' and 'durationSeconds' in error_message:
                        # Retry with default 1 hour duration
                        duration = min(duration, 3600)
                        logger.warning(
                            "Role assumption duration rejected; retrying with %ss", duration
                        )
                        response = await sts.assume_role(
                            RoleArn=role_arn,
                            RoleSessionName=session_name,
                            DurationSeconds=duration
                        )
                    else:
                        raise
                
                credentials = response['Credentials']
                self._credentials = {
                    'aws_access_key_id': credentials['AccessKeyId'],
                    'aws_secret_access_key': credentials['SecretAccessKey'],
                    'aws_session_token': credentials['SessionToken']
                }
                self._credentials_expiry = credentials['Expiration']
                self._role_arn = role_arn
                
                logger.info(f"Successfully assumed role: {role_arn}")
                return self._credentials
                
        except ClientError as e:
            logger.error(f"Failed to assume role {role_arn}: {e}")
            raise AuthenticationError(f"Role assumption failed: {e}")
    
    def are_credentials_valid(self) -> bool:
        """Check if current credentials are valid and not expired."""
        if not self._credentials or not self._credentials_expiry:
            return False
        
        # Check if credentials expire within 5 minutes
        return datetime.utcnow() < (self._credentials_expiry - timedelta(minutes=5))
    
    async def get_credentials(self) -> Optional[Dict[str, Any]]:
        """Get current valid credentials, refreshing if necessary."""
        if self.are_credentials_valid():
            return self._credentials
        
        if self._role_arn:
            # Refresh credentials by re-assuming role
            return await self.assume_role(self._role_arn, "incident-commander-refresh")
        
        return None


class AWSServiceFactory:
    """Factory for creating AWS service clients with connection pooling and health monitoring."""
    
    def __init__(self):
        """Initialize service factory."""
        self._credential_manager = AWSCredentialManager()
        self._session: Optional[aioboto3.Session] = None
        self._active_clients: Set[Any] = set()
        self._active_resources: Set[Any] = set()
        self._client_pool: Dict[str, Any] = {}
        self._client_health: Dict[str, bool] = {}
        self._lock = asyncio.Lock()
        self._retry_config = RetryConfig(max_retries=3, base_delay=1.0, max_delay=30.0)
        
        # Connection pool configuration
        self._pool_config = Config(
            retries={'max_attempts': 3, 'mode': 'adaptive'},
            max_pool_connections=50,
            region_name=config.aws.region
        )
    
    def _get_session(self) -> aioboto3.Session:
        """Get or create aioboto3 session lazily."""
        if self._session is None:
            self._session = aioboto3.Session()
        return self._session
    
    async def create_client(self, service_name: str, **kwargs) -> Any:
        """
        Create AWS service client with proper authentication, connection pooling, and retry logic.
        
        Args:
            service_name: Name of AWS service (e.g., 'dynamodb', 'kinesis')
            **kwargs: Additional client configuration
            
        Returns:
            Configured AWS service client
        """
        # Check if we have a healthy pooled client
        pool_key = f"{service_name}_{hash(frozenset(kwargs.items()))}"
        
        async with self._lock:
            if pool_key in self._client_pool and self._client_health.get(pool_key, False):
                return self._client_pool[pool_key]
        
        client_config = {
            'region_name': config.aws.region,
            'endpoint_url': config.aws.endpoint_url,
            'config': self._pool_config,
            **kwargs
        }

        # Add credentials if available
        credentials = await self._credential_manager.get_credentials()
        if credentials:
            client_config.update(credentials)

        async def _create_client():
            session = self._get_session()
            client_cm = session.client(service_name, **client_config)
            client = await client_cm.__aenter__()
            return client

        # Create client with retry logic
        client = await retry_with_backoff(
            _create_client,
            retry_config=self._retry_config,
            timeout=30.0
        )

        async with self._lock:
            self._active_clients.add(client)
            self._client_pool[pool_key] = client
            self._client_health[pool_key] = True

        return client
    
    async def create_resource(self, service_name: str, **kwargs) -> Any:
        """
        Create AWS service resource with proper authentication.
        
        Args:
            service_name: Name of AWS service (e.g., 'dynamodb', 's3')
            **kwargs: Additional resource configuration
            
        Returns:
            Configured AWS service resource
        """
        resource_config = {
            'region_name': config.aws.region,
            'endpoint_url': config.aws.endpoint_url,
            **kwargs
        }

        credentials = await self._credential_manager.get_credentials()
        if credentials:
            resource_config.update(credentials)

        session = self._get_session()
        resource_cm = session.resource(service_name, **resource_config)
        resource = await resource_cm.__aenter__()

        async with self._lock:
            self._active_resources.add(resource)

        return resource

    async def close_client(self, client: Any) -> None:
        """Close an AWS client and remove it from active tracking."""
        if client is None:
            return
        try:
            await client.__aexit__(None, None, None)
        except Exception as exc:
            logger.warning(f"Error closing AWS client: {exc}")
        finally:
            async with self._lock:
                self._active_clients.discard(client)

    async def close_resource(self, resource: Any) -> None:
        """Close an AWS resource and remove it from active tracking."""
        if resource is None:
            return
        try:
            await resource.__aexit__(None, None, None)
        except Exception as exc:
            logger.warning(f"Error closing AWS resource: {exc}")
        finally:
            async with self._lock:
                self._active_resources.discard(resource)
    
    async def get_cloudwatch_client(self):
        """Get CloudWatch client."""
        return await self.create_client('cloudwatch')
    
    async def get_stepfunctions_client(self):
        """Get Step Functions client for consensus coordination."""
        return await self.create_client('stepfunctions')
    
    async def get_inspector_client(self):
        """Get Inspector client for security validation."""
        return await self.create_client('inspector2')
    
    async def get_cost_explorer_client(self):
        """Get Cost Explorer client for FinOps operations."""
        return await self.create_client('ce')
    
    async def get_bedrock_client(self):
        """Get Bedrock runtime client."""
        return await self.create_client('bedrock-runtime')
    
    async def get_dynamodb_client(self):
        """Get DynamoDB client."""
        return await self.create_client('dynamodb')
    
    async def get_kinesis_client(self):
        """Get Kinesis client."""
        return await self.create_client('kinesis')
    
    async def get_s3_client(self):
        """Get S3 client."""
        return await self.create_client('s3')
    
    async def get_opensearch_client(self):
        """Get OpenSearch Serverless client."""
        return await self.create_client('opensearchserverless')
    
    async def cleanup(self):
        """Cleanup AWS service connections and resources."""
        try:
            # Close any open sessions or connections
            async with self._lock:
                clients = list(self._active_clients)
                resources = list(self._active_resources)
                self._active_clients.clear()
                self._active_resources.clear()

            for client in clients:
                try:
                    await client.close()
                except Exception as exc:
                    logger.warning(f"Error closing AWS client during cleanup: {exc}")

            for resource in resources:
                try:
                    await resource.close()
                except Exception as exc:
                    logger.warning(f"Error closing AWS resource during cleanup: {exc}")

            if self._session and hasattr(self._session, 'close'):
                await self._session.close()

            if self._credential_manager:
                self._credential_manager._credentials = None
                self._credential_manager._credentials_expiry = None
                self._credential_manager._role_arn = None

            logger.info("AWS service factory cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during AWS service factory cleanup: {e}")
    
    async def health_check(self) -> bool:
        """Perform health check on AWS services."""
        try:
            # Test basic AWS connectivity
            async def _check_sts():
                client = await self.create_client('sts')
                return await client.get_caller_identity()
            
            await retry_with_backoff(_check_sts, timeout=10.0)
            return True
        except Exception as e:
            logger.error(f"AWS health check failed: {e}")
            return False
    
    async def health_check_service(self, service_name: str) -> bool:
        """
        Perform health check on specific AWS service.
        
        Args:
            service_name: Name of AWS service to check
            
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            if service_name == 'stepfunctions':
                client = await self.get_stepfunctions_client()
                await client.list_state_machines(maxResults=1)
            elif service_name == 'inspector2':
                client = await self.get_inspector_client()
                await client.list_findings(maxResults=1)
            elif service_name == 'ce':
                client = await self.get_cost_explorer_client()
                # Cost Explorer requires specific date range
                from datetime import datetime, timedelta
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                await client.get_cost_and_usage(
                    TimePeriod={'Start': start_date, 'End': end_date},
                    Granularity='DAILY',
                    Metrics=['BlendedCost']
                )
            elif service_name == 'bedrock-runtime':
                client = await self.get_bedrock_client()
                # Just check if we can create the client
                pass
            elif service_name == 'dynamodb':
                client = await self.get_dynamodb_client()
                await client.list_tables(Limit=1)
            elif service_name == 'kinesis':
                client = await self.get_kinesis_client()
                await client.list_streams(Limit=1)
            elif service_name == 's3':
                client = await self.get_s3_client()
                await client.list_buckets()
            elif service_name == 'opensearchserverless':
                client = await self.get_opensearch_client()
                await client.list_collections()
            else:
                # Generic health check
                client = await self.create_client(service_name)
                # Just creating the client is enough for basic health check
            
            # Mark service as healthy
            async with self._lock:
                self._client_health[service_name] = True
            
            return True
            
        except Exception as e:
            logger.warning(f"Health check failed for {service_name}: {e}")
            
            # Mark service as unhealthy
            async with self._lock:
                self._client_health[service_name] = False
            
            return False
    
    def get_service_health_status(self) -> Dict[str, bool]:
        """Get health status of all monitored services."""
        return self._client_health.copy()
    
    async def graceful_degrade_on_service_failure(self, service_name: str, fallback_func: Callable = None):
        """
        Handle service failure with graceful degradation.
        
        Args:
            service_name: Name of failed service
            fallback_func: Optional fallback function to execute
        """
        logger.warning(f"Service {service_name} is unavailable, implementing graceful degradation")
        
        # Mark service as unhealthy
        async with self._lock:
            self._client_health[service_name] = False
        
        # Execute fallback if provided
        if fallback_func:
            try:
                return await fallback_func()
            except Exception as e:
                logger.error(f"Fallback function failed for {service_name}: {e}")
        
        # Queue requests for later retry if applicable
        logger.info(f"Queueing requests for {service_name} until service recovery")


class BedrockClient:
    """Client for AWS Bedrock model interactions with intelligent routing."""
    
    def __init__(self, service_factory: AWSServiceFactory):
        """Initialize Bedrock client."""
        self._service_factory = service_factory
        self._client = None
        self._model_health = {}
        self._request_count = 0
        self._last_health_check = datetime.utcnow()
    
    async def _get_client(self):
        """Get or create Bedrock client."""
        if not self._client:
            self._client = await self._service_factory.create_client('bedrock-runtime')
        return self._client
    
    async def _health_check_model(self, model_id: str) -> bool:
        """Check if a model is healthy by making a simple request."""
        try:
            await self.invoke_model(model_id, "Health check", max_tokens=10)
            self._model_health[model_id] = True
            return True
        except Exception as e:
            logger.warning(f"Model {model_id} health check failed: {e}")
            self._model_health[model_id] = False
            return False
    
    async def invoke_model(self, model_id: str, prompt: str, 
                          max_tokens: int = None, temperature: float = None) -> str:
        """
        Invoke Bedrock model with prompt.
        
        Args:
            model_id: Bedrock model ID
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Model response text
        """
        try:
            client = await self._get_client()
            
            # Prepare request body based on model type
            if "claude" in model_id.lower():
                body = {
                    "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
                    "max_tokens_to_sample": max_tokens or config.bedrock.max_tokens,
                    "temperature": temperature or config.bedrock.temperature,
                    "stop_sequences": ["\n\nHuman:"]
                }
            else:
                # Generic format for other models
                body = {
                    "inputText": prompt,
                    "textGenerationConfig": {
                        "maxTokenCount": max_tokens or config.bedrock.max_tokens,
                        "temperature": temperature or config.bedrock.temperature
                    }
                }
            
            response = await client.invoke_model(
                modelId=model_id,
                body=json.dumps(body),
                contentType='application/json'
            )
            
            response_body = json.loads(response['body'].read())
            
            # Extract text based on model type
            if "claude" in model_id.lower():
                return response_body.get('completion', '').strip()
            else:
                return response_body.get('results', [{}])[0].get('outputText', '').strip()
                
        except ClientError as e:
            logger.error(f"Bedrock model invocation failed: {e}")
            self._model_health[model_id] = False
            raise
        except Exception as e:
            logger.error(f"Unexpected error invoking model {model_id}: {e}")
            raise
    
    async def invoke_with_fallback(self, prompt: str, **kwargs) -> str:
        """
        Invoke model with automatic fallback to secondary model.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional parameters
            
        Returns:
            Model response text
        """
        # Check model health periodically
        if (datetime.utcnow() - self._last_health_check).seconds > 300:  # 5 minutes
            await self._health_check_model(config.bedrock.primary_model)
            await self._health_check_model(config.bedrock.fallback_model)
            self._last_health_check = datetime.utcnow()
        
        # Try primary model if healthy
        if self._model_health.get(config.bedrock.primary_model, True):
            try:
                result = await self.invoke_model(
                    config.bedrock.primary_model, 
                    prompt, 
                    **kwargs
                )
                self._model_health[config.bedrock.primary_model] = True
                return result
            except Exception as e:
                logger.warning(f"Primary model failed, trying fallback: {e}")
                self._model_health[config.bedrock.primary_model] = False
        
        # Fallback to secondary model
        try:
            result = await self.invoke_model(
                config.bedrock.fallback_model, 
                prompt, 
                **kwargs
            )
            self._model_health[config.bedrock.fallback_model] = True
            return result
        except Exception as e:
            logger.error(f"Both models failed: {e}")
            self._model_health[config.bedrock.fallback_model] = False
            raise
    
    def get_model_health(self) -> Dict[str, bool]:
        """Get health status of all models."""
        return self._model_health.copy()


class DynamoDBClient:
    """Client for DynamoDB operations."""
    
    def __init__(self, service_factory: AWSServiceFactory):
        """Initialize DynamoDB client."""
        self._service_factory = service_factory
        self._resource = None
    
    async def _get_resource(self):
        """Get or create DynamoDB resource."""
        if not self._resource:
            self._resource = await self._service_factory.create_resource('dynamodb')
        return self._resource
    
    async def get_table(self, table_name: str):
        """Get DynamoDB table resource."""
        resource = await self._get_resource()
        return await resource.Table(table_name)
    
    async def create_table_if_not_exists(self, table_name: str, 
                                       key_schema: list, 
                                       attribute_definitions: list,
                                       billing_mode: str = 'PAY_PER_REQUEST') -> bool:
        """
        Create DynamoDB table if it doesn't exist.
        
        Args:
            table_name: Name of table to create
            key_schema: Table key schema
            attribute_definitions: Attribute definitions
            billing_mode: Billing mode for the table
            
        Returns:
            True if table was created, False if it already existed
        """
        try:
            resource = await self._get_resource()
            
            # Check if table exists
            try:
                table = await resource.Table(table_name)
                await table.load()
                logger.info(f"Table {table_name} already exists")
                return False
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceNotFoundException':
                    raise
            
            # Create table
            table = await resource.create_table(
                TableName=table_name,
                KeySchema=key_schema,
                AttributeDefinitions=attribute_definitions,
                BillingMode=billing_mode
            )
            
            # Wait for table to be active
            await table.wait_until_exists()
            logger.info(f"Created table: {table_name}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to create table {table_name}: {e}")
            raise


# Global service factory instance (lazy initialization)
_aws_service_factory: Optional[AWSServiceFactory] = None

def get_aws_service_factory() -> AWSServiceFactory:
    """Get or create the global AWS service factory instance."""
    global _aws_service_factory
    if _aws_service_factory is None:
        _aws_service_factory = AWSServiceFactory()
    return _aws_service_factory
