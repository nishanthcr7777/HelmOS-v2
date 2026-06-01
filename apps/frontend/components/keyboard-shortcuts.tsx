"use client";

import { useEffect } from "react";
import { useRouter, useParams } from "next/navigation";

export function KeyboardShortcuts() {
  const router = useRouter();
  const params = useParams();
  const workspaceId = params?.workspaceId as string;

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (!(e.metaKey || e.ctrlKey) || !workspaceId) return;
      const base = `/workspace/${workspaceId}`;
      switch (e.key.toLowerCase()) {
        case "d":
          e.preventDefault();
          router.push(`${base}/dashboard`);
          break;
        case "b":
          e.preventDefault();
          router.push(`${base}/board`);
          break;
        case "r":
          e.preventDefault();
          router.push(`${base}/research`);
          break;
        case "i":
          e.preventDefault();
          router.push(`${base}/inbox`);
          break;
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [router, workspaceId]);

  return null;
}
