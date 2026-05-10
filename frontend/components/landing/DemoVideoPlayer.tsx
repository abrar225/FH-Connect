"use client";

import React, { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

export default function DemoVideoPlayer() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const videoContRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Scale up the video container as user scrolls into the section
      gsap.fromTo(
        videoContRef.current,
        { scale: 0.85, opacity: 0, borderRadius: "20%" },
        {
          scale: 1,
          opacity: 1,
          borderRadius: "0%",
          duration: 1,
          ease: "power2.out",
          scrollTrigger: {
            trigger: sectionRef.current,
            start: "top 80%",
            end: "center center",
            scrub: true,
          },
        }
      );
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  return (
    <section
      ref={sectionRef}
      className="relative w-full min-h-screen flex items-center justify-center py-20 px-4 md:px-8 bg-[#050505] overflow-hidden"
    >
      <div className="absolute top-0 left-0 w-full h-full video-grain opacity-30 pointer-events-none" />

      <div className="flex flex-col items-center w-full max-w-6xl z-10">
        <div className="mb-12 text-center w-full max-w-2xl">
          <h2 className="text-4xl md:text-6xl font-heading font-bold text-white uppercase tracking-tighter mb-4">
            See it in
            <br />
            <span style={{ WebkitTextStroke: "1px rgba(255,255,255,0.7)", color: "transparent" }}>
              Action
            </span>
          </h2>
          <p className="font-mono text-sm uppercase tracking-widest text-[#e1e1e1]/60">
            [ Project Demo Recording ]
          </p>
        </div>

        {/* Video Container Frame */}
        <div
          ref={videoContRef}
          className="relative w-full max-w-5xl bg-[#111] border border-white/10 overflow-hidden shadow-2xl flex items-center justify-center rounded-xl group/video"
        >
          {/* Video Player */}
          <video
            autoPlay
            loop
            muted
            playsInline
            controls
            className="w-full h-auto object-contain z-20"
            preload="metadata"
          >
            <source src="/connect-demo.mp4" type="video/mp4" />
            Your browser does not support the video tag.
          </video>
          
          {/* Subtle overlay to maintain dark aesthetic */}
          <div className="absolute inset-0 bg-black/10 pointer-events-none z-10" />

          {/* Minimalist overlays - fading out when hovering so they don't block controls */}
          <div className="absolute top-4 left-4 font-mono text-[10px] uppercase text-white/60 tracking-widest px-2 py-1 bg-black/50 backdrop-blur-md rounded-md pointer-events-none z-10 group-hover/video:opacity-0 transition-opacity duration-300">
            FH-Connect Demo
          </div>
          <div className="absolute top-4 right-4 font-mono text-[10px] uppercase text-white/60 tracking-widest flex items-center gap-2 px-2 py-1 bg-black/50 backdrop-blur-md rounded-md pointer-events-none z-10 group-hover/video:opacity-0 transition-opacity duration-300">
            <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
            REC
          </div>
        </div>
      </div>
    </section>
  );
}
