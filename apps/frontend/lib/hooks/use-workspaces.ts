import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";

export function useWorkspaces() {
  return useQuery({
    queryKey: ["workspaces"],
    queryFn: () => api.getWorkspaces(),
  });
}

export function useWorkspaceName(workspaceId: string) {
  const { data: workspaces } = useWorkspaces();
  return workspaces?.find((w) => w.id === workspaceId)?.name ?? workspaceId;
}

export function workspaceNameFrom(
  workspaces: { id: string; name: string }[] | undefined,
  workspaceId: string
) {
  return workspaces?.find((w) => w.id === workspaceId)?.name ?? workspaceId;
}
