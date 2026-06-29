"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { ContextTrace } from "@/lib/types";
import { cn } from "@/lib/utils";
import { ChevronDown, ChevronUp } from "lucide-react";

function StatusRow({
  label,
  count,
  detail,
  warn,
  neutral,
}: {
  label: string;
  count: number;
  detail?: string;
  warn?: boolean;
  neutral?: boolean;
}) {
  const ok = count > 0;
  return (
    <div className="flex items-start justify-between gap-4 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <div className="text-right">
        <span
          className={cn(
            "font-medium tabular-nums",
            warn && !ok && "text-destructive",
            !neutral && ok && "text-emerald-600 dark:text-emerald-400"
          )}
        >
          {neutral ? count : ok ? "Yes" : "No"} · {count}
        </span>
        {detail && <p className="mt-0.5 text-xs text-muted-foreground">{detail}</p>}
      </div>
    </div>
  );
}

export function ContextTracePanel({ trace }: { trace?: ContextTrace }) {
  const [open, setOpen] = useState(false);
  const [showIds, setShowIds] = useState(false);
  const [showResearcherRaw, setShowResearcherRaw] = useState(false);

  if (!trace) return null;

  const mem = trace.memory;
  const research = trace.research;
  const tavilyHits = research?.tavily_hits ?? 0;
  const relevantHits = research?.relevant_hits ?? 0;
  const passed = research?.passed_to_researcher ?? trace.research_sources_count ?? 0;
  const researchTokens = research?.research_tokens ?? 0;

  const memoryDetail = mem
    ? `vector ${mem.vector_hits} · text ${mem.text_hits}${
        mem.used_text_fallback ? " · text fallback" : ""
      }${mem.used_recent_fallback ? " · recent fallback" : ""}`
    : undefined;

  const researchDetail = research?.skipped_reason
    ? `Skipped: ${research.skipped_reason}`
    : `Tavily ${tavilyHits} · Relevant ${relevantHits} · Passed ${passed} · ~${researchTokens} tokens`;

  return (
    <Card className="border-dashed border-border/80 bg-muted/20">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">Context injected</CardTitle>
          <Button variant="ghost" size="sm" className="h-7" onClick={() => setOpen(!open)}>
            {open ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            {open ? "Hide" : "Show"} debug
          </Button>
        </div>
        <p className="text-xs text-muted-foreground">
          Memory: {mem?.retrieved_chunks_count ?? 0} · Entities: {trace.entities_count ?? 0} ·
          Decisions: {trace.decisions_injected ?? 0} · Sessions:{" "}
          {trace.board_sessions_injected ?? 0} · Research passed: {passed} · ~
          {trace.agent_context_tokens?.toLocaleString() ?? 0} agent context tokens
        </p>
        <p className="text-xs text-muted-foreground">{researchDetail}</p>
      </CardHeader>
      {open && (
        <CardContent className="space-y-3 pt-0">
          <StatusRow
            label="Memory retrieved?"
            count={mem?.retrieved_chunks_count ?? 0}
            detail={memoryDetail}
            warn
          />
          <StatusRow label="Entities retrieved?" count={trace.entities_count ?? 0} warn />
          <StatusRow label="Decisions retrieved?" count={trace.decisions_injected ?? 0} warn />
          <StatusRow
            label="Prior board sessions?"
            count={trace.board_sessions_injected ?? 0}
          />
          <StatusRow label="Workspace profile?" count={trace.profile_lines_count ?? 0} />
          <StatusRow label="Beliefs (system prompt)" count={trace.beliefs_count ?? 0} />

          <div className="border-t border-border pt-3">
            <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Research pipeline
            </p>
            <StatusRow label="Tavily hits" count={tavilyHits} neutral />
            <StatusRow
              label="Relevant hits"
              count={relevantHits}
              warn
              detail={research?.retrieval_case ? `Case: ${research.retrieval_case}` : undefined}
            />
            <StatusRow label="Passed to Researcher" count={passed} warn />
            <StatusRow label="Research tokens" count={researchTokens} neutral />
            {research?.queries && research.queries.length > 0 && (
              <div className="mt-2">
                <p className="text-xs text-muted-foreground">Generated queries</p>
                <ul className="mt-1 list-inside list-disc text-xs text-muted-foreground">
                  {research.queries.map((q, i) => (
                    <li key={i}>{q}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {trace.researcher && (
            <div className="border-t border-border pt-3">
              <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Researcher debug
              </p>
              {trace.researcher.model && (
                <p className="text-xs text-muted-foreground">Model: {trace.researcher.model}</p>
              )}
              {trace.researcher.parse_error && (
                <p className="text-xs text-destructive">Parse error: {trace.researcher.parse_error}</p>
              )}
              <Button
                variant="ghost"
                size="sm"
                className="mt-1 h-7 px-0 text-xs"
                onClick={() => setShowResearcherRaw(!showResearcherRaw)}
              >
                {showResearcherRaw ? "Hide" : "Show"} raw LLM response
              </Button>
              {showResearcherRaw && trace.researcher.raw_response && (
                <pre className="mt-1 max-h-40 overflow-auto rounded border border-border bg-background p-2 font-mono text-xs">
                  {trace.researcher.raw_response}
                </pre>
              )}
            </div>
          )}

          {mem?.chunk_ids && mem.chunk_ids.length > 0 && (
            <div>
              <Button
                variant="ghost"
                size="sm"
                className="h-7 px-0 text-xs"
                onClick={() => setShowIds(!showIds)}
              >
                {showIds ? "Hide" : "Show"} chunk IDs
              </Button>
              {showIds && (
                <ul className="mt-1 max-h-24 overflow-auto font-mono text-xs text-muted-foreground">
                  {mem.chunk_ids.map((id) => (
                    <li key={id}>{id}</li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
}
