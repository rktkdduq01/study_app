# CI/CD Pipeline Documentation

## Overview

This project uses GitHub Actions for continuous integration and deployment. The pipeline automatically tests, builds, and deploys the Educational RPG Platform.

## Pipeline Structure

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Commit    │────▶│     CI       │────▶│     CD      │
│   to Git    │     │   Pipeline   │     │  Pipeline   │
└─────────────┘     └──────────────┘     └─────────────┘
                           │                      │
                    ┌──────┴──────┐        ┌─────┴─────┐
                    │             │        │           │
                 Tests        Security   Staging   Production
                           Scanning
```

## CI Pipeline (`.github/workflows/ci.yml`)

Triggered on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

### Jobs

1. **Backend Tests**
   - Linting (ruff, black)
   - Security checks (safety, bandit)
   - Unit and integration tests
   - Coverage reporting

2. **Frontend Tests**
   - Linting (ESLint)
   - Type checking (TypeScript)
   - Unit and component tests
   - Build verification

3. **E2E Tests**
   - Full application tests
   - Cross-browser testing
   - Screenshot on failure

4. **Security Scan**
   - Trivy vulnerability scanning
   - Snyk dependency checks
   - SAST analysis

5. **Code Quality**
   - SonarCloud analysis
   - Code coverage thresholds

6. **Docker Build**
   - Build validation
   - Image scanning

## CD Pipeline (`.github/workflows/cd.yml`)

Triggered on:
- Push to `main` branch
- Manual workflow dispatch

### Deployment Flow

```
main branch → Build Images → Deploy to Staging → Run Tests → Deploy to Production
                                                      ↓
                                                  Rollback
```

### Environments

#### Staging
- Automatic deployment from `main`
- Full environment replication
- Smoke test validation
- URL: `https://staging.educational-rpg.com`

#### Production
- Manual approval required
- Blue-green deployment
- Automatic rollback on failure
- URL: `https://educational-rpg.com`

## Release Pipeline (`.github/workflows/release.yml`)

Triggered on:
- Git tags matching `v*`

### Release Process

1. Generate changelog
2. Create GitHub release
3. Build platform-specific artifacts
4. Publish Docker images
5. Deploy demo environment
6. Update documentation

## Setup Instructions

### 1. GitHub Secrets

Configure these secrets in your GitHub repository:

```yaml
# AWS Credentials
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY

# Docker Hub
DOCKER_USERNAME
DOCKER_PASSWORD

# Database URLs
STAGING_DATABASE_URL
PRODUCTION_DATABASE_URL

# Redis URLs
STAGING_REDIS_URL
PRODUCTION_REDIS_URL

# Security Keys
STAGING_SECRET_KEY
STAGING_JWT_SECRET_KEY
STAGING_ENCRYPTION_KEY
PRODUCTION_SECRET_KEY
PRODUCTION_JWT_SECRET_KEY
PRODUCTION_ENCRYPTION_KEY

# External Services
OPENAI_API_KEY
STRIPE_API_KEY
STRIPE_WEBHOOK_SECRET

# Monitoring
SLACK_WEBHOOK
CODECOV_TOKEN
SONAR_TOKEN
SNYK_TOKEN

# URLs
STAGING_URL
STAGING_API_URL
STAGING_WEBSOCKET_URL
PRODUCTION_URL
CLOUDFRONT_DISTRIBUTION_ID
```

### 2. AWS Setup

1. Create ECS cluster:
```bash
aws ecs create-cluster --cluster-name educational-rpg-cluster
```

2. Create ECR repositories:
```bash
aws ecr create-repository --repository-name educational-rpg/backend
aws ecr create-repository --repository-name educational-rpg/frontend
```

3. Create task definitions:
```bash
aws ecs register-task-definition --cli-input-json file://.aws/task-definition-backend.json
aws ecs register-task-definition --cli-input-json file://.aws/task-definition-frontend.json
```

4. Create services:
```bash
aws ecs create-service --cluster educational-rpg-cluster \
  --service-name educational-rpg-backend-staging \
  --task-definition educational-rpg-backend:1
```

### 3. Local Development

```bash
# Run CI checks locally
./scripts/ci-local.sh

# Deploy to local environment
./scripts/deploy.sh development

# Run specific tests
docker-compose run --rm backend pytest
docker-compose run --rm frontend npm test
```

## Docker Configuration

### Multi-stage Builds

Both backend and frontend use multi-stage builds:

```dockerfile
# Build stage - compile dependencies
FROM base as builder
# ... build steps ...

# Runtime stage - minimal image
FROM base as runtime
COPY --from=builder /app /app
```

### Security

- Non-root user execution
- Minimal base images
- No secrets in images
- Health checks included

## Monitoring & Alerts

### Deployment Notifications

Slack notifications are sent for:
- Deployment start
- Deployment success/failure
- Rollback events

### Metrics

Prometheus metrics available at:
- Response times
- Error rates
- Deployment frequency
- Lead time for changes

## Troubleshooting

### Common Issues

1. **Build Failures**
   ```bash
   # Check logs
   gh run view <run-id>
   
   # Re-run failed jobs
   gh run rerun <run-id>
   ```

2. **Deployment Failures**
   ```bash
   # Check ECS service
   aws ecs describe-services --cluster educational-rpg-cluster \
     --services educational-rpg-backend-production
   
   # View task logs
   aws logs tail /ecs/educational-rpg-backend
   ```

3. **Test Failures**
   ```bash
   # Download artifacts
   gh run download <run-id>
   
   # View test reports
   open playwright-report/index.html
   ```

### Rollback Procedure

Automatic rollback occurs on:
- Health check failures
- Smoke test failures
- Manual trigger

Manual rollback:
```bash
# Rollback to previous version
aws ecs update-service --cluster educational-rpg-cluster \
  --service educational-rpg-backend-production \
  --task-definition educational-rpg-backend:previous
```

## Best Practices

1. **Branch Protection**
   - Require PR reviews
   - Require status checks
   - Require up-to-date branches

2. **Deployment Safety**
   - Always deploy to staging first
   - Run smoke tests
   - Monitor error rates
   - Have rollback plan

3. **Secret Management**
   - Rotate secrets regularly
   - Use least privilege
   - Audit access logs
   - Never commit secrets

## Performance Optimization

### Build Caching

- Docker layer caching
- GitHub Actions cache
- npm/pip dependency caching

### Parallel Execution

- Matrix builds for multiple OS/versions
- Parallel test execution
- Concurrent Docker builds

## Maintenance

### Weekly Tasks
- Review Dependabot PRs
- Check security alerts
- Update dependencies
- Review deployment metrics

### Monthly Tasks
- Rotate secrets
- Review AWS costs
- Update documentation
- Performance review

## Cost Management

### GitHub Actions
- 2,000 free minutes/month
- Use self-hosted runners for heavy workloads

### AWS Resources
- Use spot instances for staging
- Schedule staging shutdown
- Monitor data transfer costs

## Future Improvements

1. **GitOps with ArgoCD**
2. **Canary deployments**
3. **Feature flags**
4. **Multi-region deployment**
5. **Disaster recovery automation**