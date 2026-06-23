import { Header } from "@/components/shell/header";
import { Sidebar } from "@/components/shell/sidebar";
import { WorkspacePanel } from "@/components/shell/workspace-panel";
import { KeyboardShortcuts } from "@/components/keyboard-shortcuts";

export default function WorkspaceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen flex-col">
      <Header />
      <WorkspacePanel />
      <KeyboardShortcuts />
      <div className="flex min-h-0 flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex min-h-0 flex-1 flex-col overflow-hidden md:pl-0">
          {children}
        </main>
      </div>
    </div>
  );
}
