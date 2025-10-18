#!/usr/bin/env python3
"""
Security Hardening Script for Incident Commander

Implements production-ready security configurations for hackathon demo:
- CORS policy hardening
- Security headers implementation  
- Secrets management migration
- Environment-specific configurations
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, Any, List


class SecurityHardener:
    """Implements security hardening for production deployment."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.src_dir = self.project_root / "src"
        
    def harden_cors_policy(self) -> bool:
        """Update CORS policy for production deployment."""
        print("🔒 Hardening CORS policy...")
        
        main_py_path = self.src_dir / "main.py"
        
        if not main_py_path.exists():
            print("❌ main.py not found")
            return False
        
        try:
            # Read current main.py
            with open(main_py_path, 'r') as f:
                content = f.read()
            
            # Replace wildcard CORS with environment-specific origins
            old_cors = '''app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if config.environment == "development" else ["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)'''
            
            new_cors = '''# Production-ready CORS configuration
def get_allowed_origins():
    """Get allowed origins based on environment."""
    if config.environment == "development":
        return ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8080"]
    elif config.environment == "staging":
        return ["https://staging-incident-commander.example.com"]
    else:  # production
        return [
            "https://incident-commander.example.com",
            "https://demo.incident-commander.example.com"
        ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
    expose_headers=["X-Total-Count", "X-Request-ID"],
)'''
            
            if "allow_origins=[\"*\"]" in content:
                content = content.replace(old_cors, new_cors)
                
                # Write updated content
                with open(main_py_path, 'w') as f:
                    f.write(content)
                
                print("✅ CORS policy hardened")
                return True
            else:
                print("⚠️  CORS policy already configured")
                return True
                
        except Exception as e:
            print(f"❌ Failed to harden CORS policy: {e}")
            return False
    
    def add_security_headers(self) -> bool:
        """Add security headers middleware."""
        print("🛡️  Adding security headers...")
        
        main_py_path = self.src_dir / "main.py"
        
        try:
            with open(main_py_path, 'r') as f:
                content = f.read()
            
            # Check if security headers already exist
            if "SecurityHeadersMiddleware" in content:
                print("⚠️  Security headers already configured")
                return True
            
            # Add security headers middleware after CORS
            security_middleware = '''
# Security Headers Middleware
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers for production deployment
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY", 
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' ws: wss:; "
                "frame-ancestors 'none';"
            ),
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": (
                "geolocation=(), microphone=(), camera=(), "
                "payment=(), usb=(), magnetometer=(), gyroscope=()"
            ),
            "X-Request-ID": f"req-{request.headers.get('x-request-id', 'unknown')}"
        }
        
        # Apply headers
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)
'''
            
            # Insert after CORS middleware
            cors_end = content.find(")")
            if cors_end != -1:
                # Find the end of the CORS middleware block
                lines = content.split('\n')
                insert_line = None
                
                for i, line in enumerate(lines):
                    if "app.add_middleware(" in line and "CORSMiddleware" in line:
                        # Find the closing of this middleware block
                        bracket_count = 0
                        for j in range(i, len(lines)):
                            bracket_count += lines[j].count('(') - lines[j].count(')')
                            if bracket_count == 0:
                                insert_line = j + 1
                                break
                        break
                
                if insert_line:
                    lines.insert(insert_line, security_middleware)
                    content = '\n'.join(lines)
                    
                    with open(main_py_path, 'w') as f:
                        f.write(content)
                    
                    print("✅ Security headers added")
                    return True
            
            print("❌ Could not find insertion point for security headers")
            return False
            
        except Exception as e:
            print(f"❌ Failed to add security headers: {e}")
            return False
    
    def create_production_env_template(self) -> bool:
        """Create production environment template."""
        print("🔧 Creating production environment template...")
        
        try:
            prod_env_content = '''# Production Environment Configuration
# Copy to .env.production and update with actual values

# Environment
ENVIRONMENT=production
DEBUG=false

# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=your-account-id

# Bedrock Models
BEDROCK_PRIMARY_MODEL=anthropic.claude-3-sonnet-20240229-v1:0
BEDROCK_FALLBACK_MODEL=anthropic.claude-3-haiku-20240307-v1:0

# External Services (Use AWS Secrets Manager in production)
DATADOG_API_KEY_SECRET_ARN=arn:aws:secretsmanager:region:account:secret:datadog-api-key
PAGERDUTY_API_KEY_SECRET_ARN=arn:aws:secretsmanager:region:account:secret:pagerduty-api-key
SLACK_BOT_TOKEN_SECRET_ARN=arn:aws:secretsmanager:region:account:secret:slack-bot-token

# Database Configuration
DYNAMODB_TABLE_PREFIX=incident-commander-prod
OPENSEARCH_ENDPOINT=https://your-opensearch-domain.region.es.amazonaws.com

# Security Configuration
ENCRYPTION_KEY_ARN=arn:aws:kms:region:account:key/key-id
AUDIT_LOG_BUCKET=incident-commander-audit-logs-prod
CERTIFICATE_AUTHORITY_ARN=arn:aws:acm-pca:region:account:certificate-authority/ca-id

# Performance Configuration
CONNECTION_POOL_SIZE=50
CACHE_TTL_SECONDS=300
MAX_CONCURRENT_INCIDENTS=100

# Monitoring Configuration
METRICS_NAMESPACE=IncidentCommander/Production
LOG_LEVEL=INFO
ENABLE_XRAY_TRACING=true

# Rate Limiting
BEDROCK_REQUESTS_PER_MINUTE=1000
EXTERNAL_API_REQUESTS_PER_MINUTE=100

# WebSocket Configuration
MAX_WEBSOCKET_CONNECTIONS=1000
WEBSOCKET_HEARTBEAT_INTERVAL=30

# Demo Configuration (for production demos)
DEMO_MODE_ENABLED=true
DEMO_DATA_RETENTION_HOURS=24
'''
            
            env_prod_path = self.project_root / ".env.production.template"
            with open(env_prod_path, 'w') as f:
                f.write(prod_env_content)
            
            print("✅ Production environment template created")
            print(f"   📄 {env_prod_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create production environment template: {e}")
            return False
    
    def create_secrets_manager_integration(self) -> bool:
        """Create AWS Secrets Manager integration."""
        print("🔐 Creating AWS Secrets Manager integration...")
        
        try:
            secrets_manager_code = '''"""
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
'''
            
            secrets_path = self.src_dir / "utils" / "secrets_manager.py"
            secrets_path.parent.mkdir(exist_ok=True)
            
            with open(secrets_path, 'w') as f:
                f.write(secrets_manager_code)
            
            print("✅ AWS Secrets Manager integration created")
            print(f"   📄 {secrets_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create Secrets Manager integration: {e}")
            return False
    
    def create_deployment_checklist(self) -> bool:
        """Create production deployment checklist."""
        print("📋 Creating deployment checklist...")
        
        try:
            checklist_content = '''# Production Deployment Checklist

## Pre-Deployment Security

### 1. Environment Configuration
- [ ] Copy `.env.production.template` to `.env.production`
- [ ] Update all placeholder values with actual production values
- [ ] Verify no secrets are committed to version control
- [ ] Test configuration with `python scripts/verify_setup.py`

### 2. AWS Secrets Manager Setup
- [ ] Create secrets in AWS Secrets Manager for:
  - [ ] Datadog API key
  - [ ] PagerDuty API key  
  - [ ] Slack bot token
  - [ ] Database credentials (if applicable)
- [ ] Update ARNs in `.env.production`
- [ ] Test secret retrieval with appropriate IAM permissions

### 3. Security Hardening
- [ ] Run security hardening: `python harden_security.py`
- [ ] Verify CORS policy is environment-specific
- [ ] Confirm security headers are applied
- [ ] Test CSP policy doesn't break functionality

### 4. Infrastructure Security
- [ ] Configure VPC with private subnets
- [ ] Set up security groups with minimal required access
- [ ] Enable AWS CloudTrail for audit logging
- [ ] Configure AWS Config for compliance monitoring
- [ ] Set up AWS GuardDuty for threat detection

## Performance Validation

### 5. Performance Testing
- [ ] Run performance validation: `python validate_demo_performance.py`
- [ ] Verify all performance targets are met:
  - [ ] API responses < 500ms
  - [ ] WebSocket latency < 100ms
  - [ ] Incident resolution < 3 minutes
  - [ ] Scenario triggers < 1 second
- [ ] Load test with expected demo traffic
- [ ] Validate auto-scaling configuration

### 6. WebSocket Configuration
- [ ] Test WebSocket connections under load
- [ ] Verify connection limits and cleanup
- [ ] Test reconnection logic
- [ ] Validate message broadcasting performance

## Demo Readiness

### 7. Demo Environment
- [ ] Deploy to staging environment first
- [ ] Test all 5 demo scenarios end-to-end
- [ ] Verify dashboard visual polish and animations
- [ ] Test on different browsers and screen sizes
- [ ] Prepare backup demo data/scenarios

### 8. Monitoring Setup
- [ ] Configure CloudWatch dashboards
- [ ] Set up alerts for critical metrics
- [ ] Test incident notification channels
- [ ] Verify log aggregation and search

### 9. Backup and Recovery
- [ ] Test database backup and restore procedures
- [ ] Verify configuration backup
- [ ] Document rollback procedures
- [ ] Test disaster recovery scenarios

## Final Validation

### 10. End-to-End Testing
- [ ] Complete incident lifecycle test
- [ ] Multi-user WebSocket connection test
- [ ] Security penetration testing
- [ ] Performance under demo load
- [ ] Failover and recovery testing

### 11. Documentation
- [ ] Update API documentation
- [ ] Create demo script and talking points
- [ ] Document troubleshooting procedures
- [ ] Prepare technical Q&A responses

### 12. Go-Live Checklist
- [ ] Final security scan
- [ ] Performance baseline established
- [ ] Monitoring alerts active
- [ ] Demo scenarios tested
- [ ] Rollback plan confirmed
- [ ] Team briefed on demo flow

## Post-Deployment

### 13. Monitoring
- [ ] Monitor performance metrics
- [ ] Watch for security alerts
- [ ] Track demo usage patterns
- [ ] Collect feedback for improvements

### 14. Maintenance
- [ ] Schedule regular security updates
- [ ] Plan capacity scaling if needed
- [ ] Review and rotate secrets
- [ ] Update documentation as needed

---

**Security Note**: Never commit production secrets or credentials to version control.
Use AWS Secrets Manager for all sensitive configuration in production environments.

**Performance Note**: Validate all performance targets before demo presentation.
The system should consistently deliver sub-3-minute incident resolution.
'''
            
            checklist_path = self.project_root / "DEPLOYMENT_CHECKLIST.md"
            with open(checklist_path, 'w') as f:
                f.write(checklist_content)
            
            print("✅ Deployment checklist created")
            print(f"   📄 {checklist_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create deployment checklist: {e}")
            return False
    
    def run_security_hardening(self) -> bool:
        """Run complete security hardening process."""
        print("🔒 Starting Security Hardening Process")
        print("=" * 50)
        
        success_count = 0
        total_steps = 5
        
        # Step 1: Harden CORS policy
        if self.harden_cors_policy():
            success_count += 1
        
        # Step 2: Add security headers
        if self.add_security_headers():
            success_count += 1
        
        # Step 3: Create production environment template
        if self.create_production_env_template():
            success_count += 1
        
        # Step 4: Create Secrets Manager integration
        if self.create_secrets_manager_integration():
            success_count += 1
        
        # Step 5: Create deployment checklist
        if self.create_deployment_checklist():
            success_count += 1
        
        # Summary
        print("\n" + "=" * 50)
        print("🔒 SECURITY HARDENING SUMMARY")
        print("=" * 50)
        
        print(f"Completed: {success_count}/{total_steps} steps")
        
        if success_count == total_steps:
            print("✅ Security hardening completed successfully!")
            print("🛡️  Production-ready security configuration applied")
            print("📋 Review DEPLOYMENT_CHECKLIST.md for next steps")
            return True
        else:
            print("⚠️  Some security hardening steps failed")
            print("🔧 Review errors above and retry failed steps")
            return False


def main():
    """Run security hardening."""
    hardener = SecurityHardener()
    
    try:
        success = hardener.run_security_hardening()
        
        if success:
            print("\n🚀 Security hardening complete - ready for production!")
            sys.exit(0)
        else:
            print("\n🛠️  Security hardening needs attention")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Security hardening cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Security hardening failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()