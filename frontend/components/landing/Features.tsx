"use client";

import React, { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { Brain, ListChecks, FileText, Video, Shield, Zap } from "lucide-react";

const features = [
  { icon: Brain, title: "AI Intelligence", desc: "Gemini 2.0 Flash analyzes every word in real-time." },
  { icon: ListChecks, title: "Live Drafts", desc: "Action items surface instantly as interactive cards." },
  { icon: FileText, title: "Exec Summaries", desc: "One-click reports with participation metrics." },
  { icon: Video, title: "HD Video", desc: "Crystal-clear WebRTC calls powered by LiveKit." },
  { icon: Shield, title: "Host Controls", desc: "Mute participants, manage tasks, control the room." },
  { icon: Zap, title: "Instant Access", desc: "Create, schedule, and share meetings via unique codes." },
];

export default function Features() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Stagger animate cards as they come into view
      gsap.from(".feature-card", {
        y: 100,
        opacity: 0,
        duration: 0.8,
        stagger: 0.1,
        ease: "power3.out",
        scrollTrigger: {
          trigger: containerRef.current,
          start: "top 75%",
          toggleActions: "play none none reverse",
        },
      });

      // Header animation
      gsap.from(".feat-head", {
        opacity: 0,
        x: -50,
        duration: 1,
        scrollTrigger: {
          trigger: containerRef.current,
          start: "top 85%",
        },
      });
    }, containerRef);

    return () => ctx.revert();
  }, []);

  return (
    <section ref={containerRef} className="py-24 px-6 md:px-12 bg-[#e1e1e1] text-[#050505]">
      <div className="max-w-7xl mx-auto">
        <div className="feat-head mb-16 border-b-2 border-[#050505] pb-8">
          <h2 className="text-5xl md:text-7xl font-heading font-black uppercase tracking-tighter">
            Core Features
          </h2>
          <p className="mt-4 font-mono text-sm uppercase tracking-widest opacity-60">
            [ Next-Gen Capabilities built-in ]
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feat, i) => (
            <div
              key={i}
              className="feature-card interactive group p-8 border-2 border-[#050505] bg-white hover:bg-[#050505] transition-colors duration-500 flex flex-col justify-between min-h-[300px]"
            >
              <div className="flex items-center justify-between pointer-events-none">
                <feat.icon className="w-8 h-8 text-[#050505] group-hover:text-white transition-colors duration-500" />
                <span className="font-mono text-xs font-bold opacity-30 group-hover:text-white group-hover:opacity-50 transition-colors duration-500">
                  0{i + 1}
                </span>
              </div>
              
              <div className="mt-8 pointer-events-none">
                <h3 className="text-2xl font-heading font-bold uppercase mb-4 text-[#050505] group-hover:text-white transition-colors duration-500 leading-none">
                  {feat.title}
                </h3>
                <p className="font-serif-italic text-lg text-[#050505]/70 group-hover:text-[#e1e1e1]/80 transition-colors duration-500 line-clamp-3">
                  {feat.desc}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
