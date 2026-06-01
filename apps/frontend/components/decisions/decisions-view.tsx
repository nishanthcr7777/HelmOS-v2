"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { VerdictBadge } from "@/components/shared/verdict-badge";
import { DecisionStatusBadge } from "@/components/shared/decision-status-badge";
import { SectionHeader } from "@/components/shared/section-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { Decision, DecisionStatus } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import { Download } from "lucide-react";
import { workspaces } from "@/mocks/fixtures/data";

const statusFilters: (DecisionStatus | "")[] = ["", "open", "pursuing", "deferred", "rejected", "resolved"];

function exportMarkdown(decisions: Decision[]): string {
  return decisions
    .map(
      (d) => `## ${d.title}

**Status:** ${d.status} · **Verdict:** ${d.verdict}
**Confidence:** ${Math.round(d.confidence * 100)}% · **Evidence:** ${Math.round(d.evidence_score * 100)}%
**Risk:** ${d.risk_level} · **Unknowns:** ${d.unknowns_level}

${d.synthesis}

*${formatDate(d.updated_at)}*
`
    )
    .join("\n---\n\n");
}

export function DecisionsView() {
  const params = useParams();
  const workspaceId = params.workspaceId as string;
  const [statusFilter, setStatusFilter] = useState<DecisionStatus | "">("");

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

  const wsName = (id: string) => workspaces.find((w) => w.id === id)?.name ?? id;

  return (
    <div className="space-y-4 p-4 md:p-6">
      <SectionHeader
        title="Decision management"
        subtitle="Track status, quality, and outcomes — not just history"
        action={
          <Button variant="outline" size="sm" onClick={handleExport} disabled={!decisions.length}>
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
        }
      />

      <div className="flex flex-wrap gap-2">
        {statusFilters.map((s) => (
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
        <p className="text-muted-foreground">No decisions match this filter.</p>
      ) : (
        <ul className="space-y-3">
          {decisions.map((d) => (
            <li key={d.id}>
              <Link href={`/workspace/${workspaceId}/decisions/${d.id}`}>
                <Card className="transition-colors hover:border-primary/40">
                  <CardContent className="pt-4">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <p className="font-medium">{d.title}</p>
                      <div className="flex gap-2">
                        <DecisionStatusBadge status={d.status} />
                        <VerdictBadge verdict={d.verdict} />
                      </div>
                    </div>
                    <p className="mt-2 line-clamp-2 text-sm text-muted-foreground">{d.synthesis}</p>
                    <div className="mt-3 grid grid-cols-2 gap-2 border-t border-border pt-3 text-xs sm:grid-cols-4">
                      <div>
                        <span className="text-muted-foreground">Confidence</span>
                        <p className="font-medium tabular-nums">{Math.round(d.confidence * 100)}%</p>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Risk</span>
                        <p className="font-medium capitalize">{d.risk_level}</p>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Unknowns</span>
                        <p className="font-medium capitalize">{d.unknowns_level}</p>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Workspace</span>
                        <p className="font-medium">{wsName(d.workspace_id)}</p>
                      </div>
                    </div>
                    <p className="mt-2 text-xs text-muted-foreground">
                      Updated {formatDate(d.updated_at)}
                    </p>
                  </CardContent>
                </Card>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
