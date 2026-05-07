"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { CalendarPlus, ClipboardCopy, FileText, Search, Video } from "lucide-react";
import { motion } from "framer-motion";
import { authFetch } from "@/app/lib/api";
import { safeCopyText } from "@/app/lib/clipboard";
import ScheduleMeetingModal from "@/app/components/dashboard/ScheduleMeetingModal";

type MeetingRow = {
  room_id: string;
  title?: string;
  status?: "scheduled" | "live" | "ended" | "report_processing";
  scheduled_for?: string | null;
  started_at?: string | null;
  ended_at?: string | null;
  created_at?: string | null;
  report_status?: string | null;
  has_report?: boolean;
};

export default function MeetingsPage() {
  const router = useRouter();
  const [meetings, setMeetings] = useState<MeetingRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("all");
  const [scheduleOpen, setScheduleOpen] = useState(false);

  const loadMeetings = useCallback(async () => {
    setLoading(true);
    try {
      const res = await authFetch("/api/meetings");
      setMeetings(res.ok ? await res.json() : []);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadMeetings();
  }, [loadMeetings]);

  const filtered = useMemo(() => {
    return meetings.filter((meeting) => {
      const haystack = `${meeting.title || ""} ${meeting.room_id}`.toLowerCase();
      const matchesQuery = haystack.includes(query.toLowerCase());
      const matchesFilter = filter === "all" || meeting.status === filter || meeting.report_status === filter;
      return matchesQuery && matchesFilter;
    });
  }, [meetings, query, filter]);

  const copyLink = async (roomId: string) => {
    await safeCopyText(`${window.location.origin}/room/${roomId}`);
  };

  return (
    <div className="p-8 max-w-7xl mx-auto h-full">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Meetings</h1>
          <p className="text-gray-400 mt-2">Schedule, join, review reports, and jump into transcript recordings.</p>
        </div>
        <button onClick={() => setScheduleOpen(true)} className="inline-flex items-center justify-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-white">
          <CalendarPlus className="h-4 w-4" />
          Schedule
        </button>
      </div>

      <ScheduleMeetingModal isOpen={scheduleOpen} onClose={() => { setScheduleOpen(false); loadMeetings(); }} />

      <div className="flex flex-col gap-3 md:flex-row mb-6">
        <div className="flex flex-1 items-center gap-2 rounded-xl border border-white/10 bg-surface/40 px-3">
          <Search className="h-4 w-4 text-gray-500" />
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search meetings" className="w-full bg-transparent py-2.5 text-sm text-white outline-none placeholder:text-gray-500" />
        </div>
        <select value={filter} onChange={(event) => setFilter(event.target.value)} className="rounded-xl border border-white/10 bg-surface/80 px-3 py-2.5 text-sm text-white outline-none">
          <option value="all">All statuses</option>
          <option value="scheduled">Scheduled</option>
          <option value="live">Live</option>
          <option value="ended">Ended</option>
          <option value="queued">Report queued</option>
          <option value="processing">Report processing</option>
        </select>
      </div>

      {loading ? (
        <div className="p-12 text-center text-gray-400">Loading meetings...</div>
      ) : filtered.length === 0 ? (
        <div className="rounded-xl border border-white/10 bg-surface/30 p-10 text-center text-gray-400">No meetings found.</div>
      ) : (
        <div className="space-y-3">
          {filtered.map((meeting) => (
            <motion.div key={meeting.room_id} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="rounded-xl border border-white/10 bg-surface/40 p-4">
              <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div className="flex items-center gap-4 min-w-0">
                  <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-300">
                    <Video className="h-5 w-5" />
                  </div>
                  <div className="min-w-0">
                    <h2 className="truncate font-semibold text-white">{meeting.title || "Meeting"}</h2>
                    <p className="mt-1 truncate font-mono text-xs text-gray-500">{meeting.room_id}</p>
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded-md border border-white/10 bg-white/5 px-2 py-1 text-xs uppercase tracking-wide text-gray-300">{meeting.status || "scheduled"}</span>
                  <button onClick={() => router.push(`/room/${meeting.room_id}`)} className="rounded-lg bg-primary/20 px-3 py-2 text-xs font-semibold text-primary">Join</button>
                  <button onClick={() => copyLink(meeting.room_id)} className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs font-semibold text-gray-300 inline-flex items-center gap-1.5"><ClipboardCopy className="h-3.5 w-3.5" /> Copy</button>
                  {meeting.has_report && <button onClick={() => router.push("/dashboard/reports")} className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs font-semibold text-gray-300 inline-flex items-center gap-1.5"><FileText className="h-3.5 w-3.5" /> Report</button>}
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
