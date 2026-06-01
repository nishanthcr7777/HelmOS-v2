import { MemoryView } from "@/components/memory/memory-view";
import { ScrollablePage } from "@/components/shell/scrollable-page";

export default function MemoryPage() {
  return (
    <ScrollablePage>
      <MemoryView />
    </ScrollablePage>
  );
}
