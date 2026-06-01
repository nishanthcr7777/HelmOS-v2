"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { DecisionTimeline } from "./decision-timeline";
import { SynthesisPanel } from "@/components/board/synthesis-panel";
import { DecisionStatusBadge } from "@/components/shared/decision-status-badge";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";

export function DecisionDetailView() {
  const params = useParams();
  const workspaceId = params.workspaceId as string;
  const decisionId = params.decisionId as string;

  const { data: decision, isLoading } = useQuery({
    queryKey: ["decision", decisionId],
    queryFn: () => api.getDecision(decisionId),
  });

  if (isLoading) return <div className="p-6 text-muted-foreground">Loading decision…</div>;
  if (!decision) return <div className="p-6">Decision not found.</div>;

  const synthesis = {
    recommendation: decision.synthesis,
    verdict: decision.verdict,
    confidence: decision.confidence,
    evidence_score: decision.evidence_score,
    unknowns_level: decision.unknowns_level,
    risks: decision.risks,
    unknowns: decision.unknowns,
    assumptions: decision.assumptions,
    next_action: decision.next_action ?? "",
  };

  return (
    <div className="space-y-6 p-4 md:p-6">
      <Button variant="ghost" size="sm" className="-ml-2" asChild>
        <Link href={`/workspace/${workspaceId}/decisions`}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to decisions
        </Link>
      </Button>

      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-xl font-semibold">{decision.title}</h1>
        <DecisionStatusBadge status={decision.status} />
      </div>

      <div className="grid gap-8 lg:grid-cols-2">
        <section>
          <h2 className="mb-4 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Decision timeline
          </h2>
          {decision.timeline && decision.timeline.length > 0 ? (
            <DecisionTimeline events={decision.timeline} />
          ) : (
            <p className="text-sm text-muted-foreground">No timeline events recorded.</p>
          )}
        </section>
        <section>
          <SynthesisPanel synthesis={synthesis} />
          <Button className="mt-4" variant="secondary" asChild>
            <Link href={`/workspace/${workspaceId}/board?session=${decisionId.replace("decision-", "")}`}>
              Open board report
            </Link>
          </Button>
        </section>
      </div>
    </div>
  );
}
