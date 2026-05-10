"use client";

import React from "react";
import { motion, HTMLMotionProps } from "framer-motion";

interface GlassContainerProps extends HTMLMotionProps<"div"> {
  children: React.ReactNode;
  className?: string;
  intensity?: "low" | "medium" | "high";
  interactive?: boolean;
}

export const GlassContainer = React.forwardRef<HTMLDivElement, GlassContainerProps>(function GlassContainer({
  children,
  className = "",
  intensity = "medium",
  interactive = false,
  ...props
}, ref) {
  const intensityMap = {
    low: "backdrop-blur-md bg-white/[0.02] border-white/[0.05]",
    medium: "backdrop-blur-xl bg-white/[0.05] border-white/[0.08]",
    high: "backdrop-blur-3xl saturate-200 bg-white/[0.08] border-white/[0.12]",
  };

  const interactiveStyles = interactive
    ? "hover:bg-white/[0.09] hover:border-white/[0.15] transition-all duration-300"
    : "";

  return (
    <motion.div
      ref={ref}
      className={`relative overflow-hidden rounded-3xl border shadow-2xl shadow-black/20 ${intensityMap[intensity]} ${interactiveStyles} ${className}`}
      {...props}
    >
      {/* Noise Texture Overlay */}
      <div 
        className="pointer-events-none absolute inset-0 z-0 opacity-[0.03]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
        }}
      />
      {children}
    </motion.div>
  );
});
