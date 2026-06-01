import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AppState {
  workspaceId: string;
  projectId: string | null;
  draftMessage: string;
  boardPrefillQuestion: string | null;
  setWorkspaceId: (id: string) => void;
  setProjectId: (id: string | null) => void;
  setDraftMessage: (msg: string) => void;
  setBoardPrefillQuestion: (q: string | null) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      workspaceId: "clawback-labs",
      projectId: null,
      draftMessage: "",
      boardPrefillQuestion: null,
      setWorkspaceId: (workspaceId) => set({ workspaceId, projectId: null }),
      setProjectId: (projectId) => set({ projectId }),
      setDraftMessage: (draftMessage) => set({ draftMessage }),
      setBoardPrefillQuestion: (boardPrefillQuestion) => set({ boardPrefillQuestion }),
    }),
    { name: "helmos-app" }
  )
);
