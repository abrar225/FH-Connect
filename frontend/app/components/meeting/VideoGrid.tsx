import React from "react";

// Mock user config for now
const PARTICIPANTS = [
  { id: 1, name: "Abrar", color: "bg-blue-500" },
  { id: 2, name: "Rahul", color: "bg-emerald-500" },
  { id: 3, name: "Sarah", color: "bg-purple-500" },
];

export default function VideoGrid() {
  return (
    <div className="flex-1 h-full p-6 grid grid-cols-2 grid-rows-2 gap-4">
      {PARTICIPANTS.map((p, idx) => (
        <div
          key={p.id}
          className={`relative rounded-3xl overflow-hidden glass-panel flex flex-col items-center justify-center ${
            idx === 0 ? "col-span-2 row-span-1" : ""
          }`}
        >
          {/* Simulated Video Placeholder */}
          <div className={`w-24 h-24 rounded-full flex items-center justify-center text-3xl font-bold bg-gradient-to-br from-white/10 to-transparent border border-white/20`}>
            {p.name[0]}
          </div>
          
          <div className="absolute bottom-4 left-4 bg-surface/80 backdrop-blur-md px-3 py-1 rounded-lg text-sm font-medium border border-white/10">
            {p.name}
          </div>
        </div>
      ))}
    </div>
  );
}
