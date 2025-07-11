# Disaster Recovery Plan

## Overview

This document outlines the disaster recovery procedures for the Educational RPG Platform production environment.

## Recovery Time Objectives (RTO) and Recovery Point Objectives (RPO)

- **RTO**: 4 hours
- **RPO**: 1 hour
- **Backup Frequency**: Every 2 hours
- **Backup Retention**: 30 days

## Backup Strategy

### Database Backups
- **Type**: PostgreSQL custom format dumps
- **Schedule**: Every 2 hours via cron job
- **Location**: S3 bucket `educational-rpg-backups/postgresql/`
- **Encryption**: Server-side encryption with AWS KMS
- **Script**: `/scripts/backup-database.sh`

### Application Data
- **User uploads**: Replicated to S3 with versioning enabled
- **Static assets**: Stored in S3 with CloudFront CDN
- **Configuration**: Stored in AWS SSM Parameter Store

### Infrastructure
- **Definition**: Terraform state files in S3 backend
- **Version Control**: All infrastructure code in Git

## Recovery Procedures

### 1. Database Recovery

#### Complete Database Restoration
```bash
# List available backups
./scripts/restore-database.sh

# Restore specific backup
./scripts/restore-database.sh postgresql/educational_rpg_backup_20240315_120000.tar.gz
```

#### Point-in-Time Recovery
```bash
# Enable WAL archiving (already configured)
# Restore to specific time
pg_restore --time="2024-03-15 11:30:00" ...
```

### 2. Application Recovery

#### Backend Service Recovery
```bash
# Deploy last known good version
aws ecs update-service \
  --cluster educational-rpg-cluster \
  --service educational-rpg-backend-production \
  --task-definition educational-rpg-backend:LAST_GOOD_VERSION

# Or rollback using deployment script
./scripts/rollback-deployment.sh backend LAST_GOOD_VERSION
```

#### Frontend Service Recovery
```bash
# Rollback CloudFront to previous version
aws cloudfront create-invalidation \
  --distribution-id $DISTRIBUTION_ID \
  --paths "/*"

# Deploy previous frontend version
./scripts/rollback-deployment.sh frontend LAST_GOOD_VERSION
```

### 3. Infrastructure Recovery

#### VPC and Network Recovery
```bash
cd infrastructure/terraform
terraform init
terraform plan
terraform apply
```

#### ECS Cluster Recovery
```bash
# Recreate ECS cluster
aws ecs create-cluster --cluster-name educational-rpg-cluster

# Redeploy services
terraform apply -target=module.ecs
```

## Disaster Scenarios

### Scenario 1: Database Corruption
1. Stop application services to prevent further corruption
2. Create backup of corrupted database
3. Restore from last known good backup
4. Verify data integrity
5. Resume services

### Scenario 2: Region Outage
1. Activate DR site in secondary region (us-east-1)
2. Update Route53 to point to DR site
3. Restore database from cross-region replicated backups
4. Monitor and wait for primary region recovery

### Scenario 3: Security Breach
1. Immediately isolate affected systems
2. Rotate all credentials and keys
3. Restore from backup prior to breach
4. Implement additional security measures
5. Conduct security audit

### Scenario 4: Data Loss
1. Identify scope of data loss
2. Restore from most recent backup
3. Replay transaction logs if available
4. Notify affected users
5. Implement additional safeguards

## Testing Procedures

### Monthly DR Drills
1. **Backup Verification**
   ```bash
   # Test restore to staging environment
   ./scripts/test-backup-restore.sh
   ```

2. **Failover Testing**
   - Simulate service failures
   - Test automatic failover
   - Verify monitoring alerts

3. **Recovery Time Testing**
   - Measure actual recovery times
   - Document bottlenecks
   - Optimize procedures

## Contact Information

### Escalation Path
1. **On-Call Engineer**: Check PagerDuty
2. **Team Lead**: via Slack #emergency
3. **CTO**: Phone number in 1Password
4. **AWS Support**: Premium support ticket

### External Contacts
- **AWS Support**: Enterprise support plan
- **Database Consultant**: DBA team contact
- **Security Team**: security@educational-rpg.com

## Monitoring and Alerts

### Critical Alerts
- Database down > 2 minutes
- Backend service unavailable
- High error rate (>10%)
- Security breach detected

### Alert Channels
- PagerDuty: Critical alerts
- Slack: #alerts channel
- Email: ops@educational-rpg.com

## Post-Recovery Actions

1. **Verification Checklist**
   - [ ] All services operational
   - [ ] Database integrity verified
   - [ ] No data loss confirmed
   - [ ] Performance metrics normal
   - [ ] Security scan completed

2. **Communication**
   - [ ] Update status page
   - [ ] Notify stakeholders
   - [ ] Send user communications
   - [ ] Document incident

3. **Review and Improvement**
   - [ ] Conduct post-mortem
   - [ ] Update runbooks
   - [ ] Implement improvements
   - [ ] Schedule follow-up

## Automation Scripts

### Health Check Script
```bash
#!/bin/bash
# Check all services
./scripts/health-check-all.sh

# Output:
# ✅ Database: Healthy
# ✅ Backend: Healthy (3/3 instances)
# ✅ Frontend: Healthy (3/3 instances)
# ✅ Redis: Healthy
# ✅ S3: Accessible
```

### Quick Recovery Script
```bash
#!/bin/bash
# One-command recovery
./scripts/quick-recovery.sh --service=all --restore-point=latest
```

## Documentation Updates

This disaster recovery plan should be reviewed and updated:
- Quarterly by the DevOps team
- After any major incident
- When infrastructure changes significantly
- During annual security audits

Last Updated: 2024-03-15
Next Review: 2024-06-15