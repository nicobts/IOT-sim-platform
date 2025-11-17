# Database Schema - FastAPI 1NCE Server

## Overview

This document describes the complete database schema for the 1NCE IoT management platform.

**Database:** PostgreSQL 15+ with TimescaleDB extension

**Key Features:**
- Time-series data for usage metrics
- JSONB for flexible metadata storage
- Proper indexing for fast queries
- Foreign key constraints for data integrity
- Audit timestamps on all tables

---

## Entity Relationship Diagram

```
┌──────────────┐         ┌──────────────┐
│    users     │────────<│   api_keys   │
└──────────────┘         └──────────────┘
                              
┌──────────────┐         ┌──────────────┐
│     sims     │────────<│  sim_usage   │ (Hypertable)
│              │         └──────────────┘
│              │         
│              │────────<│sim_connectivity│ (Hypertable)
│              │         └──────────────┘
│              │         
│              │────────<│  sim_events  │ (Hypertable)
│              │         └──────────────┘
│              │         
│              │────────<│  sim_quotas  │
│              │         └──────────────┘
│              │         
│              │────────<│   sim_sms    │
└──────────────┘         └──────────────┘

┌──────────────┐         ┌──────────────┐
│   orders     │────────<│ order_items  │
└──────────────┘         └──────────────┘

┌──────────────┐
│   products   │
└──────────────┘

┌──────────────┐
│support_tickets│
└──────────────┘
```

---

## Table Definitions

### 1. users

Stores API users who can authenticate with the system.

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('admin', 'user', 'readonly')),
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    organization_id INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login_at TIMESTAMP,
    
    CONSTRAINT users_username_length CHECK (LENGTH(username) >= 3),
    CONSTRAINT users_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_organization ON users(organization_id);
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = TRUE;

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

**Fields:**
- `id`: Primary key
- `username`: Unique username (min 3 chars)
- `email`: Unique email address
- `hashed_password`: Bcrypt hashed password
- `full_name`: User's full name
- `role`: User role (admin, user, readonly)
- `is_active`: Account active status
- `is_superuser`: Superuser privileges
- `organization_id`: Link to organization (future use)
- `created_at`: Account creation timestamp
- `updated_at`: Last update timestamp
- `last_login_at`: Last successful login

---

### 2. api_keys

API keys for programmatic access.

```sql
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    key_prefix VARCHAR(20) NOT NULL,  -- First 8 chars for identification
    name VARCHAR(100),
    description TEXT,
    scopes TEXT[],  -- Array of permission scopes
    is_active BOOLEAN DEFAULT TRUE,
    last_used_at TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT api_keys_valid_expiry CHECK (expires_at IS NULL OR expires_at > created_at)
);

-- Indexes
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_user ON api_keys(user_id);
CREATE INDEX idx_api_keys_active ON api_keys(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_api_keys_expires ON api_keys(expires_at) WHERE expires_at IS NOT NULL;
```

**Fields:**
- `id`: Primary key
- `user_id`: Reference to user
- `key_hash`: Bcrypt hash of the API key
- `key_prefix`: First 8 characters (for display: "sk_live_abc12345...")
- `name`: Friendly name for the key
- `description`: Key purpose description
- `scopes`: Permissions array (e.g., ['read:sims', 'write:sims'])
- `is_active`: Key active status
- `last_used_at`: Last time key was used
- `usage_count`: Number of times key has been used
- `expires_at`: Optional expiration date
- `created_at`: Key creation timestamp

---

### 3. sims

Master table for SIM cards.

```sql
CREATE TABLE sims (
    id SERIAL PRIMARY KEY,
    iccid VARCHAR(20) UNIQUE NOT NULL,
    imsi VARCHAR(15),
    msisdn VARCHAR(15),
    status VARCHAR(20),
    label VARCHAR(255),
    ip_address INET,
    ipv6_address INET,
    imei VARCHAR(15),
    imei_lock BOOLEAN DEFAULT FALSE,
    organization_id INTEGER,
    customer_org_id INTEGER,
    
    -- Network info
    current_rat VARCHAR(20),  -- Radio Access Technology
    current_country VARCHAR(3),
    current_operator VARCHAR(100),
    
    -- Service status
    activation_date TIMESTAMP,
    termination_date TIMESTAMP,
    suspension_date TIMESTAMP,
    
    -- Metadata
    tags JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    
    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_synced_at TIMESTAMP,
    
    CONSTRAINT sims_iccid_format CHECK (iccid ~ '^\d{19,20}$'),
    CONSTRAINT sims_status_valid CHECK (status IN ('Enabled', 'Disabled', 'Expired', 'Suspended', 'Terminated'))
);

-- Indexes
CREATE UNIQUE INDEX idx_sims_iccid ON sims(iccid);
CREATE INDEX idx_sims_status ON sims(status);
CREATE INDEX idx_sims_organization ON sims(organization_id);
CREATE INDEX idx_sims_customer_org ON sims(customer_org_id);
CREATE INDEX idx_sims_activation ON sims(activation_date);
CREATE INDEX idx_sims_tags ON sims USING GIN(tags);
CREATE INDEX idx_sims_metadata ON sims USING GIN(metadata);
CREATE INDEX idx_sims_synced ON sims(last_synced_at);

-- Trigger
CREATE TRIGGER update_sims_updated_at BEFORE UPDATE ON sims
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

**Fields:**
- `id`: Primary key
- `iccid`: Integrated Circuit Card Identifier (19-20 digits)
- `imsi`: International Mobile Subscriber Identity
- `msisdn`: Mobile Station International Subscriber Directory Number
- `status`: Current SIM status
- `label`: User-defined label
- `ip_address`: Assigned IPv4 address
- `ipv6_address`: Assigned IPv6 address
- `imei`: International Mobile Equipment Identity
- `imei_lock`: Whether IMEI is locked to this SIM
- `organization_id`: 1NCE organization ID
- `customer_org_id`: Customer's organization ID
- `current_rat`: Current radio technology (LTE, NB-IoT, etc.)
- `current_country`: ISO country code
- `current_operator`: Mobile network operator
- `activation_date`: When SIM was activated
- `termination_date`: When SIM was terminated
- `suspension_date`: When SIM was suspended
- `tags`: Array of tags (JSON)
- `metadata`: Additional metadata (JSON)
- `created_at`: Record creation timestamp
- `updated_at`: Last update timestamp
- `last_synced_at`: Last sync from 1NCE API

---

### 4. sim_usage (TimescaleDB Hypertable)

Time-series data for SIM usage metrics.

```sql
CREATE TABLE sim_usage (
    id SERIAL,
    sim_id INTEGER NOT NULL REFERENCES sims(id) ON DELETE CASCADE,
    iccid VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    
    -- Data usage (bytes)
    volume_rx BIGINT DEFAULT 0,
    volume_tx BIGINT DEFAULT 0,
    total_volume BIGINT DEFAULT 0,
    
    -- SMS usage
    sms_mo INTEGER DEFAULT 0,  -- Mobile Originated
    sms_mt INTEGER DEFAULT 0,  -- Mobile Terminated
    
    -- Session info
    session_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Convert to hypertable (TimescaleDB)
SELECT create_hypertable('sim_usage', 'timestamp', 
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Indexes
CREATE INDEX idx_usage_sim_time ON sim_usage(sim_id, timestamp DESC);
CREATE INDEX idx_usage_iccid_time ON sim_usage(iccid, timestamp DESC);

-- Compression policy (compress data older than 7 days)
ALTER TABLE sim_usage SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'sim_id'
);

SELECT add_compression_policy('sim_usage', INTERVAL '7 days');

-- Retention policy (drop data older than 2 years)
SELECT add_retention_policy('sim_usage', INTERVAL '2 years');

-- Continuous aggregate for daily rollups
CREATE MATERIALIZED VIEW sim_usage_daily
WITH (timescaledb.continuous) AS
SELECT 
    sim_id,
    iccid,
    time_bucket('1 day', timestamp) AS day,
    SUM(volume_rx) AS total_rx,
    SUM(volume_tx) AS total_tx,
    SUM(total_volume) AS total_volume,
    SUM(sms_mo) AS total_sms_mo,
    SUM(sms_mt) AS total_sms_mt,
    AVG(session_count) AS avg_sessions
FROM sim_usage
GROUP BY sim_id, iccid, day;

-- Refresh policy (update every hour)
SELECT add_continuous_aggregate_policy('sim_usage_daily',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour'
);
```

**Fields:**
- `id`: Primary key (not used in hypertable partitioning)
- `sim_id`: Reference to SIM
- `iccid`: ICCID for quick lookups
- `timestamp`: Data point timestamp
- `volume_rx`: Bytes received (download)
- `volume_tx`: Bytes transmitted (upload)
- `total_volume`: Total data volume
- `sms_mo`: SMS sent by device
- `sms_mt`: SMS received by device
- `session_count`: Number of data sessions
- `created_at`: Record creation timestamp

---

### 5. sim_connectivity (TimescaleDB Hypertable)

Time-series connectivity information.

```sql
CREATE TABLE sim_connectivity (
    id SERIAL,
    sim_id INTEGER NOT NULL REFERENCES sims(id) ON DELETE CASCADE,
    iccid VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    
    -- Connection status
    connected BOOLEAN NOT NULL,
    
    -- Network details
    cell_id VARCHAR(50),
    signal_strength INTEGER,  -- dBm
    signal_quality INTEGER,   -- 0-100
    rat VARCHAR(20),          -- LTE, NB-IoT, 2G, 3G
    
    -- Location
    country_code VARCHAR(3),
    operator_name VARCHAR(100),
    mcc VARCHAR(3),  -- Mobile Country Code
    mnc VARCHAR(3),  -- Mobile Network Code
    
    -- Additional info
    apn VARCHAR(100),
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Convert to hypertable
SELECT create_hypertable('sim_connectivity', 'timestamp',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Indexes
CREATE INDEX idx_connectivity_sim_time ON sim_connectivity(sim_id, timestamp DESC);
CREATE INDEX idx_connectivity_iccid_time ON sim_connectivity(iccid, timestamp DESC);
CREATE INDEX idx_connectivity_status ON sim_connectivity(connected, timestamp DESC);

-- Compression
ALTER TABLE sim_connectivity SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'sim_id'
);

SELECT add_compression_policy('sim_connectivity', INTERVAL '7 days');

-- Retention (6 months for connectivity logs)
SELECT add_retention_policy('sim_connectivity', INTERVAL '6 months');
```

**Fields:**
- `id`: Primary key
- `sim_id`: Reference to SIM
- `iccid`: ICCID for quick lookups
- `timestamp`: Connectivity check timestamp
- `connected`: Connection status (true/false)
- `cell_id`: Cell tower identifier
- `signal_strength`: Signal strength in dBm
- `signal_quality`: Signal quality percentage
- `rat`: Radio Access Technology
- `country_code`: ISO country code
- `operator_name`: Network operator name
- `mcc`: Mobile Country Code
- `mnc`: Mobile Network Code
- `apn`: Access Point Name

---

### 6. sim_events (TimescaleDB Hypertable)

Time-series event log for SIM activities.

```sql
CREATE TABLE sim_events (
    id SERIAL,
    sim_id INTEGER NOT NULL REFERENCES sims(id) ON DELETE CASCADE,
    iccid VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    
    -- Event details
    event_type VARCHAR(50) NOT NULL,
    event_category VARCHAR(30),  -- status, quota, connectivity, sms, etc.
    severity VARCHAR(20),         -- info, warning, error, critical
    
    -- Event data
    event_data JSONB DEFAULT '{}',
    description TEXT,
    
    -- Actor (who/what triggered the event)
    triggered_by VARCHAR(50),  -- user_id, system, api, etc.
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Convert to hypertable
SELECT create_hypertable('sim_events', 'timestamp',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Indexes
CREATE INDEX idx_events_sim_time ON sim_events(sim_id, timestamp DESC);
CREATE INDEX idx_events_iccid_time ON sim_events(iccid, timestamp DESC);
CREATE INDEX idx_events_type ON sim_events(event_type, timestamp DESC);
CREATE INDEX idx_events_category ON sim_events(event_category, timestamp DESC);
CREATE INDEX idx_events_severity ON sim_events(severity, timestamp DESC);
CREATE INDEX idx_events_data ON sim_events USING GIN(event_data);

-- Compression
ALTER TABLE sim_events SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'sim_id,event_type'
);

SELECT add_compression_policy('sim_events', INTERVAL '30 days');

-- Retention (1 year for events)
SELECT add_retention_policy('sim_events', INTERVAL '1 year');
```

**Event Types:**
- `sim_activated`
- `sim_suspended`
- `sim_terminated`
- `sim_resumed`
- `quota_threshold_reached`
- `quota_depleted`
- `quota_added`
- `auto_topup_triggered`
- `connectivity_lost`
- `connectivity_restored`
- `sms_sent`
- `sms_received`
- `sms_failed`
- `config_updated`
- `limit_exceeded`

---

### 7. sim_quotas

Current quota status for SIMs.

```sql
CREATE TABLE sim_quotas (
    id SERIAL PRIMARY KEY,
    sim_id INTEGER NOT NULL REFERENCES sims(id) ON DELETE CASCADE,
    iccid VARCHAR(20) NOT NULL,
    quota_type VARCHAR(10) NOT NULL CHECK (quota_type IN ('data', 'sms')),
    
    -- Quota details
    volume BIGINT,                    -- Total quota (bytes for data, count for SMS)
    used_volume BIGINT DEFAULT 0,     -- Used amount
    remaining_volume BIGINT,          -- Remaining amount
    
    -- Status
    status VARCHAR(20),
    last_volume_added BIGINT,
    last_status_change_date TIMESTAMP,
    
    -- Thresholds
    threshold_percentage INTEGER DEFAULT 80,
    threshold_volume BIGINT,
    threshold_reached BOOLEAN DEFAULT FALSE,
    
    -- Auto reload
    auto_reload BOOLEAN DEFAULT FALSE,
    auto_reload_amount BIGINT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(sim_id, quota_type)
);

-- Indexes
CREATE INDEX idx_quotas_sim ON sim_quotas(sim_id);
CREATE INDEX idx_quotas_iccid ON sim_quotas(iccid);
CREATE INDEX idx_quotas_type ON sim_quotas(quota_type);
CREATE INDEX idx_quotas_threshold ON sim_quotas(threshold_reached) WHERE threshold_reached = TRUE;
CREATE INDEX idx_quotas_auto_reload ON sim_quotas(auto_reload) WHERE auto_reload = TRUE;

-- Trigger
CREATE TRIGGER update_quotas_updated_at BEFORE UPDATE ON sim_quotas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger to calculate remaining volume
CREATE OR REPLACE FUNCTION calculate_remaining_volume()
RETURNS TRIGGER AS $$
BEGIN
    NEW.remaining_volume = NEW.volume - NEW.used_volume;
    
    -- Check threshold
    IF NEW.volume > 0 AND NEW.threshold_volume > 0 THEN
        NEW.threshold_reached = (NEW.used_volume >= NEW.threshold_volume);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_quota_remaining BEFORE INSERT OR UPDATE ON sim_quotas
    FOR EACH ROW EXECUTE FUNCTION calculate_remaining_volume();
```

---

### 8. sim_sms

SMS messages sent to/from SIMs.

```sql
CREATE TABLE sim_sms (
    id SERIAL PRIMARY KEY,
    sim_id INTEGER NOT NULL REFERENCES sims(id) ON DELETE CASCADE,
    iccid VARCHAR(20) NOT NULL,
    sms_id VARCHAR(100) UNIQUE,  -- 1NCE SMS ID
    
    -- Message details
    direction VARCHAR(2) NOT NULL CHECK (direction IN ('MO', 'MT')),
    message TEXT NOT NULL,
    encoding VARCHAR(20) DEFAULT 'GSM7',
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    failed_at TIMESTAMP,
    
    CONSTRAINT sms_message_length CHECK (LENGTH(message) <= 1600)
);

-- Indexes
CREATE INDEX idx_sms_sim ON sim_sms(sim_id);
CREATE INDEX idx_sms_iccid ON sim_sms(iccid);
CREATE INDEX idx_sms_direction ON sim_sms(direction);
CREATE INDEX idx_sms_status ON sim_sms(status);
CREATE INDEX idx_sms_created ON sim_sms(created_at DESC);
CREATE UNIQUE INDEX idx_sms_sms_id ON sim_sms(sms_id) WHERE sms_id IS NOT NULL;
```

**Fields:**
- `id`: Primary key
- `sim_id`: Reference to SIM
- `iccid`: ICCID
- `sms_id`: External SMS ID from 1NCE
- `direction`: MO (mobile-originated) or MT (mobile-terminated)
- `message`: SMS text content
- `encoding`: Character encoding (GSM7, UCS2)
- `status`: pending, sent, delivered, failed
- `error_message`: Error description if failed
- `created_at`: When SMS was created/received
- `sent_at`: When SMS was sent to network
- `delivered_at`: When SMS was delivered
- `failed_at`: When SMS failed

---

### 9. orders

Order management.

```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(100) UNIQUE,  -- External order ID
    user_id INTEGER REFERENCES users(id),
    
    -- Order details
    order_type VARCHAR(50),
    status VARCHAR(20),
    
    -- Financial
    total_amount DECIMAL(10, 2),
    currency VARCHAR(3) DEFAULT 'EUR',
    
    -- Metadata
    order_data JSONB DEFAULT '{}',
    notes TEXT,
    
    -- Timestamps
    ordered_at TIMESTAMP,
    completed_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE UNIQUE INDEX idx_orders_order_id ON orders(order_id);
CREATE INDEX idx_orders_user ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_ordered ON orders(ordered_at DESC);

-- Trigger
CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

---

### 10. order_items

Line items for orders.

```sql
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    
    -- Product details
    product_id INTEGER,
    product_name VARCHAR(255),
    product_sku VARCHAR(100),
    
    -- Quantity and pricing
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2),
    total_price DECIMAL(10, 2),
    
    -- Additional info
    item_data JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);
```

---

### 11. products

Product catalog.

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    product_id VARCHAR(100) UNIQUE,
    
    -- Product details
    name VARCHAR(255) NOT NULL,
    description TEXT,
    sku VARCHAR(100),
    category VARCHAR(50),
    
    -- Pricing
    price DECIMAL(10, 2),
    currency VARCHAR(3) DEFAULT 'EUR',
    
    -- Availability
    is_active BOOLEAN DEFAULT TRUE,
    stock_quantity INTEGER,
    
    -- Specifications
    specifications JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE UNIQUE INDEX idx_products_product_id ON products(product_id);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_active ON products(is_active) WHERE is_active = TRUE;

-- Trigger
CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

---

### 12. support_tickets

Support ticket management.

```sql
CREATE TABLE support_tickets (
    id SERIAL PRIMARY KEY,
    ticket_id VARCHAR(100) UNIQUE,
    user_id INTEGER REFERENCES users(id),
    
    -- Ticket details
    subject VARCHAR(255) NOT NULL,
    description TEXT,
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
    category VARCHAR(50),
    
    -- Assignment
    assigned_to INTEGER REFERENCES users(id),
    
    -- Resolution
    resolution TEXT,
    resolved_at TIMESTAMP,
    
    -- Metadata
    ticket_data JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE UNIQUE INDEX idx_tickets_ticket_id ON support_tickets(ticket_id);
CREATE INDEX idx_tickets_user ON support_tickets(user_id);
CREATE INDEX idx_tickets_status ON support_tickets(status);
CREATE INDEX idx_tickets_priority ON support_tickets(priority);
CREATE INDEX idx_tickets_assigned ON support_tickets(assigned_to);
CREATE INDEX idx_tickets_created ON support_tickets(created_at DESC);

-- Trigger
CREATE TRIGGER update_tickets_updated_at BEFORE UPDATE ON support_tickets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

---

## Views

### Active SIMs View

```sql
CREATE VIEW v_active_sims AS
SELECT 
    s.*,
    q_data.volume AS data_quota,
    q_data.remaining_volume AS data_remaining,
    q_sms.volume AS sms_quota,
    q_sms.remaining_volume AS sms_remaining
FROM sims s
LEFT JOIN sim_quotas q_data ON s.id = q_data.sim_id AND q_data.quota_type = 'data'
LEFT JOIN sim_quotas q_sms ON s.id = q_sms.sim_id AND q_sms.quota_type = 'sms'
WHERE s.status = 'Enabled';
```

### Daily Usage Summary View

```sql
CREATE VIEW v_daily_usage_summary AS
SELECT 
    DATE(timestamp) AS date,
    COUNT(DISTINCT sim_id) AS active_sims,
    SUM(total_volume) AS total_data,
    SUM(sms_mo + sms_mt) AS total_sms
FROM sim_usage
GROUP BY DATE(timestamp)
ORDER BY date DESC;
```

---

## Initialization Script

```sql
-- init_db.sql

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create tables (in order)
\i users.sql
\i api_keys.sql
\i sims.sql
\i sim_usage.sql
\i sim_connectivity.sql
\i sim_events.sql
\i sim_quotas.sql
\i sim_sms.sql
\i orders.sql
\i order_items.sql
\i products.sql
\i support_tickets.sql

-- Create views
\i views.sql

-- Create default admin user
INSERT INTO users (username, email, hashed_password, role, is_superuser)
VALUES ('admin', 'admin@example.com', '$2b$12$...', 'admin', TRUE);
```

---

## Migration Strategy

**Tool:** Alembic

**Migration Process:**
1. Generate migration: `alembic revision --autogenerate -m "description"`
2. Review migration file
3. Test migration: `alembic upgrade head`
4. Rollback if needed: `alembic downgrade -1`

**Example Migration:**
```python
# migrations/versions/001_initial_schema.py

def upgrade():
    # Create tables
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        # ...
    )
    
def downgrade():
    op.drop_table('users')
```

---

## Backup & Recovery

**Backup Schedule:**
- Automated daily backups at 2 AM UTC
- Weekly full backups on Sundays
- Monthly archive to cold storage

**Backup Command:**
```bash
pg_dump -Fc onceiapi > backup_$(date +%Y%m%d).dump
```

**Restore Command:**
```bash
pg_restore -d onceapi -c backup_20241116.dump
```

**Point-in-Time Recovery:**
```bash
# Restore to specific timestamp
pg_restore --target-time '2024-11-16 10:30:00'
```

---

## Performance Optimization

### Query Optimization

```sql
-- Example: Get SIM with usage summary
EXPLAIN ANALYZE
SELECT 
    s.*,
    SUM(u.total_volume) AS total_usage,
    COUNT(u.id) AS data_points
FROM sims s
LEFT JOIN sim_usage u ON s.id = u.sim_id
    AND u.timestamp >= NOW() - INTERVAL '30 days'
WHERE s.status = 'Enabled'
GROUP BY s.id;
```

### Index Maintenance

```sql
-- Rebuild indexes
REINDEX TABLE sims;

-- Analyze table statistics
ANALYZE sims;

-- Vacuum to reclaim space
VACUUM ANALYZE sims;
```

---

## Security Considerations

1. **Row-Level Security (RLS)**
```sql
ALTER TABLE sims ENABLE ROW LEVEL SECURITY;

CREATE POLICY sims_user_policy ON sims
    FOR ALL
    TO app_user
    USING (organization_id = current_setting('app.current_org_id')::int);
```

2. **Encrypted Columns**
```sql
-- Use pgcrypto for sensitive data
CREATE EXTENSION pgcrypto;

-- Encrypt API keys
UPDATE api_keys SET key_hash = crypt(api_key, gen_salt('bf', 12));
```

3. **Audit Logging**
- All destructive operations logged
- Immutable audit trail
- Compliance with GDPR/regulations

---

## Monitoring Queries

```sql
-- Table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Active connections
SELECT count(*) FROM pg_stat_activity;

-- Long-running queries
SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
FROM pg_stat_activity 
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';

-- Index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;
```

---

See `ARCHITECTURE.md` for integration with application layer.
