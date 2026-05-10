"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { CheckCircle2, Clock, ExternalLink, Search, Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { authFetch } from "@/app/lib/api";

type ActionRow = {
  id: string;
  room_id: string;
  title: string;
  detail?: string | null;
  owner?: string | null;
  deadline?: string | null;
  status: string;
  created_at?: string;
};

const filters = ["assigned", "overdue", "waiting", "completed"] as const;

export default function ActionsPage() {
  const router = useRouter();
  const [actions, setActions] = useState<ActionRow[]>([]);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<(typeof filters)[number]>("assigned");

  const loadActions = useCallback(async () => {
    const res = await authFetch("/api/actions");
    setActions(res.ok ? await res.json() : []);
  }, []);

  useEffect(() => {
    loadActions();
  }, [loadActions]);

  const visible = useMemo(() => actions.filter((action) => {
    const haystack = `${action.title} ${action.detail || ""} ${action.owner || ""}`.toLowerCase();
    if (!haystack.includes(query.toLowerCase())) return false;
    if (filter === "completed") return action.status === "completed" || action.status === "resolved";
    if (filter === "overdue") return Boolean(action.deadline && new Date(action.deadline) < new Date() && action.status !== "completed");
    if (filter === "waiting") return action.status === "pending" || action.status === "open";
    return action.status !== "completed" && action.status !== "resolved";
  }), [actions, filter, query]);

  const patch = async (id: string, status: string) => {
    const res = await authFetch(`/api/actions/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    });
    if (res.ok) loadActions();
  };

  const deleteAction = async (id: string) => {
    if (!window.confirm("Are you sure you want to delete this action? This action cannot be undone.")) return;
    const res = await authFetch(`/api/actions/${id}`, { method: "DELETE" });
    if (res.ok) loadActions();
  };

  return (
    <div className="p-8 max-w-7xl mx-auto h-full">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-white">Action Ownership</h1>
        <p className="text-gray-400 mt-2">Track commitments across meetings and close the loop after the call.</p>
      </div>

      <div className="mb-6 flex flex-col gap-3 md:flex-row">
        <div className="flex flex-1 items-center gap-2 rounded-xl border border-white/10 bg-surface/40 px-3">
          <Search className="h-4 w-4 text-gray-500" />
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search actions" className="w-full bg-transparent py-2.5 text-sm text-white outline-none placeholder:text-gray-500" />
        </div>
        <div className="flex rounded-xl border border-white/10 bg-surface/40 p-1">
          {filters.map((item) => (
            <button key={item} onClick={() => setFilter(item)} className={`rounded-lg px-3 py-2 text-xs font-semibold uppercase tracking-wide ${filter === item ? "bg-primary/20 text-primary" : "text-gray-500 hover:text-gray-300"}`}>
              {item}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-3">
        {visible.length === 0 ? (
          <div className="rounded-xl border border-white/10 bg-surface/30 p-10 text-center text-gray-400">No action items in this view.</div>
        ) : visible.map((action) => (
          <div key={action.id} className="rounded-xl border border-white/10 bg-surface/40 p-4">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div>
                <h2 className="font-semibold text-white">{action.title}</h2>
                {action.detail && <p className="mt-1 text-sm text-gray-400">{action.detail}</p>}
                <div className="mt-2 flex flex-wrap gap-2 text-xs text-gray-500">
                  <span>{action.owner || "Unassigned"}</span>
                  {action.deadline && <span className="inline-flex items-center gap-1"><Clock className="h-3 w-3" /> {new Date(action.deadline).toLocaleDateString()}</span>}
                  <span className="font-mono">{action.room_id}</span>
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                <button onClick={() => patch(action.id, action.status === "completed" ? "open" : "completed")} className="inline-flex items-center gap-2 rounded-lg bg-primary/20 px-3 py-2 text-xs font-semibold text-primary">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  {action.status === "completed" ? "Reopen" : "Complete"}
                </button>
                <button onClick={() => router.push(`/room/${action.room_id}`)} className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs font-semibold text-gray-300">
                  <ExternalLink className="h-3.5 w-3.5" />
                  Meeting
                </button>
                <button onClick={() => deleteAction(action.id)} className="inline-flex items-center gap-2 rounded-lg border border-red-500/20 bg-red-500/10 px-3 py-2 text-xs font-semibold text-red-400 hover:bg-red-500/20">
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
