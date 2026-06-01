export function confidenceLabel(value: number): "Low" | "Moderate" | "High" {
  if (value < 0.4) return "Low";
  if (value < 0.7) return "Moderate";
  return "High";
}

export function confidenceDescription(value: number): string {
  if (value < 0.4) return "Treat as hypothesis";
  if (value < 0.7) return "Verify before committing";
  return "Evidence-grounded";
}
