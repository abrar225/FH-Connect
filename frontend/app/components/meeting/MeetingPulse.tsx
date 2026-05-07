"use client";

import React, { useEffect } from "react";
import { motion } from "framer-motion";
import { useDraftStore } from "@/app/store/draftStore";
import { Activity } from "lucide-react";

import { authFetch } from "@/app/lib/api";

/**
 * MeetingPulse — A premium UI widget that displays AI-generated real-time 
 * status and key decisions made during the meeting.
 * 
 * Only the admin polls the backend for pulse updates. All participants
 * receive the results via WebSocket broadcast.
 */
interface MeetingPulseProps {
  isAdmin?: boolean;
  roomId?: string;
}

export default function MeetingPulse({ isAdmin: isAdminProp = false, roomId = "" }: MeetingPulseProps) {
  const { pulse, setPulse, transcriptions, speechStatus, aiHealth } = useDraftStore();
  const storeIsAdmin = useDraftStore((state) => state.isAdmin);

  // Use reactive store value (updated via WebSocket), fallback to prop
  const isAdmin = storeIsAdmin || isAdminProp;

  // Only admin polls for updates — results are broadcast to everyone via WebSocket
  useEffect(() => {
    if (!isAdmin || aiHealth.overall !== "ready" || transcriptions.length === 0) return;

    const fetchSummary = async () => {
      try {
        const textOnly = transcriptions.map((t) => `${t.speaker}: ${t.text}`);
        const res = await authFetch("/api/summary", {
          method: "POST",
          body: JSON.stringify({ transcripts: textOnly, room_id: roomId }),
        });
        if (res.ok) {
          const data = await res.json();
          setPulse(data);
        }
      } catch {
        // The previous pulse remains visible until the next successful update.
      }
    };

    // Initial fetch
    fetchSummary();

    const interval = setInterval(fetchSummary, 30000);
    return () => clearInterval(interval);
  }, [isAdmin, aiHealth.overall, transcriptions.length, setPulse, transcriptions, roomId]);

  const pipelineBlocked = aiHealth.overall === "unavailable";

  return (
    <div className="space-y-4 mb-6">
      {/* Pulse Header */}
      <div className="flex items-center justify-between px-1">
        <div className="flex items-center space-x-2">
          <Activity className="w-4 h-4 text-primary animate-pulse" />
          <h3 className="text-sm font-semibold text-white tracking-wide uppercase">
            Meeting Pulse
          </h3>
        </div>
      </div>

      {/* Content Card */}
      <div className="glass-panel p-4 rounded-2xl border border-white/5 bg-white/[0.02] space-y-4">
        {/* Status Section */}
        <div className="space-y-1.5">
          <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest pl-1">
            Current Status
          </p>
          <div className="bg-white/[0.03] rounded-xl p-3 border border-white/[0.05]">
            <p className="text-sm text-gray-200 leading-relaxed italic">
              &quot;{pipelineBlocked ? "Waiting for conversation..." : pulse.status}&quot;
            </p>
          </div>
        </div>

        {/* Perspectives Section */}
        {!pipelineBlocked && pulse.speaker_perspectives && Object.keys(pulse.speaker_perspectives).length > 0 && (
          <div className="space-y-2 pt-1 border-t border-white/5">
            <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest pl-1">
              Speaker Stances
            </p>
            <div className="space-y-2">
              {Object.entries(pulse.speaker_perspectives).map(([speaker, pov]) => (
                <div key={speaker} className="flex items-start space-x-2 px-1">
                  <div className="w-1.5 h-1.5 rounded-full bg-primary/40 mt-1.5 shrink-0" />
                  <p className="text-xs text-gray-400 leading-tight">
                    <span className="text-primary font-semibold">{speaker}: </span>
                    {pov}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
