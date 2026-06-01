# HelmOS API Contract (v0.2)

Base URL: `NEXT_PUBLIC_API_BASE_URL` (default `http://localhost:8000`)

Auth: `Authorization: Bearer <HELMOS_API_KEY>` on all routes except `GET /health`. Leave `HELMOS_API_KEY` empty in local backend `.env` to skip auth during development.

Backend: FastAPI on Render · Data: Supabase PostgreSQL + Storage. See [docs/supabase-setup.md](../../../docs/supabase-setup.md) and [docs/render-deploy.md](../../../docs/render-deploy.md).

## REST

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness (no auth) |
| GET | `/dashboard` | Mission control payload |
| GET | `/founder-state` | Founder state bar metrics |
| GET | `/workspaces` | List workspaces |
| GET | `/workspaces/:id/projects` | List projects |
| GET | `/workspaces/:id/profile` | Workspace profile panel |
| GET | `/entities?workspace_id=` | Entity cards |
| GET | `/beliefs?workspace_id=` | Strategic beliefs (dedicated table) |
| POST | `/beliefs` | Create belief `{ workspace_id, content }` |
| PATCH | `/beliefs/:id` | Update content, sort_order, or status |
| DELETE | `/beliefs/:id` | Archive belief |
| GET | `/memory/chunks?workspace_id&type&search` | List memory chunks |
| POST | `/memory/chunks` | Create note chunk |
| POST | `/memory/ingest` | Upload file (multipart) |
| GET | `/decisions?workspace_id&status` | Decision log |
| GET | `/decisions/:id` | Single decision |
| PATCH | `/decisions/:id` | Update status |
| GET | `/inbox?workspace_id` | Open inbox items |
| PATCH | `/inbox/:id` | Resolve/dismiss |
| POST | `/board/sessions` | Run board session (persists decision + inbox) |
| GET | `/board/sessions/:id` | Get session |
| POST | `/research/run` | Start research job |
| GET | `/research/status/:jobId` | Poll job |

## Streaming

### POST `/chat/stream`

Request: `{ "message": string, "workspace_id"?: string }`

SSE events:

```json
{ "type": "token", "content": "..." }
{ "type": "done", "confidence": 0.63, "tag": "plain", "evidence": [...] }
```

Context order in prompts: strategic beliefs → retrieved memory chunks → user message.

Types live in `lib/types/index.ts`.
