"use client";

import React, { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { Sparkles, ArrowRight } from "lucide-react";

export default function Hero({ onSignIn }: { onSignIn: () => void }) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      const tl = gsap.timeline();

      // Initial clear state
      gsap.set(".hero-char", { yPercent: 120, rotateZ: 10 });

      // Chaotic text entry
      tl.to(".hero-char", {
        yPercent: 0,
        rotateZ: 0,
        stagger: 0.05,
        duration: 1.2,
        ease: "power4.out",
        delay: 0.2, // Faster initial start
      });

      gsap.from(".hero-fade", {
        opacity: 0,
        y: 20,
        duration: 1,
        stagger: 0.15,
        delay: 0.8,
      });

      // Parallax Background
      gsap.to(".hero-bg-accent", {
        yPercent: 30,
        scale: 1.1,
        scrollTrigger: {
          trigger: containerRef.current,
          start: "top top",
          end: "bottom top",
          scrub: true,
        },
      });
    }, containerRef);

    return () => ctx.revert();
  }, []);

  const title = "FIREHOX";
  const subtitle = "CONNECT";

  return (
    <section
      ref={containerRef}
      className="relative h-screen w-full overflow-hidden text-[#e1e1e1] flex flex-col justify-between p-6 md:p-12"
    >
      {/* Background gradients and blurs instead of an image to match brand */}
      <div className="hero-bg-accent absolute inset-0 z-0 opacity-50">
        <div className="absolute top-10 left-1/4 w-[500px] h-[500px] bg-blue-600/20 rounded-full blur-[150px] mix-blend-screen" />
        <div className="absolute bottom-0 right-1/4 w-[400px] h-[400px] bg-indigo-600/20 rounded-full blur-[130px] mix-blend-screen" />
      </div>

      {/* Top Header Information Area */}
      <div className="relative z-10 w-full flex justify-between items-start hero-fade pt-8">
        <div className="flex flex-col gap-2 md:gap-3">
          <div className="text-[10px] md:text-xs font-mono uppercase tracking-widest opacity-60">
            ( Est. {new Date().getFullYear()} )
          </div>
          <div className="hidden md:block text-xs font-mono uppercase tracking-wider opacity-40 max-w-[200px]">
            AI Meeting Intel <br />
            <span className="text-white/60">& Exec Summaries</span>
          </div>
        </div>

        <div className="flex text-right flex-col items-end gap-2 md:gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono uppercase tracking-wider opacity-50">
              System Status
            </span>
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          </div>
          <button
            onClick={onSignIn}
            className="interactive mt-2 px-6 py-2 border border-white/20 rounded-full uppercase text-xs tracking-wider hover:bg-white hover:text-black transition-colors duration-300 flex items-center space-x-2"
          >
            <span>Login / Start</span>
            <ArrowRight className="w-3 h-3" />
          </button>
        </div>
      </div>

      {/* Aesthetic Numbers right */}
      <div className="hidden lg:flex absolute right-12 top-1/3 z-10 flex-col gap-8 opacity-30 hero-fade">
        <div className="flex flex-col items-end gap-2 text-xs font-mono">
          <div className="w-12 h-[1px] bg-white/40" />
          <span className="text-white/60">001</span>
        </div>
        <div className="flex flex-col items-end gap-2 text-xs font-mono">
          <div className="w-8 h-[1px] bg-white/40" />
          <span className="text-white/60">002</span>
        </div>
      </div>

      {/* Brutalist Title & Bottom Section */}
      <div className="relative z-10 mb-8 md:mb-12">
        <h1 className="text-[12vw] sm:text-[10vw] leading-[0.9] font-heading font-black tracking-tighter text-white">
          <div className="flex flex-wrap overflow-hidden">
            {title.split("").map((char, i) => (
              <span
                key={i}
                className="hero-char inline-block origin-bottom will-change-transform"
              >
                {char}
              </span>
            ))}
          </div>
          <div className="flex flex-wrap overflow-hidden pl-[5vw] sm:pl-[8vw]">
            {subtitle.split("").map((char, i) => (
              <span
                key={i + 10}
                className="hero-char inline-block origin-bottom will-change-transform text-transparent"
                style={{ WebkitTextStroke: "1px rgba(255,255,255,0.7)" }}
              >
                {char}
              </span>
            ))}
          </div>
        </h1>

        <div className="flex flex-col md:flex-row md:items-end justify-between mt-8 md:mt-16 border-t border-white/20 pt-6 md:pt-8 hero-fade gap-6">
          <div className="flex-1 max-w-2xl">
            <p className="text-sm sm:text-lg md:text-2xl font-serif-italic text-gray-300 leading-snug mb-6">
              &quot;Meetings that think for you. Zero manual effort, instant executive insights.&quot;
            </p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-[10px] md:text-xs font-mono uppercase tracking-wider opacity-70">
              <div>
                <div className="text-white/40 mb-1">Engine</div>
                <div>Gemini 2.0</div>
              </div>
              <div>
                <div className="text-white/40 mb-1">Comms</div>
                <div>LiveKit WebRTC</div>
              </div>
              <div>
                <div className="text-white/40 mb-1">Processing</div>
                <div>Real-time</div>
              </div>
              <div>
                <div className="text-white/40 mb-1">Capacity</div>
                <div>Unlimited</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
