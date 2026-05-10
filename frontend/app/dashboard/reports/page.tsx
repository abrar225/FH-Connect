"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { AlertCircle, CheckCircle2, Download, FileText, Link2, Loader2, Mail, Search, Trash2, Video } from "lucide-react";
import { motion } from "framer-motion";
import { API_BASE } from "@/app/lib/env";
import { authFetch } from "@/app/lib/api";
import { safeCopyText } from "@/app/lib/clipboard";

type ReportStatus = "none" | "queued" | "processing" | "completed" | "failed";
type ReportRow = {
  room_id: string;
  title?: string;
  report_content?: unknown;
  report_status?: ReportStatus;
  report_error?: string | null;
  report_requested_at?: string | null;
  ended_at?: string | null;
  quality_score?: number | null;
};

function statusOf(report: ReportRow): ReportStatus {
  if (report.report_status) return report.report_status;
  if (report.report_content) return "completed";
  if (report.report_requested_at) return "queued";
  return "none";
}

function ReportStatusBadge({ status }: { status: ReportStatus }) {
  const styles: Record<ReportStatus, string> = {
    none: "bg-white/5 text-gray-500 border-white/10",
    queued: "bg-sky-500/10 text-sky-300 border-sky-400/20",
    processing: "bg-amber-500/10 text-amber-300 border-amber-400/20",
    completed: "bg-emerald-500/10 text-emerald-300 border-emerald-400/20",
    failed: "bg-red-500/10 text-red-300 border-red-400/20",
  };
  const Icon = status === "completed" ? CheckCircle2 : status === "failed" ? AlertCircle : Loader2;
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-1 text-xs ${styles[status]}`}>
      <Icon className={`h-3.5 w-3.5 ${status === "queued" || status === "processing" ? "animate-spin" : ""}`} />
      {status === "none" ? "Not requested" : status[0].toUpperCase() + status.slice(1)}
    </span>
  );
}

export default function ReportsPage() {
  const [reports, setReports] = useState<ReportRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [message, setMessage] = useState("");

  const fetchReports = useCallback(async () => {
    setLoading(true);
    try {
      const res = await authFetch("/api/reports");
      setReports(res.ok ? await res.json() : []);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchReports();
  }, [fetchReports]);

  const filtered = useMemo(() => reports.filter((report) => `${report.title || ""} ${report.room_id}`.toLowerCase().includes(query.toLowerCase())), [query, reports]);

  const download = async (roomId: string, format: "markdown" | "pdf" | "docx") => {
    const res = await authFetch(`/api/reports/${roomId}/download?format=${format}`);
    if (!res.ok) {
      setMessage("Report download failed.");
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `Meeting_Report_${roomId}.${format === "markdown" ? "md" : format}`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const share = async (roomId: string) => {
    const res = await authFetch(`/api/reports/${roomId}/share`, {
      method: "POST",
      body: JSON.stringify({ expires_in_days: 30, allow_download: true }),
    });
    if (!res.ok) {
      setMessage("Share link could not be created.");
      return;
    }
    const data = await res.json();
    const link = `${API_BASE}/api/public/reports/${data.token}`;
    const copied = await safeCopyText(link);
    setMessage(copied ? "Secure report share link copied." : `Secure report share link created: ${link}`);
  };

  const email = async (roomId: string) => {
    const recipient = window.prompt("Send report to email");
    if (!recipient) return;
    const res = await authFetch(`/api/reports/${roomId}/email`, {
      method: "POST",
      body: JSON.stringify({ recipients: [recipient], message: "" }),
    });
    const data = res.ok ? await res.json() : null;
    setMessage(data?.status === "sent" ? "Report email sent." : "Email adapter is not configured yet.");
  };

  const deleteReport = async (roomId: string) => {
    if (!window.confirm("Are you sure you want to delete this report? This action cannot be undone.")) return;
    const res = await authFetch(`/api/reports/${roomId}`, { method: "DELETE" });
    if (res.ok) {
      setReports(reports.filter(r => r.room_id !== roomId));
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto h-full">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-white">Meeting Reports</h1>
        <p className="text-gray-400 mt-2">Search report history, track processing, export files, email summaries, and create secure share links.</p>
      </div>

      {message && <div className="mb-5 rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-gray-300">{message}</div>}

      <div className="mb-6 flex items-center gap-2 rounded-xl border border-white/10 bg-surface/40 px-3">
        <Search className="h-4 w-4 text-gray-500" />
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search reports" className="w-full bg-transparent py-2.5 text-sm text-white outline-none placeholder:text-gray-500" />
      </div>

      {loading ? (
        <div className="flex justify-center p-12"><div className="w-8 h-8 rounded-full border-2 border-primary border-t-transparent animate-spin" /></div>
      ) : filtered.length === 0 ? (
        <div className="p-12 rounded-xl border border-white/10 bg-surface/30 flex flex-col items-center text-center">
          <FileText className="w-12 h-12 text-gray-500 mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">No reports yet</h3>
          <p className="text-gray-400">End a meeting to generate your first structured report.</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filtered.map((report) => {
            const status = statusOf(report);
            const complete = status === "completed";
            return (
              <motion.div key={report.room_id} initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} className="rounded-xl border border-white/10 bg-surface/40 p-5">
                <div className="flex items-center space-x-3 mb-4">
                  <div className="w-10 h-10 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-400"><Video className="w-5 h-5" /></div>
                  <div className="min-w-0">
                    <h3 className="truncate font-medium text-white">{report.title || "Meeting"}</h3>
                    <p className="font-mono text-xs text-gray-500">{report.room_id}</p>
                  </div>
                </div>
                <div className="mb-4 flex items-center justify-between gap-3">
                  <ReportStatusBadge status={status} />
                  {report.quality_score != null && <span className="text-xs text-gray-400">Quality {report.quality_score}/100</span>}
                </div>
                {status === "failed" && report.report_error && <p className="mb-4 text-sm text-red-300">{report.report_error}</p>}
                <div className="grid grid-cols-3 gap-2">
                  {(["markdown", "pdf", "docx"] as const).map((format) => (
                    <button key={format} onClick={() => download(report.room_id, format)} disabled={!complete} className="rounded-lg border border-white/10 bg-white/5 px-2 py-2 text-xs font-semibold uppercase text-gray-300 disabled:opacity-40">
                      <Download className="mx-auto mb-1 h-3.5 w-3.5" />
                      {format === "markdown" ? "MD" : format}
                    </button>
                  ))}
                </div>
                <div className="mt-3 grid grid-cols-2 gap-2">
                  <button onClick={() => share(report.room_id)} disabled={!complete} className="inline-flex items-center justify-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs font-semibold text-gray-300 disabled:opacity-40"><Link2 className="h-3.5 w-3.5" /> Share</button>
                  <button onClick={() => email(report.room_id)} disabled={!complete} className="inline-flex items-center justify-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs font-semibold text-gray-300 disabled:opacity-40"><Mail className="h-3.5 w-3.5" /> Email</button>
                  <button onClick={() => deleteReport(report.room_id)} className="col-span-2 inline-flex items-center justify-center gap-2 rounded-lg border border-red-500/20 bg-red-500/10 px-3 py-2 text-xs font-semibold text-red-400 hover:bg-red-500/20"><Trash2 className="h-3.5 w-3.5" /> Delete Report</button>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}
