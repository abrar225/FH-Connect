"use client";

import React, { useEffect, ReactNode } from "react";
import Lenis from "lenis";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import CustomCursor from "./CustomCursor";

// Register ScrollTrigger globally once
if (typeof window !== "undefined") {
  gsap.registerPlugin(ScrollTrigger);
}

interface SmoothScrollLayoutProps {
  children: ReactNode;
}

export default function SmoothScrollLayout({ children }: SmoothScrollLayoutProps) {
  useEffect(() => {
    // Initialize Lenis exactly matching the referenced project
    const lenis = new Lenis({
      duration: 1.2,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      orientation: "vertical",
      gestureOrientation: "vertical",
      smoothWheel: true,
      wheelMultiplier: 1,
      touchMultiplier: 2,
    });

    lenis.on("scroll", ScrollTrigger.update);

    gsap.ticker.add((time) => {
      lenis.raf(time * 1000);
    });

    gsap.ticker.lagSmoothing(0);

    return () => {
      lenis.destroy();
      gsap.ticker.remove((time) => lenis.raf(time * 1000));
    };
  }, []);

  return (
    <div className="landing-page relative w-full min-h-screen">
      <div className="noise-overlay" />
      <CustomCursor />
      {children}
    </div>
  );
}
