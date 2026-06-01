import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { Verdict } from "@/lib/types";

const verdictStyles: Record<Verdict, string> = {
  go: "bg-verdict-go/20 text-verdict-go border-verdict-go/40",
  no_go: "bg-verdict-no_go/20 text-verdict-no_go border-verdict-no_go/40",
  conditional: "bg-verdict-conditional/20 text-verdict-conditional border-verdict-conditional/40",
  lean_for: "bg-verdict-lean_for/20 text-verdict-lean_for border-verdict-lean_for/40",
  lean_against: "bg-verdict-lean_against/20 text-verdict-lean_against border-verdict-lean_against/40",
  needs_research: "bg-verdict-needs_research/20 text-verdict-needs_research border-verdict-needs_research/40",
};

const labels: Record<Verdict, string> = {
  go: "Go",
  no_go: "No Go",
  conditional: "Conditional",
  lean_for: "Lean For",
  lean_against: "Lean Against",
  needs_research: "Needs Research",
};

export function VerdictBadge({ verdict, className }: { verdict: Verdict; className?: string }) {
  return (
    <Badge variant="outline" className={cn(verdictStyles[verdict], className)}>
      {labels[verdict]}
    </Badge>
  );
}
