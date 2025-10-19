"""
Configuration management for the Incident Commander system.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AWSConfig:
    """AWS service configuration."""
    region: str = "us-east-1"
    profile: Optional[str] = None
    endpoint_url: Optional[str] = None  # For LocalStack
    role_session_duration: int = 3600
    
    @classmethod
    def from_env(cls) -> "AWSConfig":
        """Create AWS config from environment variables."""
        return cls(
            region=os.getenv("AWS_REGION", "us-east-1"),
            profile=os.getenv("AWS_PROFILE"),
            endpoint_url=os.getenv("AWS_ENDPOINT_URL"),  # LocalStack
            role_session_duration=int(os.getenv("AWS_ROLE_SESSION_DURATION", "3600"))
        )


@dataclass
class BedrockConfig:
    """Bedrock model configuration."""
    primary_model: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    fallback_model: str = "anthropic.claude-3-haiku-20240307-v1:0"
    max_tokens: int = 4096
    temperature: float = 0.1
    
    @classmethod
    def from_env(cls) -> "BedrockConfig":
        """Create Bedrock config from environment variables."""
        return cls(
            primary_model=os.getenv("BEDROCK_PRIMARY_MODEL", cls.primary_model),
            fallback_model=os.getenv("BEDROCK_FALLBACK_MODEL", cls.fallback_model),
            max_tokens=int(os.getenv("BEDROCK_MAX_TOKENS", "4096")),
            temperature=float(os.getenv("BEDROCK_TEMPERATURE", "0.1"))
        )


@dataclass
class DatabaseConfig:
    """Database configuration."""
    dynamodb_table_prefix: str = "incident-commander"
    kinesis_stream_name: str = "incident-events"
    opensearch_endpoint: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Create database config from environment variables."""
        return cls(
            dynamodb_table_prefix=os.getenv("DYNAMODB_TABLE_PREFIX", cls.dynamodb_table_prefix),
            kinesis_stream_name=os.getenv("KINESIS_STREAM_NAME", cls.kinesis_stream_name),
            opensearch_endpoint=os.getenv("OPENSEARCH_ENDPOINT")
        )


@dataclass
class ExternalServiceConfig:
    """External service integration configuration."""
    datadog_api_key: Optional[str] = None
    pagerduty_api_key: Optional[str] = None
    slack_bot_token: Optional[str] = None
    slack_channel: Optional[str] = None
    github_token: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> "ExternalServiceConfig":
        """Create external service config from environment variables."""
        return cls(
            datadog_api_key=os.getenv("DATADOG_API_KEY"),
            pagerduty_api_key=os.getenv("PAGERDUTY_API_KEY"),
            slack_bot_token=os.getenv("SLACK_BOT_TOKEN"),
            slack_channel=os.getenv("SLACK_CHANNEL"),
            github_token=os.getenv("GITHUB_TOKEN")
        )


@dataclass
class RedisConfig:
    """Redis configuration for message bus."""
    host: str = "localhost"
    port: int = 6379
    password: Optional[str] = None
    db: int = 0
    ssl: bool = False
    
    @classmethod
    def from_env(cls) -> "RedisConfig":
        """Create Redis config from environment variables."""
        return cls(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD"),
            db=int(os.getenv("REDIS_DB", "0")),
            ssl=os.getenv("REDIS_SSL", "false").lower() == "true"
        )


@dataclass
class SecurityConfig:
    """Security configuration."""
    jwt_secret_key: Optional[str] = None
    encryption_key: Optional[str] = None
    api_rate_limit: int = 100
    cors_origins: list = field(default_factory=list)
    require_auth: bool = False
    demo_api_key: str = "demo-key-12345"
    
    @classmethod
    def from_env(cls) -> "SecurityConfig":
        """Create security config from environment variables."""
        cors_origins_str = os.getenv("CORS_ORIGINS", "*")
        cors_origins = cors_origins_str.split(",") if cors_origins_str != "*" else ["*"]
        
        return cls(
            jwt_secret_key=os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production"),
            encryption_key=os.getenv("ENCRYPTION_KEY"),
            api_rate_limit=int(os.getenv("API_RATE_LIMIT", "100")),
            cors_origins=cors_origins,
            require_auth=os.getenv("REQUIRE_AUTH", "false").lower() == "true",
            demo_api_key=os.getenv("DEMO_API_KEY", "demo-key-12345")
        )


@dataclass
class ObservabilityConfig:
    """Observability and monitoring configuration."""
    otlp_endpoint: Optional[str] = None
    otlp_token: Optional[str] = None
    prometheus_enabled: bool = True
    tracing_enabled: bool = True
    metrics_collection_interval: int = 30
    
    @classmethod
    def from_env(cls) -> "ObservabilityConfig":
        """Create observability config from environment variables."""
        return cls(
            otlp_endpoint=os.getenv("OTLP_ENDPOINT"),
            otlp_token=os.getenv("OTLP_TOKEN"),
            prometheus_enabled=os.getenv("PROMETHEUS_ENABLED", "true").lower() == "true",
            tracing_enabled=os.getenv("TRACING_ENABLED", "true").lower() == "true",
            metrics_collection_interval=int(os.getenv("METRICS_COLLECTION_INTERVAL", "30"))
        )


class ConfigManager:
    """Central configuration manager."""
    
    def __init__(self, env_file: Optional[Path] = None):
        """Initialize configuration manager."""
        if env_file and env_file.exists():
            self._load_env_file(env_file)
        
        self.aws = AWSConfig.from_env()
        self.bedrock = BedrockConfig.from_env()
        self.database = DatabaseConfig.from_env()
        self.external_services = ExternalServiceConfig.from_env()
        self.redis = RedisConfig.from_env()
        self.security = SecurityConfig.from_env()
        self.observability = ObservabilityConfig.from_env()
        
        # Environment detection
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.is_local = self.environment == "development"
        self.is_production = self.environment == "production"
        self.is_staging = self.environment == "staging"
        self.demo_effects_enabled = os.getenv("DEMO_EFFECTS_ENABLED", "0") == "1"
        self.is_test = self.environment == "test"
    
    def _load_env_file(self, env_file: Path) -> None:
        """Load environment variables from file."""
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    os.environ[key] = value
    
    def get_table_name(self, table_type: str) -> str:
        """Get DynamoDB table name with prefix."""
        return f"{self.database.dynamodb_table_prefix}-{table_type}"
    
    def validate_required_config(self) -> None:
        """Validate that required configuration is present."""
        errors = []
        
        # Production-only requirements
        if self.is_production:
            # External service integrations
            if not self.external_services.datadog_api_key:
                errors.append("DATADOG_API_KEY is required in production")
            if not self.external_services.pagerduty_api_key:
                errors.append("PAGERDUTY_API_KEY is required in production")
            if not self.external_services.slack_bot_token:
                errors.append("SLACK_BOT_TOKEN is required in production")
            if not self.external_services.slack_channel:
                errors.append("SLACK_CHANNEL is required in production")
            
            # Security requirements
            if not self.security.jwt_secret_key:
                errors.append("JWT_SECRET_KEY is required in production")
            if not self.security.encryption_key:
                errors.append("ENCRYPTION_KEY is required in production")
            if not self.security.cors_origins:
                errors.append("CORS_ORIGINS must be explicitly set in production")
            
            # Redis requirements (production should use managed Redis)
            if self.redis.host == "localhost":
                errors.append("REDIS_HOST should not be localhost in production")
            if not self.redis.password:
                errors.append("REDIS_PASSWORD is required in production")
            if not self.redis.ssl:
                errors.append("REDIS_SSL should be enabled in production")
            
            # AWS requirements
            if self.aws.endpoint_url:
                errors.append("AWS_ENDPOINT_URL should not be set in production (LocalStack)")
            
            # Bedrock limits validation
            if self.bedrock.max_tokens > 8192:
                errors.append("BEDROCK_MAX_TOKENS should not exceed 8192 in production")

        # Staging requirements
        if self.is_staging:
            if not self.external_services.datadog_api_key:
                errors.append("DATADOG_API_KEY is required in staging")
            if not self.security.jwt_secret_key:
                errors.append("JWT_SECRET_KEY is required in staging")
        
        # Development warnings (not errors)
        if self.is_local:
            warnings = []
            if not self.aws.endpoint_url:
                warnings.append("AWS_ENDPOINT_URL not set - using real AWS services in development")
            if self.redis.host != "localhost" and not self.redis.password:
                warnings.append("Using remote Redis without password in development")
            
            if warnings:
                import logging
                logger = logging.getLogger(__name__)
                for warning in warnings:
                    logger.warning(f"Development configuration warning: {warning}")
        
        # AWS session duration sanity check (all environments)
        if self.aws.role_session_duration <= 0:
            errors.append("AWS_ROLE_SESSION_DURATION must be positive")
        elif self.aws.role_session_duration > 43200:
            errors.append("AWS_ROLE_SESSION_DURATION must be <= 43200 seconds")

        if errors:
            raise ValueError(f"Configuration validation failed: {', '.join(errors)}")
    
    def get_redis_url(self) -> str:
        """Get Redis connection URL."""
        scheme = "rediss" if self.redis.ssl else "redis"
        auth = f":{self.redis.password}@" if self.redis.password else ""
        return f"{scheme}://{auth}{self.redis.host}:{self.redis.port}/{self.redis.db}"
    
    def get_bedrock_limits(self) -> Dict[str, Any]:
        """Get Bedrock service limits for production."""
        if self.is_production:
            return {
                "max_concurrent_requests": 50,
                "max_tokens_per_minute": 100000,
                "max_requests_per_minute": 1000,
                "timeout_seconds": 30
            }
        elif self.is_staging:
            return {
                "max_concurrent_requests": 20,
                "max_tokens_per_minute": 50000,
                "max_requests_per_minute": 500,
                "timeout_seconds": 30
            }
        else:  # development
            return {
                "max_concurrent_requests": 5,
                "max_tokens_per_minute": 10000,
                "max_requests_per_minute": 100,
                "timeout_seconds": 60
            }
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Get environment information for debugging."""
        return {
            "environment": self.environment,
            "is_local": self.is_local,
            "is_staging": self.is_staging,
            "is_production": self.is_production,
            "is_test": self.is_test,
            "aws_region": self.aws.region,
            "aws_endpoint": self.aws.endpoint_url,
            "aws_role_session_duration": self.aws.role_session_duration,
            "redis_host": self.redis.host,
            "redis_ssl": self.redis.ssl,
            "bedrock_primary_model": self.bedrock.primary_model,
            "bedrock_limits": self.get_bedrock_limits(),
            "demo_effects_enabled": self.demo_effects_enabled
        }


# Global configuration instance
config = ConfigManager(Path(".env") if Path(".env").exists() else None)
