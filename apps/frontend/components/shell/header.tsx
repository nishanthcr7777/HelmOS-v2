"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { useAppStore } from "@/lib/stores/app-store";
import { FounderStateBar } from "./founder-state";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { ThemeToggle } from "@/components/theme/theme-toggle";
import { useParams, useRouter } from "next/navigation";

export function Header() {
  const router = useRouter();
  const params = useParams();
  const storedWorkspaceId = useAppStore((s) => s.workspaceId);
  const setWorkspaceId = useAppStore((s) => s.setWorkspaceId);
  const workspaceId = (params?.workspaceId as string) ?? storedWorkspaceId;

  const { data: workspaces = [] } = useQuery({
    queryKey: ["workspaces"],
    queryFn: () => api.getWorkspaces(),
  });

  const { data: inbox = [] } = useQuery({
    queryKey: ["inbox", workspaceId],
    queryFn: () => api.getInbox(workspaceId),
    enabled: !!workspaceId,
  });

  const openCount = inbox.filter((i) => i.status === "open").length;

  return (
    <header className="flex h-14 shrink-0 items-center justify-between gap-4 border-b border-border bg-card/30 px-4">
      <div className="flex min-w-0 items-center gap-4">
        <Link
          href={`/workspace/${workspaceId}/dashboard`}
          className="shrink-0 text-lg font-bold tracking-tight"
        >
          HELMOS
        </Link>
        <Select
          value={workspaceId}
          onValueChange={(id) => {
            setWorkspaceId(id);
            router.push(`/workspace/${id}/dashboard`);
          }}
        >
          <SelectTrigger className="w-[160px] border-border/80">
            <SelectValue placeholder="Environment" />
          </SelectTrigger>
          <SelectContent>
            {workspaces.map((w) => (
              <SelectItem key={w.id} value={w.id}>
                {w.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <FounderStateBar />
      </div>
      <div className="flex shrink-0 items-center gap-3">
        <Link href={`/workspace/${workspaceId}/inbox`} className="flex items-center gap-2 text-sm">
          <span className="text-muted-foreground">Attention</span>
          {openCount > 0 && (
            <Badge className="bg-amber-500 text-white tabular-nums dark:bg-amber-500/90 dark:text-primary-foreground">
              {openCount}
            </Badge>
          )}
        </Link>
        <ThemeToggle />
      </div>
    </header>
  );
}
