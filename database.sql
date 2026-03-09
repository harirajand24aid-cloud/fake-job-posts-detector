-- ============================================================
-- Fake Job Post Detector — database.sql
-- SQL schema for users and prediction results
-- ============================================================

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    username  TEXT    UNIQUE NOT NULL,
    password  TEXT    NOT NULL,
    role      TEXT    NOT NULL DEFAULT 'user',
    created_at TEXT   DEFAULT (datetime('now'))
);

-- Seed default credentials
INSERT OR IGNORE INTO users (username, password, role)
    VALUES ('admin', '1234', 'admin');

INSERT OR IGNORE INTO users (username, password, role)
    VALUES ('user', '123', 'user');


-- Prediction results table
CREATE TABLE IF NOT EXISTS predictions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    filename    TEXT    NOT NULL,
    prediction  TEXT    NOT NULL CHECK(prediction IN ('FAKE', 'REAL')),
    confidence  INTEGER NOT NULL CHECK(confidence BETWEEN 0 AND 100),
    details     TEXT,
    timestamp   TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Index for fast querying
CREATE INDEX IF NOT EXISTS idx_predictions_timestamp
    ON predictions(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_predictions_prediction
    ON predictions(prediction);


-- Example query: Get all FAKE results in last 7 days
-- SELECT * FROM predictions
-- WHERE prediction = 'FAKE'
--   AND timestamp >= datetime('now', '-7 days')
-- ORDER BY timestamp DESC;

-- Example query: Summary stats
-- SELECT
--     prediction,
--     COUNT(*) AS total,
--     ROUND(AVG(confidence), 1) AS avg_confidence
-- FROM predictions
-- GROUP BY prediction;
