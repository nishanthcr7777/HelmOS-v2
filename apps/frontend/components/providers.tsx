"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { USE_MSW } from "@/lib/api/config";
import { ThemeProvider } from "@/components/theme/theme-provider";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient());
  const [mswReady, setMswReady] = useState(!USE_MSW);

  useEffect(() => {
    if (!USE_MSW) return;
    async function init() {
      const { worker } = await import("@/mocks/browser");
      await worker.start({ onUnhandledRequest: "bypass" });
      setMswReady(true);
    }
    init();
  }, []);

  if (!mswReady) {
    return (
      <div className="flex h-screen items-center justify-center text-muted-foreground">
        Starting HelmOS…
      </div>
    );
  }

  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </ThemeProvider>
  );
}
