# Deployment Scripts

All deployment-related scripts for the SwarmAI Incident Commander system.

## 📁 Directory Structure

```
deployment/
├── AWS Deployment Scripts
│   ├── deploy_production.py         # Full production deployment
│   ├── deploy_complete_system.py    # Complete system deployment
│   ├── deploy_core_system.py        # Core system only
│   ├── deploy_validated_system.py   # Validated deployment
│   ├── deploy_dashboard_to_aws.py   # Dashboard deployment
│   ├── deploy_simple_dashboard.py   # Simplified dashboard
│   └── validate_deployment.py       # Deployment validation
│
└── Shell Scripts
    ├── deploy_amplify.sh            # AWS Amplify deployment
    ├── deploy_amplify_github.sh     # GitHub + Amplify
    ├── deploy_dashboard_cloudfront.sh # CloudFront setup
    ├── run_deployment.sh            # Main deployment runner
    ├── restart_services.sh          # Service restart
    └── judge-quick-start.sh         # Quick start for judges
```

## 🚀 Quick Start

### Production Deployment
```bash
python deployment/deploy_production.py
```

### Local Testing
```bash
python deployment/deploy_validated_system.py
```

### Validation
```bash
python deployment/validate_deployment.py
```

## 📖 Documentation

For detailed deployment instructions, see:
- [DEPLOYMENT.md](../DEPLOYMENT.md) - Complete deployment guide
- [JUDGES_SETUP_GUIDE.md](../JUDGES_SETUP_GUIDE.md) - Quick setup for judges
- [DEPLOYMENT_QUICK_REFERENCE.md](../DEPLOYMENT_QUICK_REFERENCE.md) - Command reference

## ⚙️ Configuration

All deployment scripts use:
- `.env.production` - Production environment variables
- `.env.example` - Template for configuration
- `requirements.txt` - Python dependencies

## 🔍 Script Details

### deploy_production.py
Complete production deployment including:
- Lambda functions
- API Gateway
- Database setup
- Monitoring configuration
- Security groups

### deploy_complete_system.py
Full system deployment with all components:
- Multi-agent system
- Dashboard (Next.js)
- Backend API (FastAPI)
- AWS services integration

### validate_deployment.py
Validates deployment by checking:
- API endpoints
- Database connectivity
- Service health
- Security configuration

---

**Last Updated**: October 25, 2025
