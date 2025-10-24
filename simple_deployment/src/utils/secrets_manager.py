"""
AWS Secrets Manager integration for production secret management.

Replaces environment variables with secure secret retrieval for production deployment.
"""

import boto3
import json
import asyncio
from typing import Dict, Any, Optional
from functools import lru_cache
from src.utils.logging import get_logger

logger = get_logger("secrets_manager")


class SecretsManager:
    """Manages secure retrieval of secrets from AWS Secrets Manager."""
    
    def __init__(self, region_name: str = "us-east-1"):
        self.client = boto3.client("secretsmanager", region_name=region_name)
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = 300  # 5 minutes
    
    @lru_cache(maxsize=128)
    def get_secret(self, secret_arn: str) -> Optional[str]:
        """
        Retrieve secret value from AWS Secrets Manager.
        
        Args:
            secret_arn: ARN of the secret to retrieve
            
        Returns:
            Secret value as string, or None if not found
        """
        try:
            response = self.client.get_secret_value(SecretId=secret_arn)
            
            # Handle both string and JSON secrets
            if "SecretString" in response:
                secret_value = response["SecretString"]
                
                # Try to parse as JSON
                try:
                    secret_json = json.loads(secret_value)
                    return secret_json
                except json.JSONDecodeError:
                    return secret_value
            else:
                # Binary secret
                return response["SecretBinary"]
                
        except Exception as e:
            logger.error(f"Failed to retrieve secret {secret_arn}: {e}")
            return None
    
    def get_database_credentials(self, secret_arn: str) -> Optional[Dict[str, str]]:
        """Retrieve database credentials from Secrets Manager."""
        secret = self.get_secret(secret_arn)
        
        if isinstance(secret, dict):
            return {
                "username": secret.get("username"),
                "password": secret.get("password"),
                "host": secret.get("host"),
                "port": secret.get("port", 5432),
                "database": secret.get("dbname")
            }
        
        return None
    
    def get_api_key(self, secret_arn: str, key_name: str = "api_key") -> Optional[str]:
        """Retrieve API key from Secrets Manager."""
        secret = self.get_secret(secret_arn)
        
        if isinstance(secret, dict):
            return secret.get(key_name)
        elif isinstance(secret, str):
            return secret
        
        return None


# Global secrets manager instance
_secrets_manager: Optional[SecretsManager] = None


def get_secrets_manager() -> SecretsManager:
    """Get the global secrets manager instance."""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager


def get_production_config() -> Dict[str, Any]:
    """
    Get production configuration with secrets from AWS Secrets Manager.
    
    This replaces environment variables for sensitive configuration in production.
    """
    secrets_manager = get_secrets_manager()
    
    # Get secrets from environment variable ARNs
    datadog_api_key = None
    pagerduty_api_key = None
    slack_bot_token = None
    
    # Retrieve secrets if ARNs are provided
    datadog_secret_arn = os.getenv("DATADOG_API_KEY_SECRET_ARN")
    if datadog_secret_arn:
        datadog_api_key = secrets_manager.get_api_key(datadog_secret_arn)
    
    pagerduty_secret_arn = os.getenv("PAGERDUTY_API_KEY_SECRET_ARN")
    if pagerduty_secret_arn:
        pagerduty_api_key = secrets_manager.get_api_key(pagerduty_secret_arn)
    
    slack_secret_arn = os.getenv("SLACK_BOT_TOKEN_SECRET_ARN")
    if slack_secret_arn:
        slack_bot_token = secrets_manager.get_api_key(slack_secret_arn, "bot_token")
    
    return {
        "datadog_api_key": datadog_api_key,
        "pagerduty_api_key": pagerduty_api_key,
        "slack_bot_token": slack_bot_token,
        "encryption_key_arn": os.getenv("ENCRYPTION_KEY_ARN"),
        "audit_log_bucket": os.getenv("AUDIT_LOG_BUCKET"),
        "certificate_authority_arn": os.getenv("CERTIFICATE_AUTHORITY_ARN")
    }
