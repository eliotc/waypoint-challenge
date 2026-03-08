-- Waypoint database schema
-- Run once against Neon (pgvector already enabled via CREATE EXTENSION)

CREATE EXTENSION IF NOT EXISTS vector;

-- ── Courses ───────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS courses (
    id              SERIAL PRIMARY KEY,
    code            TEXT NOT NULL UNIQUE,          -- e.g. CS101
    name            TEXT NOT NULL,
    faculty         TEXT NOT NULL,                 -- Engineering, Arts, Business, etc.
    level           TEXT NOT NULL,                 -- Undergraduate, Postgraduate
    study_mode      TEXT NOT NULL,                 -- Full-time, Part-time, Online
    duration_years  NUMERIC(3,1) NOT NULL,
    atar_cutoff     INTEGER,                       -- NULL = no ATAR required
    annual_fee_aud  INTEGER NOT NULL,
    description     TEXT NOT NULL,
    career_outcomes TEXT NOT NULL,
    embedding       vector(1536)                    -- text-embedding-004 dimension
);

-- ── Events ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS events (
    id          SERIAL PRIMARY KEY,
    title       TEXT NOT NULL,
    event_type  TEXT NOT NULL,    -- OpenDay, Webinar, CampusTour, InfoSession
    start_at    TIMESTAMPTZ NOT NULL,
    end_at      TIMESTAMPTZ NOT NULL,
    location    TEXT NOT NULL,    -- Building/room or "Online"
    description TEXT NOT NULL,
    max_capacity INTEGER,
    spots_left   INTEGER
);

-- ── Tour bookings ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tour_bookings (
    id              SERIAL PRIMARY KEY,
    student_name    TEXT NOT NULL,
    email           TEXT NOT NULL,
    preferred_date  DATE NOT NULL,
    party_size      INTEGER NOT NULL DEFAULT 1,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Knowledge docs (for RAG / fallback Q&A) ──────────────────────────────────
CREATE TABLE IF NOT EXISTS knowledge_docs (
    id        SERIAL PRIMARY KEY,
    topic     TEXT NOT NULL,    -- admissions, fees, campus-life, etc.
    title     TEXT NOT NULL,
    content   TEXT NOT NULL,
    embedding vector(1536)
);

-- Indexes for fast vector search
CREATE INDEX IF NOT EXISTS courses_embedding_idx
    ON courses USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS knowledge_docs_embedding_idx
    ON knowledge_docs USING hnsw (embedding vector_cosine_ops);

-- Index for event type + date range queries
CREATE INDEX IF NOT EXISTS events_type_start_idx
    ON events (event_type, start_at);
