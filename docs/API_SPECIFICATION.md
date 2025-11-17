# API Specification - FastAPI 1NCE Server

## Overview

**Base URL:** `https://api.example.com`  
**API Version:** v1  
**Protocol:** HTTPS only  
**Format:** JSON  
**Authentication:** API Key or JWT Bearer Token

---

## Authentication

### API Key Authentication

**Method 1: Header**
```http
GET /api/v1/sims
X-API-Key: sk_live_abc123def456...
```

**Method 2: Query Parameter**
```http
GET /api/v1/sims?api_key=sk_live_abc123def456...
```

### JWT Authentication

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Usage:**
```http
GET /api/v1/sims
Authorization: Bearer eyJhbGc...
```

---

## Common Response Formats

### Success Response

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "timestamp": "2024-11-16T10:30:00Z",
    "request_id": "req_123abc"
  }
}
```

### Error Response

```json
{
  "success": false,
  "error": {
    "code": "INVALID_ICCID",
    "message": "The provided ICCID is invalid",
    "details": {
      "field": "iccid",
      "reason": "Must be 19-20 digits"
    }
  },
  "meta": {
    "timestamp": "2024-11-16T10:30:00Z",
    "request_id": "req_123abc"
  }
}
```

### Paginated Response

```json
{
  "success": true,
  "data": [ ... ],
  "pagination": {
    "total": 1000,
    "page": 1,
    "page_size": 50,
    "total_pages": 20,
    "has_next": true,
    "has_prev": false
  },
  "meta": {
    "timestamp": "2024-11-16T10:30:00Z"
  }
}
```

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_API_KEY` | 401 | API key is invalid or expired |
| `UNAUTHORIZED` | 401 | Authentication required |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `INVALID_ICCID` | 400 | Invalid ICCID format |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `UPSTREAM_ERROR` | 502 | 1NCE API error |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `VALIDATION_ERROR` | 422 | Request validation failed |

---

## Rate Limiting

**Default Limits:**
- 100 requests per minute per API key
- 1000 requests per hour per API key

**Headers:**
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1700140800
```

**429 Response:**
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 45 seconds.",
    "details": {
      "retry_after": 45
    }
  }
}
```

---

## Endpoints

## 1. Authentication

### POST /api/v1/auth/login

User login to obtain JWT token.

**Request:**
```json
{
  "username": "user@example.com",
  "password": "password123"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "username": "user@example.com",
    "role": "admin"
  }
}
```

---

### POST /api/v1/auth/refresh

Refresh JWT token.

**Request:**
```json
{
  "refresh_token": "eyJhbGc..."
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

### GET /api/v1/auth/me

Get current user information.

**Response:** `200 OK`
```json
{
  "id": 1,
  "username": "user@example.com",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "admin",
  "is_active": true,
  "created_at": "2024-01-15T10:00:00Z"
}
```

---

## 2. SIM Management

### GET /api/v1/sims

List all SIM cards with filtering and pagination.

**Query Parameters:**
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `page` | integer | Page number | 1 |
| `page_size` | integer | Items per page (max 100) | 50 |
| `status` | string | Filter by status | - |
| `organization_id` | integer | Filter by organization | - |
| `search` | string | Search by ICCID, label | - |
| `sort_by` | string | Sort field | created_at |
| `sort_order` | string | asc or desc | desc |

**Example Request:**
```http
GET /api/v1/sims?page=1&page_size=20&status=Enabled&sort_by=label
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "iccid": "8988228666000000001",
      "imsi": "901288000000001",
      "msisdn": "882360000000001",
      "status": "Enabled",
      "label": "Production Device A",
      "ip_address": "10.0.0.1",
      "imei": "123456789012345",
      "organization_id": 100,
      "activation_date": "2024-01-15T10:00:00Z",
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-11-16T10:30:00Z"
    }
  ],
  "pagination": {
    "total": 1000,
    "page": 1,
    "page_size": 20,
    "total_pages": 50
  }
}
```

---

### GET /api/v1/sims/{iccid}

Get details of a specific SIM card.

**Path Parameters:**
- `iccid` (string, required): SIM card ICCID

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "id": 1,
    "iccid": "8988228666000000001",
    "imsi": "901288000000001",
    "msisdn": "882360000000001",
    "status": "Enabled",
    "label": "Production Device A",
    "ip_address": "10.0.0.1",
    "ipv6_address": "2001:db8::1",
    "imei": "123456789012345",
    "imei_lock": false,
    "organization_id": 100,
    "current_rat": "LTE",
    "current_country": "DE",
    "current_operator": "Deutsche Telekom",
    "activation_date": "2024-01-15T10:00:00Z",
    "tags": ["production", "iot"],
    "metadata": {
      "device_type": "sensor",
      "location": "warehouse-a"
    },
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-11-16T10:30:00Z",
    "last_synced_at": "2024-11-16T10:25:00Z"
  }
}
```

**Error:** `404 Not Found`
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "SIM card not found"
  }
}
```

---

### POST /api/v1/sims

Create SIM configuration for multiple SIMs.

**Request:**
```json
{
  "sims": [
    {
      "iccid": "8988228666000000001",
      "label": "Production Device A",
      "imei_lock": false
    },
    {
      "iccid": "8988228666000000002",
      "label": "Production Device B"
    }
  ]
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "data": {
    "created": 2,
    "failed": 0,
    "sims": [
      {
        "iccid": "8988228666000000001",
        "status": "created"
      },
      {
        "iccid": "8988228666000000002",
        "status": "created"
      }
    ]
  }
}
```

---

### PUT /api/v1/sims/{iccid}

Update SIM configuration.

**Request:**
```json
{
  "label": "Updated Device Label",
  "imei_lock": true,
  "tags": ["production", "critical"],
  "metadata": {
    "location": "warehouse-b",
    "device_type": "sensor"
  }
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "iccid": "8988228666000000001",
    "label": "Updated Device Label",
    "imei_lock": true,
    "tags": ["production", "critical"],
    "metadata": {
      "location": "warehouse-b",
      "device_type": "sensor"
    },
    "updated_at": "2024-11-16T10:35:00Z"
  }
}
```

---

### GET /api/v1/sims/{iccid}/status

Get current status of a SIM card.

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "iccid": "8988228666000000001",
    "status": "Enabled",
    "status_details": {
      "is_active": true,
      "is_expired": false,
      "is_suspended": false
    },
    "activation_date": "2024-01-15T10:00:00Z",
    "last_checked": "2024-11-16T10:30:00Z"
  }
}
```

---

### GET /api/v1/sims/{iccid}/connectivity

Get connectivity information for a SIM.

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "iccid": "8988228666000000001",
    "connected": true,
    "connection_details": {
      "cell_id": "12345",
      "signal_strength": -75,
      "signal_quality": 85,
      "rat": "LTE",
      "country_code": "DE",
      "operator_name": "Deutsche Telekom",
      "mcc": "262",
      "mnc": "01",
      "apn": "iot.1nce.net"
    },
    "timestamp": "2024-11-16T10:30:00Z"
  }
}
```

---

### POST /api/v1/sims/{iccid}/reset

Reset SIM connectivity.

**Request:** (Empty body or optional parameters)
```json
{
  "reset_type": "soft"
}
```

**Response:** `202 Accepted`
```json
{
  "success": true,
  "data": {
    "iccid": "8988228666000000001",
    "reset_initiated": true,
    "expected_completion": "2024-11-16T10:35:00Z",
    "status_url": "/api/v1/sims/8988228666000000001/reset/status"
  }
}
```

---

### GET /api/v1/sims/{iccid}/events

Get event history for a SIM.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `start_date` | string (ISO 8601) | Filter events from date |
| `end_date` | string (ISO 8601) | Filter events to date |
| `event_type` | string | Filter by event type |
| `page` | integer | Page number |
| `page_size` | integer | Items per page |

**Response:** `200 OK`
```json
{
  "success": true,
  "data": [
    {
      "id": 1001,
      "event_type": "quota_threshold_reached",
      "event_category": "quota",
      "severity": "warning",
      "description": "Data quota reached 80% threshold",
      "event_data": {
        "threshold": 80,
        "current_usage": 419430400,
        "total_quota": 524288000
      },
      "timestamp": "2024-11-16T09:00:00Z"
    },
    {
      "id": 1000,
      "event_type": "sim_activated",
      "event_category": "status",
      "severity": "info",
      "description": "SIM card activated",
      "timestamp": "2024-01-15T10:00:00Z"
    }
  ],
  "pagination": {
    "total": 50,
    "page": 1,
    "page_size": 20
  }
}
```

---

## 3. Usage Data

### GET /api/v1/sims/{iccid}/usage

Get usage data for a SIM card.

**Query Parameters:**
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `start_date` | string | Start date (ISO 8601) | 30 days ago |
| `end_date` | string | End date (ISO 8601) | today |
| `granularity` | string | daily, weekly, monthly | daily |

**Example Request:**
```http
GET /api/v1/sims/8988228666000000001/usage?start_date=2024-10-01&end_date=2024-10-31&granularity=daily
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "iccid": "8988228666000000001",
    "period": {
      "start": "2024-10-01",
      "end": "2024-10-31"
    },
    "granularity": "daily",
    "usage": [
      {
        "date": "2024-10-01",
        "volume_rx": 1048576,
        "volume_tx": 524288,
        "total_volume": 1572864,
        "sms_mo": 5,
        "sms_mt": 3,
        "session_count": 12
      },
      {
        "date": "2024-10-02",
        "volume_rx": 2097152,
        "volume_tx": 1048576,
        "total_volume": 3145728,
        "sms_mo": 3,
        "sms_mt": 2,
        "session_count": 15
      }
    ],
    "summary": {
      "total_volume": 47185920,
      "total_volume_rx": 31457280,
      "total_volume_tx": 15728640,
      "total_sms_mo": 150,
      "total_sms_mt": 90,
      "average_daily_volume": 1522126,
      "peak_daily_volume": 5242880,
      "peak_date": "2024-10-15"
    }
  }
}
```

---

## 4. Quota Management

### GET /api/v1/sims/{iccid}/quota/data

Get data quota information.

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "iccid": "8988228666000000001",
    "quota_type": "data",
    "volume": 524288000,
    "used_volume": 314572800,
    "remaining_volume": 209715200,
    "percentage_used": 60.0,
    "status": "Active",
    "threshold_percentage": 80,
    "threshold_volume": 419430400,
    "threshold_reached": false,
    "auto_reload": true,
    "auto_reload_amount": 104857600,
    "last_volume_added": 104857600,
    "last_status_change_date": "2024-11-01T00:00:00Z"
  }
}
```

---

### GET /api/v1/sims/{iccid}/quota/sms

Get SMS quota information.

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "iccid": "8988228666000000001",
    "quota_type": "sms",
    "volume": 250,
    "used_volume": 145,
    "remaining_volume": 105,
    "percentage_used": 58.0,
    "status": "Active",
    "threshold_percentage": 80,
    "threshold_reached": false
  }
}
```

---

### POST /api/v1/sims/{iccid}/topup

Add quota to a single SIM.

**Request:**
```json
{
  "quota_type": "data",
  "volume": 104857600
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "iccid": "8988228666000000001",
    "quota_type": "data",
    "volume_added": 104857600,
    "new_total": 629145600,
    "new_remaining": 314572800,
    "transaction_id": "topup_abc123",
    "timestamp": "2024-11-16T10:40:00Z"
  }
}
```

---

### POST /api/v1/sims/topup

Bulk top-up for multiple SIMs.

**Request:**
```json
{
  "sims": [
    {
      "iccid": "8988228666000000001",
      "quota_type": "data",
      "volume": 104857600
    },
    {
      "iccid": "8988228666000000002",
      "quota_type": "data",
      "volume": 104857600
    }
  ]
}
```

**Response:** `202 Accepted`
```json
{
  "success": true,
  "data": {
    "job_id": "job_xyz789",
    "status": "processing",
    "total_sims": 2,
    "status_url": "/api/v1/jobs/job_xyz789"
  }
}
```

---

### POST /api/v1/sims/auto-topup

Enable or configure auto top-up.

**Request:**
```json
{
  "sims": ["8988228666000000001", "8988228666000000002"],
  "quota_type": "data",
  "threshold_percentage": 80,
  "topup_amount": 104857600,
  "enabled": true
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "configured_sims": 2,
    "failed_sims": 0,
    "details": [
      {
        "iccid": "8988228666000000001",
        "status": "configured",
        "threshold": 80,
        "topup_amount": 104857600
      },
      {
        "iccid": "8988228666000000002",
        "status": "configured",
        "threshold": 80,
        "topup_amount": 104857600
      }
    ]
  }
}
```

---

## 5. SMS Management

### GET /api/v1/sims/{iccid}/sms

List SMS messages for a SIM.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `direction` | string | MO or MT |
| `start_date` | string | Filter from date |
| `end_date` | string | Filter to date |
| `status` | string | Filter by status |
| `page` | integer | Page number |
| `page_size` | integer | Items per page |

**Response:** `200 OK`
```json
{
  "success": true,
  "data": [
    {
      "id": 501,
      "sms_id": "sms_abc123",
      "direction": "MT",
      "message": "Device alert triggered",
      "encoding": "GSM7",
      "status": "delivered",
      "created_at": "2024-11-16T10:30:00Z",
      "sent_at": "2024-11-16T10:30:05Z",
      "delivered_at": "2024-11-16T10:30:10Z"
    }
  ],
  "pagination": {
    "total": 50,
    "page": 1,
    "page_size": 20
  }
}
```

---

### POST /api/v1/sims/{iccid}/sms

Send an SMS to a SIM.

**Request:**
```json
{
  "message": "Reboot device now",
  "encoding": "GSM7"
}
```

**Response:** `202 Accepted`
```json
{
  "success": true,
  "data": {
    "sms_id": "sms_xyz789",
    "iccid": "8988228666000000001",
    "message": "Reboot device now",
    "status": "pending",
    "created_at": "2024-11-16T10:45:00Z",
    "status_url": "/api/v1/sims/8988228666000000001/sms/sms_xyz789"
  }
}
```

---

### GET /api/v1/sims/{iccid}/sms/{id}

Get SMS details and delivery status.

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "id": 501,
    "sms_id": "sms_xyz789",
    "iccid": "8988228666000000001",
    "direction": "MT",
    "message": "Reboot device now",
    "encoding": "GSM7",
    "status": "delivered",
    "created_at": "2024-11-16T10:45:00Z",
    "sent_at": "2024-11-16T10:45:05Z",
    "delivered_at": "2024-11-16T10:45:15Z"
  }
}
```

---

### DELETE /api/v1/sims/{iccid}/sms/{id}

Delete/cancel an SMS.

**Response:** `204 No Content`

---

## 6. Limits Management

### GET /api/v1/sims/limits

Get global limits.

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "daily_data_limit": 10485760,
    "monthly_data_limit": 314572800,
    "daily_sms_limit": 100,
    "monthly_sms_limit": 1000,
    "enforce_limits": true
  }
}
```

---

### POST /api/v1/sims/limits

Set global limits.

**Request:**
```json
{
  "daily_data_limit": 10485760,
  "monthly_data_limit": 314572800,
  "daily_sms_limit": 100,
  "monthly_sms_limit": 1000,
  "enforce_limits": true
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "daily_data_limit": 10485760,
    "monthly_data_limit": 314572800,
    "daily_sms_limit": 100,
    "monthly_sms_limit": 1000,
    "enforce_limits": true,
    "updated_at": "2024-11-16T10:50:00Z"
  }
}
```

---

## 7. Health & Metrics

### GET /health

Basic health check.

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "timestamp": "2024-11-16T10:55:00Z"
}
```

---

### GET /health/ready

Readiness check (all dependencies).

**Response:** `200 OK`
```json
{
  "status": "ready",
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "once_api": "healthy"
  },
  "timestamp": "2024-11-16T10:55:00Z"
}
```

**Error:** `503 Service Unavailable`
```json
{
  "status": "not_ready",
  "checks": {
    "database": "healthy",
    "redis": "unhealthy",
    "once_api": "healthy"
  },
  "timestamp": "2024-11-16T10:55:00Z"
}
```

---

### GET /health/live

Liveness check.

**Response:** `200 OK`
```json
{
  "status": "alive",
  "timestamp": "2024-11-16T10:55:00Z"
}
```

---

### GET /metrics

Prometheus metrics endpoint.

**Response:** `200 OK` (Prometheus format)
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/api/v1/sims",status="200"} 1523

# HELP http_request_duration_seconds HTTP request latency
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{method="GET",endpoint="/api/v1/sims",le="0.1"} 1200
http_request_duration_seconds_bucket{method="GET",endpoint="/api/v1/sims",le="0.5"} 1500

# HELP active_sims_total Number of active SIMs
# TYPE active_sims_total gauge
active_sims_total 850
```

---

## Webhooks (Future)

### Webhook Events

Configure webhooks to receive events:

**Event Types:**
- `sim.activated`
- `sim.suspended`
- `quota.threshold_reached`
- `quota.depleted`
- `connectivity.lost`
- `connectivity.restored`
- `sms.received`

**Webhook Payload:**
```json
{
  "event": "quota.threshold_reached",
  "timestamp": "2024-11-16T10:00:00Z",
  "data": {
    "iccid": "8988228666000000001",
    "quota_type": "data",
    "threshold": 80,
    "current_usage": 419430400,
    "total_quota": 524288000
  }
}
```

---

## SDK Examples

### Python

```python
import requests

API_KEY = "sk_live_abc123..."
BASE_URL = "https://api.example.com"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# List SIMs
response = requests.get(
    f"{BASE_URL}/api/v1/sims",
    headers=headers,
    params={"page": 1, "page_size": 20}
)
sims = response.json()

# Get SIM details
response = requests.get(
    f"{BASE_URL}/api/v1/sims/8988228666000000001",
    headers=headers
)
sim = response.json()

# Send SMS
response = requests.post(
    f"{BASE_URL}/api/v1/sims/8988228666000000001/sms",
    headers=headers,
    json={"message": "Hello device"}
)
sms = response.json()
```

### cURL

```bash
# List SIMs
curl -X GET "https://api.example.com/api/v1/sims?page=1&page_size=20" \
  -H "X-API-Key: sk_live_abc123..."

# Get SIM details
curl -X GET "https://api.example.com/api/v1/sims/8988228666000000001" \
  -H "X-API-Key: sk_live_abc123..."

# Top-up SIM
curl -X POST "https://api.example.com/api/v1/sims/8988228666000000001/topup" \
  -H "X-API-Key: sk_live_abc123..." \
  -H "Content-Type: application/json" \
  -d '{"quota_type": "data", "volume": 104857600}'
```

---

## OpenAPI/Swagger Documentation

Interactive API documentation available at:
- **Swagger UI:** `https://api.example.com/docs`
- **ReDoc:** `https://api.example.com/redoc`
- **OpenAPI JSON:** `https://api.example.com/openapi.json`

---

## Versioning

API versioning is done via URL path:
- v1: `/api/v1/...` (current)
- v2: `/api/v2/...` (future)

**Deprecation Policy:**
- 6 months notice before deprecation
- 12 months support for deprecated versions
- Breaking changes require new major version

---

## Best Practices

1. **Always use HTTPS** in production
2. **Store API keys securely** (never in code)
3. **Implement retry logic** with exponential backoff
4. **Handle rate limits** gracefully
5. **Validate all inputs** on client side
6. **Log all API interactions** for debugging
7. **Monitor API health** endpoints
8. **Use pagination** for large result sets

---

See `USER_STORIES.md` for detailed use cases and `ARCHITECTURE.md` for system design.
