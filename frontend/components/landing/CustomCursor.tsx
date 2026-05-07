"use client";

import React, { useEffect, useRef } from "react";
import { gsap } from "gsap";

export default function CustomCursor() {
  const cursorRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const cursor = cursorRef.current;
    if (!cursor) return;

    // We only enable this for devices with a fine pointer (mouse)
    if (window.matchMedia("(pointer: coarse)").matches) {
      cursor.style.display = "none";
      return;
    }

    // Faster updates without requestAnimationFrame for better response
    let mouseX = 0;
    let mouseY = 0;
    
    // Smooth cursor follow
    gsap.set(cursor, { xPercent: -50, yPercent: -50 });

    const pos = { x: window.innerWidth / 2, y: window.innerHeight / 2 };
    const handleMouseMove = (e: MouseEvent) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
    };

    window.addEventListener("mousemove", handleMouseMove);

    const ticker = gsap.ticker.add(() => {
      // Linear interpolation for smooth trailing
      pos.x += (mouseX - pos.x) * 0.2;
      pos.y += (mouseY - pos.y) * 0.2;
      gsap.set(cursor, {
        x: pos.x,
        y: pos.y
      });
    });

    // Handle hover states on interactive elements
    const handleMouseOver = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (
        target.tagName.toLowerCase() === "a" ||
        target.tagName.toLowerCase() === "button" ||
        target.closest("a") ||
        target.closest("button") ||
        target.classList.contains("interactive")
      ) {
        cursor.classList.add("hovered");
      }
    };

    const handleMouseOut = () => {
      cursor.classList.remove("hovered");
    };

    window.addEventListener("mouseover", handleMouseOver);
    window.addEventListener("mouseout", handleMouseOut);

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseover", handleMouseOver);
      window.removeEventListener("mouseout", handleMouseOut);
      gsap.ticker.remove(ticker);
    };
  }, []);

  return <div ref={cursorRef} className="custom-cursor" />;
}
