"use client";

import React, { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  LiveKitRoom,
  GridLayout,
  ParticipantTile,
  useTracks,
  useLocalParticipant,
  useRoomContext,
  useRemoteParticipants,
  RoomAudioRenderer,
} from "@livekit/components-react";
import "@livekit/components-styles";
import { Track, RoomEvent, DataPacket_Kind } from "livekit-client";
import { useAuth } from "@/app/context/AuthContext";
import TranscriptionSidebar from "./TranscriptionSidebar";
import MeetingControlBar from "./MeetingControlBar";
import FloatingCaptions from "./FloatingCaptions";
import { useMeetingSocket } from "../../hooks/useMeetingSocket";
import { useInitialDrafts } from "../../hooks/useInitialDrafts";
import { useTranscription } from "../../hooks/useTranscription";
import { MessageSquare, ChevronRight, ChevronLeft, Users } from "lucide-react";
import { useDraftStore } from "../../store/draftStore";
import ReportCard from "./ReportCard";
import FeatureSidebar from "./FeatureSidebar";

const LIVEKIT_URL = process.env.NEXT_PUBLIC_LIVEKIT_URL || "";
import { authFetch } from "@/app/lib/api";

function VideoStage() {
  const tracks = useTracks(
    [
      { source: Track.Source.Camera, withPlaceholder: true },
      { source: Track.Source.ScreenShare, withPlaceholder: false },
    ],
    { onlySubscribed: false }
  );

  return (
    <motion.div layout className="flex-1 h-full p-4 relative min-w-0">
      <GridLayout
        tracks={tracks}
        style={{
          height: "calc(100% - 120px)",
          borderRadius: "1.5rem",
          overflow: "hidden",
        }}
      >
        <ParticipantTile />
      </GridLayout>
    </motion.div>
  );
}

interface MeetingRoomProps {
  roomId: string;
  initialMicEnabled?: boolean;
  initialCamEnabled?: boolean;
  isAdmin?: boolean;
  displayName?: string;
}

export default function MeetingRoom({ 
  roomId, 
  initialMicEnabled = true, 
  initialCamEnabled = true,
  isAdmin = false,
  displayName = `User-${Math.random().toString(36).substring(2, 6)}`
}: MeetingRoomProps) {
  const [token, setToken] = useState<string>("");
  const [isConnected, setIsConnected] = useState(false);
  const [permissionsGranted, setPermissionsGranted] = useState(false);
  const [permissionError, setPermissionError] = useState<string | null>(null);
  const [roomName] = useState(roomId); // Use the prop!
  const [participantName] = useState(displayName);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isFeatureSidebarOpen, setIsFeatureSidebarOpen] = useState(true);
  const { user } = useAuth();
  
  // Create a strict and stable identity for the current session.
  // This identifier MUST be the same for the WebSocket connection and the LiveKit token identity.
  // The backend signs LiveKit and WebSocket sessions for this Supabase user id.
  const [sessionIdentity] = useState(() => user?.id || "");
  const userId = sessionIdentity;

  const addTranscription = useDraftStore((state) => state.addTranscription);
  const setStoreAdmin = useDraftStore((state) => state.setIsAdmin);
  const setStoreUserId = useDraftStore((state) => state.setUserId);
  const setAIHealth = useDraftStore((state) => state.setAIHealth);

  // Sync admin state and userId into the global store
  useEffect(() => {
    setStoreAdmin(isAdmin);
    setStoreUserId(userId);
  }, [isAdmin, userId, setStoreAdmin, setStoreUserId]);

  // Initialize real-time drafts pipeline
  const { ws } = useMeetingSocket(roomId, userId);
  useInitialDrafts(roomId);

  // Step 1: Request BOTH camera AND microphone permissions upfront
  const requestPermissions = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
        video: true,
      });
      // Stop the preview tracks — LiveKit will create its own
      stream.getTracks().forEach((track) => track.stop());
      setPermissionsGranted(true);
      setPermissionError(null);
    } catch (err: any) {
      setPermissionError(
        err.name === "NotAllowedError"
          ? "Camera & Microphone access denied. Please allow both permissions and reload."
          : "Could not access media devices. Please check your camera and microphone."
      );
    }
  }, []);

  // Step 2: Fetch a signed token from our backend
  const fetchToken = useCallback(async () => {
    try {
      const res = await authFetch(
        `/api/livekit/token?room_name=${encodeURIComponent(
          roomName
        )}&participant_name=${encodeURIComponent(participantName)}`
      );
      if (!res.ok) {
        if (res.status === 403) {
          throw new Error("This meeting room is currently locked.");
        }
        throw new Error("Token fetch failed");
      }
      const data = await res.json();
      setToken(data.token);
    } catch (e: any) {
      setPermissionError(e.message || "Failed to join meeting room.");
    }
  }, [roomName, participantName]);

  useEffect(() => {
    requestPermissions();
  }, [requestPermissions]);

  useEffect(() => {
    if (permissionsGranted) {
      fetchToken();
    }
  }, [permissionsGranted, fetchToken]);

  useEffect(() => {
    if (!permissionsGranted || !roomId) return;
    let alive = true;

    const runPreflight = async () => {
      setAIHealth({
        overall: "checking",
        message: "Checking microphone, backend, transcription, workers, and AI provider...",
        checks: {},
      });
      const micPermission = permissionsGranted
        ? {
            ok: true,
            label: "Microphone permission",
            detail: "Browser microphone permission is granted.",
          }
        : {
            ok: false,
            label: "Microphone permission",
            detail: "Browser microphone permission is not granted.",
          };
      try {
        const res = await authFetch(`/api/meeting/${roomId}/ai-health`);
        if (!alive) return;
        if (res.ok) {
          const health = await res.json();
          setAIHealth({
            overall: health.overall,
            message: health.message,
            checks: {
              microphone_permission: micPermission,
              ...(health.checks || {}),
            },
          });
        } else {
          setAIHealth({
            overall: "unavailable",
            message: "AI preflight could not be completed. Backend or authentication is unavailable.",
            checks: { microphone_permission: micPermission },
          });
        }
      } catch {
        if (!alive) return;
        setAIHealth({
          overall: "unavailable",
          message: "AI preflight could not be completed. Backend or authentication is unavailable.",
          checks: { microphone_permission: micPermission },
        });
      }
    };

    void runPreflight();
    const interval = window.setInterval(runPreflight, 60000);
    return () => {
      alive = false;
      window.clearInterval(interval);
    };
  }, [permissionsGranted, roomId, setAIHealth]);

  // Loading / Permission request screen
  if (!permissionsGranted || !token) {
    return (
      <div className="w-full h-screen bg-background text-foreground flex items-center justify-center relative">
        {/* Subtle background glow */}
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-primary/10 blur-[120px] rounded-full" />
        
        <div className="flex flex-col items-center space-y-6 max-w-md text-center px-6 relative z-10">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary to-indigo-600 flex items-center justify-center font-bold text-white text-2xl shadow-xl shadow-primary/30 animate-pulse">
            FH
          </div>
          
          <h2 className="text-xl font-semibold text-white">FireHox Connect</h2>

          {permissionError ? (
            <div className="space-y-4">
              <div className="bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3">
                <p className="text-red-400 text-sm font-medium">{permissionError}</p>
              </div>
              <button
                onClick={requestPermissions}
                className="px-6 py-2.5 rounded-xl bg-primary/20 text-primary hover:bg-primary/30 transition-all text-sm font-medium border border-primary/30 hover:scale-105"
              >
                Try Again
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center justify-center space-x-2">
                <div className="w-2 h-2 rounded-full bg-primary animate-bounce [animation-delay:0ms]" />
                <div className="w-2 h-2 rounded-full bg-primary animate-bounce [animation-delay:150ms]" />
                <div className="w-2 h-2 rounded-full bg-primary animate-bounce [animation-delay:300ms]" />
              </div>
              <p className="text-gray-400 text-sm">
                {!permissionsGranted
                  ? "Requesting camera & microphone access..."
                  : "Connecting to meeting room..."}
              </p>
              <p className="text-gray-600 text-xs">
                Please allow both camera and microphone when prompted
              </p>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-screen bg-background text-foreground flex overflow-hidden relative font-sans">
      {/* Background Ambience */}
      <div className="absolute top-[-10%] left-[-10%] w-1/2 h-1/2 bg-blue-600/20 blur-[150px] rounded-full pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-1/2 h-1/2 bg-indigo-600/10 blur-[150px] rounded-full pointer-events-none" />

      {/* Main Container with Both Sidebars */}
      <div className="flex-1 flex flex-col relative z-10 overflow-hidden">
        {/* Top Bar / Header */}
        <header className="w-full h-16 flex items-center justify-between px-8 border-b border-white/5 bg-surface/30 backdrop-blur-md shrink-0">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-primary/20">
              FH
            </div>
            <h1 className="font-semibold tracking-wide text-white/90">
              Sprint Planning
            </h1>
            <div
              className={`px-2 py-0.5 rounded-full text-xs font-medium border ml-4 flex items-center transition-colors ${
                isConnected
                  ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/20"
                  : "bg-amber-500/20 text-amber-400 border-amber-500/20"
              }`}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full mr-2 animate-pulse ${
                  isConnected ? "bg-emerald-500" : "bg-amber-500"
                }`}
              />
              {isConnected ? "Connected" : "Connecting..."}
            </div>
            <div className="px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400 text-xs font-medium border border-blue-500/20 ml-2">
              {participantName}
            </div>
          </div>

          <div className="flex items-center space-x-3">
             {/* Header remains clean now */}
          </div>
        </header>

        <div className="flex-1 flex overflow-hidden relative">
           {/* Floating Opener - Features (Left) */}
           <AnimatePresence>
            {!isFeatureSidebarOpen && (
              <motion.button
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                onClick={() => setIsFeatureSidebarOpen(true)}
                className="absolute left-0 bottom-32 z-30 bg-primary/20 backdrop-blur-xl border-y border-r border-primary/20 p-3 rounded-r-2xl text-primary hover:bg-primary/30 transition-all shadow-xl group border-l-0"
              >
                <ChevronRight className="w-5 h-5 group-hover:scale-110 transition-transform" />
              </motion.button>
            )}
           </AnimatePresence>

           {/* Floating Opener - Transcripts (Right) */}
           <AnimatePresence>
            {!isSidebarOpen && (
              <motion.button
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                onClick={() => setIsSidebarOpen(true)}
                className="absolute right-0 bottom-32 z-30 bg-primary text-white p-3 rounded-l-2xl hover:bg-primary/90 transition-all shadow-xl group border border-primary/20 shadow-primary/20 border-r-0"
              >
                <ChevronLeft className="w-5 h-5 group-hover:scale-110 transition-transform" />
              </motion.button>
            )}
           </AnimatePresence>

            <LiveKitRoom
              video={initialCamEnabled}
              audio={initialMicEnabled}
              token={token}
              serverUrl={LIVEKIT_URL}
              data-lk-theme="default"
              onConnected={() => setIsConnected(true)}
              onDisconnected={() => setIsConnected(false)}
              className="flex-1 flex flex-row relative"
              style={{ background: "transparent" }}
            >
               {/* Left Sidebar: Meeting Features - Now inside context */}
               <AnimatePresence>
                {isFeatureSidebarOpen && (
                  <motion.div 
                    initial={{ width: 0, opacity: 0 }}
                    animate={{ width: 330, opacity: 1 }}
                    exit={{ width: 0, opacity: 0 }}
                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                    className="h-full z-20 overflow-hidden bg-background/80"
                  >
                    <div className="w-[330px] h-full">
                      <FeatureSidebar onClose={() => setIsFeatureSidebarOpen(false)} isAdmin={isAdmin} userId={userId} roomId={roomId} ws={ws} />
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              <VideoStage />
              <RoomAudioRenderer />
              <MeetingControlBar isAdmin={isAdmin} roomId={roomId} userId={userId} />
              <TranscriptionAgent 
                participantName={participantName} 
                userId={userId} 
                roomId={roomId} 
              />
              <DataSubscriber />

              <FloatingCaptions />

              {/* Right Sidebar: AI Intelligence */}
              <AnimatePresence>
                {isSidebarOpen && (
                  <motion.div 
                    initial={{ width: 0, opacity: 0 }}
                    animate={{ width: 380, opacity: 1 }}
                    exit={{ width: 0, opacity: 0 }}
                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                    className="h-full z-20 overflow-hidden bg-background/80"
                  >
                    <div className="w-[380px] h-full">
                      <TranscriptionSidebar onClose={() => setIsSidebarOpen(false)} isAdmin={isAdmin} roomId={roomId} />
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </LiveKitRoom>
        </div>
      </div>

      <ReportCard />
    </div>
  );
}

/** Invisible component that captures speech and sends it to the backend.
 *  Lives inside <LiveKitRoom> so it can read the local participant's mic state. */
function TranscriptionAgent({ participantName, userId, roomId }: { participantName: string, userId: string, roomId: string }) {
  const { isMicrophoneEnabled, localParticipant } = useLocalParticipant();
  const remoteParticipants = useRemoteParticipants();
  
  const activeUsers = [
    localParticipant.name || participantName,
    ...remoteParticipants.map(p => p.name || p.identity)
  ].filter(Boolean);
  
  const handleTranscript = useCallback((text: string) => {
    const data = JSON.stringify({
      type: "transcription",
      text,
      speaker: participantName
    });
    const encoder = new TextEncoder();
    localParticipant.publishData(encoder.encode(data), {
      reliable: true
    });
  }, [localParticipant, participantName]);

  useTranscription(isMicrophoneEnabled, participantName, userId, roomId, activeUsers, handleTranscript);
  return null;
}


/** Component that listens for data messages within the room */
function DataSubscriber() {
    const room = useRoomContext();
    const addTranscription = useDraftStore((state) => state.addTranscription);

    useEffect(() => {
        if (!room) return;

        const handleData = (payload: Uint8Array, participant: any) => {
            const dataStr = new TextDecoder().decode(payload);
            try {
                const data = JSON.parse(dataStr);
                if (data.type === "transcription") {
                    addTranscription({
                        id: crypto.randomUUID(),
                        text: data.text,
                        speaker: data.speaker,
                        timestamp: new Date().toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                            second: "2-digit",
                        }),
                    });
                }
            } catch (e) {}
        };

        room.on(RoomEvent.DataReceived, handleData);
        return () => {
            room.off(RoomEvent.DataReceived, handleData);
        };
    }, [room, addTranscription]);

    return null;
}
