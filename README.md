# HelmOS v2

Founder Intelligence Operating System — evidence before confidence.

## Architecture

```text
Next.js (frontend) → FastAPI on Render → Supabase (Postgres + pgvector + Storage) → OpenRouter / Tavily / Firecrawl
```

No Docker or local Postgres. Every developer uses a Supabase project. See [docs/supabase-setup.md](docs/supabase-setup.md).

## Frontend (Plan 1)

```bash
cd apps/frontend
pnpm install
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) — lands on **Dashboard**. MSW mocks the API by default (`NEXT_PUBLIC_USE_MSW=true`).

### Workspaces

- Clawback Labs — `/workspace/clawback-labs/dashboard`
- NexOps — `/workspace/nexops/dashboard`

## Backend (Plan 2)

```bash
cd apps/backend
pip install -r requirements.txt
cp ../../.env.example .env   # fill DATABASE_URL, Supabase keys, OPENROUTER_API_KEY
uvicorn main:app --reload --port 8000
```

Apply [supabase/migrations](supabase/migrations) and [supabase/seed.sql](supabase/seed.sql) first. Details: [apps/backend/README.md](apps/backend/README.md).

Deploy API: [docs/render-deploy.md](docs/render-deploy.md) · Env template: [.env.example](.env.example).

### Plan 3 wiring

```env
NEXT_PUBLIC_USE_MSW=false
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Add `Authorization: Bearer <HELMOS_API_KEY>` in the frontend client.

## Docs

- [UX handover](docs/ux-handover.md) — user flows, IA, pain points, and refactor guidance for UI/UX work
- [API contract](apps/frontend/docs/api-contract.md)
- [Supabase setup](docs/supabase-setup.md)
- [Render deploy](docs/render-deploy.md)

## Keyboard shortcuts

- `Cmd/Ctrl+D` — Dashboard
- `Cmd/Ctrl+B` — Board review
- `Cmd/Ctrl+R` — Research
- `Cmd/Ctrl+I` — Inbox / Attention
