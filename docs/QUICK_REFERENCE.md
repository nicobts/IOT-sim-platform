# Quick Reference Guide - IOT SIM Management API

**One-page reference for common operations**

## Quick Start

```bash
# Start services
docker-compose up -d

# Create admin user
docker-compose exec api python scripts/create_admin.py

# Access API docs
open http://localhost:8000/docs
```

## Authentication

### Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### Save Token
```bash
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.access_token')
```

### Create API Key
```bash
curl -X POST "http://localhost:8000/api/v1/auth/api-keys" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Production Key","expires_in_days":365}'
```

## SIM Management

### List SIMs
```bash
curl -X GET "http://localhost:8000/api/v1/sims?page_size=10" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Get SIM Details
```bash
ICCID="89490200001234567890"
curl -X GET "http://localhost:8000/api/v1/sims/$ICCID" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Create SIM
```bash
curl -X POST "http://localhost:8000/api/v1/sims" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "iccid": "89490200001234567890",
    "label": "Production SIM"
  }' | jq
```

### Sync from 1NCE
```bash
# Sync single SIM
curl -X POST "http://localhost:8000/api/v1/sims/$ICCID/sync" \
  -H "Authorization: Bearer $TOKEN" | jq

# Sync all SIMs
curl -X POST "http://localhost:8000/api/v1/sims/sync-all" \
  -H "Authorization: Bearer $TOKEN" | jq
```

## Usage & Quotas

### Get Usage
```bash
curl -X GET "http://localhost:8000/api/v1/sims/$ICCID/usage" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Check Data Quota
```bash
curl -X GET "http://localhost:8000/api/v1/sims/$ICCID/quota/data" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Check SMS Quota
```bash
curl -X GET "http://localhost:8000/api/v1/sims/$ICCID/quota/sms" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Top-up Data (1GB)
```bash
curl -X POST "http://localhost:8000/api/v1/sims/$ICCID/topup" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"quota_type":"data","volume":1073741824}' | jq
```

### Top-up SMS (100)
```bash
curl -X POST "http://localhost:8000/api/v1/sims/$ICCID/topup" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"quota_type":"sms","volume":100}' | jq
```

## SMS

### Send SMS
```bash
curl -X POST "http://localhost:8000/api/v1/sims/$ICCID/sms" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello from API"}' | jq
```

## Connectivity

### Get Connectivity Status
```bash
curl -X GET "http://localhost:8000/api/v1/sims/$ICCID/connectivity" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Reset Connectivity
```bash
curl -X POST "http://localhost:8000/api/v1/sims/$ICCID/connectivity/reset" \
  -H "Authorization: Bearer $TOKEN" | jq
```

## Events

### Get All Events
```bash
curl -X GET "http://localhost:8000/api/v1/sims/$ICCID/events" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Get SMS Events
```bash
curl -X GET "http://localhost:8000/api/v1/sims/$ICCID/events?event_type=sms" \
  -H "Authorization: Bearer $TOKEN" | jq
```

## Scheduler (Admin)

### Get Status
```bash
curl -X GET "http://localhost:8000/api/v1/scheduler/status" \
  -H "Authorization: Bearer $TOKEN" | jq
```

## Helper Scripts

### Test All Endpoints
```bash
./scripts/test_api.sh
```

### Login and Get Token
```bash
TOKEN=$(./scripts/api_workflows.sh login admin admin123)
```

### Monitor SIM
```bash
./scripts/api_workflows.sh monitor $TOKEN 89490200001234567890
```

### Sync All SIMs
```bash
./scripts/api_workflows.sh sync-all $TOKEN
```

## Data Sizes

| Size | Bytes | Usage |
|------|-------|-------|
| 1 MB | 1048576 | ~1000 web pages |
| 10 MB | 10485760 | ~30 min music |
| 100 MB | 104857600 | ~10,000 IoT messages |
| 1 GB | 1073741824 | Standard quota |
| 10 GB | 10737418240 | Heavy usage |

## Common ICCID Formats

- **Length**: 19-20 digits
- **Example**: 89490200001234567890
- **Validation**: Must be numeric only

## Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (deleted) |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 500 | Internal Server Error |

## Environment Variables

```bash
# Required
DATABASE_URL="postgresql+asyncpg://user:password@db:5432/iot_sim_db"
REDIS_URL="redis://redis:6379/0"
ONCE_CLIENT_ID="your-client-id"
ONCE_CLIENT_SECRET="your-client-secret"

# Optional
DEBUG=true
ENABLE_SCHEDULER=true
ENABLE_METRICS=true
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Useful Commands

### Check Service Health
```bash
curl http://localhost:8000/health
```

### View API Logs
```bash
docker-compose logs -f api
```

### Run Migrations
```bash
docker-compose exec api alembic upgrade head
```

### Access Database
```bash
docker-compose exec db psql -U user -d iot_sim_db
```

### Restart Service
```bash
docker-compose restart api
```

## Troubleshooting

### 401 Unauthorized
- Token expired (get new token)
- Invalid token format
- Missing Authorization header

### 404 Not Found
- ICCID doesn't exist
- Wrong endpoint URL
- SIM not synced from 1NCE

### 500 Internal Server Error
- 1NCE API connection failed
- Database connection error
- Check logs: `docker-compose logs api`

### Connection Refused
- Service not running
- Wrong port
- Run: `docker-compose up -d`

## Links

- **API Docs**: http://localhost:8000/docs
- **Full Guide**: [API_USAGE_GUIDE.md](API_USAGE_GUIDE.md)
- **Postman Collection**: [postman_collection.json](postman_collection.json)
- **Test Script**: [../scripts/test_api.sh](../scripts/test_api.sh)
- **Workflows**: [../scripts/api_workflows.sh](../scripts/api_workflows.sh)
