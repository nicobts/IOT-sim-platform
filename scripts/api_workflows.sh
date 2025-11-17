#!/bin/bash
# Common API Workflows for IOT SIM Management
# This script provides convenient functions for common operations

set -e

# Configuration
BASE_URL="${BASE_URL:-http://localhost:8000}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

success() { echo -e "${GREEN}✓ $1${NC}"; }
error() { echo -e "${RED}✗ $1${NC}"; }
info() { echo -e "${BLUE}ℹ $1${NC}"; }
warning() { echo -e "${YELLOW}⚠ $1${NC}"; }

# Check dependencies
if ! command -v jq &> /dev/null; then
    error "jq is required. Install with: sudo apt-get install jq"
    exit 1
fi

# Function to login and get token
login() {
    local username="${1:-admin}"
    local password="${2:-admin123}"

    info "Logging in as $username..."

    TOKEN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
      -H "Content-Type: application/json" \
      -d "{\"username\":\"$username\",\"password\":\"$password\"}")

    ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token')

    if [ "$ACCESS_TOKEN" != "null" ] && [ -n "$ACCESS_TOKEN" ]; then
        success "Login successful"
        echo "$ACCESS_TOKEN"
        return 0
    else
        error "Login failed"
        echo "$TOKEN_RESPONSE" | jq '.'
        return 1
    fi
}

# Function to create API key
create_api_key() {
    local token="$1"
    local name="${2:-Production Key}"
    local days="${3:-365}"

    info "Creating API key '$name' (expires in $days days)..."

    API_KEY_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/api-keys" \
      -H "Authorization: Bearer $token" \
      -H "Content-Type: application/json" \
      -d "{
        \"name\": \"$name\",
        \"expires_in_days\": $days
      }")

    API_KEY=$(echo "$API_KEY_RESPONSE" | jq -r '.key')

    if [ "$API_KEY" != "null" ] && [ -n "$API_KEY" ]; then
        success "API key created"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "API Key: $API_KEY"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "⚠️  Save this key securely! It won't be shown again."
        echo ""
        return 0
    else
        error "Failed to create API key"
        echo "$API_KEY_RESPONSE" | jq '.'
        return 1
    fi
}

# Function to sync all SIMs from 1NCE
sync_all_sims() {
    local token="$1"

    info "Syncing all SIMs from 1NCE (this may take a while)..."

    SYNC_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/sims/sync-all" \
      -H "Authorization: Bearer $token")

    COUNT=$(echo "$SYNC_RESPONSE" | jq -r '.synced_count // 0')

    if [ "$COUNT" -gt 0 ]; then
        success "Synced $COUNT SIMs"
        return 0
    else
        warning "Sync completed but no SIMs were synced"
        echo "$SYNC_RESPONSE" | jq '.'
        return 1
    fi
}

# Function to list SIMs
list_sims() {
    local token="$1"
    local page_size="${2:-10}"
    local status="${3:-}"

    info "Listing SIMs (page size: $page_size)..."

    URL="$BASE_URL/api/v1/sims?page_size=$page_size"
    if [ -n "$status" ]; then
        URL="$URL&status=$status"
    fi

    SIMS=$(curl -s -X GET "$URL" \
      -H "Authorization: Bearer $token")

    TOTAL=$(echo "$SIMS" | jq -r '.total')
    success "Total SIMs: $TOTAL"

    echo "$SIMS" | jq '.items[] | {iccid, status, label, ip_address}'
}

# Function to get SIM details
get_sim() {
    local token="$1"
    local iccid="$2"

    if [ -z "$iccid" ]; then
        error "ICCID is required"
        return 1
    fi

    info "Getting details for SIM: $iccid"

    SIM=$(curl -s -X GET "$BASE_URL/api/v1/sims/$iccid" \
      -H "Authorization: Bearer $token")

    if echo "$SIM" | jq -e '.iccid' > /dev/null 2>&1; then
        success "SIM found"
        echo "$SIM" | jq '.'
        return 0
    else
        error "SIM not found"
        echo "$SIM" | jq '.'
        return 1
    fi
}

# Function to check quota
check_quota() {
    local token="$1"
    local iccid="$2"
    local quota_type="${3:-data}"

    if [ -z "$iccid" ]; then
        error "ICCID is required"
        return 1
    fi

    info "Checking $quota_type quota for $iccid..."

    QUOTA=$(curl -s -X GET "$BASE_URL/api/v1/sims/$iccid/quota/$quota_type" \
      -H "Authorization: Bearer $token")

    if echo "$QUOTA" | jq -e '.quota_type' > /dev/null 2>&1; then
        VOLUME=$(echo "$QUOTA" | jq -r '.volume')
        USED=$(echo "$QUOTA" | jq -r '.used_volume')
        REMAINING=$(echo "$QUOTA" | jq -r '.remaining_volume')
        PERCENTAGE=$((USED * 100 / VOLUME))

        success "Quota details:"
        echo "  Total:     $VOLUME"
        echo "  Used:      $USED ($PERCENTAGE%)"
        echo "  Remaining: $REMAINING"

        return 0
    else
        error "Could not get quota"
        echo "$QUOTA" | jq '.'
        return 1
    fi
}

# Function to top-up quota
topup_quota() {
    local token="$1"
    local iccid="$2"
    local quota_type="$3"
    local volume="$4"

    if [ -z "$iccid" ] || [ -z "$quota_type" ] || [ -z "$volume" ]; then
        error "Usage: topup_quota TOKEN ICCID TYPE VOLUME"
        echo "  TYPE: data or sms"
        echo "  VOLUME: bytes for data, count for SMS"
        return 1
    fi

    info "Topping up $volume $quota_type for $iccid..."

    TOPUP=$(curl -s -X POST "$BASE_URL/api/v1/sims/$iccid/topup" \
      -H "Authorization: Bearer $token" \
      -H "Content-Type: application/json" \
      -d "{
        \"quota_type\": \"$quota_type\",
        \"volume\": $volume
      }")

    if echo "$TOPUP" | jq -e '.message' > /dev/null 2>&1; then
        success "Top-up successful"
        echo "$TOPUP" | jq -r '.message'
        return 0
    else
        error "Top-up failed"
        echo "$TOPUP" | jq '.'
        return 1
    fi
}

# Function to send SMS
send_sms() {
    local token="$1"
    local iccid="$2"
    local message="$3"

    if [ -z "$iccid" ] || [ -z "$message" ]; then
        error "Usage: send_sms TOKEN ICCID MESSAGE"
        return 1
    fi

    info "Sending SMS to $iccid..."

    SMS=$(curl -s -X POST "$BASE_URL/api/v1/sims/$iccid/sms" \
      -H "Authorization: Bearer $token" \
      -H "Content-Type: application/json" \
      -d "{\"message\": \"$message\"}")

    if echo "$SMS" | jq -e '.message' > /dev/null 2>&1; then
        success "SMS sent"
        return 0
    else
        error "Failed to send SMS"
        echo "$SMS" | jq '.'
        return 1
    fi
}

# Function to monitor SIM
monitor_sim() {
    local token="$1"
    local iccid="$2"

    if [ -z "$iccid" ]; then
        error "ICCID is required"
        return 1
    fi

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Monitoring SIM: $iccid"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Get SIM details
    info "Getting SIM details..."
    SIM=$(curl -s -X GET "$BASE_URL/api/v1/sims/$iccid" \
      -H "Authorization: Bearer $token")

    if echo "$SIM" | jq -e '.iccid' > /dev/null 2>&1; then
        STATUS=$(echo "$SIM" | jq -r '.status')
        LABEL=$(echo "$SIM" | jq -r '.label // "N/A"')
        IP=$(echo "$SIM" | jq -r '.ip_address // "N/A"')

        echo "Status:    $STATUS"
        echo "Label:     $LABEL"
        echo "IP:        $IP"
        echo ""
    fi

    # Get connectivity
    info "Checking connectivity..."
    CONN=$(curl -s -X GET "$BASE_URL/api/v1/sims/$iccid/connectivity" \
      -H "Authorization: Bearer $token")

    if echo "$CONN" | jq -e '.status' > /dev/null 2>&1; then
        CONN_STATUS=$(echo "$CONN" | jq -r '.status')
        NETWORK=$(echo "$CONN" | jq -r '.network // "N/A"')
        echo "Connectivity: $CONN_STATUS"
        echo "Network:      $NETWORK"
        echo ""
    fi

    # Get quotas
    info "Checking data quota..."
    check_quota "$token" "$iccid" "data" 2>/dev/null
    echo ""

    info "Checking SMS quota..."
    check_quota "$token" "$iccid" "sms" 2>/dev/null
    echo ""

    # Get recent usage
    info "Getting recent usage..."
    USAGE=$(curl -s -X GET "$BASE_URL/api/v1/sims/$iccid/usage?page_size=5" \
      -H "Authorization: Bearer $token")

    if echo "$USAGE" | jq -e '. | type == "array"' > /dev/null 2>&1; then
        COUNT=$(echo "$USAGE" | jq '. | length')
        if [ "$COUNT" -gt 0 ]; then
            success "Recent usage records:"
            echo "$USAGE" | jq '.[] | {timestamp, data_volume, sms_mo, sms_mt}'
        else
            info "No usage records found"
        fi
    fi

    echo ""
}

# Interactive menu
show_menu() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  IOT SIM Management - Common Workflows"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Available commands:"
    echo ""
    echo "  1. Setup & Authentication"
    echo "     ./api_workflows.sh login [username] [password]"
    echo "     ./api_workflows.sh create-key TOKEN [name] [days]"
    echo ""
    echo "  2. SIM Management"
    echo "     ./api_workflows.sh sync-all TOKEN"
    echo "     ./api_workflows.sh list TOKEN [page_size]"
    echo "     ./api_workflows.sh get TOKEN ICCID"
    echo "     ./api_workflows.sh monitor TOKEN ICCID"
    echo ""
    echo "  3. Quota Management"
    echo "     ./api_workflows.sh check-quota TOKEN ICCID [data|sms]"
    echo "     ./api_workflows.sh topup TOKEN ICCID TYPE VOLUME"
    echo ""
    echo "  4. Communication"
    echo "     ./api_workflows.sh send-sms TOKEN ICCID MESSAGE"
    echo ""
    echo "Examples:"
    echo "  # Login and save token"
    echo "  TOKEN=\$(./api_workflows.sh login admin admin123)"
    echo ""
    echo "  # List all SIMs"
    echo "  ./api_workflows.sh list \$TOKEN"
    echo ""
    echo "  # Monitor a specific SIM"
    echo "  ./api_workflows.sh monitor \$TOKEN 89490200001234567890"
    echo ""
    echo "  # Top-up 1GB of data"
    echo "  ./api_workflows.sh topup \$TOKEN 89490200001234567890 data 1073741824"
    echo ""
}

# Main script
COMMAND="${1:-help}"

case "$COMMAND" in
    login)
        login "${2:-admin}" "${3:-admin123}"
        ;;
    create-key)
        if [ -z "$2" ]; then
            error "TOKEN is required"
            exit 1
        fi
        create_api_key "$2" "${3:-Production Key}" "${4:-365}"
        ;;
    sync-all)
        if [ -z "$2" ]; then
            error "TOKEN is required"
            exit 1
        fi
        sync_all_sims "$2"
        ;;
    list)
        if [ -z "$2" ]; then
            error "TOKEN is required"
            exit 1
        fi
        list_sims "$2" "${3:-10}" "${4:-}"
        ;;
    get)
        if [ -z "$2" ] || [ -z "$3" ]; then
            error "Usage: $0 get TOKEN ICCID"
            exit 1
        fi
        get_sim "$2" "$3"
        ;;
    check-quota)
        if [ -z "$2" ] || [ -z "$3" ]; then
            error "Usage: $0 check-quota TOKEN ICCID [data|sms]"
            exit 1
        fi
        check_quota "$2" "$3" "${4:-data}"
        ;;
    topup)
        if [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ] || [ -z "$5" ]; then
            error "Usage: $0 topup TOKEN ICCID TYPE VOLUME"
            exit 1
        fi
        topup_quota "$2" "$3" "$4" "$5"
        ;;
    send-sms)
        if [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ]; then
            error "Usage: $0 send-sms TOKEN ICCID MESSAGE"
            exit 1
        fi
        send_sms "$2" "$3" "$4"
        ;;
    monitor)
        if [ -z "$2" ] || [ -z "$3" ]; then
            error "Usage: $0 monitor TOKEN ICCID"
            exit 1
        fi
        monitor_sim "$2" "$3"
        ;;
    help|--help|-h)
        show_menu
        ;;
    *)
        error "Unknown command: $COMMAND"
        show_menu
        exit 1
        ;;
esac
