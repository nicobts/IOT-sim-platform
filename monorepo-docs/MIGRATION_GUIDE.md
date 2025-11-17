# IOT SIM Platform - Migration Guide
## Step-by-Step Transformation to Monorepo

**Version:** 1.0.0
**Last Updated:** 2024-11-17
**Branch:** `IOT-sim-platform-fullstack-monorepo`

---

## Table of Contents

1. [Before You Begin](#before-you-begin)
2. [Phase 1: Backend Restructure](#phase-1-backend-restructure)
3. [Phase 2: Root Infrastructure](#phase-2-root-infrastructure)
4. [Phase 3: React Dashboard](#phase-3-react-dashboard)
5. [Phase 4: Streamlit Admin](#phase-4-streamlit-admin)
6. [Phase 5: Monitoring Stack](#phase-5-monitoring-stack)
7. [Phase 6: CI/CD Pipelines](#phase-6-cicd-pipelines)
8. [Phase 7: Documentation](#phase-7-documentation)
9. [Testing & Validation](#testing--validation)
10. [Rollback Procedures](#rollback-procedures)

---

## Before You Begin

### Prerequisites

✅ **Required:**
- Git knowledge
- Docker & Docker Compose installed
- Node.js 18+ (for React frontend)
- Python 3.11+ (already installed)
- 4GB+ free disk space

✅ **Recommended:**
- VS Code with extensions:
  - Python
  - ESLint
  - Prettier
  - Docker
- Postman or similar API client

### Backup Current State

```bash
# 1. Ensure you're on the new branch
git checkout IOT-sim-platform-fullstack-monorepo

# 2. Create a backup tag
git tag backup-before-monorepo-$(date +%Y%m%d)
git push origin backup-before-monorepo-$(date +%Y%m%d)

# 3. Backup database (if running)
docker-compose exec db pg_dump -U user iot_sim_db > backup_$(date +%Y%m%d).sql

# 4. Stop all running containers
docker-compose down
```

### Verify Current Structure

```bash
# Check current directory structure
ls -la

# Expected output:
# app/
# tests/
# docs/
# scripts/
# docker-compose.yml
# Dockerfile
# requirements.txt
# ...
```

---

## Phase 1: Backend Restructure

**Goal:** Move existing backend to `backend/` directory

**Duration:** 1-2 hours

**Risk Level:** 🟡 Medium (careful with imports)

### Step 1.1: Create Backend Directory

```bash
# Create backend directory structure
mkdir -p backend

echo "✅ Created backend/ directory"
```

### Step 1.2: Move Files to Backend

```bash
# Move application code
git mv app backend/
git mv tests backend/
git mv alembic backend/

# Move configuration files
git mv Dockerfile backend/
git mv docker-compose.yml backend/
git mv requirements.txt backend/
git mv requirements-dev.txt backend/
git mv alembic.ini backend/

# Move environment template
git mv .env.example backend/

echo "✅ Moved files to backend/"
```

### Step 1.3: Update Import Paths

**Option A: Automated (Recommended)**

```bash
# Create update script
cat > backend/update_imports.py << 'EOF'
#!/usr/bin/env python3
"""Update import paths after backend restructure."""
import os
import re
from pathlib import Path

def update_file(filepath):
    """Update imports in a single file."""
    with open(filepath, 'r') as f:
        content = f.read()

    # Update imports
    updated = content
    updated = re.sub(r'from app\.', 'from backend.app.', updated)
    updated = re.sub(r'import app\.', 'import backend.app.', updated)

    # Only write if changed
    if updated != content:
        with open(filepath, 'w') as f:
            f.write(updated)
        print(f"Updated: {filepath}")

def main():
    backend_dir = Path("backend")

    # Update all Python files
    for pyfile in backend_dir.rglob("*.py"):
        update_file(pyfile)

    print("✅ All imports updated")

if __name__ == "__main__":
    main()
EOF

chmod +x backend/update_imports.py
python3 backend/update_imports.py
```

**Option B: Manual**

Update these key files:

1. **backend/app/main.py**
   ```python
   # OLD:
   from app.api.v1 import api_router
   from app.core.config import settings

   # NEW:
   from backend.app.api.v1 import api_router
   from backend.app.core.config import settings
   ```

2. **backend/alembic/env.py**
   ```python
   # OLD:
   from app.db.base import Base
   from app.core.config import settings

   # NEW:
   from backend.app.db.base import Base
   from backend.app.core.config import settings
   ```

3. **backend/tests/conftest.py**
   ```python
   # OLD:
   from app.db.session import get_db
   from app.main import app

   # NEW:
   from backend.app.db.session import get_db
   from backend.app.main import app
   ```

### Step 1.4: Update Alembic Configuration

```bash
# Edit backend/alembic.ini
sed -i 's|script_location = alembic|script_location = backend/alembic|g' backend/alembic.ini
sed -i 's|prepend_sys_path = .|prepend_sys_path = ..|g' backend/alembic.ini
```

### Step 1.5: Update Docker Configuration

**backend/Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini .

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**backend/docker-compose.yml:**
```yaml
version: '3.8'

services:
  db:
    image: timescale/timescaledb:latest-pg15
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: iot_sim_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  api:
    build: .
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    env_file:
      - .env

volumes:
  postgres_data:
```

### Step 1.6: Create Backend README

```bash
cat > backend/README.md << 'EOF'
# IOT SIM Platform - Backend API

FastAPI backend service for IOT SIM management.

## Quick Start

```bash
# From backend/ directory
docker-compose up -d

# Run migrations
docker-compose exec api alembic upgrade head

# Create admin user
docker-compose exec api python scripts/create_admin.py

# Access API
open http://localhost:8000/docs
```

## Development

```bash
# Install dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Lint code
black app/ tests/
isort app/ tests/
flake8 app/ tests/
mypy app/
```

## See Also

- [API Usage Guide](../docs/API_USAGE_GUIDE.md)
- [Architecture](../monorepo-docs/MONOREPO_ARCHITECTURE.md)
- [Main README](../README.md)
EOF
```

### Step 1.7: Test Backend Independently

```bash
cd backend

# Start services
docker-compose up -d

# Wait for services
sleep 10

# Run migrations
docker-compose exec api alembic upgrade head

# Run tests
docker-compose exec api pytest

# Check API
curl http://localhost:8000/health

# Expected output:
# {"status":"healthy","service":"FastAPI IOT SIM Management Server",...}

cd ..
```

### Step 1.8: Commit Changes

```bash
git add backend/
git commit -m "Phase 1: Restructure backend to backend/ directory

- Moved all backend code to backend/
- Updated import paths
- Updated Dockerfile and docker-compose.yml
- Created backend README
- All tests passing
"
```

---

## Phase 2: Root Infrastructure

**Goal:** Create monorepo-level infrastructure

**Duration:** 2-3 hours

**Risk Level:** 🟡 Medium

### Step 2.1: Create Root Docker Compose

```bash
cat > docker-compose.yml << 'EOF'
version: '3.8'

networks:
  iot-network:
    driver: bridge

volumes:
  postgres_data:
  grafana_data:
  prometheus_data:

services:
  # Database
  db:
    image: timescale/timescaledb:latest-pg15
    container_name: iot-db
    environment:
      POSTGRES_USER: ${DATABASE_USER:-user}
      POSTGRES_PASSWORD: ${DATABASE_PASSWORD:-password}
      POSTGRES_DB: ${DATABASE_NAME:-iot_sim_db}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init_timescaledb.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - iot-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: iot-redis
    networks:
      - iot-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Backend API
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: iot-backend
    volumes:
      - ./backend:/app
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:password@db:5432/iot_sim_db
      - REDIS_URL=redis://redis:6379/0
      - ENVIRONMENT=development
      - DEBUG=true
      - RELOAD=true
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - iot-network
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: iot-nginx
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - backend
    networks:
      - iot-network

  # Prometheus
  prometheus:
    image: prom/prometheus:latest
    container_name: iot-prometheus
    volumes:
      - ./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    ports:
      - "9090:9090"
    networks:
      - iot-network

  # Grafana
  grafana:
    image: grafana/grafana:latest
    container_name: iot-grafana
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning:ro
      - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards:ro
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
      - GF_SERVER_ROOT_URL=http://localhost:3001
    ports:
      - "3001:3000"
    depends_on:
      - prometheus
    networks:
      - iot-network
EOF

echo "✅ Created root docker-compose.yml"
```

### Step 2.2: Create Production Docker Compose

```bash
cat > docker-compose.prod.yml << 'EOF'
version: '3.8'

networks:
  iot-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
  grafana_data:
  prometheus_data:

services:
  db:
    image: timescale/timescaledb:latest-pg15
    container_name: iot-db-prod
    environment:
      POSTGRES_USER: ${DATABASE_USER}
      POSTGRES_PASSWORD: ${DATABASE_PASSWORD}
      POSTGRES_DB: ${DATABASE_NAME}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - iot-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G

  redis:
    image: redis:7-alpine
    container_name: iot-redis-prod
    command: redis-server --requirepass ${REDIS_PASSWORD} --maxmemory 512mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    networks:
      - iot-network
    restart: unless-stopped

  backend:
    image: ${DOCKER_REGISTRY}/iot-backend:${VERSION}
    container_name: iot-backend-prod
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - ONCE_CLIENT_ID=${ONCE_CLIENT_ID}
      - ONCE_CLIENT_SECRET=${ONCE_CLIENT_SECRET}
      - SECRET_KEY=${SECRET_KEY}
      - ENVIRONMENT=production
      - DEBUG=false
    depends_on:
      - db
      - redis
    networks:
      - iot-network
    restart: unless-stopped
    deploy:
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

  nginx:
    image: nginx:alpine
    container_name: iot-nginx-prod
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - backend
    networks:
      - iot-network
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    container_name: iot-prometheus-prod
    volumes:
      - ./monitoring/prometheus:/etc/prometheus:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
    networks:
      - iot-network
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: iot-grafana-prod
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana:/etc/grafana:ro
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_SERVER_ROOT_URL=${GRAFANA_URL}
      - GF_INSTALL_PLUGINS=
    networks:
      - iot-network
    restart: unless-stopped
EOF

echo "✅ Created docker-compose.prod.yml"
```

### Step 2.3: Update Nginx Configuration

```bash
mkdir -p nginx/conf.d

# Main Nginx config
cat > nginx/nginx.conf << 'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    keepalive_timeout 65;
    gzip on;

    include /etc/nginx/conf.d/*.conf;
}
EOF

# Backend routing
cat > nginx/conf.d/backend.conf << 'EOF'
upstream backend_api {
    least_conn;
    server backend:8000;
}

server {
    listen 80;
    server_name localhost;

    # Backend API
    location /api/ {
        proxy_pass http://backend_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # API Docs
    location /docs {
        proxy_pass http://backend_api;
        proxy_set_header Host $host;
    }

    # Health check
    location /health {
        proxy_pass http://backend_api;
    }

    # Monitoring (Grafana)
    location /monitoring/ {
        proxy_pass http://grafana:3000/;
        proxy_set_header Host $host;
    }
}
EOF

echo "✅ Created Nginx configuration"
```

### Step 2.4: Create Root Environment Template

```bash
cat > .env.example << 'EOF'
# ============================================
# IOT SIM Platform - Environment Configuration
# ============================================

# Project Info
PROJECT_NAME="IOT SIM Management Platform"
ENVIRONMENT=development
VERSION=1.0.0

# Database
DATABASE_USER=user
DATABASE_PASSWORD=password
DATABASE_NAME=iot_sim_db
DATABASE_URL=postgresql+asyncpg://user:password@db:5432/iot_sim_db

# Redis
REDIS_PASSWORD=
REDIS_URL=redis://redis:6379/0

# 1NCE API (REQUIRED)
ONCE_CLIENT_ID=your-1nce-client-id
ONCE_CLIENT_SECRET=your-1nce-client-secret

# Backend API
SECRET_KEY=your-secret-key-change-in-production
API_V1_PREFIX=/api/v1
DEBUG=true
RELOAD=true

# Grafana
GRAFANA_PASSWORD=admin
GRAFANA_URL=http://localhost:3001

# Docker Registry (Production)
DOCKER_REGISTRY=your-registry
EOF

echo "✅ Created .env.example"
```

### Step 2.5: Update .gitignore

```bash
cat >> .gitignore << 'EOF'

# Monorepo specific
*.env
!.env.example
*.env.local
*.env.*.local

# Service specific
backend/.env
frontend-react/.env.local
frontend-streamlit/.env

# Build artifacts
**/dist/
**/build/
**/.next/
**/node_modules/

# Logs
**/logs/
**/*.log

# IDE
.vscode/settings.json
.idea/

# Docker
docker-compose.override.yml

# OS
.DS_Store
Thumbs.db
EOF

echo "✅ Updated .gitignore"
```

### Step 2.6: Test Root Infrastructure

```bash
# Start all services
docker-compose up -d

# Wait for services
sleep 15

# Check all services are healthy
docker-compose ps

# Test backend through Nginx
curl http://localhost/health

# Check Grafana
curl http://localhost:3001

# Check Prometheus
curl http://localhost:9090

echo "✅ All services running"
```

### Step 2.7: Commit Changes

```bash
git add docker-compose.yml docker-compose.prod.yml nginx/ .env.example .gitignore
git commit -m "Phase 2: Add root-level infrastructure

- Created root docker-compose.yml for all services
- Created production docker-compose.prod.yml
- Configured Nginx reverse proxy
- Created environment templates
- Updated .gitignore
"
```

---

## Phase 3: React Dashboard

**Goal:** Create professional React/Next.js frontend

**Duration:** 1-2 days

**Risk Level:** 🟢 Low (new service)

### Step 3.1: Initialize Next.js Project

```bash
# Create frontend-react directory
npx create-next-app@latest frontend-react --typescript --tailwind --app --no-src

cd frontend-react
```

### Step 3.2: Install Dependencies

```bash
npm install \
  axios \
  react-query \
  react-hook-form \
  zod \
  @hookform/resolvers \
  recharts \
  lucide-react \
  date-fns

npm install -D \
  @types/node \
  @types/react \
  @types/react-dom \
  eslint-config-next \
  prettier

echo "✅ Installed dependencies"
```

### Step 3.3: Create Project Structure

```bash
cd frontend-react

# Create directory structure
mkdir -p src/{components/{common,layout,sims,usage,quotas},lib/{api,hooks,contexts,utils},types}

echo "✅ Created project structure"
```

### Step 3.4: Create API Client

```typescript
// src/lib/api/client.ts
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor (add auth token)
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor (handle errors)
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Handle token refresh or logout
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

### Step 3.5: Create Dockerfile

```dockerfile
# frontend-react/Dockerfile
FROM node:18-alpine AS base

# Dependencies
FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# Builder
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# Runner
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000

CMD ["node", "server.js"]
```

### Step 3.6: Update Docker Compose

Add to root `docker-compose.yml`:

```yaml
  # React Frontend
  frontend-react:
    build:
      context: ./frontend-react
      dockerfile: Dockerfile
    container_name: iot-frontend-react
    volumes:
      - ./frontend-react:/app
      - /app/node_modules
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    ports:
      - "3000:3000"
    depends_on:
      - backend
    networks:
      - iot-network
    command: npm run dev
```

### Step 3.7: Create README

```bash
cat > frontend-react/README.md << 'EOF'
# IOT SIM Platform - React Dashboard

Professional web dashboard for IOT SIM management.

## Quick Start

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Open browser
open http://localhost:3000
```

## Build

```bash
# Build for production
npm run build

# Start production server
npm start
```

## Tech Stack

- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- React Query
- React Hook Form
- Recharts

## See Also

- [Architecture](../monorepo-docs/MONOREPO_ARCHITECTURE.md)
- [Main README](../README.md)
EOF
```

### Step 3.8: Commit Changes

```bash
cd ..
git add frontend-react/
git commit -m "Phase 3: Add React dashboard foundation

- Initialized Next.js 14 with TypeScript
- Created project structure
- Configured API client
- Created Dockerfile
- Updated docker-compose.yml
"
```

---

## Phase 4: Streamlit Admin

**Goal:** Create admin panel

**Duration:** 4-6 hours

**Risk Level:** 🟢 Low

### Step 4.1: Create Streamlit Structure

```bash
mkdir -p frontend-streamlit/{app/pages,api,config}
cd frontend-streamlit
```

### Step 4.2: Create Home Page

```python
# frontend-streamlit/Home.py
import streamlit as st

st.set_page_config(
    page_title="IOT SIM Admin",
    page_icon="📱",
    layout="wide"
)

st.title("📱 IOT SIM Management - Admin Panel")

st.markdown("""
Welcome to the IOT SIM Management Admin Panel.

Use the sidebar to navigate between different sections.
""")

# Quick stats
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total SIMs", "0", "+0")

with col2:
    st.metric("Active SIMs", "0")

with col3:
    st.metric("Data Usage", "0 GB")

with col4:
    st.metric("SMS Sent", "0")
```

### Step 4.3: Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Step 4.4: Create requirements.txt

```txt
streamlit==1.29.0
requests==2.31.0
plotly==5.18.0
pandas==2.1.4
```

### Step 4.5: Update Docker Compose

Add to root `docker-compose.yml`:

```yaml
  # Streamlit Admin
  frontend-streamlit:
    build:
      context: ./frontend-streamlit
      dockerfile: Dockerfile
    container_name: iot-frontend-streamlit
    volumes:
      - ./frontend-streamlit:/app
    environment:
      - API_URL=http://backend:8000
    ports:
      - "8501:8501"
    depends_on:
      - backend
    networks:
      - iot-network
```

### Step 4.6: Commit Changes

```bash
cd ..
git add frontend-streamlit/
git commit -m "Phase 4: Add Streamlit admin panel foundation

- Created Streamlit project structure
- Created home page
- Created Dockerfile
- Updated docker-compose.yml
"
```

---

## Phase 5: Monitoring Stack

**Goal:** Complete observability

**Duration:** 4-6 hours

**Risk Level:** 🟢 Low

### Step 5.1: Create Monitoring Structure

```bash
mkdir -p monitoring/{prometheus,grafana/{dashboards,provisioning/{dashboards,datasources}}}
```

### Step 5.2: Configure Prometheus

```yaml
# monitoring/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'backend-api'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/api/v1/metrics'

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

### Step 5.3: Configure Grafana Datasource

```yaml
# monitoring/grafana/provisioning/datasources/prometheus.yml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
```

### Step 5.4: Commit Changes

```bash
git add monitoring/
git commit -m "Phase 5: Add monitoring stack

- Configured Prometheus
- Configured Grafana datasources
- Created directory structure
"
```

---

## Phase 6: CI/CD Pipelines

**Goal:** Service-specific pipelines

**Duration:** 4-6 hours

**Risk Level:** 🟡 Medium

### Step 6.1: Create Backend CI/CD

```yaml
# .github/workflows/backend-ci.yml
name: Backend CI/CD

on:
  push:
    paths:
      - 'backend/**'
      - '.github/workflows/backend-ci.yml'
  pull_request:
    paths:
      - 'backend/**'

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements-dev.txt

      - name: Lint
        run: |
          cd backend
          black --check app/ tests/
          isort --check app/ tests/
          flake8 app/ tests/
          mypy app/

      - name: Test
        run: |
          cd backend
          pytest --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml
```

### Step 6.2: Commit Changes

```bash
git add .github/workflows/
git commit -m "Phase 6: Add CI/CD pipelines

- Created backend CI/CD workflow
- Configured linting and testing
- Added code coverage
"
```

---

## Phase 7: Documentation

**Goal:** Complete documentation

**Duration:** 4-6 hours

**Risk Level:** 🟢 Low

### Step 7.1: Update Root README

See the main GAME_PLAN.md for README structure

### Step 7.2: Create Service READMEs

Already created in previous phases.

### Step 7.3: Commit Changes

```bash
git add README.md docs/
git commit -m "Phase 7: Update documentation

- Updated root README
- Created service READMEs
- Updated architecture docs
"
```

---

## Testing & Validation

### Full Stack Testing

```bash
# 1. Start all services
docker-compose up -d

# 2. Wait for services
sleep 30

# 3. Check all services
docker-compose ps

# 4. Test backend
curl http://localhost:8000/health

# 5. Test Nginx routing
curl http://localhost/api/v1/health

# 6. Test React (if implemented)
curl http://localhost:3000

# 7. Test Streamlit (if implemented)
curl http://localhost:8501

# 8. Test Grafana
curl http://localhost:3001

# 9. Run backend tests
docker-compose exec backend pytest

# 10. Check logs
docker-compose logs --tail=50
```

---

## Rollback Procedures

### Emergency Rollback

```bash
# 1. Stop all services
docker-compose down

# 2. Checkout backup tag
git checkout backup-before-monorepo-YYYYMMDD

# 3. Restore original structure
# (if needed)

# 4. Start original services
docker-compose up -d
```

### Selective Rollback

```bash
# Rollback specific service
git checkout HEAD~1 -- backend/

# Rebuild and restart
docker-compose up -d --build backend
```

---

**Document Status:** ✅ Complete
**Last Updated:** 2024-11-17
**Next Steps:** Begin Phase 1
