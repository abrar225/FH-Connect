'use client';

import React, { useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MicOff } from 'lucide-react';
import { useUIStore } from '@/stores/useUIStore';

// In a real scenario, this would use LiveKit's useParticipants()
// This mock represents the architectural pattern.
interface MockParticipant {
  id: string;
  name: string;
  isSpeaking: boolean;
  isMuted: boolean;
  color: string;
}

const MOCK_PARTICIPANTS: MockParticipant[] = [
  { id: '1', name: 'You', isSpeaking: false, isMuted: true, color: 'bg-blue-900' },
  { id: '2', name: 'Sarah Connor', isSpeaking: true, isMuted: false, color: 'bg-emerald-900' },
  { id: '3', name: 'John Doe', isSpeaking: false, isMuted: false, color: 'bg-purple-900' },
];

export const FluidGrid = () => {
  const { isSidebarOpen } = useUIStore();
  
  // Calculate grid columns dynamically based on participant count and sidebar state
  const gridClass = useMemo(() => {
    const count = MOCK_PARTICIPANTS.length;
    if (count === 1) return 'grid-cols-1';
    if (count === 2) return 'grid-cols-1 md:grid-cols-2';
    if (count <= 4) return 'grid-cols-2';
    if (count <= 9) return 'grid-cols-3';
    return 'grid-cols-4';
  }, []);

  return (
    <div className={`w-full h-full p-4 transition-all duration-500 ease-in-out ${isSidebarOpen ? 'pr-[340px]' : ''}`}>
      <motion.div 
        layout
        className={`w-full h-full grid gap-4 ${gridClass} auto-rows-fr`}
      >
        <AnimatePresence>
          {MOCK_PARTICIPANTS.map((p) => (
            <ParticipantTile key={p.id} participant={p} />
          ))}
        </AnimatePresence>
      </motion.div>
    </div>
  );
};

const ParticipantTile = ({ participant }: { participant: MockParticipant }) => {
  return (
    <motion.div
      layout // This is the magic that makes tiles smoothly rearrange
      initial={{ opacity: 0, scale: 0.8, y: 20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.8 }}
      transition={{ type: 'spring', damping: 25, stiffness: 200 }}
      className={`relative w-full h-full rounded-2xl overflow-hidden shadow-lg border-2 transition-all duration-300 ${
        participant.isSpeaking ? 'border-purple-500 shadow-[0_0_20px_rgba(168,85,247,0.4)]' : 'border-transparent'
      } ${participant.color}`}
    >
      {/* Video Placeholder */}
      <div className="absolute inset-0 flex items-center justify-center text-white/50 font-medium text-4xl">
        {participant.name.charAt(0)}
      </div>
      
      {/* Participant Overlay Info */}
      <div className="absolute bottom-4 left-4 right-4 flex items-center justify-between">
        <div className="bg-black/50 backdrop-blur-md px-3 py-1.5 rounded-lg text-white text-sm font-medium">
          {participant.name}
        </div>
        
        {participant.isMuted && (
          <div className="bg-red-500/80 backdrop-blur-md p-1.5 rounded-lg text-white">
            <MicOff size={16} />
          </div>
        )}
      </div>
    </motion.div>
  );
};
