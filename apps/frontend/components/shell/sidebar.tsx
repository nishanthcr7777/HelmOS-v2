"use client";

import Link from "next/link";
import { useParams, usePathname } from "next/navigation";
import {
  MessageSquare,
  Users,
  Brain,
  Search,
  Inbox,
  ScrollText,
  Menu,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useState } from "react";

const nav = [
  { href: "chat", label: "Chat", icon: MessageSquare },
  { href: "board", label: "Board", icon: Users },
  { href: "memory", label: "Memory", icon: Brain },
  { href: "research", label: "Research", icon: Search },
  { href: "inbox", label: "Inbox", icon: Inbox },
  { href: "decisions", label: "Decisions", icon: ScrollText },
];

export function Sidebar() {
  const pathname = usePathname();
  const params = useParams();
  const workspaceId = params?.workspaceId as string;
  const [open, setOpen] = useState(false);

  const links = (
    <nav className="flex flex-col gap-1 p-2">
      {nav.map(({ href, label, icon: Icon }) => {
        const path = `/workspace/${workspaceId}/${href}`;
        const active = pathname?.includes(`/${href}`);
        return (
          <Link
            key={href}
            href={path}
            onClick={() => setOpen(false)}
            className={cn(
              "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
              active
                ? "bg-primary/15 text-primary"
                : "text-muted-foreground hover:bg-accent hover:text-foreground"
            )}
          >
            <Icon className="h-4 w-4" />
            {label}
          </Link>
        );
      })}
    </nav>
  );

  return (
    <>
      <Button
        variant="ghost"
        size="icon"
        className="fixed left-2 top-16 z-40 md:hidden"
        onClick={() => setOpen(!open)}
        aria-label="Toggle navigation"
      >
        <Menu className="h-5 w-5" />
      </Button>
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-30 mt-14 w-56 overflow-y-auto border-r border-border bg-card transition-transform md:static md:mt-0 md:h-full md:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        )}
      >
        {links}
      </aside>
      {open && (
        <div
          className="fixed inset-0 z-20 bg-black/50 md:hidden"
          onClick={() => setOpen(false)}
          aria-hidden
        />
      )}
    </>
  );
}
