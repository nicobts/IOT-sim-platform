# Future Improvements - IOT SIM Platform

**Document Version:** 1.0
**Last Updated:** 2025-11-18
**Platform Version:** 2.1.0 (Next.js 16.0.3)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Performance Optimizations](#performance-optimizations)
3. [React Frontend - Complete Implementation](#react-frontend---complete-implementation)
4. [AI/ML Features](#aiml-features)
5. [MCP (Model Context Protocol) Integration](#mcp-model-context-protocol-integration)
6. [New Features](#new-features)
7. [Infrastructure Enhancements](#infrastructure-enhancements)
8. [Security Improvements](#security-improvements)
9. [Implementation Roadmap](#implementation-roadmap)
10. [Cost & ROI Analysis](#cost--roi-analysis)

---

## Executive Summary

The IOT SIM Platform has a **solid foundation** with excellent backend (8.6/10) and cutting-edge Next.js 16 frontend architecture. Key improvement areas:

### Critical Priorities
1. **Complete React Frontend** (90% missing features)
2. **Enable Caching Layer** (Redis underutilized)
3. **Implement AI/ML Features** (High ROI opportunity)
4. **Add MCP Integration** (Next.js 16 DevTools MCP ready)
5. **Real-time Features** (WebSocket support)

### Expected Impact
- **50% reduction** in API response time (caching)
- **30% reduction** in customer churn (AI predictions)
- **80% reduction** in database queries (optimization)
- **3x increase** in throughput (performance tuning)

---

## Performance Optimizations

### 1. Enable Redis Caching Layer
**Priority:** HIGH | **Effort:** LOW | **Impact:** HIGH

#### Current State
- Redis configured but underutilized
- No caching decorators
- No cache invalidation strategy

#### Implementation

```python
# backend/app/services/cache_service.py
import json
import hashlib
from typing import Any, Optional
from functools import wraps
from redis import asyncio as aioredis

class CacheService:
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client

    async def get(self, key: str) -> Optional[Any]:
        value = await self.redis.get(key)
        return json.loads(value) if value else None

    async def set(self, key: str, value: Any, ttl: int = 300):
        await self.redis.setex(key, ttl, json.dumps(value, default=str))

    async def delete(self, pattern: str):
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)

    async def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)

# Caching decorator
def cached(ttl: int = 300, key_prefix: str = ""):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hashlib.md5(
                json.dumps([str(arg) for arg in args] + [str(kwargs)], sort_keys=True).encode()
            ).hexdigest()}"

            # Check cache
            cache = kwargs.get('cache') or args[0] if args else None
            if cache and hasattr(cache, 'get'):
                cached_value = await cache.get(cache_key)
                if cached_value:
                    return cached_value

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            if cache and hasattr(cache, 'set'):
                await cache.set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator
```

#### Usage Examples

```python
# Apply to SIM endpoints
@app.get("/api/v1/sims")
@cached(ttl=300, key_prefix="sims")
async def get_sims(
    status: Optional[str] = None,
    page: int = 1,
    cache: CacheService = Depends(get_cache)
):
    cache_key = f"sims:list:{status}:{page}"

    # Check cache
    cached = await cache.get(cache_key)
    if cached:
        return cached

    # Fetch from database
    sims = await SIMService.get_sims(status=status, page=page)

    # Cache result
    await cache.set(cache_key, sims, ttl=300)

    return sims

# Cache individual SIM details
@app.get("/api/v1/sims/{iccid}")
@cached(ttl=120, key_prefix="sim_detail")
async def get_sim(iccid: str, cache: CacheService = Depends(get_cache)):
    sim = await SIMService.get_sim(iccid)
    return sim
```

#### Cache Strategy

| Data Type | TTL | Invalidation Strategy |
|-----------|-----|----------------------|
| SIM list | 5 min | On SIM create/update/delete |
| SIM detail | 2 min | On SIM update |
| Usage data | 10 min | On usage sync |
| Quota status | 1 min | On quota update |
| 1NCE API responses | 5 min | On manual refresh |
| Analytics aggregations | 30 min | Daily at midnight |

#### Expected Impact
- **80% reduction** in database queries
- **50% faster** response times
- **3x increase** in throughput
- **Lower database load**

---

### 2. Database Query Optimization
**Priority:** HIGH | **Effort:** MEDIUM | **Impact:** HIGH

#### Problem: N+1 Query Pattern

**Before (Inefficient):**
```python
# N+1 queries - BAD
sims = await session.execute(select(SIM).limit(10))
for sim in sims.scalars():
    usage = await get_last_usage(sim.iccid)  # 10 additional queries!
    quota = await get_quota(sim.iccid)       # 10 more queries!
```

**After (Optimized):**
```python
# Single query with joins - GOOD
sims_with_data = await session.execute(
    select(SIM)
    .outerjoin(SIMUsage)
    .outerjoin(SIMQuota)
    .options(
        selectinload(SIM.latest_usage),
        selectinload(SIM.quota)
    )
    .limit(10)
)
```

#### Async Parallel Operations

**Before (Sequential):**
```python
# Sequential - 300ms total
sim = await get_sim(iccid)           # 100ms
usage = await get_usage(iccid)       # 100ms
quota = await get_quota(iccid)       # 100ms
```

**After (Parallel):**
```python
# Parallel - 100ms total
sim, usage, quota = await asyncio.gather(
    get_sim(iccid),
    get_usage(iccid),
    get_quota(iccid)
)
```

#### Expected Impact
- **90% reduction** in query count
- **60% faster** page loads
- **Lower database CPU usage**

---

### 3. Response Compression
**Priority:** MEDIUM | **Effort:** LOW | **Impact:** MEDIUM

```python
# backend/app/main.py
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

#### Expected Impact
- **70% reduction** in bandwidth usage
- **Faster responses** for large payloads
- **Lower CDN costs**

---

### 4. Cursor-Based Pagination
**Priority:** MEDIUM | **Effort:** MEDIUM | **Impact:** MEDIUM

**Problem:** Offset pagination is slow for large datasets

**Before (Slow for large offsets):**
```sql
SELECT * FROM sims LIMIT 10 OFFSET 10000;  -- Scans 10,010 rows
```

**After (Fast at any position):**
```sql
SELECT * FROM sims WHERE id > {last_id} ORDER BY id LIMIT 10;  -- Scans 10 rows
```

```python
@app.get("/api/v1/sims/paginated")
async def get_sims_paginated(
    cursor: Optional[int] = None,
    limit: int = 20
):
    query = select(SIM).order_by(SIM.id).limit(limit)

    if cursor:
        query = query.where(SIM.id > cursor)

    sims = await session.execute(query)
    results = sims.scalars().all()

    next_cursor = results[-1].id if results else None

    return {
        "data": results,
        "next_cursor": next_cursor,
        "has_more": len(results) == limit
    }
```

---

### 5. Connection Pool Optimization
**Priority:** MEDIUM | **Effort:** LOW | **Impact:** MEDIUM

```python
# backend/app/database.py
engine = create_async_engine(
    DATABASE_URL,
    pool_size=50,           # Increase from 20
    max_overflow=20,        # Allow bursts
    pool_pre_ping=True,     # Check connection health
    pool_recycle=3600,      # Recycle hourly
    echo_pool=True,         # Log pool activity (dev only)
)
```

---

### 6. TimescaleDB Compression & Retention
**Priority:** LOW | **Effort:** LOW | **Impact:** MEDIUM

```sql
-- Enable compression for old usage data
SELECT add_compression_policy('sim_usage', INTERVAL '7 days');

-- Automatically delete data older than 1 year
SELECT add_retention_policy('sim_usage', INTERVAL '1 year');

-- Continuous aggregates for fast analytics
CREATE MATERIALIZED VIEW sim_usage_daily
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', timestamp) AS day,
    iccid,
    SUM(volume) AS total_volume,
    COUNT(*) AS event_count
FROM sim_usage
GROUP BY day, iccid;

-- Refresh policy
SELECT add_continuous_aggregate_policy('sim_usage_daily',
    start_offset => INTERVAL '1 month',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');
```

---

## React Frontend - Complete Implementation

### Current State: 2/10 (Skeleton Only)
### Target State: 9/10 (Production-Ready)

The React frontend is built on **Next.js 16.0.3** (cutting-edge) but missing 90% of features.

---

### 1. Authentication Flow
**Priority:** CRITICAL | **Effort:** HIGH

#### Pages to Create

```typescript
// app/auth/login/page.tsx
export default function LoginPage() {
  const [credentials, setCredentials] = useState({ email: '', password: '' });
  const router = useRouter();
  const { setUser } = useAuthStore();

  const handleLogin = async (e: FormEvent) => {
    e.preventDefault();

    const response = await apiClient.login(credentials);

    if (response.access_token) {
      setUser(response.user);
      localStorage.setItem('token', response.access_token);
      router.push('/dashboard');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center">
      <Card className="w-[400px]">
        <CardHeader>
          <CardTitle>Login to IOT SIM Platform</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleLogin} className="space-y-4">
            <Input
              type="email"
              placeholder="Email"
              value={credentials.email}
              onChange={(e) => setCredentials(prev => ({ ...prev, email: e.target.value }))}
            />
            <Input
              type="password"
              placeholder="Password"
              value={credentials.password}
              onChange={(e) => setCredentials(prev => ({ ...prev, password: e.target.value }))}
            />
            <Button type="submit" className="w-full">Login</Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
```

#### Auth Context Provider

```typescript
// app/providers/auth-provider.tsx
'use client';
import { createContext, useContext, useEffect, useState } from 'react';
import { apiClient } from '@/lib/api-client';

const AuthContext = createContext<{
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
}>({
  user: null,
  login: async () => {},
  logout: () => {},
  loading: true
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing session
    const token = localStorage.getItem('token');
    if (token) {
      apiClient.setToken(token);
      fetchUser();
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUser = async () => {
    try {
      const user = await apiClient.getCurrentUser();
      setUser(user);
    } catch {
      localStorage.removeItem('token');
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    const response = await apiClient.login({ email, password });
    localStorage.setItem('token', response.access_token);
    setUser(response.user);
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
```

---

### 2. SIM Management Pages
**Priority:** CRITICAL | **Effort:** HIGH

#### SIM List Page

```typescript
// app/sims/page.tsx
'use client';
import { useSims } from '@/hooks/use-sims';
import { DataTable } from '@/components/ui/data-table';

export default function SIMsPage() {
  const [filters, setFilters] = useState({ status: 'all', search: '' });
  const { sims, isLoading, mutate } = useSims(filters);

  const columns = [
    { accessorKey: 'iccid', header: 'ICCID' },
    { accessorKey: 'msisdn', header: 'Phone Number' },
    { accessorKey: 'status', header: 'Status', cell: ({ row }) => (
      <Badge variant={row.original.status === 'active' ? 'success' : 'secondary'}>
        {row.original.status}
      </Badge>
    )},
    { accessorKey: 'operator', header: 'Operator' },
    { accessorKey: 'ip_address', header: 'IP Address' },
    { id: 'actions', cell: ({ row }) => (
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost"><MoreHorizontal /></Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuItem onClick={() => router.push(`/sims/${row.original.iccid}`)}>
            View Details
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => handleActivate(row.original.iccid)}>
            {row.original.status === 'active' ? 'Deactivate' : 'Activate'}
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => handleDelete(row.original.iccid)}>
            Delete
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    )}
  ];

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">SIM Cards</h1>
        <Button onClick={() => router.push('/sims/new')}>
          <Plus className="mr-2" /> Add SIM
        </Button>
      </div>

      <div className="mb-4 flex gap-4">
        <Input
          placeholder="Search by ICCID or MSISDN..."
          value={filters.search}
          onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
        />
        <Select
          value={filters.status}
          onValueChange={(value) => setFilters(prev => ({ ...prev, status: value }))}
        >
          <SelectTrigger className="w-[200px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="inactive">Inactive</SelectItem>
            <SelectItem value="suspended">Suspended</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <DataTable columns={columns} data={sims || []} loading={isLoading} />
    </div>
  );
}
```

#### SIM Detail Page

```typescript
// app/sims/[iccid]/page.tsx
'use client';
import { useSIM } from '@/hooks/use-sim';
import { UsageChart } from '@/components/charts/usage-chart';
import { AIInsights } from '@/components/ai/ai-insights';

export default function SIMDetailPage({ params }: { params: { iccid: string } }) {
  const { sim, usage, quota, isLoading } = useSIM(params.iccid);

  if (isLoading) return <LoadingSpinner />;
  if (!sim) return <NotFound />;

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">{sim.iccid}</h1>
          <p className="text-muted-foreground">{sim.msisdn}</p>
        </div>
        <Badge variant={sim.status === 'active' ? 'success' : 'secondary'}>
          {sim.status}
        </Badge>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Operator</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{sim.operator}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">IP Address</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{sim.ip_address}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Data Used</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{formatBytes(quota?.used || 0)}</p>
            <p className="text-sm text-muted-foreground">
              of {formatBytes(quota?.total || 0)}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Remaining</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{formatBytes(quota?.remaining || 0)}</p>
            <Progress value={(quota?.used / quota?.total) * 100} />
          </CardContent>
        </Card>
      </div>

      {/* Usage Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Usage History (30 Days)</CardTitle>
        </CardHeader>
        <CardContent>
          <UsageChart data={usage} />
        </CardContent>
      </Card>

      {/* AI Insights */}
      <AIInsights iccid={params.iccid} />

      {/* Actions */}
      <div className="flex gap-4">
        <Button onClick={() => handleActivate(sim.iccid)}>
          {sim.status === 'active' ? 'Deactivate' : 'Activate'}
        </Button>
        <Button variant="outline" onClick={() => handleRefreshUsage(sim.iccid)}>
          <RefreshCw className="mr-2" /> Refresh Usage
        </Button>
        <Button variant="outline" onClick={() => handleSendSMS(sim.iccid)}>
          <MessageSquare className="mr-2" /> Send SMS
        </Button>
      </div>
    </div>
  );
}
```

---

### 3. State Management (Zustand)
**Priority:** CRITICAL | **Effort:** MEDIUM

```typescript
// stores/auth-store.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  user: User | null;
  token: string | null;
  setUser: (user: User) => void;
  setToken: (token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      setUser: (user) => set({ user }),
      setToken: (token) => set({ token }),
      logout: () => set({ user: null, token: null })
    }),
    { name: 'auth-storage' }
  )
);

// stores/ui-store.ts
interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  toggleSidebar: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  theme: 'light',
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setTheme: (theme) => set({ theme })
}));
```

---

### 4. Data Fetching Hooks (SWR)
**Priority:** CRITICAL | **Effort:** MEDIUM

```typescript
// hooks/use-sims.ts
import useSWR from 'swr';
import { apiClient } from '@/lib/api-client';

export function useSims(filters?: { status?: string; search?: string }) {
  const { data, error, mutate } = useSWR(
    ['/api/v1/sims', filters],
    ([url, filters]) => apiClient.getSims(filters),
    {
      refreshInterval: 30000, // Refresh every 30s
      revalidateOnFocus: true
    }
  );

  return {
    sims: data,
    isLoading: !error && !data,
    isError: error,
    mutate
  };
}

// hooks/use-sim.ts
export function useSIM(iccid: string) {
  const { data: sim, mutate: mutateSim } = useSWR(
    `/api/v1/sims/${iccid}`,
    apiClient.getSim
  );

  const { data: usage } = useSWR(
    `/api/v1/sims/${iccid}/usage`,
    apiClient.getUsage
  );

  const { data: quota } = useSWR(
    `/api/v1/sims/${iccid}/quota`,
    apiClient.getQuota
  );

  return {
    sim,
    usage,
    quota,
    isLoading: !sim,
    mutate: mutateSim
  };
}
```

---

### 5. Component Library
**Priority:** HIGH | **Effort:** MEDIUM

Using **shadcn/ui** components (already configured):

```bash
# Install all needed components
npx shadcn-ui@latest add button card input select table badge dropdown-menu dialog alert
npx shadcn-ui@latest add chart progress tabs tooltip avatar skeleton
```

---

## AI/ML Features

### Overview

The platform has rich time-series data perfect for AI/ML integration:
- Historical usage patterns
- Quota utilization
- Device behavior
- Cost optimization opportunities

---

### 1. Predictive Usage Analytics
**Priority:** HIGH | **Effort:** MEDIUM | **ROI:** HIGH

#### Goal
Predict when SIMs will reach quota limits 7-30 days in advance.

#### Implementation

```python
# backend/app/ml/models/usage_predictor.py
import pandas as pd
from prophet import Prophet
import joblib
from typing import Dict, List

class UsagePredictor:
    """Predict future SIM usage using Facebook Prophet"""

    def __init__(self):
        self.model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            changepoint_prior_scale=0.05
        )

    async def train(self, iccid: str):
        """Train model for specific SIM"""
        # Fetch historical usage data
        usage_history = await session.execute(
            select(
                SIMUsage.timestamp,
                SIMUsage.volume
            )
            .where(SIMUsage.iccid == iccid)
            .where(SIMUsage.timestamp >= date.today() - timedelta(days=90))
            .order_by(SIMUsage.timestamp)
        )

        # Prepare data for Prophet (requires 'ds' and 'y' columns)
        df = pd.DataFrame(
            [(row.timestamp, row.volume) for row in usage_history],
            columns=['ds', 'y']
        )

        if len(df) < 14:  # Need at least 2 weeks of data
            raise ValueError("Insufficient data for training")

        # Train model
        self.model.fit(df)

        # Save model
        model_path = f'models/usage_predictor_{iccid}.pkl'
        joblib.dump(self.model, model_path)

        return model_path

    async def predict(self, iccid: str, days: int = 7) -> Dict:
        """Generate usage forecast"""
        # Load trained model
        model_path = f'models/usage_predictor_{iccid}.pkl'
        model = joblib.load(model_path)

        # Create future dataframe
        future = model.make_future_dataframe(periods=days, freq='D')

        # Generate forecast
        forecast = model.predict(future)

        # Get current quota
        quota = await self.get_quota(iccid)

        # Estimate exhaustion date
        exhaustion_date = self.estimate_exhaustion_date(
            forecast,
            quota.remaining
        )

        return {
            "iccid": iccid,
            "forecast_days": days,
            "predictions": forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
                .tail(days)
                .to_dict('records'),
            "current_quota": {
                "total": quota.total,
                "used": quota.used,
                "remaining": quota.remaining
            },
            "quota_exhaustion_date": exhaustion_date,
            "days_until_exhaustion": (exhaustion_date - date.today()).days if exhaustion_date else None,
            "confidence_interval": {
                "lower": forecast['yhat_lower'].tail(days).tolist(),
                "upper": forecast['yhat_upper'].tail(days).tolist()
            }
        }

    def estimate_exhaustion_date(self, forecast: pd.DataFrame, remaining_quota: float):
        """Calculate when quota will be exhausted"""
        cumulative_usage = 0

        for _, row in forecast.iterrows():
            cumulative_usage += row['yhat']
            if cumulative_usage >= remaining_quota:
                return row['ds'].date()

        return None  # Quota won't be exhausted in forecast period

# API Endpoint
@app.get("/api/v1/ai/sims/{iccid}/usage-forecast")
async def get_usage_forecast(
    iccid: str,
    days: int = 7,
    user: User = Depends(get_current_user)
):
    """Get AI-powered usage forecast for a SIM"""
    predictor = UsagePredictor()

    try:
        forecast = await predictor.predict(iccid, days)
        return forecast
    except FileNotFoundError:
        # Model not trained yet - train it
        await predictor.train(iccid)
        forecast = await predictor.predict(iccid, days)
        return forecast
```

#### Frontend Integration

```typescript
// components/ai/usage-forecast.tsx
'use client';
import { useSWR } from 'swr';
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend } from 'recharts';

export function UsageForecast({ iccid }: { iccid: string }) {
  const { data: forecast } = useSWR(
    `/api/v1/ai/sims/${iccid}/usage-forecast?days=7`,
    apiClient.get
  );

  if (!forecast) return <LoadingSkeleton />;

  return (
    <Card>
      <CardHeader>
        <CardTitle>7-Day Usage Forecast (AI Predicted)</CardTitle>
      </CardHeader>
      <CardContent>
        <LineChart width={600} height={300} data={forecast.predictions}>
          <XAxis dataKey="ds" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="yhat" stroke="#8884d8" name="Predicted Usage" />
          <Line type="monotone" dataKey="yhat_lower" stroke="#82ca9d" name="Lower Bound" strokeDasharray="3 3" />
          <Line type="monotone" dataKey="yhat_upper" stroke="#ffc658" name="Upper Bound" strokeDasharray="3 3" />
        </LineChart>

        {forecast.quota_exhaustion_date && (
          <Alert variant="warning" className="mt-4">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Quota Exhaustion Warning</AlertTitle>
            <AlertDescription>
              Based on current trends, this SIM will exhaust its quota on{' '}
              <strong>{format(new Date(forecast.quota_exhaustion_date), 'PPP')}</strong>{' '}
              ({forecast.days_until_exhaustion} days from now).
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}
```

#### Expected Value
- **50% reduction** in quota exhaustion incidents
- **Proactive quota management**
- **Improved customer satisfaction**
- **Optimized top-up scheduling**

---

### 2. Anomaly Detection
**Priority:** HIGH | **Effort:** MEDIUM | **ROI:** HIGH

#### Goal
Detect unusual usage patterns that may indicate fraud, device malfunction, or security issues.

#### Implementation

```python
# backend/app/ml/models/anomaly_detector.py
from sklearn.ensemble import IsolationForest
import numpy as np
import joblib

class AnomalyDetector:
    """Detect anomalous SIM behavior using Isolation Forest"""

    def __init__(self):
        self.model = IsolationForest(
            contamination=0.05,  # Expect 5% anomalies
            random_state=42,
            n_estimators=100
        )

    async def train(self):
        """Train on all SIM usage data"""
        # Fetch features for all SIMs
        features = await self.create_feature_matrix()

        # Train model
        self.model.fit(features)

        # Save model
        joblib.dump(self.model, 'models/anomaly_detector.pkl')

    async def create_feature_matrix(self) -> np.ndarray:
        """Create feature matrix for all SIMs"""
        all_sims = await session.execute(select(SIM))
        features = []

        for sim in all_sims.scalars():
            sim_features = await self.extract_features(sim.iccid)
            features.append(sim_features)

        return np.array(features)

    async def extract_features(self, iccid: str) -> List[float]:
        """Extract features for a single SIM"""
        # Get last 7 days of usage
        usage = await self.get_recent_usage(iccid, days=7)

        if not usage:
            return [0] * 8  # Return zero features

        usage_values = [u.volume for u in usage]

        return [
            np.mean(usage_values),              # Average usage
            np.std(usage_values),               # Usage variance
            np.max(usage_values),               # Peak usage
            np.min(usage_values),               # Minimum usage
            len(usage_values),                  # Active days
            usage_values[-1] if usage_values else 0,  # Latest usage
            usage_values[-1] / np.mean(usage_values) if np.mean(usage_values) > 0 else 0,  # Current vs avg
            np.percentile(usage_values, 95)     # 95th percentile
        ]

    async def detect(self, iccid: str) -> Dict:
        """Detect if SIM has anomalous behavior"""
        # Load model
        model = joblib.load('models/anomaly_detector.pkl')

        # Extract features
        features = await self.extract_features(iccid)
        features_array = np.array([features])

        # Predict anomaly score
        prediction = model.predict(features_array)[0]
        anomaly_score = model.score_samples(features_array)[0]

        is_anomaly = prediction == -1
        severity = self.calculate_severity(anomaly_score)

        # Create alert if anomaly detected
        if is_anomaly:
            await self.create_anomaly_alert(iccid, anomaly_score, features)

        return {
            "iccid": iccid,
            "is_anomaly": is_anomaly,
            "anomaly_score": float(anomaly_score),
            "severity": severity,
            "features": {
                "avg_usage": features[0],
                "usage_variance": features[1],
                "peak_usage": features[2],
                "active_days": features[4],
                "latest_vs_avg": features[6]
            },
            "recommendation": self.get_recommendation(is_anomaly, severity)
        }

    def calculate_severity(self, score: float) -> str:
        """Calculate severity level from anomaly score"""
        if score < -0.5:
            return "critical"
        elif score < -0.3:
            return "high"
        elif score < -0.1:
            return "medium"
        else:
            return "low"

    def get_recommendation(self, is_anomaly: bool, severity: str) -> str:
        """Get recommendation based on anomaly status"""
        if not is_anomaly:
            return "No action needed"

        if severity == "critical":
            return "Immediate investigation required - possible fraud or malfunction"
        elif severity == "high":
            return "Review usage patterns and contact customer if needed"
        elif severity == "medium":
            return "Monitor closely for continued anomalies"
        else:
            return "Keep watching"

# Background job to check all SIMs
@celery_app.task
async def check_all_sims_for_anomalies():
    """Run anomaly detection on all active SIMs"""
    detector = AnomalyDetector()
    active_sims = await get_active_sims()

    anomalies_found = []

    for sim in active_sims:
        result = await detector.detect(sim.iccid)
        if result['is_anomaly']:
            anomalies_found.append(result)

    logger.info(f"Anomaly detection complete: {len(anomalies_found)} anomalies found")
    return anomalies_found

# API Endpoint
@app.get("/api/v1/ai/sims/{iccid}/anomaly-check")
async def check_anomaly(iccid: str):
    """Check if SIM has anomalous behavior"""
    detector = AnomalyDetector()
    return await detector.detect(iccid)
```

#### Expected Value
- **Early fraud detection**
- **Device malfunction identification**
- **Security issue prevention**
- **Automated 24/7 monitoring**

---

### 3. Natural Language Query Interface
**Priority:** MEDIUM | **Effort:** HIGH | **ROI:** MEDIUM

#### Goal
Allow users to query data using natural language instead of complex filters.

#### Implementation

```python
# backend/app/ml/services/nl_query_service.py
import openai
from typing import Dict, Any, List
import re

class NLQueryService:
    """Convert natural language to SQL/API queries using GPT-4"""

    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def process_query(self, query: str, user_context: Dict) -> Dict[str, Any]:
        """Process natural language query"""
        # Generate SQL from natural language
        sql_query = await self.generate_sql(query)

        # Execute query safely
        results = await self.execute_query_safely(sql_query, user_context)

        # Format results with AI
        explanation = await self.format_results(query, results)

        return {
            "query": query,
            "sql": sql_query,
            "results": results,
            "explanation": explanation,
            "result_count": len(results)
        }

    async def generate_sql(self, query: str) -> str:
        """Convert natural language to SQL"""
        prompt = f"""
        Convert this natural language query to a PostgreSQL query for our IoT SIM database.

        User Query: "{query}"

        Available tables and columns:

        Table: sims
        - id (integer, primary key)
        - iccid (varchar, unique)
        - imsi (varchar)
        - msisdn (varchar)
        - status (varchar: 'active', 'inactive', 'suspended')
        - ip_address (inet)
        - operator (varchar)
        - activated_at (timestamp)
        - created_at (timestamp)

        Table: sim_usage
        - id (integer, primary key)
        - iccid (varchar, foreign key)
        - timestamp (timestamp)
        - volume (bigint, bytes)
        - direction (varchar: 'upload', 'download')

        Table: sim_quota
        - iccid (varchar, primary key)
        - type (varchar: 'data', 'sms')
        - total (bigint)
        - used (bigint)
        - remaining (bigint)

        Rules:
        1. Return ONLY the SQL query, no explanation
        2. Use safe parameterized queries
        3. Include LIMIT clause (max 100 rows)
        4. Use table aliases for readability
        5. Return user-friendly column names with AS

        SQL Query:
        """

        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a SQL expert for IoT SIM management systems. Generate safe, efficient PostgreSQL queries."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1  # Low temperature for consistent SQL
        )

        sql = response.choices[0].message.content.strip()

        # Remove markdown code blocks if present
        sql = re.sub(r'```sql\n|```', '', sql).strip()

        return sql

    async def execute_query_safely(self, sql: str, user_context: Dict) -> List[Dict]:
        """Execute SQL query with safety checks"""
        # Validate query safety
        if not self.is_safe_query(sql):
            raise ValueError("Query contains potentially dangerous operations")

        # Add user's organization filter (for multi-tenancy)
        org_id = user_context.get('org_id')
        if org_id and 'FROM sims' in sql:
            sql = sql.replace('FROM sims', f'FROM sims WHERE organization_id = {org_id}')

        # Execute query
        result = await session.execute(text(sql))
        rows = result.fetchall()

        # Convert to dict
        return [dict(row._mapping) for row in rows]

    def is_safe_query(self, sql: str) -> bool:
        """Check if SQL query is safe to execute"""
        sql_lower = sql.lower()

        # Disallow dangerous operations
        dangerous_keywords = [
            'drop', 'delete', 'truncate', 'insert', 'update',
            'create', 'alter', 'grant', 'revoke', 'exec',
            'execute', 'xp_', 'sp_'
        ]

        for keyword in dangerous_keywords:
            if keyword in sql_lower:
                return False

        # Must be SELECT query
        if not sql_lower.strip().startswith('select'):
            return False

        return True

    async def format_results(self, query: str, results: List[Dict]) -> str:
        """Format query results in natural language"""
        prompt = f"""
        User asked: "{query}"

        Query returned {len(results)} results:
        {results[:5]}  # Show first 5 results

        Provide a clear, concise summary of these results in 2-3 sentences.
        Focus on key insights and patterns.
        """

        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        return response.choices[0].message.content

# API Endpoint
@app.post("/api/v1/ai/query")
async def natural_language_query(
    query: str,
    user: User = Depends(get_current_user)
):
    """Query data using natural language"""
    nl_service = NLQueryService()
    return await nl_service.process_query(
        query,
        {"user_id": user.id, "org_id": user.organization_id}
    )
```

#### Example Queries

```python
# User types: "Show me all SIMs that used more than 1GB yesterday"
# → SELECT iccid, msisdn, SUM(volume) as total_usage
#    FROM sim_usage
#    WHERE DATE(timestamp) = CURRENT_DATE - 1
#    GROUP BY iccid, msisdn
#    HAVING SUM(volume) > 1073741824
#    LIMIT 100;

# User types: "Which SIMs are close to their quota limit?"
# → SELECT s.iccid, s.msisdn, q.used, q.total,
#    (q.used::float / q.total * 100) as usage_percent
#    FROM sims s
#    JOIN sim_quota q ON s.iccid = q.iccid
#    WHERE (q.used::float / q.total) > 0.9
#    LIMIT 100;

# User types: "What's the average daily usage for US SIMs?"
# → SELECT AVG(daily_volume) as avg_daily_usage
#    FROM (
#      SELECT DATE(timestamp) as day, SUM(volume) as daily_volume
#      FROM sim_usage u
#      JOIN sims s ON u.iccid = s.iccid
#      WHERE s.operator LIKE '%US%'
#      GROUP BY DATE(timestamp)
#    ) subquery;
```

#### Frontend Component

```typescript
// components/ai/nl-query.tsx
'use client';
import { useState } from 'react';

export function NaturalLanguageQuery() {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);

    const response = await apiClient.post('/api/v1/ai/query', { query });
    setResult(response);
    setLoading(false);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Ask a Question</CardTitle>
        <CardDescription>
          Query your data using natural language
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            placeholder="e.g., Show me all SIMs that used more than 1GB yesterday"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <Button type="submit" disabled={loading}>
            {loading ? <Loader2 className="animate-spin" /> : <Search />}
            Ask
          </Button>
        </form>

        {result && (
          <div className="mt-6 space-y-4">
            <Alert>
              <Info className="h-4 w-4" />
              <AlertTitle>Result</AlertTitle>
              <AlertDescription>{result.explanation}</AlertDescription>
            </Alert>

            <div className="bg-muted p-4 rounded-lg">
              <p className="text-sm font-mono">{result.sql}</p>
            </div>

            <DataTable
              columns={Object.keys(result.results[0] || {}).map(key => ({
                accessorKey: key,
                header: key
              }))}
              data={result.results}
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
```

#### Expected Value
- **Reduced learning curve** for new users
- **Faster data access**
- **Improved user experience**
- **Self-service analytics**

---

### 4. Intelligent Quota Recommendations
**Priority:** MEDIUM | **Effort:** LOW | **ROI:** HIGH

```python
# backend/app/ml/services/quota_recommender.py
class QuotaRecommender:
    """AI-powered quota optimization"""

    async def recommend(self, iccid: str) -> Dict:
        # Get 90 days of usage history
        usage_history = await self.get_usage_history(iccid, days=90)

        # Calculate statistics
        daily_usage = [sum(day) for day in usage_history]
        avg_monthly = np.mean(daily_usage) * 30
        p95_monthly = np.percentile(daily_usage, 95) * 30
        p99_monthly = np.percentile(daily_usage, 99) * 30

        # Get current quota
        current_quota = await self.get_current_quota(iccid)

        # Analyze utilization
        utilization = avg_monthly / current_quota.total
        peak_utilization = p95_monthly / current_quota.total

        recommendations = []

        # Under-utilized (using < 50% on average)
        if utilization < 0.5:
            recommended = int(p95_monthly * 1.2)  # 20% buffer above 95th percentile
            savings = await self.calculate_savings(current_quota.total, recommended)

            recommendations.append({
                "type": "downgrade",
                "current_quota": current_quota.total,
                "recommended_quota": recommended,
                "monthly_savings": savings,
                "reason": f"Average utilization is only {utilization*100:.1f}%. You could save {savings}/month.",
                "confidence": "high"
            })

        # Over-utilized (frequently approaching limit)
        elif peak_utilization > 0.9:
            recommended = int(p99_monthly * 1.3)  # 30% buffer above 99th percentile
            additional_cost = await self.calculate_additional_cost(current_quota.total, recommended)

            recommendations.append({
                "type": "upgrade",
                "current_quota": current_quota.total,
                "recommended_quota": recommended,
                "monthly_cost_increase": additional_cost,
                "reason": f"Usage frequently exceeds 90% of quota. Prevents service interruptions.",
                "confidence": "high"
            })

        # Perfect fit
        else:
            recommendations.append({
                "type": "maintain",
                "current_quota": current_quota.total,
                "recommended_quota": current_quota.total,
                "reason": f"Current quota is well-sized (avg utilization: {utilization*100:.1f}%)",
                "confidence": "high"
            })

        return {
            "iccid": iccid,
            "analysis": {
                "avg_monthly_usage": avg_monthly,
                "p95_monthly_usage": p95_monthly,
                "current_quota": current_quota.total,
                "avg_utilization": utilization,
                "peak_utilization": peak_utilization
            },
            "recommendations": recommendations
        }

@app.get("/api/v1/ai/sims/{iccid}/quota-recommendation")
async def get_quota_recommendation(iccid: str):
    recommender = QuotaRecommender()
    return await recommender.recommend(iccid)
```

---

### 5. Churn Prediction
**Priority:** MEDIUM | **Effort:** HIGH | **ROI:** HIGH

```python
# backend/app/ml/models/churn_predictor.py
import lightgbm as lgb
import pandas as pd

class ChurnPredictor:
    """Predict which SIMs are at risk of deactivation"""

    async def train(self):
        # Create training dataset
        features_df = await self.create_feature_dataset()

        # Split features and labels
        X = features_df.drop('churn', axis=1)
        y = features_df['churn']

        # Train LightGBM model
        train_data = lgb.Dataset(X, label=y)

        params = {
            'objective': 'binary',
            'metric': 'auc',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.9
        }

        self.model = lgb.train(
            params,
            train_data,
            num_boost_round=100
        )

        # Save model
        joblib.dump(self.model, 'models/churn_predictor.pkl')

    async def create_feature_dataset(self) -> pd.DataFrame:
        """Engineer features for churn prediction"""
        all_sims = await session.execute(select(SIM))
        features = []

        for sim in all_sims.scalars():
            features.append({
                # Temporal features
                'days_active': (date.today() - sim.activated_at).days,
                'days_since_last_activity': await self.get_days_since_activity(sim.iccid),

                # Usage features
                'avg_daily_usage': await self.get_avg_usage(sim.iccid, days=30),
                'usage_trend': await self.get_usage_trend(sim.iccid),  # Increasing/decreasing
                'usage_volatility': await self.get_usage_std(sim.iccid),

                # Quota features
                'quota_utilization': await self.get_quota_utilization(sim.iccid),
                'quota_exhaustion_count': await self.get_exhaustion_count(sim.iccid),

                # Engagement features
                'login_frequency': await self.get_login_frequency(sim.iccid),
                'support_tickets_count': await self.get_ticket_count(sim.iccid),
                'payment_delays': await self.get_payment_delay_count(sim.iccid),

                # Label
                'churn': sim.status == 'deactivated'
            })

        return pd.DataFrame(features)

    async def predict(self, iccid: str) -> Dict:
        """Predict churn probability for a SIM"""
        # Load model
        model = joblib.load('models/churn_predictor.pkl')

        # Extract features
        features = await self.get_sim_features(iccid)

        # Predict
        churn_probability = model.predict([list(features.values())])[0]

        # Classify risk level
        if churn_probability > 0.7:
            risk_level = "high"
        elif churn_probability > 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "iccid": iccid,
            "churn_probability": float(churn_probability),
            "risk_level": risk_level,
            "top_risk_factors": self.get_top_risk_factors(features, model),
            "recommended_actions": self.get_retention_actions(churn_probability),
            "predicted_churn_date": self.estimate_churn_date(churn_probability)
        }

    def get_retention_actions(self, probability: float) -> List[str]:
        """Get recommended retention actions"""
        if probability > 0.7:
            return [
                "Immediate outreach - personal call from account manager",
                "Offer 20% loyalty discount for 3 months",
                "Review usage patterns and suggest optimizations",
                "Offer free quota upgrade trial"
            ]
        elif probability > 0.4:
            return [
                "Send personalized engagement email",
                "Offer quota optimization consultation",
                "Provide usage insights and tips",
                "Offer 10% discount if they commit to 6 months"
            ]
        else:
            return [
                "Continue monitoring",
                "Send monthly value summary"
            ]

@app.get("/api/v1/ai/sims/{iccid}/churn-risk")
async def predict_churn_risk(iccid: str):
    predictor = ChurnPredictor()
    return await predictor.predict(iccid)
```

---

### 6. Automated Support Ticket Classification
**Priority:** LOW | **Effort:** MEDIUM | **ROI:** MEDIUM

```python
# backend/app/ml/services/ticket_classifier.py
from transformers import pipeline

class TicketClassifier:
    """Auto-classify and prioritize support tickets"""

    def __init__(self):
        self.classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli"
        )

    async def classify(self, ticket: SupportTicket) -> Dict:
        categories = [
            "connectivity_issue",
            "billing_question",
            "quota_exhausted",
            "activation_problem",
            "technical_support",
            "account_management",
            "feature_request",
            "complaint"
        ]

        # Classify ticket
        result = self.classifier(
            ticket.description,
            categories,
            multi_label=False
        )

        category = result['labels'][0]
        confidence = result['scores'][0]

        # Determine priority
        priority = self.calculate_priority(ticket, category, confidence)

        # Auto-assign to team
        team = self.assign_team(category)

        # Update ticket
        ticket.category = category
        ticket.priority = priority
        ticket.assigned_team = team
        ticket.confidence_score = confidence

        await session.commit()

        return {
            "ticket_id": ticket.id,
            "category": category,
            "priority": priority,
            "assigned_team": team,
            "confidence": confidence,
            "suggested_response": await self.generate_suggested_response(ticket, category)
        }

    def calculate_priority(self, ticket, category, confidence):
        # High priority categories
        if category in ["connectivity_issue", "quota_exhausted", "activation_problem"]:
            return "high"

        # Low confidence = manual review
        if confidence < 0.7:
            return "medium"

        return "low"

    def assign_team(self, category):
        team_mapping = {
            "connectivity_issue": "technical_support",
            "billing_question": "billing",
            "quota_exhausted": "customer_success",
            "activation_problem": "technical_support",
            "technical_support": "technical_support",
            "account_management": "customer_success",
            "feature_request": "product",
            "complaint": "customer_success"
        }
        return team_mapping.get(category, "general_support")
```

---

## MCP (Model Context Protocol) Integration

### Overview

Next.js 16 includes **DevTools MCP** support, enabling AI-powered development assistance directly in your development workflow.

MCP allows AI models (like Claude, GPT-4, etc.) to understand your codebase structure, run commands, access files, and provide context-aware assistance.

---

### 1. Next.js 16 DevTools MCP (Built-in)
**Priority:** HIGH | **Effort:** LOW | **Impact:** HIGH

#### What is MCP?

Model Context Protocol is an open standard that enables AI models to:
- **Understand your codebase** structure and dependencies
- **Read files** and analyze code
- **Run commands** (build, test, lint)
- **Access logs** and error messages
- **Provide context-aware suggestions**

#### Enabling MCP in Next.js 16

```javascript
// next.config.js
const nextConfig = {
  experimental: {
    // MCP is enabled by default in Next.js 16!
    devTools: {
      mcp: true,  // Enable Model Context Protocol
      mcpPort: 3001  // MCP server port (optional)
    }
  }
}
```

#### Usage Examples

**1. AI-Assisted Debugging:**
```bash
# Start Next.js dev server with MCP
npm run dev

# MCP server runs on http://localhost:3001
# Connect your AI assistant (Claude Code, GitHub Copilot, etc.)
```

**AI can now:**
- Analyze build errors and suggest fixes
- Review your code for bugs
- Suggest optimizations
- Explain complex code sections
- Generate tests based on your code

**2. Context-Aware Code Generation:**

```typescript
// AI assistant can see your project structure:
// - All components in /app
// - API routes in /app/api
// - Utility functions in /lib
// - Type definitions in /types

// You can ask:
// "Create a new API route to fetch SIM usage data"
// AI generates code that matches your existing patterns!
```

---

### 2. Custom MCP Server for Backend
**Priority:** MEDIUM | **Effort:** MEDIUM | **Impact:** MEDIUM

#### Implementation

```python
# backend/app/mcp/server.py
from fastapi import FastAPI, WebSocket
import json

mcp_app = FastAPI()

class MCPServer:
    """Model Context Protocol server for AI assistance"""

    def __init__(self):
        self.tools = {
            "read_file": self.read_file,
            "list_files": self.list_files,
            "run_tests": self.run_tests,
            "analyze_logs": self.analyze_logs,
            "get_metrics": self.get_metrics
        }

    async def read_file(self, path: str) -> str:
        """Read file contents"""
        with open(path, 'r') as f:
            return f.read()

    async def list_files(self, directory: str = ".") -> List[str]:
        """List files in directory"""
        import os
        return os.listdir(directory)

    async def run_tests(self, test_path: str = "tests/") -> Dict:
        """Run pytest and return results"""
        import subprocess
        result = subprocess.run(
            ["pytest", test_path, "-v", "--json-report"],
            capture_output=True
        )
        return json.loads(result.stdout)

    async def analyze_logs(self, service: str, lines: int = 100) -> List[str]:
        """Get recent logs for analysis"""
        # Fetch from Loki/logging system
        logs = await get_logs(service, lines)
        return logs

    async def get_metrics(self, metric_name: str) -> Dict:
        """Get Prometheus metrics"""
        metrics = await prometheus_client.query(metric_name)
        return metrics

@mcp_app.websocket("/mcp")
async def mcp_websocket(websocket: WebSocket):
    """MCP WebSocket endpoint for AI assistants"""
    await websocket.accept()

    server = MCPServer()

    while True:
        # Receive request from AI
        data = await websocket.receive_json()

        tool = data.get("tool")
        params = data.get("params", {})

        # Execute tool
        if tool in server.tools:
            result = await server.tools[tool](**params)
            await websocket.send_json({
                "status": "success",
                "result": result
            })
        else:
            await websocket.send_json({
                "status": "error",
                "message": f"Unknown tool: {tool}"
            })
```

---

### 3. MCP Integration with AI Features
**Priority:** MEDIUM | **Effort:** LOW | **Impact:** HIGH

Combine MCP with AI features for enhanced capabilities:

```python
# backend/app/mcp/ai_integration.py
class MCPAIIntegration:
    """Integrate MCP with AI features for enhanced assistance"""

    async def get_codebase_context(self) -> Dict:
        """Provide AI with full codebase context"""
        return {
            "project_type": "IoT SIM Management Platform",
            "tech_stack": {
                "backend": "FastAPI + PostgreSQL + Redis + TimescaleDB",
                "frontend": "Next.js 16 + React 19 + TypeScript",
                "ml": "Prophet + LightGBM + Isolation Forest + OpenAI"
            },
            "api_routes": await self.get_api_routes(),
            "database_schema": await self.get_db_schema(),
            "ml_models": await self.get_ml_models(),
            "metrics": await self.get_available_metrics()
        }

    async def suggest_optimizations(self) -> List[Dict]:
        """AI-powered code optimization suggestions"""
        # Analyze codebase with AI
        context = await self.get_codebase_context()

        # Send to OpenAI for analysis
        response = await openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{
                "role": "system",
                "content": "You are a code optimization expert"
            }, {
                "role": "user",
                "content": f"Analyze this codebase and suggest optimizations:\n{context}"
            }]
        )

        return parse_optimization_suggestions(response)
```

---

### 4. MCP Configuration Files
**Priority:** LOW | **Effort:** LOW

```json
// .mcp/config.json
{
  "name": "IOT SIM Platform MCP Server",
  "version": "1.0.0",
  "tools": [
    {
      "name": "read_file",
      "description": "Read contents of a file",
      "parameters": {
        "path": "string"
      }
    },
    {
      "name": "run_tests",
      "description": "Run pytest tests and return results",
      "parameters": {
        "test_path": "string"
      }
    },
    {
      "name": "analyze_logs",
      "description": "Fetch and analyze application logs",
      "parameters": {
        "service": "string",
        "lines": "integer"
      }
    },
    {
      "name": "get_ai_insights",
      "description": "Get AI insights for a specific SIM",
      "parameters": {
        "iccid": "string",
        "insight_type": "string"
      }
    }
  ],
  "endpoints": {
    "websocket": "ws://localhost:8000/mcp",
    "http": "http://localhost:8000/api/v1/mcp"
  }
}
```

---

### 5. MCP Benefits for Development

| Feature | Benefit | Example |
|---------|---------|---------|
| **Context-Aware Suggestions** | AI understands your patterns | "Create a new SIM endpoint" → generates code matching existing style |
| **Automated Debugging** | AI analyzes errors and logs | "Why is test X failing?" → AI reads logs and suggests fix |
| **Code Review** | AI reviews PRs | "Review this code" → AI checks patterns, suggests improvements |
| **Documentation** | AI generates docs from code | "Document this function" → AI writes comprehensive docs |
| **Refactoring** | AI suggests improvements | "Optimize this query" → AI suggests indexes, joins |
| **Test Generation** | AI writes tests | "Generate tests for UserService" → AI creates comprehensive tests |

---

## New Features

### 1. Real-Time Dashboard (WebSocket)
**Priority:** HIGH | **Effort:** MEDIUM

```python
# backend/app/api/v1/websocket.py
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    await manager.connect(websocket)

    # Subscribe to Redis pub/sub for real-time events
    pubsub = redis.pubsub()
    await pubsub.subscribe("sim_events")

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                await websocket.send_json(json.loads(message["data"]))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await pubsub.unsubscribe("sim_events")

# Publish events to Redis
async def publish_sim_event(event_type: str, data: dict):
    await redis.publish("sim_events", json.dumps({
        "type": event_type,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }))

# Example: Publish when SIM status changes
@app.patch("/api/v1/sims/{iccid}/status")
async def update_sim_status(iccid: str, status: str):
    # Update database
    await SIMService.update_status(iccid, status)

    # Publish event
    await publish_sim_event("status_change", {
        "iccid": iccid,
        "new_status": status
    })

    return {"success": True}
```

**Frontend:**
```typescript
// hooks/use-websocket.ts
export function useWebSocket(url: string) {
  const [data, setData] = useState(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const ws = new WebSocket(url);

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setData(data);
    };

    return () => ws.close();
  }, [url]);

  return { data, connected };
}

// components/realtime-dashboard.tsx
export function RealtimeDashboard() {
  const { data: event } = useWebSocket('ws://localhost:8000/ws/dashboard');

  useEffect(() => {
    if (event) {
      toast({
        title: event.type,
        description: JSON.stringify(event.data)
      });
    }
  }, [event]);

  return <div>Real-time updates enabled</div>;
}
```

---

### 2. Advanced Analytics & Reporting
**Priority:** HIGH | **Effort:** HIGH

```python
@app.get("/api/v1/reports/usage")
async def generate_usage_report(
    start_date: date,
    end_date: date,
    format: Literal["json", "csv", "pdf", "excel"] = "json",
    group_by: Literal["day", "week", "month"] = "day"
):
    # Query TimescaleDB for aggregated data
    query = select(
        func.time_bucket(group_by, SIMUsage.timestamp).label('period'),
        func.sum(SIMUsage.volume).label('total_volume'),
        func.count(distinct(SIMUsage.iccid)).label('active_sims'),
        func.avg(SIMUsage.volume).label('avg_volume_per_event')
    ).where(
        SIMUsage.timestamp.between(start_date, end_date)
    ).group_by('period').order_by('period')

    results = await session.execute(query)
    data = results.all()

    if format == "json":
        return data
    elif format == "csv":
        return generate_csv(data)
    elif format == "pdf":
        return generate_pdf_report(data)
    elif format == "excel":
        return generate_excel_report(data)
```

---

### 3. Alert Management System
**Priority:** MEDIUM | **Effort:** MEDIUM

```python
# backend/app/models/alert.py
class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    condition = Column(JSONB)  # {"metric": "usage", "operator": ">", "threshold": 1000}
    notification_channels = Column(ARRAY(String))  # ["email", "slack", "webhook"]
    enabled = Column(Boolean, default=True)
    cooldown_minutes = Column(Integer, default=60)

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True)
    rule_id = Column(Integer, ForeignKey("alert_rules.id"))
    iccid = Column(String)
    severity = Column(String)  # low, medium, high, critical
    message = Column(Text)
    triggered_at = Column(DateTime, default=datetime.now)
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(Integer, ForeignKey("users.id"))
    acknowledged_at = Column(DateTime)

# backend/app/services/alert_service.py
class AlertService:
    async def evaluate_rules(self, sim: SIM):
        rules = await self.get_active_rules()

        for rule in rules:
            if await self.evaluate_condition(rule.condition, sim):
                # Check cooldown
                if await self.is_in_cooldown(rule.id, sim.iccid):
                    continue

                # Create alert
                alert = await self.create_alert(rule, sim)

                # Send notifications
                await self.send_notifications(rule, alert)

    async def evaluate_condition(self, condition: dict, sim: SIM) -> bool:
        metric = condition["metric"]
        operator = condition["operator"]
        threshold = condition["threshold"]

        # Get metric value
        if metric == "usage":
            value = await self.get_sim_usage(sim.iccid)
        elif metric == "quota_remaining":
            quota = await self.get_quota(sim.iccid)
            value = quota.remaining
        elif metric == "quota_utilization":
            quota = await self.get_quota(sim.iccid)
            value = quota.used / quota.total if quota.total > 0 else 0

        # Evaluate condition
        if operator == ">":
            return value > threshold
        elif operator == "<":
            return value < threshold
        elif operator == "==":
            return value == threshold
        elif operator == ">=":
            return value >= threshold
        elif operator == "<=":
            return value <= threshold

        return False

    async def send_notifications(self, rule: AlertRule, alert: Alert):
        for channel in rule.notification_channels:
            if channel == "email":
                await self.send_email_alert(rule, alert)
            elif channel == "slack":
                await self.send_slack_alert(rule, alert)
            elif channel == "webhook":
                await self.send_webhook_alert(rule, alert)
            elif channel == "sms":
                await self.send_sms_alert(rule, alert)
```

---

### 4. Bulk Operations
**Priority:** MEDIUM | **Effort:** LOW

```python
@app.post("/api/v1/sims/import")
async def import_sims(file: UploadFile):
    """Import SIMs from CSV/Excel"""
    # Read file
    content = await file.read()
    df = pd.read_csv(BytesIO(content))

    # Validate
    errors = []
    valid_rows = []

    for idx, row in df.iterrows():
        try:
            sim = SIMCreate(**row.to_dict())
            valid_rows.append(sim)
        except ValidationError as e:
            errors.append({"row": idx + 1, "errors": e.errors()})

    # Bulk insert
    if valid_rows:
        results = await SIMService.bulk_create(valid_rows)

    return {
        "imported": len(valid_rows),
        "failed": len(errors),
        "errors": errors
    }

@app.post("/api/v1/sims/bulk-activate")
async def bulk_activate(iccids: List[str]):
    """Activate multiple SIMs"""
    tasks = [SIMService.activate(iccid) for iccid in iccids]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    successful = [r for r in results if not isinstance(r, Exception)]
    failed = [r for r in results if isinstance(r, Exception)]

    return {
        "activated": len(successful),
        "failed": len(failed),
        "results": successful
    }
```

---

### 5. Multi-Tenancy / Organization Support
**Priority:** LOW | **Effort:** HIGH

```python
# Add organization model
class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    settings = Column(JSONB, default={})
    billing_email = Column(String)
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    users = relationship("User", back_populates="organization")
    sims = relationship("SIM", back_populates="organization")

# Update SIM model
class SIM(Base):
    # ... existing fields
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    organization = relationship("Organization", back_populates="sims")

# Middleware to enforce organization isolation
@app.middleware("http")
async def organization_middleware(request: Request, call_next):
    user = request.state.user

    if user:
        # Set organization context
        request.state.org_id = user.organization_id

    response = await call_next(request)
    return response

# Apply org filter to all queries
async def get_sims(
    session: AsyncSession,
    user: User = Depends(get_current_user)
):
    query = select(SIM).where(SIM.organization_id == user.organization_id)
    results = await session.execute(query)
    return results.scalars().all()
```

---

## Infrastructure Enhancements

### 1. Distributed Tracing (OpenTelemetry)
**Priority:** MEDIUM | **Effort:** MEDIUM

```python
# backend/app/telemetry.py
from opentelemetry import trace
from opentelemetry.exporter.jaeger import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

def setup_telemetry(app: FastAPI):
    # Set up tracer
    trace.set_tracer_provider(TracerProvider())

    # Configure Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name="jaeger",
        agent_port=6831,
    )

    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(jaeger_exporter)
    )

    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)

# Usage in endpoints
@app.get("/sims/{iccid}")
async def get_sim(iccid: str):
    tracer = trace.get_tracer(__name__)

    with tracer.start_as_current_span("get_sim"):
        sim = await SIMService.get_sim(iccid)

        with tracer.start_as_current_span("get_usage"):
            usage = await SIMService.get_usage(iccid)

        return {"sim": sim, "usage": usage}
```

---

### 2. Message Queue (Celery)
**Priority:** MEDIUM | **Effort:** MEDIUM

```python
# backend/app/tasks/celery_app.py
from celery import Celery

celery_app = Celery(
    "iot_platform",
    broker="redis://redis:6379/1",
    backend="redis://redis:6379/2"
)

@celery_app.task
async def sync_sims_from_once():
    """Long-running sync operation"""
    sims = await OnceClient().get_all_sims()

    for sim in sims:
        await SIMService.upsert_sim(sim)

@celery_app.task
async def generate_monthly_report():
    """Generate and email monthly reports"""
    for org in await get_all_organizations():
        report = await generate_report(org.id)
        await send_email(org.billing_email, report)

# Schedule tasks
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'sync-sims-hourly': {
        'task': 'sync_sims_from_once',
        'schedule': crontab(minute=0),  # Every hour
    },
    'monthly-reports': {
        'task': 'generate_monthly_report',
        'schedule': crontab(day_of_month=1, hour=0, minute=0),
    }
}
```

---

### 3. API Gateway (Kong/Traefik)
**Priority:** LOW | **Effort:** HIGH

```yaml
# docker-compose.yml - Add Kong
services:
  kong:
    image: kong:latest
    environment:
      KONG_DATABASE: postgres
      KONG_PG_HOST: postgres
      KONG_PG_DATABASE: kong
    ports:
      - "8000:8000"  # Proxy
      - "8001:8001"  # Admin API
    depends_on:
      - postgres

  # Configure routes
  kong-config:
    image: kong:latest
    command: >
      sh -c "
        kong config db_import /kong.yml
      "
    volumes:
      - ./kong.yml:/kong.yml
```

```yaml
# kong.yml
_format_version: "2.1"
services:
  - name: backend-api
    url: http://backend:8000
    routes:
      - name: api-route
        paths:
          - /api
    plugins:
      - name: rate-limiting
        config:
          minute: 100
          hour: 1000
      - name: jwt
        config:
          key_claim_name: kid
```

---

### 4. Database Read Replicas
**Priority:** LOW | **Effort:** HIGH

```python
# backend/app/database.py
write_engine = create_async_engine(DATABASE_URL_PRIMARY)
read_engine = create_async_engine(DATABASE_URL_REPLICA)

async def get_session(readonly: bool = False):
    engine = read_engine if readonly else write_engine
    async with AsyncSession(engine) as session:
        yield session

# Usage
@app.get("/sims")
async def get_sims(session: AsyncSession = Depends(lambda: get_session(readonly=True))):
    # Query goes to read replica
    sims = await session.execute(select(SIM))
    return sims.scalars().all()

@app.post("/sims")
async def create_sim(sim: SIMCreate, session: AsyncSession = Depends(lambda: get_session(readonly=False))):
    # Write goes to primary
    new_sim = SIM(**sim.dict())
    session.add(new_sim)
    await session.commit()
    return new_sim
```

---

## Security Improvements

### 1. Rate Limiting Enforcement
**Priority:** HIGH | **Effort:** LOW

```python
# backend/app/middleware/rate_limit.py
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://redis:6379/3"
)

# Apply to endpoints
@app.get("/api/v1/sims")
@limiter.limit("100/minute")
async def get_sims(request: Request):
    pass

# Per-user rate limiting
async def get_user_id(request: Request):
    user = request.state.user
    return user.id if user else get_remote_address(request)

@app.post("/api/v1/sims")
@limiter.limit("10/minute", key_func=get_user_id)
async def create_sim(request: Request):
    pass
```

---

### 2. Enhanced Input Validation
**Priority:** HIGH | **Effort:** LOW

```python
from pydantic import validator, Field

class SIMCreate(BaseModel):
    iccid: str = Field(..., regex=r'^\d{19,20}$')
    msisdn: str = Field(..., regex=r'^\+?[1-9]\d{1,14}$')

    @validator('iccid')
    def validate_iccid(cls, v):
        # Luhn algorithm check
        if not luhn_check(v):
            raise ValueError('Invalid ICCID checksum')
        return v
```

---

### 3. Audit Logging
**Priority:** MEDIUM | **Effort:** MEDIUM

```python
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    action = Column(String)  # CREATE, UPDATE, DELETE, READ
    resource_type = Column(String)  # SIM, User, etc.
    resource_id = Column(String)
    changes = Column(JSONB)
    ip_address = Column(String)
    user_agent = Column(String)
    timestamp = Column(DateTime, default=datetime.now)

# Middleware
@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    response = await call_next(request)

    # Log if write operation
    if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
        await log_audit(
            user_id=request.state.user.id if hasattr(request.state, 'user') else None,
            action=request.method,
            resource_type=extract_resource_type(request.url.path),
            ip_address=request.client.host,
            user_agent=request.headers.get('user-agent')
        )

    return response
```

---

## Implementation Roadmap

### Phase 1: Performance & Core Features (Weeks 1-4)

**Week 1-2: Performance Optimizations**
- [ ] Implement Redis caching layer
- [ ] Add response compression
- [ ] Optimize database queries (N+1 fixes)
- [ ] Add cursor-based pagination
- [ ] Implement connection pool optimization

**Week 3-4: React Frontend Core**
- [ ] Complete authentication flow
- [ ] Create SIM list page with filters
- [ ] Create SIM detail page
- [ ] Set up Zustand state management
- [ ] Implement SWR data fetching hooks

**Deliverables:**
- 50% faster API responses
- Functional React authentication
- SIM management pages (list, detail, create)

---

### Phase 2: AI Features - Basic (Weeks 5-8)

**Week 5-6: Predictive Analytics**
- [ ] Implement usage forecasting (Prophet)
- [ ] Create forecast API endpoints
- [ ] Build frontend forecast charts
- [ ] Add quota exhaustion alerts

**Week 7-8: Anomaly Detection**
- [ ] Train anomaly detection model (Isolation Forest)
- [ ] Create anomaly API endpoints
- [ ] Build anomaly alert system
- [ ] Add frontend anomaly indicators

**Deliverables:**
- 7-day usage forecasting
- Automated anomaly detection
- Real-time alerts for anomalies

---

### Phase 3: Advanced Features (Weeks 9-12)

**Week 9-10: Real-Time & Analytics**
- [ ] Implement WebSocket real-time updates
- [ ] Build real-time dashboard
- [ ] Create advanced analytics reports
- [ ] Add report export (PDF, Excel, CSV)

**Week 11-12: AI Enhancement**
- [ ] Natural language query interface
- [ ] Quota recommendations
- [ ] Churn prediction model
- [ ] Model training pipeline

**Deliverables:**
- Real-time dashboard with WebSocket
- AI-powered insights and recommendations
- Comprehensive analytics and reporting

---

### Phase 4: Enterprise Features (Weeks 13-16)

**Week 13-14: Infrastructure**
- [ ] Add distributed tracing (OpenTelemetry)
- [ ] Implement message queue (Celery)
- [ ] Set up log aggregation
- [ ] Database read replicas

**Week 15-16: Enterprise Features**
- [ ] Multi-tenancy support
- [ ] Alert management system
- [ ] Bulk operations
- [ ] Audit logging
- [ ] MCP integration enhancements

**Deliverables:**
- Multi-tenant SaaS platform
- Enterprise-grade observability
- Advanced alerting and automation

---

## Cost & ROI Analysis

### Development Costs

| Phase | Duration | Effort | Estimated Cost |
|-------|----------|--------|----------------|
| Phase 1: Performance & Core | 4 weeks | 1 developer | $16,000 |
| Phase 2: AI Features - Basic | 4 weeks | 1 developer + ML engineer | $24,000 |
| Phase 3: Advanced Features | 4 weeks | 1 developer + ML engineer | $24,000 |
| Phase 4: Enterprise Features | 4 weeks | 2 developers | $32,000 |
| **Total** | **16 weeks** | | **$96,000** |

### Infrastructure Costs (Monthly)

| Service | Purpose | Cost/Month |
|---------|---------|------------|
| GPU Instance (g4dn.xlarge) | ML model training | $500 |
| OpenAI API (GPT-4) | NL queries, ticket classification | $300 |
| Additional Redis | Caching, WebSocket | $50 |
| Monitoring (Datadog/NewRelic) | APM, logging | $200 |
| S3 Storage | Model storage | $50 |
| **Total** | | **$1,100/month** |

### Expected ROI

#### Efficiency Gains
- **30% reduction in customer churn** → +$50,000/year revenue
- **50% reduction in support costs** → +$30,000/year savings
- **80% reduction in manual work** → +$40,000/year savings
- **20% improvement in quota utilization** → +$25,000/year revenue

#### Total Expected Annual Benefit
**$145,000/year**

#### ROI Calculation
- **Total Investment:** $96,000 (development) + $13,200/year (infrastructure)
- **Annual Benefit:** $145,000
- **Net Benefit (Year 1):** $35,800
- **ROI (Year 1):** 33%
- **Payback Period:** ~9 months

---

## Success Metrics

### Performance Metrics
- API response time: **< 100ms** (p95)
- Database query time: **< 50ms** (p95)
- Frontend load time: **< 2s** (TTI)
- Cache hit rate: **> 80%**

### AI Metrics
- Forecast accuracy: **> 85%** (MAPE < 15%)
- Anomaly detection precision: **> 90%**
- Churn prediction AUC: **> 0.85**
- NL query success rate: **> 95%**

### Business Metrics
- Customer churn: **< 5%** (down from 7%)
- Support ticket resolution time: **< 2 hours** (down from 4)
- Quota exhaustion incidents: **< 1%** (down from 2%)
- User satisfaction (NPS): **> 50**

---

## Conclusion

This document outlines a comprehensive improvement plan for the IOT SIM Platform, covering:

1. **Performance Optimizations** - 50% faster, 3x throughput
2. **Complete React Frontend** - Production-ready user interface
3. **AI/ML Features** - Predictive analytics, anomaly detection, NL queries
4. **MCP Integration** - AI-assisted development with Next.js 16
5. **New Features** - Real-time updates, advanced analytics, multi-tenancy
6. **Infrastructure** - Distributed tracing, message queues, observability

**Priority Focus:**
1. Enable caching layer (quick win)
2. Complete React frontend (critical)
3. Implement basic AI features (high ROI)
4. Add real-time capabilities (competitive advantage)

**Next Steps:**
1. Review and prioritize features with stakeholders
2. Begin Phase 1 implementation
3. Set up CI/CD for continuous delivery
4. Monitor metrics and iterate

The platform has an **excellent foundation** with Next.js 16 and a solid backend. These improvements will transform it into a **world-class, AI-powered IoT SIM management platform**.

---

**Document Status:** Complete ✅
**Last Updated:** 2025-11-18
**Version:** 1.0
