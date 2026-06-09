-- Belief metadata: heuristics with confidence, rationale, and override conditions

ALTER TABLE strategic_beliefs
    ADD COLUMN IF NOT EXISTS confidence FLOAT NOT NULL DEFAULT 0.8,
    ADD COLUMN IF NOT EXISTS rationale TEXT,
    ADD COLUMN IF NOT EXISTS override_conditions JSONB NOT NULL DEFAULT '[]';
