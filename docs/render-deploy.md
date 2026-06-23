# Render deployment (HelmOS API)

Deploy the FastAPI backend as a **Web Service** on [Render](https://render.com). The frontend stays on Vercel/local; point `NEXT_PUBLIC_API_BASE_URL` at the Render URL in Plan 3.

## 1. Create service

1. **New → Web Service** → connect this repo.
2. **Runtime:** Python 3.12.
3. **Build command:** `pip install -r apps/backend/requirements.txt`
4. **Start command:** `cd apps/backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
5. **Health check path:** `/health`

Or use the repo root [`render.yaml`](../render.yaml) with **Blueprint** deploy.

## 2. Environment variables

Set in Render dashboard (never commit secrets):

| Variable | Required | Notes |
|----------|----------|--------|
| `DATABASE_URL` | Yes | Supabase **transaction pooler**, port 6543, `postgresql+asyncpg://...` |
| `SUPABASE_URL` | Yes | Project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | Storage uploads only (server-side) |
| `SUPABASE_ANON_KEY` | Optional | Reserved for future client auth |
| `OPENROUTER_API_KEY` | Yes | Chat, board agents, embeddings |
| `TAVILY_API_KEY` | For research | Tavily search |
| `FIRECRAWL_API_KEY` | For research | Page extraction |
| `HELMOS_API_KEY` | Yes | `Authorization: Bearer` on all routes except `/health` |
| `CORS_ORIGINS` | Yes | e.g. `http://localhost:3000,https://your-app.vercel.app` |
| `RENDER_EXTERNAL_URL` | Yes | `https://helmos-api.onrender.com` (your service URL) |
| `DAILY_SPEND_CAP_USD` | Recommended | Default `5.00` |
| `RESEARCH_MAX_PAGES_PER_SESSION` | Optional | Default `5` |

## 3. Post-deploy checks

1. `GET https://<service>/health` → `{"status":"ok"}`
2. `GET /workspaces` with `Authorization: Bearer <HELMOS_API_KEY>`
3. `GET /beliefs?workspace_id=clawback-labs` returns seeded beliefs
4. `POST /chat/stream` returns SSE tokens (timeout ≥ 120s for board)

## 4. Failure modes

| Symptom | Likely cause | Mitigation |
|---------|----------------|------------|
| 502 on first request | Cold start (starter/free) | Health ping cron; upgrade plan for demos |
| DB connection errors | Wrong pooler URL or session mode | Use transaction pooler port **6543** |
| SSE cuts off mid-stream | Proxy timeout | Increase Render HTTP timeout; keep responses chunked |
| 401 on all routes | Missing/wrong `HELMOS_API_KEY` | Match frontend `Authorization` header (Plan 3) |
| Research always fails | Spend cap or missing Tavily/Firecrawl keys | Check `DAILY_SPEND_CAP_USD` and API keys |
| Storage upload fails | Bucket missing or wrong key | Create `helmos-files` bucket; service role only |

## 5. Spend caps

- `DAILY_SPEND_CAP_USD` gates research and LLM-heavy paths via `spend_ledger`.
- When cap exceeded, research jobs return `failed` with `Daily spend cap exceeded`.
- Raise cap in Render env for production demos; monitor OpenRouter/Tavily dashboards.

## 6. Frontend wiring (Plan 3)

```env
NEXT_PUBLIC_USE_MSW=false
NEXT_PUBLIC_API_BASE_URL=https://helmos-api.onrender.com
```

Add `Authorization: Bearer ${HELMOS_API_KEY}` in the API client for protected routes.
