"use client";

import React, { useCallback, useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  useLocalParticipant,
  useRoomContext,
} from "@livekit/components-react";
import {
  Mic,
  MicOff,
  Video,
  VideoOff,
  MonitorUp,
  PhoneOff,
  ChevronUp,
  Check,
  MoreHorizontal,
  Hand,
  Settings,
  Languages,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useDraftStore } from "@/app/store/draftStore";
import { useToast } from "@/app/components/ui/ToastProvider";

import { authFetch } from "@/app/lib/api";
import { GlassContainer } from "@/app/components/ui/GlassContainer";

interface MeetingControlBarProps {
  isAdmin?: boolean;
  roomId?: string;
  userId?: string;
}

export default function MeetingControlBar({ isAdmin: isAdminProp = false, roomId = "", userId = "" }: MeetingControlBarProps) {
  const room = useRoomContext();
  const router = useRouter();
  const { localParticipant, isMicrophoneEnabled, isCameraEnabled, isScreenShareEnabled } =
    useLocalParticipant();
  const { transcriptions, drafts, setReport, showCaptions, setShowCaptions } = useDraftStore();
  const storeIsAdmin = useDraftStore((state) => state.isAdmin);
  const isRoomLocked = useDraftStore((state) => state.isLocked);
  const setIsRoomLocked = useDraftStore((state) => state.setIsLocked);
  const { toast } = useToast();

  // Use reactive store value (updated via WebSocket), fallback to prop
  const isAdmin = storeIsAdmin || isAdminProp;
  
  const [isEnding, setIsEnding] = useState(false);
  const [showMicMenu, setShowMicMenu] = useState(false);
  const [showCameraMenu, setShowCameraMenu] = useState(false);

  const [showMoreMenu, setShowMoreMenu] = useState(false);

  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setShowMicMenu(false);
        setShowCameraMenu(false);
        setShowMoreMenu(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleMuteAll = async () => {
    setShowMoreMenu(false);
    try {
      await authFetch(`/api/meeting/${roomId}/mute-all`, {
        method: 'POST',
        body: JSON.stringify({})
      });
      toast("success", "Muted All", "All other participants have been muted.");
    } catch(e) {
      toast("error", "Error", "Failed to mute participants.");
    }
  }

  const handleToggleLock = async () => {
    setShowMoreMenu(false);
    try {
      const res = await authFetch(`/api/meeting/${roomId}/lock?locked=${!isRoomLocked}`, {
        method: 'POST',
        body: JSON.stringify({})
      });
      if(res.ok) {
        setIsRoomLocked(!isRoomLocked);
        toast("success", !isRoomLocked ? "Meeting Locked" : "Meeting Unlocked", !isRoomLocked ? "No new participants can join." : "Anyone can join.");
      }
    } catch (e) {
      toast("error", "Error", "Failed to lock/unlock meeting.");
    }
  }

  const toggleMic = useCallback(async () => {
    await localParticipant.setMicrophoneEnabled(!isMicrophoneEnabled);
  }, [localParticipant, isMicrophoneEnabled]);

  const toggleCamera = useCallback(async () => {
    await localParticipant.setCameraEnabled(!isCameraEnabled);
  }, [localParticipant, isCameraEnabled]);

  const toggleScreenShare = useCallback(async () => {
    await localParticipant.setScreenShareEnabled(!isScreenShareEnabled);
  }, [localParticipant, isScreenShareEnabled]);

  const handleEndMeeting = useCallback(() => {
    setIsEnding(true);
    toast("info", "Leaving Meeting", "Redirecting to dashboard...");
    
    // Trigger report generation in the background
    authFetch("/api/meeting/end", {
      method: "POST",
      body: JSON.stringify({
        room_id: room.name,
        transcripts: transcriptions,
        approved_tasks: drafts
      }),
    }).catch(() => toast("error", "Report Error", "Could not generate the final report."));

    room.disconnect();
    router.push("/dashboard/reports");
  }, [transcriptions, drafts, room, toast, router]);

  const ControlButton = ({ 
    icon: Icon, 
    onClick, 
    active = true, 
    danger = false, 
    label,
    hasMenu = false,
    onMenuClick = () => {}
  }: any) => (
    <motion.div 
      whileHover={{ scale: 1.1, y: -4 }}
      whileTap={{ scale: 0.95 }}
      className="relative group flex items-center"
    >
      <button
        onClick={onClick}
        className={`flex flex-col items-center justify-center w-14 h-14 rounded-2xl transition-all duration-300 ${
          danger 
            ? "bg-red-500/10 hover:bg-red-500 text-red-500 hover:text-white" 
            : !active 
              ? "bg-red-500/10 text-red-500" 
              : "bg-white/5 hover:bg-white/10 text-white/70 hover:text-white"
        } border border-white/5 shadow-lg backdrop-blur-md`}
      >
        <Icon className="w-6 h-6" strokeWidth={1.5} />
        <span className="absolute bottom-full mb-3 opacity-0 group-hover:opacity-100 transition-all bg-black/80 backdrop-blur-md px-3 py-1.5 rounded-xl text-[10px] uppercase font-bold tracking-widest text-white/70 whitespace-nowrap pointer-events-none border border-white/10 z-[100] shadow-2xl">
          {label}
        </span>
      </button>
      {hasMenu && (
        <button 
          onClick={onMenuClick}
          className="absolute right-1 bottom-1 w-4 h-4 bg-white/10 rounded-full flex items-center justify-center hover:bg-white/20 transition-colors z-10"
        >
          <ChevronUp className="w-2.5 h-2.5 text-white/50" />
        </button>
      )}
    </motion.div>
  );

  return (
    <div className="absolute bottom-10 left-1/2 -translate-x-1/2 z-50 pointer-events-none flex flex-col items-center">
      
      {/* Menus and Dropups - placed above the bar */}
      <AnimatePresence>
        {showMicMenu && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.9, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 10 }}
            className="mb-4 w-60 bg-surface-raised/95 backdrop-blur-2xl border border-white/10 rounded-[2rem] shadow-[0_20px_50px_rgba(0,0,0,0.5)] p-3 pointer-events-auto"
          >
            <div className="px-3 py-1.5 text-[10px] font-bold text-white/30 uppercase tracking-widest">Microphone</div>
            <button className="w-full flex items-center justify-between px-3 py-2 rounded-lg hover:bg-white/5 text-sm text-white/80">
              <span>MacBook Pro Mic</span>
              <Check className="w-4 h-4 text-primary" />
            </button>
            <div className="h-px bg-white/5 my-1" />
            <div className="px-3 py-1.5 text-[10px] font-bold text-white/30 uppercase tracking-widest">Speaker</div>
            <button className="w-full flex items-center justify-between px-3 py-2 rounded-lg hover:bg-white/5 text-sm text-white/80">
              <span>System (Default)</span>
              <Check className="w-4 h-4 text-primary" />
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {isAdmin && showMoreMenu && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.9, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 10 }}
            className="mb-4 w-48 bg-surface-raised/95 backdrop-blur-2xl border border-white/10 rounded-[1.5rem] shadow-[0_20px_50px_rgba(0,0,0,0.5)] p-2 pointer-events-auto"
          >
            <div className="px-3 py-1.5 text-[10px] font-bold text-white/30 uppercase tracking-widest">Admin Actions</div>
            <button onClick={handleMuteAll} className="w-full text-left px-3 py-2 rounded-lg hover:bg-white/5 text-sm text-white/80">
              Mute All
            </button>
            <button onClick={handleToggleLock} className="w-full text-left px-3 py-2 rounded-lg hover:bg-white/5 text-sm text-white/80">
              {isRoomLocked ? "Unlock Meeting" : "Lock Meeting"}
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      <GlassContainer
        intensity="high"
        initial={{ y: 100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="flex items-center space-x-3 px-4 py-3 rounded-[2rem] shadow-[0_20px_50px_rgba(0,0,0,0.5)] pointer-events-auto relative overflow-visible"
        ref={containerRef as any}
      >
        <ControlButton 
          icon={isMicrophoneEnabled ? Mic : MicOff} 
          onClick={toggleMic} 
          active={isMicrophoneEnabled}
          label={isMicrophoneEnabled ? "Mute" : "Unmute"}
          hasMenu={true}
          onMenuClick={() => setShowMicMenu(!showMicMenu)}
        />
        <ControlButton 
          icon={isCameraEnabled ? Video : VideoOff} 
          onClick={toggleCamera} 
          active={isCameraEnabled}
          label={isCameraEnabled ? "Stop Video" : "Start Video"}
          hasMenu={true}
          onMenuClick={() => setShowCameraMenu(!showCameraMenu)}
        />
        
        <div className="w-px h-10 bg-white/10 mx-1" />

        <ControlButton 
          icon={MonitorUp} 
          onClick={toggleScreenShare} 
          active={!isScreenShareEnabled}
          label="Share Screen"
        />
        <ControlButton 
          icon={Hand} 
          label="Raise Hand"
        />
        <ControlButton 
          icon={Languages} 
          onClick={() => setShowCaptions(!showCaptions)}
          active={showCaptions}
          label={showCaptions ? "Hide Captions" : "Show Captions"}
        />
        {isAdmin && (
          <ControlButton 
            icon={MoreHorizontal} 
            label="More Actions"
            onClick={() => setShowMoreMenu(!showMoreMenu)}
            active={showMoreMenu}
          />
        )}
        
        <div className="w-px h-10 bg-white/10 mx-1" />

        <ControlButton 
          icon={PhoneOff} 
          onClick={handleEndMeeting} 
          danger={true}
          label="Leave Meeting"
        />
      </GlassContainer>
    </div>
  );
}
