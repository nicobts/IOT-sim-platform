# CI/CD Pipeline Documentation

Comprehensive CI/CD pipeline using GitHub Actions for automated testing, security scanning, building, and deployment.

## Overview

The CI/CD pipeline consists of 6 main workflows:

1. **Backend CI** - Test and lint Python backend
2. **Frontend React CI** - Test and build Next.js frontend
3. **Frontend Streamlit CI** - Test and validate Streamlit admin
4. **Security** - Vulnerability and secrets scanning
5. **Docker Build** - Build and push container images
6. **Deploy** - Deploy to staging/production

## Workflows

### 1. Backend CI (`backend-ci.yml`)

**Triggers:**
- Push to `main` or `develop` branches (when backend/ changes)
- Pull requests to `main` or `develop` (when backend/ changes)

**Jobs:**

#### Lint and Format Check
- **Black**: Code formatting check
- **isort**: Import sorting check
- **Ruff**: Fast Python linter
- **MyPy**: Static type checking

#### Test
- **Services**: PostgreSQL (TimescaleDB), Redis
- **Coverage**: pytest with coverage reporting
- **Upload**: Coverage to Codecov

#### Build
- **Docker**: Build backend Docker image
- **Test**: Verify image imports successfully

**Status Badge:**
```markdown
![Backend CI](https://github.com/YOUR_ORG/IOT-sim-platform/workflows/Backend%20CI/badge.svg)
```

### 2. Frontend React CI (`frontend-react-ci.yml`)

**Triggers:**
- Push to `main` or `develop` branches (when frontend-react/ changes)
- Pull requests to `main` or `develop` (when frontend-react/ changes)

**Jobs:**

#### Lint and Type Check
- **ESLint**: JavaScript/TypeScript linting
- **TypeScript**: Type checking

#### Build
- **Next.js**: Production build
- **Artifacts**: Upload build artifacts

#### Docker Build
- **Dev**: Build development image
- **Prod**: Build production image

**Status Badge:**
```markdown
![Frontend React CI](https://github.com/YOUR_ORG/IOT-sim-platform/workflows/Frontend%20React%20CI/badge.svg)
```

### 3. Frontend Streamlit CI (`frontend-streamlit-ci.yml`)

**Triggers:**
- Push to `main` or `develop` branches (when frontend-streamlit/ changes)
- Pull requests to `main` or `develop` (when frontend-streamlit/ changes)

**Jobs:**

#### Lint
- **Black**: Code formatting check
- **isort**: Import sorting check
- **Ruff**: Python linting

#### Test
- **Import Check**: Validate Streamlit app imports
- **Syntax Check**: Check Python syntax

#### Docker Build
- **Dev**: Build development image
- **Prod**: Build production image

**Status Badge:**
```markdown
![Frontend Streamlit CI](https://github.com/YOUR_ORG/IOT-sim-platform/workflows/Frontend%20Streamlit%20CI/badge.svg)
```

### 4. Security Scan (`security.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Weekly schedule (Sunday at midnight)

**Jobs:**

#### Backend Security
- **Safety**: Python dependency vulnerability check
- **Bandit**: Security linter for Python

#### Frontend Security
- **npm audit**: Node.js dependency vulnerability check

#### Docker Security
- **Trivy**: Container vulnerability scanner
- Scans all three services (backend, react, streamlit)

#### Secrets Detection
- **Gitleaks**: Detect secrets in git history

#### CodeQL Analysis
- **Languages**: Python and JavaScript
- **Analysis**: Advanced security analysis

**Status Badge:**
```markdown
![Security Scan](https://github.com/YOUR_ORG/IOT-sim-platform/workflows/Security%20Scan/badge.svg)
```

### 5. Docker Build and Push (`docker-build.yml`)

**Triggers:**
- Push to `main` branch
- Tags matching `v*` (e.g., v1.0.0)
- Pull requests to `main` branch

**Jobs:**

#### Build Backend
- **Registry**: GitHub Container Registry (ghcr.io)
- **Tags**: Branch, PR, semver, SHA
- **Cache**: GitHub Actions cache

#### Build Frontend React
- **Registry**: GitHub Container Registry
- **File**: Dockerfile.prod
- **Build Args**: NEXT_PUBLIC_API_URL

#### Build Frontend Streamlit
- **Registry**: GitHub Container Registry
- **File**: Dockerfile.prod

**Images Pushed:**
- `ghcr.io/YOUR_ORG/iot-sim-platform/backend`
- `ghcr.io/YOUR_ORG/iot-sim-platform/frontend-react`
- `ghcr.io/YOUR_ORG/iot-sim-platform/frontend-streamlit`

**Status Badge:**
```markdown
![Docker Build](https://github.com/YOUR_ORG/IOT-sim-platform/workflows/Docker%20Build%20and%20Push/badge.svg)
```

### 6. Deploy (`deploy.yml`)

**Triggers:**
- Manual workflow dispatch only

**Inputs:**
- **environment**: staging or production
- **version**: Tag or branch to deploy

**Jobs:**

#### Deploy
- **SSH**: Configure SSH for remote deployment
- **Staging**: Deploy to staging environment
- **Production**:
  - Copy files to server
  - Pull latest images
  - Run database migrations
  - Zero-downtime deployment
  - Health check
- **Notification**: Slack notification

#### Rollback (on failure)
- Automatic rollback on deployment failure
- Slack notification

**Manual Trigger:**
```bash
# Via GitHub UI: Actions → Deploy → Run workflow
# Select environment and version
```

## Required Secrets

Configure these secrets in GitHub Settings → Secrets:

### Docker Registry
- `GITHUB_TOKEN` - Automatically provided

### Deployment (Production)
- `SSH_PRIVATE_KEY` - SSH key for deployment server
- `DEPLOY_HOST` - Deployment server hostname
- `DEPLOY_USER` - SSH username

### Notifications
- `SLACK_WEBHOOK` - Slack webhook URL for notifications

### Optional
- `NEXT_PUBLIC_API_URL` - Public API URL for React frontend
- `CODECOV_TOKEN` - Codecov upload token
- `GITLEAKS_LICENSE` - Gitleaks Pro license (optional)

## Branch Protection Rules

Recommended branch protection for `main`:

```yaml
Require pull request reviews: 1 approval
Require status checks:
  - Backend CI / lint-and-format
  - Backend CI / test
  - Frontend React CI / lint-and-type-check
  - Frontend React CI / build
  - Frontend Streamlit CI / lint
  - Security Scan / backend-security
  - Security Scan / frontend-security
  - Security Scan / secrets-scan

Require branches to be up to date: true
Require conversation resolution: true
```

## Deployment Process

### Staging Deployment

1. Merge feature branch to `develop`
2. CI workflows run automatically
3. Manual deployment:
   ```bash
   Actions → Deploy → Run workflow
   Environment: staging
   Version: develop
   ```

### Production Deployment

1. Create release tag:
   ```bash
   git tag -a v1.0.0 -m "Release v1.0.0"
   git push origin v1.0.0
   ```

2. Docker images build automatically

3. Manual deployment:
   ```bash
   Actions → Deploy → Run workflow
   Environment: production
   Version: v1.0.0
   ```

4. Deployment steps:
   - Copy configuration files
   - Pull Docker images
   - Run database migrations
   - Rolling update (zero-downtime)
   - Health check
   - Slack notification

## Monitoring Deployments

### GitHub Actions UI
1. Go to Actions tab
2. Select workflow
3. View run details, logs, and artifacts

### Deployment Notifications
- Slack notifications for deployment status
- GitHub deployment status
- Email notifications (configurable)

### Rollback Procedure

If deployment fails:
1. Automatic rollback triggers
2. Previous version redeployed
3. Slack notification sent

Manual rollback:
```bash
# Redeploy previous version
Actions → Deploy → Run workflow
Environment: production
Version: v1.0.0  # Previous stable version
```

## Local Development

### Running CI Checks Locally

**Backend:**
```bash
cd backend

# Format check
black --check .
isort --check-only .

# Lint
ruff check .

# Type check
mypy app/ --ignore-missing-imports

# Test
pytest tests/ -v --cov=app
```

**Frontend React:**
```bash
cd frontend-react

# Lint
npm run lint

# Type check
npm run type-check

# Build
npm run build
```

**Frontend Streamlit:**
```bash
cd frontend-streamlit

# Format check
black --check .
isort --check-only .

# Lint
ruff check .

# Import check
python -c "import streamlit; import app"
```

### Testing Docker Builds Locally

```bash
# Backend
cd backend
docker build -t iot-backend:local .

# Frontend React
cd frontend-react
docker build -f Dockerfile.prod -t iot-frontend-react:local .

# Frontend Streamlit
cd frontend-streamlit
docker build -f Dockerfile.prod -t iot-frontend-streamlit:local .
```

## Troubleshooting

### CI Failures

**Linting errors:**
```bash
# Auto-fix formatting
black .
isort .

# Check remaining issues
ruff check . --fix
```

**Test failures:**
```bash
# Run specific test
pytest tests/path/to/test.py::test_name -v

# Run with verbose output
pytest -vv --tb=long
```

**Build failures:**
```bash
# Check Docker build locally
docker build --no-cache -t test:local .

# Check logs
docker logs <container-id>
```

### Deployment Issues

**SSH connection failed:**
- Verify SSH_PRIVATE_KEY secret
- Check DEPLOY_HOST is accessible
- Verify DEPLOY_USER has permissions

**Health check failed:**
- Check service logs: `docker-compose logs`
- Verify environment variables
- Check database connectivity

**Database migration failed:**
- Check migration files
- Verify database connection
- Review migration logs

## Best Practices

### Commit Messages
Follow conventional commits:
```
feat: Add new feature
fix: Fix bug
docs: Update documentation
test: Add tests
ci: Update CI configuration
refactor: Refactor code
```

### Pull Requests
- Wait for all checks to pass
- Request review from team members
- Squash commits before merging
- Delete branch after merge

### Security
- Never commit secrets
- Use GitHub Secrets for sensitive data
- Enable branch protection
- Require signed commits (optional)
- Review security scan results

### Performance
- Use caching for dependencies
- Parallel job execution where possible
- Optimize Docker build layers
- Use multi-stage builds

## Metrics and Monitoring

### GitHub Insights
- View workflow run history
- Monitor success/failure rates
- Track deployment frequency
- Measure lead time for changes

### Code Coverage
- View coverage reports in Codecov
- Track coverage trends
- Identify untested code
- Set coverage thresholds

### Security Alerts
- Review Dependabot alerts
- Monitor security scan results
- Track vulnerability remediation
- Update dependencies regularly

## Future Enhancements

### Planned Improvements
- [ ] Add performance testing
- [ ] Implement canary deployments
- [ ] Add integration tests
- [ ] Set up preview environments
- [ ] Add automated rollback triggers
- [ ] Implement blue-green deployments
- [ ] Add load testing
- [ ] Integrate with monitoring (Datadog, New Relic)
- [ ] Add automated changelog generation
- [ ] Implement semantic versioning automation

### Optional Integrations
- Jira integration for issue tracking
- PagerDuty for on-call alerts
- Sentry for error tracking
- Datadog for APM
- ArgoCD for GitOps

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
- [CodeQL](https://codeql.github.com/)
- [Trivy Scanner](https://github.com/aquasecurity/trivy)
- [Dependabot](https://docs.github.com/en/code-security/dependabot)
