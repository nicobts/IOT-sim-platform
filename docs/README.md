# FastAPI 1NCE Server

> Production-ready FastAPI server for complete 1NCE IoT platform integration

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 🎯 Overview

A comprehensive REST API server that provides seamless integration with the 1NCE IoT connectivity platform. This project enables programmatic management of IoT SIM cards, real-time usage tracking, quota management, SMS capabilities, and complete device lifecycle management.

### Key Features

✅ **Complete 1NCE API Integration**
- OAuth 2.0 authentication with automatic token refresh
- All SIM management endpoints
- Usage tracking and analytics
- Quota and top-up management
- SMS sending and receiving
- Order and product management

✅ **Production-Ready Architecture**
- FastAPI with async/await support
- PostgreSQL + TimescaleDB for time-series data
- Redis caching for performance
- Background job scheduler
- Comprehensive error handling
- Structured logging

✅ **Developer Experience**
- Auto-generated API documentation (Swagger/ReDoc)
- Type-safe with Pydantic models
- Easy local development with Docker Compose
- Comprehensive test suite
- CI/CD ready

✅ **Monitoring & Observability**
- Prometheus metrics
- Health check endpoints
- Structured logging
- Error tracking integration

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [API Documentation](#api-documentation)

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- 1NCE API credentials

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/fastapi-1nce-server.git
cd fastapi-1nce-server
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your 1NCE credentials
```

3. **Start with Docker Compose**
```bash
docker-compose up -d
```

4. **Access the API**
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📚 Documentation

- **[GAME_PLAN.md](GAME_PLAN.md)** - Complete development roadmap
- **[USER_STORIES.md](USER_STORIES.md)** - User stories and acceptance criteria
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture
- **[DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)** - Database schema
- **[API_SPECIFICATION.md](API_SPECIFICATION.md)** - API reference
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deployment guide

## 🔧 Configuration

See `.env.example` for all configuration options.

## 📖 API Documentation

Interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📝 License

MIT License - see [LICENSE](LICENSE) file.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/)
- [1NCE](https://1nce.com/)
- [TimescaleDB](https://www.timescale.com/)

---

**Built with ❤️ using FastAPI and 1NCE**
