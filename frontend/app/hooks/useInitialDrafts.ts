"use client";

import { useEffect, useRef } from "react";
import { useDraftStore } from "@/app/store/draftStore";

import { authFetch } from "@/app/lib/api";

export function useInitialDrafts(roomId: string) {
  const addDraft = useDraftStore((state) => state.addDraft);
  const fetched = useRef(false);

  useEffect(() => {
    if (fetched.current || !roomId) return;
    
    async function fetchDrafts() {
      try {
        const res = await authFetch(`/api/approval?room_id=${encodeURIComponent(roomId)}`);
        if (res.ok) {
          const drafts = await res.json();
          drafts.forEach((draft: any) => addDraft(draft));
        }
      } catch {
        // Drafts will still arrive over WebSocket after the connection is ready.
      }
    }
    
    fetched.current = true;
    fetchDrafts();
  }, [addDraft, roomId]);
}
