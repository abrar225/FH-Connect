import { create } from "zustand";

export interface TaskDraft {
  id: string;
  room_id: string;
  original_transcript: string;
  title: string;
  assignee: string | null;
  deadline: string | null;
  status: "pending" | "approved" | "rejected";
  reasoning?: string;
  created_at?: string;
}

export interface MeetingReport {
  executive_summary: string;
  key_decisions: string[];
  tasks: TaskDraft[];
  participation: Record<string, number>;
  meeting_minutes: string;
}

export interface TranscriptionLine {
  id: string;
  text: string;
  speaker: string;
  timestamp: string;
}

export interface ChatMessage {
  id: string;
  senderId: string;
  senderName: string;
  text: string;
  timestamp: string;
  recipientId?: string; // "ALL" or userId
  isPrivate?: boolean;
}

export interface MeetingPulse {
  status: string;
  speaker_perspectives: Record<string, string>;
}

export interface PipelineCheck {
  ok: boolean;
  label: string;
  detail: string;
}

export interface MeetingAIHealth {
  overall: "checking" | "ready" | "unavailable";
  message: string;
  checks: Record<string, PipelineCheck>;
  checkedAt?: string;
}

export interface ReportStatus {
  status: string;
  has_report: boolean;
  report_error?: string | null;
  report_requested_at?: string | null;
  ended_at?: string | null;
}

export interface MeetingInsight {
  id: string;
  room_id: string;
  type: "decision" | "action_item" | "risk" | "question" | "follow_up";
  title: string;
  detail?: string | null;
  owner?: string | null;
  deadline?: string | null;
  status: string;
  confidence?: number;
  created_at?: string;
}

export interface IntentClarification {
  id: string;
  room_id: string;
  text: string;
  speaker?: string | null;
  proposed_action?: string | null;
  proposed_payload?: Partial<TaskDraft> | null;
  confidence?: number | null;
  status?: string;
}

export interface MeetingAgenda {
  room_id?: string;
  goals: string[];
  agenda_items: string[];
  expected_decisions: string[];
  attendees: string[];
  prep_docs: string[];
}

export type MeetingSidebarTab = "chat" | "agenda" | "insights" | "copilot" | "people";

interface DraftStoreState {
  activeRoomId: string | null;
  enterRoom: (roomId: string) => void;
  hydrateRoom: (snapshot: {
    roomId: string;
    isAdmin?: boolean;
    isLocked?: boolean;
    transcriptions?: TranscriptionLine[];
    drafts?: TaskDraft[];
    insights?: MeetingInsight[];
    agenda?: MeetingAgenda;
    reportStatus?: ReportStatus;
  }) => void;
  leaveRoom: (roomId: string) => void;
  resetRoomState: () => void;

  wsStatus: "connecting" | "connected" | "disconnected" | "error";
  setWsStatus: (status: "connecting" | "connected" | "disconnected" | "error") => void;

  speechStatus: "listening" | "error" | "stopped";
  speechError: string | null;
  setSpeechStatus: (status: "listening" | "error" | "stopped", errorMsg?: string | null) => void;

  isAdmin: boolean;
  setIsAdmin: (isAdmin: boolean) => void;

  userId: string;
  setUserId: (userId: string) => void;

  transcriptions: TranscriptionLine[];
  addTranscription: (line: TranscriptionLine) => void;
  updateTranscription: (id: string, text: string) => void;

  // Meeting Pulse
  pulse: MeetingPulse;
  setPulse: (pulse: MeetingPulse) => void;

  aiHealth: MeetingAIHealth;
  setAIHealth: (health: MeetingAIHealth) => void;

  agenda: MeetingAgenda;
  setAgenda: (agenda: MeetingAgenda) => void;

  insights: MeetingInsight[];
  addInsight: (insight: MeetingInsight) => void;
  updateInsight: (id: string, updates: Partial<MeetingInsight>) => void;
  setInsights: (insights: MeetingInsight[]) => void;

  // Task Drafts & Actions
  drafts: TaskDraft[];
  activeDraftId: string | null;
  addDraft: (draft: TaskDraft) => void;
  updateDraft: (id: string, updates: Partial<TaskDraft>) => void;
  setActiveDraft: (id: string | null) => void;
  removeDraft: (id: string) => void;
  clarifications: IntentClarification[];
  addClarification: (clarification: IntentClarification) => void;
  removeClarification: (id: string) => void;

  // Final Report
  report: MeetingReport | null;
  setReport: (report: MeetingReport | null) => void;
  isReportFinalized: boolean;
  setIsReportFinalized: (finalized: boolean) => void;
  reportStatus: ReportStatus | null;
  setReportStatus: (status: ReportStatus | null) => void;
  
  isLocked: boolean;
  setIsLocked: (isLocked: boolean) => void;

  showCaptions: boolean;
  setShowCaptions: (show: boolean) => void;

  chatMessages: ChatMessage[];
  setChatMessages: (messages: ChatMessage[]) => void;
  addChatMessage: (msg: ChatMessage) => void;
  unreadChatCount: number;
  incrementUnreadChat: () => void;
  clearUnreadChat: () => void;

  activeTab: MeetingSidebarTab;
  setActiveTab: (tab: MeetingSidebarTab) => void;
}

export const useDraftStore = create<DraftStoreState>((set) => ({
  activeRoomId: null,
  resetRoomState: () => set({
    wsStatus: "disconnected",
    speechStatus: "stopped",
    speechError: null,
    transcriptions: [],
    pulse: { status: "Waiting for conversation...", speaker_perspectives: {} },
    aiHealth: { overall: "checking", message: "Checking AI meeting pipeline...", checks: {} },
    agenda: { goals: [], agenda_items: [], expected_decisions: [], attendees: [], prep_docs: [] },
    insights: [],
    drafts: [],
    clarifications: [],
    activeDraftId: null,
    report: null,
    reportStatus: null,
    isReportFinalized: false,
    isLocked: false,
    chatMessages: [],
    unreadChatCount: 0,
    activeTab: "chat",
  }),
  enterRoom: (roomId) => set((state) => {
    if (state.activeRoomId === roomId) return state;
    return {
      activeRoomId: roomId,
      wsStatus: "disconnected",
      speechStatus: "stopped",
      speechError: null,
      transcriptions: [],
      pulse: { status: "Waiting for conversation...", speaker_perspectives: {} },
      aiHealth: { overall: "checking", message: "Checking AI meeting pipeline...", checks: {} },
      agenda: { goals: [], agenda_items: [], expected_decisions: [], attendees: [], prep_docs: [] },
      insights: [],
      drafts: [],
      clarifications: [],
      activeDraftId: null,
      report: null,
      reportStatus: null,
      isReportFinalized: false,
      isLocked: false,
      chatMessages: [],
      unreadChatCount: 0,
      activeTab: "chat",
    };
  }),
  hydrateRoom: (snapshot) => set((state) => {
    if (state.activeRoomId !== snapshot.roomId) return state;
    return {
      isAdmin: snapshot.isAdmin ?? state.isAdmin,
      isLocked: snapshot.isLocked ?? state.isLocked,
      transcriptions: snapshot.transcriptions ?? state.transcriptions,
      drafts: snapshot.drafts ?? state.drafts,
      insights: snapshot.insights ?? state.insights,
      agenda: snapshot.agenda ?? state.agenda,
      reportStatus: snapshot.reportStatus ?? state.reportStatus,
    };
  }),
  leaveRoom: (roomId) => set((state) => {
    if (state.activeRoomId !== roomId) return state;
    return {
      activeRoomId: null,
      wsStatus: "disconnected",
      speechStatus: "stopped",
      speechError: null,
      transcriptions: [],
      pulse: { status: "Waiting for conversation...", speaker_perspectives: {} },
      aiHealth: { overall: "checking", message: "Checking AI meeting pipeline...", checks: {} },
      agenda: { goals: [], agenda_items: [], expected_decisions: [], attendees: [], prep_docs: [] },
      insights: [],
      drafts: [],
      clarifications: [],
      activeDraftId: null,
      report: null,
      reportStatus: null,
      isReportFinalized: false,
      isLocked: false,
      chatMessages: [],
      unreadChatCount: 0,
      activeTab: "chat",
    };
  }),

  wsStatus: "disconnected",
  setWsStatus: (status) => set({ wsStatus: status }),

  speechStatus: "stopped",
  speechError: null,
  setSpeechStatus: (status, errorMsg = null) => set({ speechStatus: status, speechError: errorMsg }),

  isAdmin: false,
  setIsAdmin: (isAdmin) => set({ isAdmin }),

  userId: "",
  setUserId: (userId) => set({ userId }),

  transcriptions: [],
  addTranscription: (line) =>
    set((state) => {
      if (state.transcriptions.some((t) => t.id === line.id)) {
        return {
          transcriptions: state.transcriptions.map((t) => (t.id === line.id ? { ...t, ...line } : t)),
        };
      }
      return { transcriptions: [...state.transcriptions, line] };
    }),
  updateTranscription: (id, text) =>
    set((state) => ({
      transcriptions: state.transcriptions.map((t) =>
        t.id === id ? { ...t, text } : t
      ),
    })),

  pulse: {
    status: "Waiting for conversation...",
    speaker_perspectives: {},
  },
  setPulse: (pulse) => set({ pulse }),

  aiHealth: {
    overall: "checking",
    message: "Checking AI meeting pipeline...",
    checks: {},
  },
  setAIHealth: (health) => set({ aiHealth: { ...health, checkedAt: new Date().toISOString() } }),

  agenda: {
    goals: [],
    agenda_items: [],
    expected_decisions: [],
    attendees: [],
    prep_docs: [],
  },
  setAgenda: (agenda) => set({ agenda }),

  insights: [],
  addInsight: (insight) =>
    set((state) => {
      if (state.insights.some((item) => item.id === insight.id)) return state;
      return { insights: [insight, ...state.insights] };
    }),
  updateInsight: (id, updates) =>
    set((state) => ({
      insights: state.insights.map((item) => (item.id === id ? { ...item, ...updates } : item)),
    })),
  setInsights: (insights) => set({ insights }),

  drafts: [],
  activeDraftId: null,
  addDraft: (draft) => set((state) => {
    if (state.drafts.some((item) => item.id === draft.id)) {
      return { drafts: state.drafts.map((item) => (item.id === draft.id ? { ...item, ...draft } : item)) };
    }
    return { drafts: [...state.drafts, draft] };
  }),
  updateDraft: (id, updates) =>
    set((state) => ({
      drafts: state.drafts.map((d) => (d.id === id ? { ...d, ...updates } : d)),
    })),
  setActiveDraft: (id) => set({ activeDraftId: id }),
  removeDraft: (id) =>
    set((state) => ({
      drafts: state.drafts.filter((d) => d.id !== id),
      activeDraftId: state.activeDraftId === id ? null : state.activeDraftId,
    })),
  clarifications: [],
  addClarification: (clarification) => set((state) => {
    if (state.clarifications.some((item) => item.id === clarification.id)) {
      return {
        clarifications: state.clarifications.map((item) =>
          item.id === clarification.id ? { ...item, ...clarification } : item
        ),
      };
    }
    return { clarifications: [clarification, ...state.clarifications] };
  }),
  removeClarification: (id) => set((state) => ({
    clarifications: state.clarifications.filter((item) => item.id !== id),
  })),

  report: null,
  setReport: (report) => set({ report }),
  isReportFinalized: false,
  setIsReportFinalized: (finalized) => set({ isReportFinalized: finalized }),
  reportStatus: null,
  setReportStatus: (reportStatus) => set({ reportStatus }),
  
  isLocked: false,
  setIsLocked: (isLocked) => set({ isLocked }),

  showCaptions: true,
  setShowCaptions: (show) => set({ showCaptions: show }),

  chatMessages: [],
  setChatMessages: (messages) => set({ chatMessages: messages }),
  addChatMessage: (msg) =>
    set((state) => {
      // Deduplicate by ID
      if (state.chatMessages.some((m) => m.id === msg.id)) return state;
      return { chatMessages: [...state.chatMessages, msg] };
    }),

  unreadChatCount: 0,
  incrementUnreadChat: () => set((state) => ({ unreadChatCount: state.unreadChatCount + 1 })),
  clearUnreadChat: () => set({ unreadChatCount: 0 }),

  activeTab: "chat",
  setActiveTab: (tab) => set({ activeTab: tab }),
}));
