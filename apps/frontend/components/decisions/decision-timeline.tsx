import type { DecisionTimelineEvent } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import { cn } from "@/lib/utils";

const stageOrder: DecisionTimelineEvent["stage"][] = [
  "question",
  "research",
  "board",
  "decision",
  "outcome",
];

export function DecisionTimeline({ events }: { events: DecisionTimelineEvent[] }) {
  const sorted = [...events].sort(
    (a, b) => stageOrder.indexOf(a.stage) - stageOrder.indexOf(b.stage)
  );

  return (
    <ol className="relative space-y-0 border-l border-border pl-6">
      {sorted.map((event, i) => (
        <li key={event.id} className="pb-8 last:pb-0">
          <span
            className={cn(
              "absolute -left-[5px] mt-1.5 h-2.5 w-2.5 rounded-full border-2 border-background",
              i === sorted.length - 1 ? "bg-primary" : "bg-muted-foreground"
            )}
          />
          <p className="text-xs font-semibold uppercase tracking-wider text-primary">
            {event.label}
          </p>
          <p className="mt-1 text-sm">{event.summary}</p>
          <p className="mt-1 text-xs text-muted-foreground">{formatDate(event.at)}</p>
        </li>
      ))}
    </ol>
  );
}
