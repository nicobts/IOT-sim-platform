# IOT SIM Platform - Deployment Guide

Comprehensive guide for deploying the full-stack IOT SIM Platform monorepo to production.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Development Deployment](#development-deployment)
- [Production Deployment](#production-deployment)
- [Environment Configuration](#environment-configuration)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Monitoring Setup](#monitoring-setup)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)
- [Security Best Practices](#security-best-practices)

---

## Overview

The IOT SIM Platform is a full-stack monorepo with multiple services:

- **Backend API** (FastAPI) - Port 8000
- **Frontend Dashboard** (Next.js) - Port 3000
- **Admin Panel** (Streamlit) - Port 8501
- **Monitoring** (Prometheus + Grafana) - Ports 9090, 3001
- **Database** (PostgreSQL + TimescaleDB) - Port 5432
- **Cache** (Redis) - Port 6379
- **Reverse Proxy** (Nginx) - Port 80, 443

---

## Prerequisites

### Required Software

- **Docker** 24.0+ and Docker Compose 2.20+
- **Git** for source control
- **1NCE API Credentials** (client ID and secret)

### Optional Tools

- **kubectl** (for Kubernetes deployment)
- **terraform** (for infrastructure as code)
- **helm** (for Kubernetes package management)
- **GitHub CLI** (for CI/CD setup)

### Infrastructure Requirements

**Minimum (Development):**
- 4 CPU cores
- 8GB RAM
- 50GB disk space
- Ubuntu 20.04+ or equivalent

**Recommended (Production):**
- 8+ CPU cores
- 16GB+ RAM
- 100GB+ SSD storage
- Load balancer
- Managed PostgreSQL (e.g., AWS RDS, GCP Cloud SQL)
- Managed Redis (e.g., AWS ElastiCache, Redis Cloud)

---

## Quick Start

### 1. Clone Repository

```bash
git clone <repository-url>
cd IOT-sim-platform
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your configuration
nano .env

# Required: Set your 1NCE credentials
# ONCE_CLIENT_ID=your_client_id
# ONCE_CLIENT_SECRET=your_client_secret
```

### 3. Start All Services

```bash
# Start all services in development mode
docker-compose up -d

# View logs
docker-compose logs -f

# Check service health
docker-compose ps
```

### 4. Initialize Database

```bash
# Run database migrations
docker-compose exec backend alembic upgrade head

# Create admin user
docker-compose exec backend python scripts/create_admin.py
```

### 5. Access Services

- **React Dashboard**: http://localhost:3000
- **Streamlit Admin**: http://localhost:8501 (admin/admin123)
- **Backend API**: http://localhost:8000/docs
- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090

---

## Development Deployment

### Using Docker Compose (Recommended)

The development environment uses `docker-compose.yml`:

```bash
# Start all services with hot reload
docker-compose up -d

# Start specific service
docker-compose up -d backend

# View service logs
docker-compose logs -f backend

# Restart service after code changes
docker-compose restart backend

# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

### Local Development (Without Docker)

**Backend:**
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend React:**
```bash
cd frontend-react

# Install dependencies
npm install

# Run development server
npm run dev
# Access at http://localhost:3000
```

**Frontend Streamlit:**
```bash
cd frontend-streamlit

# Install dependencies
pip install -r requirements.txt

# Run development server
streamlit run app.py
# Access at http://localhost:8501
```

### Development Tools

**Code Quality:**
```bash
# Backend linting
cd backend
black app/ tests/
isort app/ tests/
ruff check app/ tests/
mypy app/

# Frontend linting
cd frontend-react
npm run lint
npm run type-check
```

**Testing:**
```bash
# Backend tests
cd backend
pytest --cov=app --cov-report=html

# Frontend tests
cd frontend-react
npm test
```

---

## Production Deployment

### Using Docker Compose Production

The production environment uses `docker-compose.prod.yml` with:
- Resource limits
- Health checks
- Logging configuration
- Security hardening
- Multiple backend replicas

**1. Prepare Environment:**

```bash
# Copy production environment template
cp .env.example .env.production

# Edit with production settings
nano .env.production
```

**Critical Production Settings:**
```bash
# Environment
ENVIRONMENT=production

# Security
SECRET_KEY=<generate-with: openssl rand -hex 32>
DEBUG=false

# Database (use managed service)
DATABASE_URL=postgresql+asyncpg://user:password@db-host:5432/iot_platform
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis (use managed service)
REDIS_URL=redis://redis-host:6379/0
REDIS_PASSWORD=<strong-password>

# 1NCE API
ONCE_CLIENT_ID=<production-client-id>
ONCE_CLIENT_SECRET=<production-client-secret>

# Frontend URLs
NEXT_PUBLIC_API_URL=https://api.yourdomain.com

# Monitoring
GRAFANA_ADMIN_PASSWORD=<strong-password>

# SSL
ENABLE_SSL=true
```

**2. Deploy Services:**

```bash
# Pull latest images
docker-compose -f docker-compose.prod.yml pull

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Create admin user
docker-compose -f docker-compose.prod.yml exec backend python scripts/create_admin.py

# Check health
curl http://localhost:8000/health
```

**3. Configure SSL/TLS:**

```bash
# Generate SSL certificates (Let's Encrypt recommended)
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Or use self-signed for testing
cd nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout server.key -out server.crt

# Update nginx configuration
cp nginx/conf.d/ssl.conf.example nginx/conf.d/ssl.conf
nano nginx/conf.d/ssl.conf

# Restart nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

**4. Verify Deployment:**

```bash
# Check all services are running
docker-compose -f docker-compose.prod.yml ps

# Check logs for errors
docker-compose -f docker-compose.prod.yml logs

# Test endpoints
curl https://yourdomain.com/health
curl https://yourdomain.com/api/v1/health/ready
```

---

## Environment Configuration

### Environment Variables

The platform uses a comprehensive `.env` file for configuration. See `.env.example` for all options.

**Key Sections:**

1. **Database Configuration**
```bash
DATABASE_USER=postgres
DATABASE_PASSWORD=<strong-password>
DATABASE_NAME=iot_sim_db
DATABASE_HOST=db
DATABASE_PORT=5432
DATABASE_URL=postgresql+asyncpg://${DATABASE_USER}:${DATABASE_PASSWORD}@${DATABASE_HOST}:${DATABASE_PORT}/${DATABASE_NAME}
```

2. **Redis Configuration**
```bash
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=<strong-password>
REDIS_DB=0
REDIS_URL=redis://:${REDIS_PASSWORD}@${REDIS_HOST}:${REDIS_PORT}/${REDIS_DB}
```

3. **Backend Configuration**
```bash
ENVIRONMENT=production
SECRET_KEY=<generate-random>
DEBUG=false
CORS_ORIGINS=["https://yourdomain.com"]
API_PREFIX=/api/v1
```

4. **1NCE API Configuration**
```bash
ONCE_CLIENT_ID=<your-client-id>
ONCE_CLIENT_SECRET=<your-client-secret>
ONCE_API_BASE_URL=https://api.1nce.com
```

5. **Frontend Configuration**
```bash
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

6. **Monitoring Configuration**
```bash
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=<strong-password>
PROMETHEUS_RETENTION=90d
```

### Secrets Management

**Production Best Practices:**

1. **Use Secret Management Tools:**
```bash
# AWS Secrets Manager
aws secretsmanager get-secret-value --secret-id iot-platform/production

# HashiCorp Vault
vault kv get secret/iot-platform/production

# Docker Secrets
echo "my_secret" | docker secret create db_password -
```

2. **Never Commit Secrets:**
```bash
# .env files are in .gitignore
# Use .env.example as template only
```

3. **Rotate Secrets Regularly:**
```bash
# Rotate JWT secret
openssl rand -hex 32 > new_secret.txt

# Update .env
# Restart services
docker-compose -f docker-compose.prod.yml restart backend
```

---

## Docker Deployment

### Building Images

**Build All Services:**
```bash
# Development images
docker-compose build

# Production images
docker-compose -f docker-compose.prod.yml build

# Build specific service
docker-compose build backend
```

**Push to Registry:**
```bash
# Tag images
docker tag iot-backend:latest ghcr.io/your-org/iot-backend:v1.0.0
docker tag iot-frontend-react:latest ghcr.io/your-org/iot-frontend-react:v1.0.0
docker tag iot-frontend-streamlit:latest ghcr.io/your-org/iot-frontend-streamlit:v1.0.0

# Push to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
docker push ghcr.io/your-org/iot-backend:v1.0.0
docker push ghcr.io/your-org/iot-frontend-react:v1.0.0
docker push ghcr.io/your-org/iot-frontend-streamlit:v1.0.0
```

### Resource Limits

Production `docker-compose.prod.yml` includes resource limits:

```yaml
services:
  backend:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

Adjust based on your workload.

---

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (1.24+)
- kubectl configured
- Helm 3+ (recommended)

### Deployment Steps

**1. Create Namespace:**
```bash
kubectl create namespace iot-platform
```

**2. Create Secrets:**
```bash
# Create secret from .env file
kubectl create secret generic iot-platform-env \
  --from-env-file=.env.production \
  -n iot-platform

# Create registry secret (if using private registry)
kubectl create secret docker-registry regcred \
  --docker-server=ghcr.io \
  --docker-username=<username> \
  --docker-password=<token> \
  -n iot-platform
```

**3. Deploy PostgreSQL (if not using managed service):**
```bash
# Using Helm
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install postgresql bitnami/postgresql \
  --namespace iot-platform \
  --set auth.username=postgres \
  --set auth.password=<password> \
  --set auth.database=iot_sim_db
```

**4. Deploy Redis:**
```bash
helm install redis bitnami/redis \
  --namespace iot-platform \
  --set auth.password=<password>
```

**5. Deploy Application:**

Create `k8s/` directory with manifests:

**backend-deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: iot-platform
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: ghcr.io/your-org/iot-backend:v1.0.0
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: iot-platform-env
        resources:
          limits:
            cpu: 1000m
            memory: 1Gi
          requests:
            cpu: 500m
            memory: 512Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
```

**Deploy:**
```bash
kubectl apply -f k8s/ -n iot-platform

# Check status
kubectl get pods -n iot-platform
kubectl get services -n iot-platform

# View logs
kubectl logs -f deployment/backend -n iot-platform
```

**6. Expose Services:**
```bash
# Create ingress
kubectl apply -f k8s/ingress.yaml

# Or use LoadBalancer
kubectl expose deployment backend \
  --type=LoadBalancer \
  --port=80 \
  --target-port=8000 \
  -n iot-platform
```

---

## Monitoring Setup

### Prometheus & Grafana

**Access Dashboards:**

1. **Grafana** (http://localhost:3001)
   - Login: admin / (password from .env)
   - Dashboards:
     - Backend API Dashboard
     - System Overview
     - SIM Metrics

2. **Prometheus** (http://localhost:9090)
   - Metrics collection
   - Alert rules
   - Query interface

**Configure Alerts:**

Edit `monitoring/prometheus/alerts.yml` to customize alert rules.

**Notification Channels:**

```bash
# Configure Slack notifications
# Edit monitoring/grafana/provisioning/notifiers/slack.yml

# Test alerts
docker-compose exec prometheus promtool check rules /etc/prometheus/alerts.yml
```

### Application Metrics

The backend exposes metrics at `/api/v1/metrics`:

- HTTP request metrics
- Database connection pool
- Cache hit/miss ratios
- SIM-specific metrics
- 1NCE API call metrics

### Logs

**View Logs:**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend

# Follow with timestamps
docker-compose logs -f -t backend
```

**Log Aggregation (Production):**

Consider integrating with:
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Loki + Grafana**
- **Datadog**
- **CloudWatch** (AWS)
- **Stackdriver** (GCP)

---

## CI/CD Integration

The platform includes comprehensive GitHub Actions workflows.

### Workflows

1. **Backend CI** - Lint, test, build backend
2. **Frontend React CI** - Lint, type-check, build React app
3. **Frontend Streamlit CI** - Lint, validate Streamlit app
4. **Security Scan** - Vulnerability and secrets scanning
5. **Docker Build** - Build and push images to registry
6. **Deploy** - Deploy to staging/production

See [.github/CICD.md](.github/CICD.md) for complete documentation.

### Setup

**1. Configure Secrets:**

GitHub Settings → Secrets → Actions:

```
GITHUB_TOKEN (automatic)
SSH_PRIVATE_KEY
DEPLOY_HOST
DEPLOY_USER
SLACK_WEBHOOK
NEXT_PUBLIC_API_URL
CODECOV_TOKEN (optional)
```

**2. Branch Protection:**

Enable for `main` branch:
- Require pull request reviews
- Require status checks to pass
- Require branches to be up to date

**3. Manual Deployment:**

```bash
# Via GitHub UI
Actions → Deploy → Run workflow
Select: environment (staging/production)
        version (tag or branch)

# Or via GitHub CLI
gh workflow run deploy.yml \
  -f environment=production \
  -f version=v1.0.0
```

---

## Troubleshooting

### Common Issues

**1. Database Connection Failed**

```bash
# Check database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Verify DATABASE_URL in .env
echo $DATABASE_URL

# Test connection
docker-compose exec backend python -c "from app.db.session import engine; print(engine)"
```

**2. Redis Connection Failed**

```bash
# Check Redis is running
docker-compose ps redis

# Test connection
docker-compose exec redis redis-cli ping

# Check REDIS_URL
echo $REDIS_URL
```

**3. 1NCE API Authentication Failed**

```bash
# Verify credentials
echo $ONCE_CLIENT_ID
echo $ONCE_CLIENT_SECRET

# Test API connection
docker-compose exec backend python -c "from app.clients.once import OnceClient; client = OnceClient(); print(client.get_auth_token())"
```

**4. Frontend Can't Connect to Backend**

```bash
# Check NEXT_PUBLIC_API_URL
echo $NEXT_PUBLIC_API_URL

# Verify backend is accessible
curl http://localhost:8000/health

# Check CORS settings in backend
# Edit backend/app/core/config.py - CORS_ORIGINS
```

**5. High Memory Usage**

```bash
# Check resource usage
docker stats

# Reduce backend replicas
# Edit docker-compose.prod.yml - backend.deploy.replicas

# Adjust PostgreSQL pool size
# Edit .env - DATABASE_POOL_SIZE
```

**6. Slow Query Performance**

```bash
# Check database indexes
docker-compose exec db psql -U postgres -d iot_sim_db -c "\d+ sims"

# Run VACUUM ANALYZE
docker-compose exec db psql -U postgres -d iot_sim_db -c "VACUUM ANALYZE;"

# Check slow queries
docker-compose exec db psql -U postgres -d iot_sim_db -c "SELECT * FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 10;"
```

---

## Security Best Practices

### 1. Secrets Management

- ✅ Use environment variables for secrets
- ✅ Never commit secrets to git
- ✅ Rotate secrets regularly
- ✅ Use secret management tools (Vault, AWS Secrets Manager)
- ✅ Encrypt secrets at rest

### 2. Network Security

- ✅ Use HTTPS/TLS in production
- ✅ Configure firewall rules
- ✅ Restrict database/Redis access to internal network
- ✅ Use VPC/private networks
- ✅ Enable CORS only for trusted origins

### 3. Application Security

- ✅ Keep dependencies updated
- ✅ Run security scans (Trivy, Bandit, Safety)
- ✅ Use strong JWT secrets
- ✅ Implement rate limiting
- ✅ Validate all inputs
- ✅ Use prepared statements (SQLAlchemy handles this)

### 4. Container Security

- ✅ Use minimal base images
- ✅ Run containers as non-root user
- ✅ Scan images for vulnerabilities
- ✅ Use read-only root filesystem where possible
- ✅ Drop unnecessary capabilities

### 5. Database Security

- ✅ Use strong passwords
- ✅ Enable SSL/TLS connections
- ✅ Regular backups
- ✅ Limit user permissions
- ✅ Enable audit logging

### 6. Monitoring & Incident Response

- ✅ Enable logging for all services
- ✅ Set up alerts for anomalies
- ✅ Regular security audits
- ✅ Have incident response plan
- ✅ Monitor failed login attempts

---

## Backup & Recovery

### Database Backups

**Automated Backups:**
```bash
# Create backup script
#!/bin/bash
BACKUP_DIR=/backups
DATE=$(date +%Y%m%d_%H%M%S)

docker-compose exec -T db pg_dump -U postgres iot_sim_db > $BACKUP_DIR/backup_$DATE.sql

# Keep last 7 days
find $BACKUP_DIR -name "backup_*.sql" -mtime +7 -delete
```

**Manual Backup:**
```bash
# Backup database
docker-compose exec db pg_dump -U postgres iot_sim_db > backup.sql

# Restore database
docker-compose exec -T db psql -U postgres iot_sim_db < backup.sql
```

### Volume Backups

```bash
# Backup volumes
docker run --rm \
  -v iot-sim-platform_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/postgres_data_backup.tar.gz -C /data .

# Restore volumes
docker run --rm \
  -v iot-sim-platform_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/postgres_data_backup.tar.gz -C /data
```

---

## Scaling

### Horizontal Scaling

**Backend:**
```yaml
# Increase replicas
services:
  backend:
    deploy:
      replicas: 5  # Increase from 3
```

**Load Balancer:**
```nginx
# nginx/nginx.conf
upstream backend {
    least_conn;
    server backend:8000 max_fails=3 fail_timeout=30s;
    # Add more backend instances
}
```

### Vertical Scaling

```yaml
# Increase resources
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2.0'      # Increase CPU
          memory: 2G       # Increase memory
```

### Database Scaling

- Use managed PostgreSQL with read replicas
- Implement connection pooling (already configured)
- Enable TimescaleDB compression for time-series data
- Consider sharding for very large datasets

---

## Performance Optimization

### Caching

Redis caching is configured for:
- API responses
- 1NCE API calls
- Database queries

Adjust TTL in backend config:
```python
# backend/app/core/config.py
CACHE_TTL = 300  # seconds
```

### Database Optimization

```sql
-- Create indexes for frequently queried columns
CREATE INDEX idx_sims_iccid ON sims(iccid);
CREATE INDEX idx_usage_timestamp ON usage_records(timestamp DESC);

-- Enable TimescaleDB compression
SELECT add_compression_policy('usage_records', INTERVAL '7 days');
```

### Frontend Optimization

- Next.js automatic code splitting
- Image optimization with next/image
- SWR for data caching
- Production build with minification

---

## Support & Resources

### Documentation

- [Main README](README.md)
- [API Usage Guide](docs/API_USAGE_GUIDE.md)
- [CI/CD Documentation](.github/CICD.md)
- [Monitoring Guide](monitoring/README.md)
- [Backend README](backend/README.md)

### Community

- GitHub Issues
- Contribution Guide
- Security Policy

### Commercial Support

Contact your account manager for enterprise support options.

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.
