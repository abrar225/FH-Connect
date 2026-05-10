"use client";

import { useEffect, useRef } from "react";
import { useDraftStore } from "@/app/store/draftStore";

import { authFetch } from "@/app/lib/api";

export function useInitialDrafts(roomId: string) {
  const hydrateRoom = useDraftStore((state) => state.hydrateRoom);
  const fetched = useRef(false);

  useEffect(() => {
    if (fetched.current || !roomId) return;
    
    async function fetchDrafts() {
      try {
        const res = await authFetch(`/api/meeting/${encodeURIComponent(roomId)}/drafts`);
        if (res.ok) {
          const drafts = await res.json();
          hydrateRoom({ roomId, drafts });
        }
      } catch {
        // Drafts will still arrive over WebSocket after the connection is ready.
      }
    }
    
    fetched.current = true;
    fetchDrafts();
  }, [hydrateRoom, roomId]);
}
