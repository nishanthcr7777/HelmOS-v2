/** Full-height scroll container for workspace views (board, memory, inbox, etc.) */
export function ScrollablePage({ children }: { children: React.ReactNode }) {
  return <div className="h-full min-h-0 overflow-y-auto overscroll-contain">{children}</div>;
}
