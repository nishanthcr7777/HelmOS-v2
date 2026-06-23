import type {
  AgentOutput,
  BoardSession,
  InboxItem,
  MemoryChunk,
  Project,
  ResearchJob,
  Workspace,
} from "@/lib/types";

export const workspaces: Workspace[] = [
  {
    id: "clawback-labs",
    name: "Clawback Labs",
    description: "Payroll clawback recovery for mid-market employers",
  },
  {
    id: "nexops",
    name: "NexOps",
    description: "Operations intelligence and workflow automation",
  },
];

export const projects: Project[] = [
  { id: "proj-claw-q3", workspace_id: "clawback-labs", name: "Q3 Outreach Campaign", status: "active" },
  { id: "proj-claw-icp", workspace_id: "clawback-labs", name: "ICP Refinement", status: "active" },
  { id: "proj-nex-pilot", workspace_id: "nexops", name: "Pilot Onboarding", status: "active" },
];

const agentOutputsAcme: AgentOutput[] = [
  {
    agent: "cto",
    question_answered: "Is Acme Corp a good Clawback target?",
    verdict: "conditional",
    confidence: 0.62,
    influence_weight: 0.05,
    evidence_quality: "low",
    research_age_days: 14,
    evidence_score: 0.45,
    evidence_used: [{ source: "memory_chunk", snippet: "Acme uses legacy payroll stack", chunk_id: "chunk-1" }],
    key_assumptions: ["Technical integration is feasible within 6 weeks"],
    risks: ["Unknown API access to payroll vendor"],
    unknowns: ["Current payroll provider contract terms"],
    recommendation: "Proceed only after confirming payroll system compatibility.",
    suggested_next_action: "Request payroll vendor from champion contact",
  },
  {
    agent: "operator",
    question_answered: "Is Acme Corp a good Clawback target?",
    verdict: "lean_against",
    confidence: 0.58,
    influence_weight: 0.2,
    evidence_quality: "moderate",
    research_age_days: 3,
    evidence_score: 0.68,
    evidence_used: [{ source: "tavily_search", snippet: "Acme Corp headcount ~2,400", url: "https://example.com/acme" }],
    key_assumptions: ["Sales cycle under 90 days"],
    risks: ["Account may require enterprise motion outside current capacity"],
    unknowns: ["Decision-maker accessibility"],
    recommendation: "Deprioritize until smaller proof accounts close.",
    suggested_next_action: "Focus on 200–800 employee targets this quarter",
  },
  {
    agent: "skeptic",
    question_answered: "Is Acme Corp a good Clawback target?",
    verdict: "lean_against",
    confidence: 0.65,
    influence_weight: 0.25,
    evidence_quality: "moderate",
    research_age_days: 3,
    evidence_score: 0.7,
    evidence_used: [{ source: "tavily_search", snippet: "No public clawback litigation signals", url: "https://example.com/news" }],
    key_assumptions: ["Assumes active compliance pain"],
    risks: ["No verified in-market urgency"],
    unknowns: ["Recent layoffs or reorgs"],
    recommendation: "Do not prioritize without confirming active compliance need.",
    suggested_next_action: "Search HR/compliance job postings in last 90 days",
  },
  {
    agent: "researcher",
    question_answered: "Is Acme Corp a good Clawback target?",
    verdict: "conditional",
    confidence: 0.71,
    influence_weight: 0.4,
    evidence_quality: "high",
    research_age_days: 3,
    evidence_score: 0.82,
    evidence_used: [
      { source: "tavily_search", snippet: "Series B in 2022, expanding HR ops", url: "https://example.com/funding" },
      { source: "memory_chunk", snippet: "Prior note: compliance team exists", chunk_id: "chunk-2" },
    ],
    key_assumptions: [],
    risks: ["Public data may be stale"],
    unknowns: ["Current headcount"],
    recommendation: "Moderate fit — validate compliance budget owner.",
    suggested_next_action: "Run targeted research on recent HR leadership changes",
  },
  {
    agent: "sales_strategist",
    question_answered: "Is Acme Corp a good Clawback target?",
    verdict: "lean_for",
    confidence: 0.55,
    influence_weight: 0.1,
    evidence_quality: "moderate",
    research_age_days: 7,
    evidence_score: 0.6,
    evidence_used: [{ source: "memory_chunk", snippet: "ICP: mid-market with distributed workforce", chunk_id: "chunk-3" }],
    key_assumptions: ["Buyer cares about payroll error recovery"],
    risks: ["Pitch may miss finance vs HR buyer"],
    unknowns: ["Budget cycle timing"],
    recommendation: "Test message around payroll audit exposure, not generic savings.",
    suggested_next_action: "Draft 2-line outreach A/B for HR vs Finance",
  },
];

export const boardSessions: BoardSession[] = [
  {
    id: "session-acme-001",
    workspace_id: "clawback-labs",
    project_id: "proj-claw-q3",
    question: "Is Acme Corp a good Clawback target?",
    status: "complete",
    agent_outputs: agentOutputsAcme,
    synthesis: {
      recommendation:
        "Conditional pursue: evidence suggests fit but skeptic and operator flags require validation before prioritization.",
      verdict: "conditional",
      confidence: 0.63,
      evidence_score: 0.72,
      unknowns_level: "high",
      risks: [
        "No verified in-market urgency",
        "Account size may stretch current sales motion",
        "Unknown payroll integration path",
      ],
      unknowns: ["Current headcount", "Compliance budget owner", "Payroll vendor"],
      assumptions: ["Acme still has active compliance function"],
      next_action: "Confirm compliance need via job postings + champion intro within 2 weeks",
    },
    created_at: "2026-05-28T14:30:00Z",
  },
  {
    id: "session-nex-001",
    workspace_id: "nexops",
    question: "Should we launch self-serve onboarding for pilot customers?",
    status: "complete",
    agent_outputs: agentOutputsAcme.map((a) => ({
      ...a,
      question_answered: "Should we launch self-serve onboarding for pilot customers?",
    })),
    synthesis: {
      recommendation: "Defer self-serve until support playbooks are documented.",
      verdict: "conditional",
      confidence: 0.6,
      evidence_score: 0.55,
      unknowns_level: "moderate",
      risks: ["Support load spike", "Incomplete docs"],
      unknowns: ["Pilot customer technical sophistication"],
      assumptions: ["Current team can handle 5 pilots"],
      next_action: "Ship guided onboarding checklist first",
    },
    created_at: "2026-05-25T10:00:00Z",
  },
];

export const decisions = boardSessions.map((s) => ({
  id: `decision-${s.id}`,
  workspace_id: s.workspace_id,
  project_id: s.project_id,
  title: s.question,
  question: s.question,
  synthesis: s.synthesis?.recommendation ?? "",
  verdict: s.synthesis?.verdict ?? "conditional",
  confidence: s.synthesis?.confidence ?? 0.5,
  evidence_score: s.synthesis?.evidence_score ?? 0.5,
  risk_level: "moderate" as const,
  unknowns_level: s.synthesis?.unknowns_level ?? ("moderate" as const),
  agent_outputs: s.agent_outputs,
  risks: s.synthesis?.risks ?? [],
  unknowns: s.synthesis?.unknowns ?? [],
  assumptions: s.synthesis?.assumptions ?? [],
  next_action: s.synthesis?.next_action,
  status: s.id === "session-acme-001" ? ("open" as const) : ("resolved" as const),
  updated_at: s.created_at,
  created_at: s.created_at,
}));

export const inboxItems: InboxItem[] = [
  {
    id: "inbox-1",
    workspace_id: "clawback-labs",
    decision_id: "decision-session-acme-001",
    item_type: "conflict",
    title: "Board split on Acme Corp priority",
    body: "Operator and Skeptic lean against; Sales Strategist leans for.",
    priority: "high",
    status: "open",
    created_at: "2026-05-28T15:00:00Z",
  },
  {
    id: "inbox-2",
    workspace_id: "clawback-labs",
    item_type: "risky_assumption",
    title: "Unverified compliance pain at Acme",
    body: "Skeptic flagged assumption without public evidence.",
    priority: "high",
    status: "open",
    created_at: "2026-05-28T15:01:00Z",
  },
  {
    id: "inbox-3",
    workspace_id: "clawback-labs",
    item_type: "unresolved_decision",
    title: "Resolve Acme target verdict",
    body: "Conditional pursue — needs founder call on prioritization.",
    priority: "medium",
    status: "open",
    created_at: "2026-05-28T15:02:00Z",
  },
  {
    id: "inbox-4",
    workspace_id: "nexops",
    item_type: "blocked_action",
    title: "Self-serve blocked on support docs",
    body: "Operator recommendation: complete playbooks first.",
    priority: "medium",
    status: "open",
    created_at: "2026-05-25T11:00:00Z",
  },
  {
    id: "inbox-5",
    workspace_id: "clawback-labs",
    item_type: "opportunity",
    title: "Series B companies in ICP band",
    body: "Researcher found 12 matches in Q3 list — review for outreach.",
    priority: "low",
    status: "open",
    created_at: "2026-05-27T09:00:00Z",
  },
];

function makeChunks(workspaceId: string): MemoryChunk[] {
  const base = [
    {
      chunk_type: "strategy_note" as const,
      content: "ICP focus: 200–1,500 employees, multi-state payroll, recent audit or compliance hiring.",
      entity_name: undefined,
    },
    {
      chunk_type: "entity_profile" as const,
      content: "Acme Corp — legacy payroll, compliance team ~8, Series B 2022.",
      entity_name: "Acme Corp",
    },
    {
      chunk_type: "research_summary" as const,
      content: "Tavily summary: Acme expanding HR operations; no public clawback cases.",
      entity_name: "Acme Corp",
      source_url: "https://example.com/acme-overview",
    },
    {
      chunk_type: "decision_log" as const,
      content: "Board session: conditional pursue Acme pending compliance validation.",
      entity_name: "Acme Corp",
    },
    {
      chunk_type: "document_chunk" as const,
      content: "Outbound playbook v2 — lead with audit exposure, not generic ROI.",
      source_file: "playbook-v2.pdf",
    },
  ];
  return Array.from({ length: 24 }, (_, i) => {
    const item = base[i % base.length];
    return {
      id: `chunk-${workspaceId}-${i}`,
      workspace_id: workspaceId,
      project_id: workspaceId === "clawback-labs" ? "proj-claw-q3" : "proj-nex-pilot",
      chunk_type: item.chunk_type,
      content: `${item.content} (record ${i + 1})`,
      summary: item.content.slice(0, 80),
      source_url: "source_url" in item ? item.source_url : undefined,
      source_file: "source_file" in item ? item.source_file : undefined,
      entity_name: item.entity_name,
      fetched_at: item.chunk_type === "research_summary" ? "2026-05-20T00:00:00Z" : undefined,
      created_at: new Date(2026, 4, 1 + (i % 28)).toISOString(),
    };
  });
}

export const memoryChunks: MemoryChunk[] = [
  ...makeChunks("clawback-labs"),
  ...makeChunks("nexops"),
];

export const researchJobs: ResearchJob[] = [
  {
    id: "research-job-1",
    workspace_id: "clawback-labs",
    entity_name: "Acme Corp",
    queries: ["Acme Corp company overview", "Acme Corp payroll compliance news"],
    step: "done",
    sources: [
      {
        url: "https://example.com/acme",
        title: "Acme Corp Company Profile",
        snippet: "Enterprise software company, ~2,400 employees.",
        published_at: "2025-11-01",
        relevance: "relevant",
      },
      {
        url: "https://example.com/acme-hr",
        title: "Acme HR Expansion",
        snippet: "Hiring compliance analysts in Austin and Denver.",
        published_at: "2026-03-15",
        relevance: "relevant",
      },
      {
        url: "https://example.com/acme-funding",
        title: "Acme Series B",
        snippet: "Raised $45M Series B in 2022.",
        published_at: "2022-06-10",
        relevance: "maybe",
      },
    ],
    created_at: "2026-05-28T13:00:00Z",
  },
];

export const suggestedPrompts: Record<string, string[]> = {
  "clawback-labs": [
    "Is Acme Corp a good Clawback target?",
    "Summarize our Q3 outreach strategy",
    "What risks did the board flag last session?",
  ],
  nexops: [
    "Should we launch self-serve onboarding?",
    "What blockers exist for pilot customers?",
    "Summarize NexOps pilot status",
  ],
};

export const chatStreamResponse = `Based on stored context, **Acme Corp** shows moderate fit as a Clawback target.

**Key points:**
- Entity profile notes legacy payroll and an active compliance team
- Research summaries show HR expansion but no public clawback signals
- Prior board session reached a *conditional pursue* verdict

**Confidence:** Moderate (0.63) — verify compliance pain before prioritizing.

Use **Invoke Board** for a full adversarial review with all five agents.`;
