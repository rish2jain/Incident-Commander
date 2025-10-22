# Deployment Scripts

AWS deployment and infrastructure management scripts for the Incident Commander system.

## Scripts

### Deployment
- `deploy_complete_system.py` - Complete system deployment to AWS
- `deploy_to_aws.py` - Standard AWS deployment
- `deploy_ultimate_system.py` - Ultimate system deployment

**Note:** These scripts may have overlapping functionality. Review and consolidate as needed.

### Setup and Configuration
- `setup_aws_credentials.py` - Configure AWS credentials
- `harden_security.py` - Apply security hardening measures

### Fixes and Maintenance
- `fix_dashboard_lambda.py` - Dashboard Lambda function fixes

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
