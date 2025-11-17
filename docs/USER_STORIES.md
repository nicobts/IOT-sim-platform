# User Stories - FastAPI 1NCE Server

## Epic 1: Authentication & Authorization

### US-001: System Authentication with 1NCE API
**As a** system administrator  
**I want** the system to automatically authenticate with the 1NCE API  
**So that** I can access 1NCE services programmatically

**Acceptance Criteria:**
- [ ] System obtains OAuth 2.0 bearer token using client credentials
- [ ] Token is cached in Redis with 1-hour TTL
- [ ] Token automatically refreshes 10 minutes before expiry
- [ ] Failed authentication returns clear error messages
- [ ] Authentication metrics are tracked (success/failure rate)

**Technical Notes:**
- Use Basic Auth with username:password for token endpoint
- Endpoint: `POST /oauth/token`
- Response includes `access_token`, `token_type`, `expires_in`

**Priority:** P0 (Blocker)  
**Story Points:** 5

---

### US-002: API Key Authentication for Users
**As a** API consumer  
**I want** to authenticate to the FastAPI server using API keys  
**So that** I can securely access the API endpoints

**Acceptance Criteria:**
- [ ] Users can generate API keys via endpoint or admin panel
- [ ] API keys are securely hashed before storage
- [ ] Each request validates API key from header or query param
- [ ] Invalid keys return 401 Unauthorized
- [ ] API key usage is logged for audit purposes
- [ ] Keys can be revoked/disabled
- [ ] Keys can have expiration dates

**Technical Notes:**
```python
# Header: X-API-Key: {api_key}
# OR Query: ?api_key={api_key}
```

**Priority:** P0 (Blocker)  
**Story Points:** 8

---

## Epic 2: SIM Management

### US-003: List All SIM Cards
**As a** developer  
**I want** to retrieve a list of all SIM cards  
**So that** I can see the current inventory

**Acceptance Criteria:**
- [ ] GET /api/v1/sims returns paginated list of SIMs
- [ ] Response includes: iccid, imsi, msisdn, status, label
- [ ] Supports filtering by status, organization_id
- [ ] Supports pagination (page, page_size)
- [ ] Supports sorting (by date, status, etc.)
- [ ] Results are cached for 5 minutes
- [ ] Response time < 500ms for 1000 SIMs

**Example Response:**
```json
{
  "total": 1000,
  "page": 1,
  "page_size": 50,
  "data": [
    {
      "iccid": "8988228666000000001",
      "imsi": "901288000000001",
      "msisdn": "882360000000001",
      "status": "Enabled",
      "label": "Production Device A",
      "ip_address": "10.0.0.1",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

**Priority:** P0 (Blocker)  
**Story Points:** 5

---

### US-004: Get Single SIM Details
**As a** developer  
**I want** to retrieve detailed information about a specific SIM  
**So that** I can view its complete configuration and status

**Acceptance Criteria:**
- [ ] GET /api/v1/sims/{iccid} returns full SIM details
- [ ] Includes all fields from 1NCE API response
- [ ] Returns 404 if SIM not found
- [ ] Response time < 200ms
- [ ] Results cached for 2 minutes

**Priority:** P0 (Blocker)  
**Story Points:** 3

---

### US-005: Create/Update SIM Configuration
**As a** administrator  
**I want** to create or update SIM configurations  
**So that** I can manage device settings

**Acceptance Criteria:**
- [ ] POST /api/v1/sims creates configuration for multiple SIMs
- [ ] PUT /api/v1/sims/{iccid} updates single SIM configuration
- [ ] Validates ICCID format
- [ ] Validates all required fields
- [ ] Returns updated SIM data
- [ ] Logs all configuration changes
- [ ] Invalidates cache after update

**Priority:** P1 (High)  
**Story Points:** 5

---

### US-006: Get SIM Status
**As a** developer  
**I want** to check the current status of a SIM  
**So that** I can determine if it's active, suspended, or terminated

**Acceptance Criteria:**
- [ ] GET /api/v1/sims/{iccid}/status returns current status
- [ ] Includes status details: enabled, expired, suspended, etc.
- [ ] Response time < 200ms
- [ ] Status changes trigger cache invalidation

**Possible Status Values:**
- Enabled
- Disabled
- Expired
- Suspended
- Terminated

**Priority:** P0 (Blocker)  
**Story Points:** 3

---

### US-007: Get SIM Connectivity Information
**As a** IoT engineer  
**I want** to see real-time connectivity details of a SIM  
**So that** I can troubleshoot connectivity issues

**Acceptance Criteria:**
- [ ] GET /api/v1/sims/{iccid}/connectivity returns connection info
- [ ] Includes: cell_id, signal_strength, RAT, operator, country
- [ ] Shows online/offline status
- [ ] Response time < 300ms
- [ ] Data stored in time-series database

**Example Response:**
```json
{
  "iccid": "8988228666000000001",
  "connected": true,
  "cell_id": "12345",
  "signal_strength": -75,
  "rat": "LTE",
  "country_code": "DE",
  "operator_name": "Deutsche Telekom",
  "timestamp": "2024-11-16T10:30:00Z"
}
```

**Priority:** P1 (High)  
**Story Points:** 5

---

### US-008: Reset SIM Connectivity
**As a** support engineer  
**I want** to reset a SIM's connectivity  
**So that** I can resolve connection issues remotely

**Acceptance Criteria:**
- [ ] POST /api/v1/sims/{iccid}/reset initiates connectivity reset
- [ ] Confirms reset was triggered successfully
- [ ] Logs reset action with timestamp and user
- [ ] Returns expected reset completion time
- [ ] Sends notification when reset completes

**Priority:** P1 (High)  
**Story Points:** 3

---

## Epic 3: Usage Tracking & Analytics

### US-009: Get SIM Usage Data
**As a** billing analyst  
**I want** to retrieve usage data for a SIM  
**So that** I can track data consumption and costs

**Acceptance Criteria:**
- [ ] GET /api/v1/sims/{iccid}/usage returns usage data
- [ ] Supports date range filtering (start_date, end_date)
- [ ] Returns daily granularity data
- [ ] Includes: volume_rx, volume_tx, total_volume
- [ ] Includes SMS counts (MO/MT)
- [ ] Data stored in TimescaleDB
- [ ] Response time < 1s for 90 days of data

**Example Response:**
```json
{
  "iccid": "8988228666000000001",
  "period": {
    "start": "2024-10-01",
    "end": "2024-10-31"
  },
  "usage": [
    {
      "date": "2024-10-01",
      "volume_rx": 1048576,
      "volume_tx": 524288,
      "total_volume": 1572864,
      "sms_mo": 5,
      "sms_mt": 3
    }
  ],
  "summary": {
    "total_volume": 47185920,
    "total_sms_mo": 150,
    "total_sms_mt": 90
  }
}
```

**Priority:** P0 (Blocker)  
**Story Points:** 8

---

### US-010: Automated Usage Sync
**As a** system  
**I want** to automatically sync usage data from 1NCE API  
**So that** the database always has up-to-date usage information

**Acceptance Criteria:**
- [ ] Background job runs every hour
- [ ] Syncs usage data for all active SIMs
- [ ] Only fetches new data (incremental sync)
- [ ] Handles API rate limits gracefully
- [ ] Logs sync statistics (records added, errors, duration)
- [ ] Sends alerts on sync failures
- [ ] Retries failed syncs with exponential backoff

**Priority:** P0 (Blocker)  
**Story Points:** 8

---

## Epic 4: Quota Management

### US-011: Get Data Quota
**As a** developer  
**I want** to check a SIM's data quota  
**So that** I can monitor remaining data allowance

**Acceptance Criteria:**
- [ ] GET /api/v1/sims/{iccid}/quota/data returns data quota info
- [ ] Includes: total volume, remaining, status, threshold
- [ ] Shows last top-up date and amount
- [ ] Indicates if auto-reload is enabled
- [ ] Response time < 200ms

**Example Response:**
```json
{
  "iccid": "8988228666000000001",
  "quota_type": "data",
  "volume": 524288000,
  "remaining": 314572800,
  "status": "Active",
  "threshold_percentage": 80,
  "threshold_volume": 419430400,
  "auto_reload": true,
  "last_volume_added": 104857600,
  "last_status_change_date": "2024-11-01T00:00:00Z"
}
```

**Priority:** P1 (High)  
**Story Points:** 5

---

### US-012: Get SMS Quota
**As a** developer  
**I want** to check a SIM's SMS quota  
**So that** I can monitor remaining SMS allowance

**Acceptance Criteria:**
- [ ] GET /api/v1/sims/{iccid}/quota/sms returns SMS quota info
- [ ] Includes: total SMS, remaining, status
- [ ] Shows MO/MT breakdown if available
- [ ] Response time < 200ms

**Priority:** P1 (High)  
**Story Points:** 3

---

### US-013: Single SIM Top-Up
**As a** administrator  
**I want** to add data or SMS quota to a single SIM  
**So that** I can extend service for specific devices

**Acceptance Criteria:**
- [ ] POST /api/v1/sims/{iccid}/topup adds quota
- [ ] Supports data volume (in bytes) or SMS count
- [ ] Validates top-up amount
- [ ] Returns updated quota information
- [ ] Logs top-up transaction
- [ ] Sends confirmation notification

**Request Example:**
```json
{
  "quota_type": "data",
  "volume": 104857600  // 100MB in bytes
}
```

**Priority:** P1 (High)  
**Story Points:** 5

---

### US-014: Bulk Top-Up
**As a** administrator  
**I want** to top-up multiple SIMs at once  
**So that** I can efficiently manage large fleets

**Acceptance Criteria:**
- [ ] POST /api/v1/sims/topup accepts list of ICCIDs
- [ ] Processes top-ups asynchronously
- [ ] Returns job ID for tracking progress
- [ ] Provides endpoint to check job status
- [ ] Generates summary report (success/failed)
- [ ] Handles partial failures gracefully

**Request Example:**
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

**Priority:** P2 (Medium)  
**Story Points:** 8

---

### US-015: Enable Auto Top-Up
**As a** administrator  
**I want** to enable automatic top-up for SIMs  
**So that** devices never run out of data unexpectedly

**Acceptance Criteria:**
- [ ] POST /api/v1/sims/auto-topup enables auto top-up
- [ ] Configures threshold percentage (e.g., 80%)
- [ ] Configures top-up amount
- [ ] Applies to single SIM or multiple SIMs
- [ ] Background job monitors quotas every 30 minutes
- [ ] Triggers top-up when threshold reached
- [ ] Logs all auto top-up actions

**Priority:** P2 (Medium)  
**Story Points:** 8

---

## Epic 5: SMS Management

### US-016: List SMS Messages
**As a** developer  
**I want** to retrieve SMS messages for a SIM  
**So that** I can see communication history

**Acceptance Criteria:**
- [ ] GET /api/v1/sims/{iccid}/sms returns SMS list
- [ ] Includes both MO (mobile-originated) and MT (mobile-terminated)
- [ ] Supports filtering by direction (MO/MT)
- [ ] Supports date range filtering
- [ ] Paginated results
- [ ] Response time < 500ms

**Example Response:**
```json
{
  "iccid": "8988228666000000001",
  "total": 50,
  "sms": [
    {
      "id": "sms-12345",
      "direction": "MT",
      "message": "Device alert triggered",
      "timestamp": "2024-11-16T10:30:00Z",
      "status": "delivered"
    }
  ]
}
```

**Priority:** P2 (Medium)  
**Story Points:** 5

---

### US-017: Send SMS
**As a** developer  
**I want** to send an SMS to a SIM  
**So that** I can communicate with IoT devices

**Acceptance Criteria:**
- [ ] POST /api/v1/sims/{iccid}/sms sends SMS
- [ ] Validates message length (max 160 chars standard)
- [ ] Returns SMS ID for tracking
- [ ] Validates SIM is SMS-capable
- [ ] Queues SMS if SIM is offline
- [ ] Provides delivery status endpoint

**Request Example:**
```json
{
  "message": "Reboot device",
  "encoding": "GSM7"
}
```

**Priority:** P2 (Medium)  
**Story Points:** 5

---

### US-018: Get SMS Details
**As a** developer  
**I want** to check the status of a sent SMS  
**So that** I can confirm message delivery

**Acceptance Criteria:**
- [ ] GET /api/v1/sims/{iccid}/sms/{id} returns SMS details
- [ ] Shows delivery status (sent, delivered, failed)
- [ ] Shows timestamps (sent, delivered)
- [ ] Shows error reason if failed

**Priority:** P3 (Low)  
**Story Points:** 3

---

## Epic 6: Events & Monitoring

### US-019: Get SIM Events
**As a** support engineer  
**I want** to view event history for a SIM  
**So that** I can troubleshoot issues

**Acceptance Criteria:**
- [ ] GET /api/v1/sims/{iccid}/events returns event list
- [ ] Includes: activation, suspension, quota changes, errors
- [ ] Supports date range filtering
- [ ] Supports filtering by event type
- [ ] Paginated results
- [ ] Response time < 500ms

**Event Types:**
- sim_activated
- sim_suspended
- sim_terminated
- quota_threshold_reached
- connectivity_lost
- connectivity_restored
- configuration_changed

**Priority:** P2 (Medium)  
**Story Points:** 5

---

### US-020: Real-Time Alerts
**As a** system administrator  
**I want** to receive alerts for critical events  
**So that** I can respond to issues quickly

**Acceptance Criteria:**
- [ ] System monitors for alert conditions
- [ ] Sends alerts via webhook/email/Slack
- [ ] Configurable alert rules
- [ ] Alert types: quota threshold, connectivity loss, API errors
- [ ] Includes relevant context in alerts
- [ ] Supports alert deduplication (don't spam)

**Priority:** P2 (Medium)  
**Story Points:** 8

---

## Epic 7: Order & Product Management

### US-021: List Orders
**As a** procurement manager  
**I want** to view all orders  
**So that** I can track SIM purchases

**Acceptance Criteria:**
- [ ] GET /api/v1/orders returns order list
- [ ] Includes: order ID, date, status, items, total
- [ ] Supports filtering by status, date range
- [ ] Paginated results

**Priority:** P3 (Low)  
**Story Points:** 5

---

### US-022: Create Order
**As a** procurement manager  
**I want** to create new SIM orders  
**So that** I can purchase additional capacity

**Acceptance Criteria:**
- [ ] POST /api/v1/orders creates new order
- [ ] Validates product availability
- [ ] Calculates total cost
- [ ] Returns order confirmation
- [ ] Integrates with 1NCE order API

**Priority:** P3 (Low)  
**Story Points:** 8

---

### US-023: View Product Catalog
**As a** developer  
**I want** to view available products  
**So that** I can see pricing and features

**Acceptance Criteria:**
- [ ] GET /api/v1/products returns product list
- [ ] Includes: name, description, pricing, features
- [ ] Cached for 1 hour
- [ ] Response time < 300ms

**Priority:** P3 (Low)  
**Story Points:** 3

---

## Epic 8: Support & Limits

### US-024: Manage Global Limits
**As a** administrator  
**I want** to set global usage limits  
**So that** I can control costs and prevent abuse

**Acceptance Criteria:**
- [ ] GET /api/v1/sims/limits returns current limits
- [ ] POST /api/v1/sims/limits updates limits
- [ ] Limits apply to all SIMs by default
- [ ] Can set: daily data limit, monthly data limit, SMS limits
- [ ] System enforces limits in real-time
- [ ] Sends alerts when limits approached

**Priority:** P2 (Medium)  
**Story Points:** 8

---

### US-025: SIM-Specific Limits
**As a** administrator  
**I want** to set limits for specific SIMs  
**So that** I can have granular control over usage

**Acceptance Criteria:**
- [ ] GET /api/v1/sims/{service}/limits returns SIM limits
- [ ] Limits override global limits
- [ ] Can set per-SIM budgets
- [ ] Can whitelist/blacklist destinations

**Priority:** P3 (Low)  
**Story Points:** 5

---

## Epic 9: System Administration

### US-026: Health Check
**As a** DevOps engineer  
**I want** to check system health  
**So that** I can monitor service availability

**Acceptance Criteria:**
- [ ] GET /health returns basic health status
- [ ] GET /health/ready checks all dependencies (DB, Redis, 1NCE API)
- [ ] GET /health/live checks if app is running
- [ ] Response time < 100ms
- [ ] Returns proper HTTP status codes (200, 503)

**Priority:** P0 (Blocker)  
**Story Points:** 3

---

### US-027: Metrics & Observability
**As a** DevOps engineer  
**I want** to collect application metrics  
**So that** I can monitor performance and troubleshoot issues

**Acceptance Criteria:**
- [ ] GET /metrics returns Prometheus metrics
- [ ] Tracks: request count, latency, error rate
- [ ] Tracks: 1NCE API call count, latency, errors
- [ ] Tracks: cache hit/miss rate
- [ ] Tracks: background job execution times
- [ ] Includes business metrics (active SIMs, daily usage)

**Priority:** P1 (High)  
**Story Points:** 8

---

## Non-Functional Requirements

### NFR-001: Performance
- API response time: p95 < 500ms, p99 < 1s
- Support 100 concurrent requests
- Handle 10,000+ SIMs efficiently

### NFR-002: Reliability
- Uptime: 99.9%
- Automatic retry on 1NCE API failures
- Graceful degradation when dependencies unavailable

### NFR-003: Security
- All endpoints require authentication
- Secrets stored in environment variables
- API keys securely hashed
- HTTPS only in production
- Rate limiting: 100 req/min per API key

### NFR-004: Scalability
- Horizontally scalable (stateless API)
- Database connection pooling
- Redis caching for read-heavy operations
- Background jobs for heavy operations

### NFR-005: Maintainability
- Code coverage > 80%
- Automated tests in CI/CD
- Clear logging and error messages
- API documentation (OpenAPI/Swagger)
- Structured logging (JSON)

---

## Prioritization

**P0 (Must Have - MVP):**
- US-001, US-002 (Authentication)
- US-003, US-004, US-006 (Basic SIM info)
- US-009, US-010 (Usage tracking)
- US-026 (Health checks)

**P1 (Should Have - Week 3-4):**
- US-005 (SIM config)
- US-007, US-008 (Connectivity)
- US-011, US-012, US-013 (Quota management)
- US-027 (Metrics)

**P2 (Could Have - Week 5-6):**
- US-014, US-015 (Bulk & auto top-up)
- US-016, US-017 (SMS)
- US-019, US-020 (Events & alerts)
- US-024 (Global limits)

**P3 (Nice to Have - Future):**
- US-021, US-022, US-023 (Orders & products)
- US-018 (SMS details)
- US-025 (SIM-specific limits)

---

## Story Point Reference

- **1-2 points**: Simple endpoint, CRUD operation, < 1 day
- **3-5 points**: Standard feature, moderate complexity, 1-2 days
- **8 points**: Complex feature, multiple components, 3-5 days
- **13 points**: Epic-level, needs breakdown, > 1 week

**Total Story Points: 165**  
**Estimated Timeline: 8-10 weeks** (with team of 2-3 developers)
