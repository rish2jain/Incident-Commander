# Deployment Scripts

AWS deployment and infrastructure management scripts for the Incident Commander system.

## Primary Deployment Script

### ⭐ **deploy_to_aws.py** - Canonical Deployment Script
The primary, production-ready deployment script using CloudFormation infrastructure as code.

**Features:**
- CloudFormation-based infrastructure management
- Environment parameterization (demo, staging, production)
- Versioned deployment artifacts in S3
- Comprehensive error handling and rollback capability
- Production-ready AWS best practices

**When to Use:** This is the default script for all deployments.

## Supporting Scripts

### Setup and Configuration
- `setup_aws_credentials.py` - Configure AWS credentials interactively
- `harden_security.py` - Apply security hardening to deployed resources

### Fixes and Maintenance
- `fix_dashboard_lambda.py` - Fix and update dashboard Lambda function

## Archived Scripts

The following scripts have been archived due to overlap with deploy_to_aws.py:
- `scripts/archive/deploy_complete_system_ARCHIVED_OCT22.py` - S3 static hosting approach (superseded)
- `scripts/archive/deploy_ultimate_system_ARCHIVED_OCT22.py` - AWS AI services deployment (superseded)

**See:** [scripts/archive/README.md](../archive/README.md) for archival details and migration notes.

## Usage

### Initial Setup
```bash
python scripts/deployment/setup_aws_credentials.py
```

### Deployment
```bash
python scripts/deployment/deploy_to_aws.py
```

### Security Hardening
```bash
python scripts/deployment/harden_security.py
```

## Prerequisites
- AWS CLI configured
- Appropriate AWS credentials
- Required environment variables set
- CDK installed (for infrastructure as code)

## Notes
- Review deployment scripts for current canonical version
- Some scripts may be superseded - check documentation
- Always test in non-production environment first
