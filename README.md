# FastAPI IOT SIM Management and Monitoring Server

A production-ready FastAPI server providing complete integration with the 1NCE IoT platform for programmatic management of SIM cards, connectivity, usage tracking, and order management.

## Features

- **Complete 1NCE API Integration**: OAuth 2.0 authentication with automatic token refresh
- **SIM Card Management**: Full CRUD operations for SIM cards with status tracking
- **Usage Tracking**: Time-series data storage using TimescaleDB for efficient querying
- **Quota Management**: Data and SMS quota tracking with auto top-up support
- **Real-time Connectivity**: Monitor SIM connectivity and network information
- **Event Logging**: Comprehensive event tracking for all SIM activities
- **SMS Management**: Send and receive SMS messages programmatically
- **Order Management**: Create and track orders for SIM cards and products
- **API Authentication**: JWT tokens and API keys for secure access
- **Caching**: Redis-based caching for improved performance
- **Background Jobs**: Automated sync and monitoring tasks
- **Production Ready**: Docker, Kubernetes, comprehensive logging, metrics

## Tech Stack

- **Backend**: FastAPI 0.104+, Python 3.11+
- **Database**: PostgreSQL 15+ with TimescaleDB extension
- **Cache**: Redis 7+
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Authentication**: JWT (python-jose), OAuth 2.0
- **Background Tasks**: APScheduler
- **Monitoring**: Prometheus, Structlog
- **Deployment**: Docker, Docker Compose, Kubernetes-ready

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ (with TimescaleDB)
- Redis 7+
- 1NCE API credentials (client ID and secret)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd IOT-sim-platform
```

### 2. Set Up Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# IMPORTANT: Set your 1NCE credentials
nano .env
```

### 3. Using Docker Compose (Recommended)

```bash
# Start all services (PostgreSQL, Redis, API)
docker-compose up -d

# View logs
docker-compose logs -f api

# Create admin user
docker-compose exec api python scripts/create_admin.py

# Run database migrations
docker-compose exec api alembic upgrade head

# Access the application
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### 4. Manual Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Create admin user
python scripts/create_admin.py

# Start the server
uvicorn app.main:app --reload

# Or use the main file
python app/main.py
```

## API Documentation & Testing

### Interactive Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs - Try endpoints directly in browser
- **ReDoc**: http://localhost:8000/redoc - Alternative documentation view
- **OpenAPI JSON**: http://localhost:8000/openapi.json - Machine-readable spec

### Complete Usage Guides

📚 **[Complete API Usage Guide](docs/API_USAGE_GUIDE.md)** - Comprehensive guide with:
- Step-by-step setup instructions
- All 40+ endpoints with detailed examples
- curl and Postman examples for every endpoint
- Complete authentication workflows
- Real-world usage scenarios
- Troubleshooting guide

📋 **[Quick Reference](docs/QUICK_REFERENCE.md)** - One-page cheat sheet with common commands

📮 **[Postman Collection](docs/postman_collection.json)** - Import into Postman for instant testing

### Testing the API

**Automated test script:**
```bash
# Test all endpoints automatically
./scripts/test_api.sh

# Expected output: ✓ All critical tests passed!
```

**Quick workflow examples:**
```bash
# Login and save token
TOKEN=$(./scripts/api_workflows.sh login admin admin123)

# List all SIMs
./scripts/api_workflows.sh list $TOKEN

# Monitor a specific SIM
./scripts/api_workflows.sh monitor $TOKEN 89490200001234567890

# Check data quota
./scripts/api_workflows.sh check-quota $TOKEN 89490200001234567890 data
```

**Manual testing with curl:**
```bash
# 1. Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 2. Save token
TOKEN="your-access-token-here"

# 3. List SIMs
curl -X GET "http://localhost:8000/api/v1/sims" \
  -H "Authorization: Bearer $TOKEN" | jq

# 4. Get SIM details
curl -X GET "http://localhost:8000/api/v1/sims/89490200001234567890" \
  -H "Authorization: Bearer $TOKEN" | jq
```

For detailed API specifications, see [docs/API_SPECIFICATION.md](docs/API_SPECIFICATION.md)

## Production Deployment

### Using the Deployment Script

```bash
# Copy production environment template
cp .env.production.template .env.production

# Edit with your production credentials
nano .env.production

# Run deployment
chmod +x scripts/deployment/deploy.sh
./scripts/deployment/deploy.sh production
```

### Manual Production Deployment

```bash
# Pull latest images
docker-compose -f docker-compose.prod.yml pull

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head

# Check health
curl http://localhost:8000/health
```

### Monitoring

- **Grafana Dashboard**: http://localhost:3000 (admin/your_password)
- **Prometheus Metrics**: http://localhost:9090
- **Application Metrics**: http://localhost:8000/api/v1/metrics

For comprehensive deployment guides, see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

## Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

## Development

### Project Structure

```
IOT-sim-platform/
├── app/
│   ├── api/v1/          # API endpoints
│   ├── clients/         # External API clients (1NCE)
│   ├── core/            # Core functionality (config, security, logging)
│   ├── db/              # Database configuration and migrations
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   ├── tasks/           # Background tasks
│   ├── utils/           # Utility functions
│   └── main.py          # FastAPI application
├── docs/                # Documentation
├── scripts/             # Utility scripts
├── tests/               # Test suite
├── docker/              # Docker configurations
├── .env.example         # Environment template
├── alembic.ini          # Alembic configuration
├── docker-compose.yml   # Docker Compose configuration
└── requirements.txt     # Python dependencies
```

### Running Tests

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html --cov-report=term

# Run specific test file
pytest tests/unit/test_security.py -v

# Run specific test
pytest tests/unit/test_security.py::TestPasswordHashing::test_hash_password -v

# Run integration tests only
pytest tests/integration/ -v

# Run with markers
pytest -m "not slow" -v

# View HTML coverage report
open htmlcov/index.html
```

### CI/CD

The project includes GitHub Actions workflows for:

- **Linting & Code Quality**: Black, isort, Flake8, MyPy
- **Testing**: Automated test suite with PostgreSQL and Redis
- **Security Scanning**: Safety and Bandit
- **Docker Build**: Automated image building and pushing
- **Deployment**: Automated deployment to staging/production

Setup pre-commit hooks for local development:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files

# Run specific test file
pytest tests/unit/test_once_client.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Lint code
ruff check app/ tests/

# Type checking
mypy app/
```

## Configuration

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection URL | Required |
| `REDIS_URL` | Redis connection URL | Required |
| `ONCE_CLIENT_ID` | 1NCE OAuth client ID | Required |
| `ONCE_CLIENT_SECRET` | 1NCE OAuth client secret | Required |
| `SECRET_KEY` | JWT signing key | Auto-generated |
| `ENVIRONMENT` | Environment (development/production) | development |
| `LOG_LEVEL` | Logging level | INFO |

See [.env.example](.env.example) for all available options.

## Deployment

### Docker

```bash
# Build production image
docker build -t iot-sim-api:latest .

# Run container
docker run -d \
  --name iot-sim-api \
  -p 8000:8000 \
  --env-file .env \
  iot-sim-api:latest
```

### Kubernetes

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for complete deployment guides including:

- Kubernetes manifests
- AWS ECS deployment
- Google Cloud Run deployment
- Terraform examples

## Monitoring

### Health Checks

- `GET /health` - Basic health check
- `GET /health/ready` - Readiness check (DB, Redis, 1NCE API)
- `GET /health/live` - Liveness check

### Metrics

Prometheus metrics available at `/metrics`:

- HTTP request metrics
- 1NCE API call metrics
- Database connection pool metrics
- Cache hit/miss ratios

### Logging

Structured JSON logging with request IDs:

```json
{
  "timestamp": "2024-01-15T10:30:45Z",
  "level": "info",
  "event": "http_request",
  "method": "GET",
  "path": "/api/v1/sims",
  "status_code": 200,
  "duration_ms": 45.2
}
```

## Documentation

- [Game Plan](docs/GAME_PLAN.md) - Development roadmap
- [Architecture](docs/ARCHITECTURE.md) - System architecture and design
- [Database Schema](docs/DATABASE_SCHEMA.md) - Complete database schema
- [API Specification](docs/API_SPECIFICATION.md) - Full API reference
- [User Stories](docs/USER_STORIES.md) - Feature requirements
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment
- [Developer Quickstart](docs/DEVELOPER_QUICKSTART.md) - 15-minute setup guide
- [Contributing](docs/CONTRIBUTING.md) - Contribution guidelines

## Contributing

Please read [CONTRIBUTING.md](docs/CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:

- Create an issue in the repository
- Check the [documentation](docs/)
- Review [common issues](docs/DEVELOPER_QUICKSTART.md#troubleshooting)

## Roadmap

See [GAME_PLAN.md](docs/GAME_PLAN.md) for the complete development roadmap and upcoming features.

Current Status: **Phase 1 Complete** - Core foundation implemented with:
- Complete project structure
- 1NCE API client with OAuth 2.0
- Database models and migrations
- Core utilities and configuration
- Docker setup for local development

Next Steps: **Phase 2** - API endpoints and services implementation
