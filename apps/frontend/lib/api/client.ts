import { API_BASE } from "./config";
import type {
  BoardSession,
  Decision,
  InboxItem,
  MemoryChunk,
  Project,
  ResearchJob,
  Workspace,
} from "@/lib/types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) throw new Error(`API error: ${res.status} ${path}`);
  return res.json() as Promise<T>;
}

export const api = {
  getWorkspaces: () => request<Workspace[]>("/workspaces"),

  getProjects: (workspaceId: string) =>
    request<Project[]>(`/workspaces/${workspaceId}/projects`),

  getMemoryChunks: (params: {
    workspace_id: string;
    project_id?: string;
    type?: string;
    search?: string;
  }) => {
    const q = new URLSearchParams({ workspace_id: params.workspace_id });
    if (params.project_id) q.set("project_id", params.project_id);
    if (params.type) q.set("type", params.type);
    if (params.search) q.set("search", params.search);
    return request<MemoryChunk[]>(`/memory/chunks?${q}`);
  },

  createMemoryChunk: (body: Partial<MemoryChunk>) =>
    request<MemoryChunk>("/memory/chunks", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  ingestFile: async (file: File, workspaceId: string) => {
    const form = new FormData();
    form.append("file", file);
    form.append("workspace_id", workspaceId);
    const res = await fetch(`${API_BASE}/memory/ingest`, { method: "POST", body: form });
    if (!res.ok) throw new Error("Ingest failed");
    return res.json() as Promise<{ status: string; chunk_count: number }>;
  },

  getDecisions: (workspaceId: string, status?: string) => {
    const q = new URLSearchParams({ workspace_id: workspaceId });
    if (status) q.set("status", status);
    return request<Decision[]>(`/decisions?${q}`);
  },

  patchDecision: (id: string, body: { status: string }) =>
    request<Decision>(`/decisions/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  getInbox: (workspaceId: string) =>
    request<InboxItem[]>(`/inbox?workspace_id=${workspaceId}`),

  patchInbox: (id: string, body: { status: string }) =>
    request<InboxItem>(`/inbox/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  getBoardSession: (id: string) => request<BoardSession>(`/board/sessions/${id}`),

  createBoardSession: (body: { question: string; workspace_id: string }) =>
    request<BoardSession>("/board/sessions", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  runResearch: (body: { entity_name: string; workspace_id: string }) =>
    request<ResearchJob>("/research/run", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  getResearchStatus: (jobId: string) =>
    request<ResearchJob>(`/research/status/${jobId}`),
};

export async function streamChat(
  message: string,
  onToken: (token: string) => void,
  onDone: (meta: {
    confidence?: number;
    tag?: string;
    evidence?: { source: string; snippet: string; url?: string; chunk_id?: string }[];
  }) => void
): Promise<void> {
  const res = await fetch(`${API_BASE}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!res.ok || !res.body) throw new Error("Stream failed");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      try {
        const data = JSON.parse(line.slice(6)) as {
          type: string;
          content?: string;
          confidence?: number;
          tag?: string;
          evidence?: { source: string; snippet: string; url?: string; chunk_id?: string }[];
        };
        if (data.type === "token" && data.content) onToken(data.content);
        if (data.type === "done") onDone(data);
      } catch {
        /* ignore parse errors */
      }
    }
  }
}
