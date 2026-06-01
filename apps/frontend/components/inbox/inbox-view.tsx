"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { InboxItem, InboxItemType } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import { cn } from "@/lib/utils";

const typeColors: Record<InboxItemType, string> = {
  unresolved_decision: "border-l-inbox-decision",
  risky_assumption: "border-l-inbox-assumption",
  blocked_action: "border-l-inbox-blocked",
  opportunity: "border-l-inbox-opportunity",
  conflict: "border-l-inbox-conflict",
};

const priorityOrder = { high: 0, medium: 1, low: 2 };

export function InboxView() {
  const params = useParams();
  const workspaceId = params.workspaceId as string;
  const queryClient = useQueryClient();

  const { data: items = [], isLoading } = useQuery({
    queryKey: ["inbox", workspaceId],
    queryFn: () => api.getInbox(workspaceId),
  });

  const patch = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      api.patchInbox(id, { status }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["inbox"] }),
  });

  const sorted = [...items].sort(
    (a, b) => priorityOrder[a.priority] - priorityOrder[b.priority]
  );

  return (
    <div className="space-y-4 p-4 md:p-6">
      <h1 className="text-xl font-semibold">Inbox</h1>
      <p className="text-sm text-muted-foreground">Items that need founder attention.</p>

      {isLoading ? (
        <p className="text-muted-foreground">Loading…</p>
      ) : sorted.length === 0 ? (
        <p className="text-muted-foreground">Inbox zero — nothing needs action.</p>
      ) : (
        <ul className="space-y-3">
          {sorted.map((item) => (
            <InboxRow
              key={item.id}
              item={item}
              workspaceId={workspaceId}
              onResolve={() => patch.mutate({ id: item.id, status: "resolved" })}
              onDismiss={() => patch.mutate({ id: item.id, status: "dismissed" })}
            />
          ))}
        </ul>
      )}
    </div>
  );
}

function InboxRow({
  item,
  workspaceId,
  onResolve,
  onDismiss,
}: {
  item: InboxItem;
  workspaceId: string;
  onResolve: () => void;
  onDismiss: () => void;
}) {
  const boardHref = item.decision_id
    ? `/workspace/${workspaceId}/board?session=${item.decision_id.replace("decision-", "")}`
    : `/workspace/${workspaceId}/board`;

  return (
    <Card className={cn("border-l-4", typeColors[item.item_type])}>
      <CardContent className="flex flex-wrap items-start justify-between gap-4 pt-4">
        <div className="min-w-0 flex-1">
          <Link href={boardHref} className="font-medium hover:text-primary">
            {item.title}
          </Link>
          {item.body && <p className="mt-1 text-sm text-muted-foreground">{item.body}</p>}
          <p className="mt-2 text-xs text-muted-foreground">
            {item.item_type.replace(/_/g, " ")} · {item.priority} · {formatDate(item.created_at)}
          </p>
        </div>
        <div className="flex gap-2">
          <Button size="sm" onClick={onResolve}>
            Resolve
          </Button>
          <Button size="sm" variant="secondary" onClick={onDismiss}>
            Defer
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
