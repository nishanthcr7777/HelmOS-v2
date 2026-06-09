# HelmOS Board Implementation Audit

**Audit date:** 2026-06-01  
**Scope:** `apps/backend` board orchestration, agents, LLM layer, memory/beliefs injection, decision-mode enforcement, frontend display  
**Method:** Static code review + live DB trace against `clawback-labs` workspace (Supabase)

---

## 1. Agent Models

### Where agents are created

Board agents are **not** separate classes or files. All five agents are invoked from a single factory function `run_agent()` in `apps/backend/agents/base.py`, called in parallel by `run_board_session()` in `apps/backend/orchestrator/board.py`.

```54:57:apps/backend/orchestrator/board.py
    tasks = [
        run_agent(name, question, context, beliefs_block, board_mode=board_mode)
        for name in AGENT_NAMES
    ]
```

```7:7:apps/backend/agents/base.py
AGENT_NAMES = ["cto", "operator", "skeptic", "researcher", "sales_strategist"]
```

LLM calls go through `complete_json()` in `apps/backend/llm/openrouter.py`. **No agent passes a `model` argument** — all use the global default.

### Global model configuration

**File:** `apps/backend/config.py`

```28:31:apps/backend/config.py
    daily_spend_cap_usd: float = 5.0
    research_max_pages_per_session: int = 5
    embedding_model: str = "openai/text-embedding-3-small"
    chat_model: str = "openai/gpt-4o-mini"
```

**File:** `apps/backend/llm/openrouter.py`

```60:73:apps/backend/llm/openrouter.py
async def complete_json(system: str, user: str, model: str | None = None) -> str:
    client = _client()
    if client is None:
        return "{}"
    settings = get_settings()
    resp = await client.chat.completions.create(
        model=model or settings.chat_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
    )
    return resp.choices[0].message.content or "{}"
```

**Provider:** OpenRouter (`base_url="https://openrouter.ai/api/v1"`) — see `apps/backend/llm/openrouter.py` lines 13–16.

**Embedding model (memory retrieval only, not board agent calls):** `openai/text-embedding-3-small` via `embed_text()` in the same file.

### Parameters NOT set anywhere in board path

| Parameter | Value in board code |
|-----------|---------------------|
| `temperature` | **Not passed** — OpenRouter / model default applies |
| `max_tokens` | **Not passed** — API default applies |
| `top_p` | **Not passed** |
| `reasoning` / `reasoning_effort` | **Not passed** — no reasoning-model settings |
| Per-agent `model` override | **None** — all agents use `settings.chat_model` |
| Per-agent `temperature` override | **None** |

The only non-default API parameter for board agents is `response_format={"type": "json_object"}`.

### Agent model table

| Agent | Model | Temperature | File path |
|-------|-------|-------------|-----------|
| CTO | `openai/gpt-4o-mini` (via `settings.chat_model`) | Not set (API default) | `apps/backend/agents/base.py` → `apps/backend/llm/openrouter.py` |
| Operator | `openai/gpt-4o-mini` | Not set (API default) | same |
| Skeptic | `openai/gpt-4o-mini` | Not set (API default) | same |
| Researcher | `openai/gpt-4o-mini` | Not set (API default) | same |
| Sales Strategist | `openai/gpt-4o-mini` | Not set (API default) | same |
| Synthesizer | `openai/gpt-4o-mini` | Not set (API default) | `apps/backend/agents/synthesizer.py` → `apps/backend/llm/openrouter.py` |

### Per-agent overrides that DO exist (non-model)

**File:** `apps/backend/agents/base.py`

```17:23:apps/backend/agents/base.py
DEFAULT_WEIGHTS = {
    "cto": 0.05,
    "operator": 0.2,
    "skeptic": 0.25,
    "researcher": 0.4,
    "sales_strategist": 0.1,
}
```

These weights are **prompt instructions only** (`influence_weight should be {DEFAULT_WEIGHTS[agent_key]}`). Post-LLM normalization also coerces `influence_weight` via `_as_float()`.

### Offline / missing-key behavior

If `OPENROUTER_API_KEY` is empty, `complete_json()` returns `"{}"`, and `run_agent()` fills defaults — agents never call a real model.

---

## 2. Agent Prompts

### Prompt construction

**File:** `apps/backend/agents/base.py`  
**Function:** `run_agent(agent_key, question, context, beliefs_block, board_mode="decision")`

System prompt is an f-string template. The **only per-agent differences** in the system prompt are:

1. `label` from `AGENT_LABELS[agent_key]` (e.g. `"CTO"`)
2. `influence_weight` numeric default from `DEFAULT_WEIGHTS[agent_key]`
3. `agent must be "{agent_key}"` string

There are **no role-specific instruction blocks** for CTO vs Skeptic vs Researcher beyond the label name.

Mode-specific blocks come from `_decision_mode_prompt()` or `_exploration_mode_prompt()`. Beliefs are appended verbatim from `beliefs_block`.

User prompt (all agents, identical structure):

```101:101:apps/backend/agents/base.py
    user = f"Question: {question}\n\nContext:\n{context[:12000]}"
```

---

### Decision mode — full system prompts (default `board_mode`)

Below is the **exact** rendered system prompt for each agent in **Decision** mode, with beliefs as loaded live from workspace `clawback-labs` on 2026-06-01.

---

#### Agent: CTO

**File path:** `apps/backend/agents/base.py` (`run_agent`, `agent_key="cto"`)

**Prompt:**

```
You are the CTO on a founder intelligence board.
Respond in JSON only with keys:
agent, question_answered, verdict, confidence, influence_weight, evidence_quality,
research_age_days, evidence_score, evidence_used, key_assumptions, risks, unknowns,
primary_pick, recommendation, suggested_next_action.

verdict: for|against|conditional (needs_research ONLY if evidence_score < 0.20)
confidence and evidence_score: floats 0.0-1.0 (NOT words like "low" or "high")
evidence_quality: high|moderate|low
influence_weight should be 0.05.
agent must be "cto".


BOARD MODE: DECISION — founder needs a usable pick, not abstention.

Rules (mandatory):
- verdict MUST be exactly one of: for | against | conditional
  Map mentally: for = lean yes, against = lean no, conditional = yes with caveats
- needs_research is FORBIDDEN unless evidence_score is below 0.20
- primary_pick: one concrete answer to the question (sector, target, option name, or "conditional: X")
- recommendation MUST start with primary_pick, then "Confidence NN%", then rationale
- If choosing between sectors/options (e.g. SaaS vs logistics), PICK ONE even if uncertain
- An imperfect recommendation beats refusing to choose

Founder principle: An imperfect recommendation is more useful than five abstentions.


## Strategic beliefs (founding doctrine)
- ICP = 200–1,500 employees
- Avoid enterprise first — no 5,000+ employee targets until 3 mid-market wins
- Revenue before perfection — ship outreach before full product polish
- Credibility over growth hacks — no fake case studies or inflated metrics

```

---

#### Agent: Operator

**File path:** `apps/backend/agents/base.py` (`run_agent`, `agent_key="operator"`)

**Prompt:**

```
You are the Operator on a founder intelligence board.
Respond in JSON only with keys:
agent, question_answered, verdict, confidence, influence_weight, evidence_quality,
research_age_days, evidence_score, evidence_used, key_assumptions, risks, unknowns,
primary_pick, recommendation, suggested_next_action.

verdict: for|against|conditional (needs_research ONLY if evidence_score < 0.20)
confidence and evidence_score: floats 0.0-1.0 (NOT words like "low" or "high")
evidence_quality: high|moderate|low
influence_weight should be 0.2.
agent must be "operator".


BOARD MODE: DECISION — founder needs a usable pick, not abstention.

Rules (mandatory):
- verdict MUST be exactly one of: for | against | conditional
  Map mentally: for = lean yes, against = lean no, conditional = yes with caveats
- needs_research is FORBIDDEN unless evidence_score is below 0.20
- primary_pick: one concrete answer to the question (sector, target, option name, or "conditional: X")
- recommendation MUST start with primary_pick, then "Confidence NN%", then rationale
- If choosing between sectors/options (e.g. SaaS vs logistics), PICK ONE even if uncertain
- An imperfect recommendation beats refusing to choose

Founder principle: An imperfect recommendation is more useful than five abstentions.


## Strategic beliefs (founding doctrine)
- ICP = 200–1,500 employees
- Avoid enterprise first — no 5,000+ employee targets until 3 mid-market wins
- Revenue before perfection — ship outreach before full product polish
- Credibility over growth hacks — no fake case studies or inflated metrics

```

---

#### Agent: Skeptic

**File path:** `apps/backend/agents/base.py` (`run_agent`, `agent_key="skeptic"`)

**Prompt:**

```
You are the Skeptic on a founder intelligence board.
Respond in JSON only with keys:
agent, question_answered, verdict, confidence, influence_weight, evidence_quality,
research_age_days, evidence_score, evidence_used, key_assumptions, risks, unknowns,
primary_pick, recommendation, suggested_next_action.

verdict: for|against|conditional (needs_research ONLY if evidence_score < 0.20)
confidence and evidence_score: floats 0.0-1.0 (NOT words like "low" or "high")
evidence_quality: high|moderate|low
influence_weight should be 0.25.
agent must be "skeptic".


BOARD MODE: DECISION — founder needs a usable pick, not abstention.

Rules (mandatory):
- verdict MUST be exactly one of: for | against | conditional
  Map mentally: for = lean yes, against = lean no, conditional = yes with caveats
- needs_research is FORBIDDEN unless evidence_score is below 0.20
- primary_pick: one concrete answer to the question (sector, target, option name, or "conditional: X")
- recommendation MUST start with primary_pick, then "Confidence NN%", then rationale
- If choosing between sectors/options (e.g. SaaS vs logistics), PICK ONE even if uncertain
- An imperfect recommendation beats refusing to choose

Founder principle: An imperfect recommendation is more useful than five abstentions.


## Strategic beliefs (founding doctrine)
- ICP = 200–1,500 employees
- Avoid enterprise first — no 5,000+ employee targets until 3 mid-market wins
- Revenue before perfection — ship outreach before full product polish
- Credibility over growth hacks — no fake case studies or inflated metrics

```

---

#### Agent: Researcher

**File path:** `apps/backend/agents/base.py` (`run_agent`, `agent_key="researcher"`)

**Prompt:**

```
You are the Researcher on a founder intelligence board.
Respond in JSON only with keys:
agent, question_answered, verdict, confidence, influence_weight, evidence_quality,
research_age_days, evidence_score, evidence_used, key_assumptions, risks, unknowns,
primary_pick, recommendation, suggested_next_action.

verdict: for|against|conditional (needs_research ONLY if evidence_score < 0.20)
confidence and evidence_score: floats 0.0-1.0 (NOT words like "low" or "high")
evidence_quality: high|moderate|low
influence_weight should be 0.4.
agent must be "researcher".


BOARD MODE: DECISION — founder needs a usable pick, not abstention.

Rules (mandatory):
- verdict MUST be exactly one of: for | against | conditional
  Map mentally: for = lean yes, against = lean no, conditional = yes with caveats
- needs_research is FORBIDDEN unless evidence_score is below 0.20
- primary_pick: one concrete answer to the question (sector, target, option name, or "conditional: X")
- recommendation MUST start with primary_pick, then "Confidence NN%", then rationale
- If choosing between sectors/options (e.g. SaaS vs logistics), PICK ONE even if uncertain
- An imperfect recommendation beats refusing to choose

Founder principle: An imperfect recommendation is more useful than five abstentions.


## Strategic beliefs (founding doctrine)
- ICP = 200–1,500 employees
- Avoid enterprise first — no 5,000+ employee targets until 3 mid-market wins
- Revenue before perfection — ship outreach before full product polish
- Credibility over growth hacks — no fake case studies or inflated metrics

```

---

#### Agent: Sales Strategist (displayed as "Sales" in UI)

**File path:** `apps/backend/agents/base.py` (`run_agent`, `agent_key="sales_strategist"`)

**Prompt:**

```
You are the Sales Strategist on a founder intelligence board.
Respond in JSON only with keys:
agent, question_answered, verdict, confidence, influence_weight, evidence_quality,
research_age_days, evidence_score, evidence_used, key_assumptions, risks, unknowns,
primary_pick, recommendation, suggested_next_action.

verdict: for|against|conditional (needs_research ONLY if evidence_score < 0.20)
confidence and evidence_score: floats 0.0-1.0 (NOT words like "low" or "high")
evidence_quality: high|moderate|low
influence_weight should be 0.1.
agent must be "sales_strategist".


BOARD MODE: DECISION — founder needs a usable pick, not abstention.

Rules (mandatory):
- verdict MUST be exactly one of: for | against | conditional
  Map mentally: for = lean yes, against = lean no, conditional = yes with caveats
- needs_research is FORBIDDEN unless evidence_score is below 0.20
- primary_pick: one concrete answer to the question (sector, target, option name, or "conditional: X")
- recommendation MUST start with primary_pick, then "Confidence NN%", then rationale
- If choosing between sectors/options (e.g. SaaS vs logistics), PICK ONE even if uncertain
- An imperfect recommendation beats refusing to choose

Founder principle: An imperfect recommendation is more useful than five abstentions.


## Strategic beliefs (founding doctrine)
- ICP = 200–1,500 employees
- Avoid enterprise first — no 5,000+ employee targets until 3 mid-market wins
- Revenue before perfection — ship outreach before full product polish
- Credibility over growth hacks — no fake case studies or inflated metrics

```

---

### Exploration mode — mode block difference only

**File:** `apps/backend/agents/base.py` — `_exploration_mode_prompt()`

```
BOARD MODE: EXPLORATION — open analysis; needs_research is allowed when evidence is thin.
verdict: go|no_go|conditional|lean_for|lean_against|needs_research
```

And verdict field becomes:

```
verdict: go|no_go|conditional|lean_for|lean_against|needs_research
```

All other system prompt structure is identical per agent (label + weight + agent key only).

---

## 3. Board Orchestrator

### Entry point

**File:** `apps/backend/orchestrator/board.py`  
**Function:** `run_board_session(session, workspace_id, question, project_id=None, board_mode="decision")`

**API route:** `apps/backend/api/routes/board.py` — `POST /board/sessions` with `BoardCreate.board_mode` default `"decision"`.

### Full orchestration flow

```33:62:apps/backend/orchestrator/board.py
async def run_board_session(
    session: AsyncSession,
    workspace_id: str,
    question: str,
    project_id: str | None = None,
    board_mode: BoardMode = "decision",
) -> BoardSession:
    beliefs = BeliefService(session)
    beliefs_block = await beliefs.pack_for_prompt(workspace_id)
    context = await _build_context(session, workspace_id, question)

    board = BoardSession(
        workspace_id=workspace_id,
        project_id=project_id,
        question=question,
        status="running",
        agent_outputs=[],
    )
    session.add(board)
    await session.flush()

    tasks = [
        run_agent(name, question, context, beliefs_block, board_mode=board_mode)
        for name in AGENT_NAMES
    ]
    outputs: list[dict[str, Any]] = list(await asyncio.gather(*tasks))

    synthesis = await synthesize_board(question, outputs, beliefs_block, board_mode=board_mode)
    board.agent_outputs = outputs
    board.status = "complete"
```

Post-synthesis: creates `Decision` row, stores `synthesis` JSON on `BoardSession`, optionally creates `InboxItem` for unresolved/conflict.

### Memory injection

**File:** `apps/backend/orchestrator/board.py`  
**Function:** `_build_context()`

```26:30:apps/backend/orchestrator/board.py
async def _build_context(session: AsyncSession, workspace_id: str, question: str) -> str:
    memory = MemoryService(session)
    chunks = await memory.search(question, workspace_id, limit=8)
    lines = [f"[{c.chunk_type}] {c.content[:800]}" for c in chunks]
    return "\n".join(lines) if lines else "No memory chunks retrieved."
```

**File:** `apps/backend/memory/retrieval.py`  
**Function:** `MemoryService.search()`

- Embeds the question via `embed_text()` → `openai/text-embedding-3-small`
- If embedding succeeds: vector search on `memory_chunks` where `embedding IS NOT NULL`
- If embedding fails: ILIKE text fallback on `content`
- **No fallback to text search when embedding succeeds but zero embedded rows exist**

Injected into each agent as the `Context:` section of the user message (max 12,000 chars).

### Beliefs injection

**File:** `apps/backend/beliefs/service.py`  
**Function:** `pack_for_prompt(workspace_id)`

```71:76:apps/backend/beliefs/service.py
    async def pack_for_prompt(self, workspace_id: str) -> str:
        beliefs = await self.list_active(workspace_id)
        if not beliefs:
            return ""
        lines = [f"- {b.content}" for b in beliefs]
        return "## Strategic beliefs (founding doctrine)\n" + "\n".join(lines)
```

Appended to **system** prompt for every agent and the synthesizer.

### Evidence injection

There is **no separate evidence pipeline** for board sessions.

- `evidence_used` is an **LLM output field** requested in the JSON schema; the orchestrator does not pre-populate it from memory chunk IDs.
- Memory content is injected only as unstructured text in `Context:`.
- Research pipeline (`apps/backend/research/pipeline.py`) writes `memory_chunks` but board does not call it automatically.

### Previous decisions injection

**Not implemented.** `run_board_session()` does not query `decisions`, `board_sessions`, or `entities`.

Grep of `apps/backend/orchestrator/` shows `Decision` is only used to **create** a new decision after the board run — not to load prior context.

### Workspace profile injection

**Not implemented** in board path. `WorkspaceProfile` (`metrics`, `context_lines`) exists in DB and API (`apps/backend/api/routes/workspaces.py`) but is never read by `orchestrator/board.py`.

### Entity injection

**Not implemented.** `entities` table is seeded (`supabase/seed.sql`) but board orchestrator never queries it.

---

## 4. Decision Mode Logic

### Board mode type

**File:** `apps/backend/agents/board_modes.py`

```5:7:apps/backend/agents/board_modes.py
BoardMode = Literal["exploration", "decision"]

NEEDS_RESEARCH_MAX_EVIDENCE = 0.2
```

**File:** `apps/backend/api/routes/board.py`

```15:22:apps/backend/api/routes/board.py
BoardMode = Literal["exploration", "decision"]


class BoardCreate(BaseModel):
    question: str
    workspace_id: str
    project_id: str | None = None
    board_mode: BoardMode = "decision"
```

### Verdict enum / schema

**Frontend TypeScript** — `apps/frontend/lib/types/index.ts`:

```1:7:apps/frontend/lib/types/index.ts
export type Verdict =
  | "go"
  | "no_go"
  | "conditional"
  | "lean_for"
  | "lean_against"
  | "needs_research";
```

**Backend:** No Pydantic enum. Verdicts are free-form strings stored in JSONB / `decisions.verdict`. Decision mode maps LLM-facing `for`/`against` to stored `lean_for`/`lean_against`.

**File:** `apps/backend/agents/board_modes.py`

```20:28:apps/backend/agents/board_modes.py
_DECISION_TO_STORED = {
    "for": "lean_for",
    "go": "lean_for",
    "lean_for": "lean_for",
    "against": "lean_against",
    "no_go": "lean_against",
    "lean_against": "lean_against",
    "conditional": "conditional",
}
```

**UI labels in Decision mode** — `apps/frontend/components/shared/verdict-badge.tsx`:

- `lean_for` / `go` → **"For"**
- `lean_against` / `no_go` → **"Against"**
- `conditional` → **"Conditional"**
- `needs_research` → **"Needs Research"**

### Validation rules — agent output

**File:** `apps/backend/agents/board_modes.py`  
**Function:** `enforce_agent_output(data, board_mode)`

```37:67:apps/backend/agents/board_modes.py
def enforce_agent_output(data: dict[str, Any], board_mode: BoardMode) -> dict[str, Any]:
    evidence_score = float(data.get("evidence_score") or 0)
    verdict_raw = _normalize_verdict_token(data.get("verdict"))

    if board_mode == "decision":
        if verdict_raw == "needs_research":
            if evidence_score < NEEDS_RESEARCH_MAX_EVIDENCE:
                data["verdict"] = "needs_research"
            else:
                data["verdict"] = "conditional"
        elif verdict_raw in _DECISION_TO_STORED:
            data["verdict"] = _DECISION_TO_STORED[verdict_raw]
        else:
            data["verdict"] = "conditional"

        rec = str(data.get("recommendation") or "").strip()
        if not rec or rec.lower().startswith("insufficient"):
            pick = str(data.get("primary_pick") or "conditional pursuit").strip()
            conf = float(data.get("confidence") or 0.5)
            data["recommendation"] = (
                f"{pick}. Confidence {int(round(conf * 100))}%. "
                "Proceed with validation steps while acting on this lean."
            )
    else:
        if verdict_raw in _EXPLORATION_VERDICTS:
            mapped = _DECISION_TO_STORED.get(verdict_raw, verdict_raw)
            data["verdict"] = mapped if mapped in _EXPLORATION_VERDICTS else verdict_raw
        else:
            data["verdict"] = "needs_research"

    return data
```

### Validation rules — synthesis

**File:** `apps/backend/agents/board_modes.py`  
**Function:** `enforce_synthesis(data, question, board_mode)`

```81:107:apps/backend/agents/board_modes.py
    if board_mode == "decision":
        if verdict_raw == "needs_research" and evidence_score >= NEEDS_RESEARCH_MAX_EVIDENCE:
            data["verdict"] = "conditional"
        elif verdict_raw in _DECISION_TO_STORED:
            data["verdict"] = _DECISION_TO_STORED[verdict_raw]
        else:
            data["verdict"] = "conditional"
    ...
    if board_mode == "decision":
        if not direct:
            direct = _first_sentence(body) or "Conditional recommendation pending founder review"
        ...
        data["recommendation"] = f"{direct} Confidence {conf_pct}%. {rest}".strip()
```

### Fallback behavior (post-LLM)

**File:** `apps/backend/agents/base.py`

| Field | Decision mode default | Exploration mode default |
|-------|----------------------|--------------------------|
| `verdict` (if missing) | `"conditional"` | `"needs_research"` |
| `confidence` | `_as_float(..., 0.55)` | same |
| `evidence_score` | `_as_float(..., 0.35)` | same |
| `recommendation` | `"Conditional pursuit — validate..."` | same |

Invalid / empty JSON from LLM → nearly all fields are defaulted, then `enforce_agent_output()` runs.

### Can an agent return "Needs Research" when evidence exists?

**Decision mode:**

| Condition | Result |
|-----------|--------|
| LLM returns `needs_research` AND `evidence_score < 0.20` | **Allowed** — stored as `needs_research` |
| LLM returns `needs_research` AND `evidence_score >= 0.20` | **Blocked** — coerced to `conditional` |
| LLM returns unknown verdict | **Fallback** → `conditional` |
| Missing verdict | Default `conditional` before enforcement |

**Exploration mode:**

- `needs_research` is allowed without evidence threshold.
- Unknown verdict → `needs_research`.

**Important:** `evidence_score` is **self-reported by the LLM**, not computed from retrieved memory. An agent can set `evidence_score: 0.15` while memory chunks exist in DB but were not retrieved — and still get `needs_research` in decision mode.

---

## 5. Agent Differentiation Audit

### Verdict

**Agents do NOT have materially different instructions.** They share one template; only these lines differ:

| Agent | Unique lines in system prompt |
|-------|------------------------------|
| CTO | `You are the CTO...`, `influence_weight should be 0.05.`, `agent must be "cto".` |
| Operator | `You are the Operator...`, `influence_weight should be 0.2.`, `agent must be "operator".` |
| Skeptic | `You are the Skeptic...`, `influence_weight should be 0.25.`, `agent must be "skeptic".` |
| Researcher | `You are the Researcher...`, `influence_weight should be 0.4.`, `agent must be "researcher".` |
| Sales | `You are the Sales Strategist...`, `influence_weight should be 0.1.`, `agent must be "sales_strategist".` |

### Examples of what is NOT differentiated

- No Skeptic-specific "challenge assumptions" rubric
- No Researcher-specific "cite sources / evidence_used requirements"
- No CTO-specific "technical feasibility" lens
- No Operator-specific "execution / hiring / ops" lens
- No Sales-specific "GTM / ICP / pipeline" lens
- Same JSON schema, same decision-mode rules, same beliefs block, same memory context for all five

### Expected behavioral outcome

All five agents receive **identical context and nearly identical instructions**. Differentiation depends entirely on the model inferring role behavior from the one-line role title — not from engineered prompt separation. This explains homogeneous outputs and weak disagreement.

---

## 6. Confidence Calculation

### Generation (LLM)

Confidence is **not calculated algorithmically**. The prompt instructs:

```
confidence and evidence_score: floats 0.0-1.0 (NOT words like "low" or "high")
```

The LLM emits `confidence` in JSON; no weighted aggregation across agents feeds individual agent confidence.

### Normalization — backend

**File:** `apps/backend/agents/base.py`  
**Function:** `_as_float(value, default=0.5)`

```34:43:apps/backend/agents/base.py
def _as_float(value: object, default: float = 0.5) -> float:
    try:
        n = float(value)  # type: ignore[arg-type]
        if n != n:  # NaN
            return default
        if n > 1.0 and n <= 100.0:
            return n / 100.0
        return max(0.0, min(1.0, n))
    except (TypeError, ValueError):
        return default
```

Applied in `run_agent()`:

```110:114:apps/backend/agents/base.py
    data["confidence"] = _as_float(data.get("confidence"), 0.55)
    data["influence_weight"] = _as_float(data.get("influence_weight"), DEFAULT_WEIGHTS[agent_key])
    ...
    data["evidence_score"] = _as_float(data.get("evidence_score"), 0.35)
```

**File:** `apps/backend/agents/synthesizer.py` — synthesis confidence:

```55:56:apps/backend/agents/synthesizer.py
    data["confidence"] = _as_float(data.get("confidence"), 0.55)
    data["evidence_score"] = _as_float(data.get("evidence_score"), 0.4)
```

**File:** `apps/backend/orchestrator/board.py` — decision row persistence:

```71:72:apps/backend/orchestrator/board.py
        confidence=_as_float(synthesis.get("confidence"), 0.5),
        evidence_score=_as_float(synthesis.get("evidence_score"), 0.5),
```

Note: orchestrator `_as_float` does **not** divide 0–100 scale (unlike `base._as_float`).

### Normalization — frontend

**File:** `apps/frontend/lib/confidence.ts`  
**Functions:** `normalizeConfidence()`, `confidencePercent()`

```1:15:apps/frontend/lib/confidence.ts
/** Coerce LLM/API values (0–1, 0–100, NaN, strings) to a safe 0–1 float. */
export function normalizeConfidence(value: unknown, fallback = 0.5): number {
  if (typeof value === "string") {
    const trimmed = value.trim().replace(/%$/, "");
    const parsed = Number(trimmed);
    if (!Number.isFinite(parsed)) return fallback;
    return parsed > 1 ? Math.min(1, parsed / 100) : Math.max(0, Math.min(1, parsed));
  }
  if (typeof value !== "number" || !Number.isFinite(value)) return fallback;
  return value > 1 ? Math.min(1, value / 100) : Math.max(0, Math.min(1, value));
}

export function confidencePercent(value: unknown, fallback = 0.5): number {
  return Math.round(normalizeConfidence(value, fallback) * 100);
}
```

**File:** `apps/frontend/components/shared/confidence-breakdown.tsx` — uses `confidencePercent()`.

**File:** `apps/frontend/components/board/agent-card.tsx` — influence weight also uses `confidencePercent()`.

### Why Researcher previously displayed NaN%

**Root cause (frontend):** Before `normalizeConfidence()`, display code used raw arithmetic:

```javascript
Math.round(confidence * 100)
Math.round(agent.influence_weight * 100)
```

`Math.round(undefined * 100)` → `NaN`. `Math.round(null * 100)` → `0` (not NaN). `Math.round("high" * 100)` → `NaN`.

**Contributing causes:**

1. **Missing or non-numeric API fields** on `agent_outputs[]` — e.g. older sessions, failed JSON parse (`{}` defaults applied only when keys missing; malformed partial JSON could leak through before fixes).
2. **LLM returned non-numeric confidence** — e.g. string `"moderate"` — backend `_as_float` now catches via `ValueError` → default `0.55`, but **historical sessions stored before normalization** could still serve bad values from DB.
3. **`influence_weight` displayed on Researcher card** — if LLM omitted it or returned non-numeric, `agent.influence_weight * 100` produced NaN in the influence line independent of confidence.
4. **No frontend guard** until `confidencePercent()` was added.

Researcher was not uniquely broken in backend code — same code path for all agents. NaN was a **display-layer** issue when numeric fields were `undefined` or non-coercible in JS.

---

## 7. Synthesis Prompt

**File:** `apps/backend/agents/synthesizer.py`  
**Function:** `synthesize_board(question, agent_outputs, beliefs_block, board_mode="decision")`

### Exact system prompt — Decision mode (default)

```
You synthesize a founder board session into one recommendation.
Return JSON with: direct_answer, recommendation, verdict, confidence, evidence_score, unknowns_level,
risks, unknowns, assumptions, next_action, rationale.

confidence and evidence_score: floats 0.0-1.0
unknowns_level: high|moderate|low


DECISION MODE synthesis rules (mandatory):
- direct_answer: ONE sentence that answers the founder's question directly (pick an option/sector/target)
- recommendation: direct_answer first, then "Confidence NN%", then risks/unknowns analysis
- verdict: for|against|conditional only (map to lean_for/lean_against/conditional); needs_research ONLY if evidence_score < 0.20
- Never open with "need more research" or "insufficient data" unless evidence_score < 0.20
- Example: "SaaS." as direct_answer for a sector question — then full recommendation with confidence

Founder principle: An imperfect recommendation is more useful than five abstentions.


## Strategic beliefs (founding doctrine)
- ICP = 200–1,500 employees
- Avoid enterprise first — no 5,000+ employee targets until 3 mid-market wins
- Revenue before perfection — ship outreach before full product polish
- Credibility over growth hacks — no fake case studies or inflated metrics

```

(Beliefs block varies by workspace; shown here for `clawback-labs`.)

### Exact system prompt — Exploration mode

Same opening, with mode block:

```
EXPLORATION MODE: broader analysis allowed; needs_research verdict OK when appropriate.
```

### User message to synthesizer

```43:43:apps/backend/agents/synthesizer.py
    user = json.dumps({"question": question, "agent_outputs": agent_outputs}, indent=2)[:14000]
```

### Does synthesis force a recommendation?

**Decision mode — yes, by prompt + post-processing:**

1. Prompt requires `direct_answer` and forbids opening with "need more research" unless `evidence_score < 0.20`.
2. `enforce_synthesis()` rebuilds `recommendation` as `"{direct_answer} Confidence {NN}%. {rest}"`.
3. Default fallback if LLM returns empty: `"Board could not reach consensus — defer decision."` then enforcement still prepends direct answer structure in decision mode.
4. `needs_research` verdict coerced to `conditional` when `evidence_score >= 0.20`.

**Exploration mode — no hard force:**

- Prompt allows `needs_research`.
- `enforce_synthesis()` does not restructure recommendation; uses body as-is.
- Fallback: `"Board could not reach consensus — defer decision."`

**Can synthesis simply repeat agents and say "do more research"?**

- **Decision mode:** Possible in the `rest` body after the forced first sentence, but opening abstention is blocked/restructured. Verdict `needs_research` is blocked unless low self-reported `evidence_score`.
- **Exploration mode:** Yes — no direct-answer enforcement.

---

## 8. Memory Usage Trace

### Question

```
Should Clawback target SaaS, logistics, or manufacturing?
```

### Workspace

`clawback-labs` (Clawback Labs)

### Live trace (2026-06-01, Supabase connected)

Executed `BeliefService.pack_for_prompt()` and `MemoryService.search()` using the same code paths as `run_board_session()`.

#### Workspace beliefs injected

**Source:** `strategic_beliefs` table via `apps/backend/beliefs/service.py`

**Exact text appended to system prompt:**

```
## Strategic beliefs (founding doctrine)
- ICP = 200–1,500 employees
- Avoid enterprise first — no 5,000+ employee targets until 3 mid-market wins
- Revenue before perfection — ship outreach before full product polish
- Credibility over growth hacks — no fake case studies or inflated metrics
```

| Metric | Value |
|--------|-------|
| Belief count | 4 |
| Characters | 292 |
| Approx tokens (chars ÷ 4) | ~73 |

**Seed source:** `supabase/seed.sql` lines 15–19.

#### Memory chunks injected

**Retrieved at runtime:** **0 chunks**

**Exact context string passed to all agents:**

```
No memory chunks retrieved.
```

| Metric | Value |
|--------|-------|
| Characters | 27 |
| Approx tokens | ~7 |

#### Why seed memory was not retrieved

**Seed data exists** in `supabase/seed.sql` lines 71–74:

```sql
INSERT INTO memory_chunks (workspace_id, chunk_type, content, summary, entity_name) VALUES
  ('clawback-labs', 'strategy_note', 'Target companies with dedicated compliance teams and recent Series B funding.', 'ICP strategy note', NULL),
  ('clawback-labs', 'entity_profile', 'Acme Corp uses legacy payroll stack. Compliance team exists per LinkedIn.', 'Acme profile', 'Acme Corp'),
  ('clawback-labs', 'research_summary', 'Acme Corp: Series B 2022, HR expansion, no public clawback litigation.', 'Acme research', 'Acme Corp'),
```

**Retrieval logic** (`apps/backend/memory/retrieval.py`):

```32:35:apps/backend/memory/retrieval.py
        embedding = await embed_text(query)
        if embedding:
            return await self._vector_search(embedding, workspace_id, project_id, limit)
        return await self._text_fallback(query, workspace_id, project_id, limit)
```

```49:49:apps/backend/memory/retrieval.py
            WHERE workspace_id = :ws AND embedding IS NOT NULL
```

Seed inserts **do not populate `embedding`**. OpenRouter embedding **succeeds** → vector search runs → zero rows match `embedding IS NOT NULL` → empty list → **text fallback never runs**.

**None of the three seed chunks are relevant to SaaS/logistics/manufacturing sector selection anyway** — they describe Acme Corp and generic ICP strategy.

#### Retrieved entities

**Not injected.** Board orchestrator has no `Entity` query.

**Entities in DB for `clawback-labs` (not passed to board):**

| name | type | summary |
|------|------|---------|
| Acme Corp | company | Series B HR expansion; conditional board fit. ~2,400 employees. |
| BrightPay Inc | company | ICP band match; compliance team hiring signals. |

From `supabase/seed.sql` lines 41–58.

#### Research evidence

**Not injected directly.** Research summaries exist only if stored as `memory_chunks` with `chunk_type = 'research_summary'` **and** non-null `embedding`. Currently none retrieved.

Research pipeline (`apps/backend/research/pipeline.py`) is a separate `POST /research/run` flow — not triggered by board.

#### Previous decisions

**Not injected.** No query of `decisions` or prior `board_sessions` in orchestrator.

#### Workspace profile

**Not injected.** `workspace_profiles.context_lines` for clawback-labs includes:

```json
["Mid-market payroll clawback recovery", "Series B–D employers with compliance teams", "Avoid enterprise motion until 3 wins"]
```

From `supabase/seed.sql` lines 28–29 — **available in DB, unused by board**.

#### Full user prompt per agent (this question)

```
Question: Should Clawback target SaaS, logistics, or manufacturing?

Context:
No memory chunks retrieved.
```

| Metric | Value |
|--------|-------|
| User prompt characters | ~95 |
| Approx tokens | ~24 |

#### Synthesizer input size

Agent outputs JSON serialized, truncated to **14,000 characters** (`synthesizer.py` line 43). Token count depends on LLM output size; not logged at runtime.

---

## 9. Improvement Recommendations

Ranked by expected impact on board quality. **No code changes made** — recommendations only.

### 1. Per-agent role prompts with enforced disagreement (Impact: Critical)

**Problem:** Section 5 — one template, title-only differentiation.  
**Change:** Add dedicated system blocks per agent (Skeptic must argue against; Researcher must cite `evidence_used` from context; Sales anchors ICP/pipeline; CTO on build complexity; Operator on execution capacity). Require Skeptic verdict ≠ majority when evidence_score < 0.5.  
**Files:** `apps/backend/agents/base.py` (or split into `agents/prompts/cto.py`, etc.)

### 2. Fix memory retrieval dead zone (Impact: Critical)

**Problem:** Section 8 — seed chunks never retrieved; vector path returns empty when no embeddings.  
**Change:** If vector search returns 0 rows, fall back to text/keyword search; backfill embeddings on seed ingest; run embedding job for existing chunks.  
**Files:** `apps/backend/memory/retrieval.py`, `supabase/seed.sql`, ingestion pipeline.

### 3. Inject workspace profile + entities + prior decisions (Impact: High)

**Problem:** Section 3 — only beliefs + memory text injected; rich DB context ignored.  
**Change:** Extend `_build_context()` to append `WorkspaceProfile.context_lines`, top-N entities by question similarity, last 3 decisions on related topics.  
**Files:** `apps/backend/orchestrator/board.py`, new `context/builder.py`.

### 4. Bind `evidence_used` to retrieved chunk IDs (Impact: High)

**Problem:** `evidence_used` is LLM-hallucinated; memory injected as opaque text.  
**Change:** Pass structured chunk list with IDs in prompt; validate `evidence_used[].chunk_id` against retrieval set; penalize/retry if empty while chunks exist.  
**Files:** `apps/backend/orchestrator/board.py`, `apps/backend/agents/base.py`.

### 5. Compute `evidence_score` from retrieval, not LLM self-report (Impact: High)

**Problem:** Section 4 — agent can claim `evidence_score: 0.15` to unlock `needs_research` despite DB data.  
**Change:** `evidence_score = f(chunks_retrieved, similarity scores, recency)` computed server-side; override or cap LLM value.  
**Files:** `apps/backend/orchestrator/board.py`, `apps/backend/agents/board_modes.py`.

### 6. Model tiering per agent (Impact: High)

**Problem:** Section 1 — all agents on `gpt-4o-mini`, no temperature tuning.  
**Change:** Skeptic/Researcher on stronger model; Operator/Sales on mini; set `temperature` (e.g. 0.3 Researcher, 0.7 Skeptic); optional `max_tokens` per stage.  
**Files:** `apps/backend/config.py`, `apps/backend/llm/openrouter.py`, `apps/backend/agents/base.py`.

### 7. Weighted synthesis from agent outputs (Impact: Medium-High)

**Problem:** Synthesizer re-reads raw JSON; influence weights are prompt-only.  
**Change:** Server-side weighted vote (`lean_for` × weight × confidence); synthesis prompt receives pre-computed tally + dissent summary; force synthesis to address top dissent.  
**Files:** `apps/backend/agents/synthesizer.py`, new `agents/consensus.py`.

### 8. Sector/question-type structured output schema (Impact: Medium)

**Problem:** Sector questions need `primary_pick` from a constrained set; free text allows vague answers.  
**Change:** Detect multi-choice questions; add JSON schema `options_considered`, `selected_option`, `rejected_options[]` with required rationale per rejection.  
**Files:** `apps/backend/agents/base.py`, `apps/backend/agents/board_modes.py`.

### 9. Belief anchoring requirements (Impact: Medium)

**Problem:** Beliefs appended but not required to be cited.  
**Change:** Prompt rule: "Must cite ≥1 belief ID in `key_assumptions` or flag `belief_conflict`"; validate against `pack_for_prompt` list.  
**Files:** `apps/backend/beliefs/service.py`, `apps/backend/agents/base.py`.

### 10. Log and expose context trace on board session (Impact: Medium)

**Problem:** Section 8 — founders cannot see what was/wasn't injected; debugging requires code reading.  
**Change:** Store `context_trace` on `board_sessions.synthesis` JSON: beliefs chars, chunk IDs, scores, token estimates, missing embedding count.  
**Files:** `apps/backend/orchestrator/board.py`, `apps/backend/schemas/types.py`, frontend board debug panel.

---

## Appendix A — File Index

| Concern | Path |
|---------|------|
| Agent factory | `apps/backend/agents/base.py` |
| Decision mode enforcement | `apps/backend/agents/board_modes.py` |
| Synthesis | `apps/backend/agents/synthesizer.py` |
| Orchestrator | `apps/backend/orchestrator/board.py` |
| API | `apps/backend/api/routes/board.py` |
| LLM / OpenRouter | `apps/backend/llm/openrouter.py` |
| Config / models | `apps/backend/config.py` |
| Memory search | `apps/backend/memory/retrieval.py` |
| Beliefs | `apps/backend/beliefs/service.py` |
| DB models | `apps/backend/db/models.py` |
| API types | `apps/backend/schemas/types.py` |
| Frontend board UI | `apps/frontend/components/board/board-view.tsx` |
| Verdict display | `apps/frontend/components/shared/verdict-badge.tsx` |
| Confidence display | `apps/frontend/lib/confidence.ts` |
| Seed data | `supabase/seed.sql` |
| Board mode tests | `apps/backend/tests/test_board_modes.py` |

## Appendix B — Configuration reference

| Setting | Default | Env override |
|---------|---------|--------------|
| `chat_model` | `openai/gpt-4o-mini` | `CHAT_MODEL` (if set in `.env`) |
| `embedding_model` | `openai/text-embedding-3-small` | `EMBEDDING_MODEL` |
| `board_mode` default | `decision` | Request body `board_mode` |
| `NEEDS_RESEARCH_MAX_EVIDENCE` | `0.2` | Code constant only |
| OpenRouter base URL | `https://openrouter.ai/api/v1` | Hardcoded |
| Context max chars (agents) | `12000` | Hardcoded in `base.py` |
| Synthesis input max chars | `14000` | Hardcoded in `synthesizer.py` |
| Memory chunks retrieved | `8` (max returned after scoring) | `limit=8` in `_build_context` |
