import { UnknownsBadge } from "./quality-badge";
import type { UnknownsLevel } from "@/lib/types";

export function ConfidenceBreakdown({
  confidence,
  evidenceScore,
  unknownsLevel,
}: {
  confidence: number;
  evidenceScore: number;
  unknownsLevel: UnknownsLevel;
}) {
  return (
    <div className="grid gap-1 text-xs tabular-nums">
      <div className="flex justify-between gap-4">
        <span className="text-muted-foreground">Confidence</span>
        <span className="font-medium">{Math.round(confidence * 100)}%</span>
      </div>
      <div className="flex justify-between gap-4">
        <span className="text-muted-foreground">Evidence</span>
        <span className="font-medium text-emerald-400">{Math.round(evidenceScore * 100)}%</span>
      </div>
      <div className="flex justify-between gap-4">
        <UnknownsBadge level={unknownsLevel} />
      </div>
    </div>
  );
}
