# IOT SIM Platform - Monitoring Stack

Comprehensive monitoring solution using Prometheus and Grafana.

## Overview

The monitoring stack provides real-time insights into:
- **API Performance**: Request rates, response times, error rates
- **System Health**: CPU, memory, disk usage
- **Database Metrics**: Connection pools, query performance
- **SIM Metrics**: Status distribution, data usage, quota consumption
- **1NCE API**: Integration health and performance

## Components

### Prometheus
- **Metrics Collection**: Scrapes metrics every 15-30 seconds
- **Data Storage**: 90-day retention (configurable)
- **Alert Evaluation**: Real-time alert rule evaluation
- **Access**: http://localhost:9090

### Grafana
- **Visualization**: Interactive dashboards and charts
- **Alerting**: Alert notifications (when configured)
- **User Management**: Multi-user support
- **Access**: http://localhost:3001 (admin/admin)

## Dashboards

### 1. Backend API Dashboard (`backend-api`)
**Metrics Displayed:**
- Request rate (gauge)
- HTTP requests by endpoint (time series)
- Response time p95/p99 (time series)
- HTTP status codes breakdown (stacked area)
- Database connection pool (time series)

**Use Cases:**
- Monitor API performance
- Identify slow endpoints
- Track error rates
- Monitor database connections

**Refresh Rate:** 10 seconds

### 2. System Overview Dashboard (`system-overview`)
**Metrics Displayed:**
- Backend API status (stat)
- Requests per minute (stat with trend)
- Response time p95 (stat with threshold)
- Error rate percentage (stat with threshold)
- CPU usage (time series)
- Memory usage (time series)
- Redis metrics (connections, memory)
- PostgreSQL connections (time series)

**Use Cases:**
- Overall system health check
- Resource utilization monitoring
- Quick status overview
- Capacity planning

**Refresh Rate:** 10 seconds

### 3. SIM Metrics Dashboard (`sim-metrics`)
**Metrics Displayed:**
- Total SIMs (stat)
- Active SIMs (stat)
- Activation rate (stat with thresholds)
- SIMs by status (pie chart)
- SIMs by operator (bar chart)
- Data usage by SIM (time series)
- Quota usage percentage (time series)

**Use Cases:**
- Monitor SIM fleet health
- Track data consumption
- Identify quota issues
- Analyze operator distribution

**Refresh Rate:** 30 seconds

## Alert Rules

### Backend Alerts
| Alert | Condition | For | Severity |
|-------|-----------|-----|----------|
| BackendDown | API unreachable | 1m | Critical |
| HighErrorRate | Error rate > 5% | 5m | Warning |
| HighResponseTime | p95 > 1s | 5m | Warning |
| HighDatabaseConnections | < 2 connections available | 5m | Warning |

### System Alerts
| Alert | Condition | For | Severity |
|-------|-----------|-----|----------|
| HighMemoryUsage | Memory > 90% | 5m | Warning |
| HighDiskUsage | Disk > 85% | 5m | Warning |

### Redis Alerts
| Alert | Condition | For | Severity |
|-------|-----------|-----|----------|
| RedisHighMemory | Memory > 90% | 5m | Warning |
| RedisConnectionFailures | No clients connected | 2m | Critical |

### SIM Alerts
| Alert | Condition | For | Severity |
|-------|-----------|-----|----------|
| QuotaUsageHigh | Quota > 85% | 10m | Warning |
| QuotaNearlyExhausted | Quota > 95% | 5m | Critical |
| AbnormalDataUsageSpike | Usage > 3x average | 10m | Warning |
| SIMStatusChanged | Status distribution changed | 1m | Info |

### 1NCE API Alerts
| Alert | Condition | For | Severity |
|-------|-----------|-----|----------|
| OnceAPIHighErrorRate | Error rate > 10% | 5m | Warning |
| OnceAPISlowResponses | p95 > 5s | 5m | Warning |
| OnceAPIUnavailable | API down | 2m | Critical |

## Configuration

### Prometheus Configuration
Located in `prometheus/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'backend-api'
    metrics_path: '/api/v1/metrics'
    scrape_interval: 30s
    static_configs:
      - targets: ['backend:8000']
```

### Alert Rules
Located in `prometheus/alerts.yml`:

```yaml
groups:
  - name: backend_alerts
    interval: 30s
    rules:
      - alert: BackendDown
        expr: up{job="backend-api"} == 0
        for: 1m
        labels:
          severity: critical
```

### Grafana Provisioning
- **Datasources**: `grafana/provisioning/datasources/prometheus.yml`
- **Dashboards**: `grafana/provisioning/dashboards/default.yml`
- **Dashboard JSON**: `grafana/dashboards/*.json`

## Usage

### Access Grafana
1. Open http://localhost:3001
2. Login with default credentials (admin/admin)
3. Navigate to Dashboards → Browse
4. Select a dashboard:
   - Backend API Dashboard
   - System Overview Dashboard
   - SIM Metrics Dashboard

### Access Prometheus
1. Open http://localhost:9090
2. Use the query interface to explore metrics
3. Check Alerts → View active alerts
4. Use Graph to visualize custom queries

### Example Prometheus Queries

**Request rate:**
```promql
rate(http_requests_total[5m])
```

**Error rate:**
```promql
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))
```

**Response time p95:**
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

**Database connections:**
```promql
db_pool_size - db_pool_available
```

**SIM quota usage:**
```promql
(quota_used / quota_total) * 100
```

## Metrics Exposed by Backend

The FastAPI backend exposes metrics at `/api/v1/metrics`:

### HTTP Metrics
- `http_requests_total` - Total HTTP requests (counter)
- `http_request_duration_seconds` - Request duration (histogram)
- `http_requests_in_progress` - Requests currently being processed (gauge)

### Database Metrics
- `db_pool_size` - Database connection pool size (gauge)
- `db_pool_available` - Available connections (gauge)
- `db_query_duration_seconds` - Query execution time (histogram)

### Cache Metrics
- `cache_hits_total` - Cache hits (counter)
- `cache_misses_total` - Cache misses (counter)
- `cache_size_bytes` - Cache size in bytes (gauge)

### SIM Metrics
- `sim_total_count` - Total number of SIMs (gauge)
- `sim_active_count` - Number of active SIMs (gauge)
- `sim_status_count` - SIMs by status (gauge with labels)
- `sim_operator_count` - SIMs by operator (gauge with labels)
- `sim_data_usage_bytes` - Data usage per SIM (counter)
- `quota_total` - Total quota (gauge with labels)
- `quota_used` - Used quota (gauge with labels)

### 1NCE API Metrics
- `once_api_requests_total` - Total requests to 1NCE API (counter)
- `once_api_errors_total` - API errors (counter)
- `once_api_duration_seconds` - Request duration (histogram)
- `once_api_up` - API availability (gauge)

## Troubleshooting

### Prometheus Not Scraping Metrics
1. Check Prometheus targets: http://localhost:9090/targets
2. Verify backend is exposing metrics: `curl http://localhost:8000/api/v1/metrics`
3. Check Prometheus logs: `docker-compose logs prometheus`

### Grafana Dashboards Not Loading
1. Check Grafana logs: `docker-compose logs grafana`
2. Verify datasource is configured: Grafana → Configuration → Data Sources
3. Check dashboard provisioning: Grafana → Configuration → Plugins

### Alerts Not Firing
1. Check alert rules: http://localhost:9090/alerts
2. Verify alert expressions are correct
3. Check evaluation intervals in `prometheus.yml`
4. Review Prometheus logs for rule evaluation errors

### High Cardinality Issues
If you notice Prometheus using too much memory:
1. Reduce label cardinality (e.g., don't use user IDs as labels)
2. Increase scrape intervals
3. Reduce retention period
4. Consider using recording rules for complex queries

## Best Practices

### Dashboard Design
- Use consistent time ranges across panels
- Add descriptions to panels
- Use appropriate visualization types
- Set meaningful thresholds
- Group related metrics together

### Alert Configuration
- Set appropriate thresholds (not too sensitive)
- Use "for" duration to avoid flapping
- Include meaningful descriptions
- Test alerts in staging first
- Document alert runbooks

### Metric Naming
- Follow Prometheus naming conventions
- Use descriptive names
- Include units in names (e.g., `_bytes`, `_seconds`)
- Use labels for dimensions
- Keep cardinality low

### Performance
- Use recording rules for expensive queries
- Set appropriate retention periods
- Monitor Prometheus resource usage
- Use remote storage for long-term retention
- Optimize scrape intervals based on needs

## Production Deployment

### Resource Requirements
- **Prometheus**: 1-2 CPU cores, 2-4GB RAM
- **Grafana**: 0.5-1 CPU cores, 512MB-1GB RAM

### Security
1. Change default Grafana password
2. Enable authentication for Prometheus (use reverse proxy)
3. Use TLS for all connections
4. Restrict network access (internal only)
5. Regular security updates

### High Availability
For production, consider:
- Prometheus federation or Thanos
- Grafana clustering
- External alert manager
- Remote storage backend
- Load balancing

### Backup
Backup these directories regularly:
- `prometheus_data/` - Metrics data
- `grafana_data/` - Dashboards and settings
- `monitoring/prometheus/` - Configuration files
- `monitoring/grafana/` - Provisioning files

## Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [PromQL Tutorial](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)
