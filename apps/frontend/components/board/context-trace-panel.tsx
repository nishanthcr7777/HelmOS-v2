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
}: {
  label: string;
  count: number;
  detail?: string;
  warn?: boolean;
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
            ok && "text-emerald-600 dark:text-emerald-400"
          )}
        >
          {ok ? "Yes" : "No"} · {count}
        </span>
        {detail && <p className="mt-0.5 text-xs text-muted-foreground">{detail}</p>}
      </div>
    </div>
  );
}

export function ContextTracePanel({ trace }: { trace?: ContextTrace }) {
  const [open, setOpen] = useState(false);
  const [showIds, setShowIds] = useState(false);

  if (!trace) return null;

  const mem = trace.memory;
  const memoryDetail = mem
    ? `vector ${mem.vector_hits} · text ${mem.text_hits}${
        mem.used_text_fallback ? " · text fallback" : ""
      }${mem.used_recent_fallback ? " · recent fallback" : ""}`
    : undefined;

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
          {trace.agent_context_chars?.toLocaleString() ?? 0} chars · ~
          {trace.agent_context_tokens?.toLocaleString() ?? 0} tokens
        </p>
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
