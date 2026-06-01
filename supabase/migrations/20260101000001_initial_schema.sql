-- HelmOS initial schema (Plan 2 — Supabase + Render)
-- Workspace IDs are TEXT slugs to match frontend fixtures (clawback-labs, nexops).

CREATE TABLE workspaces (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE projects (
    id           TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    name         TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'active',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE workspace_profiles (
    workspace_id   TEXT PRIMARY KEY REFERENCES workspaces(id) ON DELETE CASCADE,
    metrics        JSONB NOT NULL DEFAULT '[]',
    context_lines  JSONB NOT NULL DEFAULT '[]',
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE strategic_beliefs (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    content      TEXT NOT NULL,
    sort_order   INT NOT NULL DEFAULT 0,
    status       TEXT NOT NULL DEFAULT 'active',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX strategic_beliefs_workspace_idx
    ON strategic_beliefs (workspace_id, status, sort_order);

CREATE TABLE memory_chunks (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    project_id   TEXT REFERENCES projects(id) ON DELETE SET NULL,
    chunk_type   TEXT NOT NULL,
    content      TEXT NOT NULL,
    summary      TEXT,
    source_url   TEXT,
    source_file  TEXT,
    entity_name  TEXT,
    embedding    vector(1536),
    metadata     JSONB NOT NULL DEFAULT '{}',
    fetched_at   TIMESTAMPTZ,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX memory_chunks_workspace_idx
    ON memory_chunks (workspace_id, chunk_type, created_at DESC);

-- IVFFlat index: create after ~1000 rows or use HNSW on newer Supabase
-- CREATE INDEX memory_chunks_embedding_idx ON memory_chunks
--     USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE TABLE board_sessions (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id  TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    project_id    TEXT REFERENCES projects(id) ON DELETE SET NULL,
    question      TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'running',
    agent_outputs JSONB NOT NULL DEFAULT '[]',
    synthesis     JSONB,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE decisions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    project_id      TEXT REFERENCES projects(id) ON DELETE SET NULL,
    title           TEXT,
    question        TEXT NOT NULL,
    synthesis       TEXT NOT NULL DEFAULT '',
    verdict         TEXT,
    confidence      DOUBLE PRECISION,
    evidence_score  DOUBLE PRECISION,
    risk_level      TEXT,
    unknowns_level  TEXT,
    agent_outputs   JSONB NOT NULL DEFAULT '[]',
    risks           JSONB NOT NULL DEFAULT '[]',
    unknowns        JSONB NOT NULL DEFAULT '[]',
    assumptions     JSONB NOT NULL DEFAULT '[]',
    next_action     TEXT,
    status          TEXT NOT NULL DEFAULT 'open',
    timeline        JSONB NOT NULL DEFAULT '[]',
    resolved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX decisions_workspace_idx ON decisions (workspace_id, status, updated_at DESC);

CREATE TABLE inbox_items (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    decision_id  UUID REFERENCES decisions(id) ON DELETE SET NULL,
    item_type    TEXT NOT NULL,
    title        TEXT NOT NULL,
    body         TEXT,
    priority     TEXT NOT NULL DEFAULT 'medium',
    status       TEXT NOT NULL DEFAULT 'open',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX inbox_items_workspace_idx ON inbox_items (workspace_id, status, priority);

CREATE TABLE entities (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id        TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    name                TEXT NOT NULL,
    entity_type         TEXT NOT NULL DEFAULT 'company',
    last_researched_at  TIMESTAMPTZ,
    confidence          DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    linked_decision_ids JSONB NOT NULL DEFAULT '[]',
    summary             TEXT NOT NULL DEFAULT '',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX entities_workspace_idx ON entities (workspace_id, name);

CREATE TABLE files (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    project_id   TEXT REFERENCES projects(id) ON DELETE SET NULL,
    filename     TEXT NOT NULL,
    file_type    TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    chunk_count  INT NOT NULL DEFAULT 0,
    status       TEXT NOT NULL DEFAULT 'processing',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE research_cache (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url        TEXT NOT NULL UNIQUE,
    content    TEXT NOT NULL,
    summary    TEXT,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX research_cache_url_idx ON research_cache (url, fetched_at DESC);

CREATE TABLE research_jobs (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    entity_name  TEXT NOT NULL,
    queries      JSONB NOT NULL DEFAULT '[]',
    step         TEXT NOT NULL DEFAULT 'idle',
    sources      JSONB NOT NULL DEFAULT '[]',
    status       TEXT NOT NULL DEFAULT 'pending',
    error        TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE spend_ledger (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    day          DATE NOT NULL DEFAULT CURRENT_DATE,
    amount_usd   DOUBLE PRECISION NOT NULL DEFAULT 0,
    category     TEXT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX spend_ledger_day_category_idx ON spend_ledger (day, category);
