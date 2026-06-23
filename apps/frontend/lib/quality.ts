import type { QualityLevel, UnknownsLevel } from "@/lib/types";

export function qualityLabel(level: QualityLevel): string {
  return level.charAt(0).toUpperCase() + level.slice(1);
}

export function qualityColor(level: QualityLevel): string {
  switch (level) {
    case "high":
      return "text-emerald-600 dark:text-emerald-400";
    case "moderate":
      return "text-amber-600 dark:text-amber-400";
    case "low":
      return "text-red-600 dark:text-red-400";
  }
}

export function unknownsLabel(level: UnknownsLevel): string {
  return level.charAt(0).toUpperCase() + level.slice(1);
}

export function unknownsColor(level: UnknownsLevel): string {
  switch (level) {
    case "high":
      return "text-amber-600 dark:text-amber-400";
    case "moderate":
      return "text-muted-foreground";
    case "low":
      return "text-emerald-600 dark:text-emerald-400";
  }
}
