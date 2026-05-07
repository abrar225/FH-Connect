"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, CalendarPlus, Check } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { authFetch } from "@/app/lib/api";
import { safeCopyText } from "@/app/lib/clipboard";

// Utility to generate a 9-letter code
const generateMeetingId = () => {
  const chars = "abcdefghijklmnopqrstuvwxyz";
  let result = "";
  for (let i = 0; i < 9; i++) {
    if (i > 0 && i % 3 === 0) result += "-";
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
};

interface ScheduleMeetingModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function ScheduleMeetingModal({ isOpen, onClose }: ScheduleMeetingModalProps) {
  const { user } = useAuth();
  const [title, setTitle] = useState("");
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [loading, setLoading] = useState(false);
  const [successCode, setSuccessCode] = useState<string | null>(null);

  const handleSchedule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user || !title || !date || !time) return;

    setLoading(true);
    
    // Combine date and time
    const scheduledDateTime = new Date(`${date}T${time}`).toISOString();
    const roomId = generateMeetingId();

    // Create meeting via backend API (bypasses Supabase RLS)
    try {
      const resp = await authFetch("/api/meetings/schedule", {
        method: "POST",
        body: JSON.stringify({
          room_id: roomId,
          title,
          scheduled_for: scheduledDateTime,
          agenda: {
            goals: [],
            agenda_items: [],
            expected_decisions: [],
            attendees: [],
            prep_docs: [],
          },
        }),
      });

      setLoading(false);

      if (!resp.ok) {
        alert("Failed to schedule meeting.");
      } else {
        setSuccessCode(roomId);
      }
    } catch (err) {
      setLoading(false);
      alert("Failed to schedule meeting.");
    }
  };

  const handleReset = () => {
    setTitle("");
    setDate("");
    setTime("");
    setSuccessCode(null);
    onClose();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={successCode ? handleReset : onClose}
            className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none"
          >
            <div className="w-full max-w-md bg-surface border border-white/10 rounded-2xl shadow-2xl p-6 pointer-events-auto relative">
              <button
                onClick={successCode ? handleReset : onClose}
                className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors p-1"
              >
                <X className="w-5 h-5" />
              </button>

              {successCode ? (
                <div className="text-center py-6">
                  <div className="w-16 h-16 rounded-full bg-emerald-500/10 flex items-center justify-center text-emerald-400 mx-auto mb-4">
                    <Check className="w-8 h-8" />
                  </div>
                  <h2 className="text-2xl font-bold text-white mb-2">Meeting Scheduled!</h2>
                  <p className="text-gray-400 mb-6">Share this code with your participants:</p>
                  
                  <div className="bg-background border border-white/10 p-4 rounded-xl flex items-center justify-between group cursor-copy" onClick={() => safeCopyText(successCode)}>
                    <span className="font-mono text-2xl tracking-widest text-primary flex-1">{successCode}</span>
                    <span className="text-xs text-gray-500 group-hover:text-white transition-colors">Copy</span>
                  </div>
                  
                  <button
                    onClick={handleReset}
                    className="mt-8 w-full bg-white/10 hover:bg-white/15 text-white px-4 py-3 rounded-xl font-medium transition-colors"
                  >
                    Done
                  </button>
                </div>
              ) : (
                <>
                  <div className="flex items-center space-x-3 mb-6">
                    <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center text-amber-400">
                      <CalendarPlus className="w-5 h-5" />
                    </div>
                    <h2 className="text-xl font-semibold text-white">Schedule Meeting</h2>
                  </div>

                  <form onSubmit={handleSchedule} className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-400 mb-1.5">
                        Meeting Title
                      </label>
                      <input
                        type="text"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        placeholder="e.g., Weekly Sync"
                        className="w-full bg-background border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder-gray-600 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500 transition-all"
                        required
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-400 mb-1.5">
                          Date
                        </label>
                        <input
                          type="date"
                          value={date}
                          onChange={(e) => setDate(e.target.value)}
                          className="w-full bg-background border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder-gray-600 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500 transition-all"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-400 mb-1.5">
                          Time
                        </label>
                        <input
                          type="time"
                          value={time}
                          onChange={(e) => setTime(e.target.value)}
                          className="w-full bg-background border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder-gray-600 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500 transition-all"
                          required
                        />
                      </div>
                    </div>

                    <div className="pt-4">
                      <button
                        type="submit"
                        disabled={loading || !title || !date || !time}
                        className="w-full flex items-center justify-center space-x-2 bg-amber-500 hover:bg-amber-600 disabled:opacity-50 disabled:cursor-not-allowed text-white px-4 py-3 rounded-xl font-medium transition-colors"
                      >
                        {loading ? (
                          <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        ) : (
                          <span>Schedule Now</span>
                        )}
                      </button>
                    </div>
                  </form>
                </>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
