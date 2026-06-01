"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { SectionHeader } from "@/components/shared/section-header";
import type { ChunkType, MemoryChunk } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import { researchAgeLabel } from "@/lib/agent-meta";
import { Upload } from "lucide-react";

const noteTypes: ChunkType[] = [
  "strategy_note",
  "research_summary",
  "decision_log",
  "document_chunk",
];

export function MemoryView() {
  const params = useParams();
  const workspaceId = params.workspaceId as string;
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("");
  const [noteContent, setNoteContent] = useState("");
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data: chunks = [], isLoading } = useQuery({
    queryKey: ["memory", workspaceId, typeFilter, search],
    queryFn: () =>
      api.getMemoryChunks({
        workspace_id: workspaceId,
        type: typeFilter || undefined,
        search: search || undefined,
      }),
  });

  const { data: beliefs = [] } = useQuery({
    queryKey: ["beliefs", workspaceId],
    queryFn: () => api.getBeliefs(workspaceId),
  });

  const { data: entities = [] } = useQuery({
    queryKey: ["entities", workspaceId],
    queryFn: () => api.getEntities(workspaceId),
  });

  const addNote = useMutation({
    mutationFn: () =>
      api.createMemoryChunk({
        workspace_id: workspaceId,
        chunk_type: "strategy_note",
        content: noteContent,
      }),
    onSuccess: () => {
      setNoteContent("");
      queryClient.invalidateQueries({ queryKey: ["memory"] });
    },
  });

  const filteredChunks = chunks.filter((c) => c.chunk_type !== "entity_profile");

  async function onFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadStatus("processing");
    try {
      await api.ingestFile(file, workspaceId);
      setUploadStatus("indexed");
      queryClient.invalidateQueries({ queryKey: ["memory"] });
    } catch {
      setUploadStatus("error");
    }
  }

  return (
    <div className="space-y-6 p-4 md:p-6">
      <SectionHeader
        title="Organizational knowledge"
        subtitle="Strategic beliefs, entities, and operational memory"
      />

      <Tabs defaultValue="beliefs">
        <TabsList>
          <TabsTrigger value="beliefs">Strategic beliefs</TabsTrigger>
          <TabsTrigger value="entities">Entity cards</TabsTrigger>
          <TabsTrigger value="notes">Notes & documents</TabsTrigger>
        </TabsList>

        <TabsContent value="beliefs" className="mt-4 space-y-3">
          <p className="text-sm text-muted-foreground">
            Founding principles that guide decisions — separate from transient notes.
          </p>
          {beliefs.map((b) => (
            <Card key={b.id} className="border-l-4 border-l-primary/50">
              <CardContent className="pt-4">
                <p className="text-sm font-medium">{b.content}</p>
                <p className="mt-2 text-xs text-muted-foreground">Since {formatDate(b.created_at)}</p>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="entities" className="mt-4">
          <div className="grid gap-3 md:grid-cols-2">
            {entities.map((entity) => (
              <Card key={entity.id}>
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <CardTitle className="text-base">{entity.name}</CardTitle>
                    <span className="text-xs uppercase text-muted-foreground">{entity.entity_type}</span>
                  </div>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <p className="text-muted-foreground">{entity.summary}</p>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-muted-foreground">Last researched</span>
                      <p>
                        {entity.research_age_days != null
                          ? researchAgeLabel(entity.research_age_days)
                          : "—"}
                      </p>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Confidence</span>
                      <p className="tabular-nums">{Math.round(entity.confidence * 100)}%</p>
                    </div>
                  </div>
                  {entity.linked_decision_ids.length > 0 && (
                    <div className="border-t border-border pt-2">
                      <p className="text-xs text-muted-foreground">Linked decisions</p>
                      {entity.linked_decision_ids.map((id) => (
                        <Link
                          key={id}
                          href={`/workspace/${workspaceId}/decisions/${id}`}
                          className="mt-1 block text-xs text-primary hover:underline"
                        >
                          View decision →
                        </Link>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="notes" className="mt-4 space-y-4">
          <div className="flex flex-wrap gap-2">
            <Input
              placeholder="Search notes…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="max-w-xs"
            />
            <Dialog>
              <DialogTrigger asChild>
                <Button variant="secondary">Add note</Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Add operational note</DialogTitle>
                </DialogHeader>
                <Textarea
                  value={noteContent}
                  onChange={(e) => setNoteContent(e.target.value)}
                  rows={5}
                />
                <Button onClick={() => addNote.mutate()} disabled={!noteContent.trim()}>
                  Save
                </Button>
              </DialogContent>
            </Dialog>
          </div>

          <label className="flex cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed border-border p-6 hover:bg-accent/30">
            <Upload className="mb-2 h-6 w-6 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">Upload PDF, TXT, or MD</span>
            <input type="file" className="hidden" accept=".pdf,.txt,.md" onChange={onFileUpload} />
            {uploadStatus && <span className="mt-2 text-xs text-primary">Status: {uploadStatus}</span>}
          </label>

          <div className="flex flex-wrap gap-1">
            <Button size="sm" variant={typeFilter === "" ? "default" : "outline"} onClick={() => setTypeFilter("")}>
              All
            </Button>
            {noteTypes.map((t) => (
              <Button
                key={t}
                size="sm"
                variant={typeFilter === t ? "default" : "outline"}
                onClick={() => setTypeFilter(t)}
              >
                {t.replace("_", " ")}
              </Button>
            ))}
          </div>

          {isLoading ? (
            <p className="text-muted-foreground">Loading…</p>
          ) : (
            <div className="grid gap-3 md:grid-cols-2">
              {filteredChunks.map((chunk: MemoryChunk) => (
                <Card key={chunk.id}>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-xs font-semibold uppercase text-muted-foreground">
                      {chunk.chunk_type.replace("_", " ")}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="line-clamp-4 text-sm">{chunk.content}</p>
                    <p className="mt-2 text-xs text-muted-foreground">{formatDate(chunk.created_at)}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
