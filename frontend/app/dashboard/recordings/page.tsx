"use client";

import React, { useCallback, useEffect, useState } from "react";
import { Download, FileText, Search, Timer } from "lucide-react";
import { authFetch } from "@/app/lib/api";

type RecordingRow = {
  room_id: string;
  title?: string;
  started_at?: string | null;
  ended_at?: string | null;
  transcript_count: number;
  has_report: boolean;
};

type TranscriptLine = {
  id: string;
  speaker: string;
  text: string;
  spoken_at?: string;
  timestamp?: string;
};

export default function RecordingsPage() {
  const [recordings, setRecordings] = useState<RecordingRow[]>([]);
  const [selected, setSelected] = useState<RecordingRow | null>(null);
  const [transcript, setTranscript] = useState<TranscriptLine[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);

  const loadRecordings = useCallback(async () => {
    setLoading(true);
    try {
      const res = await authFetch("/api/recordings");
      const rows = res.ok ? await res.json() : [];
      setRecordings(rows);
      if (!selected && rows.length > 0) setSelected(rows[0]);
    } finally {
      setLoading(false);
    }
  }, [selected]);

  const loadTranscript = useCallback(async () => {
    if (!selected) return;
    const suffix = query ? `?q=${encodeURIComponent(query)}` : "";
    const res = await authFetch(`/api/recordings/${selected.room_id}/transcript${suffix}`);
    setTranscript(res.ok ? await res.json() : []);
  }, [query, selected]);

  useEffect(() => {
    loadRecordings();
  }, [loadRecordings]);

  useEffect(() => {
    loadTranscript();
  }, [loadTranscript]);

  const downloadTranscript = () => {
    if (!selected) return;
    const body = transcript.map((line) => `[${line.spoken_at || line.timestamp || ""}] ${line.speaker}: ${line.text}`).join("\n");
    const blob = new Blob([body], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${selected.room_id}-transcript.txt`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-8 max-w-7xl mx-auto h-full">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-white">Transcript Recordings</h1>
        <p className="text-gray-400 mt-2">Search meeting transcripts, jump by speaker and time, and download recording text.</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[360px_1fr]">
        <div className="space-y-3">
          {loading ? (
            <div className="rounded-xl border border-white/10 bg-surface/30 p-6 text-gray-400">Loading...</div>
          ) : recordings.length === 0 ? (
            <div className="rounded-xl border border-white/10 bg-surface/30 p-6 text-gray-400">No transcript recordings yet.</div>
          ) : recordings.map((recording) => (
            <button key={recording.room_id} onClick={() => setSelected(recording)} className={`w-full rounded-xl border p-4 text-left transition-colors ${selected?.room_id === recording.room_id ? "border-primary/40 bg-primary/10" : "border-white/10 bg-surface/40 hover:bg-surface/60"}`}>
              <div className="flex items-center gap-3">
                <Timer className="h-5 w-5 text-amber-300" />
                <div className="min-w-0">
                  <h2 className="truncate text-sm font-semibold text-white">{recording.title || "Meeting"}</h2>
                  <p className="mt-1 font-mono text-xs text-gray-500">{recording.room_id}</p>
                </div>
              </div>
              <p className="mt-3 text-xs text-gray-400">{recording.transcript_count} transcript lines{recording.has_report ? " · report linked" : ""}</p>
            </button>
          ))}
        </div>

        <div className="min-h-[520px] rounded-xl border border-white/10 bg-surface/30 p-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between mb-4">
            <div className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3">
              <Search className="h-4 w-4 text-gray-500" />
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search transcript" className="w-full bg-transparent py-2.5 text-sm text-white outline-none placeholder:text-gray-500" />
            </div>
            <button onClick={downloadTranscript} disabled={!selected || transcript.length === 0} className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm font-semibold text-gray-300 disabled:opacity-40">
              <Download className="h-4 w-4" />
              Download
            </button>
          </div>

          {transcript.length === 0 ? (
            <div className="flex h-80 flex-col items-center justify-center text-center text-gray-500">
              <FileText className="mb-3 h-10 w-10" />
              Select a recording or adjust search.
            </div>
          ) : (
            <div className="max-h-[620px] space-y-3 overflow-y-auto pr-2">
              {transcript.map((line) => (
                <div key={line.id} className="rounded-xl border border-white/10 bg-white/5 p-3">
                  <div className="mb-1 flex items-center justify-between gap-3">
                    <span className="text-xs font-semibold text-white">{line.speaker || "Speaker"}</span>
                    <span className="text-[11px] text-gray-500">{line.spoken_at ? new Date(line.spoken_at).toLocaleTimeString() : line.timestamp}</span>
                  </div>
                  <p className="text-sm leading-relaxed text-gray-300">{line.text}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
