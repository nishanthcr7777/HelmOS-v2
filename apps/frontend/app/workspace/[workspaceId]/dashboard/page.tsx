import { DashboardView } from "@/components/dashboard/dashboard-view";
import { ScrollablePage } from "@/components/shell/scrollable-page";

export default function DashboardPage() {
  return (
    <ScrollablePage>
      <DashboardView />
    </ScrollablePage>
  );
}
