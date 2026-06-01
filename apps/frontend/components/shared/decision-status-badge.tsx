import { Badge } from "@/components/ui/badge";
import type { DecisionStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

const styles: Record<DecisionStatus, string> = {
  open: "border-blue-500/40 text-blue-400",
  pursuing: "border-emerald-500/40 text-emerald-400",
  deferred: "border-amber-500/40 text-amber-400",
  rejected: "border-red-500/40 text-red-400",
  resolved: "border-muted-foreground/40 text-muted-foreground",
};

const labels: Record<DecisionStatus, string> = {
  open: "Open",
  pursuing: "Pursuing",
  deferred: "Deferred",
  rejected: "Rejected",
  resolved: "Resolved",
};

export function DecisionStatusBadge({ status }: { status: DecisionStatus }) {
  return (
    <Badge variant="outline" className={cn("text-xs capitalize", styles[status])}>
      {labels[status]}
    </Badge>
  );
}
