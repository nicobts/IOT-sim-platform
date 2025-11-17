# IOT SIM Platform - Backend API

FastAPI backend service for IOT SIM management with 1NCE integration.

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

# Run tests with coverage
pytest --cov=app --cov-report=html

# Lint code
black app/ tests/
isort app/ tests/
flake8 app/ tests/

# Type checking
mypy app/
```

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Project Structure

```
backend/
├── app/                    # Application code
│   ├── api/v1/            # API endpoints
│   ├── clients/           # External clients (1NCE)
│   ├── core/              # Core functionality
│   ├── db/                # Database layer
│   ├── models/            # SQLAlchemy models
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # Business logic
│   ├── tasks/             # Background jobs
│   ├── utils/             # Utilities
│   └── main.py            # FastAPI application
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── e2e/              # End-to-end tests
├── alembic.ini           # Alembic configuration
├── Dockerfile            # Docker container
├── docker-compose.yml    # Development environment
├── requirements.txt      # Python dependencies
└── requirements-dev.txt  # Development dependencies
```

## Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `ONCE_CLIENT_ID`: 1NCE API client ID
- `ONCE_CLIENT_SECRET`: 1NCE API client secret
- `SECRET_KEY`: JWT signing key

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_security.py

# Run with markers
pytest -m "not slow"

# Generate coverage report
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

## Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View history
alembic history
```

## See Also

- [Complete API Usage Guide](../docs/API_USAGE_GUIDE.md)
- [API Specification](../docs/API_SPECIFICATION.md)
- [Quick Reference](../docs/QUICK_REFERENCE.md)
- [Monorepo Architecture](../monorepo-docs/MONOREPO_ARCHITECTURE.md)
- [Main README](../README.md)

## Tech Stack

- **Framework**: FastAPI 0.104+
- **Python**: 3.11+
- **Database**: PostgreSQL 15+ with TimescaleDB
- **Cache**: Redis 7+
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Authentication**: JWT (python-jose)
- **Background Tasks**: APScheduler
- **Monitoring**: Prometheus
- **Testing**: pytest

## Production

For production deployment, see:
- [Deployment Guide](../docs/DEPLOYMENT.md)
- [Production Readiness](../PRODUCTION_READINESS.md)
- [Migration Guide](../monorepo-docs/MIGRATION_GUIDE.md)
