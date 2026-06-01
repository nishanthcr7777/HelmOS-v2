import { redirect } from "next/navigation";

export default function ChatRedirect({
  params,
}: {
  params: { workspaceId: string };
}) {
  redirect(`/workspace/${params.workspaceId}/brief`);
}
