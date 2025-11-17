# Developer Quick Start Guide

Get up and running with the FastAPI 1NCE Server in 15 minutes.

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- 1NCE API credentials (username & password)
- Git

## Step 1: Clone & Setup (2 minutes)

```bash
# Navigate to project directory
cd fastapi-1nce-project

# Create environment file
cp .env.example .env

# Edit .env file with your credentials
nano .env  # or use your preferred editor
```

**Required settings in `.env`:**
```bash
ONCE_USERNAME=your_1nce_username
ONCE_PASSWORD=your_1nce_password
SECRET_KEY=change-this-to-random-string  # Generate: openssl rand -hex 32
```

## Step 2: Start Development Environment (5 minutes)

```bash
# Start all services
docker-compose up -d

# Check services are running
docker-compose ps

# You should see:
# - db (PostgreSQL + TimescaleDB)
# - redis
# - api (will be created in Step 3)
```

## Step 3: Create Project Structure (3 minutes)

```bash
# Create main application directory
mkdir -p app/{api/v1,clients,core,models,schemas,services,db,utils,tasks}
mkdir -p tests/{unit,integration,e2e}
mkdir -p scripts

# Create __init__.py files
find app -type d -exec touch {}/__init__.py \;
find tests -type d -exec touch {}/__init__.py \;
```

## Step 4: Install Dependencies (2 minutes)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Step 5: Initialize Database (2 minutes)

```bash
# Wait for database to be ready
docker-compose exec db pg_isready

# Create TimescaleDB extension
docker-compose exec db psql -U onceapi -d onceapi -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"

# Initialize Alembic
alembic init app/db/migrations

# Create first migration (you'll need to create models first)
# alembic revision --autogenerate -m "Initial schema"
# alembic upgrade head
```

## Step 6: Create Your First File (1 minute)

Create `app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="FastAPI 1NCE Server",
    description="Production-ready API for 1NCE IoT platform",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "FastAPI 1NCE Server", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Step 7: Run the Server (1 minute)

```bash
# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or with Python
python -m app.main
```

## Step 8: Test the API (1 minute)

```bash
# Test root endpoint
curl http://localhost:8000

# Expected response:
# {"message":"FastAPI 1NCE Server","status":"running"}

# Test health endpoint
curl http://localhost:8000/health

# View API docs
# Open browser: http://localhost:8000/docs
```

## ✅ Success!

If you can see the Swagger UI at http://localhost:8000/docs, you're ready to start developing!

---

## Next Steps

Now you're ready to implement features following the game plan:

### 1. Implement 1NCE Client (2-3 hours)

Create `app/clients/once_client.py`:

```python
import httpx
from typing import Optional

class OnceClient:
    def __init__(self, username: str, password: str, base_url: str):
        self.username = username
        self.password = password
        self.base_url = base_url
        self.token: Optional[str] = None
    
    async def get_token(self) -> str:
        """Get OAuth2 token from 1NCE API"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/oauth/token",
                auth=(self.username, self.password),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={"grant_type": "client_credentials"}
            )
            response.raise_for_status()
            data = response.json()
            self.token = data["access_token"]
            return self.token
    
    async def get_sims(self):
        """Get all SIMs from 1NCE API"""
        if not self.token:
            await self.get_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/v1/sims",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            response.raise_for_status()
            return response.json()
```

### 2. Create Database Models (1-2 hours)

Create `app/models/sim.py`:

```python
from sqlalchemy import Column, Integer, String, DateTime, Boolean, TIMESTAMP
from sqlalchemy.dialects.postgresql import INET, JSONB
from datetime import datetime
from app.db.base import Base

class SIM(Base):
    __tablename__ = "sims"
    
    id = Column(Integer, primary_key=True)
    iccid = Column(String(20), unique=True, nullable=False)
    imsi = Column(String(15))
    msisdn = Column(String(15))
    status = Column(String(20))
    label = Column(String(255))
    ip_address = Column(INET)
    imei = Column(String(15))
    organization_id = Column(Integer)
    
    metadata = Column(JSONB, default={})
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_synced_at = Column(DateTime)
```

### 3. Create API Endpoints (2-3 hours)

Create `app/api/v1/sims.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.clients.once_client import OnceClient
from app.core.config import settings

router = APIRouter(prefix="/sims", tags=["SIMs"])

@router.get("/")
async def list_sims():
    """List all SIM cards"""
    client = OnceClient(
        settings.ONCE_USERNAME,
        settings.ONCE_PASSWORD,
        settings.ONCE_API_BASE_URL
    )
    
    try:
        sims = await client.get_sims()
        return {"success": True, "data": sims}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

@router.get("/{iccid}")
async def get_sim(iccid: str):
    """Get single SIM details"""
    # Implementation here
    pass
```

### 4. Add Configuration (30 minutes)

Create `app/core/config.py`:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 1NCE API
    ONCE_USERNAME: str
    ONCE_PASSWORD: str
    ONCE_API_BASE_URL: str = "https://api.1nce.com"
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### 5. Write Your First Test (30 minutes)

Create `tests/unit/test_once_client.py`:

```python
import pytest
from app.clients.once_client import OnceClient

@pytest.mark.asyncio
async def test_get_token():
    client = OnceClient("test", "test", "https://api.1nce.com")
    # Add mocking here
    # Test token retrieval
    pass
```

---

## Common Issues

### Issue: Database connection failed

**Solution:**
```bash
# Check if database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### Issue: Redis connection failed

**Solution:**
```bash
# Check if Redis is running
docker-compose ps redis

# Test Redis connection
docker-compose exec redis redis-cli ping
# Should return: PONG
```

### Issue: Import errors

**Solution:**
```bash
# Make sure you're in virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

---

## Development Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/sim-management
   ```

2. **Write code**
   - Follow the architecture guide
   - Implement user stories
   - Write tests

3. **Run tests**
   ```bash
   pytest tests/ -v
   ```

4. **Check code quality**
   ```bash
   black app tests
   ruff check app tests
   mypy app
   ```

5. **Commit and push**
   ```bash
   git add .
   git commit -m "Add SIM management endpoints"
   git push origin feature/sim-management
   ```

---

## Useful Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f api

# Run tests
pytest tests/ -v --cov=app

# Format code
black app tests

# Run development server
uvicorn app.main:app --reload

# Create database migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

---

## Resources

- **Documentation**: See all `.md` files in project root
- **API Docs**: http://localhost:8000/docs (when running)
- **FastAPI**: https://fastapi.tiangolo.com
- **SQLAlchemy**: https://docs.sqlalchemy.org
- **Pydantic**: https://docs.pydantic.dev

---

## Getting Help

1. Check the documentation files (ARCHITECTURE.md, DATABASE_SCHEMA.md, etc.)
2. Review user stories for feature requirements
3. Check the game plan for implementation timeline
4. Review API specification for endpoint details

---

**You're all set! Start building!** 🚀

Follow the game plan in GAME_PLAN.md for the complete development roadmap.
