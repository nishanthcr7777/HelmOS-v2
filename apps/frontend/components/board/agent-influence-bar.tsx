import { AGENT_LABELS } from "@/lib/agent-meta";
import type { AgentOutput } from "@/lib/types";

export function AgentInfluenceBar({ agents }: { agents: AgentOutput[] }) {
  const sorted = [...agents].sort((a, b) => b.influence_weight - a.influence_weight);

  return (
    <div className="rounded-lg border border-border bg-card/50 p-4">
      <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        Agent influence weight
      </p>
      <div className="space-y-2">
        {sorted.map((a) => (
          <div key={a.agent} className="flex items-center gap-3 text-sm">
            <span className="w-24 shrink-0 text-muted-foreground">
              {AGENT_LABELS[a.agent] ?? a.agent}
            </span>
            <div className="h-2 flex-1 overflow-hidden rounded-full bg-secondary">
              <div
                className="h-full rounded-full bg-primary"
                style={{ width: `${a.influence_weight * 100}%` }}
              />
            </div>
            <span className="w-10 shrink-0 text-right tabular-nums text-muted-foreground">
              {Math.round(a.influence_weight * 100)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
