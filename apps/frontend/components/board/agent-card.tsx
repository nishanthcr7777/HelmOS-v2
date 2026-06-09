"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { VerdictBadge } from "@/components/shared/verdict-badge";
import { EvidenceAccordion } from "@/components/shared/evidence-accordion";
import { QualityBadge } from "@/components/shared/quality-badge";
import { ConfidenceBreakdown } from "@/components/shared/confidence-breakdown";
import type { AgentOutput } from "@/lib/types";
import { AGENT_LABELS, researchAgeLabel } from "@/lib/agent-meta";
import { ChevronDown, ChevronUp, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { confidencePercent } from "@/lib/confidence";
import type { BoardMode } from "@/lib/types";
import { asStringList, cn } from "@/lib/utils";

export function AgentCard({
  agent,
  boardMode = "decision",
  loading,
}: {
  agent: AgentOutput;
  boardMode?: BoardMode;
  loading?: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  const risks = asStringList(agent.risks);
  const unknowns = asStringList(agent.unknowns);
  const assumptions = asStringList(agent.key_assumptions);

  return (
    <Card className={cn("border-border/80", loading && "opacity-60")}>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <div>
            <CardTitle className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
              {AGENT_LABELS[agent.agent] ?? agent.agent}
            </CardTitle>
            <p className="mt-1 text-xs tabular-nums text-muted-foreground">
              Influence {confidencePercent(agent.influence_weight, 0.1)}%
            </p>
          </div>
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
          ) : (
            <VerdictBadge verdict={agent.verdict} boardMode={boardMode} />
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <ConfidenceBreakdown
          confidence={agent.confidence}
          evidenceScore={agent.evidence_score}
          unknownsLevel={unknowns.length >= 2 ? "high" : unknowns.length === 1 ? "moderate" : "low"}
        />
        <div className="flex flex-wrap gap-3 border-y border-border py-2 text-xs">
          <QualityBadge level={agent.evidence_quality} label="Evidence quality" />
          <span className="text-muted-foreground">
            Research age: <span className="text-foreground">{researchAgeLabel(agent.research_age_days)}</span>
          </span>
        </div>
        <p className="line-clamp-2 text-muted-foreground">{agent.recommendation}</p>
        {risks.length > 0 && (
          <p className="text-xs">
            <span className="font-medium text-amber-600 dark:text-amber-400">Risks: </span>
            {risks.slice(0, 2).join("; ")}
          </p>
        )}
        <Button variant="ghost" size="sm" className="h-7 px-0" onClick={() => setExpanded(!expanded)}>
          {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          Full report
        </Button>
        {expanded && (
          <div className="space-y-2 border-t border-border pt-2">
            <p>{agent.recommendation}</p>
            <p className="text-xs text-muted-foreground">{agent.suggested_next_action}</p>
            {assumptions.length > 0 && (
              <div>
                <p className="text-xs font-medium uppercase text-muted-foreground">Assumptions</p>
                <ul className="mt-1 list-inside list-disc text-xs text-muted-foreground">
                  {assumptions.map((a, i) => (
                    <li key={i}>{a}</li>
                  ))}
                </ul>
              </div>
            )}
            <EvidenceAccordion evidence={agent.evidence_used} />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
