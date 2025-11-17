# Technical Architecture - FastAPI 1NCE Server

## System Overview

This document describes the technical architecture for the FastAPI-based 1NCE IoT management platform.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Applications                      │
│  (Web Dashboard, Mobile Apps, External Services, CLI Tools)     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTPS / API Requests
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      Load Balancer (ALB)                         │
│                    SSL Termination / WAF                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
┌───────────────▼──────────┐   ┌─────────▼────────────────┐
│   FastAPI Instance 1     │   │   FastAPI Instance N     │
│   (Stateless Service)    │   │   (Horizontal Scaling)   │
└───────────────┬──────────┘   └─────────┬────────────────┘
                │                         │
                └────────────┬────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼────────┐  ┌────────▼────────┐  ┌───────▼────────┐
│  PostgreSQL    │  │     Redis       │  │  1NCE API      │
│  + TimescaleDB │  │   (Cache +      │  │  (External)    │
│  (Time-series) │  │   Token Store)  │  │                │
└────────────────┘  └─────────────────┘  └────────────────┘
        │
┌───────▼────────┐
│  Background    │
│  Workers       │
│  (APScheduler) │
└────────────────┘
        │
┌───────▼────────┐
│  Monitoring    │
│  (Prometheus + │
│   Grafana)     │
└────────────────┘
```

## Component Details

### 1. API Layer (FastAPI)

**Technology:** FastAPI 0.104+, Python 3.11+

**Responsibilities:**
- HTTP request handling
- Request validation (Pydantic)
- Authentication & authorization
- Rate limiting
- API documentation (OpenAPI)
- Response serialization

**Design Patterns:**
- Dependency Injection for shared resources
- Repository pattern for data access
- Service layer for business logic
- Middleware for cross-cutting concerns

**Key Components:**

```python
app/
├── main.py              # Application entry point
├── api/
│   ├── deps.py          # Shared dependencies
│   └── v1/              # API version 1
│       ├── auth.py      # Authentication endpoints
│       ├── sims.py      # SIM management
│       └── ...
├── core/
│   ├── config.py        # Configuration management
│   ├── security.py      # JWT, API key validation
│   └── middleware.py    # Custom middleware
```

**API Versioning Strategy:**
- URL-based versioning: `/api/v1/...`
- Major version in URL path
- Maintain backward compatibility within major version
- Deprecation notices 6 months before removal

---

### 2. Database Layer

#### PostgreSQL + TimescaleDB

**Technology:** PostgreSQL 15+ with TimescaleDB extension

**Purpose:**
- Primary data store for SIM cards, users, API keys
- Time-series data for usage metrics (TimescaleDB)
- Event logging and audit trails

**Schema Design:**

**Regular Tables (PostgreSQL):**
- `users` - API users
- `api_keys` - Authentication tokens
- `sims` - SIM card master data
- `sim_quotas` - Current quota state
- `orders` - Order history
- `products` - Product catalog

**Hypertables (TimescaleDB):**
- `sim_usage` - Daily usage metrics (partitioned by time)
- `sim_connectivity` - Connection history
- `sim_events` - Event stream

**Indexing Strategy:**
```sql
-- SIM lookups
CREATE INDEX idx_sims_iccid ON sims(iccid);
CREATE INDEX idx_sims_status ON sims(status);
CREATE INDEX idx_sims_org ON sims(organization_id);

-- Time-series queries
CREATE INDEX idx_usage_iccid_time ON sim_usage(iccid, timestamp DESC);
CREATE INDEX idx_connectivity_iccid_time ON sim_connectivity(iccid, timestamp DESC);

-- API key lookups
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
```

**Data Retention:**
- Usage data: 2 years (then compress/archive)
- Events: 1 year
- Connectivity logs: 6 months
- Audit logs: 7 years (compliance)

**Backup Strategy:**
- Automated daily backups
- Point-in-time recovery enabled
- Weekly full backups
- Monthly archive to S3/Glacier

---

### 3. Caching Layer (Redis)

**Technology:** Redis 7+

**Use Cases:**

1. **Authentication Token Cache**
```python
Key: f"1nce:token:bearer"
TTL: 3600 seconds (1 hour)
Value: {
    "access_token": "...",
    "expires_at": "2024-11-16T11:30:00Z"
}
```

2. **API Response Cache**
```python
# SIM list cache
Key: f"sims:list:{page}:{page_size}:{filters_hash}"
TTL: 300 seconds (5 minutes)

# SIM details cache
Key: f"sim:details:{iccid}"
TTL: 120 seconds (2 minutes)

# Usage data cache
Key: f"usage:{iccid}:{start_date}:{end_date}"
TTL: 1800 seconds (30 minutes)
```

3. **Rate Limiting**
```python
# Sliding window rate limit
Key: f"ratelimit:{api_key}:{endpoint}:{minute}"
TTL: 60 seconds
Value: request_count
```

4. **Distributed Locks**
```python
# Prevent concurrent token refresh
Key: f"lock:token_refresh"
TTL: 300 seconds
```

**Cache Invalidation Strategy:**
- Write-through: Update DB first, then invalidate cache
- TTL-based expiration for most data
- Event-based invalidation for critical updates
- Cache warming on startup for hot data

**High Availability:**
- Redis Sentinel for automatic failover
- Or Redis Cluster for horizontal scaling
- Persistence: RDB + AOF for durability

---

### 4. 1NCE API Client

**Design:** Singleton client with connection pooling

**Features:**

1. **Authentication Management**
```python
class OnceClient:
    async def get_access_token(self) -> str:
        """
        Get cached token or refresh if expired
        Uses Redis for token storage
        Implements lock to prevent concurrent refresh
        """
```

2. **Request Handling**
```python
async def _request(self, method, endpoint, **kwargs):
    """
    - Automatic retry with exponential backoff
    - Circuit breaker pattern
    - Request/response logging
    - Error handling & custom exceptions
    """
```

3. **Error Handling**
```python
class OnceAPIError(Exception): pass
class OnceAuthError(OnceAPIError): pass
class OnceRateLimitError(OnceAPIError): pass
class OnceTimeoutError(OnceAPIError): pass
class OnceNotFoundError(OnceAPIError): pass
```

4. **Retry Logic**
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.HTTPError, OnceTimeoutError))
)
```

**Rate Limiting:**
- Respect 1NCE API rate limits
- Implement client-side rate limiting
- Queue requests if needed
- Monitor rate limit headers

**Monitoring:**
- Track request count, latency, error rate
- Alert on high error rates
- Log all API interactions

---

### 5. Background Workers

**Technology:** APScheduler (AsyncIOScheduler)

**Scheduled Jobs:**

```python
# Data Synchronization
@scheduler.scheduled_job('interval', minutes=15)
async def sync_sims():
    """Sync SIM list from 1NCE API"""

@scheduler.scheduled_job('interval', hours=1)
async def sync_usage_data():
    """Fetch usage data for all active SIMs"""

# Monitoring
@scheduler.scheduled_job('interval', minutes=30)
async def check_quotas():
    """Check SIM quotas and send alerts"""

@scheduler.scheduled_job('interval', hours=1)
async def check_auto_topup():
    """Process auto top-up requests"""

# Maintenance
@scheduler.scheduled_job('cron', hour=2)
async def cleanup_old_data():
    """Archive/delete old data"""

@scheduler.scheduled_job('interval', minutes=50)
async def refresh_token():
    """Proactive token refresh"""
```

**Job Management:**
- Job status tracking in database
- Failed job retry mechanism
- Job execution logging
- Alert on job failures
- Job execution metrics

**Concurrency:**
- Use async/await for I/O operations
- Limit concurrent API calls
- Queue-based processing for bulk operations

---

### 6. Authentication & Security

#### API Authentication

**Methods:**

1. **API Key (Primary)**
```http
GET /api/v1/sims
X-API-Key: sk_live_abc123...
```

2. **JWT Token (Optional)**
```http
GET /api/v1/sims
Authorization: Bearer eyJhbGc...
```

**API Key Management:**
```python
# Generation
import secrets
api_key = f"sk_live_{secrets.token_urlsafe(32)}"

# Storage (hashed)
from passlib.hash import bcrypt
hashed = bcrypt.hash(api_key)
```

**Security Headers:**
```python
# Middleware adds security headers
headers = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000",
    "Content-Security-Policy": "default-src 'self'"
}
```

#### Authorization

**Role-Based Access Control (RBAC):**

```python
class Role(Enum):
    ADMIN = "admin"
    USER = "user"
    READONLY = "readonly"

class Permission(Enum):
    READ_SIMS = "read:sims"
    WRITE_SIMS = "write:sims"
    MANAGE_QUOTAS = "manage:quotas"
    SEND_SMS = "send:sms"
    MANAGE_ORDERS = "manage:orders"

# Endpoint protection
@router.get("/sims")
@require_permissions([Permission.READ_SIMS])
async def list_sims():
    ...
```

---

### 7. Monitoring & Observability

#### Logging

**Structured Logging (structlog):**

```python
logger.info(
    "sim_created",
    iccid=iccid,
    status=status,
    user_id=user_id,
    duration_ms=duration
)
```

**Log Levels:**
- DEBUG: Detailed debugging info
- INFO: General informational messages
- WARNING: Warning messages
- ERROR: Error messages
- CRITICAL: Critical failures

**Log Aggregation:**
- CloudWatch Logs (AWS)
- ELK Stack (self-hosted)
- Structured JSON format for parsing

#### Metrics (Prometheus)

**Application Metrics:**
```python
from prometheus_client import Counter, Histogram, Gauge

# HTTP metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

# Business metrics
active_sims = Gauge('active_sims_total', 'Number of active SIMs')
daily_data_usage = Counter('daily_data_usage_bytes', 'Daily data usage')

# 1NCE API metrics
once_api_calls = Counter(
    'once_api_calls_total',
    'Total 1NCE API calls',
    ['endpoint', 'status']
)
```

**Grafana Dashboards:**
- API Performance (latency, throughput, error rate)
- 1NCE API Health (success rate, latency)
- Business Metrics (active SIMs, usage trends)
- System Resources (CPU, memory, DB connections)

#### Tracing (Optional - Jaeger/Zipkin)

- Distributed tracing for request flows
- Identify bottlenecks
- Debug complex transactions

#### Error Tracking (Sentry)

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="...",
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
    environment="production"
)
```

---

### 8. Deployment Architecture

#### Containerization (Docker)

**Multi-stage Dockerfile:**
```dockerfile
# Builder stage
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
COPY ./app /app
ENV PATH=/root/.local/bin:$PATH
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Orchestration

**Option 1: AWS ECS Fargate**
- Serverless container management
- Auto-scaling based on CPU/memory
- Service discovery
- Load balancing (ALB)

**Option 2: Kubernetes**
- Self-managed or managed (EKS, GKE, AKS)
- Horizontal Pod Autoscaler
- Ingress controller for routing
- ConfigMaps & Secrets for configuration

#### Infrastructure as Code

**Terraform Example:**
```hcl
module "ecs_fargate" {
  source = "terraform-aws-modules/ecs/aws"
  
  cluster_name = "once-api"
  
  services = {
    once-api = {
      desired_count = 2
      
      container_definitions = {
        api = {
          image = "once-api:latest"
          port_mappings = [
            { containerPort = 8000 }
          ]
          environment = [
            { name = "ENV", value = "production" }
          ]
        }
      }
    }
  }
}
```

---

### 9. Data Flow Diagrams

#### SIM List Request Flow

```
Client Request
     │
     ▼
API Gateway (Auth)
     │
     ▼
Check Cache (Redis)
     │
     ├─ Hit ──────────────┐
     │                    │
     └─ Miss              │
        │                 │
        ▼                 │
   Query Database         │
        │                 │
        ▼                 │
   Cache Result ──────────┤
        │                 │
        └─────────────────┘
                │
                ▼
         Return Response
```

#### Usage Data Sync Flow

```
Scheduler Trigger
     │
     ▼
Get Active SIMs (Database)
     │
     ▼
For each SIM:
     │
     ├─ Get Last Sync Timestamp
     │
     ├─ Call 1NCE API (with token)
     │      │
     │      ├─ Success ──────────┐
     │      │                    │
     │      └─ Error             │
     │         │                 │
     │         ├─ Retry (3x)     │
     │         └─ Log Error      │
     │                           │
     └────────────────────────────┘
                │
                ▼
         Store in TimescaleDB
                │
                ▼
         Update Last Sync
                │
                ▼
         Invalidate Cache
```

---

## Performance Considerations

### Database Optimization

1. **Connection Pooling**
```python
# SQLAlchemy async engine
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True
)
```

2. **Query Optimization**
- Use proper indexes
- Avoid N+1 queries (use joins/eager loading)
- Pagination for large result sets
- Database query explain analysis

3. **TimescaleDB Optimization**
- Compression for old data
- Continuous aggregates for analytics
- Retention policies for data cleanup

### Caching Strategy

**Cache Hierarchy:**
1. Application-level cache (in-memory)
2. Redis cache (distributed)
3. Database query results

**Cache Patterns:**
- Cache-aside (lazy loading)
- Write-through for critical data
- TTL-based expiration
- Event-based invalidation

### API Performance

1. **Async/Await**
```python
# Use async for I/O operations
async def get_sim(iccid: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"/sims/{iccid}")
```

2. **Connection Pooling**
```python
# Reuse HTTP connections
client = httpx.AsyncClient(
    limits=httpx.Limits(
        max_connections=100,
        max_keepalive_connections=20
    )
)
```

3. **Request Batching**
- Batch 1NCE API calls when possible
- Bulk database operations

---

## Security Best Practices

### Data Protection

1. **Encryption at Rest**
- Database encryption (AWS RDS encryption)
- Encrypted backups

2. **Encryption in Transit**
- HTTPS/TLS only
- TLS 1.2+ minimum

3. **Secrets Management**
- AWS Secrets Manager / HashiCorp Vault
- Never commit secrets to Git
- Rotate credentials regularly

### Input Validation

```python
# Pydantic models for validation
class SIMCreate(BaseModel):
    iccid: str = Field(..., regex=r'^\d{19,20}$')
    label: Optional[str] = Field(None, max_length=255)
```

### Rate Limiting

```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/v1/sims")
@limiter.limit("100/minute")
async def list_sims():
    ...
```

### Audit Logging

- Log all destructive operations
- Track who did what and when
- Immutable audit log
- Compliance with data protection regulations

---

## Scalability Strategy

### Horizontal Scaling

- Stateless API servers
- Load balancer distributes traffic
- Auto-scaling based on metrics

### Database Scaling

1. **Read Replicas**
- Route read queries to replicas
- Reduce load on primary

2. **Sharding (Future)**
- Shard by organization_id
- Partition usage data by time

### Caching Scaling

- Redis Cluster for horizontal scaling
- Consistent hashing for distribution

---

## Disaster Recovery

### Backup Strategy

1. **Database Backups**
- Automated daily backups
- Point-in-time recovery (PITR)
- Cross-region replication

2. **Configuration Backups**
- Infrastructure as Code in Git
- Environment variables in Secrets Manager

### Recovery Procedures

1. **Database Recovery**
- Restore from latest backup
- Replay WAL logs for PITR

2. **Service Recovery**
- Deploy from last known good image
- Rollback deployment if needed

### RTO/RPO Targets

- **RTO** (Recovery Time Objective): < 1 hour
- **RPO** (Recovery Point Objective): < 15 minutes

---

## Technology Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| API Framework | FastAPI 0.104+ | REST API server |
| Language | Python 3.11+ | Application code |
| Database | PostgreSQL 15+ | Primary data store |
| Time-Series DB | TimescaleDB | Usage metrics |
| Cache | Redis 7+ | Token cache, API cache |
| Background Jobs | APScheduler | Scheduled tasks |
| HTTP Client | HTTPX | Async 1NCE API calls |
| ORM | SQLAlchemy 2.0+ | Database abstraction |
| Validation | Pydantic 2.5+ | Data validation |
| Authentication | JWT / API Keys | User authentication |
| Logging | structlog | Structured logging |
| Metrics | Prometheus | Metrics collection |
| Visualization | Grafana | Dashboards |
| Error Tracking | Sentry | Error monitoring |
| Containerization | Docker | Application packaging |
| Orchestration | ECS/Kubernetes | Container management |
| IaC | Terraform | Infrastructure provisioning |
| CI/CD | GitHub Actions | Automation pipeline |

---

## Next Steps

1. Review architecture with stakeholders
2. Set up development environment
3. Implement core authentication layer
4. Build 1NCE API client
5. Create database schema and migrations
6. Implement first API endpoints
7. Set up monitoring and observability
8. Deploy to staging environment
9. Load testing and optimization
10. Production deployment

See `GAME_PLAN.md` for detailed implementation timeline.
