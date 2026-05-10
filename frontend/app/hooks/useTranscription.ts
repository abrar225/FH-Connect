"use client";

import { useEffect } from "react";
import { useDraftStore } from "@/app/store/draftStore";

/**
 * useTranscription — (Refactored) Server-side transcription pipeline.
 * This hook now only manages the UI speech status. Audio ingestion 
 * and transcription are handled entirely by the backend via LiveKit.
 *
 * @param isMicEnabled — When false, UI reflects paused state.
 */
export function useTranscription(isMicEnabled: boolean) {
  const setSpeechStatus = useDraftStore((state) => state.setSpeechStatus);

  useEffect(() => {
    if (isMicEnabled) {
      setSpeechStatus("listening", null);
    } else {
      setSpeechStatus("stopped", "Microphone is muted. Unmute to generate transcript, pulse, and tasks.");
    }
  }, [isMicEnabled, setSpeechStatus]);
}
