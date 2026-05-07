"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "./context/AuthContext";
import SmoothScrollLayout from "../components/landing/SmoothScrollLayout";
import Hero from "../components/landing/Hero";
import VideoPlaceholder from "../components/landing/VideoPlaceholder";
import Features from "../components/landing/Features";
import CallToAction from "../components/landing/CallToAction";

export default function LandingPage() {
  const { user, loading, signInWithGoogle } = useAuth();
  const router = useRouter();

  // Redirect logged-in users to dashboard
  useEffect(() => {
    if (!loading && user) {
      router.push("/dashboard");
    }
  }, [user, loading, router]);

  // Show brutalist loading while checking auth
  if (loading) {
    return (
      <div className="w-full h-screen bg-[#050505] flex items-center justify-center">
        <div className="w-16 h-16 border-4 border-white/20 border-t-white rounded-full animate-spin" />
      </div>
    );
  }

  // If user is logged in, show nothing (redirect is happening)
  if (user) return null;

  return (
    <SmoothScrollLayout>
      <main className="relative selection:bg-white selection:text-black">
        <Hero onSignIn={signInWithGoogle} />
        <VideoPlaceholder />
        <Features />
        <CallToAction onSignIn={signInWithGoogle} />

        {/* Brutalist Footer */}
        <footer className="border-t border-white/20 py-10 px-6 bg-[#050505] text-[#e1e1e1]">
          <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between text-xs font-mono uppercase tracking-widest opacity-60">
            <div className="flex items-center space-x-3 mb-4 md:mb-0">
              <div className="w-6 h-6 rounded-none bg-white text-black flex items-center justify-center font-bold">
                FH
              </div>
              <span>FireHox Connect</span>
            </div>
            <div className="flex items-center space-x-6">
              <span>© {new Date().getFullYear()} FireHox</span>
              <a href="#" className="interactive hover:text-white transition-colors">
                Privacy
              </a>
              <a href="#" className="interactive hover:text-white transition-colors">
                Terms
              </a>
            </div>
          </div>
        </footer>
      </main>
    </SmoothScrollLayout>
  );
}
