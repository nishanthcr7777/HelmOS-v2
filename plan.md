# HelmOS v2 — Founder Intelligence Operating System
## Technical Architecture & Implementation Plan

> **Design philosophy:** Evidence before confidence. Fast execution with validation. The founder stays in the loop and makes every final call.

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Phased Implementation Roadmap](#2-phased-implementation-roadmap)
3. [MVP Boundaries](#3-mvp-boundaries)
4. [Token Economy Strategy](#4-token-economy-strategy)
5. [Memory Architecture](#5-memory-architecture)
6. [Agent Orchestration Flow](#6-agent-orchestration-flow)
7. [Research Pipeline Design](#7-research-pipeline-design)
8. [Database Schema](#8-database-schema)
9. [Frontend UX Structure](#9-frontend-ux-structure)
10. [Failure Modes & Mitigations](#10-failure-modes--mitigations)

---

## 1. System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FOUNDER INTERFACE                            │
│                     Next.js + Tailwind UI                           │
│   Chat  │  Board Room  │  Workspace  │  Inbox  │  Research Panel    │
└────────────────────────────┬────────────────────────────────────────┘
                             │ HTTPS / SSE streaming
┌────────────────────────────▼────────────────────────────────────────┐
│                        FASTAPI BACKEND                              │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │  Orchestrator│  │  Board       │  │  Research Layer          │  │
│  │  (router +   │  │  System      │  │  (Tavily / Exa /         │  │
│  │   planner)   │  │  (5 agents)  │  │   Firecrawl / PDF)       │  │
│  └──────┬───────┘  └──────┬───────┘  └────────────┬─────────────┘  │
│         │                 │                        │                │
│  ┌──────▼─────────────────▼────────────────────────▼─────────────┐ │
│  │                    MEMORY SERVICE                              │ │
│  │         Retrieval · Summarization · Context packing           │ │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                      PERSISTENCE LAYER                              │
│  PostgreSQL + pgvector  │  File store (S3-compatible or local)      │
└─────────────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                        MODEL LAYER                                  │
│  OpenRouter API  →  cheap router / summarizer + premium reasoner   │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Purpose | Technology |
|-----------|---------|------------|
| **Frontend** | Founder's primary interface; streaming responses | Next.js 14, Tailwind, Vercel AI SDK |
| **FastAPI backend** | Orchestration, routing, session management | Python 3.12, FastAPI, Celery (async tasks) |
| **Orchestrator** | Classifies intent, plans agent calls, assembles outputs | Small LLM (Claude Haiku / GPT-4o-mini via OpenRouter) |
| **Board System** | 5 specialized agents with adversarial framing | Medium/large LLM (Sonnet / GPT-4o) — selective use |
| **Research Layer** | Web search, page extraction, PDF parsing | Tavily (search), Firecrawl (extraction), PyMuPDF (PDF) |
| **Memory Service** | Retrieval, context compression, project summaries | pgvector + custom chunking |
| **PostgreSQL + pgvector** | Structured data + semantic vector search | Postgres 16, pgvector 0.7 |
| **OpenRouter** | Unified LLM API with model routing | OpenRouter (pay-per-token) |

### What This Architecture Deliberately Avoids

- No autonomous agent loops that act without founder approval
- No recursive self-calling agent chains
- No background agents modifying strategy without explicit trigger
- No separate microservices for MVP — monolith first, split only when bottleneck proven

---

## 2. Phased Implementation Roadmap

### Phase 1 — Foundation (Weeks 1–3)
**Goal:** Founder can ask questions about Clawback Labs / NexOps and get memory-grounded answers.

- [ ] Repo setup: monorepo with `apps/frontend`, `apps/backend`
- [ ] FastAPI skeleton with auth (API key or Clerk.dev for simplicity)
- [ ] PostgreSQL + pgvector setup via Docker Compose
- [ ] Basic memory schema: workspaces, projects, memory chunks
- [ ] Simple document ingestion: paste text or upload file → embed → store
- [ ] Single LLM call with memory retrieval (no board system yet)
- [ ] Minimal chat UI: message input, streaming output, project selector
- [ ] OpenRouter integration with model config

**Exit criteria:** Founder can paste a strategy doc, then ask a follow-up question two days later and get a grounded answer citing stored context.

---

### Phase 2 — Board System (Weeks 4–6)
**Goal:** Adversarial review is available on demand for any major decision.

- [ ] Board agent definitions: CTO, Operator, Skeptic, Researcher, Sales Strategist
- [ ] Structured evidence packet format (see Section 6)
- [ ] Orchestrator intent classifier: routes to single agent vs. full board vs. research
- [ ] Board workflow: parallel agent calls → synthesis → structured output
- [ ] Confidence scoring + assumption exposure in each agent response
- [ ] Frontend: Board Room view showing each agent's position
- [ ] Decision log: store board outputs with the triggering question

**Exit criteria:** Founder submits "Is X company a good Clawback target?" and receives 5 differentiated agent positions + synthesized recommendation with explicit risks and unknowns.

---

### Phase 3 — Research Pipeline (Weeks 7–9)
**Goal:** Agent responses are grounded in real web evidence, not hallucinated facts.

- [ ] Tavily integration for web search (cheap, JSON results)
- [ ] Firecrawl / Playwright fallback for full page extraction
- [ ] Company research workflow: name → search → extract → summarize → store in memory
- [ ] PDF ingestion: PyMuPDF → chunk → embed → store
- [ ] Evidence packet enrichment: every board response links to source snippets
- [ ] Research cache: avoid re-fetching the same URL within 7 days
- [ ] Frontend: Research Panel showing sources used in any response

**Exit criteria:** Board response includes cited URLs and extracted snippets. Founder can see exactly what information was used to form each opinion.

---

### Phase 4 — Founder Inbox + Polish (Weeks 10–12)
**Goal:** System surfaces what needs the founder's attention without being asked.

- [ ] Inbox schema: unresolved decisions, risky assumptions, blocked items, opportunities
- [ ] Inbox population: any board synthesis that ends with open questions auto-queues to Inbox
- [ ] Inbox UI: priority-sorted, one-click to "resolve" or "defer"
- [ ] Workspace summaries: on-demand project status summary from memory
- [ ] Search across all stored memory
- [ ] Basic export: decision log as markdown

**Exit criteria:** After a week of use, Inbox contains the 3–5 most important unresolved founder decisions, and founder can act on each without context switching.

---

## 3. MVP Boundaries

### In Scope (Phase 1–2 only as "MVP")

- Two workspaces: Clawback Labs, NexOps
- Text document ingestion (paste + upload)
- Memory retrieval for LLM context
- Five board agents with structured adversarial outputs
- Single founder user (no multi-tenant)
- Basic decision log
- API key authentication

### Explicitly Out of Scope for MVP

| Excluded Feature | Reason |
|------------------|--------|
| LinkedIn scraping | Legal/ToS risk, Firecrawl handles company sites instead |
| Screenshot ingestion | Vision models expensive; defer to Phase 4+ |
| Autonomous agents that act without input | Against core philosophy |
| Multi-user / team access | Adds auth complexity; solo founder first |
| Fine-tuned models | Cost/complexity; prompt engineering is sufficient at this scale |
| Real-time notifications / email digests | Nice-to-have; Inbox UI is sufficient |
| Mobile app | Web first |
| Workflow automation (Zapier-style) | Premature; creates maintenance debt |

### The "Good Enough" Bar for MVP

The MVP is complete when the founder can, in a single session:
1. Store context about a company
2. Ask the board a strategic question about it
3. Receive a structured response with explicit risks, unknowns, and a recommended next action
4. Have that exchange stored and retrievable later

Anything else is Phase 3+.

---

## 4. Token Economy Strategy

### Core Problem

A naive implementation sends full conversation history + all memory + all agent outputs to a large model on every call. That is 10–50x more expensive than necessary and slower.

### Model Tier Assignments

| Task | Model | Estimated Cost |
|------|-------|---------------|
| Intent classification / routing | `mistral/mistral-7b-instruct` or `openai/gpt-4o-mini` | ~$0.0001/call |
| Memory chunk summarization | `openai/gpt-4o-mini` | ~$0.0002/chunk |
| Research extraction + summarization | `openai/gpt-4o-mini` | ~$0.0005/page |
| Board agent responses (all 5) | `anthropic/claude-3-5-sonnet` or `openai/gpt-4o` | ~$0.01–0.03/board session |
| Final synthesis | `anthropic/claude-3-5-sonnet` | ~$0.005/call |

**Target cost per full board session (research + board + synthesis):** < $0.10

### Context Compression Rules

1. **Memory retrieval, not injection:** Never send the full memory store. Retrieve the top-K most relevant chunks (K=5–10) using pgvector cosine similarity before each call.
2. **Evidence packets, not raw pages:** Research output is summarized to 200–400 word structured packets before being passed to board agents.
3. **Rolling summaries for long projects:** Projects older than 30 messages get a rolling summary. New messages reference the summary, not the raw history.
4. **Agent outputs are structured JSON, not essays:** Each board agent returns a fixed schema (see Section 6). This caps output token length predictably.
5. **Synthesis step uses compressed agent outputs:** The synthesizer receives the 5 agent JSON outputs (not their full reasoning traces) to generate the final recommendation.

### Token Budget Example

A full board session on "Is company X a good Clawback target?":

```
Intent classification:    ~200 input tokens
Research summary:         ~600 input + ~400 output tokens  (cheap model)
Memory retrieval:         ~1,000 input tokens (5 chunks × 200 tokens)
Board agents (×5):        ~1,500 input + ~800 output each = ~11,500 total
Synthesis:                ~2,000 input + ~500 output tokens
─────────────────────────────────────────────────────────────────────
Total:                    ~15,700 tokens
At Sonnet pricing ($3/M in, $15/M out): ≈ $0.07–0.12 per session
```

This is realistic and affordable at founder usage patterns (5–20 sessions/day).

---

## 5. Memory Architecture

### Design Goals

- Retrieval-based: never inject full history, always retrieve relevant chunks
- Structured: project, entity type, and recency are first-class fields
- Cheap: embeddings are computed once on write, not on every read
- Summarized: long raw documents are chunked and summarized before storage

### Memory Hierarchy

```
Workspace (e.g., "Clawback Labs")
├── Projects (e.g., "Q3 Outreach Campaign")
│   ├── Memory Chunks (indexed by embedding)
│   │   ├── Type: strategy_note
│   │   ├── Type: research_summary
│   │   ├── Type: decision_log
│   │   └── Type: entity_profile (company, person)
│   └── Files (linked to chunks)
└── Global workspace memory (cross-project context)
```

### Chunking Strategy

- **Strategy notes / decisions:** Preserve as single chunks (usually 200–600 tokens). No splitting needed.
- **Uploaded documents:** Split at paragraph/section boundaries. Target 300–500 tokens per chunk. Overlap 50 tokens.
- **Research pages:** Summarize first (to 300 words via cheap model), then store the summary as a single chunk with source URL.
- **Board session outputs:** Store synthesis as one chunk + decision log entry.

### Retrieval

1. Embed the user's query using `text-embedding-3-small` (OpenAI, cheapest option, ~$0.00002/1K tokens)
2. Query pgvector with cosine similarity: `ORDER BY embedding <=> $query_embedding LIMIT 10`
3. Filter by workspace + optionally project
4. Re-rank by recency weight: `score = similarity * 0.7 + recency_weight * 0.3`
5. Return top 5–8 chunks as context for the LLM call

### Memory Freshness

- Entity profiles (companies, people) expire after 30 days — trigger re-research on access
- Strategy notes never expire (founder explicitly deletes them)
- Research summaries tagged with fetch date; stale flag after 7 days

---

## 6. Agent Orchestration Flow

### Board Agents

Each agent has a fixed identity, adversarial framing, and structured output schema.

| Agent | Core Question | Adversarial Bias |
|-------|--------------|-----------------|
| **CTO** | Is this technically feasible? What are the implementation risks? | Assumes technical complexity is always underestimated |
| **Operator** | Can we actually execute this given current resources? | Assumes capacity and timelines are always optimistic |
| **Skeptic** | What are the strongest reasons this fails? | Forced disagreement — finds flaws even in good ideas |
| **Researcher** | What does the actual evidence say? | Rejects claims not backed by source material |
| **Sales Strategist** | Is the ICP right? Is the outreach angle strong? | Assumes most pitches miss the buyer's real problem |

### Structured Agent Output Schema

```json
{
  "agent": "skeptic",
  "question_answered": "Is Acme Corp a good Clawback target?",
  "verdict": "lean_against",
  "confidence": 0.65,
  "evidence_used": [
    {"source": "tavily_search", "snippet": "Acme Corp raised Series B in 2022...", "url": "..."},
    {"source": "memory_chunk", "chunk_id": "uuid", "summary": "Previous note on Acme..."}
  ],
  "key_assumptions": [
    "Assumes Acme still has a compliance team (not verified)",
    "Assumes their Series B hasn't changed leadership"
  ],
  "risks": [
    "No public evidence of payroll clawback issues — may not be in-market",
    "Size may be too large for current Clawback Labs sales motion"
  ],
  "unknowns": [
    "Current headcount",
    "Recent layoffs or reorgs"
  ],
  "recommendation": "Do not prioritize without confirming they have an active compliance need. Run a 15-min LinkedIn search first.",
  "suggested_next_action": "Search LinkedIn for Acme Corp HR/Compliance job postings in last 90 days"
}
```

### Orchestration Flow

```
FOUNDER INPUT
     │
     ▼
┌─────────────────────────────┐
│  INTENT CLASSIFIER          │
│  (cheap model, ~200 tokens) │
│                             │
│  Outputs one of:            │
│  - simple_memory_query      │
│  - research_request         │
│  - board_decision           │
│  - workspace_update         │
└──────────────┬──────────────┘
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
  SIMPLE QUERY     BOARD DECISION
  (single LLM      (full workflow)
   + memory)
                        │
               ┌────────▼────────┐
               │  RESEARCH STEP  │
               │  (if needed)    │
               │  Tavily search  │
               │  + extraction   │
               │  + summarize    │
               └────────┬────────┘
                        │
               ┌────────▼────────┐
               │  MEMORY FETCH   │
               │  Top-K relevant │
               │  chunks         │
               └────────┬────────┘
                        │
               ┌────────▼────────┐
               │  BOARD AGENTS   │
               │  (parallel API  │
               │   calls, 5×)    │
               └────────┬────────┘
                        │
               ┌────────▼────────┐
               │  SYNTHESIS      │
               │  Compressed     │
               │  agent outputs  │
               │  → final rec.   │
               └────────┬────────┘
                        │
               ┌────────▼────────┐
               │  STORE TO       │
               │  MEMORY +       │
               │  DECISION LOG   │
               └────────┬────────┘
                        │
                        ▼
                 FOUNDER RESPONSE
              (streamed to frontend)
```

### Parallel vs. Sequential

- Board agent calls are **parallel** (use `asyncio.gather` or Celery tasks)
- Research step is **sequential before** board agents (agents need the evidence)
- Synthesis is **sequential after** board agents (needs all 5 outputs)

### Human-in-the-Loop Gates

- **Before research:** If research will cost more than $0.05 (multiple pages), prompt founder to confirm
- **Before acting on synthesis:** Synthesis always ends with a recommended next action. Founder explicitly confirms or dismisses.
- **Conflicting board opinions:** If >2 agents have opposing verdicts, flag to Inbox for explicit founder resolution. Do not auto-resolve.

---

## 7. Research Pipeline Design

### Research Trigger

Research is triggered when:
- Intent classifier returns `research_request`
- Intent classifier returns `board_decision` AND the entity being analyzed has no fresh memory chunks (< 7 days old)
- Founder explicitly asks to "research X"

### Pipeline Steps

```
1. QUERY CONSTRUCTION
   - Extract entity name + research intent from founder question
   - Generate 2–3 search queries (cheap model)
   - Example: "Acme Corp" + "Clawback target" →
     ["Acme Corp company overview", "Acme Corp payroll compliance news", "Acme Corp recent funding headcount"]

2. WEB SEARCH
   - Tavily API: structured JSON results, low cost (~$0.001/search)
   - Returns: title, URL, snippet, published date
   - Fetch top 5 results per query → 10–15 total candidates

3. RELEVANCE FILTER
   - Cheap model scores each result: relevant / maybe / skip
   - Keep top 5–8 results for extraction

4. PAGE EXTRACTION (selective)
   - Firecrawl for clean markdown extraction
   - Only extract pages marked "relevant"
   - Skip PDFs at this stage (separate ingest flow)
   - Rate limit: max 5 pages per research session to control cost

5. CONTENT SUMMARIZATION
   - Each extracted page → 200–400 word structured summary (cheap model)
   - Schema: {company, key_facts, relevance_to_query, source_url, fetched_at}

6. EVIDENCE PACKET ASSEMBLY
   - Combine all summaries into one evidence packet
   - Include original snippets from Tavily results for attribution
   - Total evidence packet: ~1,500–2,000 tokens

7. CACHE TO MEMORY
   - Store evidence packet as memory chunks tagged by entity + workspace
   - Mark with fetched_at timestamp
   - Future calls within 7 days skip the research step and use cached chunks

8. HAND-OFF TO BOARD AGENTS
   - Evidence packet included in each board agent's system prompt
```

### PDF / Document Ingestion

Separate from the live research pipeline:

```
FOUNDER UPLOADS FILE
     │
     ▼
PyMuPDF → extract text
     │
     ▼
Chunk at 400 tokens (overlap 50)
     │
     ▼
Summarize each chunk (cheap model, optional for large docs)
     │
     ▼
Embed (text-embedding-3-small)
     │
     ▼
Store in PostgreSQL + pgvector with metadata
(workspace_id, project_id, source_file, chunk_index, created_at)
```

### Research Cost Controls

| Control | Implementation |
|---------|---------------|
| Search result cap | Max 15 Tavily results per session |
| Page extraction cap | Max 5 pages per research session |
| Cache hit | Skip research if entity has fresh chunks (< 7 days) |
| Cost estimate before execution | Show founder estimated cost for large research jobs |
| Chunk deduplication | Hash content; skip re-embedding identical chunks |

---

## 8. Database Schema

### Core Tables

```sql
-- Workspaces: top-level context containers
CREATE TABLE workspaces (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,           -- "Clawback Labs", "NexOps"
    description TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Projects within a workspace
CREATE TABLE projects (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    name         TEXT NOT NULL,
    status       TEXT DEFAULT 'active',  -- active | archived
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- Memory chunks: the core retrieval unit
CREATE TABLE memory_chunks (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    project_id   UUID REFERENCES projects(id) ON DELETE SET NULL,
    chunk_type   TEXT NOT NULL,          -- strategy_note | research_summary | decision_log | entity_profile | document_chunk
    content      TEXT NOT NULL,          -- the actual text content
    summary      TEXT,                   -- optional pre-computed summary
    source_url   TEXT,                   -- for research chunks
    source_file  TEXT,                   -- for document chunks
    entity_name  TEXT,                   -- for entity profiles (company name, person name)
    embedding    vector(1536),           -- text-embedding-3-small output
    metadata     JSONB DEFAULT '{}',
    fetched_at   TIMESTAMPTZ,            -- for research chunks (freshness check)
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    updated_at   TIMESTAMPTZ DEFAULT NOW()
);

-- Vector index for fast similarity search
CREATE INDEX ON memory_chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Index for filtered retrieval by workspace
CREATE INDEX ON memory_chunks (workspace_id, chunk_type, created_at DESC);

-- Decision log: permanent record of board sessions
CREATE TABLE decisions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    project_id      UUID REFERENCES projects(id) ON DELETE SET NULL,
    question        TEXT NOT NULL,       -- the founder's original question
    synthesis       TEXT NOT NULL,       -- final synthesized recommendation
    verdict         TEXT,                -- go | no_go | conditional | needs_research
    confidence      FLOAT,              -- 0.0–1.0
    agent_outputs   JSONB NOT NULL,      -- array of all 5 agent response objects
    risks           JSONB DEFAULT '[]',
    unknowns        JSONB DEFAULT '[]',
    assumptions     JSONB DEFAULT '[]',
    next_action     TEXT,
    status          TEXT DEFAULT 'open', -- open | resolved | deferred
    resolved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Inbox items: surfaces unresolved or high-priority items
CREATE TABLE inbox_items (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    decision_id  UUID REFERENCES decisions(id) ON DELETE CASCADE,
    item_type    TEXT NOT NULL,  -- unresolved_decision | risky_assumption | blocked_action | opportunity | conflict
    title        TEXT NOT NULL,
    body         TEXT,
    priority     TEXT DEFAULT 'medium',  -- high | medium | low
    status       TEXT DEFAULT 'open',    -- open | resolved | dismissed
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- Files: uploaded documents linked to memory chunks
CREATE TABLE files (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    project_id   UUID REFERENCES projects(id) ON DELETE SET NULL,
    filename     TEXT NOT NULL,
    file_type    TEXT NOT NULL,   -- pdf | txt | md | docx
    storage_path TEXT NOT NULL,   -- path in file store
    chunk_count  INT DEFAULT 0,
    status       TEXT DEFAULT 'processing',  -- processing | indexed | error
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- Research cache: deduplicate URL fetches
CREATE TABLE research_cache (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url         TEXT NOT NULL UNIQUE,
    content     TEXT NOT NULL,
    summary     TEXT,
    fetched_at  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX ON research_cache (url, fetched_at DESC);
```

### Design Notes

- **pgvector** is the right call here: it eliminates the operational overhead of a separate Qdrant instance, and at the data volumes a solo founder generates (tens of thousands of chunks at most), Postgres with an IVFFlat index is fast enough.
- **JSONB for agent outputs:** avoids schema churn as the agent response format evolves in early development.
- **No user table for MVP:** single-founder use with API key auth. Add Clerk.dev auth when multi-user is needed.
- **Alembic for migrations:** schema will evolve; use Alembic from day one rather than raw `CREATE TABLE` statements.

---

## 9. Frontend UX Structure

### Navigation Structure

```
┌───────────────────────────────────────────────────────────┐
│  HELMOS                     [Clawback Labs ▼]    [Inbox 3] │
├────────────┬──────────────────────────────────────────────┤
│            │                                              │
│  SIDEBAR   │              MAIN PANEL                      │
│            │                                              │
│  Chat      │  (context-dependent content)                 │
│  Board     │                                              │
│  Memory    │                                              │
│  Research  │                                              │
│  Inbox     │                                              │
│  Decisions │                                              │
│            │                                              │
└────────────┴──────────────────────────────────────────────┘
```

### Views

#### Chat View (default)
- Streaming chat interface, markdown rendered
- Messages tagged with: plain response / board session / research
- Each response shows confidence level and a "View Evidence" expandable
- "Invoke Board" button converts any question to a full board session

#### Board Room View
- Triggered by board sessions
- Five cards: one per agent, showing verdict badge + key points
- Synthesis panel below with final recommendation, risks, unknowns
- Founder action bar: "Accept", "Defer", "Push Back" (sends dissent to re-run)
- Collapsed by default for simple queries; expanded automatically for board sessions

#### Memory / Workspace View
- List of all memory chunks for current workspace
- Filter by type (strategy_note, research, entity, document)
- Full-text search
- Manual "Add Note" for founder to directly store context
- Entity cards: grouped view of all chunks about a single company/person

#### Research Panel
- Triggered when research is running (shows progress: searching → extracting → summarizing)
- After completion: shows sources used, with URL and snippet
- Option to re-run research on an entity with updated queries

#### Inbox View
- Priority-sorted list of open items
- Item types use distinct visual treatment: decision (blue), assumption risk (yellow), blocked (red), opportunity (green), conflict (orange)
- One-click "Resolve" or "Defer to [date]"
- Clicking any item opens the source decision in the Board Room view

#### Decision Log View
- Chronological list of all board sessions
- Filter by workspace, verdict, status
- Each entry: question → synthesis → verdict badge → status
- Exportable as markdown

### UX Principles

1. **Streaming first:** Every LLM response streams token-by-token. Founder sees progress, not a spinner.
2. **Evidence is always accessible, never forced:** Confidence levels and source links are visible but collapsed by default.
3. **One primary action per screen:** Board Room has one CTA. Inbox item has two (resolve/defer). No decision paralysis from UI.
4. **Keyboard-first:** `Cmd+K` to focus chat, `Cmd+B` to invoke board, `Cmd+R` to trigger research.
5. **Workspace switcher is always visible:** Never lose context about which project you're working in.
6. **No dark patterns:** No "are you sure?" modals for non-destructive actions. Memory is versioned, not deleted.

### Tech Stack

- **Next.js 14 (App Router):** Server components for initial data, client components for streaming
- **Tailwind CSS + shadcn/ui:** Consistent, fast-to-build component library
- **Vercel AI SDK:** Handles streaming chat with minimal boilerplate
- **TanStack Query:** Client-side data fetching and caching
- **Zustand:** Lightweight global state (current workspace, active session)

---

## 10. Failure Modes & Mitigations

### LLM Output Failures

| Failure Mode | Likelihood | Mitigation |
|-------------|-----------|-----------|
| Agent produces generic/agreeable output instead of adversarial | High (common in vanilla prompts) | System prompt explicitly mandates disagreement format; output is validated against schema — missing "risks" or "assumptions" fields trigger a retry with stronger instructions |
| Agent fabricates company facts | High without research | Researcher agent only cites evidence from the evidence packet; synthesis step explicitly flags any claim without a source |
| Confidence scores are arbitrary | Medium | Confidence is calibrated to evidence volume: 0 sources = max 0.4 confidence; 3+ sources = up to 0.9. Enforced in post-processing. |
| Synthesis contradicts all 5 agents | Low | Synthesis prompt is given all 5 structured outputs; if final verdict contradicts majority, it must include a rationale field |

### Memory Failures

| Failure Mode | Likelihood | Mitigation |
|-------------|-----------|-----------|
| Wrong chunks retrieved (low recall) | Medium | Use hybrid search: pgvector cosine similarity + BM25 keyword match; combine scores with RRF (Reciprocal Rank Fusion) |
| Stale research used for current decision | Medium | Freshness check: if most relevant chunks are > 7 days old for an entity, offer founder a "refresh research" prompt before board session |
| Memory grows too large to be useful | Low (solo founder volume) | Rolling summaries at 30+ message project histories; project-level summarization available on demand |
| Embedding model changed, old vectors incompatible | Low | Store embedding model version with each chunk; re-embed on model change (batch job) |

### Research Pipeline Failures

| Failure Mode | Likelihood | Mitigation |
|-------------|-----------|-----------|
| Tavily returns irrelevant results | Medium | Relevance filter step (cheap model) before extraction; founder can provide additional search context |
| Firecrawl fails / rate limited | Medium | Fallback to BeautifulSoup simple extraction; cache successful extractions aggressively |
| Research cost spikes unexpectedly | Low | Hard cap: max 5 page extractions per session; show estimated cost to founder before large research jobs |
| Company has no public web presence | Medium | Researcher agent explicitly flags "insufficient public evidence" instead of hallucinating; moves to "unknowns" in synthesis |

### Orchestration Failures

| Failure Mode | Likelihood | Mitigation |
|-------------|-----------|-----------|
| Intent classifier misroutes (e.g., routes strategic question to simple query) | Medium | Classifier outputs confidence; below 0.7 defaults to board session (safer to over-route than under-route) |
| One board agent API call times out | Low | `asyncio.gather` with per-call timeout (30s); missing agent is flagged in synthesis rather than blocking the whole session |
| OpenRouter rate limit or outage | Low | Retry with exponential backoff (3 attempts); surface error clearly to founder rather than silent failure |
| Infinite clarification loops | Low | Orchestrator is allowed exactly one clarification question per session; after that, it proceeds with stated assumptions |

### Operational / Cost Failures

| Failure Mode | Likelihood | Mitigation |
|-------------|-----------|-----------|
| API cost runaway (many board sessions) | Low for solo founder | Daily spend cap configurable in env vars; alert when 80% consumed; hard stop at 100% |
| PostgreSQL disk growth from embeddings | Low initially | Each 1536-dim float32 vector = 6KB; 10,000 chunks = 60MB; fine for years at solo founder usage |
| Session context corrupted mid-stream | Low | Sessions are idempotent on retry; each board session writes to DB on completion, not during |

### Philosophical / Design Failures

| Failure Mode | Likelihood | Mitigation |
|-------------|-----------|-----------|
| System becomes an echo chamber (founder only asks confirming questions) | Medium | Skeptic agent has mandatory veto rights in synthesis — synthesis cannot reach "strong go" verdict if Skeptic raises a critical unfalsifiable assumption |
| Founder over-trusts system confidence scores | Medium | Confidence label system: 0.0–0.4 = "Low — treat as hypothesis", 0.4–0.7 = "Moderate — verify before committing", 0.7–0.9 = "High — evidence-grounded", 0.9+ is never displayed (no LLM output deserves that label) |
| Decision log becomes noise | Medium | Only full board sessions write to decision log; simple queries do not. Inbox only surfaces items that require action, not all history. |

---

## Appendix A: Directory Structure

```
helmos/
├── apps/
│   ├── frontend/                    # Next.js 14
│   │   ├── app/
│   │   │   ├── (auth)/
│   │   │   ├── workspace/[id]/
│   │   │   │   ├── chat/
│   │   │   │   ├── board/
│   │   │   │   ├── memory/
│   │   │   │   ├── research/
│   │   │   │   ├── inbox/
│   │   │   │   └── decisions/
│   │   │   └── api/                 # Next.js API routes (thin proxies only)
│   │   ├── components/
│   │   │   ├── board/
│   │   │   ├── chat/
│   │   │   ├── memory/
│   │   │   └── ui/                  # shadcn components
│   │   └── lib/
│   └── backend/                     # FastAPI
│       ├── api/
│       │   ├── routes/
│       │   │   ├── chat.py
│       │   │   ├── board.py
│       │   │   ├── memory.py
│       │   │   ├── research.py
│       │   │   └── inbox.py
│       │   └── deps.py
│       ├── agents/
│       │   ├── orchestrator.py
│       │   ├── board/
│       │   │   ├── base.py
│       │   │   ├── cto.py
│       │   │   ├── operator.py
│       │   │   ├── skeptic.py
│       │   │   ├── researcher.py
│       │   │   └── sales_strategist.py
│       │   └── synthesizer.py
│       ├── memory/
│       │   ├── retrieval.py
│       │   ├── ingestion.py
│       │   └── summarization.py
│       ├── research/
│       │   ├── search.py            # Tavily integration
│       │   ├── extraction.py        # Firecrawl / fallback
│       │   ├── pdf_ingest.py        # PyMuPDF
│       │   └── pipeline.py          # Full research orchestration
│       ├── db/
│       │   ├── models.py            # SQLAlchemy models
│       │   ├── migrations/          # Alembic
│       │   └── session.py
│       ├── llm/
│       │   ├── client.py            # OpenRouter wrapper
│       │   └── models.py            # Model tier config
│       └── main.py
├── docker-compose.yml               # Postgres + pgvector + backend + frontend
├── .env.example
└── plan.md                          # This document
```

## Appendix B: Environment Variables

```bash
# LLM
OPENROUTER_API_KEY=

# Research
TAVILY_API_KEY=
FIRECRAWL_API_KEY=           # Optional; fallback extraction works without it

# Database
DATABASE_URL=postgresql://helmos:password@localhost:5432/helmos

# File Storage
STORAGE_PATH=./data/files    # Local for MVP; swap for S3_BUCKET later

# Cost Controls
DAILY_SPEND_CAP_USD=5.00
RESEARCH_MAX_PAGES_PER_SESSION=5

# Auth
HELMOS_API_KEY=              # Simple API key for MVP; replace with Clerk for multi-user
```

## Appendix C: OpenRouter Model Config

```python
# llm/models.py
MODEL_TIERS = {
    "router":       "openai/gpt-4o-mini",
    "summarizer":   "openai/gpt-4o-mini",
    "board_agent":  "anthropic/claude-3-5-sonnet",
    "synthesizer":  "anthropic/claude-3-5-sonnet",
    "embedder":     "openai/text-embedding-3-small",  # via OpenAI directly
}

# Override per-call if needed:
# board_agent = "openai/gpt-4o" for complex technical decisions
# board_agent = "openai/gpt-4o-mini" for simple factual routing
```

---

*Plan version: 0.1 — subject to revision after founder review. Implementation should not begin until Phase 1 scope is confirmed.*
