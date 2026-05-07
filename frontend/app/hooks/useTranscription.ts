"use client";

import { useEffect, useRef, useCallback } from "react";
import { useDraftStore } from "@/app/store/draftStore";

import { authFetch } from "@/app/lib/api";

/**
 * useTranscription — Captures speech via Deepgram's Real-time WebSocket SDK.
 *
 * @param isMicEnabled — When false, recording is paused.
 * @param participantName — The name of the local participant for attribution.
 * @param userId - The ID of the authenticated user.
 * @param roomId - The active meeting room ID.
 * @param activeUsers - Current active participants in the meeting.
 * @param onTranscript — Optional callback for each new final transcript line.
 */
export function useTranscription(
  isMicEnabled: boolean, 
  participantName: string = "You",
  userId: string = "",
  roomId: string = "",
  activeUsers: string[] = [],
  onTranscript?: (text: string) => void
) {
  const socketRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const addTranscription = useDraftStore((state) => state.addTranscription);
  const updateTranscription = useDraftStore((state) => state.updateTranscription);
  const setSpeechStatus = useDraftStore((state) => state.setSpeechStatus);
  const currentSentenceId = useRef<string>(crypto.randomUUID());

  const activeUsersRef = useRef(activeUsers);
  useEffect(() => {
    activeUsersRef.current = activeUsers;
  }, [activeUsers]);

  const sendToBackend = useCallback(
    async (text: string, isFinal: boolean) => {
      if (!text.trim()) return;

      const sentenceId = currentSentenceId.current;
      const transcriptObject = {
        id: sentenceId,
        text: text.trim(),
        speaker: participantName,
        timestamp: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        }),
      };

      const transcriptions = useDraftStore.getState().transcriptions;
      if (transcriptions.some((t) => t.id === sentenceId)) {
        updateTranscription(sentenceId, text.trim());
      } else {
        addTranscription(transcriptObject);
      }

      if (isFinal) {
        currentSentenceId.current = crypto.randomUUID(); // generate new ID for the next sentence
        if (onTranscript) onTranscript(text.trim());
      }

      try {
        await authFetch("/api/transcript", {
          method: "POST",
          body: JSON.stringify({ 
            text: text.trim(),
            speaker: participantName,
            room_id: roomId,
            active_users: activeUsersRef.current,
            is_final: isFinal,
            id: sentenceId,
          }),
        });
      } catch {
        setSpeechStatus("error", "Unable to send transcript");
      }
    },
    [addTranscription, updateTranscription, participantName, roomId, onTranscript, setSpeechStatus]
  );

  const startStreaming = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0 && socketRef.current?.readyState === 1) {
          socketRef.current.send(event.data);
        }
      };

      mediaRecorder.start(250); // Send 250ms chunks
    } catch {
      setSpeechStatus("error", "Unable to access microphone");
    }
  }, [setSpeechStatus]);

  const startDeepgram = useCallback(async () => {
    try {
      setSpeechStatus("listening", null);
      
      // 1. Fetch temp token
      const res = await authFetch("/api/deepgram/token");
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setSpeechStatus("error", err.detail || "Transcription service is not configured");
        return;
      }
      const { token } = await res.json();
      if (!token) {
        setSpeechStatus("error", "Transcription service did not return a usable token");
        return;
      }
      
      // 2. Open WebSocket with interim results
      const socket = new WebSocket("wss://api.deepgram.com/v1/listen?smart_format=true&model=nova-2&interim_results=true", ["token", token]);
      socketRef.current = socket;

      socket.onopen = () => {
        startStreaming();
      };

      socket.onmessage = (message) => {
        const data = JSON.parse(message.data);
        const transcript = data.channel?.alternatives[0]?.transcript;
        if (transcript) {
          sendToBackend(transcript, data.is_final);
        }
      };

      socket.onerror = () => setSpeechStatus("error", "Transcription connection failed");
      socket.onclose = () => setSpeechStatus("stopped", null);

    } catch {
      setSpeechStatus("error", "Failed to connect to transcription engine");
    }
  }, [sendToBackend, setSpeechStatus, startStreaming]);

  const stopActiveSession = useCallback(() => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(t => t.stop());
      mediaRecorderRef.current = null;
    }
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }
    setSpeechStatus("stopped", null);
  }, [setSpeechStatus]);

  useEffect(() => {
    if (isMicEnabled) {
      startDeepgram();
    } else {
      stopActiveSession();
      setSpeechStatus("stopped", "Microphone is muted. Unmute to generate transcript, pulse, and tasks.");
    }
    return () => stopActiveSession();
  }, [isMicEnabled, startDeepgram, stopActiveSession, setSpeechStatus]);
}
