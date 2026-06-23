"use client";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import type { EvidenceSource } from "@/lib/types";
import { ExternalLink } from "lucide-react";

export function EvidenceAccordion({ evidence }: { evidence: EvidenceSource[] }) {
  if (!evidence?.length) return null;

  return (
    <Accordion type="single" collapsible className="w-full">
      <AccordionItem value="evidence" className="border-none">
        <AccordionTrigger className="py-2 text-xs text-muted-foreground hover:no-underline">
          View Evidence ({evidence.length})
        </AccordionTrigger>
        <AccordionContent>
          <ul className="space-y-2 text-sm">
            {evidence.map((e, i) => (
              <li key={i} className="rounded-md border border-border/60 bg-secondary/30 p-2">
                <p className="text-xs text-muted-foreground">{e.source}</p>
                <p className="mt-1">{e.snippet}</p>
                {e.url && (
                  <a
                    href={e.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-1 inline-flex items-center gap-1 text-xs text-primary hover:underline"
                  >
                    Source <ExternalLink className="h-3 w-3" />
                  </a>
                )}
              </li>
            ))}
          </ul>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
}
