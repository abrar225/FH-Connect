import { create } from 'zustand';

// Note: Core WebRTC state (tracks, peers) is mostly handled by LiveKit context,
// but we need this store for UI-level room state (layout modes, pinned participants).

export type LayoutMode = 'grid' | 'speaker' | 'presentation';

interface RoomState {
  layoutMode: LayoutMode;
  pinnedParticipantId: string | null;
  activeSpeakerId: string | null;
  
  // Actions
  setLayoutMode: (mode: LayoutMode) => void;
  pinParticipant: (participantId: string | null) => void;
  setActiveSpeaker: (participantId: string | null) => void;
}

export const useRoomStore = create<RoomState>((set) => ({
  layoutMode: 'grid',
  pinnedParticipantId: null,
  activeSpeakerId: null,

  setLayoutMode: (mode) => set(() => ({ layoutMode: mode })),
  
  pinParticipant: (participantId) => set(() => ({ 
    pinnedParticipantId: participantId,
    // Automatically switch to speaker mode if someone is pinned
    layoutMode: participantId ? 'speaker' : 'grid' 
  })),

  setActiveSpeaker: (participantId) => set(() => ({
    activeSpeakerId: participantId
  }))
}));
