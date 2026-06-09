export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export const USE_MSW = process.env.NEXT_PUBLIC_USE_MSW !== "false";

export const MOCK_LATENCY_MS = Number(process.env.NEXT_PUBLIC_MOCK_LATENCY_MS ?? "0");

export const API_KEY = process.env.NEXT_PUBLIC_HELMOS_API_KEY ?? "";

/** Headers for JSON API calls (includes Bearer when API_KEY is set). */
export function apiHeaders(extra?: HeadersInit): HeadersInit {
  const headers = new Headers(extra);
  if (API_KEY && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${API_KEY}`);
  }
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  return headers;
}

/** Auth only — for multipart uploads (no Content-Type; browser sets boundary). */
export function apiAuthHeaders(): HeadersInit {
  return API_KEY ? { Authorization: `Bearer ${API_KEY}` } : {};
}
