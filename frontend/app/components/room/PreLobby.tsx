"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { Mic, MicOff, Video, VideoOff, Settings, Sparkles, LogIn, ShieldAlert } from "lucide-react";
import { useAuth } from "@/app/context/AuthContext";
import { useMediaStream } from "@/app/hooks/useMediaStream";

interface PreLobbyProps {
  roomId: string;
  onJoin: (settings: { micEnabled: boolean; camEnabled: boolean; displayName: string }) => void;
}

export default function PreLobby({ roomId, onJoin }: PreLobbyProps) {
  const { user } = useAuth();
  const [micEnabled, setMicEnabled] = useState(true);
  const [camEnabled, setCamEnabled] = useState(true);
  const [displayName, setDisplayName] = useState("");

  useEffect(() => {
    if (user?.name) {
      setDisplayName(user.name);
    } else {
      setDisplayName(`User-${Math.random().toString(36).substring(2, 6)}`);
    }
  }, [user]);

  const { videoRef, permissionError, audioLevel } = useMediaStream(camEnabled, micEnabled);

  const toggleMic = () => setMicEnabled(!micEnabled);
  const toggleCam = () => setCamEnabled(!camEnabled);

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-6 bg-[radial-gradient(circle_at_top_right,_var(--tw-gradient-stops))] from-indigo-500/10 via-background to-background">
      <div className="max-w-4xl w-full">
        {/* Header Section */}
        <motion.div
           initial={{ opacity: 0, y: -20 }}
           animate={{ opacity: 1, y: 0 }}
           className="text-center mb-10"
        >
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-bold mb-4 uppercase tracking-widest">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Ready to Join</span>
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">Setup your hardware</h1>
          <p className="text-gray-400">Meeting Room: <span className="text-gray-300 font-mono">{roomId}</span></p>
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-8 items-center">
          {/* LEFT: Video Preview */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
            className="aspect-video bg-surface overflow-hidden rounded-3xl border-4 border-white/5 relative shadow-2xl shadow-black/40 group"
          >
            {camEnabled ? (
               <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover mirror" />
            ) : (
              <div className="w-full h-full flex flex-col items-center justify-center bg-surface-raised">
                <div className="w-20 h-20 rounded-full bg-white/5 flex items-center justify-center mb-4">
                   <VideoOff className="w-8 h-8 text-gray-500" />
                </div>
                <p className="text-gray-500 font-medium">Camera is Off</p>
              </div>
            )}

            {/* Error Message Overlay */}
            {permissionError && (
              <div className="absolute inset-0 z-20 bg-black/80 backdrop-blur-md flex flex-col items-center justify-center p-8 text-center">
                <ShieldAlert className="w-12 h-12 text-red-500 mb-4" />
                <h3 className="text-white font-bold text-lg mb-2">Permission Denied</h3>
                <p className="text-gray-400 text-sm max-w-xs">{permissionError}</p>
                <button 
                   onClick={() => window.location.reload()}
                   className="mt-6 px-5 py-2 bg-white/10 hover:bg-white/20 text-white rounded-xl text-sm transition-colors border border-white/10"
                >
                  Try Again
                </button>
              </div>
            )}

            {/* Float HUD */}
            <div className="absolute bottom-4 left-4 right-4 flex items-center justify-between pointer-events-none">
              <div className="flex items-center space-x-2 pointer-events-auto">
                <input
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  className="px-3 py-1.5 rounded-lg bg-black/40 backdrop-blur-md border border-white/10 text-white text-xs font-medium focus:outline-none focus:border-primary w-32 md:w-48 transition-all"
                  placeholder="Your Name"
                />
              </div>
              <div className="flex items-center space-x-2">
                 <div className="w-1.5 h-10 bg-white/10 rounded-full overflow-hidden relative rotate-180">
                    <motion.div 
                      className="absolute bottom-0 w-full bg-primary"
                      animate={{ height: `${Math.min(audioLevel * 100, 100)}%` }}
                      transition={{ type: "spring", stiffness: 300, damping: 30 }}
                    />
                 </div>
              </div>
            </div>
          </motion.div>

          {/* RIGHT: Presence & Controls */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="flex flex-col space-y-6"
          >
            <div className="p-6 rounded-3xl bg-surface/40 backdrop-blur-xl border border-white/10">
              <h3 className="text-white font-semibold mb-6">Device Controls</h3>
              <div className="grid grid-cols-2 gap-4">
                 <button 
                  onClick={toggleMic}
                  className={`flex flex-col items-center justify-center p-5 rounded-2xl border-2 transition-all group ${
                    micEnabled 
                      ? "bg-primary/5 border-primary/20 hover:border-primary/40 text-primary" 
                      : "bg-surface-raised border-white/5 hover:border-white/10 text-gray-500"
                  }`}
                 >
                    {micEnabled ? <Mic className="w-6 h-6 mb-3" /> : <MicOff className="w-6 h-6 mb-3" />}
                    <span className="text-xs font-bold uppercase tracking-widest">{micEnabled ? 'On' : 'Off'}</span>
                 </button>

                 <button 
                  onClick={toggleCam}
                  className={`flex flex-col items-center justify-center p-5 rounded-2xl border-2 transition-all group ${
                    camEnabled
                      ? "bg-primary/5 border-primary/20 hover:border-primary/40 text-primary" 
                      : "bg-surface-raised border-white/5 hover:border-white/10 text-gray-500"
                  }`}
                 >
                    {camEnabled ? <Video className="w-6 h-6 mb-3" /> : <VideoOff className="w-6 h-6 mb-3" />}
                    <span className="text-xs font-bold uppercase tracking-widest">{camEnabled ? 'On' : 'Off'}</span>
                 </button>
              </div>

              <button className="w-full mt-6 flex items-center justify-center space-x-2 p-3 text-gray-400 hover:text-white transition-colors text-sm font-medium">
                <Settings className="w-4 h-4" />
                <span>Advanced Settings</span>
              </button>
            </div>

            <button 
              onClick={() => onJoin({ micEnabled, camEnabled, displayName })}
              className="w-full py-4 rounded-3xl bg-gradient-to-r from-primary to-indigo-600 text-white font-bold text-lg shadow-xl shadow-primary/30 hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center space-x-3"
            >
              <span>Join Meeting Now</span>
              <LogIn className="w-5 h-5" />
            </button>
            
            <p className="text-center text-xs text-gray-500 px-8">
              By joining, you agree to allow FH-Connect to record and process the meeting for AI insights.
            </p>
          </motion.div>
        </div>
      </div>

      <style jsx>{`
        .mirror {
          transform: scaleX(-1);
        }
      `}</style>
    </div>
  );
}
