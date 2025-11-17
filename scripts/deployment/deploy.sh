#!/bin/bash
#
# Production Deployment Script for IOT SIM Management Platform
# Usage: ./deploy.sh [environment]
# Example: ./deploy.sh production
#

set -e

ENVIRONMENT=${1:-production}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=================================================="
echo "IOT SIM Management Platform - Deployment"
echo "=================================================="
echo "Environment: $ENVIRONMENT"
echo "Project Root: $PROJECT_ROOT"
echo ""

cd "$PROJECT_ROOT"

# Load environment variables
if [ -f ".env.$ENVIRONMENT" ]; then
    echo "✓ Loading environment variables from .env.$ENVIRONMENT"
    export $(cat ".env.$ENVIRONMENT" | grep -v '^#' | xargs)
else
    echo "✗ Error: .env.$ENVIRONMENT file not found"
    exit 1
fi

# Pre-deployment checks
echo ""
echo "Running pre-deployment checks..."

# Check Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "✗ Error: Docker is not running"
    exit 1
fi
echo "✓ Docker is running"

# Check required environment variables
REQUIRED_VARS=(
    "SECRET_KEY"
    "DATABASE_URL"
    "REDIS_URL"
    "ONCE_CLIENT_ID"
    "ONCE_CLIENT_SECRET"
)

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo "✗ Error: Required environment variable $var is not set"
        exit 1
    fi
done
echo "✓ All required environment variables are set"

# Check disk space
AVAILABLE_SPACE=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
if [ "$AVAILABLE_SPACE" -lt 10 ]; then
    echo "✗ Warning: Less than 10GB disk space available"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
echo "✓ Sufficient disk space available"

# Backup database
echo ""
echo "Creating database backup..."
BACKUP_DIR="$PROJECT_ROOT/backups"
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/db_backup_$(date +%Y%m%d_%H%M%S).sql"

if docker-compose -f docker-compose.prod.yml ps db | grep -q "Up"; then
    docker-compose -f docker-compose.prod.yml exec -T db \
        pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > "$BACKUP_FILE" 2>/dev/null || true
    if [ -f "$BACKUP_FILE" ] && [ -s "$BACKUP_FILE" ]; then
        echo "✓ Database backup created: $BACKUP_FILE"
    else
        echo "⚠ Warning: Database backup failed (may be first deployment)"
    fi
else
    echo "⚠ No existing database to backup"
fi

# Pull latest images
echo ""
echo "Pulling latest Docker images..."
docker-compose -f docker-compose.prod.yml pull

# Stop existing containers
echo ""
echo "Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down

# Start new containers
echo ""
echo "Starting new containers..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
echo ""
echo "Waiting for services to be healthy..."
MAX_WAIT=120
WAIT_TIME=0

while [ $WAIT_TIME -lt $MAX_WAIT ]; do
    if docker-compose -f docker-compose.prod.yml ps | grep -q "unhealthy"; then
        echo "Waiting for services... ($WAIT_TIME/$MAX_WAIT seconds)"
        sleep 5
        WAIT_TIME=$((WAIT_TIME + 5))
    else
        break
    fi
done

if [ $WAIT_TIME -ge $MAX_WAIT ]; then
    echo "✗ Error: Services did not become healthy in time"
    docker-compose -f docker-compose.prod.yml logs --tail=50
    exit 1
fi

# Run database migrations
echo ""
echo "Running database migrations..."
docker-compose -f docker-compose.prod.yml exec -T api alembic upgrade head

# Health check
echo ""
echo "Running health checks..."
HEALTH_URL="http://localhost:8000/health"
HEALTH_RESPONSE=$(curl -s "$HEALTH_URL" || echo "failed")

if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo "✓ Health check passed"
else
    echo "✗ Error: Health check failed"
    echo "Response: $HEALTH_RESPONSE"
    exit 1
fi

# Show running containers
echo ""
echo "Running containers:"
docker-compose -f docker-compose.prod.yml ps

# Show logs
echo ""
echo "Recent logs (last 20 lines):"
docker-compose -f docker-compose.prod.yml logs --tail=20 api

echo ""
echo "=================================================="
echo "Deployment completed successfully!"
echo "=================================================="
echo "API URL: http://localhost:8000"
echo "Docs: http://localhost:8000/docs"
echo "Health: http://localhost:8000/health"
echo "Grafana: http://localhost:3000"
echo ""
echo "To view logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "To stop: docker-compose -f docker-compose.prod.yml down"
echo "=================================================="
