"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "../context/AuthContext";
import { motion } from "framer-motion";
import { Video, CalendarPlus, Key, Clock, ClipboardList, AlertTriangle, FileText } from "lucide-react";
import { useRouter } from "next/navigation";
import { authFetch } from "@/app/lib/api";
import JoinMeetingModal from "../components/dashboard/JoinMeetingModal";
import ScheduleMeetingModal from "../components/dashboard/ScheduleMeetingModal";

// Utility to generate a 9-letter code (abc-def-ghi)
const generateMeetingId = () => {
  const chars = "abcdefghijklmnopqrstuvwxyz";
  const randomBytes = new Uint8Array(9);
  crypto.getRandomValues(randomBytes);
  let result = "";
  for (let i = 0; i < 9; i++) {
    if (i > 0 && i % 3 === 0) result += "-";
    result += chars.charAt(randomBytes[i] % chars.length);
  }
  return result;
};

export default function DashboardPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [isCreating, setIsCreating] = useState(false);
  const [isJoinOpen, setIsJoinOpen] = useState(false);
  const [isScheduleOpen, setIsScheduleOpen] = useState(false);
  const [recentMeetings, setRecentMeetings] = useState<any[]>([]);
  const [actions, setActions] = useState<any[]>([]);
  const [createError, setCreateError] = useState("");

  const fetchMeetings = useCallback(async () => {
    if (!user) return;
    const [meetingsRes, actionsRes] = await Promise.all([
      authFetch("/api/meetings"),
      authFetch("/api/actions"),
    ]);
    if (meetingsRes.ok) {
      const meetings = await meetingsRes.json();
      setRecentMeetings(meetings.slice(0, 5));
    }
    if (actionsRes.ok) setActions(await actionsRes.json());
  }, [user]);

  useEffect(() => {
    fetchMeetings();
  }, [fetchMeetings]);

  const handleNewMeeting = async () => {
    if (!user) return;
    setIsCreating(true);
    setCreateError("");
    
    const roomId = generateMeetingId();
    
    // Create meeting via backend API (bypasses Supabase RLS)
    try {
      const resp = await authFetch("/api/meeting/create", {
        method: "POST",
        body: JSON.stringify({
          room_id: roomId,
          title: "Instant Meeting",
        }),
      });
      const result = await resp.json();
      if (!resp.ok) {
        setCreateError(result?.detail || "Failed to create meeting.");
        setIsCreating(false);
        return;
      }
    } catch (err) {
      setCreateError("Failed to create meeting.");
      setIsCreating(false);
      return;
    }

    setIsCreating(false);
    router.push(`/room/${roomId}`);
  };

  const name = user?.name?.split(" ")[0] || "User";
  const openActions = actions.filter((item) => item.status !== "completed" && item.status !== "resolved").length;
  const overdueActions = actions.filter((item) => item.deadline && new Date(item.deadline) < new Date() && item.status !== "completed").length;
  const upcomingMeetings = recentMeetings.filter((item) => item.status === "scheduled").length;
  const reportsProcessing = recentMeetings.filter((item) => item.report_status === "queued" || item.report_status === "processing").length;

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Modals */}
      <JoinMeetingModal isOpen={isJoinOpen} onClose={() => setIsJoinOpen(false)} />
      <ScheduleMeetingModal isOpen={isScheduleOpen} onClose={() => {
        setIsScheduleOpen(false);
        fetchMeetings(); // refresh list
      }} />

      {/* ─── GREETING ─── */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="mb-10"
      >
        <h1 className="text-3xl font-bold tracking-tight text-white mb-2">
          Welcome back, {name}
        </h1>
        <p className="text-gray-400">
          What would you like to do today?
        </p>
        {createError && <p className="text-red-400 text-sm mt-3">{createError}</p>}
      </motion.div>

      {/* ─── QUICK ACTIONS ─── */}
      <div className="grid md:grid-cols-3 gap-6 mb-12">
        {/* New Meeting */}
        <motion.button
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          onClick={handleNewMeeting}
          disabled={isCreating}
          className="group relative flex flex-col p-6 rounded-2xl bg-gradient-to-br from-primary/10 to-indigo-600/10 border border-primary/20 hover:border-primary/40 transition-all text-left overflow-hidden h-40"
        >
          <div className="absolute top-0 right-0 w-32 h-32 bg-primary/10 rounded-full blur-2xl -mr-10 -mt-10 transition-transform group-hover:scale-150" />
          <div className="w-12 h-12 rounded-xl bg-primary/20 flex items-center justify-center mb-auto shadow-inner text-primary">
            {isCreating ? (
              <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            ) : (
              <Video className="w-6 h-6" />
            )}
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">New Meeting</h3>
            <p className="text-sm text-gray-400">Start an instant meeting</p>
          </div>
        </motion.button>

        {/* Join Meeting */}
        <motion.button
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          onClick={() => setIsJoinOpen(true)}
          className="group relative flex flex-col p-6 rounded-2xl bg-surface/40 hover:bg-surface/60 border border-white/5 hover:border-white/10 transition-all text-left overflow-hidden h-40"
        >
          <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center mb-auto shadow-inner text-emerald-400">
            <Key className="w-6 h-6 group-hover:-rotate-12 transition-transform" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Join Meeting</h3>
            <p className="text-sm text-gray-400">Enter a room code or link</p>
          </div>
        </motion.button>

        {/* Schedule Meeting */}
        <motion.button
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          onClick={() => setIsScheduleOpen(true)}
          className="group relative flex flex-col p-6 rounded-2xl bg-surface/40 hover:bg-surface/60 border border-white/5 hover:border-white/10 transition-all text-left overflow-hidden h-40"
        >
          <div className="w-12 h-12 rounded-xl bg-amber-500/10 flex items-center justify-center mb-auto shadow-inner text-amber-400">
            <CalendarPlus className="w-6 h-6 group-hover:scale-110 transition-transform" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Schedule Meeting</h3>
            <p className="text-sm text-gray-400">Plan ahead and invite others</p>
          </div>
        </motion.button>
      </div>

      <div className="grid gap-4 md:grid-cols-4 mb-12">
        <SummaryCard icon={ClipboardList} label="Open Actions" value={openActions} tone="text-sky-300" />
        <SummaryCard icon={AlertTriangle} label="Overdue" value={overdueActions} tone="text-red-300" />
        <SummaryCard icon={CalendarPlus} label="Upcoming" value={upcomingMeetings} tone="text-amber-300" />
        <SummaryCard icon={FileText} label="Reports Processing" value={reportsProcessing} tone="text-emerald-300" />
      </div>

      {/* ─── RECENT & UPCOMING ─── */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.4 }}
      >
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-white">Recent Meetings</h2>
        </div>

        <div className="space-y-3">
          {recentMeetings.length === 0 ? (
            <div className="p-8 rounded-2xl border border-white/5 bg-surface/20 flex flex-col items-center justify-center text-center">
              <div className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center mb-3">
                <Clock className="w-5 h-5 text-gray-500" />
              </div>
              <p className="text-gray-400">No recent meetings found.</p>
              <p className="text-sm text-gray-500 mt-1">Start a new meeting to see it here.</p>
            </div>
          ) : (
            recentMeetings.map((mtg, index) => (
              <div key={mtg.room_id || mtg.id || `meeting-${index}`} className="p-4 rounded-xl border border-white/5 bg-surface/40 flex items-center justify-between hover:bg-surface/60 transition-colors cursor-pointer" onClick={() => router.push(`/room/${mtg.room_id}`)}>
                <div className="flex items-center space-x-4">
                  <div className="w-10 h-10 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-400">
                    <Video className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="text-white font-medium">{mtg.title || "Meeting"}</h4>
                    <p className="text-xs text-gray-500 font-mono mt-0.5">{mtg.room_id}</p>
                  </div>
                </div>
                <div className="text-right flex flex-col items-end">
                  <span className="text-sm text-gray-400">
                     {new Date(mtg.started_at || mtg.scheduled_for || mtg.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                  </span>
                  <button className="text-xs text-primary mt-1 opacity-0 group-hover:opacity-100 transition-opacity">Rejoin</button>
                </div>
              </div>
            ))
          )}
        </div>
      </motion.div>
    </div>
  );
}

function SummaryCard({ icon: Icon, label, value, tone }: { icon: React.ElementType; label: string; value: number; tone: string }) {
  return (
    <div className="rounded-xl border border-white/10 bg-surface/40 p-4">
      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-400">{label}</span>
        <Icon className={`h-4 w-4 ${tone}`} />
      </div>
      <div className="mt-3 text-3xl font-bold text-white">{value}</div>
    </div>
  );
}
