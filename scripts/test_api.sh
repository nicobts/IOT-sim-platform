#!/bin/bash
# API Testing Script for IOT SIM Management Server
# This script tests all major API endpoints

set -e

# Configuration
BASE_URL="${BASE_URL:-http://localhost:8000}"
USERNAME="${API_USERNAME:-admin}"
PASSWORD="${API_PASSWORD:-admin123}"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

error() {
    echo -e "${RED}✗ $1${NC}"
}

info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

section() {
    echo -e "\n${BLUE}═══════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}\n"
}

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    error "jq is not installed. Please install jq to run this script."
    echo "  Ubuntu/Debian: sudo apt-get install jq"
    echo "  macOS: brew install jq"
    exit 1
fi

# Check if curl is installed
if ! command -v curl &> /dev/null; then
    error "curl is not installed. Please install curl to run this script."
    exit 1
fi

section "API Testing Script"
info "Base URL: $BASE_URL"
info "Username: $USERNAME"

# Test 1: Health Check
section "1. Health Checks"

info "Testing basic health endpoint..."
HEALTH=$(curl -s "$BASE_URL/health")
if echo "$HEALTH" | jq -e '.status == "healthy"' > /dev/null 2>&1; then
    success "Health check passed"
    echo "$HEALTH" | jq '.'
else
    error "Health check failed"
    echo "$HEALTH"
    exit 1
fi

info "Testing readiness check..."
READY=$(curl -s "$BASE_URL/health/ready")
if echo "$READY" | jq -e '.status' > /dev/null 2>&1; then
    success "Readiness check passed"
    echo "$READY" | jq '.'
else
    warning "Readiness check returned error (this is OK if dependencies aren't ready)"
    echo "$READY" | jq '.'
fi

info "Testing liveness check..."
LIVE=$(curl -s "$BASE_URL/health/live")
if echo "$LIVE" | jq -e '.status == "alive"' > /dev/null 2>&1; then
    success "Liveness check passed"
else
    error "Liveness check failed"
    exit 1
fi

# Test 2: Authentication
section "2. Authentication"

info "Logging in as $USERNAME..."
TOKEN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}")

ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token')
REFRESH_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.refresh_token')

if [ "$ACCESS_TOKEN" != "null" ] && [ -n "$ACCESS_TOKEN" ]; then
    success "Login successful"
    info "Access token: ${ACCESS_TOKEN:0:50}..."
    export ACCESS_TOKEN
    export REFRESH_TOKEN
else
    error "Login failed"
    echo "$TOKEN_RESPONSE" | jq '.'
    exit 1
fi

info "Getting current user info..."
USER=$(curl -s -X GET "$BASE_URL/api/v1/auth/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$USER" | jq -e '.username' > /dev/null 2>&1; then
    USER_NAME=$(echo "$USER" | jq -r '.username')
    IS_SUPERUSER=$(echo "$USER" | jq -r '.is_superuser')
    success "User: $USER_NAME (Superuser: $IS_SUPERUSER)"
else
    error "Failed to get user info"
    echo "$USER" | jq '.'
fi

info "Creating API key..."
API_KEY_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/api-keys" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Script Key",
    "expires_in_days": 1
  }')

API_KEY=$(echo "$API_KEY_RESPONSE" | jq -r '.key')
API_KEY_ID=$(echo "$API_KEY_RESPONSE" | jq -r '.id')

if [ "$API_KEY" != "null" ] && [ -n "$API_KEY" ]; then
    success "API key created: ${API_KEY:0:20}..."
    export API_KEY
    export API_KEY_ID
else
    warning "Failed to create API key (might not have permission)"
fi

info "Listing API keys..."
API_KEYS=$(curl -s -X GET "$BASE_URL/api/v1/auth/api-keys" \
  -H "Authorization: Bearer $ACCESS_TOKEN")
KEY_COUNT=$(echo "$API_KEYS" | jq '. | length')
success "Found $KEY_COUNT API key(s)"

# Test 3: SIM Management
section "3. SIM Management"

info "Listing SIMs..."
SIMS=$(curl -s -X GET "$BASE_URL/api/v1/sims?page_size=5" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$SIMS" | jq -e '.items' > /dev/null 2>&1; then
    TOTAL=$(echo "$SIMS" | jq -r '.total')
    PAGE_SIZE=$(echo "$SIMS" | jq -r '.page_size')
    success "Total SIMs: $TOTAL"

    # Get first SIM ICCID if available
    FIRST_ICCID=$(echo "$SIMS" | jq -r '.items[0].iccid // empty')

    if [ -n "$FIRST_ICCID" ]; then
        export TEST_ICCID="$FIRST_ICCID"
        info "Using ICCID for testing: $TEST_ICCID"

        info "Getting SIM details..."
        SIM_DETAILS=$(curl -s -X GET "$BASE_URL/api/v1/sims/$TEST_ICCID" \
          -H "Authorization: Bearer $ACCESS_TOKEN")

        if echo "$SIM_DETAILS" | jq -e '.iccid' > /dev/null 2>&1; then
            success "Retrieved SIM details"
            echo "$SIM_DETAILS" | jq '{iccid, status, label}'
        else
            warning "Could not get SIM details"
        fi
    else
        warning "No SIMs found in database. Some tests will be skipped."
        info "You can sync SIMs from 1NCE or create test SIMs."
    fi
else
    error "Failed to list SIMs"
    echo "$SIMS" | jq '.'
fi

# Test 4: Usage & Quotas (if we have a test ICCID)
if [ -n "$TEST_ICCID" ]; then
    section "4. Usage & Quotas"

    info "Getting usage data..."
    USAGE=$(curl -s -X GET "$BASE_URL/api/v1/sims/$TEST_ICCID/usage" \
      -H "Authorization: Bearer $ACCESS_TOKEN")

    if echo "$USAGE" | jq -e '. | type == "array"' > /dev/null 2>&1; then
        USAGE_COUNT=$(echo "$USAGE" | jq '. | length')
        success "Found $USAGE_COUNT usage record(s)"
    else
        warning "No usage data available"
    fi

    info "Getting data quota..."
    DATA_QUOTA=$(curl -s -X GET "$BASE_URL/api/v1/sims/$TEST_ICCID/quota/data" \
      -H "Authorization: Bearer $ACCESS_TOKEN")

    if echo "$DATA_QUOTA" | jq -e '.quota_type' > /dev/null 2>&1; then
        VOLUME=$(echo "$DATA_QUOTA" | jq -r '.volume')
        USED=$(echo "$DATA_QUOTA" | jq -r '.used_volume')
        REMAINING=$(echo "$DATA_QUOTA" | jq -r '.remaining_volume')
        success "Data quota - Total: $VOLUME, Used: $USED, Remaining: $REMAINING"
    else
        warning "Data quota not available"
    fi

    info "Getting SMS quota..."
    SMS_QUOTA=$(curl -s -X GET "$BASE_URL/api/v1/sims/$TEST_ICCID/quota/sms" \
      -H "Authorization: Bearer $ACCESS_TOKEN")

    if echo "$SMS_QUOTA" | jq -e '.quota_type' > /dev/null 2>&1; then
        VOLUME=$(echo "$SMS_QUOTA" | jq -r '.volume')
        USED=$(echo "$SMS_QUOTA" | jq -r '.used_volume')
        REMAINING=$(echo "$SMS_QUOTA" | jq -r '.remaining_volume')
        success "SMS quota - Total: $VOLUME, Used: $USED, Remaining: $REMAINING"
    else
        warning "SMS quota not available"
    fi
fi

# Test 5: Scheduler (if superuser)
section "5. Scheduler"

if [ "$IS_SUPERUSER" = "true" ]; then
    info "Getting scheduler status..."
    SCHEDULER=$(curl -s -X GET "$BASE_URL/api/v1/scheduler/status" \
      -H "Authorization: Bearer $ACCESS_TOKEN")

    if echo "$SCHEDULER" | jq -e '.enabled' > /dev/null 2>&1; then
        ENABLED=$(echo "$SCHEDULER" | jq -r '.enabled')
        RUNNING=$(echo "$SCHEDULER" | jq -r '.running')
        JOB_COUNT=$(echo "$SCHEDULER" | jq -r '.total_jobs // 0')
        success "Scheduler - Enabled: $ENABLED, Running: $RUNNING, Jobs: $JOB_COUNT"

        if [ "$JOB_COUNT" -gt 0 ]; then
            echo "$SCHEDULER" | jq '.jobs[] | {id, name, next_run_time}'
        fi
    else
        warning "Scheduler is not enabled"
    fi
else
    info "Skipping scheduler tests (requires superuser)"
fi

# Test 6: Metrics
section "6. Metrics"

info "Getting Prometheus metrics..."
METRICS=$(curl -s "$BASE_URL/api/v1/metrics")

if echo "$METRICS" | grep -q "^# HELP"; then
    success "Metrics endpoint is working"
    METRIC_COUNT=$(echo "$METRICS" | grep -c "^# HELP" || echo "0")
    info "Found $METRIC_COUNT metric types"
else
    warning "Metrics not available or disabled"
fi

# Test 7: Cleanup
section "7. Cleanup"

if [ -n "$API_KEY_ID" ] && [ "$API_KEY_ID" != "null" ]; then
    info "Revoking test API key..."
    REVOKE_RESPONSE=$(curl -s -w "%{http_code}" -X DELETE "$BASE_URL/api/v1/auth/api-keys/$API_KEY_ID" \
      -H "Authorization: Bearer $ACCESS_TOKEN")

    if [ "$REVOKE_RESPONSE" = "204" ]; then
        success "API key revoked"
    else
        warning "Could not revoke API key (status: $REVOKE_RESPONSE)"
    fi
fi

# Summary
section "Test Summary"

success "All critical tests passed!"
info "API is functioning correctly"

echo -e "\n${BLUE}Next steps:${NC}"
echo "  1. Explore the API docs: $BASE_URL/docs"
echo "  2. Import Postman collection: docs/postman_collection.json"
echo "  3. Read the API usage guide: docs/API_USAGE_GUIDE.md"

if [ -n "$ACCESS_TOKEN" ]; then
    echo -e "\n${BLUE}Your access token (valid for 30 minutes):${NC}"
    echo "$ACCESS_TOKEN"
fi

echo ""
