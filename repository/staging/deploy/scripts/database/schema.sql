-- ScalogramV3 V8 Production Database Schema
-- PostgreSQL Schema for PIMES (Precursor Ionospheric Monitoring Earthquake System)

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- ============================================================
-- TABLE: stations
-- Registry of 24 BMKG magnetometer stations
-- ============================================================
CREATE TABLE IF NOT EXISTS stations (
    station_id SERIAL PRIMARY KEY,
    station_code VARCHAR(10) UNIQUE NOT NULL,
    station_name VARCHAR(100) NOT NULL,
    latitude DECIMAL(10, 6) NOT NULL,
    longitude DECIMAL(10, 6) NOT NULL,
    elevation DECIMAL(8, 2),
    ftp_host VARCHAR(100),
    ftp_path VARCHAR(255),
    ftp_username VARCHAR(50),
    ftp_password VARCHAR(255),  -- ENCRYPTED in production
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_stations_code ON stations(station_code);
CREATE INDEX IF NOT EXISTS idx_stations_active ON stations(is_active);

-- ============================================================
-- TABLE: raw_files
-- Track collected raw data files from FTP
-- ============================================================
CREATE TABLE IF NOT EXISTS raw_files (
    file_id SERIAL PRIMARY KEY,
    station_id INTEGER REFERENCES stations(station_id) ON DELETE CASCADE,
    file_date DATE NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    file_size BIGINT,
    file_hash VARCHAR(64),
    download_status VARCHAR(20) DEFAULT 'pending',  -- pending, downloaded, failed
    download_timestamp TIMESTAMP,
    download_error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(station_id, file_date)
);

CREATE INDEX IF NOT EXISTS idx_raw_files_station_date ON raw_files(station_id, file_date);
CREATE INDEX IF NOT EXISTS idx_raw_files_status ON raw_files(download_status);
CREATE INDEX IF NOT EXISTS idx_raw_files_date ON raw_files(file_date);

-- ============================================================
-- TABLE: predictions
-- Store model predictions
-- ============================================================
CREATE TABLE IF NOT EXISTS predictions (
    prediction_id SERIAL PRIMARY KEY,
    station_id INTEGER REFERENCES stations(station_id) ON DELETE CASCADE,
    prediction_time TIMESTAMP NOT NULL,
    tensor_path VARCHAR(512),
    event_probability DECIMAL(5, 4) NOT NULL,
    magnitude DECIMAL(4, 2),
    azimuth DECIMAL(6, 2),
    kp_index DECIMAL(4, 2),
    dst_index DECIMAL(8, 2),
    model_version VARCHAR(50),
    inference_duration_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_predictions_station_time ON predictions(station_id, prediction_time);
CREATE INDEX IF NOT EXISTS idx_predictions_time ON predictions(prediction_time);
CREATE INDEX IF NOT EXISTS idx_predictions_probability ON predictions(event_probability);

-- ============================================================
-- TABLE: event_alerts
-- Track generated earthquake alerts
-- ============================================================
CREATE TABLE IF NOT EXISTS event_alerts (
    alert_id SERIAL PRIMARY KEY,
    prediction_id INTEGER REFERENCES predictions(prediction_id) ON DELETE CASCADE,
    station_id INTEGER REFERENCES stations(station_id) ON DELETE CASCADE,
    alert_time TIMESTAMP NOT NULL,
    alert_level VARCHAR(20) NOT NULL,  -- low, medium, high, critical
    event_probability DECIMAL(5, 4) NOT NULL,
    magnitude DECIMAL(4, 2),
    azimuth DECIMAL(6, 2),
    lead_time_hours DECIMAL(4, 2),
    alert_status VARCHAR(20) DEFAULT 'active',  -- active, acknowledged, resolved
    acknowledged_by VARCHAR(100),
    acknowledged_at TIMESTAMP,
    email_sent BOOLEAN DEFAULT FALSE,
    email_sent_at TIMESTAMP,
    sms_sent BOOLEAN DEFAULT FALSE,
    sms_sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_alerts_station_time ON event_alerts(station_id, alert_time);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON event_alerts(alert_status);
CREATE INDEX IF NOT EXISTS idx_alerts_level ON event_alerts(alert_level);

-- ============================================================
-- TABLE: system_logs
-- System operation logs for monitoring
-- ============================================================
CREATE TABLE IF NOT EXISTS system_logs (
    log_id SERIAL PRIMARY KEY,
    log_time TIMESTAMP NOT NULL,
    log_level VARCHAR(10) NOT NULL,  -- DEBUG, INFO, WARNING, ERROR, CRITICAL
    service_name VARCHAR(50) NOT NULL,  -- collector, preprocessing, inference, alert
    station_id INTEGER REFERENCES stations(station_id) ON DELETE SET NULL,
    message TEXT NOT NULL,
    error_details TEXT,
    execution_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_logs_time ON system_logs(log_time);
CREATE INDEX IF NOT EXISTS idx_logs_level ON system_logs(log_level);
CREATE INDEX IF NOT EXISTS idx_logs_service ON system_logs(service_name);
CREATE INDEX IF NOT EXISTS idx_logs_station ON system_logs(station_id);

-- ============================================================
-- TABLE: cosmic_indices
-- Store cosmic ray indices (Kp, Dst)
-- ============================================================
CREATE TABLE IF NOT EXISTS cosmic_indices (
    index_id SERIAL PRIMARY KEY,
    index_time TIMESTAMP NOT NULL,
    kp_index DECIMAL(4, 2) NOT NULL,
    dst_index DECIMAL(8, 2) NOT NULL,
    source VARCHAR(50) DEFAULT 'NOAA',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(index_time)
);

CREATE INDEX IF NOT EXISTS idx_cosmic_time ON cosmic_indices(index_time);

-- ============================================================
-- FUNCTION: update_updated_at_column
-- Automatically update updated_at timestamp
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- TRIGGERS: Auto-update updated_at
-- ============================================================
CREATE TRIGGER update_stations_updated_at BEFORE UPDATE ON stations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- VIEWS: For common queries
-- ============================================================

-- View: Active stations
CREATE OR REPLACE VIEW v_active_stations AS
SELECT station_id, station_code, station_name, latitude, longitude, elevation
FROM stations
WHERE is_active = TRUE;

-- View: Recent predictions
CREATE OR REPLACE VIEW v_recent_predictions AS
SELECT p.*, s.station_code, s.station_name
FROM predictions p
JOIN stations s ON p.station_id = s.station_id
ORDER BY p.prediction_time DESC
LIMIT 1000;

-- View: Active alerts
CREATE OR REPLACE VIEW v_active_alerts AS
SELECT a.*, s.station_code, s.station_name
FROM event_alerts a
JOIN stations s ON a.station_id = s.station_id
WHERE a.alert_status = 'active'
ORDER BY a.alert_time DESC;

-- View: System health (last 24 hours)
CREATE OR REPLACE VIEW v_system_health AS
SELECT 
    service_name,
    log_level,
    COUNT(*) as log_count,
    AVG(execution_time_ms) as avg_execution_time_ms,
    MAX(log_time) as last_log_time
FROM system_logs
WHERE log_time >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
GROUP BY service_name, log_level
ORDER BY service_name, log_level;

-- ============================================================
-- INITIAL DATA: Insert sample stations (if needed)
-- ============================================================
-- Uncomment and modify for initial deployment
/*
INSERT INTO stations (station_code, station_name, latitude, longitude, elevation, ftp_host, ftp_path) VALUES
('SCN', 'Sukabumi Cianjur', -6.95, 106.95, 500, 'ftp.bmkg.go.id', '/mdata/SCN'),
('BIT', 'Bitung', 1.43, 124.98, 200, 'ftp.bmkg.go.id', '/mdata/BIT'),
-- Add remaining 22 stations...
ON CONFLICT (station_code) DO NOTHING;
*/
