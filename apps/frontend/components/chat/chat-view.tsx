"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { streamChat } from "@/lib/api/client";
import { EvidenceAccordion } from "@/components/shared/evidence-accordion";
import { ConfidenceLabel } from "@/components/shared/confidence-label";
import { useAppStore } from "@/lib/stores/app-store";
import { suggestedPrompts } from "@/mocks/fixtures/data";
import type { ChatMessage, EvidenceSource, MessageTag } from "@/lib/types";
import { Square, Users } from "lucide-react";

export function ChatView() {
  const router = useRouter();
  const params = useParams();
  const workspaceId = params.workspaceId as string;
  const setBoardPrefill = useAppStore((s) => s.setBoardPrefillQuestion);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [streamContent, setStreamContent] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamContent]);

  async function sendMessage(text: string) {
    if (!text.trim() || streaming) return;
    const userMsg: ChatMessage = {
      id: `u-${Date.now()}`,
      role: "user",
      content: text.trim(),
    };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setStreaming(true);
    setStreamContent("");

    let full = "";
    try {
      await streamChat(
        text,
        (token) => {
          full += token;
          setStreamContent(full);
        },
        (meta) => {
          const assistant: ChatMessage = {
            id: `a-${Date.now()}`,
            role: "assistant",
            content: full,
            tag: (meta.tag as MessageTag) ?? "plain",
            confidence: meta.confidence,
            evidence: meta.evidence as EvidenceSource[],
          };
          setMessages((m) => [...m, assistant]);
          setStreamContent("");
        }
      );
    } catch {
      setMessages((m) => [
        ...m,
        {
          id: `err-${Date.now()}`,
          role: "assistant",
          content: "Something went wrong. Please try again.",
        },
      ]);
      setStreamContent("");
    } finally {
      setStreaming(false);
    }
  }

  function invokeBoard() {
    const q = input.trim() || messages.filter((m) => m.role === "user").pop()?.content;
    if (q) setBoardPrefill(q);
    router.push(`/workspace/${workspaceId}/board`);
  }

  const prompts = suggestedPrompts[workspaceId] ?? [];

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-4">
        <div className="mx-auto max-w-3xl space-y-4 py-4" role="log" aria-live="polite" aria-label="Chat messages">
          {messages.length === 0 && !streaming && (
            <div className="rounded-lg border border-dashed border-border p-8 text-center">
              <p className="text-muted-foreground">Ask anything about your workspace context.</p>
              <div className="mt-4 flex flex-wrap justify-center gap-2">
                {prompts.map((p) => (
                  <Button key={p} variant="outline" size="sm" onClick={() => sendMessage(p)}>
                    {p}
                  </Button>
                ))}
              </div>
            </div>
          )}
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[85%] rounded-lg px-4 py-3 ${
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "border border-border bg-card"
                }`}
              >
                {msg.tag && msg.role === "assistant" && (
                  <Badge variant="secondary" className="mb-2 text-xs">
                    {msg.tag}
                  </Badge>
                )}
                {msg.role === "assistant" ? (
                  <div className="prose prose-invert prose-sm max-w-none">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                  </div>
                ) : (
                  <p className="text-sm">{msg.content}</p>
                )}
                {msg.confidence != null && (
                  <div className="mt-2">
                    <ConfidenceLabel value={msg.confidence} />
                  </div>
                )}
                {msg.evidence && <EvidenceAccordion evidence={msg.evidence} />}
              </div>
            </div>
          ))}
          {streaming && streamContent && (
            <div className="flex justify-start">
              <div className="max-w-[85%] rounded-lg border border-border bg-card px-4 py-3">
                <div className="prose prose-invert prose-sm max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{streamContent}</ReactMarkdown>
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      </div>

      <div className="shrink-0 border-t border-border bg-background p-4">
        <div className="mx-auto flex max-w-3xl flex-col gap-2">
          <Textarea
            placeholder="Ask HelmOS… (Cmd+K to focus)"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendMessage(input);
              }
            }}
            rows={3}
            aria-label="Message input"
          />
          <div className="flex gap-2">
            <Button onClick={() => sendMessage(input)} disabled={streaming || !input.trim()}>
              Send
            </Button>
            <Button variant="secondary" onClick={invokeBoard} disabled={streaming}>
              <Users className="mr-2 h-4 w-4" />
              Invoke Board
            </Button>
            {streaming && (
              <Button variant="ghost" size="icon" onClick={() => setStreaming(false)} aria-label="Stop">
                <Square className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
