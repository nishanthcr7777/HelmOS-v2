import { confidencePercent } from "@/lib/confidence";
import { UnknownsBadge } from "./quality-badge";
import type { UnknownsLevel } from "@/lib/types";

export function ConfidenceBreakdown({
  confidence,
  evidenceScore,
  unknownsLevel,
}: {
  confidence: unknown;
  evidenceScore: unknown;
  unknownsLevel: UnknownsLevel;
}) {
  return (
    <div className="grid gap-1 text-xs tabular-nums">
      <div className="flex justify-between gap-4">
        <span className="text-muted-foreground">Confidence</span>
        <span className="font-medium">{confidencePercent(confidence)}%</span>
      </div>
      <div className="flex justify-between gap-4">
        <span className="text-muted-foreground">Evidence</span>
        <span className="font-medium text-emerald-600 dark:text-emerald-400">
          {confidencePercent(evidenceScore)}%
        </span>
      </div>
      <div className="flex justify-between gap-4">
        <UnknownsBadge level={unknownsLevel} />
      </div>
    </div>
  );
}
