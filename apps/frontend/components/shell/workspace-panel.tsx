"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { useParams } from "next/navigation";

export function WorkspacePanel() {
  const params = useParams();
  const workspaceId = params?.workspaceId as string;

  const { data: profile } = useQuery({
    queryKey: ["workspace-profile", workspaceId],
    queryFn: () => api.getWorkspaceProfile(workspaceId),
    enabled: !!workspaceId,
  });

  if (!profile) return null;

  return (
    <div className="shrink-0 border-b border-border bg-card/40 px-4 py-3">
      <div className="flex flex-wrap gap-6">
        {profile.metrics.map((m) => (
          <div key={m.label} className="min-w-[100px]">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              {m.label}
            </p>
            <p className="mt-0.5 text-sm font-medium tabular-nums">{m.value}</p>
          </div>
        ))}
      </div>
      <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
        {profile.context_lines.map((line, i) => (
          <li key={i}>· {line}</li>
        ))}
      </ul>
    </div>
  );
}
