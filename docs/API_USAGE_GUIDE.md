# Complete API Usage & Testing Guide

**FastAPI IOT SIM Management Server**
Version: 1.0.0
Last Updated: 2024-11-17

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Setup & Configuration](#setup--configuration)
3. [Authentication](#authentication)
4. [API Endpoints Reference](#api-endpoints-reference)
5. [Complete Workflows](#complete-workflows)
6. [Testing with Postman](#testing-with-postman)
7. [Testing with curl](#testing-with-curl)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites

- Docker & Docker Compose installed
- 1NCE API credentials (client ID & secret)
- Postman or curl for testing

### 5-Minute Setup

```bash
# 1. Clone the repository
git clone <repository-url>
cd IOT-sim-platform

# 2. Configure environment
cp .env.example .env
nano .env  # Add your 1NCE credentials

# 3. Start services
docker-compose up -d

# 4. Run database migrations
docker-compose exec api alembic upgrade head

# 5. Create admin user
docker-compose exec api python scripts/create_admin.py

# 6. Access the API
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
# Health: http://localhost:8000/health
```

---

## Setup & Configuration

### Environment Variables

Create a `.env` file with the following configuration:

```bash
# Application Settings
PROJECT_NAME="FastAPI IOT SIM Management Server"
VERSION="1.0.0"
DEBUG=true                    # Enable for development
ENVIRONMENT="development"

# Server
HOST="0.0.0.0"
PORT=8000

# Security
SECRET_KEY="your-secret-key-min-32-characters-change-in-production"
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database
DATABASE_URL="postgresql+asyncpg://user:password@db:5432/iot_sim_db"

# Redis
REDIS_URL="redis://redis:6379/0"

# 1NCE API (REQUIRED - Get from 1NCE portal)
ONCE_CLIENT_ID="your-1nce-client-id"
ONCE_CLIENT_SECRET="your-1nce-client-secret"

# Features
ENABLE_SCHEDULER=true
ENABLE_METRICS=true
ENABLE_CACHE=true
```

### Creating Admin User

**Default credentials:**
- Username: `admin`
- Password: `admin123`
- Email: `admin@example.com`

**Custom credentials:**
```bash
docker-compose exec api python scripts/create_admin.py \
  --username "myadmin" \
  --email "admin@mycompany.com" \
  --password "SecurePass123!"
```

### Verify Installation

```bash
# Check service health
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "service": "FastAPI IOT SIM Management Server",
  "version": "1.0.0",
  "environment": "development"
}

# Check API documentation
open http://localhost:8000/docs
```

---

## Authentication

The API supports two authentication methods:

### 1. JWT Token Authentication (Recommended for users)

**Step 1: Login to get tokens**

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Step 2: Use access token in requests**

```bash
curl -X GET "http://localhost:8000/api/v1/sims" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Step 3: Refresh token when expired**

```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

### 2. API Key Authentication (Recommended for automation)

**Step 1: Create API key (requires JWT token first)**

```bash
# Login first
ACCESS_TOKEN="your-access-token-here"

# Create API key
curl -X POST "http://localhost:8000/api/v1/auth/api-keys" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production API Key",
    "expires_in_days": 365
  }'
```

**Response:**
```json
{
  "key": "iot_key_EXAMPLE1234abcd",
  "id": 1,
  "name": "Production API Key",
  "user_id": 1,
  "is_active": true,
  "created_at": "2024-11-17T10:30:00Z",
  "expires_at": "2025-11-17T10:30:00Z"
}
```

**⚠️ Important:** Save the key value! It's only shown once.

**Step 2: Use API key in requests**

```bash
curl -X GET "http://localhost:8000/api/v1/sims" \
  -H "X-API-Key: iot_key_EXAMPLE1234abcd"
```

**List your API keys:**

```bash
curl -X GET "http://localhost:8000/api/v1/auth/api-keys" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Revoke an API key:**

```bash
curl -X DELETE "http://localhost:8000/api/v1/auth/api-keys/1" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

---

## API Endpoints Reference

### Base URL
- **Development:** `http://localhost:8000`
- **Production:** `https://your-domain.com`
- **API Prefix:** `/api/v1`

### Endpoint Categories

1. **Health** - Service health checks
2. **Authentication** - Login, tokens, API keys
3. **SIM Management** - CRUD operations for SIMs
4. **Usage & Quotas** - Data usage and quota management
5. **SMS** - Send and receive SMS
6. **Connectivity** - Network connectivity status
7. **Scheduler** - Background job management
8. **Metrics** - Prometheus metrics

---

## 1. Health Endpoints

### 1.1 Basic Health Check

**Endpoint:** `GET /health`
**Authentication:** None
**Description:** Check if the API is running

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "FastAPI IOT SIM Management Server",
  "version": "1.0.0",
  "environment": "development"
}
```

### 1.2 Readiness Check

**Endpoint:** `GET /health/ready`
**Authentication:** None
**Description:** Check if the API is ready to serve traffic

```bash
curl http://localhost:8000/health/ready
```

**Response (Healthy):**
```json
{
  "status": "ready",
  "checks": {
    "database": "ok",
    "redis": "ok",
    "once_api": "ok"
  }
}
```

### 1.3 Liveness Check

**Endpoint:** `GET /health/live`
**Authentication:** None
**Description:** Check if the API process is alive

```bash
curl http://localhost:8000/health/live
```

**Response:**
```json
{
  "status": "alive"
}
```

---

## 2. Authentication Endpoints

### 2.1 Login

**Endpoint:** `POST /api/v1/auth/login`
**Authentication:** None
**Description:** Authenticate and receive JWT tokens

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwidXNlcm5hbWUiOiJhZG1pbiIsImV4cCI6MTYzMjE0NTIwMH0.abc123",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwidXNlcm5hbWUiOiJhZG1pbiIsImV4cCI6MTYzMjc1MDAwMH0.def456",
  "token_type": "bearer"
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid credentials

### 2.2 Refresh Token

**Endpoint:** `POST /api/v1/auth/refresh`
**Authentication:** None
**Description:** Get new access token using refresh token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 2.3 Get Current User

**Endpoint:** `GET /api/v1/auth/me`
**Authentication:** JWT or API Key
**Description:** Get current authenticated user info

```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Response:**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "is_active": true,
  "is_superuser": true,
  "created_at": "2024-11-17T10:00:00Z"
}
```

### 2.4 Register User (Admin Only)

**Endpoint:** `POST /api/v1/auth/register`
**Authentication:** JWT or API Key (Superuser required)
**Description:** Create a new user

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "is_superuser": false
  }'
```

**Response:**
```json
{
  "id": 2,
  "username": "john_doe",
  "email": "john@example.com",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2024-11-17T11:00:00Z"
}
```

**Validation Rules:**
- Username: min 3 characters, alphanumeric + underscore
- Email: valid email format
- Password: min 8 characters

### 2.5 Create API Key

**Endpoint:** `POST /api/v1/auth/api-keys`
**Authentication:** JWT or API Key
**Description:** Create a new API key

```bash
curl -X POST "http://localhost:8000/api/v1/auth/api-keys" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production API Key",
    "expires_in_days": 365
  }'
```

**Request Parameters:**
- `name` (optional): Descriptive name for the key
- `expires_in_days` (optional): Expiration in days (1-365), default: 365

**Response:**
```json
{
  "key": "iot_key_EXAMPLE1234567890abcdefghijklmnop",
  "id": 1,
  "name": "Production API Key",
  "user_id": 1,
  "is_active": true,
  "created_at": "2024-11-17T10:30:00Z",
  "expires_at": "2025-11-17T10:30:00Z"
}
```

### 2.6 List API Keys

**Endpoint:** `GET /api/v1/auth/api-keys`
**Authentication:** JWT or API Key
**Description:** List all API keys for current user

```bash
curl -X GET "http://localhost:8000/api/v1/auth/api-keys" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Production API Key",
    "user_id": 1,
    "is_active": true,
    "created_at": "2024-11-17T10:30:00Z",
    "expires_at": "2025-11-17T10:30:00Z",
    "last_used_at": "2024-11-17T12:00:00Z"
  }
]
```

### 2.7 Revoke API Key

**Endpoint:** `DELETE /api/v1/auth/api-keys/{api_key_id}`
**Authentication:** JWT or API Key
**Description:** Deactivate an API key

```bash
curl -X DELETE "http://localhost:8000/api/v1/auth/api-keys/1" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Response:** `204 No Content`

---

## 3. SIM Management Endpoints

### 3.1 List SIMs

**Endpoint:** `GET /api/v1/sims`
**Authentication:** JWT or API Key
**Description:** Get paginated list of SIM cards

```bash
# Basic request
curl -X GET "http://localhost:8000/api/v1/sims" \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# With pagination
curl -X GET "http://localhost:8000/api/v1/sims?page=2&page_size=50" \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# With status filter
curl -X GET "http://localhost:8000/api/v1/sims?status=active" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Query Parameters:**
- `page` (optional): Page number, default: 1
- `page_size` (optional): Items per page (1-1000), default: 100
- `status` (optional): Filter by status (active, inactive, suspended)

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "iccid": "89490200001234567890",
      "imsi": "901405123456789",
      "msisdn": "+491234567890",
      "status": "active",
      "label": "Production SIM 1",
      "ip_address": "10.0.0.1",
      "created_at": "2024-11-17T10:00:00Z",
      "updated_at": "2024-11-17T12:00:00Z",
      "last_status_change_at": "2024-11-17T10:00:00Z"
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 100,
  "total_pages": 2
}
```

### 3.2 Create SIM

**Endpoint:** `POST /api/v1/sims`
**Authentication:** JWT or API Key
**Description:** Create a new SIM record

```bash
curl -X POST "http://localhost:8000/api/v1/sims" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "iccid": "89490200001234567890",
    "imsi": "901405123456789",
    "msisdn": "+491234567890",
    "label": "Production SIM 1"
  }'
```

**Request Body:**
- `iccid` (required): SIM ICCID (19-20 digits)
- `imsi` (optional): IMSI (14-15 digits)
- `msisdn` (optional): Phone number
- `label` (optional): Custom label

**Response:**
```json
{
  "id": 1,
  "iccid": "89490200001234567890",
  "imsi": "901405123456789",
  "msisdn": "+491234567890",
  "status": "active",
  "label": "Production SIM 1",
  "created_at": "2024-11-17T10:00:00Z",
  "updated_at": "2024-11-17T10:00:00Z"
}
```

**Validation:**
- ICCID must be 19-20 digits
- IMSI must be 14-15 digits
- ICCID must be unique

### 3.3 Get SIM by ICCID

**Endpoint:** `GET /api/v1/sims/{iccid}`
**Authentication:** JWT or API Key
**Description:** Get SIM details by ICCID

```bash
curl -X GET "http://localhost:8000/api/v1/sims/89490200001234567890" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Response:**
```json
{
  "id": 1,
  "iccid": "89490200001234567890",
  "imsi": "901405123456789",
  "msisdn": "+491234567890",
  "status": "active",
  "label": "Production SIM 1",
  "ip_address": "10.0.0.1",
  "imei": "123456789012345",
  "imei_lock": true,
  "created_at": "2024-11-17T10:00:00Z",
  "updated_at": "2024-11-17T12:00:00Z",
  "last_status_change_at": "2024-11-17T10:00:00Z"
}
```

**Error Responses:**
- `404 Not Found` - SIM not found

### 3.4 Update SIM

**Endpoint:** `PATCH /api/v1/sims/{iccid}`
**Authentication:** JWT or API Key
**Description:** Update SIM information

```bash
curl -X PATCH "http://localhost:8000/api/v1/sims/89490200001234567890" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "label": "Updated Production SIM",
    "metadata": {
      "location": "Warehouse A",
      "device_type": "Sensor"
    }
  }'
```

**Request Body:**
- `label` (optional): New label
- `metadata` (optional): Custom JSON metadata

**Response:**
```json
{
  "id": 1,
  "iccid": "89490200001234567890",
  "label": "Updated Production SIM",
  "metadata": {
    "location": "Warehouse A",
    "device_type": "Sensor"
  },
  "updated_at": "2024-11-17T13:00:00Z"
}
```

### 3.5 Sync SIM from 1NCE

**Endpoint:** `POST /api/v1/sims/{iccid}/sync`
**Authentication:** JWT or API Key
**Description:** Fetch latest SIM data from 1NCE API

```bash
curl -X POST "http://localhost:8000/api/v1/sims/89490200001234567890/sync" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Response:**
```json
{
  "id": 1,
  "iccid": "89490200001234567890",
  "imsi": "901405123456789",
  "msisdn": "+491234567890",
  "status": "active",
  "ip_address": "10.0.0.1",
  "imei": "123456789012345",
  "imei_lock": true,
  "updated_at": "2024-11-17T13:05:00Z"
}
```

**What it does:**
- Fetches current SIM data from 1NCE
- Updates local database
- Returns updated SIM record

### 3.6 Sync All SIMs

**Endpoint:** `POST /api/v1/sims/sync-all`
**Authentication:** JWT or API Key
**Description:** Synchronize all SIMs from 1NCE

```bash
curl -X POST "http://localhost:8000/api/v1/sims/sync-all" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Response:**
```json
{
  "synced_count": 150,
  "message": "Successfully synced 150 SIMs"
}
```

**Note:** This may take a while for large numbers of SIMs.

---

## 4. Usage & Quota Endpoints

### 4.1 Get SIM Usage

**Endpoint:** `GET /api/v1/sims/{iccid}/usage`
**Authentication:** JWT or API Key
**Description:** Get SIM usage data with optional date filtering

```bash
# Get all usage
curl -X GET "http://localhost:8000/api/v1/sims/89490200001234567890/usage" \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Get usage for date range
curl -X GET "http://localhost:8000/api/v1/sims/89490200001234567890/usage?start_date=2024-11-01T00:00:00Z&end_date=2024-11-17T23:59:59Z" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Query Parameters:**
- `start_date` (optional): Start date (ISO format)
- `end_date` (optional): End date (ISO format)

**Response:**
```json
[
  {
    "id": 1,
    "sim_id": 1,
    "iccid": "89490200001234567890",
    "timestamp": "2024-11-17T12:00:00Z",
    "data_volume": 1048576,
    "sms_mo": 5,
    "sms_mt": 2,
    "data_volume_rx": 524288,
    "data_volume_tx": 524288,
    "country": "DE",
    "network": "T-Mobile"
  }
]
```

**Fields:**
- `data_volume`: Total data in bytes
- `sms_mo`: SMS sent (Mobile Originated)
- `sms_mt`: SMS received (Mobile Terminated)
- `data_volume_rx`: Data received in bytes
- `data_volume_tx`: Data transmitted in bytes

### 4.2 Sync Usage from 1NCE

**Endpoint:** `POST /api/v1/sims/{iccid}/usage/sync`
**Authentication:** JWT or API Key
**Description:** Fetch latest usage data from 1NCE

```bash
curl -X POST "http://localhost:8000/api/v1/sims/89490200001234567890/usage/sync" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Response:**
```json
[
  {
    "id": 2,
    "sim_id": 1,
    "iccid": "89490200001234567890",
    "timestamp": "2024-11-17T13:00:00Z",
    "data_volume": 2097152,
    "sms_mo": 7,
    "sms_mt": 3
  }
]
```

### 4.3 Get SIM Quota

**Endpoint:** `GET /api/v1/sims/{iccid}/quota/{quota_type}`
**Authentication:** JWT or API Key
**Description:** Get SIM quota (data or SMS)

```bash
# Get data quota
curl -X GET "http://localhost:8000/api/v1/sims/89490200001234567890/quota/data" \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Get SMS quota
curl -X GET "http://localhost:8000/api/v1/sims/89490200001234567890/quota/sms" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Path Parameters:**
- `quota_type`: `data` or `sms`

**Response (Data Quota):**
```json
{
  "id": 1,
  "sim_id": 1,
  "iccid": "89490200001234567890",
  "quota_type": "data",
  "volume": 1073741824,
  "used_volume": 104857600,
  "remaining_volume": 968884224,
  "threshold_percentage": 80,
  "threshold_volume": 858993459,
  "auto_refill": false,
  "status": "active",
  "expires_at": "2025-11-17T00:00:00Z",
  "last_refill_at": "2024-11-17T00:00:00Z"
}
```

**Response (SMS Quota):**
```json
{
  "id": 2,
  "sim_id": 1,
  "iccid": "89490200001234567890",
  "quota_type": "sms",
  "volume": 100,
  "used_volume": 15,
  "remaining_volume": 85,
  "threshold_percentage": 80,
  "auto_refill": false,
  "status": "active"
}
```

### 4.4 Top-up Quota

**Endpoint:** `POST /api/v1/sims/{iccid}/topup`
**Authentication:** JWT or API Key
**Description:** Add quota to SIM (data or SMS)

```bash
# Top-up data (1GB = 1073741824 bytes)
curl -X POST "http://localhost:8000/api/v1/sims/89490200001234567890/topup" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "quota_type": "data",
    "volume": 1073741824
  }'

# Top-up SMS
curl -X POST "http://localhost:8000/api/v1/sims/89490200001234567890/topup" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "quota_type": "sms",
    "volume": 100
  }'
```

**Request Body:**
- `quota_type`: `data` or `sms`
- `volume`: Volume to add (bytes for data, count for SMS)

**Response:**
```json
{
  "message": "Successfully topped up 1073741824 data for SIM 89490200001234567890"
}
```

---

## 5. SMS Endpoints

### 5.1 Send SMS

**Endpoint:** `POST /api/v1/sims/{iccid}/sms`
**Authentication:** JWT or API Key
**Description:** Send SMS to a SIM

```bash
curl -X POST "http://localhost:8000/api/v1/sims/89490200001234567890/sms" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello from the API!",
    "destination_address": "+491234567890"
  }'
```

**Request Body:**
- `message` (required): SMS message (max 160 characters)
- `destination_address` (optional): Destination phone number

**Response:**
```json
{
  "message": "SMS sent successfully to SIM 89490200001234567890"
}
```

**Limits:**
- Maximum 160 characters per message
- SMS quota must be available

---

## 6. Connectivity Endpoints

### 6.1 Get Connectivity Status

**Endpoint:** `GET /api/v1/sims/{iccid}/connectivity`
**Authentication:** JWT or API Key
**Description:** Get current connectivity status from 1NCE

```bash
curl -X GET "http://localhost:8000/api/v1/sims/89490200001234567890/connectivity" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Response:**
```json
{
  "iccid": "89490200001234567890",
  "status": "online",
  "ip_address": "10.0.0.1",
  "network": "T-Mobile",
  "country_code": "DE",
  "signal_strength": -75,
  "last_connect": "2024-11-17T12:00:00Z",
  "session_duration": 3600,
  "apn": "iot.1nce.net"
}
```

### 6.2 Reset Connectivity

**Endpoint:** `POST /api/v1/sims/{iccid}/connectivity/reset`
**Authentication:** JWT or API Key
**Description:** Reset SIM connectivity via 1NCE

```bash
curl -X POST "http://localhost:8000/api/v1/sims/89490200001234567890/connectivity/reset" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Response:**
```json
{
  "message": "Connectivity reset successful for SIM 89490200001234567890"
}
```

**What it does:**
- Terminates current session
- Forces SIM to re-establish connection
- Useful for troubleshooting connectivity issues

---

## 7. Events Endpoints

### 7.1 Get SIM Events

**Endpoint:** `GET /api/v1/sims/{iccid}/events`
**Authentication:** JWT or API Key
**Description:** Get SIM events from 1NCE

```bash
# Get all events
curl -X GET "http://localhost:8000/api/v1/sims/89490200001234567890/events" \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Filter by event type
curl -X GET "http://localhost:8000/api/v1/sims/89490200001234567890/events?event_type=connectivity" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Query Parameters:**
- `event_type` (optional): Filter by event type

**Response:**
```json
[
  {
    "id": "evt_123",
    "iccid": "89490200001234567890",
    "event_type": "connectivity",
    "event_name": "session_start",
    "timestamp": "2024-11-17T12:00:00Z",
    "details": {
      "ip_address": "10.0.0.1",
      "network": "T-Mobile",
      "country": "DE"
    }
  },
  {
    "id": "evt_124",
    "event_type": "sms",
    "event_name": "sms_received",
    "timestamp": "2024-11-17T12:05:00Z",
    "details": {
      "from": "+491234567890",
      "message": "Hello"
    }
  }
]
```

**Event Types:**
- `connectivity` - Connection events
- `sms` - SMS events
- `quota` - Quota events
- `status_change` - Status change events

---

## 8. Scheduler Endpoints (Admin Only)

### 8.1 Get Scheduler Status

**Endpoint:** `GET /api/v1/scheduler/status`
**Authentication:** JWT or API Key (Superuser required)
**Description:** Get scheduler and job statistics

```bash
curl -X GET "http://localhost:8000/api/v1/scheduler/status" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Response:**
```json
{
  "enabled": true,
  "running": true,
  "state": 1,
  "total_jobs": 4,
  "jobs": [
    {
      "id": "sync_all_sims",
      "name": "Sync All SIMs",
      "next_run_time": "2024-11-17T13:00:00Z",
      "trigger": "interval[0:15:00]"
    },
    {
      "id": "sync_usage_data",
      "name": "Sync Usage Data",
      "next_run_time": "2024-11-17T14:00:00Z",
      "trigger": "interval[1:00:00]"
    },
    {
      "id": "check_quotas",
      "name": "Check Quotas",
      "next_run_time": "2024-11-17T13:30:00Z",
      "trigger": "interval[0:30:00]"
    },
    {
      "id": "cleanup_old_data",
      "name": "Cleanup Old Data",
      "next_run_time": "2024-11-18T02:00:00Z",
      "trigger": "cron[day='*', hour='2', minute='0']"
    }
  ]
}
```

**Background Jobs:**
1. **Sync All SIMs** - Every 15 minutes
2. **Sync Usage Data** - Every hour
3. **Check Quotas** - Every 30 minutes
4. **Cleanup Old Data** - Daily at 2 AM UTC

### 8.2 Get Job Details

**Endpoint:** `GET /api/v1/scheduler/jobs/{job_id}`
**Authentication:** JWT or API Key (Superuser required)
**Description:** Get details for a specific job

```bash
curl -X GET "http://localhost:8000/api/v1/scheduler/jobs/sync_all_sims" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Response:**
```json
{
  "id": "sync_all_sims",
  "name": "Sync All SIMs",
  "next_run_time": "2024-11-17T13:00:00Z",
  "trigger": "interval[0:15:00]"
}
```

---

## 9. Metrics Endpoint

### 9.1 Prometheus Metrics

**Endpoint:** `GET /api/v1/metrics`
**Authentication:** None
**Description:** Get Prometheus metrics

```bash
curl http://localhost:8000/api/v1/metrics
```

**Response:** (Prometheus text format)
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/api/v1/sims",status="200"} 1234

# HELP http_request_duration_seconds HTTP request duration
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{method="GET",endpoint="/api/v1/sims",le="0.1"} 950
http_request_duration_seconds_bucket{method="GET",endpoint="/api/v1/sims",le="0.5"} 1200

# HELP database_connections Active database connections
# TYPE database_connections gauge
database_connections 15

# HELP once_api_requests_total Total 1NCE API requests
# TYPE once_api_requests_total counter
once_api_requests_total{method="get_sim",status="success"} 500

# HELP cache_hits_total Total cache hits
# TYPE cache_hits_total counter
cache_hits_total 1500

# HELP cache_misses_total Total cache misses
# TYPE cache_misses_total counter
cache_misses_total 250
```

**Metrics Categories:**
- HTTP request metrics
- Database metrics
- 1NCE API metrics
- Background job metrics
- Cache metrics
- Authentication metrics

---

## Complete Workflows

### Workflow 1: Initial Setup & Authentication

```bash
#!/bin/bash
set -e

# 1. Start services
docker-compose up -d

# 2. Wait for services
sleep 10

# 3. Run migrations
docker-compose exec -T api alembic upgrade head

# 4. Create admin user
docker-compose exec -T api python scripts/create_admin.py

# 5. Get access token
TOKEN_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }')

ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token')
echo "Access Token: $ACCESS_TOKEN"

# 6. Create API key
API_KEY_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/auth/api-keys" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production Key",
    "expires_in_days": 365
  }')

API_KEY=$(echo $API_KEY_RESPONSE | jq -r '.key')
echo "API Key: $API_KEY"

# Save for later use
echo "export API_KEY=$API_KEY" > .api_credentials
echo "Credentials saved to .api_credentials"
```

### Workflow 2: Sync and Monitor SIMs

```bash
#!/bin/bash
source .api_credentials

# 1. Sync all SIMs from 1NCE
echo "Syncing all SIMs..."
curl -s -X POST "http://localhost:8000/api/v1/sims/sync-all" \
  -H "X-API-Key: $API_KEY" | jq

# 2. List all SIMs
echo -e "\nListing SIMs..."
curl -s -X GET "http://localhost:8000/api/v1/sims?page_size=10" \
  -H "X-API-Key: $API_KEY" | jq

# 3. Get specific SIM details
ICCID="89490200001234567890"
echo -e "\nGetting SIM details..."
curl -s -X GET "http://localhost:8000/api/v1/sims/$ICCID" \
  -H "X-API-Key: $API_KEY" | jq

# 4. Check connectivity
echo -e "\nChecking connectivity..."
curl -s -X GET "http://localhost:8000/api/v1/sims/$ICCID/connectivity" \
  -H "X-API-Key: $API_KEY" | jq

# 5. Get usage data
echo -e "\nGetting usage data..."
curl -s -X GET "http://localhost:8000/api/v1/sims/$ICCID/usage" \
  -H "X-API-Key: $API_KEY" | jq
```

### Workflow 3: Manage Quotas

```bash
#!/bin/bash
source .api_credentials
ICCID="89490200001234567890"

# 1. Check data quota
echo "Checking data quota..."
DATA_QUOTA=$(curl -s -X GET "http://localhost:8000/api/v1/sims/$ICCID/quota/data" \
  -H "X-API-Key: $API_KEY")

echo $DATA_QUOTA | jq

REMAINING=$(echo $DATA_QUOTA | jq -r '.remaining_volume')
THRESHOLD=$(echo $DATA_QUOTA | jq -r '.threshold_volume')

# 2. Top-up if below threshold
if [ "$REMAINING" -lt "$THRESHOLD" ]; then
  echo -e "\nQuota below threshold, topping up 1GB..."
  curl -s -X POST "http://localhost:8000/api/v1/sims/$ICCID/topup" \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d '{
      "quota_type": "data",
      "volume": 1073741824
    }' | jq
fi

# 3. Check SMS quota
echo -e "\nChecking SMS quota..."
curl -s -X GET "http://localhost:8000/api/v1/sims/$ICCID/quota/sms" \
  -H "X-API-Key: $API_KEY" | jq
```

### Workflow 4: Send SMS and Monitor

```bash
#!/bin/bash
source .api_credentials
ICCID="89490200001234567890"

# 1. Send SMS
echo "Sending SMS..."
curl -s -X POST "http://localhost:8000/api/v1/sims/$ICCID/sms" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Test message from API"
  }' | jq

# 2. Wait a bit
sleep 5

# 3. Check events
echo -e "\nChecking SMS events..."
curl -s -X GET "http://localhost:8000/api/v1/sims/$ICCID/events?event_type=sms" \
  -H "X-API-Key: $API_KEY" | jq

# 4. Sync usage to see SMS count
echo -e "\nSyncing usage..."
curl -s -X POST "http://localhost:8000/api/v1/sims/$ICCID/usage/sync" \
  -H "X-API-Key: $API_KEY" | jq
```

---

## Testing with Postman

### Import Collection

1. **Create new collection:** "IOT SIM Management API"

2. **Set collection variables:**
   - `base_url`: `http://localhost:8000`
   - `access_token`: (will be set by login)
   - `api_key`: (will be set after creation)

### Collection Structure

```
IOT SIM Management API/
├── 1. Health/
│   ├── Basic Health Check
│   ├── Readiness Check
│   └── Liveness Check
├── 2. Authentication/
│   ├── Login (sets access_token)
│   ├── Refresh Token
│   ├── Get Current User
│   ├── Register User
│   ├── Create API Key (sets api_key)
│   ├── List API Keys
│   └── Revoke API Key
├── 3. SIM Management/
│   ├── List SIMs
│   ├── Create SIM
│   ├── Get SIM
│   ├── Update SIM
│   ├── Sync SIM
│   └── Sync All SIMs
├── 4. Usage & Quotas/
│   ├── Get Usage
│   ├── Sync Usage
│   ├── Get Data Quota
│   ├── Get SMS Quota
│   └── Top-up Quota
├── 5. SMS/
│   └── Send SMS
├── 6. Connectivity/
│   ├── Get Connectivity
│   └── Reset Connectivity
├── 7. Events/
│   └── Get Events
├── 8. Scheduler/
│   ├── Get Status
│   └── Get Job Details
└── 9. Metrics/
    └── Get Metrics
```

### Environment Setup

**Pre-request Script (Collection level):**
```javascript
// Automatically add authorization header
const access_token = pm.collectionVariables.get("access_token");
const api_key = pm.collectionVariables.get("api_key");

if (access_token) {
    pm.request.headers.add({
        key: "Authorization",
        value: `Bearer ${access_token}`
    });
} else if (api_key) {
    pm.request.headers.add({
        key: "X-API-Key",
        value: api_key
    });
}
```

### Example Request: Login

**Request:**
- Method: `POST`
- URL: `{{base_url}}/api/v1/auth/login`
- Headers: `Content-Type: application/json`
- Body (raw JSON):
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Tests Script:**
```javascript
// Save access token
const response = pm.response.json();
pm.collectionVariables.set("access_token", response.access_token);
pm.collectionVariables.set("refresh_token", response.refresh_token);

// Test response
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Access token received", function () {
    pm.expect(response.access_token).to.exist;
});
```

### Example Request: Create API Key

**Request:**
- Method: `POST`
- URL: `{{base_url}}/api/v1/auth/api-keys`
- Headers: `Authorization: Bearer {{access_token}}`
- Body (raw JSON):
```json
{
  "name": "Postman Test Key",
  "expires_in_days": 30
}
```

**Tests Script:**
```javascript
// Save API key
const response = pm.response.json();
pm.collectionVariables.set("api_key", response.key);

pm.test("API key created", function () {
    pm.expect(response.key).to.exist;
});
```

---

## Testing with curl

### Complete curl Examples

**1. Health Check:**
```bash
curl http://localhost:8000/health
```

**2. Login:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }' | jq
```

**3. Save Token to Environment:**
```bash
# Extract and save token
ACCESS_TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.access_token')

# Export for use in other commands
export ACCESS_TOKEN
echo "Token saved: $ACCESS_TOKEN"
```

**4. Get Current User:**
```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq
```

**5. Create SIM:**
```bash
curl -X POST "http://localhost:8000/api/v1/sims" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "iccid": "89490200001234567890",
    "imsi": "901405123456789",
    "msisdn": "+491234567890",
    "label": "Test SIM"
  }' | jq
```

**6. List SIMs with Pagination:**
```bash
curl -X GET "http://localhost:8000/api/v1/sims?page=1&page_size=10" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq
```

**7. Sync SIM:**
```bash
ICCID="89490200001234567890"
curl -X POST "http://localhost:8000/api/v1/sims/$ICCID/sync" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq
```

**8. Get Usage:**
```bash
# Get all usage
curl -X GET "http://localhost:8000/api/v1/sims/$ICCID/usage" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq

# Get usage with date filter
START_DATE="2024-11-01T00:00:00Z"
END_DATE="2024-11-17T23:59:59Z"
curl -X GET "http://localhost:8000/api/v1/sims/$ICCID/usage?start_date=$START_DATE&end_date=$END_DATE" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq
```

**9. Check Quota:**
```bash
curl -X GET "http://localhost:8000/api/v1/sims/$ICCID/quota/data" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq
```

**10. Top-up Quota:**
```bash
curl -X POST "http://localhost:8000/api/v1/sims/$ICCID/topup" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "quota_type": "data",
    "volume": 1073741824
  }' | jq
```

**11. Send SMS:**
```bash
curl -X POST "http://localhost:8000/api/v1/sims/$ICCID/sms" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello from API"
  }' | jq
```

**12. Get Connectivity:**
```bash
curl -X GET "http://localhost:8000/api/v1/sims/$ICCID/connectivity" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq
```

**13. Get Events:**
```bash
curl -X GET "http://localhost:8000/api/v1/sims/$ICCID/events" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq
```

### Helper Script for Testing

Save as `test_api.sh`:

```bash
#!/bin/bash

# Configuration
BASE_URL="http://localhost:8000"
USERNAME="admin"
PASSWORD="admin123"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print success
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error
error() {
    echo -e "${RED}✗ $1${NC}"
}

# Test health
echo "Testing health endpoint..."
HEALTH=$(curl -s "$BASE_URL/health")
if echo $HEALTH | jq -e '.status == "healthy"' > /dev/null; then
    success "Health check passed"
else
    error "Health check failed"
    exit 1
fi

# Login
echo -e "\nLogging in..."
TOKEN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}")

ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token')

if [ "$ACCESS_TOKEN" != "null" ] && [ -n "$ACCESS_TOKEN" ]; then
    success "Login successful"
    export ACCESS_TOKEN
else
    error "Login failed"
    exit 1
fi

# Get current user
echo -e "\nGetting current user..."
USER=$(curl -s -X GET "$BASE_URL/api/v1/auth/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

if echo $USER | jq -e '.username' > /dev/null; then
    USERNAME=$(echo $USER | jq -r '.username')
    success "User: $USERNAME"
else
    error "Failed to get user"
fi

# List SIMs
echo -e "\nListing SIMs..."
SIMS=$(curl -s -X GET "$BASE_URL/api/v1/sims?page_size=5" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

TOTAL=$(echo $SIMS | jq -r '.total')
success "Total SIMs: $TOTAL"

# Get scheduler status (if superuser)
echo -e "\nGetting scheduler status..."
SCHEDULER=$(curl -s -X GET "$BASE_URL/api/v1/scheduler/status" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

if echo $SCHEDULER | jq -e '.enabled' > /dev/null; then
    ENABLED=$(echo $SCHEDULER | jq -r '.enabled')
    RUNNING=$(echo $SCHEDULER | jq -r '.running')
    success "Scheduler enabled: $ENABLED, running: $RUNNING"
fi

echo -e "\n${GREEN}All tests passed!${NC}"
```

Make it executable and run:
```bash
chmod +x test_api.sh
./test_api.sh
```

---

## Troubleshooting

### Common Issues

#### 1. Cannot Connect to API

**Problem:** `curl: (7) Failed to connect to localhost:8000`

**Solutions:**
```bash
# Check if services are running
docker-compose ps

# Check logs
docker-compose logs api

# Restart services
docker-compose restart
```

#### 2. 401 Unauthorized

**Problem:** API returns 401 even with token

**Solutions:**
```bash
# Check token expiration
echo $ACCESS_TOKEN | cut -d '.' -f 2 | base64 -d | jq

# Get new token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Verify token format
echo "Bearer $ACCESS_TOKEN"  # Should have 'Bearer ' prefix
```

#### 3. Database Connection Error

**Problem:** API fails to start, database connection errors in logs

**Solutions:**
```bash
# Check database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Reset database
docker-compose down -v
docker-compose up -d
docker-compose exec api alembic upgrade head
```

#### 4. 1NCE API Connection Failed

**Problem:** Sync endpoints return 500 errors

**Solutions:**
```bash
# Verify credentials in .env
cat .env | grep ONCE

# Test 1NCE API manually
curl -X POST "https://api.1nce.com/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=$ONCE_CLIENT_ID&client_secret=$ONCE_CLIENT_SECRET"

# Check API logs
docker-compose logs -f api | grep once
```

#### 5. Scheduler Not Running

**Problem:** Background jobs not executing

**Solutions:**
```bash
# Check scheduler status (superuser only)
curl -X GET "http://localhost:8000/api/v1/scheduler/status" \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Enable scheduler in .env
echo "ENABLE_SCHEDULER=true" >> .env

# Restart API
docker-compose restart api
```

#### 6. Invalid ICCID Format

**Problem:** 400 error when creating SIM

**Solutions:**
```bash
# ICCID must be 19-20 digits
# Valid: 89490200001234567890 (20 digits)
# Invalid: 894902000012345 (too short)

# Test with valid ICCID
curl -X POST "http://localhost:8000/api/v1/sims" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "iccid": "89490200001234567890"
  }'
```

### Debugging Tips

**1. Enable Debug Mode:**
```bash
# In .env
DEBUG=true
LOG_LEVEL=DEBUG

# Restart
docker-compose restart api
```

**2. View Detailed Logs:**
```bash
# Follow logs
docker-compose logs -f api

# Filter for errors
docker-compose logs api | grep ERROR

# Check specific endpoint
docker-compose logs api | grep "/api/v1/sims"
```

**3. Check API Documentation:**
```bash
# Interactive API docs
open http://localhost:8000/docs

# Try endpoints directly in browser
```

**4. Validate JSON:**
```bash
# Use jq to validate JSON
echo '{"username":"admin","password":"admin123"}' | jq

# Pretty print responses
curl ... | jq '.'
```

**5. Test Database:**
```bash
# Connect to database
docker-compose exec db psql -U user -d iot_sim_db

# Check tables
\dt

# Check SIM count
SELECT COUNT(*) FROM sims;
```

---

## API Rate Limits

**Default Limits:**
- General API: 60 requests/minute
- Login endpoint: Special handling (avoid brute force)
- Burst: 10 requests

**Headers in Response:**
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1700145600
```

**Handling Rate Limits:**
```bash
# Check rate limit headers
curl -i http://localhost:8000/api/v1/sims \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Use exponential backoff
for i in {1..5}; do
  curl ... && break
  sleep $((2**i))
done
```

---

## Security Best Practices

1. **Never commit .env files**
   ```bash
   # Add to .gitignore
   echo ".env" >> .gitignore
   echo ".api_credentials" >> .gitignore
   ```

2. **Rotate API keys regularly**
   ```bash
   # Create new key
   curl -X POST "http://localhost:8000/api/v1/auth/api-keys" ...

   # Update application
   # Then revoke old key
   curl -X DELETE "http://localhost:8000/api/v1/auth/api-keys/1" ...
   ```

3. **Use HTTPS in production**
   ```bash
   # Always use https:// in production
   BASE_URL="https://api.yourdomain.com"
   ```

4. **Limit API key permissions**
   - Create separate keys for different services
   - Set appropriate expiration dates
   - Monitor usage via logs

5. **Secure credentials**
   ```bash
   # Use environment variables
   export ONCE_CLIENT_ID="..."
   export ONCE_CLIENT_SECRET="..."

   # Use secrets management in production
   # (AWS Secrets Manager, HashiCorp Vault, etc.)
   ```

---

## Next Steps

1. **Explore Interactive Docs:** http://localhost:8000/docs
2. **Set Up Monitoring:** Configure Grafana dashboards
3. **Automate Workflows:** Create scripts for common tasks
4. **Production Deployment:** See [DEPLOYMENT.md](DEPLOYMENT.md)
5. **Frontend Development:** Build React/Streamlit frontends

---

## Additional Resources

- **API Specification:** [API_SPECIFICATION.md](API_SPECIFICATION.md)
- **Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **Development Guide:** [DEVELOPER_QUICKSTART.md](DEVELOPER_QUICKSTART.md)
- **Production Guide:** [PRODUCTION_READINESS.md](../PRODUCTION_READINESS.md)
- **1NCE API Docs:** https://help.1nce.com/dev-hub/reference

---

## Support

For issues or questions:
- Check logs: `docker-compose logs -f api`
- Review documentation in `/docs`
- Check GitHub issues
- Interactive API docs: http://localhost:8000/docs

---

**Last Updated:** 2024-11-17
**Version:** 1.0.0
