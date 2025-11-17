# Deployment Guide

This guide covers deploying the FastAPI 1NCE Server to various production environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [AWS ECS Deployment](#aws-ecs-deployment)
- [Cloud Run Deployment](#cloud-run-deployment)
- [Post-Deployment](#post-deployment)

---

## Prerequisites

### Required

- Docker 20.10+
- Docker Compose 2.0+
- 1NCE API credentials
- PostgreSQL 15+ (or managed service)
- Redis 7+ (or managed service)

### Optional

- Terraform 1.0+ (for IaC)
- Kubernetes 1.24+ (for K8s deployment)
- AWS CLI (for AWS deployment)
- Google Cloud SDK (for GCP deployment)

---

## Environment Configuration

### 1. Create Production Environment File

```bash
cp .env.example .env.production
```

### 2. Configure Environment Variables

**Critical Settings:**

```bash
# Environment
ENV=production
DEBUG=false

# 1NCE API
ONCE_USERNAME=your_production_username
ONCE_PASSWORD=your_production_password
ONCE_API_BASE_URL=https://api.1nce.com

# Database (use managed service in production)
DATABASE_URL=postgresql://user:password@db-host:5432/onceapi
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis (use managed service in production)
REDIS_URL=redis://redis-host:6379/0
REDIS_PASSWORD=your_redis_password

# Security
SECRET_KEY=<generate-with: openssl rand -hex 32>
API_KEY_PREFIX=sk_live_

# CORS (restrict to your domains)
ALLOWED_ORIGINS=["https://yourdomain.com"]

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=1000

# Monitoring
SENTRY_DSN=https://your-sentry-dsn
PROMETHEUS_ENABLED=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

---

## Docker Deployment

### Simple Docker Run

```bash
# Build image
docker build -t once-api:latest .

# Run container
docker run -d \
  --name once-api \
  -p 8000:8000 \
  --env-file .env.production \
  --restart unless-stopped \
  once-api:latest
```

### Docker Compose (Production)

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  api:
    image: once-api:latest
    build:
      context: .
      dockerfile: docker/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - ENV=production
    env_file:
      - .env.production
    depends_on:
      - db
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    
  db:
    image: timescale/timescaledb:latest-pg15
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: onceapi
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    
  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

**Deploy:**

```bash
docker-compose -f docker-compose.prod.yml up -d
```

---

## Kubernetes Deployment

### 1. Create Namespace

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: once-api
```

### 2. Create Secrets

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: once-api-secrets
  namespace: once-api
type: Opaque
stringData:
  DATABASE_URL: postgresql://user:pass@db:5432/onceapi
  REDIS_URL: redis://:password@redis:6379/0
  SECRET_KEY: your-secret-key
  ONCE_USERNAME: your-username
  ONCE_PASSWORD: your-password
```

### 3. Create ConfigMap

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: once-api-config
  namespace: once-api
data:
  ENV: "production"
  LOG_LEVEL: "INFO"
  ONCE_API_BASE_URL: "https://api.1nce.com"
```

### 4. Create Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: once-api
  namespace: once-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: once-api
  template:
    metadata:
      labels:
        app: once-api
    spec:
      containers:
      - name: api
        image: once-api:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: once-api-config
        - secretRef:
            name: once-api-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health/live
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

### 5. Create Service

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: once-api
  namespace: once-api
spec:
  type: LoadBalancer
  selector:
    app: once-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
```

### 6. Create HPA (Auto-scaling)

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: once-api-hpa
  namespace: once-api
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: once-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Deploy to Kubernetes

```bash
# Apply manifests
kubectl apply -f k8s/

# Check deployment
kubectl get pods -n once-api
kubectl get services -n once-api

# View logs
kubectl logs -f deployment/once-api -n once-api

# Scale manually
kubectl scale deployment once-api --replicas=5 -n once-api
```

---

## AWS ECS Deployment

### Using Terraform

Create `terraform/main.tf`:

```hcl
terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# VPC
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  
  name = "once-api-vpc"
  cidr = "10.0.0.0/16"
  
  azs             = ["us-east-1a", "us-east-1b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]
  
  enable_nat_gateway = true
  enable_dns_hostnames = true
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "once-api-cluster"
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# Task Definition
resource "aws_ecs_task_definition" "api" {
  family                   = "once-api"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  
  container_definitions = jsonencode([
    {
      name  = "api"
      image = "${aws_ecr_repository.api.repository_url}:latest"
      
      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]
      
      environment = [
        {
          name  = "ENV"
          value = "production"
        }
      ]
      
      secrets = [
        {
          name      = "DATABASE_URL"
          valueFrom = aws_secretsmanager_secret.db_url.arn
        },
        {
          name      = "REDIS_URL"
          valueFrom = aws_secretsmanager_secret.redis_url.arn
        }
      ]
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/once-api"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}

# ECS Service
resource "aws_ecs_service" "api" {
  name            = "once-api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 2
  launch_type     = "FARGATE"
  
  network_configuration {
    subnets         = module.vpc.private_subnets
    security_groups = [aws_security_group.api.id]
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 8000
  }
}

# Application Load Balancer
resource "aws_lb" "api" {
  name               = "once-api-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = module.vpc.public_subnets
}

# RDS PostgreSQL
resource "aws_db_instance" "postgres" {
  identifier        = "once-api-db"
  engine            = "postgres"
  engine_version    = "15.3"
  instance_class    = "db.t3.medium"
  allocated_storage = 100
  
  db_name  = "onceapi"
  username = var.db_username
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.db.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "mon:04:00-mon:05:00"
  
  enabled_cloudwatch_logs_exports = ["postgresql"]
}

# ElastiCache Redis
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "once-api-redis"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
  
  subnet_group_name  = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.redis.id]
}
```

**Deploy:**

```bash
cd terraform

# Initialize
terraform init

# Plan
terraform plan -var-file=production.tfvars

# Apply
terraform apply -var-file=production.tfvars
```

---

## Cloud Run Deployment (Google Cloud)

### 1. Build and Push Image

```bash
# Configure Docker for GCR
gcloud auth configure-docker

# Build image
docker build -t gcr.io/PROJECT_ID/once-api:latest .

# Push to GCR
docker push gcr.io/PROJECT_ID/once-api:latest
```

### 2. Deploy to Cloud Run

```bash
gcloud run deploy once-api \
  --image gcr.io/PROJECT_ID/once-api:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ENV=production,LOG_LEVEL=INFO \
  --set-secrets DATABASE_URL=db-url:latest,REDIS_URL=redis-url:latest \
  --min-instances 1 \
  --max-instances 10 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300
```

---

## Post-Deployment

### 1. Database Migrations

```bash
# Run migrations
docker exec -it once-api alembic upgrade head

# Or via kubectl
kubectl exec -it deployment/once-api -n once-api -- alembic upgrade head
```

### 2. Create Admin User

```bash
docker exec -it once-api python scripts/create_admin.py \
  --username admin \
  --email admin@example.com \
  --password SecurePassword123
```

### 3. Health Check

```bash
# Check health
curl https://your-domain.com/health

# Check readiness
curl https://your-domain.com/health/ready
```

### 4. Verify API

```bash
# Get API docs
curl https://your-domain.com/docs

# Test authentication
curl -X POST https://your-domain.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "SecurePassword123"}'
```

### 5. Set Up Monitoring

**Prometheus:**
```bash
# Add Prometheus scrape config
scrape_configs:
  - job_name: 'once-api'
    static_configs:
      - targets: ['api:8000']
```

**Grafana Dashboards:**
- Import pre-built dashboards
- Configure alerts
- Set up notification channels

### 6. Configure Backups

**Database:**
```bash
# AWS RDS: Automated backups enabled
# Manual snapshot
aws rds create-db-snapshot \
  --db-instance-identifier once-api-db \
  --db-snapshot-identifier once-api-backup-$(date +%Y%m%d)
```

**Redis:**
```bash
# ElastiCache: Enable automatic backups
# Manual backup
aws elasticache create-snapshot \
  --cache-cluster-id once-api-redis \
  --snapshot-name redis-backup-$(date +%Y%m%d)
```

### 7. SSL/TLS Configuration

**Let's Encrypt (Nginx):**
```bash
# Install certbot
apt-get install certbot python3-certbot-nginx

# Obtain certificate
certbot --nginx -d api.yourdomain.com

# Auto-renewal
certbot renew --dry-run
```

---

## Scaling Considerations

### Horizontal Scaling

**Docker Swarm:**
```bash
docker service scale once-api=5
```

**Kubernetes:**
```bash
kubectl scale deployment once-api --replicas=5 -n once-api
```

**AWS ECS:**
```bash
aws ecs update-service \
  --cluster once-api-cluster \
  --service once-api \
  --desired-count 5
```

### Vertical Scaling

Update resource limits in deployment manifests and redeploy.

---

## Troubleshooting

### Common Issues

**1. Database Connection Failed**
```bash
# Check database connectivity
docker exec -it once-api python -c "from app.db.session import engine; print(engine.connect())"
```

**2. Redis Connection Failed**
```bash
# Test Redis connection
docker exec -it once-api python -c "import redis; r = redis.from_url('redis://...'); print(r.ping())"
```

**3. 1NCE API Authentication Failed**
```bash
# Test credentials
curl -u username:password https://api.1nce.com/oauth/token
```

### Logs

**Docker:**
```bash
docker logs once-api
```

**Kubernetes:**
```bash
kubectl logs -f deployment/once-api -n once-api
```

**AWS ECS:**
```bash
aws logs tail /ecs/once-api --follow
```

---

## Security Checklist

- [ ] HTTPS enabled
- [ ] Secrets stored in vault
- [ ] Database encrypted
- [ ] API keys rotated regularly
- [ ] Rate limiting configured
- [ ] CORS properly set
- [ ] Security headers enabled
- [ ] Regular security updates
- [ ] Audit logging enabled
- [ ] Network security groups configured

---

## Performance Optimization

### Database

- Enable connection pooling
- Add appropriate indexes
- Use read replicas
- Enable query caching

### Redis

- Configure eviction policy
- Set appropriate TTLs
- Monitor memory usage
- Use Redis Cluster for scale

### Application

- Enable response compression
- Use CDN for static assets
- Implement request caching
- Optimize database queries

---

## Rollback Procedure

### Docker

```bash
# Rollback to previous version
docker service update --rollback once-api
```

### Kubernetes

```bash
# Rollback deployment
kubectl rollout undo deployment/once-api -n once-api

# Rollback to specific revision
kubectl rollout undo deployment/once-api --to-revision=2 -n once-api
```

### Database

```bash
# Rollback migration
alembic downgrade -1
```

---

## Cost Optimization

**AWS:**
- Use Spot instances for non-critical workloads
- Right-size RDS instances
- Enable RDS reserved instances
- Use S3 lifecycle policies for backups

**GCP:**
- Use preemptible VMs
- Optimize Cloud SQL instance size
- Use committed use discounts

---

For additional help, see:
- [Architecture Documentation](ARCHITECTURE.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Monitoring Guide](MONITORING.md)
