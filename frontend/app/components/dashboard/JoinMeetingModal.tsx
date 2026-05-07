"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Key, ArrowRight } from "lucide-react";
import { supabase } from "@/lib/supabase";
import { useRouter } from "next/navigation";

interface JoinMeetingModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function JoinMeetingModal({ isOpen, onClose }: JoinMeetingModalProps) {
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const executeJoin = async (targetCode: string) => {
    if (!targetCode.trim()) return;

    const cleanedCode = targetCode.trim().toLowerCase();

    setLoading(true);
    await new Promise((r) => setTimeout(r, 500)); // Brief simulated load for UI feedback
    setLoading(false);
    
    onClose();
    router.push(`/room/${cleanedCode}`);
  };

  const handleJoin = async (e: React.FormEvent) => {
    e.preventDefault();
    executeJoin(code);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let rawValue = e.target.value.toLowerCase();
    let isUrl = false;
    
    // Automatically extract code if a full URL is pasted
    if (rawValue.includes("/room/")) {
      const parts = rawValue.split("/room/");
      rawValue = parts[parts.length - 1].split("/")[0].split("?")[0];
      isUrl = true;
    }

    let val = rawValue.replace(/[^a-z0-9]/g, "");
    if (val.length > 9) val = val.substring(0, 9);
    
    // Formatting with hyphens
    let formatted = val;
    if (val.length > 3 && val.length <= 6) {
      formatted = `${val.slice(0, 3)}-${val.slice(3)}`;
    } else if (val.length > 6) {
      formatted = `${val.slice(0, 3)}-${val.slice(3, 6)}-${val.slice(6)}`;
    }
    
    setCode(formatted);
    setError(null);

    // Auto-join if a link was pasted and we extracted a likely code
    if (isUrl && val.length >= 3) {
      executeJoin(formatted);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
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
                onClick={onClose}
                className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors p-1"
              >
                <X className="w-5 h-5" />
              </button>

              <div className="flex items-center space-x-3 mb-6">
                <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-400">
                  <Key className="w-5 h-5" />
                </div>
                <h2 className="text-xl font-semibold text-white">Join Meeting</h2>
              </div>

              <form onSubmit={handleJoin} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1.5">
                    Meeting Code
                  </label>
                  <input
                    type="text"
                    value={code}
                    onChange={handleChange}
                    placeholder="abc-def-ghi"
                    className="w-full bg-background border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 font-mono text-center text-lg tracking-widest transition-all"
                    required
                  />
                  {error && <p className="text-red-400 text-sm mt-2">{error}</p>}
                </div>

                <div className="pt-2">
                  <button
                    type="submit"
                    disabled={loading || code.length < 3}
                    className="w-full flex items-center justify-center space-x-2 bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 disabled:cursor-not-allowed text-white px-4 py-3 rounded-xl font-medium transition-colors"
                  >
                    {loading ? (
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                      <>
                        <span>Join Room</span>
                        <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
