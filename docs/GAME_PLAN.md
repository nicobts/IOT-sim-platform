# 🎯 Complete Game Plan: FastAPI Server for 1NCE API Integration

## 📋 Executive Summary

**Project Goal**: Build a production-ready FastAPI server that provides complete integration with the 1NCE IoT platform APIs, enabling programmatic management of SIM cards, connectivity, usage tracking, and order management.

**Tech Stack**: FastAPI, PostgreSQL, Redis, Docker, Pytest, CI/CD

**Timeline**: 6-8 weeks for MVP, 10-12 weeks for production-ready

---

## 🏗️ Phase 1: Foundation & Planning (Week 1)

### 1.1 Requirements Gathering

**Deliverables:**
- [ ] Feature specification document
- [ ] API endpoint mapping (1NCE → FastAPI)
- [ ] Database schema design
- [ ] Architecture diagrams

**Key Decisions:**
- Authentication strategy (token caching, refresh logic)
- Rate limiting approach
- Error handling patterns
- Logging and monitoring strategy

**Activities:**
```
✓ Map all 1NCE API endpoints:
  - Authorization (OAuth 2.0)
  - SIM Management (20+ endpoints)
  - Order Management
  - Product Information
  - Support Management
  - 1NCE OS

✓ Define user stories:
  - As an admin, I need to authenticate with 1NCE
  - As a developer, I need to retrieve all SIMs
  - As a system, I need to track usage automatically
  - etc.
```

### 1.2 Technology Stack Selection

**Core Framework:**
- FastAPI 0.104+ (async support, auto docs)
- Python 3.11+ (performance improvements)

**Database:**
- PostgreSQL 15+ (primary data store)
- Redis 7+ (caching, session management)

**Additional Libraries:**
```python
# Core
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
pydantic-settings>=2.1.0

# HTTP & API
httpx>=0.25.0
tenacity>=8.2.0

# Database
asyncpg>=0.29.0
sqlalchemy[asyncio]>=2.0.0
alembic>=1.12.0

# Caching
redis[hiredis]>=5.0.0

# Security
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6

# Monitoring
prometheus-client>=0.19.0
structlog>=23.2.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
faker>=20.1.0
```

### 1.3 Project Structure Design

```
fastapi-1nce-server/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app initialization
│   ├── config.py               # Configuration management
│   │
│   ├── api/                    # API routes
│   │   ├── __init__.py
│   │   ├── deps.py             # Dependencies (auth, db)
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py         # Authentication endpoints
│   │       ├── sims.py         # SIM management
│   │       ├── orders.py       # Order management
│   │       ├── products.py     # Product info
│   │       └── support.py      # Support tickets
│   │
│   ├── core/                   # Core functionality
│   │   ├── __init__.py
│   │   ├── security.py         # JWT, password hashing
│   │   ├── config.py           # Settings
│   │   └── logging.py          # Structured logging
│   │
│   ├── clients/                # External API clients
│   │   ├── __init__.py
│   │   └── once_client.py      # 1NCE API client
│   │
│   ├── models/                 # Database models
│   │   ├── __init__.py
│   │   ├── sim.py
│   │   ├── usage.py
│   │   ├── order.py
│   │   └── user.py
│   │
│   ├── schemas/                # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── sim.py
│   │   ├── usage.py
│   │   ├── order.py
│   │   └── auth.py
│   │
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── sim_service.py
│   │   ├── usage_service.py
│   │   └── auth_service.py
│   │
│   ├── db/                     # Database
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── session.py
│   │   └── migrations/         # Alembic migrations
│   │
│   └── utils/                  # Utilities
│       ├── __init__.py
│       ├── cache.py            # Redis caching
│       ├── retry.py            # Retry logic
│       └── validators.py       # Custom validators
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── scripts/
│   ├── init_db.py
│   └── seed_data.py
│
├── docker/
│   ├── Dockerfile
│   ├── Dockerfile.dev
│   └── docker-compose.yml
│
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── cd.yml
│
├── alembic.ini
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── .env.example
└── README.md
```

---

## 💻 Phase 2: Core Development (Weeks 2-5)

### 2.1 Week 2: Authentication & 1NCE Client

**Objectives:**
- Implement OAuth 2.0 client credentials flow
- Build robust 1NCE API client
- Set up token caching and refresh

**Implementation Details:**

**1NCE Client (`app/clients/once_client.py`):**
```python
class OnceClient:
    """Async client for 1NCE API with automatic token refresh"""
    
    Features:
    - Automatic bearer token acquisition
    - Token caching in Redis (1hr expiry)
    - Automatic token refresh
    - Retry logic with exponential backoff
    - Request/response logging
    - Rate limiting protection
    - Circuit breaker pattern
```

**Key Features:**
```python
# Token Management
- get_access_token() → Cache in Redis
- refresh_token_if_needed()
- Background token refresh (50min intervals)

# Request Methods
- async def get(endpoint, params)
- async def post(endpoint, data)
- async def put(endpoint, data)
- async def delete(endpoint)

# Error Handling
- OnceAPIError
- OnceAuthError
- OnceRateLimitError
- OnceTimeoutError
```

**Deliverables:**
- [ ] 1NCE client with full auth flow
- [ ] Token caching in Redis
- [ ] Unit tests (90%+ coverage)
- [ ] Integration tests with 1NCE sandbox

### 2.2 Week 3: Database Models & SIM Management

**Database Schema:**

```sql
-- SIM Cards
CREATE TABLE sims (
    id SERIAL PRIMARY KEY,
    iccid VARCHAR(20) UNIQUE NOT NULL,
    imsi VARCHAR(15),
    msisdn VARCHAR(15),
    status VARCHAR(20),
    label VARCHAR(255),
    ip_address INET,
    imei VARCHAR(15),
    organization_id INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_synced_at TIMESTAMP,
    metadata JSONB
);

-- Usage Data (TimescaleDB hypertable)
CREATE TABLE sim_usage (
    id SERIAL PRIMARY KEY,
    sim_id INTEGER REFERENCES sims(id),
    iccid VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    volume_rx BIGINT DEFAULT 0,
    volume_tx BIGINT DEFAULT 0,
    total_volume BIGINT DEFAULT 0,
    sms_mo INTEGER DEFAULT 0,
    sms_mt INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable('sim_usage', 'timestamp');

-- Connectivity Info
CREATE TABLE sim_connectivity (
    id SERIAL PRIMARY KEY,
    sim_id INTEGER REFERENCES sims(id),
    iccid VARCHAR(20) NOT NULL,
    connected BOOLEAN,
    cell_id VARCHAR(50),
    signal_strength INTEGER,
    rat VARCHAR(10),  -- Radio Access Technology
    country_code VARCHAR(3),
    operator_name VARCHAR(100),
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Events
CREATE TABLE sim_events (
    id SERIAL PRIMARY KEY,
    sim_id INTEGER REFERENCES sims(id),
    iccid VARCHAR(20) NOT NULL,
    event_type VARCHAR(50),
    event_data JSONB,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Quotas
CREATE TABLE sim_quotas (
    id SERIAL PRIMARY KEY,
    sim_id INTEGER REFERENCES sims(id),
    iccid VARCHAR(20) NOT NULL,
    quota_type VARCHAR(10),  -- 'data' or 'sms'
    volume BIGINT,
    last_volume_added BIGINT,
    last_status_change_date TIMESTAMP,
    status VARCHAR(20),
    threshold_percentage INTEGER,
    threshold_volume BIGINT,
    auto_reload BOOLEAN,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Users (for API authentication)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- API Keys
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    key_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**FastAPI Endpoints:**
```python
# SIM Management
GET    /api/v1/sims                    # List all SIMs
GET    /api/v1/sims/{iccid}            # Get single SIM
POST   /api/v1/sims                    # Create SIM config
PUT    /api/v1/sims/{iccid}            # Update SIM config
GET    /api/v1/sims/{iccid}/status     # Get SIM status
GET    /api/v1/sims/{iccid}/usage      # Get usage data
GET    /api/v1/sims/{iccid}/connectivity # Get connectivity
POST   /api/v1/sims/{iccid}/reset      # Reset connectivity
GET    /api/v1/sims/{iccid}/events     # Get events
```

**Deliverables:**
- [ ] Complete database schema
- [ ] SQLAlchemy models
- [ ] Alembic migrations
- [ ] SIM CRUD operations
- [ ] Sync service (1NCE → DB)

### 2.3 Week 4: Advanced SIM Features & Quotas

**Endpoints:**
```python
# Quota Management
GET    /api/v1/sims/{iccid}/quota/data  # Data quota
GET    /api/v1/sims/{iccid}/quota/sms   # SMS quota
POST   /api/v1/sims/{iccid}/topup       # Single top-up
POST   /api/v1/sims/topup               # Bulk top-up
POST   /api/v1/sims/auto-topup          # Enable auto top-up

# SMS Management
GET    /api/v1/sims/{iccid}/sms         # List SMS
POST   /api/v1/sims/{iccid}/sms         # Send SMS
GET    /api/v1/sims/{iccid}/sms/{id}    # Get SMS details
DELETE /api/v1/sims/{iccid}/sms/{id}    # Delete SMS

# Limits & Extensions
GET    /api/v1/sims/limits              # Global limits
POST   /api/v1/sims/limits              # Set global limits
GET    /api/v1/sims/{service}/limits    # SIM-specific limits
POST   /api/v1/sims/extension           # Extend SIM

# Transfer
POST   /api/v1/sims/transfer            # Transfer SIMs
```

**Business Logic:**
- Quota monitoring service
- Auto top-up scheduler
- SMS queueing and delivery tracking
- Limit enforcement
- Transfer orchestration

**Deliverables:**
- [ ] Quota management system
- [ ] SMS sending/receiving
- [ ] Auto top-up scheduler
- [ ] Transfer workflow

### 2.4 Week 5: Order & Product Management

**Order Management Endpoints:**
```python
GET    /api/v1/orders                   # List orders
GET    /api/v1/orders/{id}              # Get order details
POST   /api/v1/orders                   # Create order
PUT    /api/v1/orders/{id}              # Update order
```

**Product Information:**
```python
GET    /api/v1/products                 # List products
GET    /api/v1/products/{id}            # Product details
GET    /api/v1/products/pricing         # Pricing info
```

**Support Management:**
```python
GET    /api/v1/support/tickets          # List tickets
POST   /api/v1/support/tickets          # Create ticket
GET    /api/v1/support/tickets/{id}     # Ticket details
PUT    /api/v1/support/tickets/{id}     # Update ticket
```

**Deliverables:**
- [ ] Order management system
- [ ] Product catalog sync
- [ ] Support ticket integration

---

## 🔧 Phase 3: Advanced Features (Week 6)

### 3.1 Background Jobs & Schedulers

**APScheduler Tasks:**
```python
# Scheduled Jobs
- sync_all_sims()           # Every 15 minutes
- sync_usage_data()         # Every hour
- check_quotas()            # Every 30 minutes
- auto_topup_check()        # Every hour
- token_refresh()           # Every 50 minutes
- cleanup_old_data()        # Daily
- generate_reports()        # Daily

# Event-driven Jobs
- on_sim_status_change()
- on_quota_threshold()
- on_connectivity_lost()
```

**Implementation:**
```python
# app/tasks/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('interval', minutes=15)
async def sync_sims():
    # Fetch from 1NCE, update DB
    pass
```

**Deliverables:**
- [ ] Background job scheduler
- [ ] Data sync jobs
- [ ] Monitoring jobs
- [ ] Alert system

### 3.2 Caching Strategy

**Redis Caching Layers:**
```python
# Token Cache
- bearer_token: 1hr TTL
- refresh_lock: 5min TTL

# API Response Cache
- sim_list: 5min TTL
- sim_details:{iccid}: 2min TTL
- usage_data:{iccid}:{date}: 30min TTL
- product_catalog: 1hr TTL

# Rate Limiting
- rate_limit:{endpoint}:{user}: 1min sliding window
```

**Cache Decorator:**
```python
@cache(ttl=300, key_prefix="sims")
async def get_all_sims():
    pass
```

**Deliverables:**
- [ ] Redis caching layer
- [ ] Cache invalidation strategy
- [ ] Cache warming on startup

### 3.3 Monitoring & Observability

**Prometheus Metrics:**
```python
# API Metrics
- http_requests_total
- http_request_duration_seconds
- http_requests_in_progress

# 1NCE API Metrics
- once_api_requests_total
- once_api_errors_total
- once_api_latency_seconds
- token_refresh_count

# Business Metrics
- active_sims_count
- daily_data_usage_bytes
- quota_threshold_alerts
- sms_sent_total
```

**Logging:**
```python
# Structured logging with structlog
logger.info("sim_synced", 
    iccid=iccid, 
    status=status,
    duration_ms=duration)
```

**Health Checks:**
```python
GET /health          # Basic health
GET /health/ready    # Readiness (DB, Redis, 1NCE API)
GET /health/live     # Liveness
GET /metrics         # Prometheus metrics
```

**Deliverables:**
- [ ] Prometheus metrics
- [ ] Structured logging
- [ ] Health check endpoints
- [ ] Grafana dashboards

---

## 🧪 Phase 4: Testing (Week 7)

### 4.1 Test Strategy

**Unit Tests (70% coverage minimum):**
```python
tests/unit/
├── test_once_client.py      # Mock 1NCE API
├── test_auth_service.py     # Auth logic
├── test_sim_service.py      # Business logic
├── test_cache.py            # Redis caching
└── test_validators.py       # Data validation
```

**Integration Tests:**
```python
tests/integration/
├── test_database.py         # DB operations
├── test_once_api.py         # Real API calls (sandbox)
├── test_cache_flow.py       # Cache integration
└── test_background_jobs.py  # Scheduler tasks
```

**E2E Tests:**
```python
tests/e2e/
├── test_sim_workflow.py     # Full SIM lifecycle
├── test_usage_tracking.py   # Usage collection
└── test_quota_management.py # Quota + top-up
```

**Load Testing:**
```python
# Using Locust
- 100 concurrent users
- 1000 requests/minute
- Measure: response time, error rate, throughput
```

**Deliverables:**
- [ ] Unit tests (80%+ coverage)
- [ ] Integration tests
- [ ] E2E test suite
- [ ] Load test results
- [ ] Test documentation

### 4.2 CI/CD Pipeline

**GitHub Actions Workflow:**
```yaml
# .github/workflows/ci.yml
name: CI/CD

on: [push, pull_request]

jobs:
  test:
    - Run linters (ruff, black, mypy)
    - Run unit tests
    - Run integration tests
    - Upload coverage to Codecov
    
  build:
    - Build Docker image
    - Scan for vulnerabilities (Trivy)
    - Push to registry
    
  deploy-staging:
    - Deploy to staging environment
    - Run E2E tests
    - Smoke tests
    
  deploy-production:
    - Manual approval
    - Blue-green deployment
    - Health checks
    - Rollback on failure
```

**Deliverables:**
- [ ] CI/CD pipeline
- [ ] Automated testing
- [ ] Docker builds
- [ ] Deployment automation

---

## 🚀 Phase 5: Deployment (Week 8)

### 5.1 Containerization

**Docker Setup:**
```dockerfile
# Dockerfile
FROM python:3.11-slim

# Multi-stage build
# Stage 1: Builder
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
COPY ./app /app
ENV PATH=/root/.local/bin:$PATH
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
```

**Docker Compose (Development):**
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/once
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
      
  db:
    image: timescale/timescaledb:latest-pg15
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: once
    volumes:
      - postgres_data:/var/lib/postgresql/data
      
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
      
  worker:
    build: .
    command: python -m app.tasks.worker
    depends_on:
      - redis
      - db
```

### 5.2 Infrastructure as Code

**Terraform (AWS Example):**
```hcl
# AWS ECS Fargate deployment
module "ecs_cluster" {
  source = "terraform-aws-modules/ecs/aws"
  
  cluster_name = "once-api-cluster"
  
  fargate_capacity_providers = {
    FARGATE = {
      default_capacity_provider_strategy = {
        weight = 100
      }
    }
  }
}

# RDS PostgreSQL with TimescaleDB
module "db" {
  source = "terraform-aws-modules/rds/aws"
  
  identifier = "once-api-db"
  engine     = "postgres"
  engine_version = "15.3"
  instance_class = "db.t3.medium"
}

# ElastiCache Redis
module "redis" {
  source = "terraform-aws-modules/elasticache/aws"
  
  cluster_id = "once-api-cache"
  engine     = "redis"
  node_type  = "cache.t3.micro"
}

# Application Load Balancer
module "alb" {
  source = "terraform-aws-modules/alb/aws"
  
  name = "once-api-alb"
  load_balancer_type = "application"
  
  vpc_id = module.vpc.vpc_id
  subnets = module.vpc.public_subnets
}
```

**Kubernetes (Alternative):**
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: once-api
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
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secrets
              key: url
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
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
```

### 5.3 Production Deployment Checklist

**Security:**
- [ ] HTTPS/TLS enabled
- [ ] API key authentication
- [ ] Rate limiting configured
- [ ] CORS policies set
- [ ] Security headers enabled
- [ ] Secrets in vault (AWS Secrets Manager/HashiCorp Vault)
- [ ] Database encrypted at rest
- [ ] Network security groups configured

**Performance:**
- [ ] Database indexes optimized
- [ ] Connection pooling configured
- [ ] Redis caching enabled
- [ ] CDN for static assets (if any)
- [ ] Gzip compression enabled
- [ ] Query optimization done

**Reliability:**
- [ ] Auto-scaling configured
- [ ] Health checks enabled
- [ ] Backup strategy implemented
- [ ] Disaster recovery plan
- [ ] Blue-green deployment setup
- [ ] Circuit breakers configured
- [ ] Retry logic with backoff

**Monitoring:**
- [ ] APM tool integrated (DataDog/New Relic)
- [ ] Log aggregation (CloudWatch/ELK)
- [ ] Error tracking (Sentry)
- [ ] Uptime monitoring (Pingdom/UptimeRobot)
- [ ] Alerts configured (PagerDuty)
- [ ] Grafana dashboards

**Documentation:**
- [ ] API documentation (Swagger/ReDoc)
- [ ] Deployment runbook
- [ ] Incident response plan
- [ ] Architecture diagrams
- [ ] Developer onboarding guide

---

## 📊 Phase 6: Post-Launch (Week 9+)

### 6.1 Monitoring & Maintenance

**Week 1 Post-Launch:**
- Monitor error rates, latency, throughput
- Review logs for anomalies
- Collect user feedback
- Performance optimization

**Ongoing:**
- Monthly security updates
- Quarterly dependency updates
- Feature enhancements based on usage
- Cost optimization

### 6.2 Feature Roadmap

**Phase 7 - Analytics Dashboard (Weeks 10-12):**
- React/Vue.js web dashboard
- Real-time SIM status visualization
- Usage analytics and charts
- Alert configuration UI
- Bulk operations interface

**Phase 8 - Advanced Features (Weeks 13-16):**
- WebSocket support for real-time updates
- GraphQL API option
- Machine learning for usage prediction
- Anomaly detection
- Cost optimization recommendations

---

## 📈 Success Metrics

**Technical KPIs:**
- API response time: < 200ms (p95)
- Uptime: 99.9%
- Test coverage: > 80%
- Code quality: A grade (SonarQube)
- Build time: < 5 minutes

**Business KPIs:**
- API requests handled: 10,000+/day
- Data sync latency: < 5 minutes
- Error rate: < 0.1%
- User satisfaction: > 4.5/5

---

## 🛠️ Development Best Practices

### Code Quality
```python
# Use type hints everywhere
async def get_sim(iccid: str) -> SimSchema:
    pass

# Dependency injection
async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session

# Proper error handling
try:
    sim = await once_client.get_sim(iccid)
except OnceAPIError as e:
    logger.error("Failed to fetch SIM", iccid=iccid, error=str(e))
    raise HTTPException(status_code=502, detail="Upstream API error")
```

### Git Workflow
- Feature branches from `develop`
- PR reviews required (2 approvers)
- Squash and merge to `develop`
- Release branches to `main`
- Semantic versioning (v1.0.0)

### Documentation
- Docstrings for all public functions
- API endpoints documented in OpenAPI
- Architecture decisions recorded (ADRs)
- Runbooks for operations

---

## 💰 Estimated Costs (Monthly)

**Infrastructure (AWS):**
- ECS Fargate (2 tasks): $50
- RDS PostgreSQL (db.t3.medium): $70
- ElastiCache Redis (cache.t3.micro): $15
- ALB: $20
- Data transfer: $20
- CloudWatch: $10
**Total: ~$185/month**

**SaaS Tools:**
- Sentry (10K events): $26
- DataDog (1 host): $15
**Total: ~$40/month**

**Grand Total: ~$225/month**

---

## 🎓 Learning Resources

**FastAPI:**
- Official docs: https://fastapi.tiangolo.com
- Full Stack FastAPI Template: https://github.com/tiangolo/full-stack-fastapi-template

**1NCE API:**
- API Documentation (use 1NCE MCP tool)
- OAuth 2.0 Client Credentials: https://oauth.net/2/grant-types/client-credentials/

**PostgreSQL + TimescaleDB:**
- TimescaleDB docs: https://docs.timescale.com

**Testing:**
- pytest-asyncio: https://pytest-asyncio.readthedocs.io

---

## 🚦 Next Steps

Ready to start? Here's your first sprint:

**Sprint 1 (Week 1):**
1. ✅ Set up project structure
2. ✅ Configure development environment (Docker Compose)
3. ✅ Implement 1NCE OAuth client
4. ✅ Create database models
5. ✅ Build first endpoint: `GET /api/v1/sims`

See `USER_STORIES.md` for detailed user stories and acceptance criteria.
