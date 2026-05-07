"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  FileText, 
  CheckCircle2, 
  ListTodo, 
  Download, 
  X,
  Trophy,
  Activity,
  Check,
  Trash2,
  Edit3,
  Save,
  Send,
  Loader2,
  ShieldCheck
} from "lucide-react";
import { useDraftStore, TaskDraft } from "@/app/store/draftStore";
import { useToast } from "@/app/components/ui/ToastProvider";
import ReactMarkdown from "react-markdown";

export default function ReportCard() {
  const { report, setReport, isAdmin, isReportFinalized, setIsReportFinalized } = useDraftStore();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [localTasks, setLocalTasks] = useState<TaskDraft[]>([]);
  const [isPublishing, setIsPublishing] = useState(false);
  const { toast } = useToast();

  // Initialize local tasks when report arrives
  React.useEffect(() => {
    if (report && localTasks.length === 0) {
      setLocalTasks(report.tasks);
    }
  }, [report, localTasks.length]);

  if (!report) return null;

  const handleTaskStatus = (id: string, status: "pending" | "approved" | "rejected") => {
    setLocalTasks(prev => prev.map(t => t.id === id ? { ...t, status } : t));
  };

  const handleTaskEdit = (id: string, updates: Partial<TaskDraft>) => {
    setLocalTasks(prev => prev.map(t => t.id === id ? { ...t, ...updates } : t));
  };

  const handlePublish = async () => {
    setIsPublishing(true);
    toast("info", "Publishing Report...", "Finalizing session data and syncing tasks.");
    
    try {
      // In a real app, this would hit /api/report/publish
      // We'll simulate a delay
      await new Promise(r => setTimeout(r, 1500));
      
      setIsReportFinalized(true);
      toast("success", "Report Published", "The final report is now visible to all participants.");
    } catch (e) {
      toast("error", "Publish Failed", "Could not finalize the report.");
    } finally {
      setIsPublishing(false);
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-black/80 backdrop-blur-md"
      >
        <motion.div
          initial={{ scale: 0.9, y: 20, opacity: 0 }}
          animate={{ scale: 1, y: 0, opacity: 1 }}
          className="relative w-full max-w-5xl h-[90vh] bg-surface-raised border border-white/10 rounded-[2.5rem] shadow-2xl flex flex-col overflow-hidden"
        >
          {/* Admin Badge */}
          {isAdmin && (
            <div className="absolute top-6 left-1/2 -translate-x-1/2 flex items-center space-x-2 px-3 py-1 bg-amber-500/20 border border-amber-500/30 rounded-full text-amber-400 text-[10px] font-bold uppercase tracking-widest z-10">
              <ShieldCheck className="w-3 h-3" />
              <span>Admin Governance Mode</span>
            </div>
          )}

          {/* Close Button */}
          <button 
            onClick={() => setReport(null)}
            className="absolute top-6 right-6 p-2 rounded-full bg-white/5 hover:bg-white/10 text-gray-400 transition-colors z-10"
          >
            <X className="w-5 h-5" />
          </button>

          {/* Header */}
          <div className="p-10 pb-6 border-b border-white/5 bg-gradient-to-br from-primary/10 via-transparent to-transparent shrink-0">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="p-2.5 bg-primary/20 rounded-2xl text-primary">
                  <FileText className="w-6 h-6" />
                </div>
                <div>
                  <h1 className="text-3xl font-bold tracking-tight text-white italic">Session Intelligence Report</h1>
                  <p className="text-gray-400 mt-1">Sprint Planning: Engineering Team Alpha</p>
                </div>
              </div>
              
              {isAdmin && !isReportFinalized && (
                <motion.button 
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handlePublish}
                  disabled={isPublishing}
                  className="flex items-center space-x-2 px-6 py-3 bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-white rounded-2xl font-bold text-sm transition-all shadow-lg shadow-emerald-500/20"
                >
                  {isPublishing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                  <span>Publish Final Report</span>
                </motion.button>
              )}
            </div>
          </div>

          {/* Scrollable Content */}
          <div className="flex-1 overflow-y-auto p-10 space-y-12 custom-scrollbar">
            
            {/* Executive Summary */}
            <section className="space-y-4">
              <div className="flex items-center space-x-2 text-primary font-bold tracking-widest text-xs uppercase opacity-70">
                <Trophy className="w-4 h-4" />
                <span>Executive Summary</span>
              </div>
              <p className="text-xl text-gray-100 leading-relaxed font-medium bg-white/5 p-6 rounded-[2rem] border border-white/5 italic">
                &quot;{report.executive_summary}&quot;
              </p>
            </section>

            {/* Smart Meeting Minutes */}
            <section className="space-y-4">
              <div className="flex items-center space-x-2 text-indigo-400 font-bold tracking-widest text-xs uppercase opacity-70">
                <FileText className="w-4 h-4" />
                <span>Smart Meeting Minutes</span>
              </div>
              <div className="prose prose-invert prose-emerald max-w-none text-gray-200 bg-white/5 p-8 rounded-[2rem] border border-white/5 shadow-inner 
                 prose-h1:text-2xl prose-h1:font-bold prose-h1:text-white prose-h1:mb-4
                 prose-h2:text-xl prose-h2:font-semibold prose-h2:text-gray-100 prose-h2:mt-6 prose-h2:mb-3
                 prose-h3:text-lg prose-h3:font-medium prose-h3:text-gray-200
                 prose-p:text-gray-300 prose-p:leading-relaxed prose-p:mb-4
                 prose-ul:list-disc prose-ul:pl-5 prose-ul:mb-4 prose-ul:text-emerald-100/80
                 prose-ol:list-decimal prose-ol:pl-5 prose-ol:mb-4
                 prose-li:mb-2
                 prose-strong:text-white prose-strong:font-bold">
                <ReactMarkdown>{report.meeting_minutes}</ReactMarkdown>
              </div>
            </section>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
              
              {/* Key Decisions */}
              <section className="space-y-5">
                <div className="flex items-center space-x-2 text-emerald-400 font-bold tracking-widest text-xs uppercase">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Key Decisions</span>
                </div>
                <div className="space-y-3">
                  {report.key_decisions.map((decision, i) => (
                    <div key={i} className="flex items-start space-x-3 bg-emerald-500/5 p-4 rounded-2xl border border-emerald-500/10">
                      <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-2 shrink-0 shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
                      <p className="text-sm text-emerald-100/80 leading-relaxed font-medium">{decision}</p>
                    </div>
                  ))}
                </div>
              </section>

              {/* Participation */}
              <section className="space-y-5">
                <div className="flex items-center space-x-2 text-blue-400 font-bold tracking-widest text-xs uppercase">
                  <Activity className="w-4 h-4" />
                  <span>Participation Flux</span>
                </div>
                <div className="bg-white/5 p-6 rounded-[2rem] border border-white/5 space-y-5">
                  {Object.entries(report.participation).map(([name, percent]) => (
                    <div key={name} className="space-y-2">
                      <div className="flex justify-between text-xs font-semibold">
                        <span className="text-gray-300">{name}</span>
                        <span className="text-blue-400">{percent}% Contribution</span>
                      </div>
                      <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                        <motion.div 
                          initial={{ width: 0 }}
                          animate={{ width: `${percent}%` }}
                          transition={{ duration: 1, ease: "easeOut" }}
                          className="h-full bg-gradient-to-r from-blue-600 to-indigo-400" 
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </section>

            </div>

            {/* Task Administration Grid */}
            <section className="space-y-6 pb-10">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2 text-amber-400 font-bold tracking-widest text-xs uppercase">
                  <ListTodo className="w-4 h-4" />
                  <span>Task Administration Board ({localTasks.length})</span>
                </div>
                {isAdmin && !isReportFinalized && (
                  <button 
                    onClick={() => setLocalTasks(prev => prev.map(t => ({ ...t, status: "approved" })))}
                    className="text-[10px] font-bold text-gray-500 hover:text-white uppercase tracking-tighter transition-colors"
                  >
                    Approve All Drafts
                  </button>
                )}
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                {localTasks.map((task) => (
                  <motion.div 
                    layout
                    key={task.id} 
                    className={`relative flex flex-col p-5 rounded-[2rem] border transition-all duration-300 ${
                      task.status === "approved" 
                        ? "bg-emerald-500/10 border-emerald-500/30" 
                        : task.status === "rejected"
                        ? "bg-red-500/10 border-red-500/20 grayscale opacity-60"
                        : "bg-surface-raised border-white/10 hover:border-white/20"
                    }`}
                  >
                    {editingId === task.id ? (
                      <input 
                        autoFocus
                        className="bg-transparent border-none text-white font-semibold text-sm mb-2 focus:ring-0 w-full"
                        defaultValue={task.title}
                        onBlur={(e) => {
                          handleTaskEdit(task.id, { title: e.target.value });
                          setEditingId(null);
                        }}
                      />
                    ) : (
                      <h4 className={`text-sm font-semibold mb-2 pr-6 ${task.status === "rejected" ? "line-through" : "text-white"}`}>
                        {task.title}
                      </h4>
                    )}

                    <div className="mt-auto pt-4 flex items-center justify-between border-t border-white/5">
                      <div className="flex items-center space-x-2">
                        <div className="w-7 h-7 rounded-full bg-primary/20 flex items-center justify-center text-[10px] text-white font-bold group">
                          {task.assignee?.charAt(0) || "?"}
                        </div>
                        <span className="text-xs font-medium text-gray-400">{task.assignee || "Unassigned"}</span>
                      </div>
                      
                      {isAdmin && !isReportFinalized && (
                        <div className="flex items-center space-x-1">
                          <motion.button 
                            whileHover={{ scale: 1.15, rotate: 5 }}
                            whileTap={{ scale: 0.9 }}
                            onClick={() => setEditingId(task.id)}
                            className="p-2 rounded-xl text-gray-500 hover:text-white hover:bg-white/5 transition-colors"
                          >
                            <Edit3 className="w-3.5 h-3.5" />
                          </motion.button>
                          <motion.button 
                            whileHover={{ scale: 1.15, y: -2 }}
                            whileTap={{ scale: 0.9 }}
                            onClick={() => handleTaskStatus(task.id, task.status === "rejected" ? "pending" : "rejected")}
                            className={`p-2 rounded-xl transition-colors ${task.status === "rejected" ? "text-red-400 bg-red-500/10" : "text-gray-500 hover:text-red-400 hover:bg-red-500/5"}`}
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </motion.button>
                          <motion.button 
                            whileHover={{ scale: 1.15, y: -2 }}
                            whileTap={{ scale: 0.9 }}
                            onClick={() => handleTaskStatus(task.id, task.status === "approved" ? "pending" : "approved")}
                            className={`p-2 rounded-xl transition-colors ${task.status === "approved" ? "text-emerald-400 bg-emerald-500/10" : "text-gray-500 hover:text-emerald-400 hover:bg-emerald-500/5"}`}
                          >
                            <Check className="w-3.5 h-3.5" />
                          </motion.button>
                        </div>
                      )}
                    </div>
                  </motion.div>
                ))}
              </div>
            </section>

          </div>

          {/* Footer Actions */}
          <div className="p-8 px-10 border-t border-white/5 bg-white/[0.02] flex items-center justify-between shrink-0">
            <div className="flex items-center space-x-4 text-[10px] text-gray-500 font-bold uppercase tracking-tighter">
              <span>FH-Connect Engine 3.1</span>
              <span>•</span>
              <span className={isReportFinalized ? "text-emerald-500" : "text-amber-500"}>
                {isReportFinalized ? "Finalized & Synced" : "Review in Progress"}
              </span>
            </div>
            
            <div className="flex items-center space-x-3">
              <motion.button 
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="px-6 py-2.5 bg-white/5 text-gray-400 rounded-2xl font-bold text-sm hover:bg-white/10 flex items-center space-x-2 transition-all border border-white/5"
                onClick={() => setReport(null)}
              >
                <span>Close Preview</span>
              </motion.button>
              <motion.button 
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="px-6 py-2.5 bg-white text-black rounded-2xl font-bold text-sm shadow-[0_0_20px_rgba(255,255,255,0.2)] flex items-center space-x-2 transition-all"
                onClick={() => window.print()}
              >
                <Download className="w-4 h-4" />
                <span>Export Report PDF</span>
              </motion.button>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
