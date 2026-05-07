import { create } from 'zustand';

interface UIState {
  isSidebarOpen: boolean;
  activeSidebarTab: 'chat' | 'intelligence' | 'participants' | null;
  isSettingsModalOpen: boolean;
  isWhiteboardOpen: boolean;
  
  // Actions
  toggleSidebar: () => void;
  openSidebarTab: (tab: 'chat' | 'intelligence' | 'participants') => void;
  closeSidebar: () => void;
  setSettingsModalOpen: (isOpen: boolean) => void;
  toggleWhiteboard: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  isSidebarOpen: false,
  activeSidebarTab: null,
  isSettingsModalOpen: false,
  isWhiteboardOpen: false,

  toggleSidebar: () => set((state) => ({ 
    isSidebarOpen: !state.isSidebarOpen,
    activeSidebarTab: !state.isSidebarOpen ? (state.activeSidebarTab || 'chat') : null
  })),
  
  openSidebarTab: (tab) => set(() => ({
    isSidebarOpen: true,
    activeSidebarTab: tab
  })),

  closeSidebar: () => set(() => ({
    isSidebarOpen: false,
    activeSidebarTab: null
  })),

  setSettingsModalOpen: (isOpen) => set(() => ({
    isSettingsModalOpen: isOpen
  })),

  toggleWhiteboard: () => set((state) => ({
    isWhiteboardOpen: !state.isWhiteboardOpen
  }))
}));
