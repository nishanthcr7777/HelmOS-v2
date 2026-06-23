"use client";

import Link from "next/link";
import { useParams, usePathname } from "next/navigation";
import {
  LayoutDashboard,
  FileText,
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
  { href: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "decisions", label: "Decisions", icon: ScrollText },
  { href: "board", label: "Board", icon: Users },
  { href: "memory", label: "Knowledge", icon: Brain },
  { href: "research", label: "Research", icon: Search },
  { href: "inbox", label: "Inbox", icon: Inbox },
  { href: "brief", label: "Intel brief", icon: FileText },
];

export function Sidebar() {
  const pathname = usePathname();
  const params = useParams();
  const workspaceId = params?.workspaceId as string;
  const [open, setOpen] = useState(false);

  const links = (
    <nav className="flex flex-col gap-0.5 p-2">
      {nav.map(({ href, label, icon: Icon }) => {
        const path = `/workspace/${workspaceId}/${href}`;
        const active =
          pathname === path ||
          pathname?.startsWith(`${path}/`) ||
          (href === "dashboard" && pathname === `/workspace/${workspaceId}`);
        return (
          <Link
            key={href}
            href={path}
            onClick={() => setOpen(false)}
            className={cn(
              "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
              active
                ? "bg-primary/15 font-medium text-primary"
                : "text-muted-foreground hover:bg-accent hover:text-foreground",
              href === "brief" && "mt-2 border-t border-border pt-3"
            )}
          >
            <Icon className="h-4 w-4 shrink-0" />
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
          "fixed inset-y-0 left-0 z-30 mt-14 w-52 overflow-y-auto border-r border-border bg-card transition-transform md:static md:mt-0 md:h-full md:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        )}
      >
        <p className="px-4 pb-1 pt-3 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
          Navigation
        </p>
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
