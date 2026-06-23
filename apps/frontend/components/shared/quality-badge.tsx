import { qualityColor, qualityLabel, unknownsColor, unknownsLabel } from "@/lib/quality";
import type { QualityLevel, UnknownsLevel } from "@/lib/types";
import { cn } from "@/lib/utils";

export function QualityBadge({ level, label }: { level: QualityLevel; label?: string }) {
  return (
    <span className={cn("text-xs font-medium tabular-nums", qualityColor(level))}>
      {label ?? "Quality"}: {qualityLabel(level)}
    </span>
  );
}

export function UnknownsBadge({ level }: { level: UnknownsLevel }) {
  return (
    <span className="text-xs font-medium tabular-nums text-muted-foreground">
      Unknowns: <span className={cn(unknownsColor(level))}>{unknownsLabel(level)}</span>
    </span>
  );
}
