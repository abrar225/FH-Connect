"use client";

import { useEffect, useRef, useCallback } from "react";
import { useDraftStore } from "@/app/store/draftStore";

import { authWsUrl } from "@/app/lib/api";
export function useMeetingSocket(roomId: string, userId: string = "") {
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);
  const backoffRef = useRef(1000);
  const retryCount = useRef(0);
  
  const addDraft = useDraftStore((state) => state.addDraft);
  const updateDraft = useDraftStore((state) => state.updateDraft);
  const removeDraft = useDraftStore((state) => state.removeDraft);
  const setWsStatus = useDraftStore((state) => state.setWsStatus);
  const setPulse = useDraftStore((state) => state.setPulse);
  const setIsAdmin = useDraftStore((state) => state.setIsAdmin);
  const setIsLocked = useDraftStore((state) => state.setIsLocked);
  const setAgenda = useDraftStore((state) => state.setAgenda);
  const addInsight = useDraftStore((state) => state.addInsight);
  const updateInsight = useDraftStore((state) => state.updateInsight);
  const addChatMessage = useDraftStore((state) => state.addChatMessage);
  const incrementUnreadChat = useDraftStore((state) => state.incrementUnreadChat);
  const addClarification = useDraftStore((state) => state.addClarification);
  const removeClarification = useDraftStore((state) => state.removeClarification);
  const addDraftStoreTranscription = useDraftStore((state) => state.addTranscription);
  const updateDraftStoreTranscription = useDraftStore((state) => state.updateTranscription);


  const connect = useCallback(() => {
    if (!roomId) return;
    if (ws.current?.readyState === WebSocket.OPEN || ws.current?.readyState === WebSocket.CONNECTING) return;
    
    setWsStatus("connecting");
    authWsUrl(`/ws/${roomId}`).then((wsUrl) => {
      ws.current = new WebSocket(wsUrl);

      ws.current.onopen = () => {
      setWsStatus("connected");
      backoffRef.current = 1000; // Reset backoff on success
      retryCount.current = 0; // Reset retries on success
      };

      ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const eventRoomId = data.room_id || data.payload?.room_id || data.agenda?.room_id || data.insight?.room_id;
        const activeRoomId = useDraftStore.getState().activeRoomId;
        if (eventRoomId && activeRoomId && eventRoomId !== activeRoomId) {
          return;
        }
        // --- Handle Meeting Pulse broadcasts (Phase 2) ---
        if (data.type === "pulse") {
          setPulse({
            status: data.status || "Waiting for conversation...",
            speaker_perspectives: data.speaker_perspectives || {},
          });
          return;
        }

        // --- Handle Admin Update broadcasts (Phase 3) ---
        if (data.type === "admin_update") {
          const admins: string[] = data.admins || [];
          const currentUserId = useDraftStore.getState().userId;
          setIsAdmin(admins.includes(currentUserId));
          return;
        }

        // --- Handle Lock Update broadcasts (Phase 4) ---
        if (data.type === "lock_update") {
          setIsLocked(data.is_locked);
          return;
        }

        if (data.type === "agenda_updated") {
          setAgenda({
            room_id: data.agenda?.room_id,
            goals: data.agenda?.goals || [],
            agenda_items: data.agenda?.agenda_items || [],
            expected_decisions: data.agenda?.expected_decisions || [],
            attendees: data.agenda?.attendees || [],
            prep_docs: data.agenda?.prep_docs || [],
          });
          return;
        }

        if (data.type === "insight_created") {
          addInsight(data.insight);
          return;
        }

        if (data.type === "insight_updated") {
          updateInsight(data.insight.id, data.insight);
          return;
        }

        if (data.type === "report_status") {
          useDraftStore.getState().setReportStatus({
            status: data.status,
            has_report: data.status === "completed",
            report_error: data.error,
          });
          return;
        }

        if (data.type === "intent_clarification_required") {
          addClarification({
            id: data.event_id || data.id || `clarification-${data.room_id || roomId}-${data.trace_id || Date.now()}`,
            room_id: data.room_id || roomId,
            text: data.text || "",
            speaker: data.speaker || null,
            proposed_action: data.proposed_action || null,
            proposed_payload: data.proposed_payload || null,
            confidence: data.confidence ?? null,
            status: data.status || "pending",
          });
          return;
        }

        if (data.type === "clarification_status") {
          if (data.id) removeClarification(data.id);
          return;
        }

        // --- Handle Chat messages ---
        if (data.type === "chat") {
          addChatMessage(data);
          if (useDraftStore.getState().activeTab !== "chat") {
            incrementUnreadChat();
          }
          return;
        }

        // --- Handle Transcript Broadcasts (Live Captions) ---
        if (data.type === "transcript" || data.type === "TRANSCRIPT_INTERIM" || data.type === "TRANSCRIPT_FINAL") {
          const transcriptPayload = data.payload || data;
          const transcriptions = useDraftStore.getState().transcriptions;
          const exists = transcriptions.some((t) => t.id === transcriptPayload.id);
          
          if (exists) {
            updateDraftStoreTranscription(transcriptPayload.id, transcriptPayload.text);
          } else {
            addDraftStoreTranscription({
              id: transcriptPayload.id,
              text: transcriptPayload.text,
              speaker: transcriptPayload.speaker || "Unknown",
              timestamp: transcriptPayload.timestamp || new Date().toLocaleTimeString(),
            });
          }
          return;
        }
        // --- Handle Draft Status Broadcasts (Approve/Reject) ---
        if (data.type === "draft_status") {
          const currentDrafts = useDraftStore.getState().drafts;
          const exists = currentDrafts.some((d) => d.id === data.id);
          if (exists) {
            updateDraft(data.id, { status: data.status });
          } else {
            // Draft may not exist locally yet (participant joined late) — add it
            addDraft({
              id: data.id,
              room_id: data.room_id || roomId,
              title: data.title,
              assignee: data.assignee,
              deadline: data.deadline,
              status: data.status,
              original_transcript: data.original_transcript || "",
            });
          }
          return;
        }

        // --- Handle Draft CRUD (existing logic) ---
        // 1. Handle explicit cancellations
        if (data.action === "CANCEL") {
          removeDraft(data.id);
          return;
        }

        // 2. Handle CREATE or UPDATE
        if (data.id && data.title) {
          // Re-fetch current state to check existence
          const currentDrafts = useDraftStore.getState().drafts;
          const exists = currentDrafts.some(d => d.id === data.id);
          
          if (exists) {
            updateDraft(data.id, data);
          } else {
            addDraft(data);
          }
        }
      } catch {
        setWsStatus("error");
      }
      };

      ws.current.onclose = () => {
      if (retryCount.current >= 5) {
        setWsStatus("error");
        return;
      }

      setWsStatus("connecting");
      retryCount.current += 1;
      
      // Auto-reconnect with exponential backoff (max 10s)
      if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = setTimeout(() => {
        backoffRef.current = Math.min(backoffRef.current * 1.5, 10000);
        connect();
      }, backoffRef.current);
      };
    
      ws.current.onerror = () => {
        setWsStatus("error");
      };
    });
  }, [
    addChatMessage,
    addClarification,
    addDraft,
    addDraftStoreTranscription,
    addInsight,
    incrementUnreadChat,
    removeDraft,
    removeClarification,
    roomId,
    setIsAdmin,
    setIsLocked,
    setAgenda,
    setPulse,
    setWsStatus,
    updateDraft,
    updateDraftStoreTranscription,
    updateInsight,
  ]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current);
      if (ws.current) {
        ws.current.onclose = null; // Prevent reconnect on unmount
        ws.current.close();
      }
    };
  }, [connect]);

  return { ws: ws.current };
}
