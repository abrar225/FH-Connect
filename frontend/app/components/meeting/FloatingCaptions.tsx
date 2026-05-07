"use client";

import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useDraftStore } from "@/app/store/draftStore";

/**
 * FloatingCaptions — Displays real-time captions overlaying the video stage.
 * Uses glassmorphism and subtle animations for a premium feel.
 */
export default function FloatingCaptions() {
  const transcriptions = useDraftStore((state) => state.transcriptions);
  const speechStatus = useDraftStore((state) => state.speechStatus);
  const showCaptions = useDraftStore((state) => state.showCaptions);
  const [activeCaption, setActiveCaption] = useState<{
    text: string;
    speaker: string;
    id: string;
  } | null>(null);

  // When a new transcription arrives, show it as a caption
  useEffect(() => {
    if (transcriptions.length > 0) {
      const lastLine = transcriptions[transcriptions.length - 1];
      setActiveCaption({
        text: lastLine.text,
        speaker: lastLine.speaker,
        id: lastLine.id,
      });

      // Clear the caption after 4 seconds of no activity
      const timer = setTimeout(() => {
        setActiveCaption(null);
      }, 4000);

      return () => clearTimeout(timer);
    }
  }, [transcriptions]);

  // Only hide when user explicitly disables captions.
  // We no longer hide when mic is stopped — other speakers' captions
  // still arrive via WebSocket and must remain visible.
  if (!showCaptions) return null;

  return (
    <div className="absolute bottom-36 left-1/2 -translate-x-1/2 z-50 w-full max-w-2xl px-6 pointer-events-none drop-shadow-2xl">
      <AnimatePresence mode="wait">
        {activeCaption && (
          <motion.div
            key={activeCaption.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.2 } }}
            className="flex flex-col items-center"
          >
            <div className="bg-black/85 backdrop-blur-md rounded-lg py-3 px-6 border border-white/10 text-center shadow-2xl">
              <span className="block text-[10px] uppercase tracking-widest text-primary/80 font-bold mb-1">
                {activeCaption.speaker}
              </span>
              <p className="text-white text-lg md:text-xl font-medium leading-normal tracking-wide">
                {activeCaption.text}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
