import { http, HttpResponse, delay } from "msw";
import { API_BASE, MOCK_LATENCY_MS } from "@/lib/api/config";
import {
  boardSessions,
  chatStreamResponse,
  decisions,
  inboxItems,
  memoryChunks,
  projects,
  researchJobs,
  workspaces,
} from "../fixtures/data";
import type { MemoryChunk, ResearchJob } from "@/lib/types";

const base = API_BASE;

let chunksStore = [...memoryChunks];
let inboxStore = [...inboxItems];
let researchStore = [...researchJobs];

function sseData(data: object): string {
  return `data: ${JSON.stringify(data)}\n\n`;
}

export const handlers = [
  http.get(`${base}/workspaces`, async () => {
    await delay(MOCK_LATENCY_MS);
    return HttpResponse.json(workspaces);
  }),

  http.get(`${base}/workspaces/:id/projects`, async ({ params }) => {
    await delay(MOCK_LATENCY_MS);
    const list = projects.filter((p) => p.workspace_id === params.id);
    return HttpResponse.json(list);
  }),

  http.get(`${base}/memory/chunks`, async ({ request }) => {
    await delay(MOCK_LATENCY_MS);
    const url = new URL(request.url);
    const workspaceId = url.searchParams.get("workspace_id");
    const type = url.searchParams.get("type");
    const search = url.searchParams.get("search")?.toLowerCase();
    let list = chunksStore.filter((c) => !workspaceId || c.workspace_id === workspaceId);
    if (type) list = list.filter((c) => c.chunk_type === type);
    if (search) list = list.filter((c) => c.content.toLowerCase().includes(search));
    return HttpResponse.json(list);
  }),

  http.post(`${base}/memory/chunks`, async ({ request }) => {
    await delay(MOCK_LATENCY_MS);
    const body = (await request.json()) as Partial<MemoryChunk>;
    const chunk: MemoryChunk = {
      id: `chunk-new-${Date.now()}`,
      workspace_id: body.workspace_id ?? "clawback-labs",
      project_id: body.project_id,
      chunk_type: body.chunk_type ?? "strategy_note",
      content: body.content ?? "",
      created_at: new Date().toISOString(),
    };
    chunksStore = [chunk, ...chunksStore];
    return HttpResponse.json(chunk, { status: 201 });
  }),

  http.post(`${base}/memory/ingest`, async () => {
    await delay(800);
    return HttpResponse.json({ status: "indexed", chunk_count: 12 });
  }),

  http.get(`${base}/decisions`, async ({ request }) => {
    await delay(MOCK_LATENCY_MS);
    const url = new URL(request.url);
    const workspaceId = url.searchParams.get("workspace_id");
    const status = url.searchParams.get("status");
    let list = decisions.filter((d) => !workspaceId || d.workspace_id === workspaceId);
    if (status) list = list.filter((d) => d.status === status);
    return HttpResponse.json(list);
  }),

  http.get(`${base}/decisions/:id`, async ({ params }) => {
    await delay(MOCK_LATENCY_MS);
    const d = decisions.find((x) => x.id === params.id);
    if (!d) return new HttpResponse(null, { status: 404 });
    return HttpResponse.json(d);
  }),

  http.patch(`${base}/decisions/:id`, async ({ params, request }) => {
    await delay(MOCK_LATENCY_MS);
    const body = (await request.json()) as { status?: string };
    const d = decisions.find((x) => x.id === params.id);
    if (!d) return new HttpResponse(null, { status: 404 });
    if (body.status) d.status = body.status as typeof d.status;
    return HttpResponse.json(d);
  }),

  http.get(`${base}/inbox`, async ({ request }) => {
    await delay(MOCK_LATENCY_MS);
    const url = new URL(request.url);
    const workspaceId = url.searchParams.get("workspace_id");
    const list = inboxStore
      .filter((i) => i.status === "open")
      .filter((i) => !workspaceId || i.workspace_id === workspaceId)
      .sort((a, b) => {
        const order = { high: 0, medium: 1, low: 2 };
        return order[a.priority] - order[b.priority];
      });
    return HttpResponse.json(list);
  }),

  http.patch(`${base}/inbox/:id`, async ({ params, request }) => {
    await delay(MOCK_LATENCY_MS);
    const body = (await request.json()) as { status?: string };
    const item = inboxStore.find((i) => i.id === params.id);
    if (!item) return new HttpResponse(null, { status: 404 });
    if (body.status) item.status = body.status as typeof item.status;
    return HttpResponse.json(item);
  }),

  http.get(`${base}/board/sessions/:id`, async ({ params }) => {
    await delay(MOCK_LATENCY_MS);
    const s = boardSessions.find((x) => x.id === params.id);
    if (!s) return new HttpResponse(null, { status: 404 });
    return HttpResponse.json(s);
  }),

  http.post(`${base}/board/sessions`, async ({ request }) => {
    await delay(MOCK_LATENCY_MS);
    const body = (await request.json()) as { question: string; workspace_id: string };
    const session = boardSessions[0];
    return HttpResponse.json({
      ...session,
      id: `session-${Date.now()}`,
      question: body.question,
      workspace_id: body.workspace_id,
    });
  }),

  http.post(`${base}/research/run`, async ({ request }) => {
    const body = (await request.json()) as { entity_name: string; workspace_id: string };
    const job: ResearchJob = {
      id: `research-${Date.now()}`,
      workspace_id: body.workspace_id,
      entity_name: body.entity_name,
      queries: [`${body.entity_name} overview`, `${body.entity_name} compliance news`],
      step: "querying",
      sources: [],
      created_at: new Date().toISOString(),
    };
    researchStore = [job, ...researchStore];
    return HttpResponse.json(job);
  }),

  http.get(`${base}/research/status/:jobId`, async ({ params }) => {
    const job = researchStore.find((j) => j.id === params.jobId);
    if (!job) return new HttpResponse(null, { status: 404 });
    const steps: ResearchJob["step"][] = ["querying", "searching", "extracting", "summarizing", "done"];
    const idx = Math.min(
      steps.length - 1,
      Math.floor((Date.now() - new Date(job.created_at).getTime()) / 1200)
    );
    const updated = {
      ...job,
      step: steps[idx],
      sources: idx >= 4 ? researchJobs[0].sources : job.sources,
    };
    const i = researchStore.findIndex((j) => j.id === job.id);
    if (i >= 0) researchStore[i] = updated;
    return HttpResponse.json(updated);
  }),

  http.post(`${base}/chat/stream`, async () => {
    const tokens = chatStreamResponse.split(/(?=\s)/);
    const stream = new ReadableStream({
      async start(controller) {
        const encoder = new TextEncoder();
        for (const token of tokens) {
          await delay(25);
          controller.enqueue(encoder.encode(sseData({ type: "token", content: token })));
        }
        controller.enqueue(
          encoder.encode(
            sseData({
              type: "done",
              confidence: 0.63,
              tag: "plain",
              evidence: [
                {
                  source: "memory_chunk",
                  snippet: "Acme Corp — legacy payroll, compliance team ~8",
                  chunk_id: "chunk-clawback-labs-1",
                },
                {
                  source: "tavily_search",
                  snippet: "No public clawback litigation signals",
                  url: "https://example.com/news",
                },
              ],
            })
          )
        );
        controller.close();
      },
    });
    return new HttpResponse(stream, {
      headers: { "Content-Type": "text/event-stream" },
    });
  }),
];
