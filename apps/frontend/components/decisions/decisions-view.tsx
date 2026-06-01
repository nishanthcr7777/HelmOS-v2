"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { VerdictBadge } from "@/components/shared/verdict-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { Decision } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import { Download } from "lucide-react";

function exportMarkdown(decisions: Decision[]): string {
  return decisions
    .map(
      (d) => `## ${d.question}

**Verdict:** ${d.verdict} · **Confidence:** ${Math.round(d.confidence * 100)}% · **Status:** ${d.status}

${d.synthesis}

**Risks:** ${d.risks.join("; ")}

**Next action:** ${d.next_action ?? "—"}

*${formatDate(d.created_at)}*
`
    )
    .join("\n---\n\n");
}

export function DecisionsView() {
  const params = useParams();
  const workspaceId = params.workspaceId as string;
  const [statusFilter, setStatusFilter] = useState("");

  const { data: decisions = [], isLoading } = useQuery({
    queryKey: ["decisions", workspaceId, statusFilter],
    queryFn: () => api.getDecisions(workspaceId, statusFilter || undefined),
  });

  function handleExport() {
    const md = exportMarkdown(decisions);
    const blob = new Blob([md], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `helmos-decisions-${workspaceId}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-4 p-4 md:p-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-xl font-semibold">Decision Log</h1>
        <Button variant="outline" onClick={handleExport} disabled={!decisions.length}>
          <Download className="mr-2 h-4 w-4" />
          Export markdown
        </Button>
      </div>

      <div className="flex gap-2">
        {["", "open", "resolved", "deferred"].map((s) => (
          <Button
            key={s || "all"}
            size="sm"
            variant={statusFilter === s ? "default" : "outline"}
            onClick={() => setStatusFilter(s)}
          >
            {s || "All"}
          </Button>
        ))}
      </div>

      {isLoading ? (
        <p className="text-muted-foreground">Loading…</p>
      ) : decisions.length === 0 ? (
        <p className="text-muted-foreground">No decisions recorded yet.</p>
      ) : (
        <ul className="space-y-3">
          {decisions.map((d) => (
            <Card key={d.id}>
              <CardContent className="pt-4">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <p className="font-medium">{d.question}</p>
                  <VerdictBadge verdict={d.verdict} />
                </div>
                <p className="mt-2 line-clamp-2 text-sm text-muted-foreground">{d.synthesis}</p>
                <p className="mt-2 text-xs text-muted-foreground">
                  {d.status} · {formatDate(d.created_at)}
                </p>
              </CardContent>
            </Card>
          ))}
        </ul>
      )}
    </div>
  );
}
