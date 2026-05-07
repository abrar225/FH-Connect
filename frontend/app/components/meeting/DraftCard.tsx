"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { Check, X, Calendar, User, Clock, Trash2, Edit3, Save } from "lucide-react";
import { TaskDraft, useDraftStore } from "@/app/store/draftStore";
import { authFetch } from "@/app/lib/api";

interface DraftCardProps {
  draft: TaskDraft;
  isAdmin?: boolean;
  activeUsers?: string[];
  index?: number;
}

export default function DraftCard({ draft, isAdmin = false, activeUsers = [], index = 0 }: DraftCardProps) {
  const { updateDraft, removeDraft } = useDraftStore();
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(draft.title);
  const [editAssignee, setEditAssignee] = useState(draft.assignee || "");
  const [editDeadline, setEditDeadline] = useState(draft.deadline || "");

  const handleApprove = async () => {
    updateDraft(draft.id, { status: "approved" });
    try {
      await authFetch("/api/approval/approve", {
        method: "POST",
        body: JSON.stringify({ id: draft.id, room_id: draft.room_id, assignee: draft.assignee }),
      });
    } catch {
      updateDraft(draft.id, { status: "pending" });
    }
  };
  
  const handleReject = async () => {
    updateDraft(draft.id, { status: "rejected" });
    try {
      await authFetch("/api/approval/reject", {
        method: "POST",
        body: JSON.stringify({ id: draft.id, room_id: draft.room_id }),
      });
    } catch {
      updateDraft(draft.id, { status: "pending" });
    }
  };
  
  const handleSave = () => {
    updateDraft(draft.id, {
      title: editTitle,
      assignee: editAssignee || null,
      deadline: editDeadline || null,
    });
    setIsEditing(false);
  };

  const isApproved = draft.status === "approved";
  const isRejected = draft.status === "rejected";

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 30, scale: 0.95 }}
      animate={{ 
        opacity: isRejected ? 0.5 : 1, 
        y: 0, 
        scale: 1,
        backgroundColor: isApproved 
          ? "rgba(16, 185, 129, 0.1)" 
          : isRejected 
            ? "rgba(239, 68, 68, 0.05)" 
            : "rgba(255, 255, 255, 0.03)"
      }}
      exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.2 } }}
      transition={{ 
        type: "spring", 
        stiffness: 400, 
        damping: 30,
        delay: index * 0.05
      }}
      whileHover={{ scale: 1.02 }}
      className={`relative flex flex-col p-4 rounded-2xl border transition-colors ${
        isApproved 
          ? "border-emerald-500/30" 
          : isRejected
            ? "border-red-500/20 grayscale"
            : "border-white/10 hover:border-white/20 shadow-[0_4px_20px_rgba(0,0,0,0.2)]"
      }`}
    >
      {/* Draft Content */}
      <div className="flex-1 space-y-3">
        {isEditing ? (
          <div className="space-y-2 pb-2">
            <input
              autoFocus
              className="w-full bg-black/20 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-primary"
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              placeholder="Task description..."
            />
            <div className="flex items-center space-x-2">
              <input
                className="w-1/2 bg-black/20 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-gray-300 focus:outline-none focus:border-primary"
                value={editAssignee}
                onChange={(e) => setEditAssignee(e.target.value)}
                placeholder="Assignee..."
              />
              <input
                className="w-1/2 bg-black/20 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-gray-300 focus:outline-none focus:border-primary"
                value={editDeadline}
                onChange={(e) => setEditDeadline(e.target.value)}
                placeholder="Deadline..."
              />
            </div>
            <div className="flex justify-end pt-1">
              <button
                onClick={handleSave}
                className="flex items-center space-x-1 px-3 py-1.5 bg-primary/20 text-primary hover:bg-primary/30 rounded-lg text-xs font-semibold transition-colors"
              >
                <Save className="w-3.5 h-3.5" />
                <span>Save Editable</span>
              </button>
            </div>
          </div>
        ) : (
          <>
            <div className="flex justify-between items-start">
              <h4 className={`text-sm font-medium leading-snug ${isRejected ? "line-through text-gray-500" : "text-gray-100"}`}>
                {draft.title}
              </h4>
              
              {isAdmin && !isApproved && !isRejected && (
                <button
                  onClick={() => setIsEditing(true)}
                  className="p-1 rounded-md text-gray-500 hover:text-white hover:bg-white/10 transition-colors"
                >
                  <Edit3 className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            <div className="flex items-center space-x-4">
              {isAdmin ? (
                <div className="flex items-center space-x-1.5 text-xs text-gray-400">
                  <User className="w-3.5 h-3.5" />
                  <select 
                    value={draft.assignee || ""}
                    onChange={(e) => updateDraft(draft.id, { assignee: e.target.value })}
                    className="bg-black/20 border border-white/10 rounded px-2 py-0.5 text-xs text-gray-300 focus:outline-none focus:border-primary appearance-none cursor-pointer"
                  >
                    <option value="" disabled>Select Assignee</option>
                    {activeUsers.map(user => (
                      <option key={user} value={user}>{user}</option>
                    ))}
                    {draft.assignee && !activeUsers.includes(draft.assignee) && (
                      <option value={draft.assignee}>{draft.assignee}</option>
                    )}
                  </select>
                </div>
              ) : (
                draft.assignee && (
                  <div className="flex items-center space-x-1.5 text-xs text-gray-400">
                    <User className="w-3.5 h-3.5" />
                    <span className="font-medium text-gray-300">{draft.assignee}</span>
                  </div>
                )
              )}
              {draft.deadline && (
                <div className="flex items-center space-x-1.5 text-xs text-gray-400">
                  <Calendar className="w-3.5 h-3.5" />
                  <span className="font-medium text-gray-300">{draft.deadline}</span>
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* Action Buttons (Only show if pending and isAdmin) */}
      {isAdmin && !isApproved && !isRejected && !isEditing && (
        <div className="flex items-center space-x-2 pt-4 mt-1 border-t border-white/5">
          <button
            onClick={handleReject}
            className="flex-1 flex items-center justify-center space-x-1.5 py-2 px-3 rounded-xl bg-white/5 text-gray-400 hover:bg-red-500/10 hover:text-red-400 transition-colors text-xs font-bold uppercase tracking-wider"
          >
            <X className="w-3.5 h-3.5" />
            <span>Discard</span>
          </button>
          <button
            onClick={handleApprove}
            disabled={!draft.assignee}
            className={`flex-[2] flex items-center justify-center space-x-1.5 py-2 px-3 rounded-xl text-xs font-bold uppercase tracking-wider ${
              !draft.assignee 
                ? "bg-gray-500/10 text-gray-500 opacity-50 cursor-not-allowed" 
                : "bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500 hover:text-white transition-all shadow-lg shadow-emerald-500/10 active:scale-95"
            }`}
          >
            <Check className="w-4 h-4" />
            <span>Approve Task</span>
          </button>
        </div>
      )}

      {/* Status Badge Layout */}
      {(isApproved || isRejected) && (
        <div className="absolute top-0 right-4 -translate-y-1/2 flex">
          <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-widest shadow-sm border ${
            isApproved 
              ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" 
              : "bg-red-500/20 text-red-400 border-red-500/30"
          }`}>
            {draft.status}
          </span>
        </div>
      )}
    </motion.div>
  );
}
