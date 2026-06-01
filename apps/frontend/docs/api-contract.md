# HelmOS API Contract (v0.1)

Base URL: `NEXT_PUBLIC_API_BASE_URL` (default `http://localhost:8000`)

Auth (Plan 3): `Authorization: Bearer <HELMOS_API_KEY>`

## REST

| Method | Path | Description |
|--------|------|-------------|
| GET | `/workspaces` | List workspaces |
| GET | `/workspaces/:id/projects` | List projects |
| GET | `/memory/chunks?workspace_id&type&search` | List memory chunks |
| POST | `/memory/chunks` | Create note chunk |
| POST | `/memory/ingest` | Upload file (multipart) |
| GET | `/decisions?workspace_id&status` | Decision log |
| GET | `/decisions/:id` | Single decision |
| PATCH | `/decisions/:id` | Update status |
| GET | `/inbox?workspace_id` | Open inbox items |
| PATCH | `/inbox/:id` | Resolve/dismiss |
| POST | `/board/sessions` | Start board session |
| GET | `/board/sessions/:id` | Get session |
| POST | `/research/run` | Start research job |
| GET | `/research/status/:jobId` | Poll job |

## Streaming

### POST `/chat/stream`

Request: `{ "message": string }`

SSE events:

```json
{ "type": "token", "content": "..." }
{ "type": "done", "confidence": 0.63, "tag": "plain", "evidence": [...] }
```

Types live in `lib/types/index.ts`.
