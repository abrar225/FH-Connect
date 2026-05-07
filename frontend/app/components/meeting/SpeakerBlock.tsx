"use client";

import React from "react";
import { motion } from "framer-motion";
import { TranscriptionLine } from "@/app/store/draftStore";
import { User, MessageSquare } from "lucide-react";

interface SpeakerBlockProps {
  speaker: string;
  lines: TranscriptionLine[];
  isLive?: boolean;
}

export default function SpeakerBlock({ speaker, lines, isLive }: SpeakerBlockProps) {
  if (lines.length === 0) return null;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.95, y: 10 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      className={`group relative rounded-2xl p-4 transition-all border ${
        isLive 
        ? "bg-primary/5 border-primary/20 shadow-lg shadow-primary/5" 
        : "bg-surface/40 border-white/5 hover:border-white/10"
      }`}
    >
      {/* Speaker Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2.5">
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors ${
            isLive ? "bg-primary/20 text-primary" : "bg-white/5 text-gray-400"
          }`}>
            <User className="w-4 h-4" />
          </div>
          <div>
            <span className={`text-xs font-bold tracking-wider transition-colors ${
              isLive ? "text-primary" : "text-gray-400"
            }`}>
              {speaker}
            </span>
            {isLive && (
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex items-center space-x-1.5 mt-0.5"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-[10px] text-emerald-400 uppercase font-bold tracking-tight">Speaking</span>
              </motion.div>
            )}
          </div>
        </div>
        <div className="text-[10px] text-gray-600 font-mono">
          {lines[lines.length - 1].timestamp}
        </div>
      </div>

      {/* Transcripts List */}
      <div className="space-y-2.5 pl-1.5 border-l-2 border-white/5 ml-4">
        {lines.map((line, idx) => (
          <motion.div
            key={line.id}
            initial={{ opacity: 0, x: -5 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: idx * 0.05 }}
            className="group/line flex items-start space-x-2"
          >
            <div className="mt-1.5 w-1 h-1 rounded-full bg-white/10 group-hover/line:bg-primary/40 transition-colors" />
            <p className="text-sm text-gray-300 leading-relaxed group-hover/line:text-white transition-colors">
              {line.text}
            </p>
          </motion.div>
        ))}
      </div>

      {/* Decorative Blur for Live Speaker */}
      {isLive && (
        <div className="absolute inset-0 pointer-events-none rounded-2xl ring-1 ring-primary/30 blur-[2px] opacity-20" />
      )}
    </motion.div>
  );
}
