# HelmOS Backend (Plan 2)

FastAPI API backed by **Supabase PostgreSQL** (+ pgvector) and **Supabase Storage**. Deployed to **Render**.

## Setup

1. Complete [docs/supabase-setup.md](../../docs/supabase-setup.md) (migrations + seed + `helmos-files` bucket).
2. Copy root [`.env.example`](../../.env.example) to `apps/backend/.env` and fill secrets.
3. Install and run:

```bash
cd apps/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

4. Frontend (separate terminal):

```bash
cd apps/frontend
# NEXT_PUBLIC_USE_MSW=false
# NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
pnpm dev
```

## Auth

When `HELMOS_API_KEY` is set, send `Authorization: Bearer <key>` on all routes except `GET /health`. Leave empty locally to skip auth.

## Architecture

- **SQL / vectors:** `DATABASE_URL` + SQLAlchemy (never supabase-py for pgvector)
- **Storage:** `StorageService` via Supabase SDK + service role
- **Beliefs:** `strategic_beliefs` table + `BeliefService.pack_for_prompt()` — not in memory retrieval
- **Memory:** `MemoryService.search()` on `memory_chunks` only

See [docs/render-deploy.md](../../docs/render-deploy.md) for production deploy.
