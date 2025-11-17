-- Initialize TimescaleDB extension
-- This script is run automatically when the PostgreSQL container starts

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create hypertables after tables are created by Alembic
-- This would typically be done in a migration, but we include it here for reference

-- Note: These CREATE HYPERTABLE commands should be run AFTER the tables are created
-- Either through Alembic migrations or manually after table creation

-- Example commands (to be run after table creation):
-- SELECT create_hypertable('sim_usage', 'timestamp', if_not_exists => TRUE);
-- SELECT create_hypertable('sim_connectivity', 'timestamp', if_not_exists => TRUE);
-- SELECT create_hypertable('sim_events', 'timestamp', if_not_exists => TRUE);

-- Set compression policy for hypertables (optional, for better performance)
-- ALTER TABLE sim_usage SET (
--   timescaledb.compress,
--   timescaledb.compress_segmentby = 'iccid'
-- );

-- SELECT add_compression_policy('sim_usage', INTERVAL '7 days');
