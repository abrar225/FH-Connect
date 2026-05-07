"use client";

import React, { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { ArrowRight } from "lucide-react";

export default function CallToAction({ onSignIn }: { onSignIn: () => void }) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Manifesto text scroll effect
      gsap.to(".manifesto-text", {
        backgroundPositionX: "100%",
        ease: "none",
        scrollTrigger: {
          trigger: containerRef.current,
          start: "top bottom",
          end: "bottom top",
          scrub: true,
        },
      });
      
      gsap.from(".cta-button", {
        y: 50,
        opacity: 0,
        duration: 0.8,
        ease: "back.out(1.7)",
        scrollTrigger: {
          trigger: ".cta-trigger",
          start: "top 80%",
        },
      });
    }, containerRef);
    return () => ctx.revert();
  }, []);

  return (
    <section ref={containerRef} className="relative py-32 px-6 bg-[#050505] text-[#e1e1e1] overflow-hidden flex flex-col items-center justify-center min-h-[80vh]">
      <div className="absolute inset-0 noise-overlay" />
      
      <div className="max-w-6xl mx-auto text-center z-10 w-full relative">
        <h2 
          className="manifesto-text text-[8vw] md:text-[6vw] font-heading font-black uppercase leading-[0.9] tracking-tighter text-transparent bg-clip-text"
          style={{
            backgroundImage: "linear-gradient(90deg, transparent 0%, #fff 50%, transparent 100%)",
            backgroundSize: "200% 100%",
            WebkitTextStroke: "1px rgba(255,255,255,0.2)"
          }}
        >
          TRANSFORM YOUR<br/>COLLABORATION
        </h2>

        <p className="mt-12 font-serif-italic text-lg md:text-2xl text-gray-400 max-w-2xl mx-auto">
          &quot;Step into the future where AI takes the notes, tracks the actions, and summarizes the chaos.&quot;
        </p>

        <div className="cta-trigger mt-16 relative">
          {/* A glowing border effect behind the button */}
          <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-48 h-16 bg-blue-600/30 blur-2xl rounded-full pointer-events-none" />
          
          <button
            onClick={onSignIn}
            className="cta-button interactive relative px-12 py-5 bg-[#e1e1e1] text-[#050505] font-mono font-bold uppercase tracking-[0.2em] hover:bg-white transition-all duration-300 flex items-center space-x-4 mx-auto hover:px-14 border border-[#e1e1e1]"
          >
            <span>Launch Platform</span>
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>
      </div>
      
      {/* Decorative large noise text in bg */}
      <div className="absolute bottom-[-5%] left-0 w-full text-center opacity-5 pointer-events-none overflow-hidden select-none">
        <span className="text-[25vw] font-heading font-black tracking-tighter whitespace-nowrap">
          SYSTEM ON
        </span>
      </div>
    </section>
  );
}
