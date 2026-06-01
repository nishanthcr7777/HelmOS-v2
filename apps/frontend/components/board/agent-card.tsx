"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { VerdictBadge } from "@/components/shared/verdict-badge";
import { ConfidenceLabel } from "@/components/shared/confidence-label";
import { EvidenceAccordion } from "@/components/shared/evidence-accordion";
import type { AgentOutput } from "@/lib/types";
import { ChevronDown, ChevronUp, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const agentLabels: Record<string, string> = {
  cto: "CTO",
  operator: "Operator",
  skeptic: "Skeptic",
  researcher: "Researcher",
  sales_strategist: "Sales Strategist",
};

export function AgentCard({
  agent,
  loading,
}: {
  agent: AgentOutput;
  loading?: boolean;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <Card className={cn(loading && "opacity-60")}>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-base">{agentLabels[agent.agent] ?? agent.agent}</CardTitle>
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
          ) : (
            <VerdictBadge verdict={agent.verdict} />
          )}
        </div>
        <ConfidenceLabel value={agent.confidence} />
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        <p className="line-clamp-2 text-muted-foreground">{agent.recommendation}</p>
        {agent.risks.length > 0 && (
          <p>
            <span className="font-medium text-amber-400">Risks: </span>
            {agent.risks.slice(0, 2).join("; ")}
          </p>
        )}
        <Button variant="ghost" size="sm" className="h-7 px-0" onClick={() => setExpanded(!expanded)}>
          {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          {expanded ? "Less" : "More"} details
        </Button>
        {expanded && (
          <div className="space-y-2 border-t border-border pt-2">
            <p>{agent.recommendation}</p>
            <p className="text-xs text-muted-foreground">{agent.suggested_next_action}</p>
            {agent.key_assumptions.length > 0 && (
              <div>
                <p className="font-medium">Assumptions</p>
                <ul className="list-inside list-disc text-muted-foreground">
                  {agent.key_assumptions.map((a, i) => (
                    <li key={i}>{a}</li>
                  ))}
                </ul>
              </div>
            )}
            {agent.unknowns.length > 0 && (
              <div>
                <p className="font-medium">Unknowns</p>
                <ul className="list-inside list-disc text-muted-foreground">
                  {agent.unknowns.map((u, i) => (
                    <li key={i}>{u}</li>
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
