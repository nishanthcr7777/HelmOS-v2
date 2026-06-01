# HelmOS v2

Founder Intelligence Operating System — evidence before confidence.

## Frontend (Plan 1)

```bash
cd apps/frontend
pnpm install
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) — lands on **Dashboard** (mission control). MSW mocks the API by default (`NEXT_PUBLIC_USE_MSW=true`).

### Workspaces

- Clawback Labs — `/workspace/clawback-labs/dashboard`
- NexOps — `/workspace/nexops/dashboard`

### Keyboard shortcuts

- `Cmd/Ctrl+D` — Dashboard
- `Cmd/Ctrl+B` — Board review
- `Cmd/Ctrl+R` — Research
- `Cmd/Ctrl+I` — Inbox / Attention

See [apps/frontend/docs/api-contract.md](apps/frontend/docs/api-contract.md) for API shapes (Plan 3 wiring).
