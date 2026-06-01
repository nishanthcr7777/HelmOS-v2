import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { VerdictBadge } from "@/components/shared/verdict-badge";
import { ConfidenceLabel } from "@/components/shared/confidence-label";
import type { BoardSynthesis } from "@/lib/types";

export function SynthesisPanel({ synthesis }: { synthesis: BoardSynthesis }) {
  return (
    <Card className="border-primary/30 bg-primary/5">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Synthesis</CardTitle>
          <VerdictBadge verdict={synthesis.verdict} />
        </div>
        <ConfidenceLabel value={synthesis.confidence} showDescription />
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        <p>{synthesis.recommendation}</p>
        {synthesis.next_action && (
          <p>
            <span className="font-medium">Next action: </span>
            {synthesis.next_action}
          </p>
        )}
        <div className="grid gap-3 md:grid-cols-3">
          <div>
            <p className="font-medium text-amber-400">Risks</p>
            <ul className="mt-1 list-inside list-disc text-muted-foreground">
              {synthesis.risks.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          </div>
          <div>
            <p className="font-medium">Unknowns</p>
            <ul className="mt-1 list-inside list-disc text-muted-foreground">
              {synthesis.unknowns.map((u, i) => (
                <li key={i}>{u}</li>
              ))}
            </ul>
          </div>
          <div>
            <p className="font-medium">Assumptions</p>
            <ul className="mt-1 list-inside list-disc text-muted-foreground">
              {synthesis.assumptions.map((a, i) => (
                <li key={i}>{a}</li>
              ))}
            </ul>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
