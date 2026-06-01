"use client";

import { useState } from "react";
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
import type { ChunkType, MemoryChunk } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import { Upload } from "lucide-react";

const chunkTypes: ChunkType[] = [
  "strategy_note",
  "research_summary",
  "decision_log",
  "entity_profile",
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

  const entities = chunks.reduce<Record<string, MemoryChunk[]>>((acc, c) => {
    const name = c.entity_name ?? "_ungrouped";
    if (!acc[name]) acc[name] = [];
    acc[name].push(c);
    return acc;
  }, {});

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
    <div className="space-y-4 p-4 md:p-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-xl font-semibold">Memory</h1>
        <div className="flex gap-2">
          <Dialog>
            <DialogTrigger asChild>
              <Button variant="secondary">Add Note</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add strategy note</DialogTitle>
              </DialogHeader>
              <Textarea
                value={noteContent}
                onChange={(e) => setNoteContent(e.target.value)}
                placeholder="Store context for the founder…"
                rows={5}
              />
              <Button onClick={() => addNote.mutate()} disabled={!noteContent.trim()}>
                Save
              </Button>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        <Input
          placeholder="Search memory…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="max-w-xs"
        />
        <div className="flex flex-wrap gap-1">
          <Button
            size="sm"
            variant={typeFilter === "" ? "default" : "outline"}
            onClick={() => setTypeFilter("")}
          >
            All
          </Button>
          {chunkTypes.map((t) => (
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
      </div>

      <label className="flex cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed border-border p-8 hover:bg-accent/50">
        <Upload className="mb-2 h-8 w-8 text-muted-foreground" />
        <span className="text-sm text-muted-foreground">Upload PDF, TXT, or MD</span>
        <input type="file" className="hidden" accept=".pdf,.txt,.md" onChange={onFileUpload} />
        {uploadStatus && (
          <span className="mt-2 text-xs text-primary">Status: {uploadStatus}</span>
        )}
      </label>

      <Tabs defaultValue="chunks">
        <TabsList>
          <TabsTrigger value="chunks">Chunks</TabsTrigger>
          <TabsTrigger value="entities">Entity cards</TabsTrigger>
        </TabsList>
        <TabsContent value="chunks" className="mt-4">
          {isLoading ? (
            <p className="text-muted-foreground">Loading…</p>
          ) : chunks.length === 0 ? (
            <p className="text-muted-foreground">No memory chunks found.</p>
          ) : (
            <div className="grid gap-3 md:grid-cols-2">
              {chunks.map((chunk) => (
                <Card key={chunk.id}>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium capitalize">
                      {chunk.chunk_type.replace("_", " ")}
                    </CardTitle>
                    <p className="text-xs text-muted-foreground">{formatDate(chunk.created_at)}</p>
                  </CardHeader>
                  <CardContent>
                    <p className="line-clamp-4 text-sm">{chunk.content}</p>
                    {chunk.entity_name && (
                      <p className="mt-2 text-xs text-primary">{chunk.entity_name}</p>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
        <TabsContent value="entities" className="mt-4">
          <div className="grid gap-3 md:grid-cols-2">
            {Object.entries(entities)
              .filter(([name]) => name !== "_ungrouped")
              .map(([name, list]) => (
                <Card key={name}>
                  <CardHeader>
                    <CardTitle>{name}</CardTitle>
                    <p className="text-xs text-muted-foreground">
                      {list.length} chunks · updated {formatDate(list[0]?.created_at ?? "")}
                    </p>
                  </CardHeader>
                </Card>
              ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
