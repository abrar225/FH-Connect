"use client";

import React, { useState, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  MessageSquare,
  BarChart3,
  Users,
  Settings,
  LayoutGrid,
  X,
  ShieldCheck,
  Crown,
  Loader2,
  Send,
  ClipboardList,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  CircleHelp,
  Repeat2,
} from "lucide-react";

import {
  useLocalParticipant,
  useRemoteParticipants,
} from "@livekit/components-react";
import { Mic, MicOff } from "lucide-react";
import { GlassContainer } from "@/app/components/ui/GlassContainer";
import { MeetingSidebarTab, useDraftStore } from "@/app/store/draftStore";
import { useToast } from "@/app/components/ui/ToastProvider";

import { authFetch } from "@/app/lib/api";

interface FeatureSidebarProps {
  onClose: () => void;
  isAdmin?: boolean;
  userId?: string;
  roomId?: string;
  ws?: WebSocket | null;
}

export default function FeatureSidebar({ onClose, isAdmin = false, userId = "", roomId = "", ws = null }: FeatureSidebarProps) {
  const { localParticipant, isMicrophoneEnabled } = useLocalParticipant();
  const remoteParticipants = useRemoteParticipants();
  const storeIsAdmin = useDraftStore((state) => state.isAdmin);
  const activeTab = useDraftStore((state) => state.activeTab);
  const setActiveTab = useDraftStore((state) => state.setActiveTab);
  const unreadChatCount = useDraftStore((state) => state.unreadChatCount);
  const clearUnreadChat = useDraftStore((state) => state.clearUnreadChat);
  const setAgenda = useDraftStore((state) => state.setAgenda);
  const setInsights = useDraftStore((state) => state.setInsights);
  const { toast } = useToast();
  const [loadingTarget, setLoadingTarget] = useState<string | null>(null);

  // Use the reactive store value (updated via WebSocket) if available
  const effectiveIsAdmin = storeIsAdmin || isAdmin;

  useEffect(() => {
    if (!roomId) return;
    let alive = true;

    const loadMeetingContext = async () => {
      try {
        const [agendaRes, insightsRes] = await Promise.all([
          authFetch(`/api/meeting/${roomId}/agenda`),
          authFetch(`/api/meeting/${roomId}/insights`),
        ]);

        if (!alive) return;
        if (agendaRes.ok) {
          const agenda = await agendaRes.json();
          setAgenda(agenda);
        }
        if (insightsRes.ok) {
          const insights = await insightsRes.json();
          setInsights(insights);
        }
      } catch {
        if (alive) toast("error", "Meeting context unavailable", "Agenda and insights could not be loaded.");
      }
    };

    void loadMeetingContext();
    return () => {
      alive = false;
    };
  }, [roomId, setAgenda, setInsights, toast]);

  const handleToggleAdmin = useCallback(async (targetIdentity: string, makeAdmin: boolean) => {
    setLoadingTarget(targetIdentity);
    try {
      const res = await authFetch(`/api/meeting/${roomId}/admin?is_admin=${makeAdmin}`, {
        method: 'POST',
        body: JSON.stringify({
          target_user_id: targetIdentity,
        }),
      });
      if (res.ok) {
        toast("success", makeAdmin ? "Admin Granted" : "Admin Revoked", 
          makeAdmin ? `${targetIdentity} is now an admin.` : `${targetIdentity} is no longer an admin.`);
      } else {
        const err = await res.json().catch(() => ({}));
        toast("error", "Error", err.detail || "Failed to update admin.");
      }
    } catch (e) {
      toast("error", "Error", "Failed to update admin role.");
    } finally {
      setLoadingTarget(null);
    }
  }, [roomId, toast]);
  
  const handleMuteUser = useCallback(async (targetIdentity: string) => {
    setLoadingTarget(targetIdentity);
    try {
      const res = await authFetch(`/api/meeting/${roomId}/mute-user`, {
        method: 'POST',
        body: JSON.stringify({
          target_user_id: targetIdentity,
        }),
      });
      if (res.ok) {
        toast("success", "User Muted", `${targetIdentity} has been muted.`);
      } else {
        const err = await res.json().catch(() => ({}));
        toast("error", "Error", err.detail || "Failed to mute user.");
      }
    } catch (e) {
      toast("error", "Error", "Failed to mute participant.");
    } finally {
      setLoadingTarget(null);
    }
  }, [roomId, toast]);


  const tabs = [
    { id: "chat", icon: MessageSquare, label: "Chat" },
    { id: "agenda", icon: ClipboardList, label: "Agenda" },
    { id: "insights", icon: BarChart3, label: "Insights" },
    { id: "copilot", icon: Sparkles, label: "Copilot" },
    { id: "people", icon: Users, label: "People" },
  ] satisfies Array<{ id: MeetingSidebarTab; icon: React.ElementType; label: string }>;

  return (
    <GlassContainer intensity="high" className="w-full h-full flex flex-col overflow-hidden relative rounded-none border-y-0 border-l-0 border-r border-white/5">
      {/* Search / Top Bar */}
      <div className="p-4 shrink-0 border-b border-white/5 flex items-center space-x-2">
         <div className="flex-1 bg-white/5 border border-white/10 rounded-xl px-3 py-2 flex items-center space-x-2">
            <div className="w-4 h-4 text-white/30 truncate text-[10px] font-medium tracking-tight">Search members...</div>
         </div>
         <button className="p-2 rounded-xl bg-white/5 border border-white/10 text-white/40">
            <LayoutGrid className="w-4 h-4" />
         </button>
         <button 
           onClick={onClose}
           className="p-2 rounded-xl hover:bg-white/5 text-white/30 hover:text-white transition-all"
         >
           <X className="w-4 h-4" />
         </button>
      </div>

      {/* Navigation Tabs */}
      <div className="flex px-4 pt-2 space-x-1 shrink-0">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => {
              setActiveTab(tab.id);
              if (tab.id === "chat") clearUnreadChat();
            }}
            className={`flex-1 py-2.5 rounded-xl transition-all relative flex flex-col items-center justify-center space-y-1 ${
              activeTab === tab.id ? "bg-primary/20 text-primary border border-primary/20" : "text-white/40 hover:text-white/60"
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.id === "chat" && unreadChatCount > 0 && activeTab !== "chat" && (
              <span className="absolute top-2 right-4 w-2 h-2 bg-red-500 rounded-full border border-background shadow-lg shadow-red-500/50" />
            )}
            <span className="text-[9px] font-bold uppercase tracking-tighter">{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-hidden flex flex-col relative p-4">
        <AnimatePresence mode="wait">
          {activeTab === "chat" ? (
            <ChatTab userId={userId} roomId={roomId} ws={ws} />
          ) : activeTab === "agenda" ? (
            <AgendaTab roomId={roomId} />
          ) : activeTab === "insights" ? (
            <InsightsTab />
          ) : activeTab === "copilot" ? (
            <CopilotTab roomId={roomId} />
          ) : activeTab === "people" ? (
             <motion.div
               key="people"
               initial={{ opacity: 0, x: 20 }}
               animate={{ opacity: 1, x: 0 }}
               exit={{ opacity: 0, x: -20 }}
               className="flex-1 flex flex-col space-y-3 overflow-y-auto custom-scrollbar"
             >
                <div className="px-1 text-[10px] font-bold text-white/20 uppercase tracking-[0.2em] mb-2">In Meeting ({remoteParticipants.length + 1})</div>
                
                {/* Local Participant */}
                <div className="flex items-center justify-between p-2.5 rounded-xl bg-white/5 border border-white/5">
                   <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 rounded-lg bg-primary/20 border border-primary/30 flex items-center justify-center text-[10px] font-bold text-primary">ME</div>
                      <div>
                         <div className="text-[11px] font-bold text-white/90 flex items-center space-x-1.5">
                           <span>{localParticipant.name || "You"}</span>
                           {effectiveIsAdmin && (
                             <Crown className="w-3 h-3 text-amber-400" />
                           )}
                         </div>
                         <div className={`text-[9px] ${effectiveIsAdmin ? "text-amber-400" : "text-white/30"}`}>
                           {effectiveIsAdmin ? "Admin" : "Participant"}
                         </div>
                      </div>
                   </div>
                   {isMicrophoneEnabled ? <Mic className="w-3.5 h-3.5 text-emerald-400" /> : <MicOff className="w-3.5 h-3.5 text-red-400" />}
                </div>

                {/* Remote Participants */}
                {remoteParticipants.map((p) => (
                   <div key={p.sid} className="flex items-center justify-between p-2.5 rounded-xl hover:bg-white/5 transition-all group">
                      <div className="flex items-center space-x-3">
                         <div className="w-8 h-8 rounded-lg bg-white/10 border border-white/5 flex items-center justify-center text-[10px] font-bold text-white/40">
                            {(p.name || p.identity).substring(0, 2).toUpperCase()}
                         </div>
                         <div>
                            <div className="text-[11px] font-bold text-white/80">{p.name || p.identity}</div>
                            <div className="text-[9px] text-white/30">Participant</div>
                         </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        {p.isMicrophoneEnabled ? <Mic className="w-3.5 h-3.5 text-emerald-400" /> : <MicOff className="w-3.5 h-3.5 text-red-400" />}
                        
                        {/* Admin Action Buttons — only visible to admins */}
                        {effectiveIsAdmin && (
                          <div className="flex items-center space-x-1.5">
                            <motion.button
                              initial={{ scale: 0 }}
                              animate={{ scale: 1 }}
                              onClick={() => handleMuteUser(p.identity)}
                              disabled={loadingTarget === p.identity}
                              className="opacity-0 group-hover:opacity-100 transition-opacity p-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 text-red-400"
                              title="Mute Participant"
                            >
                              {loadingTarget === p.identity ? (
                                <Loader2 className="w-3 h-3 animate-spin" />
                              ) : (
                                <MicOff className="w-3 h-3" />
                              )}
                            </motion.button>
                            
                            <motion.button
                              initial={{ scale: 0 }}
                              animate={{ scale: 1 }}
                              onClick={() => handleToggleAdmin(p.identity, true)}
                              disabled={loadingTarget === p.identity}
                              className="opacity-0 group-hover:opacity-100 transition-opacity p-1.5 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/20 text-amber-400 text-[9px] font-bold uppercase tracking-wider flex items-center space-x-1"
                              title="Make Admin"
                            >
                              {loadingTarget === p.identity ? (
                                <Loader2 className="w-3 h-3 animate-spin" />
                              ) : (
                                <>
                                  <ShieldCheck className="w-3 h-3" />
                                  <span>Admin</span>
                                </>
                              )}
                            </motion.button>
                          </div>
                        )}
                      </div>
                   </div>
                ))}
             </motion.div>
          ) : null}
        </AnimatePresence>
      </div>

      {/* Footer Info */}
      <div className="p-4 border-t border-white/5 bg-black/10 shrink-0">
        <div className="flex items-center justify-between">
          <span className="text-[9px] font-bold text-white/20 uppercase tracking-[0.2em]">Secure Session</span>
          <Settings className="w-4 h-4 text-white/20" />
        </div>
      </div>
    </GlassContainer>
  );
}

function ChatTab({ userId, roomId, ws }: { userId: string; roomId: string; ws: WebSocket | null }) {
  const chatMessages = useDraftStore((state) => state.chatMessages);
  const remoteParticipants = useRemoteParticipants();
  const { localParticipant } = useLocalParticipant();
  
  const [message, setMessage] = useState("");
  const [chatType, setChatType] = useState<"public" | "private">("public");
  const [recipient, setRecipient] = useState<string>("ALL");

  const publicMessages = chatMessages.filter(m => !m.isPrivate);
  const privateMessages = chatMessages.filter(m => 
    m.isPrivate && (m.senderId === userId || m.recipientId === userId)
  );

  const activeMessages = chatType === "public" ? publicMessages : privateMessages;

  const handleSendMessage = () => {
    if (!message.trim() || !ws || ws.readyState !== WebSocket.OPEN) return;

    const chatPayload = {
      type: "CHAT_SEND",
      payload: {
        id: crypto.randomUUID(),
        senderName: localParticipant.name || "You",
        text: message,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        recipientId: chatType === "public" ? "ALL" : recipient
      }
    };

    ws.send(JSON.stringify(chatPayload));
    setMessage("");
  };

  return (
    <motion.div
      key="chat"
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.98 }}
      className="flex-1 flex flex-col h-full overflow-hidden"
    >
      {/* Chat Type Toggle */}
      <div className="flex bg-white/5 p-1 rounded-xl mb-4 border border-white/5">
        <button 
          onClick={() => setChatType("public")}
          className={`flex-1 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all ${chatType === "public" ? "bg-white/10 text-white shadow-sm" : "text-white/30 hover:text-white/50"}`}
        >
          Public
        </button>
        <button 
          onClick={() => setChatType("private")}
          className={`flex-1 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all ${chatType === "private" ? "bg-white/10 text-white shadow-sm" : "text-white/30 hover:text-white/50"}`}
        >
          Private
        </button>
      </div>

      {chatType === "private" && (
        <div className="mb-4">
          <select 
            value={recipient} 
            onChange={(e) => setRecipient(e.target.value)}
            className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-[11px] text-white/70 outline-none focus:border-primary/50 transition-colors"
          >
            <option value="ALL" className="bg-slate-900">Select Recipient...</option>
            {remoteParticipants.map(p => (
              <option key={p.identity} value={p.identity} className="bg-slate-900">
                {p.name || p.identity}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Message Feed */}
      <div className="flex-1 space-y-4 overflow-y-auto custom-scrollbar pr-2 pt-2 pb-4">
        {activeMessages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center opacity-20 space-y-2">
            <MessageSquare className="w-8 h-8" />
            <p className="text-[10px] uppercase font-bold tracking-widest">No messages yet</p>
          </div>
        ) : (
          activeMessages.map((msg) => (
            <div key={msg.id} className={`flex items-start space-x-3 mb-2 ${msg.senderId === userId ? "flex-row-reverse space-x-reverse" : ""}`}>
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-[10px] font-bold border shrink-0 ${
                msg.senderId === userId 
                  ? "bg-primary/20 border-primary/30 text-primary" 
                  : "bg-white/10 border-white/10 text-white/40"
              }`}>
                {(msg.senderName || "??").substring(0, 2).toUpperCase()}
              </div>
              <div className={`flex flex-col ${msg.senderId === userId ? "items-end" : "items-start"} max-w-[80%]`}>
                <div className="flex items-baseline space-x-2 mb-1 px-1">
                  <span className="text-[11px] font-bold text-white/80 shrink-0">{msg.senderId === userId ? "You" : msg.senderName}</span>
                  <span className="text-[9px] text-white/20 uppercase shrink-0">{msg.timestamp}</span>
                  {msg.isPrivate && (
                    <span className="text-[9px] bg-amber-500/10 text-amber-500 px-1.5 rounded-sm font-bold uppercase tracking-tighter shrink-0">Private</span>
                  )}
                </div>
                <div className={`py-2 px-3 rounded-2xl text-xs leading-relaxed break-words whitespace-pre-wrap ${
                  msg.senderId === userId 
                    ? "bg-primary text-white rounded-tr-none shadow-lg shadow-primary/20" 
                    : "bg-white/5 text-white/70 rounded-tl-none border border-white/5"
                }`}>
                  {msg.text}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Chat Input */}
      <div className="mt-auto pt-4 border-t border-white/5">
        <div className="flex items-center space-x-2 bg-white/5 border border-white/10 rounded-2xl px-2 py-2 focus-within:border-primary/50 transition-all">
          <input 
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
            placeholder={chatType === "public" ? "Message everyone..." : `Message ${recipient === "ALL" ? "someone" : (remoteParticipants.find(p => p.identity === recipient)?.name || recipient)}...`}
            className="flex-1 bg-transparent border-none outline-none text-[12px] text-white px-2 placeholder:text-white/20"
          />
          <button 
            onClick={handleSendMessage}
            disabled={!message.trim()}
            className="p-2 rounded-xl bg-primary text-white disabled:opacity-30 disabled:grayscale transition-all hover:scale-105 active:scale-95"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </motion.div>
  );
}

function linesToText(value: string[] | undefined) {
  return (value || []).join("\n");
}

function textToLines(value: string) {
  return value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

function AgendaTab({ roomId }: { roomId: string }) {
  const agenda = useDraftStore((state) => state.agenda);
  const setAgenda = useDraftStore((state) => state.setAgenda);
  const { toast } = useToast();
  const [goals, setGoals] = useState(linesToText(agenda.goals));
  const [items, setItems] = useState(linesToText(agenda.agenda_items));
  const [decisions, setDecisions] = useState(linesToText(agenda.expected_decisions));
  const [attendees, setAttendees] = useState(linesToText(agenda.attendees));
  const [prepDocs, setPrepDocs] = useState(linesToText(agenda.prep_docs));
  const [saving, setSaving] = useState(false);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    setGoals(linesToText(agenda.goals));
    setItems(linesToText(agenda.agenda_items));
    setDecisions(linesToText(agenda.expected_decisions));
    setAttendees(linesToText(agenda.attendees));
    setPrepDocs(linesToText(agenda.prep_docs));
  }, [agenda]);

  const payload = {
    goals: textToLines(goals),
    agenda_items: textToLines(items),
    expected_decisions: textToLines(decisions),
    attendees: textToLines(attendees),
    prep_docs: textToLines(prepDocs),
  };

  const saveAgenda = async () => {
    setSaving(true);
    try {
      const res = await authFetch(`/api/meeting/${roomId}/agenda`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error("Save failed");
      const nextAgenda = await res.json();
      setAgenda(nextAgenda);
      toast("success", "Agenda saved", "Meeting purpose and prep are synced.");
    } catch {
      toast("error", "Agenda save failed", "Please check your access and try again.");
    } finally {
      setSaving(false);
    }
  };

  const generateAgenda = async () => {
    setGenerating(true);
    try {
      const topic = payload.goals[0] || "Productive team meeting";
      const res = await authFetch(`/api/meeting/${roomId}/agenda/generate`, {
        method: "POST",
        body: JSON.stringify({ topic, attendees: payload.attendees }),
      });
      if (!res.ok) throw new Error("Generation failed");
      const nextAgenda = await res.json();
      setAgenda(nextAgenda);
      toast("success", "Agenda generated", "AI created a structured starting point.");
    } catch {
      toast("error", "Agenda generation failed", "The agenda can still be edited manually.");
    } finally {
      setGenerating(false);
    }
  };

  return (
    <motion.div
      key="agenda"
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      className="flex-1 overflow-y-auto custom-scrollbar space-y-3 pr-1"
    >
      <div className="grid grid-cols-2 gap-2">
        <button onClick={generateAgenda} disabled={generating} className="py-2 rounded-xl bg-primary/20 border border-primary/20 text-primary text-[10px] font-bold uppercase tracking-wider flex items-center justify-center space-x-2 disabled:opacity-50">
          {generating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
          <span>Generate</span>
        </button>
        <button onClick={saveAgenda} disabled={saving} className="py-2 rounded-xl bg-white/10 border border-white/10 text-white/80 text-[10px] font-bold uppercase tracking-wider flex items-center justify-center space-x-2 disabled:opacity-50">
          {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle2 className="w-3.5 h-3.5" />}
          <span>Save</span>
        </button>
      </div>
      <AgendaField label="Goals" value={goals} onChange={setGoals} />
      <AgendaField label="Agenda Items" value={items} onChange={setItems} />
      <AgendaField label="Expected Decisions" value={decisions} onChange={setDecisions} />
      <AgendaField label="Attendees" value={attendees} onChange={setAttendees} />
      <AgendaField label="Prep Docs" value={prepDocs} onChange={setPrepDocs} />
    </motion.div>
  );
}

function AgendaField({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <label className="block">
      <span className="block text-[9px] font-bold uppercase tracking-[0.18em] text-white/30 mb-1.5">{label}</span>
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        rows={3}
        className="w-full resize-none rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-[11px] leading-relaxed text-white/80 outline-none focus:border-primary/50 placeholder:text-white/20"
        placeholder="One item per line"
      />
    </label>
  );
}

const insightMeta = {
  decision: { label: "Decisions", icon: CheckCircle2, color: "text-emerald-300" },
  action_item: { label: "Actions", icon: ClipboardList, color: "text-sky-300" },
  risk: { label: "Risks", icon: AlertTriangle, color: "text-amber-300" },
  question: { label: "Questions", icon: CircleHelp, color: "text-violet-300" },
  follow_up: { label: "Follow-ups", icon: Repeat2, color: "text-pink-300" },
};

function InsightsTab() {
  const insights = useDraftStore((state) => state.insights);
  const updateInsight = useDraftStore((state) => state.updateInsight);
  const { toast } = useToast();

  const patchInsight = async (id: string, status: string) => {
    try {
      const res = await authFetch(`/api/actions/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      });
      if (!res.ok) throw new Error("Update failed");
      const updated = await res.json();
      updateInsight(id, updated);
    } catch {
      toast("error", "Insight update failed", "Please check your access and try again.");
    }
  };

  return (
    <motion.div
      key="insights"
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      className="flex-1 overflow-y-auto custom-scrollbar space-y-4 pr-1"
    >
      {Object.entries(insightMeta).map(([type, meta]) => {
        const group = insights.filter((item) => item.type === type);
        const Icon = meta.icon;
        return (
          <section key={type} className="space-y-2">
            <div className="flex items-center justify-between px-1">
              <div className={`flex items-center space-x-2 text-[10px] font-bold uppercase tracking-[0.18em] ${meta.color}`}>
                <Icon className="w-3.5 h-3.5" />
                <span>{meta.label}</span>
              </div>
              <span className="text-[10px] text-white/30">{group.length}</span>
            </div>
            {group.length === 0 ? (
              <div className="rounded-xl border border-white/5 bg-white/[0.03] px-3 py-2 text-[10px] text-white/25">No items captured yet.</div>
            ) : (
              group.map((item) => (
                <div key={item.id} className="rounded-xl border border-white/10 bg-white/5 p-3 space-y-2">
                  <div className="text-[12px] font-bold text-white/85 leading-snug">{item.title}</div>
                  {item.detail && <p className="text-[10px] text-white/45 leading-relaxed">{item.detail}</p>}
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate text-[9px] uppercase tracking-wider text-white/30">{item.owner || item.status}</span>
                    <button
                      onClick={() => patchInsight(item.id, item.status === "resolved" || item.status === "completed" ? "open" : item.type === "action_item" ? "completed" : "resolved")}
                      className="shrink-0 rounded-lg border border-white/10 bg-white/5 px-2 py-1 text-[9px] font-bold uppercase tracking-wider text-white/60 hover:text-white"
                    >
                      {item.status === "resolved" || item.status === "completed" ? "Reopen" : "Done"}
                    </button>
                  </div>
                </div>
              ))
            )}
          </section>
        );
      })}
    </motion.div>
  );
}

function CopilotTab({ roomId }: { roomId: string }) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const askCopilot = async () => {
    if (!question.trim()) return;
    setLoading(true);
    try {
      const res = await authFetch(`/api/meeting/${roomId}/copilot`, {
        method: "POST",
        body: JSON.stringify({ question }),
      });
      if (!res.ok) throw new Error("Copilot failed");
      const data = await res.json();
      setAnswer(data.answer || "");
    } catch {
      toast("error", "Copilot unavailable", "The copilot can only answer from this meeting context.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      key="copilot"
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      className="flex-1 flex flex-col overflow-hidden"
    >
      <div className="flex-1 overflow-y-auto custom-scrollbar rounded-xl border border-white/10 bg-white/5 p-3">
        {answer ? (
          <p className="whitespace-pre-wrap text-[12px] leading-relaxed text-white/75">{answer}</p>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-center text-white/25 space-y-2">
            <Sparkles className="w-8 h-8" />
            <p className="text-[10px] uppercase tracking-widest font-bold">Ask about this meeting only</p>
          </div>
        )}
      </div>
      <div className="mt-3 flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-2 py-2">
        <input
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          onKeyDown={(event) => event.key === "Enter" && askCopilot()}
          placeholder="What decisions are pending?"
          className="min-w-0 flex-1 bg-transparent px-2 text-[12px] text-white outline-none placeholder:text-white/20"
        />
        <button onClick={askCopilot} disabled={loading || !question.trim()} className="rounded-xl bg-primary p-2 text-white disabled:opacity-40">
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
        </button>
      </div>
    </motion.div>
  );
}
