# IOT SIM Platform - Monorepo Architecture
## Detailed Technical Architecture & Design

**Version:** 1.0.0
**Last Updated:** 2024-11-17
**Status:** 📐 Planning Phase

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Service Architecture](#service-architecture)
3. [Data Flow](#data-flow)
4. [Network Architecture](#network-architecture)
5. [Database Design](#database-design)
6. [Authentication & Authorization](#authentication--authorization)
7. [API Design](#api-design)
8. [Frontend Architecture](#frontend-architecture)
9. [Monitoring & Observability](#monitoring--observability)
10. [Deployment Architecture](#deployment-architecture)
11. [Security Architecture](#security-architecture)
12. [Scalability & Performance](#scalability--performance)

---

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USERS                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   End Users  │  │    Admins    │  │  Developers  │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    NGINX REVERSE PROXY                           │
│                  (SSL/TLS Termination)                           │
│                  (Load Balancing)                                │
│                  (Rate Limiting)                                 │
└───┬─────────────┬──────────────────┬──────────────┬─────────────┘
    │             │                  │              │
    ▼             ▼                  ▼              ▼
┌────────┐  ┌──────────┐  ┌──────────────┐  ┌──────────────┐
│ React  │  │Streamlit │  │   Backend    │  │   Grafana    │
│Dashboard│  │  Admin   │  │   API        │  │  Monitor     │
│:3000   │  │  :8501   │  │   :8000      │  │   :3001      │
└────┬───┘  └─────┬────┘  └──────┬───────┘  └──────┬───────┘
     │            │                │                  │
     │            │                │                  │
     └────────────┴────────────────┼──────────────────┘
                                   │
                  ┌────────────────┴────────────────┐
                  │                                 │
                  ▼                                 ▼
         ┌─────────────────┐            ┌──────────────────┐
         │   PostgreSQL    │            │     Redis        │
         │  (TimescaleDB)  │            │     Cache        │
         │     :5432       │            │     :6379        │
         └────────┬────────┘            └─────────┬────────┘
                  │                               │
                  └───────────────┬───────────────┘
                                  │
                                  ▼
                        ┌──────────────────┐
                        │   1NCE API       │
                        │ (External)       │
                        └──────────────────┘
```

### System Components

| Component | Technology | Purpose | Port |
|-----------|-----------|---------|------|
| **React Dashboard** | Next.js 14, TypeScript, Tailwind | Main user interface | 3000 |
| **Streamlit Admin** | Streamlit, Python | Internal admin panel | 8501 |
| **Backend API** | FastAPI, Python 3.11 | REST API, business logic | 8000 |
| **Database** | PostgreSQL 15 + TimescaleDB | Data persistence | 5432 |
| **Cache** | Redis 7 | Caching, sessions | 6379 |
| **Nginx** | Nginx 1.25 | Reverse proxy, load balancer | 80/443 |
| **Prometheus** | Prometheus | Metrics collection | 9090 |
| **Grafana** | Grafana | Monitoring dashboards | 3001 |
| **1NCE API** | External | SIM card management | - |

---

## Service Architecture

### 1. Backend API (FastAPI)

```
backend/
├── app/
│   ├── api/v1/                    # API Endpoints
│   │   ├── __init__.py           # Router aggregation
│   │   ├── deps.py               # Shared dependencies
│   │   ├── auth.py               # Authentication endpoints
│   │   ├── sims.py               # SIM management
│   │   ├── usage.py              # Usage tracking
│   │   ├── quotas.py             # Quota management
│   │   ├── sms.py                # SMS operations
│   │   ├── scheduler.py          # Job management
│   │   └── metrics.py            # Prometheus metrics
│   │
│   ├── clients/                   # External API Clients
│   │   ├── __init__.py
│   │   └── once_client.py        # 1NCE API client
│   │
│   ├── core/                      # Core Functionality
│   │   ├── __init__.py
│   │   ├── config.py             # Configuration (Pydantic)
│   │   ├── security.py           # JWT, password hashing
│   │   ├── logging.py            # Structured logging
│   │   └── exceptions.py         # Custom exceptions
│   │
│   ├── db/                        # Database Layer
│   │   ├── __init__.py
│   │   ├── session.py            # DB session management
│   │   └── base.py               # Base model
│   │
│   ├── models/                    # SQLAlchemy Models
│   │   ├── __init__.py
│   │   ├── user.py               # User model
│   │   ├── api_key.py            # API keys
│   │   ├── sim.py                # SIM cards
│   │   ├── sim_usage.py          # Usage data (TimescaleDB)
│   │   ├── sim_quota.py          # Quotas
│   │   ├── sms.py                # SMS messages
│   │   └── ...
│   │
│   ├── schemas/                   # Pydantic Schemas
│   │   ├── __init__.py
│   │   ├── auth.py               # Auth schemas
│   │   ├── sim.py                # SIM schemas
│   │   ├── usage.py              # Usage schemas
│   │   └── ...
│   │
│   ├── services/                  # Business Logic
│   │   ├── __init__.py
│   │   ├── auth_service.py       # Authentication logic
│   │   ├── sim_service.py        # SIM management logic
│   │   ├── usage_service.py      # Usage tracking logic
│   │   └── ...
│   │
│   ├── tasks/                     # Background Jobs
│   │   ├── __init__.py
│   │   ├── scheduler.py          # APScheduler setup
│   │   ├── sync_jobs.py          # Sync jobs
│   │   └── cleanup_jobs.py       # Cleanup jobs
│   │
│   ├── utils/                     # Utilities
│   │   ├── __init__.py
│   │   ├── cache.py              # Redis caching
│   │   ├── validators.py         # Custom validators
│   │   ├── metrics.py            # Prometheus metrics
│   │   └── pagination.py         # Pagination helpers
│   │
│   └── main.py                    # FastAPI application
│
└── tests/                         # Test Suite
    ├── unit/                      # Unit tests
    ├── integration/               # Integration tests
    └── e2e/                       # End-to-end tests
```

**Key Features:**
- **Async/Await**: All I/O operations are asynchronous
- **Dependency Injection**: FastAPI's dependency system
- **Type Safety**: Pydantic for validation
- **ORM**: SQLAlchemy 2.0 async
- **Background Jobs**: APScheduler for scheduled tasks
- **Caching**: Redis for performance
- **Metrics**: Prometheus instrumentation

### 2. React Dashboard (Next.js)

```
frontend-react/
├── src/
│   ├── app/                       # Next.js App Router
│   │   ├── layout.tsx            # Root layout
│   │   ├── page.tsx              # Home/Dashboard
│   │   ├── login/                # Login page
│   │   ├── sims/                 # SIM management pages
│   │   ├── usage/                # Usage pages
│   │   ├── quotas/               # Quota pages
│   │   └── settings/             # Settings pages
│   │
│   ├── components/                # React Components
│   │   ├── common/               # Shared components
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Table.tsx
│   │   │   ├── Modal.tsx
│   │   │   └── ...
│   │   ├── layout/               # Layout components
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── Footer.tsx
│   │   ├── sims/                 # SIM components
│   │   │   ├── SIMList.tsx
│   │   │   ├── SIMDetail.tsx
│   │   │   ├── SIMForm.tsx
│   │   │   └── ...
│   │   ├── usage/                # Usage components
│   │   │   ├── UsageChart.tsx
│   │   │   ├── UsageTable.tsx
│   │   │   └── ...
│   │   └── quotas/               # Quota components
│   │       ├── QuotaCard.tsx
│   │       ├── TopUpModal.tsx
│   │       └── ...
│   │
│   ├── lib/                       # Libraries & Utilities
│   │   ├── api/                  # API Client
│   │   │   ├── client.ts         # Axios instance
│   │   │   ├── auth.ts           # Auth API
│   │   │   ├── sims.ts           # SIM API
│   │   │   ├── usage.ts          # Usage API
│   │   │   └── ...
│   │   ├── hooks/                # Custom hooks
│   │   │   ├── useAuth.ts        # Auth hook
│   │   │   ├── useSIMs.ts        # SIM data hook
│   │   │   ├── useUsage.ts       # Usage hook
│   │   │   └── ...
│   │   ├── contexts/             # React contexts
│   │   │   └── AuthContext.tsx   # Auth context
│   │   └── utils/                # Utility functions
│   │       ├── format.ts         # Formatters
│   │       ├── validators.ts     # Validators
│   │       └── ...
│   │
│   ├── types/                     # TypeScript types
│   │   ├── api.ts                # API types
│   │   ├── sim.ts                # SIM types
│   │   └── ...
│   │
│   └── styles/                    # Styles
│       └── globals.css           # Global styles
│
├── public/                        # Static assets
│   ├── images/
│   └── icons/
│
└── tests/                         # Tests
    ├── components/
    ├── integration/
    └── e2e/
```

**Key Features:**
- **Server Components**: Leverage Next.js 14 server components
- **TypeScript**: Full type safety
- **Tailwind CSS**: Utility-first styling
- **React Query**: Server state management
- **React Hook Form**: Form handling
- **Zod**: Schema validation
- **Chart.js/Recharts**: Data visualization

### 3. Streamlit Admin Panel

```
frontend-streamlit/
├── app/
│   ├── pages/                     # Streamlit pages
│   │   ├── 1_📊_Dashboard.py
│   │   ├── 2_📱_SIMs.py
│   │   ├── 3_📈_Usage.py
│   │   ├── 4_💾_Quotas.py
│   │   ├── 5_💬_SMS.py
│   │   └── 6_⚙️_Admin.py
│   │
│   ├── components/                # Reusable components
│   │   ├── __init__.py
│   │   ├── charts.py             # Chart components
│   │   ├── tables.py             # Table components
│   │   └── forms.py              # Form components
│   │
│   └── utils/                     # Utilities
│       ├── __init__.py
│       ├── formatters.py         # Data formatters
│       └── validators.py         # Validators
│
├── api/                           # API Client
│   ├── __init__.py
│   ├── client.py                 # HTTP client
│   └── auth.py                   # Auth handling
│
├── config/                        # Configuration
│   ├── __init__.py
│   └── settings.py               # App settings
│
└── Home.py                        # Main entry point
```

**Key Features:**
- **Rapid Development**: Python-based UI
- **Interactive Charts**: Plotly integration
- **Session State**: Built-in state management
- **File Upload**: CSV import/export
- **Real-time Updates**: Auto-refresh capabilities

### 4. Monitoring Stack

```
monitoring/
├── grafana/
│   ├── dashboards/
│   │   ├── infrastructure.json   # System metrics
│   │   ├── business.json         # Business KPIs
│   │   ├── api.json              # API metrics
│   │   └── sims.json             # SIM overview
│   │
│   ├── datasources/
│   │   └── prometheus.yml        # Prometheus datasource
│   │
│   ├── provisioning/
│   │   ├── dashboards/
│   │   └── datasources/
│   │
│   └── grafana.ini               # Grafana config
│
├── prometheus/
│   ├── prometheus.yml            # Main config
│   ├── alerts.yml                # Alert rules
│   │
│   └── rules/
│       ├── recording.yml         # Recording rules
│       └── alerts.yml            # Alert rules
│
└── alertmanager/
    └── alertmanager.yml          # Alert routing
```

---

## Data Flow

### 1. User Authentication Flow

```
User (Browser)
    │
    │ 1. POST /api/v1/auth/login
    │    {username, password}
    ▼
React Dashboard (Next.js)
    │
    │ 2. Forward to API
    ▼
Backend API (FastAPI)
    │
    │ 3. Validate credentials
    │ 4. Hash comparison
    ▼
PostgreSQL
    │
    │ 5. Return user data
    ▼
Backend API
    │
    │ 6. Generate JWT tokens
    │    - Access token (30 min)
    │    - Refresh token (7 days)
    ▼
React Dashboard
    │
    │ 7. Store tokens
    │    - localStorage/sessionStorage
    │ 8. Set Authorization header
    │    - Bearer {access_token}
    ▼
Protected Routes
```

### 2. SIM Data Retrieval Flow

```
User Request
    │
    │ 1. GET /api/v1/sims?page=1&page_size=50
    ▼
Nginx
    │
    │ 2. Route to backend
    │    - Rate limiting
    │    - SSL termination
    ▼
Backend API
    │
    │ 3. Auth middleware
    │    - Validate JWT
    │    - Check permissions
    ▼
Redis Cache
    │
    ├─ Cache HIT? ──────────┐
    │                        │
    │ Cache MISS             │
    ▼                        │
PostgreSQL                  │
    │                        │
    │ 4. Query SIMs          │
    │    SELECT * FROM sims  │
    │    LIMIT 50 OFFSET 0   │
    ▼                        │
Backend API                 │
    │                        │
    │ 5. Cache result        │
    │    (TTL: 5 minutes)    │
    ▼                        │
    └────────────────────────┘
    │
    │ 6. Return JSON
    │    {items, total, page, ...}
    ▼
React Dashboard
    │
    │ 7. Display in table
    │    - Pagination
    │    - Sorting
    │    - Filtering
    ▼
User sees data
```

### 3. SIM Synchronization Flow

```
User Action
    │
    │ 1. Click "Sync from 1NCE"
    ▼
Backend API
    │
    │ 2. Trigger sync job
    ▼
Background Scheduler (APScheduler)
    │
    │ 3. Execute sync job
    ▼
1NCE API Client
    │
    │ 4. Authenticate with 1NCE
    │    - OAuth 2.0 client credentials
    │    - Get access token
    ▼
1NCE API (External)
    │
    │ 5. GET /v1/sims
    │    - Paginated requests
    │    - Rate limiting (respect)
    ▼
Backend API
    │
    │ 6. Process SIM data
    │    - Transform format
    │    - Validate data
    ▼
PostgreSQL
    │
    │ 7. Upsert SIMs
    │    INSERT ... ON CONFLICT UPDATE
    ▼
Redis Cache
    │
    │ 8. Invalidate cache
    │    - Clear SIM lists
    │    - Clear individual SIMs
    ▼
Prometheus
    │
    │ 9. Record metrics
    │    - sync_duration
    │    - sims_synced
    │    - errors
    ▼
Grafana
    │
    │ 10. Display in dashboard
    ▼
User sees updated data
```

### 4. Usage Data Collection Flow

```
Scheduled Job (Every hour)
    │
    ▼
Backend Scheduler
    │
    │ 1. Trigger usage sync
    ▼
1NCE API
    │
    │ 2. GET /v1/usage
    │    - Last 24 hours
    ▼
Backend API
    │
    │ 3. Parse usage data
    │    - Data volume
    │    - SMS count
    │    - Timestamps
    ▼
PostgreSQL (TimescaleDB)
    │
    │ 4. INSERT usage records
    │    - Optimized for time-series
    │    - Automatic compression
    │    - Retention policies
    ▼
Prometheus
    │
    │ 5. Export metrics
    │    - Total usage
    │    - Per-SIM usage
    ▼
Grafana
    │
    │ 6. Visualize trends
    │    - Usage charts
    │    - Forecasting
    ▼
Alerts (if thresholds exceeded)
```

---

## Network Architecture

### Docker Network Topology

```
┌────────────────────────────────────────────────────────────┐
│                    Docker Host                              │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐ │
│  │            iot-network (bridge)                       │ │
│  │                                                        │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │ │
│  │  │  nginx   │  │ frontend │  │streamlit │           │ │
│  │  │  :80/443 │  │  react   │  │  :8501   │           │ │
│  │  └────┬─────┘  │  :3000   │  └────┬─────┘           │ │
│  │       │        └────┬─────┘       │                  │ │
│  │       │             │             │                  │ │
│  │       └─────────────┼─────────────┘                  │ │
│  │                     │                                │ │
│  │              ┌──────┴──────┐                         │ │
│  │              │   backend   │                         │ │
│  │              │    api      │                         │ │
│  │              │   :8000     │                         │ │
│  │              └──────┬──────┘                         │ │
│  │                     │                                │ │
│  │        ┌────────────┼────────────┐                   │ │
│  │        │            │            │                   │ │
│  │   ┌────▼────┐  ┌───▼─────┐ ┌───▼────┐              │ │
│  │   │postgres │  │  redis  │ │prometheus│            │ │
│  │   │  :5432  │  │  :6379  │ │  :9090  │              │ │
│  │   └─────────┘  └─────────┘ └───┬────┘              │ │
│  │                                 │                    │ │
│  │                           ┌─────▼────┐               │ │
│  │                           │ grafana  │               │ │
│  │                           │  :3001   │               │ │
│  │                           └──────────┘               │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                             │
│  Port Mappings (Host:Container):                          │
│  - 80:80     → Nginx HTTP                                 │
│  - 443:443   → Nginx HTTPS                                │
│  - 3000:3000 → React (dev only)                           │
│  - 8000:8000 → Backend API (dev only)                     │
│  - 8501:8501 → Streamlit (dev only)                       │
│  - 3001:3000 → Grafana                                    │
│  - 9090:9090 → Prometheus (internal)                      │
│  - 5432:5432 → PostgreSQL (internal)                      │
│  - 6379:6379 → Redis (internal)                           │
└─────────────────────────────────────────────────────────────┘
```

### Service Communication

**Development:**
- Direct port access
- No Nginx required
- Hot reload enabled

**Production:**
- All traffic through Nginx
- Internal network only
- No direct port access

### Network Security

```yaml
networks:
  iot-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
    driver_opts:
      com.docker.network.bridge.name: iot-net
```

**Firewall Rules:**
- External → Nginx only (80, 443)
- Nginx → All services (internal)
- Services → Database/Redis (internal)
- Backend → 1NCE API (external)

---

## Database Design

### Schema Overview

```sql
-- Users & Authentication
users (id, username, email, hashed_password, is_active, is_superuser)
api_keys (id, user_id, key_hash, name, expires_at, is_active)

-- SIM Management
sims (id, iccid, imsi, msisdn, status, ip_address, ...)
sim_usage (id, sim_id, timestamp, data_volume, sms_mo, sms_mt, ...)
sim_quotas (id, sim_id, quota_type, volume, used_volume, ...)
sim_connectivity (id, sim_id, status, network, country, ...)
sim_events (id, sim_id, event_type, timestamp, details)

-- SMS
sms_messages (id, sim_id, direction, message, status, ...)

-- Orders & Products
orders (id, user_id, status, total_cost, ...)
order_items (id, order_id, product_id, quantity, price)
products (id, name, description, price, sku)

-- Support
support_tickets (id, user_id, subject, status, priority, ...)
```

### TimescaleDB Hypertables

```sql
-- Convert sim_usage to hypertable
SELECT create_hypertable('sim_usage', 'timestamp');

-- Compression policy (after 7 days)
SELECT add_compression_policy('sim_usage', INTERVAL '7 days');

-- Retention policy (keep 1 year)
SELECT add_retention_policy('sim_usage', INTERVAL '1 year');

-- Continuous aggregates for performance
CREATE MATERIALIZED VIEW sim_usage_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', timestamp) AS hour,
    sim_id,
    SUM(data_volume) as total_data,
    SUM(sms_mo) as total_sms_sent,
    SUM(sms_mt) as total_sms_received
FROM sim_usage
GROUP BY hour, sim_id;
```

### Indexes

```sql
-- SIMs
CREATE INDEX idx_sims_iccid ON sims(iccid);
CREATE INDEX idx_sims_status ON sims(status);
CREATE INDEX idx_sims_created_at ON sims(created_at);

-- Usage (TimescaleDB auto-creates time indexes)
CREATE INDEX idx_usage_sim_id ON sim_usage(sim_id);

-- Quotas
CREATE INDEX idx_quotas_sim_id ON sim_quotas(sim_id);
CREATE INDEX idx_quotas_type ON sim_quotas(quota_type);

-- Events
CREATE INDEX idx_events_sim_id ON sim_events(sim_id);
CREATE INDEX idx_events_type ON sim_events(event_type);
CREATE INDEX idx_events_timestamp ON sim_events(timestamp);
```

---

## Authentication & Authorization

### JWT Token Strategy

**Access Token:**
- **Lifetime:** 30 minutes
- **Payload:** {sub: user_id, username, exp}
- **Use:** API requests
- **Storage:** Memory/sessionStorage (frontend)

**Refresh Token:**
- **Lifetime:** 7 days
- **Payload:** {sub: user_id, type: refresh, exp}
- **Use:** Get new access token
- **Storage:** httpOnly cookie (recommended) or localStorage

### API Key Strategy

**Format:** `iot_key_{random_32_bytes}`

**Storage:**
- Hash (SHA-256) stored in database
- Plain key shown only once on creation
- Prefix stored for identification

**Usage:**
- Header: `X-API-Key: iot_key_...`
- Query param: `?api_key=iot_key_...` (discouraged)

### Authorization Levels

```python
# Permission levels
class UserRole(str, Enum):
    ADMIN = "admin"          # Full access
    OPERATOR = "operator"    # SIM management, no user management
    VIEWER = "viewer"        # Read-only access

# Endpoint protection
@router.get("/admin/users")
async def list_users(
    current_user: User = Depends(require_admin)
):
    ...

@router.get("/sims")
async def list_sims(
    current_user: User = Depends(require_authenticated)
):
    ...
```

---

## API Design

### RESTful Principles

```
GET    /api/v1/sims           # List SIMs
POST   /api/v1/sims           # Create SIM
GET    /api/v1/sims/{iccid}   # Get SIM
PATCH  /api/v1/sims/{iccid}   # Update SIM
DELETE /api/v1/sims/{iccid}   # Delete SIM (soft delete)

# Nested resources
GET    /api/v1/sims/{iccid}/usage
GET    /api/v1/sims/{iccid}/quotas
POST   /api/v1/sims/{iccid}/topup

# Actions (non-CRUD)
POST   /api/v1/sims/{iccid}/sync
POST   /api/v1/sims/{iccid}/sms
POST   /api/v1/sims/sync-all
```

### API Versioning

- **URL Versioning:** `/api/v1/`, `/api/v2/`
- **Header Versioning:** `Accept: application/vnd.api.v1+json`
- **Deprecation:** Minimum 6 months notice

### Error Responses

```json
{
  "error": {
    "code": "SIM_NOT_FOUND",
    "message": "SIM with ICCID 89490200001234567890 not found",
    "details": {
      "iccid": "89490200001234567890"
    },
    "request_id": "req_abc123"
  }
}
```

### Rate Limiting

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1700145600
```

---

## Frontend Architecture

### State Management Strategy

**React Dashboard:**

```typescript
// Server state (React Query)
const { data: sims, isLoading } = useQuery({
  queryKey: ['sims', page],
  queryFn: () => api.sims.list({ page })
});

// Client state (React Context)
const { user, isAuthenticated } = useAuth();

// Form state (React Hook Form)
const { register, handleSubmit } = useForm<SIMFormData>();
```

**Streamlit:**

```python
# Session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# Caching
@st.cache_data(ttl=300)
def get_sims():
    return api.get_sims()
```

### Routing Structure

```typescript
// Next.js App Router
app/
  layout.tsx              # → /
  page.tsx                # → / (Dashboard)
  login/page.tsx          # → /login
  sims/
    page.tsx              # → /sims (List)
    [iccid]/page.tsx      # → /sims/89... (Detail)
    new/page.tsx          # → /sims/new (Create)
  usage/page.tsx          # → /usage
  quotas/page.tsx         # → /quotas
  settings/page.tsx       # → /settings
```

---

## Monitoring & Observability

### Metrics Collection

**Application Metrics:**
```python
# Prometheus metrics
http_requests_total = Counter('http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'])

http_request_duration = Histogram('http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint'])

sims_total = Gauge('sims_total',
    'Total number of SIMs',
    ['status'])
```

**Database Metrics:**
- Connection pool size
- Query duration
- Slow queries
- Lock waits

**Business Metrics:**
- Active SIMs
- Data consumption
- SMS usage
- Top-up frequency
- Revenue

### Logging Strategy

**Structured Logging:**
```python
logger.info(
    "sim_created",
    iccid=sim.iccid,
    user_id=current_user.id,
    duration_ms=duration
)
```

**Log Levels:**
- DEBUG: Development only
- INFO: Normal operations
- WARNING: Potential issues
- ERROR: Errors (still functioning)
- CRITICAL: System failures

### Alerting Rules

```yaml
groups:
  - name: api_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High API error rate"

      - alert: SlowQueries
        expr: histogram_quantile(0.95, rate(db_query_duration_seconds_bucket[5m])) > 1
        for: 10m
        annotations:
          summary: "Database queries are slow"
```

---

## Deployment Architecture

### Development Environment

```yaml
# docker-compose.yml
services:
  backend:
    build: ./backend
    volumes:
      - ./backend:/app  # Hot reload
    environment:
      - DEBUG=true
      - RELOAD=true

  frontend-react:
    build: ./frontend-react
    volumes:
      - ./frontend-react:/app
      - /app/node_modules
    command: npm run dev
```

### Production Environment

```yaml
# docker-compose.prod.yml
services:
  backend:
    image: iot-backend:latest
    replicas: 3
    resources:
      limits:
        cpus: '2'
        memory: 2G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### CI/CD Pipeline

```yaml
# .github/workflows/backend-ci.yml
name: Backend CI/CD

on:
  push:
    paths:
      - 'backend/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: pytest

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Build Docker image
        run: docker build -t backend:${{ github.sha }}

  deploy:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production
        run: ./scripts/deployment/deploy.sh
```

---

## Security Architecture

### Security Layers

1. **Network Security**
   - HTTPS only (TLS 1.3)
   - Firewall rules
   - Private networks

2. **Application Security**
   - Input validation (Pydantic)
   - SQL injection prevention (ORM)
   - XSS protection
   - CSRF tokens

3. **Authentication**
   - Strong password hashing (bcrypt)
   - JWT tokens
   - API keys

4. **Authorization**
   - Role-based access control
   - Endpoint protection
   - Resource ownership

5. **Data Security**
   - Encryption at rest
   - Encryption in transit
   - Sensitive data masking

### Security Headers

```nginx
add_header X-Frame-Options "DENY";
add_header X-Content-Type-Options "nosniff";
add_header X-XSS-Protection "1; mode=block";
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
add_header Content-Security-Policy "default-src 'self'";
```

---

## Scalability & Performance

### Horizontal Scaling

```yaml
# Backend replicas
services:
  backend:
    deploy:
      replicas: 3

# Nginx load balancing
upstream backend {
    least_conn;
    server backend-1:8000;
    server backend-2:8000;
    server backend-3:8000;
}
```

### Caching Strategy

**Layers:**
1. Browser cache (static assets)
2. CDN cache (global distribution)
3. Redis cache (API responses)
4. Database query cache

**Cache Invalidation:**
- Time-based (TTL)
- Event-based (on updates)
- Manual (admin action)

### Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| API Response (p95) | < 200ms | Prometheus |
| Frontend Load | < 2s | Lighthouse |
| Database Query | < 100ms | Slow query log |
| Cache Hit Rate | > 80% | Redis stats |
| Uptime | 99.9% | Grafana |

---

**Document Status:** ✅ Complete
**Last Updated:** 2024-11-17
**Next Review:** After implementation begins
