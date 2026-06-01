export type Verdict =
  | "go"
  | "no_go"
  | "conditional"
  | "lean_for"
  | "lean_against"
  | "needs_research";

export type MessageTag = "plain" | "board" | "research";

export type ChunkType =
  | "strategy_note"
  | "strategic_belief"
  | "research_summary"
  | "decision_log"
  | "entity_profile"
  | "document_chunk";

export type DecisionStatus =
  | "open"
  | "pursuing"
  | "deferred"
  | "rejected"
  | "resolved";

export type QualityLevel = "high" | "moderate" | "low";

export type UnknownsLevel = "high" | "moderate" | "low";

export type InboxItemType =
  | "unresolved_decision"
  | "risky_assumption"
  | "blocked_action"
  | "opportunity"
  | "conflict";

export type ResearchStep =
  | "querying"
  | "searching"
  | "extracting"
  | "summarizing"
  | "done"
  | "idle";

export type EntityType = "company" | "person" | "partner" | "market";

export interface EvidenceSource {
  source: string;
  snippet: string;
  url?: string;
  chunk_id?: string;
  summary?: string;
}

export interface AgentOutput {
  agent: string;
  question_answered: string;
  verdict: Verdict;
  confidence: number;
  influence_weight: number;
  evidence_quality: QualityLevel;
  research_age_days: number;
  evidence_score: number;
  evidence_used: EvidenceSource[];
  key_assumptions: string[];
  risks: string[];
  unknowns: string[];
  recommendation: string;
  suggested_next_action: string;
}

export interface BoardSynthesis {
  recommendation: string;
  verdict: Verdict;
  confidence: number;
  evidence_score: number;
  unknowns_level: UnknownsLevel;
  risks: string[];
  unknowns: string[];
  assumptions: string[];
  next_action: string;
  rationale?: string;
}

export interface BoardSession {
  id: string;
  workspace_id: string;
  project_id?: string;
  question: string;
  status: "running" | "complete";
  agent_outputs: AgentOutput[];
  synthesis?: BoardSynthesis;
  created_at: string;
}

export interface MemoryChunk {
  id: string;
  workspace_id: string;
  project_id?: string;
  chunk_type: ChunkType;
  content: string;
  summary?: string;
  source_url?: string;
  source_file?: string;
  entity_name?: string;
  fetched_at?: string;
  created_at: string;
}

export interface StrategicBelief {
  id: string;
  workspace_id: string;
  content: string;
  created_at: string;
}

export interface EntityCard {
  id: string;
  workspace_id: string;
  name: string;
  entity_type: EntityType;
  last_researched_at?: string;
  research_age_days?: number;
  confidence: number;
  linked_decision_ids: string[];
  summary: string;
}

export interface Decision {
  id: string;
  workspace_id: string;
  project_id?: string;
  title: string;
  question: string;
  synthesis: string;
  verdict: Verdict;
  confidence: number;
  evidence_score: number;
  risk_level: QualityLevel;
  unknowns_level: UnknownsLevel;
  agent_outputs: AgentOutput[];
  risks: string[];
  unknowns: string[];
  assumptions: string[];
  next_action?: string;
  status: DecisionStatus;
  resolved_at?: string;
  updated_at: string;
  created_at: string;
  timeline?: DecisionTimelineEvent[];
}

export interface DecisionTimelineEvent {
  id: string;
  stage: "question" | "research" | "board" | "decision" | "outcome";
  label: string;
  summary: string;
  at: string;
}

export interface InboxItem {
  id: string;
  workspace_id: string;
  decision_id?: string;
  item_type: InboxItemType;
  title: string;
  body?: string;
  priority: "high" | "medium" | "low";
  status: "open" | "resolved" | "dismissed";
  created_at: string;
}

export interface Workspace {
  id: string;
  name: string;
  description?: string;
}

export interface WorkspaceProfile {
  workspace_id: string;
  metrics: { label: string; value: string }[];
  context_lines: string[];
}

export interface Project {
  id: string;
  workspace_id: string;
  name: string;
  status: "active" | "archived";
}

export interface ResearchSource {
  url: string;
  title: string;
  snippet: string;
  published_at?: string;
  relevance: "relevant" | "maybe" | "skip";
}

export interface ResearchJob {
  id: string;
  workspace_id: string;
  entity_name: string;
  queries: string[];
  step: ResearchStep;
  sources: ResearchSource[];
  created_at: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  tag?: MessageTag;
  confidence?: number;
  evidence?: EvidenceSource[];
}

export interface EvidencePacket {
  entity_name: string;
  summaries: { key_facts: string; source_url: string }[];
  fetched_at: string;
}

export interface FounderState {
  decision_load: QualityLevel;
  blocked_items: number;
  open_decisions: number;
  research_needed: number;
}

export interface FocusPriority {
  id: string;
  workspace_id: string;
  workspace_name: string;
  items: string[];
}

export interface BoardAlert {
  id: string;
  workspace_id: string;
  alert_type: "conflict" | "risky_assumption" | "low_confidence";
  title: string;
  detail: string;
  session_id?: string;
  created_at: string;
}

export interface OpportunityFeedItem {
  id: string;
  workspace_id: string;
  workspace_name: string;
  title: string;
  detail: string;
  entity_name?: string;
  created_at: string;
}

export interface DashboardPayload {
  founder_state: FounderState;
  todays_focus: FocusPriority[];
  active_decisions: Decision[];
  board_alerts: BoardAlert[];
  opportunities: OpportunityFeedItem[];
}
