"""
AWS service clients and authentication management.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Set
import json

import aioboto3
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from src.utils.config import config
from src.utils.logging import get_logger
from src.utils.exceptions import AuthenticationError, ConfigurationError


logger = get_logger("aws_services")


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
    """Factory for creating AWS service clients."""
    
    def __init__(self):
        """Initialize service factory."""
        self._credential_manager = AWSCredentialManager()
        self._session: Optional[aioboto3.Session] = None
        self._active_clients: Set[Any] = set()
        self._active_resources: Set[Any] = set()
        self._lock = asyncio.Lock()
    
    def _get_session(self) -> aioboto3.Session:
        """Get or create aioboto3 session lazily."""
        if self._session is None:
            self._session = aioboto3.Session()
        return self._session
    
    async def create_client(self, service_name: str, **kwargs) -> Any:
        """
        Create AWS service client with proper authentication.
        
        Args:
            service_name: Name of AWS service (e.g., 'dynamodb', 'kinesis')
            **kwargs: Additional client configuration
            
        Returns:
            Configured AWS service client
        """
        client_config = {
            'region_name': config.aws.region,
            'endpoint_url': config.aws.endpoint_url,
            **kwargs
        }

        # Add credentials if available
        credentials = await self._credential_manager.get_credentials()
        if credentials:
            client_config.update(credentials)

        session = self._get_session()
        client = await session.client(service_name, **client_config)

        async with self._lock:
            self._active_clients.add(client)

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
        resource = await session.resource(service_name, **resource_config)

        async with self._lock:
            self._active_resources.add(resource)

        return resource

    async def close_client(self, client: Any) -> None:
        """Close an AWS client and remove it from active tracking."""
        if client is None:
            return
        try:
            await client.close()
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
            await resource.close()
        except Exception as exc:
            logger.warning(f"Error closing AWS resource: {exc}")
        finally:
            async with self._lock:
                self._active_resources.discard(resource)
    
    async def get_cloudwatch_client(self):
        """Get CloudWatch client."""
        return await self.create_client('cloudwatch')
    
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
            client = await self.create_client('sts')
            await client.get_caller_identity()
            return True
        except Exception as e:
            logger.error(f"AWS health check failed: {e}")
            return False


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
