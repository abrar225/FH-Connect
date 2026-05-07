'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Mic, MicOff, Video, VideoOff, 
  MonitorUp, MessageSquare, Users, 
  MoreVertical, PhoneOff, Sparkles 
} from 'lucide-react';
import { useUIStore } from '@/stores/useUIStore';

// Note: In a real implementation, we would hook this up to LiveKit's useLocalParticipant
// For now, it manages its own local visual state for the blueprint.

export const DynamicControls = () => {
  const [isMicOn, setIsMicOn] = useState(true);
  const [isVideoOn, setIsVideoOn] = useState(true);
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  const [showMoreMenu, setShowMoreMenu] = useState(false);

  const { toggleSidebar, activeSidebarTab } = useUIStore();

  const toggleMic = () => setIsMicOn(!isMicOn);
  const toggleVideo = () => setIsVideoOn(!isVideoOn);
  const toggleScreenShare = () => setIsScreenSharing(!isScreenSharing);

  return (
    <div className="fixed bottom-8 left-1/2 -translate-x-1/2 z-50">
      <motion.div 
        initial={{ y: 50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ type: 'spring', damping: 25, stiffness: 200 }}
        className="relative flex items-center gap-2 p-2 rounded-full bg-black/60 backdrop-blur-xl border border-white/10 shadow-[0_8px_32px_rgba(0,0,0,0.4)]"
      >
        {/* Mic Toggle */}
        <ControlButton 
          isActive={isMicOn} 
          onClick={toggleMic}
          activeColor="bg-white/10 hover:bg-white/20 text-white"
          inactiveColor="bg-red-500/20 hover:bg-red-500/30 text-red-500"
          icon={isMicOn ? <Mic size={20} /> : <MicOff size={20} />}
          label={isMicOn ? 'Mute' : 'Unmute'}
        />

        {/* Video Toggle */}
        <ControlButton 
          isActive={isVideoOn} 
          onClick={toggleVideo}
          activeColor="bg-white/10 hover:bg-white/20 text-white"
          inactiveColor="bg-red-500/20 hover:bg-red-500/30 text-red-500"
          icon={isVideoOn ? <Video size={20} /> : <VideoOff size={20} />}
          label={isVideoOn ? 'Stop Video' : 'Start Video'}
        />

        <div className="w-[1px] h-8 bg-white/10 mx-1" />

        {/* Screen Share */}
        <ControlButton 
          isActive={isScreenSharing} 
          onClick={toggleScreenShare}
          activeColor="bg-blue-500/20 hover:bg-blue-500/30 text-blue-400"
          inactiveColor="bg-white/10 hover:bg-white/20 text-white"
          icon={<MonitorUp size={20} />}
          label="Share Screen"
        />

        {/* Intelligence / AI Pulse (Glow effect when active) */}
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => toggleSidebar()}
          className={`relative group flex items-center justify-center w-12 h-12 rounded-full transition-colors ${
            activeSidebarTab === 'intelligence' 
              ? 'bg-purple-500/20 text-purple-400' 
              : 'bg-white/10 hover:bg-white/20 text-white'
          }`}
        >
          {activeSidebarTab === 'intelligence' && (
            <span className="absolute inset-0 rounded-full bg-purple-500/30 blur-md animate-pulse" />
          )}
          <Sparkles size={20} className="relative z-10" />
          <Tooltip>AI Pulse</Tooltip>
        </motion.button>

        {/* Chat */}
        <ControlButton 
          isActive={activeSidebarTab === 'chat'} 
          onClick={() => toggleSidebar()}
          activeColor="bg-white/20 text-white"
          inactiveColor="bg-white/10 hover:bg-white/20 text-white"
          icon={<MessageSquare size={20} />}
          label="Chat"
        />

        <div className="w-[1px] h-8 bg-white/10 mx-1" />

        {/* Leave Meeting (Distinctive red button) */}
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="relative group flex items-center gap-2 px-4 h-12 rounded-full bg-red-500 hover:bg-red-600 text-white shadow-[0_0_15px_rgba(239,68,68,0.4)] transition-colors"
        >
          <PhoneOff size={20} />
          <span className="font-medium text-sm pr-1">Leave</span>
        </motion.button>
      </motion.div>
    </div>
  );
};

// --- Subcomponents ---

interface ControlButtonProps {
  isActive: boolean;
  onClick: () => void;
  activeColor: string;
  inactiveColor: string;
  icon: React.ReactNode;
  label: string;
}

const ControlButton = ({ isActive, onClick, activeColor, inactiveColor, icon, label }: ControlButtonProps) => (
  <motion.button
    whileHover={{ scale: 1.05 }}
    whileTap={{ scale: 0.95 }}
    onClick={onClick}
    className={`relative group flex items-center justify-center w-12 h-12 rounded-full transition-colors ${isActive ? activeColor : inactiveColor}`}
  >
    {icon}
    <Tooltip>{label}</Tooltip>
  </motion.button>
);

const Tooltip = ({ children }: { children: React.ReactNode }) => (
  <span className="absolute -top-10 scale-0 opacity-0 group-hover:scale-100 group-hover:opacity-100 transition-all duration-200 bg-black/80 text-white text-xs py-1 px-2 rounded backdrop-blur-md border border-white/10 pointer-events-none whitespace-nowrap">
    {children}
  </span>
);
