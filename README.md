# HelmOS v2

Founder Intelligence Operating System — evidence before confidence.

## Frontend (Plan 1)

```bash
cd apps/frontend
pnpm install
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000). MSW mocks the API by default (`NEXT_PUBLIC_USE_MSW=true`).

### Workspaces

- Clawback Labs — `/workspace/clawback-labs/chat`
- NexOps — `/workspace/nexops/chat`

### Keyboard shortcuts

- `Cmd/Ctrl+K` — Chat
- `Cmd/Ctrl+B` — Board Room
- `Cmd/Ctrl+R` — Research

See [apps/frontend/docs/api-contract.md](apps/frontend/docs/api-contract.md) for API shapes (Plan 3 wiring).
