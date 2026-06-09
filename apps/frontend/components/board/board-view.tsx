"use client";

import { useState } from "react";
import { useRouter, useSearchParams, useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { useAppStore } from "@/lib/stores/app-store";
import { AgentCard } from "./agent-card";
import { AgentInfluenceBar } from "./agent-influence-bar";
import { SynthesisPanel } from "./synthesis-panel";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function BoardView() {
  const router = useRouter();
  const params = useParams();
  const searchParams = useSearchParams();
  const workspaceId = params.workspaceId as string;
  const sessionId = searchParams.get("session");
  const prefill = useAppStore((s) => s.boardPrefillQuestion);
  const clearPrefill = useAppStore((s) => s.setBoardPrefillQuestion);
  const [question, setQuestion] = useState(prefill ?? "");
  const [actionError, setActionError] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const {
    data: session,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["board", sessionId],
    queryFn: () => api.getBoardSession(sessionId!),
    enabled: Boolean(sessionId),
    retry: false,
  });

  const runBoard = useMutation({
    mutationFn: () => api.createBoardSession({ question, workspace_id: workspaceId }),
    onSuccess: (data) => {
      clearPrefill(null);
      setActionError(null);
      router.push(`/workspace/${workspaceId}/board?session=${data.id}`);
    },
    onError: () => setActionError("Board session failed. Check the API is running."),
  });

  const patchDecision = useMutation({
    mutationFn: ({ decisionId, status }: { decisionId: string; status: string }) =>
      api.patchDecision(decisionId, { status }),
    onSuccess: () => {
      setActionError(null);
      queryClient.invalidateQueries({ queryKey: ["decisions"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["inbox"] });
    },
    onError: () => setActionError("Could not update decision. Run a new board session if this one is older."),
  });

  const pushBack = useMutation({
    mutationFn: () => {
      const recap = session?.synthesis?.recommendation ?? session?.question ?? question;
      return api.createBoardSession({
        workspace_id: workspaceId,
        question: `Founder pushback — re-evaluate with extra skepticism: ${recap}`,
      });
    },
    onSuccess: (data) => {
      setActionError(null);
      router.push(`/workspace/${workspaceId}/board?session=${data.id}`);
    },
    onError: () => setActionError("Push back failed. Try again."),
  });

  const decisionId = session?.decision_id;

  function handleDecisionAction(status: string) {
    if (!decisionId) {
      setActionError("No linked decision for this session. Run the board again.");
      return;
    }
    patchDecision.mutate({ decisionId, status });
  }

  if (!sessionId) {
    return (
      <div className="p-6">
        <h1 className="text-xl font-semibold">Board review</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Adversarial intelligence report — weighted agent positions with evidence quality.
        </p>
        <div className="mt-4 flex gap-2">
          <Input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Strategic question for the board…"
            className="max-w-xl"
          />
          <Button onClick={() => runBoard.mutate()} disabled={!question.trim() || runBoard.isPending}>
            {runBoard.isPending ? "Running…" : "Run Board"}
          </Button>
        </div>
        {actionError && <p className="mt-2 text-sm text-destructive">{actionError}</p>}
      </div>
    );
  }

  if (isLoading) {
    return <div className="p-6 text-muted-foreground">Loading board session…</div>;
  }

  if (isError || !session) {
    return (
      <div className="p-6">
        <h1 className="text-xl font-semibold">Board review</h1>
        <p className="mt-2 text-sm text-muted-foreground">Session not found.</p>
        <Button className="mt-4" variant="secondary" onClick={() => router.push(`/workspace/${workspaceId}/board`)}>
          Start new board session
        </Button>
      </div>
    );
  }

  if (!session.synthesis) {
    return (
      <div className="p-6">
        <h1 className="text-xl font-semibold">Board review</h1>
        <p className="mt-1 text-sm text-muted-foreground">{session.question}</p>
        <p className="mt-4 text-muted-foreground">Board is still running or incomplete…</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-4 md:p-6">
      <div>
        <h1 className="text-xl font-semibold">Board review</h1>
        <p className="mt-1 text-sm text-muted-foreground">{session.question}</p>
      </div>

      <AgentInfluenceBar agents={session.agent_outputs} />

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {session.agent_outputs.map((agent) => (
          <AgentCard
            key={agent.agent}
            agent={agent}
            loading={pushBack.isPending && agent.agent === "skeptic"}
          />
        ))}
      </div>

      <SynthesisPanel synthesis={session.synthesis} />

      <div className="flex flex-wrap gap-2 border-t border-border pt-4">
        <Button
          onClick={() => handleDecisionAction("pursuing")}
          disabled={patchDecision.isPending}
        >
          Accept
        </Button>
        <Button
          variant="secondary"
          onClick={() => handleDecisionAction("deferred")}
          disabled={patchDecision.isPending}
        >
          Defer
        </Button>
        <Button
          variant="outline"
          onClick={() => pushBack.mutate()}
          disabled={pushBack.isPending}
        >
          {pushBack.isPending ? "Pushing back…" : "Push Back"}
        </Button>
      </div>
      {actionError && <p className="text-sm text-destructive">{actionError}</p>}
      {patchDecision.isSuccess && (
        <p className="text-sm text-muted-foreground">Decision updated.</p>
      )}
    </div>
  );
}
