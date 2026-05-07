"use client";

import React, { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import PreLobby from "@/app/components/room/PreLobby";
import MeetingRoom from "@/app/components/meeting/MeetingRoom";
import { useAuth } from "@/app/context/AuthContext";
import { authFetch } from "@/app/lib/api";

export default function RoomPage() {
  const { roomId } = useParams() as { roomId: string };
  const { user, loading } = useAuth();
  
  const [hasJoined, setHasJoined] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  
  const [initialState, setInitialState] = useState({
    micEnabled: true,
    camEnabled: true,
    displayName: "",
  });

  useEffect(() => {
    async function checkMeetingAdmin() {
      if (!user) return;
      
      // Query via backend API (bypasses Supabase RLS)
        try {
        const resp = await authFetch(`/debug/meeting/${roomId}`);
        const data = await resp.json();
        
        if (data.error) {
          setIsInitializing(false);
          return;
        }

        // Determine admin: check admins array first, then fallback to created_by
        const admins: string[] = data.admins || [];
        const createdBy: string = data.created_by || "";
        const userIsAdmin = admins.includes(user.id) || createdBy === user.id;

        if (userIsAdmin) {
          setIsAdmin(true);
          // By-pass the lobby for admins
          setInitialState(prev => ({ ...prev, displayName: user.name || `Admin-${Math.random().toString(36).substring(2, 6)}` }));
          setHasJoined(true);
        }
      } catch {
        // Non-admins continue through the lobby.
      }
      setIsInitializing(false);
    }
    
    if (!loading && user) {
      checkMeetingAdmin();
    } else if (!loading && !user) {
      setIsInitializing(false);
    }
  }, [user, loading, roomId]);

  const handleJoin = (settings: { micEnabled: boolean; camEnabled: boolean; displayName: string }) => {
    setInitialState(settings);
    setHasJoined(true);
  };

  if (loading || isInitializing) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="w-10 h-10 rounded-xl bg-primary animate-pulse" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex h-screen items-center justify-center bg-background p-6 text-center">
        <div className="bg-surface/50 p-8 rounded-3xl border border-white/5 backdrop-blur-xl max-w-sm w-full">
          <h1 className="text-2xl font-bold text-white mb-4">Sign in Required</h1>
          <p className="text-gray-400 mb-8 leading-relaxed">
            Please sign in to join <span className="text-primary font-mono">{roomId}</span>.
          </p>
          <a
            href="/"
            className="block w-full py-3 bg-gradient-to-r from-primary to-indigo-600 text-white rounded-xl font-semibold shadow-lg shadow-primary/25 hover:scale-[1.02] active:scale-[0.98] transition-all"
          >
            Go Home
          </a>
        </div>
      </div>
    );
  }

  if (!hasJoined) {
    return <PreLobby roomId={roomId} onJoin={handleJoin} />;
  }

  return (
    <MeetingRoom 
      roomId={roomId} 
      initialMicEnabled={initialState.micEnabled} 
      initialCamEnabled={initialState.camEnabled} 
      isAdmin={isAdmin}
      displayName={initialState.displayName}
    />
  );
}
