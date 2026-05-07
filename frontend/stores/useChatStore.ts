import { create } from 'zustand';

export interface ChatMessage {
  id: string;
  senderId: string;
  senderName: string;
  content: string;
  timestamp: number;
  isSystem?: boolean;
}

interface ChatState {
  messages: ChatMessage[];
  unreadCount: number;
  
  // Actions
  addMessage: (message: ChatMessage) => void;
  clearMessages: () => void;
  resetUnreadCount: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  unreadCount: 0,

  addMessage: (message) => set((state) => {
    // Only keep last 500 messages to prevent memory bloat in very long meetings
    const newMessages = [...state.messages, message].slice(-500);
    return {
      messages: newMessages,
      unreadCount: state.unreadCount + 1,
    };
  }),

  clearMessages: () => set(() => ({ messages: [], unreadCount: 0 })),
  
  resetUnreadCount: () => set(() => ({ unreadCount: 0 }))
}));
