"use client";

import { useState } from "react";
import { useSearchParams, useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { useAppStore } from "@/lib/stores/app-store";
import { AgentCard } from "./agent-card";
import { AgentInfluenceBar } from "./agent-influence-bar";
import { SynthesisPanel } from "./synthesis-panel";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { boardSessions } from "@/mocks/fixtures/data";

export function BoardView() {
  const params = useParams();
  const searchParams = useSearchParams();
  const workspaceId = params.workspaceId as string;
  const sessionId = searchParams.get("session") ?? "session-acme-001";
  const prefill = useAppStore((s) => s.boardPrefillQuestion);
  const clearPrefill = useAppStore((s) => s.setBoardPrefillQuestion);
  const [question, setQuestion] = useState(prefill ?? "");
  const [pushBackLoading, setPushBackLoading] = useState(false);
  const queryClient = useQueryClient();

  const { data: session } = useQuery({
    queryKey: ["board", sessionId],
    queryFn: () => api.getBoardSession(sessionId),
    initialData: boardSessions.find((s) => s.id === sessionId) ?? boardSessions[0],
  });

  const runBoard = useMutation({
    mutationFn: () => api.createBoardSession({ question, workspace_id: workspaceId }),
    onSuccess: () => {
      clearPrefill(null);
      queryClient.invalidateQueries({ queryKey: ["board"] });
    },
  });

  if (!session?.synthesis) {
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
            Run Board
          </Button>
        </div>
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
            loading={pushBackLoading && agent.agent === "skeptic"}
          />
        ))}
      </div>

      {session.synthesis && <SynthesisPanel synthesis={session.synthesis} />}

      <div className="flex flex-wrap gap-2 border-t border-border pt-4">
        <Button
          onClick={() => {
            if (session) {
              api.patchDecision(`decision-${session.id}`, { status: "resolved" });
            }
          }}
        >
          Accept
        </Button>
        <Button
          variant="secondary"
          onClick={() => {
            if (session) {
              api.patchDecision(`decision-${session.id}`, { status: "deferred" });
            }
          }}
        >
          Defer
        </Button>
        <Button
          variant="outline"
          onClick={() => {
            setPushBackLoading(true);
            setTimeout(() => setPushBackLoading(false), 2000);
          }}
        >
          Push Back
        </Button>
      </div>
    </div>
  );
}
