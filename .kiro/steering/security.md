# Security Guidelines

## Authentication & Authorization

### Agent Identity Management

All agents must authenticate using AWS IAM roles with least privilege:

```python
class AgentIdentity:
    def __init__(self, agent_name: str):
        self.role_arn = f"arn:aws:iam::account:role/IncidentCommander-{agent_name}"
        self.session = boto3.Session()
        self.credentials = self.assume_role()

    def assume_role(self):
        return self.session.client('sts').assume_role(
            RoleArn=self.role_arn,
            RoleSessionName=f"{self.agent_name}-session"
        )
```

**Security Requirements:**

- Each agent has dedicated IAM role with minimal permissions
- Rotate credentials every 12 hours
- Use AWS STS for temporary credentials
- Log all authentication attempts

### API Security

#### Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/incidents/trigger")
@limiter.limit("10/minute")
async def trigger_incident(request: Request):
    # Rate limited to prevent abuse
    pass
```

#### Input Validation

```python
from pydantic import BaseModel, validator
import re

class IncidentRequest(BaseModel):
    incident_type: str
    severity: int
    description: str

    @validator('description')
    def sanitize_description(cls, v):
        # Prevent injection attacks
        return re.sub(r'[<>"\']', '', v)[:1000]
```

## Data Protection

### Encryption Standards

**At Rest:**

- All DynamoDB tables encrypted with AWS KMS
- S3 buckets use AES-256 encryption
- Vector database encrypted with customer-managed keys

**In Transit:**

- TLS 1.3 for all API communications
- mTLS for inter-agent communication
- VPC endpoints for AWS service calls

```python
# Encryption helper
class SecureStorage:
    def __init__(self):
        self.kms_client = boto3.client('kms')
        self.key_id = os.environ['INCIDENT_COMMANDER_KMS_KEY']

    def encrypt_sensitive_data(self, data: str) -> str:
        response = self.kms_client.encrypt(
            KeyId=self.key_id,
            Plaintext=data.encode()
        )
        return base64.b64encode(response['CiphertextBlob']).decode()
```

### PII Handling

**Data Classification:**

- Incident logs may contain PII - treat as sensitive
- Redact personal information before storage
- Use tokenization for reversible anonymization

```python
class PIIRedactor:
    def __init__(self):
        self.patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'ip': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b'
        }

    def redact_log(self, log_entry: str) -> str:
        for pattern_name, pattern in self.patterns.items():
            log_entry = re.sub(pattern, f'[REDACTED_{pattern_name.upper()}]', log_entry)
        return log_entry
```

## Access Control

### Zero Trust Architecture

**Principles:**

- Never trust, always verify
- Least privilege access
- Continuous verification
- Assume breach mentality

```python
class ZeroTrustValidator:
    def validate_agent_request(self, agent_id: str, action: str, context: dict) -> bool:
        # Verify agent identity
        if not self.verify_agent_certificate(agent_id):
            return False

        # Check action permissions
        if not self.check_rbac_permissions(agent_id, action):
            return False

        # Validate request context
        if not self.validate_context(context):
            return False

        return True
```

### Role-Based Access Control (RBAC)

```python
AGENT_PERMISSIONS = {
    "detection": [
        "cloudwatch:GetMetricStatistics",
        "logs:FilterLogEvents",
        "dynamodb:PutItem"  # Only write to detection table
    ],
    "diagnosis": [
        "logs:DescribeLogGroups",
        "xray:GetTraceSummaries",
        "dynamodb:GetItem",
        "dynamodb:PutItem"
    ],
    "resolution": [
        "lambda:InvokeFunction",
        "ecs:UpdateService",
        "autoscaling:SetDesiredCapacity",
        "dynamodb:UpdateItem"
    ]
}
```

## Incident Response Security

### Secure Action Execution

All resolution actions must be validated and sandboxed:

```python
class SecureActionExecutor:
    def __init__(self):
        self.sandbox_account = os.environ['SANDBOX_ACCOUNT_ID']
        self.production_account = os.environ['PRODUCTION_ACCOUNT_ID']

    async def execute_action(self, action: ResolutionAction) -> ActionResult:
        # First test in sandbox
        sandbox_result = await self.execute_in_sandbox(action)

        if not sandbox_result.success:
            raise ActionValidationError("Action failed in sandbox")

        # Require additional approval for high-risk actions
        if action.risk_level == "HIGH":
            await self.request_human_approval(action)

        return await self.execute_in_production(action)
```

### Audit Logging

**Security Event Logging:**

```python
class SecurityAuditLogger:
    def log_security_event(self, event_type: str, agent_id: str, details: dict):
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "agent_id": agent_id,
            "source_ip": self.get_source_ip(),
            "user_agent": self.get_user_agent(),
            "details": details,
            "severity": self.calculate_severity(event_type)
        }

        # Send to security SIEM
        self.send_to_siem(audit_entry)

        # Store in tamper-proof log
        self.store_audit_log(audit_entry)
```

**Required Audit Events:**

- Agent authentication/authorization
- Privilege escalation attempts
- Data access and modifications
- Configuration changes
- Failed security validations

## Compliance & Governance

### SOC 2 Type II Requirements

**Access Controls:**

- Multi-factor authentication for admin access
- Regular access reviews and deprovisioning
- Segregation of duties for critical operations

**System Operations:**

- Automated vulnerability scanning
- Patch management procedures
- Incident response procedures

**Change Management:**

- All code changes require peer review
- Automated security testing in CI/CD
- Change approval for production deployments

### Data Retention Policies

```python
class DataRetentionManager:
    RETENTION_POLICIES = {
        "incident_logs": timedelta(days=2555),  # 7 years for compliance
        "agent_communications": timedelta(days=90),
        "metrics_data": timedelta(days=365),
        "audit_logs": timedelta(days=2555)  # 7 years
    }

    async def enforce_retention(self):
        for data_type, retention_period in self.RETENTION_POLICIES.items():
            cutoff_date = datetime.utcnow() - retention_period
            await self.delete_expired_data(data_type, cutoff_date)
```

## Threat Modeling

### Attack Vectors

**Agent Impersonation:**

- Mitigation: Certificate-based authentication
- Detection: Behavioral analysis of agent actions

**Privilege Escalation:**

- Mitigation: Least privilege IAM roles
- Detection: CloudTrail monitoring for role assumptions

**Data Exfiltration:**

- Mitigation: VPC endpoints, encryption
- Detection: Unusual data access patterns

**Supply Chain Attacks:**

- Mitigation: Dependency scanning, signed containers
- Detection: Runtime behavior monitoring

### Security Monitoring

```python
class SecurityMonitor:
    def __init__(self):
        self.anomaly_detector = AnomalyDetector()
        self.threat_intelligence = ThreatIntelligence()

    async def monitor_agent_behavior(self, agent_id: str, action: str):
        # Check against known attack patterns
        if self.threat_intelligence.is_suspicious_pattern(action):
            await self.alert_security_team(agent_id, action)

        # Detect behavioral anomalies
        if self.anomaly_detector.is_anomalous(agent_id, action):
            await self.quarantine_agent(agent_id)
```

## Secure Development Practices

### Code Security

**Static Analysis:**

- Bandit for Python security linting
- Semgrep for custom security rules
- SonarQube for code quality and security

**Dependency Management:**

```bash
# Security scanning in CI/CD
pip-audit --requirement requirements.txt
safety check
snyk test
```

**Secrets Management:**

- Never commit secrets to version control
- Use AWS Secrets Manager for runtime secrets
- Rotate secrets automatically
- Scan for accidentally committed secrets

### Container Security

```dockerfile
# Secure container practices
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install security updates
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

# Copy application
COPY --chown=appuser:appuser . /app
WORKDIR /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python health_check.py
```
