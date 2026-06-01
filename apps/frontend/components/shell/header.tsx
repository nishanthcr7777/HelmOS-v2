"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { useAppStore } from "@/lib/stores/app-store";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
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
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-border px-4">
      <div className="flex items-center gap-4">
        <Link href={`/workspace/${workspaceId}/chat`} className="text-lg font-bold tracking-tight">
          HELMOS
        </Link>
        <Select
          value={workspaceId}
          onValueChange={(id) => {
            setWorkspaceId(id);
            router.push(`/workspace/${id}/chat`);
          }}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Workspace" />
          </SelectTrigger>
          <SelectContent>
            {workspaces.map((w) => (
              <SelectItem key={w.id} value={w.id}>
                {w.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <Link href={`/workspace/${workspaceId}/inbox`} className="flex items-center gap-2">
        <span className="text-sm text-muted-foreground">Inbox</span>
        {openCount > 0 && (
          <Badge className="bg-primary text-primary-foreground">{openCount}</Badge>
        )}
      </Link>
    </header>
  );
}
