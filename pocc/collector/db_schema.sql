CREATE TABLE IF NOT EXISTS predictions (
    prediction_uuid TEXT PRIMARY KEY,
    station TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    probability REAL,
    confidence REAL,
    uncertainty REAL,
    magnitude REAL,
    azimuth REAL,
    explanation TEXT,
    model_version TEXT,
    model_name TEXT,
    backend TEXT,
    latency_ms REAL,
    artifact_uuid TEXT,
    pipeline_version TEXT,
    qc_version TEXT,
    qc_score REAL,
    input_hash TEXT,
    prediction_hash TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_predictions_station ON predictions(station);
CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON predictions(timestamp);

CREATE TABLE IF NOT EXISTS decisions (
    decision_uuid TEXT PRIMARY KEY,
    prediction_uuid TEXT REFERENCES predictions(prediction_uuid),
    level TEXT NOT NULL,
    probability REAL,
    confidence REAL,
    uncertainty REAL,
    qc_score REAL,
    triggered_rules JSONB,
    explanation TEXT,
    station TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_decisions_station ON decisions(station);
CREATE INDEX IF NOT EXISTS idx_decisions_level ON decisions(level);
CREATE INDEX IF NOT EXISTS idx_decisions_created ON decisions(created_at);

CREATE TABLE IF NOT EXISTS fused_events (
    event_id TEXT PRIMARY KEY,
    fused_probability REAL,
    fused_confidence REAL,
    n_stations INTEGER,
    stations TEXT[],
    centroid_lat REAL,
    centroid_lon REAL,
    max_distance_km REAL,
    time_window_start TIMESTAMPTZ,
    time_window_end TIMESTAMPTZ,
    input_predictions JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fused_events_created ON fused_events(created_at);

CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    state TEXT DEFAULT 'NEW',
    stations TEXT[],
    fused_probability REAL,
    peak_probability REAL DEFAULT 0,
    n_stations INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_state ON events(state);
CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at);
CREATE INDEX IF NOT EXISTS idx_events_updated ON events(updated_at);

CREATE TABLE IF NOT EXISTS warnings (
    warning_id TEXT PRIMARY KEY,
    event_id TEXT REFERENCES events(event_id),
    level TEXT NOT NULL,
    probability REAL,
    state TEXT DEFAULT 'NEW',
    stations TEXT[],
    reason TEXT,
    issued_at TIMESTAMPTZ DEFAULT NOW(),
    expired_at TIMESTAMPTZ,
    verified_at TIMESTAMPTZ,
    retracted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_warnings_level ON warnings(level);
CREATE INDEX IF NOT EXISTS idx_warnings_state ON warnings(state);
CREATE INDEX IF NOT EXISTS idx_warnings_issued ON warnings(issued_at);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id TEXT PRIMARY KEY,
    worker TEXT NOT NULL,
    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ,
    status TEXT DEFAULT 'RUNNING',
    processed_files INTEGER DEFAULT 0,
    failed_files INTEGER DEFAULT 0,
    latency_ms REAL,
    error TEXT,
    detail JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_worker ON pipeline_runs(worker);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_start ON pipeline_runs(start_time);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status ON pipeline_runs(status);

CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    component TEXT NOT NULL,
    action TEXT NOT NULL,
    detail JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_log_component ON audit_log(component);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log(created_at);
