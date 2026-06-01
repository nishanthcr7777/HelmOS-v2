import { confidenceDescription, confidenceLabel } from "@/lib/confidence";
import { cn } from "@/lib/utils";

export function ConfidenceLabel({
  value,
  showDescription = false,
  className,
}: {
  value: number;
  showDescription?: boolean;
  className?: string;
}) {
  const label = confidenceLabel(value);
  const tone =
    label === "Low"
      ? "text-amber-600 dark:text-amber-400"
      : label === "Moderate"
        ? "text-blue-600 dark:text-blue-400"
        : "text-emerald-600 dark:text-emerald-400";

  return (
    <span className={cn("text-xs", className)}>
      <span className={cn("font-medium", tone)}>{label}</span>
      <span className="text-muted-foreground"> ({Math.round(value * 100)}%)</span>
      {showDescription && (
        <span className="block text-muted-foreground">{confidenceDescription(value)}</span>
      )}
    </span>
  );
}
