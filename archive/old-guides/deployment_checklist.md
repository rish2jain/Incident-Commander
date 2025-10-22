# Production Deployment Checklist

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
