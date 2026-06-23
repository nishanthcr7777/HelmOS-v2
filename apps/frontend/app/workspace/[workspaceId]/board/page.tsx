import { Suspense } from "react";
import { BoardView } from "@/components/board/board-view";
import { ScrollablePage } from "@/components/shell/scrollable-page";

export default function BoardPage() {
  return (
    <ScrollablePage>
      <Suspense fallback={<div className="p-6 text-muted-foreground">Loading board…</div>}>
        <BoardView />
      </Suspense>
    </ScrollablePage>
  );
}
