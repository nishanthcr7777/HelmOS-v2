import type {
  BoardAlert,
  DashboardPayload,
  Decision,
  DecisionTimelineEvent,
  EntityCard,
  FocusPriority,
  FounderState,
  OpportunityFeedItem,
  StrategicBelief,
  WorkspaceProfile,
} from "@/lib/types";
import { boardSessions, decisions as baseDecisions, inboxItems } from "./data";

export const founderState: FounderState = {
  decision_load: "moderate",
  blocked_items: inboxItems.filter((i) => i.item_type === "blocked_action" && i.status === "open").length,
  open_decisions: 4,
  research_needed: 3,
};

export const todaysFocus: FocusPriority[] = [
  {
    id: "focus-claw",
    workspace_id: "clawback-labs",
    workspace_name: "Clawback Labs",
    items: [
      "Qualify 3 target companies",
      "Review Acme Corp board session",
      "Resolve board conflict on Acme priority",
    ],
  },
  {
    id: "focus-nex",
    workspace_id: "nexops",
    workspace_name: "NexOps",
    items: [
      "Follow up on mentor feedback",
      "Review BCH ecosystem opportunity",
      "Unblock self-serve onboarding path",
    ],
  },
];

export const boardAlerts: BoardAlert[] = [
  {
    id: "alert-1",
    workspace_id: "clawback-labs",
    alert_type: "conflict",
    title: "Conflicting agent opinions on Acme Corp",
    detail: "Operator & Skeptic lean against; Sales Strategist leans for.",
    session_id: "session-acme-001",
    created_at: "2026-05-28T15:00:00Z",
  },
  {
    id: "alert-2",
    workspace_id: "clawback-labs",
    alert_type: "risky_assumption",
    title: "Unverified compliance pain at Acme",
    detail: "Skeptic: no public evidence of in-market urgency.",
    session_id: "session-acme-001",
    created_at: "2026-05-28T15:01:00Z",
  },
  {
    id: "alert-3",
    workspace_id: "nexops",
    alert_type: "low_confidence",
    title: "Low-confidence self-serve recommendation",
    detail: "Synthesis confidence 60% — support playbook gap unknown.",
    session_id: "session-nex-001",
    created_at: "2026-05-25T11:00:00Z",
  },
];

export const opportunities: OpportunityFeedItem[] = [
  {
    id: "opp-1",
    workspace_id: "clawback-labs",
    workspace_name: "Clawback Labs",
    title: "Series B companies in ICP band",
    detail: "12 matches from Q3 research pass — review for outreach.",
    created_at: "2026-05-27T09:00:00Z",
  },
  {
    id: "opp-2",
    workspace_id: "clawback-labs",
    workspace_name: "Clawback Labs",
    title: "Acme Corp — potential lead",
    detail: "HR expansion signals; conditional board verdict.",
    entity_name: "Acme Corp",
    created_at: "2026-05-28T14:30:00Z",
  },
  {
    id: "opp-3",
    workspace_id: "nexops",
    workspace_name: "NexOps",
    title: "BCH ecosystem partnership window",
    detail: "Mentor intro pending — align pilot narrative.",
    created_at: "2026-05-26T10:00:00Z",
  },
];

const acmeTimeline: DecisionTimelineEvent[] = [
  {
    id: "tl-1",
    stage: "question",
    label: "Question",
    summary: "Is Acme Corp a good Clawback target?",
    at: "2026-05-28T10:00:00Z",
  },
  {
    id: "tl-2",
    stage: "research",
    label: "Research",
    summary: "Tavily + memory: Series B, HR expansion, no public clawback signals.",
    at: "2026-05-28T13:00:00Z",
  },
  {
    id: "tl-3",
    stage: "board",
    label: "Board Review",
    summary: "5-agent review — conditional pursue with validation gates.",
    at: "2026-05-28T14:30:00Z",
  },
  {
    id: "tl-4",
    stage: "decision",
    label: "Final Decision",
    summary: "Open — founder validation required before prioritization.",
    at: "2026-05-28T15:00:00Z",
  },
];

export const decisionsEnriched: Decision[] = baseDecisions.map((d) => {
  const session = boardSessions.find((s) => `decision-${s.id}` === d.id);
  const synthesis = session?.synthesis;
  return {
    ...d,
    title: d.question.length > 48 ? `${d.question.slice(0, 48)}…` : d.question,
    evidence_score: synthesis?.evidence_score ?? 0.65,
    risk_level:
      (d.risks?.length ?? 0) >= 3 ? "high" : (d.risks?.length ?? 0) >= 2 ? "moderate" : "low",
    unknowns_level: synthesis?.unknowns_level ?? "high",
    updated_at: d.created_at,
    status:
      d.id === "decision-session-acme-001"
        ? "open"
        : d.id === "decision-session-nex-001"
          ? "pursuing"
          : "resolved",
    timeline:
      d.id === "decision-session-acme-001"
        ? acmeTimeline
        : [
            {
              id: "tl-n1",
              stage: "question",
              label: "Question",
              summary: d.question,
              at: d.created_at,
            },
            {
              id: "tl-n2",
              stage: "board",
              label: "Board Review",
              summary: d.synthesis,
              at: d.created_at,
            },
          ],
  };
});

export const dashboardPayload: DashboardPayload = {
  founder_state: founderState,
  todays_focus: todaysFocus,
  active_decisions: decisionsEnriched.filter((d) =>
    ["open", "pursuing", "deferred"].includes(d.status)
  ),
  board_alerts: boardAlerts,
  opportunities,
};

export const workspaceProfiles: Record<string, WorkspaceProfile> = {
  "clawback-labs": {
    workspace_id: "clawback-labs",
    metrics: [
      { label: "ICP", value: "200–1,500 employees" },
      { label: "Pipeline", value: "18 targets" },
      { label: "Active Targets", value: "6 qualified" },
      { label: "Revenue Goal", value: "$120K ARR Q3" },
    ],
    context_lines: [
      "Multi-state payroll · compliance hiring signal",
      "Avoid enterprise motion until 3 mid-market wins",
    ],
  },
  nexops: {
    workspace_id: "nexops",
    metrics: [
      { label: "Roadmap", value: "Pilot → GA Q4" },
      { label: "Open Issues", value: "7" },
      { label: "BCH Opportunities", value: "2 active" },
      { label: "Ecosystem", value: "Mentor pipeline warm" },
    ],
    context_lines: [
      "Self-serve deferred pending support playbooks",
      "Founder prioritizes credibility over growth hacks",
    ],
  },
};

export const strategicBeliefs: StrategicBelief[] = [
  {
    id: "belief-claw-1",
    workspace_id: "clawback-labs",
    content: "ICP = 200–1,500 employees with multi-state payroll complexity",
    created_at: "2026-04-01T00:00:00Z",
  },
  {
    id: "belief-claw-2",
    workspace_id: "clawback-labs",
    content: "Avoid enterprise first — prove mid-market motion before upmarket",
    created_at: "2026-04-05T00:00:00Z",
  },
  {
    id: "belief-claw-3",
    workspace_id: "clawback-labs",
    content: "Founder prioritizes credibility over growth hacks in outreach",
    created_at: "2026-04-10T00:00:00Z",
  },
  {
    id: "belief-nex-1",
    workspace_id: "nexops",
    content: "Pilot customers need guided onboarding — not self-serve yet",
    created_at: "2026-05-01T00:00:00Z",
  },
  {
    id: "belief-nex-2",
    workspace_id: "nexops",
    content: "BCH ecosystem is primary partnership lane for Q3",
    created_at: "2026-05-12T00:00:00Z",
  },
];

export const entityCards: EntityCard[] = [
  {
    id: "entity-acme",
    workspace_id: "clawback-labs",
    name: "Acme Corp",
    entity_type: "company",
    last_researched_at: "2026-05-28T13:00:00Z",
    research_age_days: 3,
    confidence: 0.63,
    linked_decision_ids: ["decision-session-acme-001"],
    summary: "Legacy payroll, compliance team ~8, Series B 2022. Conditional target.",
  },
  {
    id: "entity-vertex",
    workspace_id: "clawback-labs",
    name: "Vertex Payroll",
    entity_type: "company",
    last_researched_at: "2026-05-20T00:00:00Z",
    research_age_days: 11,
    confidence: 0.48,
    linked_decision_ids: [],
    summary: "Mid-market HR tech — research stale, re-run before outreach.",
  },
  {
    id: "entity-bch",
    workspace_id: "nexops",
    name: "BCH Collective",
    entity_type: "partner",
    last_researched_at: "2026-05-26T00:00:00Z",
    research_age_days: 5,
    confidence: 0.55,
    linked_decision_ids: [],
    summary: "Ecosystem partner — mentor intro path open.",
  },
];
