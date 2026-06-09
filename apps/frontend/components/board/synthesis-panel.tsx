import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { VerdictBadge } from "@/components/shared/verdict-badge";
import { ConfidenceBreakdown } from "@/components/shared/confidence-breakdown";
import type { BoardSynthesis } from "@/lib/types";
import { asStringList } from "@/lib/utils";

export function SynthesisPanel({ synthesis }: { synthesis: BoardSynthesis }) {
  const risks = asStringList(synthesis.risks);
  const unknowns = asStringList(synthesis.unknowns);
  const assumptions = asStringList(synthesis.assumptions);

  return (
    <Card className="border-primary/30 bg-primary/5">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm uppercase tracking-wide">Synthesis report</CardTitle>
          <VerdictBadge verdict={synthesis.verdict} />
        </div>
        <div className="mt-3 max-w-xs">
          <ConfidenceBreakdown
            confidence={synthesis.confidence}
            evidenceScore={synthesis.evidence_score}
            unknownsLevel={synthesis.unknowns_level}
          />
        </div>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        <p>{synthesis.recommendation}</p>
        {synthesis.next_action && (
          <p className="rounded-md border border-border bg-background/50 p-3">
            <span className="text-xs font-semibold uppercase text-muted-foreground">
              Recommended next action
            </span>
            <span className="mt-1 block">{synthesis.next_action}</span>
          </p>
        )}
        <div className="grid gap-3 md:grid-cols-3">
          <div>
            <p className="text-xs font-semibold uppercase text-amber-600 dark:text-amber-400">Risks</p>
            <ul className="mt-1 list-inside list-disc text-muted-foreground">
              {risks.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase text-muted-foreground">Unknowns</p>
            <ul className="mt-1 list-inside list-disc text-muted-foreground">
              {unknowns.map((u, i) => (
                <li key={i}>{u}</li>
              ))}
            </ul>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase text-muted-foreground">Assumptions</p>
            <ul className="mt-1 list-inside list-disc text-muted-foreground">
              {assumptions.map((a, i) => (
                <li key={i}>{a}</li>
              ))}
            </ul>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
