/** Coerce LLM/API values (0–1, 0–100, NaN, strings) to a safe 0–1 float. */
export function normalizeConfidence(value: unknown, fallback = 0.5): number {
  if (typeof value === "string") {
    const trimmed = value.trim().replace(/%$/, "");
    const parsed = Number(trimmed);
    if (!Number.isFinite(parsed)) return fallback;
    return parsed > 1 ? Math.min(1, parsed / 100) : Math.max(0, Math.min(1, parsed));
  }
  if (typeof value !== "number" || !Number.isFinite(value)) return fallback;
  return value > 1 ? Math.min(1, value / 100) : Math.max(0, Math.min(1, value));
}

export function confidencePercent(value: unknown, fallback = 0.5): number {
  return Math.round(normalizeConfidence(value, fallback) * 100);
}

export function confidenceLabel(value: number): "Low" | "Moderate" | "High" {
  const n = normalizeConfidence(value);
  if (n < 0.4) return "Low";
  if (n < 0.7) return "Moderate";
  return "High";
}

export function confidenceDescription(value: number): string {
  const n = normalizeConfidence(value);
  if (n < 0.4) return "Treat as hypothesis";
  if (n < 0.7) return "Verify before committing";
  return "Evidence-grounded";
}
