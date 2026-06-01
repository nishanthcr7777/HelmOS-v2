export const AGENT_LABELS: Record<string, string> = {
  researcher: "Researcher",
  skeptic: "Skeptic",
  operator: "Operator",
  sales_strategist: "Sales",
  cto: "CTO",
};

export const DEFAULT_AGENT_WEIGHTS: Record<string, number> = {
  researcher: 0.4,
  skeptic: 0.25,
  operator: 0.2,
  sales_strategist: 0.1,
  cto: 0.05,
};

export function researchAgeLabel(days: number): string {
  if (days <= 0) return "Today";
  if (days === 1) return "1 day old";
  if (days < 7) return `${days} days old`;
  if (days < 14) return "7–13 days old";
  if (days === 14) return "14 days old";
  return `${days} days old`;
}
