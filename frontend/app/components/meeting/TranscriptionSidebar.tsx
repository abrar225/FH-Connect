"use client";

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  useLocalParticipant,
  useRemoteParticipants
} from "@livekit/components-react";
import {
  Mic,
  MicOff,
  WifiOff,
  Settings,
  Sparkles,
  X,
  AlertTriangle,
} from "lucide-react";
import { useDraftStore } from "@/app/store/draftStore";
import MeetingPulse from "./MeetingPulse";
import DraftCard from "./DraftCard";
import { GlassContainer } from "@/app/components/ui/GlassContainer";

export default function TranscriptionSidebar({ onClose, isAdmin, roomId }: { onClose: () => void, isAdmin?: boolean, roomId?: string }) {
  const { transcriptions, drafts, wsStatus, speechStatus, speechError, aiHealth } = useDraftStore();
  const { localParticipant, isMicrophoneEnabled } = useLocalParticipant();
  const remoteParticipants = useRemoteParticipants();
  const pipelineBlocked = aiHealth.overall === "unavailable";
  const primaryWarning = !isMicrophoneEnabled
    ? { icon: MicOff, label: "Muted", text: "Microphone is muted. Unmute to generate transcript, pulse, and tasks." }
    : aiHealth.overall === "unavailable"
      ? { icon: AlertTriangle, label: "AI offline", text: aiHealth.message }
      : wsStatus === "disconnected"
        ? { icon: WifiOff, label: "Offline", text: "Connection lost. Reconnecting to meeting intelligence..." }
        : speechStatus === "error" && speechError && !["aborted", "no-speech"].includes(speechError)
          ? { icon: AlertTriangle, label: "Speech error", text: speechError }
          : null;
  
  const activeUsers = [
    localParticipant.name || localParticipant.identity,
    ...remoteParticipants.map(p => p.name || p.identity)
  ].filter(Boolean) as string[];

  return (
    <GlassContainer intensity="high" className="w-full h-full flex flex-col overflow-hidden shadow-2xl relative rounded-none border-y-0 border-r-0 border-l border-white/5">
      {/* Background Glow */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 blur-[100px] rounded-full pointer-events-none" />

      {/* Static Header */}
      <div className="px-6 pt-6 pb-4 shrink-0 border-b border-white/5">
        <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-primary animate-pulse" />
              <h2 className="text-sm font-bold uppercase tracking-widest text-white/90">Meeting Intel</h2>
            </div>
            <button 
              onClick={onClose}
              className="p-1.5 rounded-lg hover:bg-white/5 text-white/30 hover:text-white transition-all"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="flex items-center justify-between">
            <p className="text-[10px] text-white/30 uppercase tracking-tighter">AI-Driven Real-time Analysis</p>
            <div className="px-2 py-0.5 rounded-full border border-white/10 bg-white/5 text-[9px] font-bold text-white/40">
              {drafts.length} DETECTED
            </div>
          </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-hidden flex flex-col relative">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex-1 flex flex-col p-6 overflow-y-auto custom-scrollbar"
            >
              <MeetingPulse isAdmin={isAdmin} roomId={roomId} />

              <div className="mt-8 space-y-4 relative flex-1">
                <AnimatePresence mode="popLayout">
                  {drafts.length > 0 && !pipelineBlocked ? (
                    drafts.map((draft: any, index: number) => <DraftCard key={draft.id} draft={draft} isAdmin={isAdmin} activeUsers={activeUsers} index={index} />)
                  ) : (
                    <motion.div 
                      key="empty"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="absolute inset-0 flex flex-col items-center justify-center text-center p-8"
                    >
                      <div className="w-16 h-16 rounded-3xl bg-white/5 border border-white/10 flex items-center justify-center mb-4">
                        <Mic className="w-8 h-8 text-white/20" />
                      </div>
                      <h3 className="text-white/80 font-semibold mb-1">Observation Mode</h3>
                      <p className="text-[10px] text-white/40 leading-relaxed uppercase tracking-wider">
                        Awaiting insights...
                      </p>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </motion.div>
      </div>

      {/* Sidebar Footer */}
      <div className="p-4 border-t border-white/5 bg-black/20 shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex min-w-0 flex-1 items-center space-x-2">
            {primaryWarning ? (
              <div
                title={primaryWarning.text}
                className="inline-flex max-w-full items-center gap-1.5 rounded-full border border-amber-500/25 bg-amber-500/10 px-2.5 py-1 text-amber-300"
              >
                <primaryWarning.icon className="w-3.5 h-3.5 shrink-0 text-amber-300" />
                <span className="truncate text-[10px] font-bold uppercase tracking-wide">
                  {primaryWarning.label}
                </span>
              </div>
            ) : (
              <>
                <div className={`w-1.5 h-1.5 rounded-full ${aiHealth.overall === "ready" && !pipelineBlocked ? "bg-emerald-500" : "bg-white/20"}`} />
                <span className="text-[10px] font-bold uppercase tracking-widest text-white/40">Meeting tools ready</span>
              </>
            )}
          </div>
          <button className="p-2 rounded-lg hover:bg-white/5 text-white/40 transition-colors">
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </div>
    </GlassContainer>
  );
}
