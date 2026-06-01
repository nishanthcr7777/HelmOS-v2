"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { SectionHeader } from "@/components/shared/section-header";
import { DecisionStatusBadge } from "@/components/shared/decision-status-badge";
import { VerdictBadge } from "@/components/shared/verdict-badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { formatDate } from "@/lib/utils";
import { workspaces } from "@/mocks/fixtures/data";
import {
  AlertTriangle,
  ArrowRight,
  GitBranch,
  Lightbulb,
  Target,
} from "lucide-react";
import { cn } from "@/lib/utils";

export function DashboardView() {
  const params = useParams();
  const workspaceId = params.workspaceId as string;

  const { data, isLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => api.getDashboard(),
  });

  if (isLoading || !data) {
    return <div className="p-6 text-muted-foreground">Loading mission brief…</div>;
  }

  const wsName = (id: string) => workspaces.find((w) => w.id === id)?.name ?? id;

  return (
    <div className="mx-auto max-w-6xl space-y-8 p-4 md:p-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">What matters now</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Founder intelligence brief — priorities, decisions, and signals across workspaces.
        </p>
      </div>

      <section>
        <SectionHeader title="Today's focus" subtitle="Top priorities from inbox and open decisions" />
        <div className="grid gap-4 md:grid-cols-2">
          {data.todays_focus.map((focus) => (
            <Card key={focus.id} className="border-border/80">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Target className="h-4 w-4 text-primary" />
                  {focus.workspace_name}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ol className="list-decimal space-y-2 pl-4 text-sm">
                  {focus.items.map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ol>
                <Button variant="ghost" size="sm" className="mt-3 h-8 px-0" asChild>
                  <Link href={`/workspace/${focus.workspace_id}/inbox`}>
                    View inbox <ArrowRight className="ml-1 h-3 w-3" />
                  </Link>
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section>
        <SectionHeader
          title="Active decisions"
          subtitle="Requires founder judgment"
          action={
            <Button variant="outline" size="sm" asChild>
              <Link href={`/workspace/${workspaceId}/decisions`}>All decisions</Link>
            </Button>
          }
        />
        <div className="grid gap-3 lg:grid-cols-2">
          {data.active_decisions.slice(0, 5).map((d) => (
            <Link key={d.id} href={`/workspace/${d.workspace_id}/decisions/${d.id}`}>
              <Card className="transition-colors hover:border-primary/40">
                <CardContent className="pt-4">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <p className="font-medium leading-snug">{d.title}</p>
                    <DecisionStatusBadge status={d.status} />
                  </div>
                  <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                    <span>{wsName(d.workspace_id)}</span>
                    <span>·</span>
                    <VerdictBadge verdict={d.verdict} />
                    <span>·</span>
                    <span>Updated {formatDate(d.updated_at)}</span>
                  </div>
                  <div className="mt-3 grid grid-cols-3 gap-2 border-t border-border pt-3 text-xs">
                    <div>
                      <span className="text-muted-foreground">Confidence</span>
                      <p className="font-medium tabular-nums">{Math.round(d.confidence * 100)}%</p>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Risk</span>
                      <p className="font-medium capitalize">{d.risk_level}</p>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Unknowns</span>
                      <p className="font-medium capitalize">{d.unknowns_level}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </section>

      <div className="grid gap-8 lg:grid-cols-2">
        <section>
          <SectionHeader title="Board alerts" subtitle="Conflicts, assumptions, low confidence" />
          <ul className="space-y-2">
            {data.board_alerts.map((alert) => (
              <li key={alert.id}>
                <Link
                  href={
                    alert.session_id
                      ? `/workspace/${alert.workspace_id}/board?session=${alert.session_id}`
                      : `/workspace/${alert.workspace_id}/board`
                  }
                  className="flex gap-3 rounded-lg border border-border bg-card/50 p-3 transition-colors hover:border-amber-500/30"
                >
                  <AlertTriangle
                    className={cn(
                      "mt-0.5 h-4 w-4 shrink-0",
                      alert.alert_type === "conflict" && "text-orange-600 dark:text-orange-400",
                      alert.alert_type === "risky_assumption" && "text-amber-600 dark:text-amber-400",
                      alert.alert_type === "low_confidence" && "text-red-600 dark:text-red-400"
                    )}
                  />
                  <div>
                    <p className="text-sm font-medium">{alert.title}</p>
                    <p className="text-xs text-muted-foreground">{alert.detail}</p>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </section>

        <section>
          <SectionHeader title="Opportunity feed" subtitle="Leads, research, partnerships" />
          <ul className="space-y-2">
            {data.opportunities.map((opp) => (
              <li key={opp.id}>
                <Link
                  href={`/workspace/${opp.workspace_id}/research`}
                  className="flex gap-3 rounded-lg border border-border bg-card/50 p-3 transition-colors hover:border-emerald-500/30"
                >
                  <Lightbulb className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
                  <div>
                    <p className="text-sm font-medium">{opp.title}</p>
                    <p className="text-xs text-muted-foreground">
                      {opp.workspace_name}
                      {opp.entity_name ? ` · ${opp.entity_name}` : ""}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">{opp.detail}</p>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      </div>

      <section className="rounded-lg border border-dashed border-border p-4">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <GitBranch className="h-4 w-4" />
          Need deep analysis? Use{" "}
          <Link href={`/workspace/${workspaceId}/board`} className="text-primary hover:underline">
            Board review
          </Link>{" "}
          or{" "}
          <Link href={`/workspace/${workspaceId}/brief`} className="text-primary hover:underline">
            Intelligence brief
          </Link>{" "}
          — not the default starting point.
        </div>
      </section>
    </div>
  );
}
