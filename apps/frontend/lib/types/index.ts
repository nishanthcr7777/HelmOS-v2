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
  | "research_summary"
  | "decision_log"
  | "entity_profile"
  | "document_chunk";

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

export interface Decision {
  id: string;
  workspace_id: string;
  project_id?: string;
  question: string;
  synthesis: string;
  verdict: Verdict;
  confidence: number;
  agent_outputs: AgentOutput[];
  risks: string[];
  unknowns: string[];
  assumptions: string[];
  next_action?: string;
  status: "open" | "resolved" | "deferred";
  resolved_at?: string;
  created_at: string;
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
