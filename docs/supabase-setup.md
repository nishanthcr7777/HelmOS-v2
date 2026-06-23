# Supabase setup (HelmOS Plan 2)

HelmOS uses Supabase for PostgreSQL (+ pgvector), object storage, and optional future Auth. There is **no local Postgres** — every developer needs a Supabase project (prod + optional dev).

## 1. Create project

1. Go to [supabase.com](https://supabase.com) → New project.
2. Note **Project URL**, **anon key**, **service role key**, and database password.

## 2. Enable pgvector

In **SQL Editor**, run:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Or apply repo migrations (step 3).

## 3. Apply schema and seed

**Option A — Supabase CLI**

```bash
supabase link --project-ref YOUR_REF
supabase db push
psql "$DATABASE_URL" -f supabase/seed.sql
```

**Option B — SQL Editor**

1. Run `supabase/migrations/20260101000000_enable_pgvector.sql`
2. Run `supabase/migrations/20260101000001_initial_schema.sql`
3. Run `supabase/seed.sql`

## 4. Storage bucket

1. **Storage** → New bucket → name: `helmos-files` → **Private**.
2. Backend uses **service role** only; browsers receive **signed URLs** from the API.

Recommended policy: no public access; all uploads via FastAPI with `SUPABASE_SERVICE_ROLE_KEY`.

## 5. Connection strings

| Use | Env | Notes |
|-----|-----|-------|
| SQLAlchemy / pgvector | `DATABASE_URL` | **Transaction pooler**, port **6543**, `postgresql+asyncpg://...` |
| Storage SDK | `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` | Do not use SDK for vector search |

Example pooler URL (Dashboard → Settings → Database → Connection string → Transaction pooler):

```text
postgresql+asyncpg://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
```

## 6. Vector index (later)

IVFFlat needs rows before tuning. After ~1000 `memory_chunks` with embeddings:

```sql
CREATE INDEX memory_chunks_embedding_idx ON memory_chunks
  USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

Or use HNSW if your Supabase Postgres version supports it.

## 7. Verify

```sql
SELECT id, name FROM workspaces;
SELECT content FROM strategic_beliefs WHERE workspace_id = 'clawback-labs' ORDER BY sort_order;
```

You should see `clawback-labs`, `nexops`, and seeded beliefs.
