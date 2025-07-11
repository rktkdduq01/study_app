# Production Deployment Guide

## Overview

This guide covers the complete production deployment process for the Educational RPG Platform.

## Prerequisites

### Required Tools
- AWS CLI configured with production credentials
- Docker and Docker Compose
- Terraform >= 1.0
- kubectl with kubeconfig for production cluster
- PostgreSQL client tools
- Node.js >= 18.x

### Access Requirements
- AWS production account access
- Database credentials in AWS SSM
- Slack webhook for notifications
- PagerDuty integration for alerts

## Infrastructure Setup

### 1. Initial Infrastructure Deployment

```bash
# Navigate to terraform directory
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Review infrastructure plan
terraform plan -out=tfplan

# Apply infrastructure
terraform apply tfplan
```

### 2. SSL Certificate Setup

```bash
# Generate SSL certificates
./scripts/setup-ssl-certificates.sh generate

# Verify certificates
./scripts/setup-ssl-certificates.sh verify

# Setup auto-renewal
./scripts/setup-ssl-certificates.sh auto-renew
```

## Application Deployment

### 1. First-Time Deployment

```bash
# Set environment
export ENVIRONMENT=production

# Run deployment script
./scripts/production-deploy.sh
```

The deployment script will:
1. Check prerequisites
2. Build and push Docker images
3. Run database migrations
4. Deploy to ECS
5. Wait for services to stabilize
6. Run smoke tests
7. Invalidate CloudFront cache
8. Send deployment notification

### 2. Database Setup

```bash
# Initial database setup
psql -h $DB_HOST -U $DB_USER -d postgres -c "CREATE DATABASE educational_rpg;"

# Run initial migrations
docker run --rm \
  -e DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST/educational_rpg" \
  educational-rpg-backend:latest \
  alembic upgrade head

# Verify database
psql -h $DB_HOST -U $DB_USER -d educational_rpg -c "\dt"
```

### 3. Environment Variables

Production environment variables are stored in AWS SSM Parameter Store:

```bash
# Backend secrets
aws ssm put-parameter --name "/educational-rpg/production/secret-key" --value "..." --type SecureString
aws ssm put-parameter --name "/educational-rpg/production/jwt-secret" --value "..." --type SecureString
aws ssm put-parameter --name "/educational-rpg/production/openai-api-key" --value "..." --type SecureString
aws ssm put-parameter --name "/educational-rpg/production/stripe-api-key" --value "..." --type SecureString

# Database configuration
aws ssm put-parameter --name "/educational-rpg/production/database-url" --value "..." --type SecureString
aws ssm put-parameter --name "/educational-rpg/production/redis-url" --value "..." --type SecureString
```

## Monitoring Setup

### 1. Prometheus Configuration

```bash
# Apply Prometheus rules
kubectl apply -f infrastructure/monitoring/prometheus-rules.yaml

# Verify rules loaded
kubectl -n monitoring exec -it prometheus-0 -- promtool check rules /etc/prometheus/rules/*.yaml
```

### 2. Grafana Dashboard

```bash
# Import dashboard
curl -X POST http://grafana.educational-rpg.com/api/dashboards/db \
  -H "Authorization: Bearer $GRAFANA_API_KEY" \
  -H "Content-Type: application/json" \
  -d @infrastructure/monitoring/grafana-dashboard.json
```

### 3. Alert Configuration

Configure alert channels in Grafana:
1. Navigate to Alerting > Notification channels
2. Add Slack webhook
3. Add PagerDuty integration
4. Test notifications

## Backup Configuration

### 1. Database Backups

```bash
# Setup backup cron job
crontab -e

# Add backup schedule (every 2 hours)
0 */2 * * * /scripts/backup-database.sh >> /var/log/backup.log 2>&1

# Test backup
./scripts/backup-database.sh
```

### 2. Application Data Backups

S3 versioning is enabled for all user data buckets. Configure lifecycle policies:

```bash
aws s3api put-bucket-lifecycle-configuration \
  --bucket educational-rpg-uploads \
  --lifecycle-configuration file://s3-lifecycle.json
```

## Security Checklist

### Pre-Deployment
- [ ] All secrets rotated and stored in SSM
- [ ] Security groups reviewed and minimized
- [ ] WAF rules configured
- [ ] SSL certificates valid
- [ ] CORS origins restricted

### Post-Deployment
- [ ] Run security scan: `./scripts/security-scan.sh`
- [ ] Verify HTTPS enforcement
- [ ] Check rate limiting active
- [ ] Confirm encryption at rest
- [ ] Test authentication flows

## Deployment Verification

### 1. Health Checks

```bash
# Backend health
curl https://api.educational-rpg.com/health

# Frontend health
curl https://educational-rpg.com/

# WebSocket test
wscat -c wss://api.educational-rpg.com/ws
```

### 2. Smoke Tests

```bash
# Run automated smoke tests
PLAYWRIGHT_BASE_URL=https://educational-rpg.com npm run test:e2e -- --grep "@smoke"
```

### 3. Performance Tests

```bash
# Run load test
artillery run tests/load/production.yml
```

## Rollback Procedures

### Quick Rollback

```bash
# Rollback to previous version
./scripts/rollback-deployment.sh backend PREVIOUS_VERSION
./scripts/rollback-deployment.sh frontend PREVIOUS_VERSION
```

### Database Rollback

```bash
# Restore from backup
./scripts/restore-database.sh

# Or rollback specific migration
docker run --rm \
  -e DATABASE_URL="$DATABASE_URL" \
  educational-rpg-backend:latest \
  alembic downgrade -1
```

## Troubleshooting

### Common Issues

#### 1. Deployment Fails
```bash
# Check ECS service events
aws ecs describe-services \
  --cluster educational-rpg-cluster \
  --services educational-rpg-backend-production

# Check task logs
aws logs tail /ecs/educational-rpg-backend --follow
```

#### 2. Database Connection Issues
```bash
# Test connection
psql -h $DB_HOST -U $DB_USER -d educational_rpg -c "SELECT 1"

# Check security group
aws ec2 describe-security-groups --group-ids sg-xxxxx
```

#### 3. High Error Rate
```bash
# Check application logs
aws logs insights query \
  --log-group-name /ecs/educational-rpg-backend \
  --query-string 'fields @timestamp, @message | filter @message like /ERROR/'
```

## Maintenance Procedures

### 1. Enable Maintenance Mode

```bash
# Update environment variable
aws ssm put-parameter \
  --name "/educational-rpg/production/maintenance-mode" \
  --value "true" \
  --overwrite

# Restart services
aws ecs update-service \
  --cluster educational-rpg-cluster \
  --service educational-rpg-backend-production \
  --force-new-deployment
```

### 2. Database Maintenance

```bash
# Analyze and vacuum
psql -h $DB_HOST -U $DB_USER -d educational_rpg <<EOF
ANALYZE;
VACUUM ANALYZE;
EOF
```

### 3. Cache Clearing

```bash
# Clear Redis cache
redis-cli -h $REDIS_HOST FLUSHALL

# Clear CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id $DISTRIBUTION_ID \
  --paths "/*"
```

## Post-Deployment Tasks

1. **Update Status Page**
   - Mark deployment complete
   - Update version number
   - Clear any incidents

2. **Monitor Metrics**
   - Watch error rates for 30 minutes
   - Check performance metrics
   - Verify all alerts cleared

3. **Documentation**
   - Update deployment log
   - Note any issues encountered
   - Document configuration changes

4. **Communication**
   - Notify team in Slack
   - Update stakeholders
   - Send release notes if applicable

## Contact Information

- **DevOps On-Call**: Check PagerDuty
- **AWS Support**: Premium support portal
- **Database Admin**: dba@educational-rpg.com
- **Security Team**: security@educational-rpg.com

Last Updated: 2024-03-15
Version: 1.0.0