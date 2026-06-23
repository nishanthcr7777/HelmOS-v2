"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { ResearchJob, ResearchStep } from "@/lib/types";
import { Check, Circle } from "lucide-react";
import { cn } from "@/lib/utils";

const steps: { key: ResearchStep; label: string }[] = [
  { key: "querying", label: "Querying" },
  { key: "searching", label: "Searching" },
  { key: "extracting", label: "Extracting" },
  { key: "summarizing", label: "Summarizing" },
  { key: "done", label: "Done" },
];

export function ResearchView() {
  const params = useParams();
  const workspaceId = params.workspaceId as string;
  const [entity, setEntity] = useState("Acme Corp");
  const [queries, setQueries] = useState(["Acme Corp company overview", "Acme Corp payroll compliance"]);
  const [job, setJob] = useState<ResearchJob | null>(null);

  const runResearch = useMutation({
    mutationFn: () => api.runResearch({ entity_name: entity, workspace_id: workspaceId }),
    onSuccess: (j) => setJob(j),
  });

  useEffect(() => {
    if (!job || job.step === "done") return;
    const t = setInterval(async () => {
      const updated = await api.getResearchStatus(job.id);
      setJob(updated);
    }, 1200);
    return () => clearInterval(t);
  }, [job]);

  const stepIndex = steps.findIndex((s) => s.key === (job?.step ?? "idle"));

  return (
    <div className="space-y-6 p-4 md:p-6">
      <h1 className="text-xl font-semibold">Research</h1>
      <p className="text-sm text-muted-foreground">
        Web research pipeline — search, extract, summarize (mock).
      </p>

      <div className="flex flex-wrap gap-2">
        <Input value={entity} onChange={(e) => setEntity(e.target.value)} className="max-w-xs" />
        <Button onClick={() => runResearch.mutate()} disabled={runResearch.isPending}>
          Run research
        </Button>
      </div>

      <div className="space-y-2">
        <p className="text-sm font-medium">Queries</p>
        {queries.map((q, i) => (
          <Input
            key={i}
            value={q}
            onChange={(e) => {
              const next = [...queries];
              next[i] = e.target.value;
              setQueries(next);
            }}
          />
        ))}
        <Button variant="outline" size="sm" onClick={() => setQueries([...queries, ""])}>
          Add query
        </Button>
      </div>

      {job && (
        <>
          <ol className="flex flex-wrap gap-4">
            {steps.map((s, i) => (
              <li key={s.key} className="flex items-center gap-2 text-sm">
                {i <= stepIndex ? (
                  <Check className="h-4 w-4 text-primary" />
                ) : (
                  <Circle className="h-4 w-4 text-muted-foreground" />
                )}
                <span className={cn(i === stepIndex && "font-medium text-primary")}>{s.label}</span>
              </li>
            ))}
          </ol>

          {job.sources.length > 0 && (
            <div className="space-y-3">
              <h2 className="font-medium">Sources</h2>
              {job.sources.map((src, i) => (
                <Card key={i}>
                  <CardContent className="pt-4">
                    <div className="flex items-start justify-between gap-2">
                      <a href={src.url} className="font-medium text-primary hover:underline" target="_blank" rel="noreferrer">
                        {src.title}
                      </a>
                      <Badge variant="outline">{src.relevance}</Badge>
                    </div>
                    <p className="mt-2 text-sm text-muted-foreground">{src.snippet}</p>
                    {src.published_at && (
                      <p className="mt-1 text-xs text-muted-foreground">{src.published_at}</p>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
