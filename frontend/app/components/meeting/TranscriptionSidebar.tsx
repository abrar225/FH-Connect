"use client";

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  useLocalParticipant,
  useRemoteParticipants
} from "@livekit/components-react";
import {
  Check,
  Mic,
  MicOff,
  WifiOff,
  Settings,
  Sparkles,
  X,
  AlertTriangle,
} from "lucide-react";
import { IntentClarification, TaskDraft, useDraftStore } from "@/app/store/draftStore";
import MeetingPulse from "./MeetingPulse";
import DraftCard from "./DraftCard";
import { GlassContainer } from "@/app/components/ui/GlassContainer";
import { authFetch } from "@/app/lib/api";

export default function TranscriptionSidebar({ onClose, isAdmin, roomId }: { onClose: () => void, isAdmin?: boolean, roomId?: string }) {
  const { transcriptions, drafts, clarifications, wsStatus, speechStatus, speechError, aiHealth } = useDraftStore();
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
              {drafts.length + clarifications.length} DETECTED
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
                  {(drafts.length > 0 || clarifications.length > 0) && !pipelineBlocked ? (
                    <>
                      {clarifications.map((clarification: IntentClarification, index: number) => (
                        <ClarificationCard
                          key={clarification.id}
                          clarification={clarification}
                          isAdmin={isAdmin}
                          activeUsers={activeUsers}
                          index={index}
                        />
                      ))}
                      {drafts.map((draft: TaskDraft, index: number) => (
                        <DraftCard
                          key={draft.id}
                          draft={draft}
                          isAdmin={isAdmin}
                          activeUsers={activeUsers}
                          index={index + clarifications.length}
                        />
                      ))}
                    </>
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

function ClarificationCard({
  clarification,
  isAdmin = false,
  activeUsers = [],
  index = 0,
}: {
  clarification: IntentClarification;
  isAdmin?: boolean;
  activeUsers?: string[];
  index?: number;
}) {
  const removeClarification = useDraftStore((state) => state.removeClarification);
  const [title, setTitle] = React.useState(clarification.proposed_payload?.title || clarification.text || "");
  const [assignee, setAssignee] = React.useState(clarification.proposed_payload?.assignee || "");
  const [deadline, setDeadline] = React.useState(clarification.proposed_payload?.deadline || "");
  const [busy, setBusy] = React.useState(false);

  const reject = async () => {
    setBusy(true);
    try {
      await authFetch("/api/approval/clarifications/reject", {
        method: "POST",
        body: JSON.stringify({ id: clarification.id, room_id: clarification.room_id }),
      });
      removeClarification(clarification.id);
    } finally {
      setBusy(false);
    }
  };

  const accept = async () => {
    setBusy(true);
    try {
      await authFetch("/api/approval/clarifications/accept", {
        method: "POST",
        body: JSON.stringify({
          id: clarification.id,
          room_id: clarification.room_id,
          title,
          assignee: assignee || null,
          deadline: deadline || null,
        }),
      });
      removeClarification(clarification.id);
    } finally {
      setBusy(false);
    }
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 24, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.96 }}
      transition={{ type: "spring", stiffness: 380, damping: 30, delay: index * 0.04 }}
      className="relative flex flex-col gap-3 rounded-2xl border border-amber-500/20 bg-amber-500/10 p-4"
    >
      <div className="flex items-start gap-3">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-300" />
        <div className="min-w-0 flex-1">
          <p className="text-xs font-bold uppercase tracking-widest text-amber-200">Clarify Intent</p>
          <p className="mt-1 text-xs leading-relaxed text-white/60">{clarification.text}</p>
        </div>
      </div>

      {isAdmin ? (
        <div className="space-y-2">
          <input
            className="w-full rounded-lg border border-white/10 bg-black/20 px-3 py-1.5 text-sm text-white focus:border-primary focus:outline-none"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Task description"
          />
          <div className="flex items-center gap-2">
            <select
              value={assignee}
              onChange={(event) => setAssignee(event.target.value)}
              className="min-w-0 flex-1 rounded-lg border border-white/10 bg-black/20 px-2 py-1.5 text-xs text-gray-300 focus:border-primary focus:outline-none"
            >
              <option value="">No assignee</option>
              {activeUsers.map((user) => (
                <option key={user} value={user}>{user}</option>
              ))}
              {assignee && !activeUsers.includes(assignee) && <option value={assignee}>{assignee}</option>}
            </select>
            <input
              className="min-w-0 flex-1 rounded-lg border border-white/10 bg-black/20 px-2 py-1.5 text-xs text-gray-300 focus:border-primary focus:outline-none"
              value={deadline}
              onChange={(event) => setDeadline(event.target.value)}
              placeholder="Deadline"
            />
          </div>
          <div className="flex items-center gap-2 border-t border-white/10 pt-3">
            <button
              onClick={reject}
              disabled={busy}
              className="flex-1 rounded-xl bg-white/5 px-3 py-2 text-xs font-bold uppercase tracking-wider text-gray-400 transition-colors hover:bg-red-500/10 hover:text-red-300 disabled:opacity-50"
            >
              Reject
            </button>
            <button
              onClick={accept}
              disabled={busy || !title.trim()}
              className="flex-[2] inline-flex items-center justify-center gap-1.5 rounded-xl bg-emerald-500/20 px-3 py-2 text-xs font-bold uppercase tracking-wider text-emerald-300 transition-colors hover:bg-emerald-500 hover:text-white disabled:opacity-50"
            >
              <Check className="h-3.5 w-3.5" />
              <span>Approve</span>
            </button>
          </div>
        </div>
      ) : (
        <p className="text-[10px] font-bold uppercase tracking-wider text-white/35">Waiting for an admin decision</p>
      )}
    </motion.div>
  );
}
