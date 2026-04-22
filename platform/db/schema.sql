-- Postgres schema for the fraud detection platform.

CREATE TABLE IF NOT EXISTS predictions (
    job_id         UUID PRIMARY KEY,
    transaction_id BIGINT NOT NULL,
    created_at     TIMESTAMPTZ DEFAULT now(),
    fraud_proba    DOUBLE PRECISION NOT NULL,
    top_signals    JSONB NOT NULL,
    raw_payload    JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_predictions_txn ON predictions(transaction_id);
CREATE INDEX IF NOT EXISTS idx_predictions_created ON predictions(created_at DESC);

-- Mirrors the in-memory `graph_state` bundled in fraud_artifact.joblib, so
CREATE TABLE IF NOT EXISTS entity_stats (
    entity_type    TEXT NOT NULL,     -- 'card1' | 'P_emaildomain' | 'uid' | ...
    entity_value   TEXT NOT NULL,
    nbr_fraud_rate DOUBLE PRECISION,
    degree_map     JSONB,             -- {'card1': 3, 'P_emaildomain': 2, ...}
    amt_mean       DOUBLE PRECISION,
    amt_std        DOUBLE PRECISION,
    updated_at     TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (entity_type, entity_value)
);

-- Append-only log of transaction times per entity, used by the worker to
CREATE TABLE IF NOT EXISTS velocity_events (
    entity_type    TEXT NOT NULL,
    entity_value   TEXT NOT NULL,
    transaction_dt BIGINT NOT NULL,
    PRIMARY KEY (entity_type, entity_value, transaction_dt)
);
CREATE INDEX IF NOT EXISTS idx_velocity_lookup
    ON velocity_events(entity_type, entity_value, transaction_dt DESC);
