"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { qualityLabel } from "@/lib/quality";
import { cn } from "@/lib/utils";

export function FounderStateBar() {
  const { data } = useQuery({
    queryKey: ["founder-state"],
    queryFn: () => api.getFounderState(),
  });

  if (!data) return null;

  const items = [
    { label: "Decision load", value: qualityLabel(data.decision_load) },
    { label: "Blocked", value: String(data.blocked_items) },
    { label: "Open decisions", value: String(data.open_decisions) },
    { label: "Research needed", value: String(data.research_needed) },
  ];

  return (
    <div className="hidden items-center gap-4 border-l border-border pl-4 lg:flex">
      <span className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
        Founder state
      </span>
      {items.map((item) => (
        <div key={item.label} className="text-xs">
          <span className="text-muted-foreground">{item.label}: </span>
          <span
            className={cn(
              "font-medium tabular-nums",
              item.label === "Blocked" && Number(item.value) > 0 && "text-amber-400"
            )}
          >
            {item.value}
          </span>
        </div>
      ))}
    </div>
  );
}
