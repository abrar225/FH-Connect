"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth } from "../context/AuthContext";
import { useRouter, usePathname } from "next/navigation";
import {
  Home,
  Video,
  Settings,
  LogOut,
  Menu,
  X,
  Clock,
  Calendar,
  ClipboardList
} from "lucide-react";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, loading, authError, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // Authentication check protection
  React.useEffect(() => {
    if (!loading && !user) {
      router.push("/");
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <div className="w-full h-screen bg-background flex flex-col items-center justify-center">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-indigo-600 animate-pulse mb-4" />
        <p className="text-gray-400 text-sm animate-pulse">Loading dashboard...</p>
        {authError && <p className="mt-3 max-w-sm text-center text-xs text-amber-300">{authError}</p>}
      </div>
    );
  }

  if (!user) {
    return (
      <div className="w-full h-screen bg-background flex flex-col items-center justify-center px-6 text-center">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-indigo-600 mb-4" />
        <p className="text-white font-semibold">Session not ready</p>
        <p className="mt-2 max-w-sm text-sm text-gray-400">
          {authError || "Your sign-in session could not be loaded. Please return to sign in again."}
        </p>
        <button
          onClick={() => router.push("/")}
          className="mt-5 rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-white"
        >
          Go to sign in
        </button>
      </div>
    );
  }

  const handleLogout = async () => {
    await logout();
    router.push("/");
  };

  const navItems = [
    { label: "Home", icon: Home, path: "/dashboard" },
    { label: "Meetings", icon: Video, path: "/dashboard/meetings" },
    { label: "Actions", icon: Calendar, path: "/dashboard/actions" },
    { label: "Recordings", icon: Clock, path: "/dashboard/recordings" },
    { label: "Reports", icon: ClipboardList, path: "/dashboard/reports" },
    { label: "Settings", icon: Settings, path: "/dashboard/settings" },
  ];

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      {/* ─── SIDEBAR (DESKTOP) ─── */}
      <aside className="hidden md:flex flex-col w-64 border-r border-white/5 bg-surface/30 backdrop-blur-xl h-full">
        {/* Brand */}
        <div className="h-16 flex items-center px-6 border-b border-white/5">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-indigo-600 flex items-center justify-center font-bold text-white text-xs shadow-lg shadow-primary/30">
              FH
            </div>
            <span className="font-semibold tracking-tight text-white">
              FireHox <span className="text-primary">Connect</span>
            </span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-8 space-y-2 overflow-y-auto">
          {navItems.map((item) => {
            const isActive = pathname === item.path;
            return (
              <button
                key={item.label}
                onClick={() => router.push(item.path)}
                className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all ${
                  isActive
                    ? "bg-primary/10 text-primary font-medium border border-primary/20"
                    : "text-gray-400 hover:text-white hover:bg-white/5 border border-transparent"
                }`}
              >
                <item.icon className={`w-5 h-5 ${isActive ? "text-primary" : ""}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* User Card (Bottom) */}
        <div className="p-4 border-t border-white/5">
          <div className="flex items-center space-x-3 p-3 rounded-xl bg-surface border border-white/5">
            {user.avatarUrl ? (
              // Firebase profile photos are externally hosted and already sized for avatars.
              // eslint-disable-next-line @next/next/no-img-element
              <img src={user.avatarUrl} alt="Avatar" className="w-10 h-10 rounded-full border border-white/10" />
            ) : (
              <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center font-bold text-primary">
                {user.name?.charAt(0) || user.email?.charAt(0) || "U"}
              </div>
            )}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">{user.name || "User"}</p>
              <p className="text-xs text-gray-500 truncate">{user.email}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="mt-3 w-full flex items-center justify-center space-x-2 px-4 py-2 rounded-lg text-sm text-gray-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
          >
            <LogOut className="w-4 h-4" />
            <span>Sign out</span>
          </button>
        </div>
      </aside>

      {/* ─── MOBILE HEADER & MENU ─── */}
      <div className="md:hidden flex flex-col h-full w-full">
        <header className="h-16 flex items-center justify-between px-6 border-b border-white/5 bg-surface/30 backdrop-blur-xl z-20">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-indigo-600 flex items-center justify-center font-bold text-white text-xs">
              FH
            </div>
            <span className="font-semibold text-white">FireHox</span>
          </div>
          <button onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)} className="p-2 text-gray-400 hover:text-white">
            {isMobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </header>

        <AnimatePresence>
          {isMobileMenuOpen && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="absolute top-16 left-0 right-0 bg-surface border-b border-white/5 z-10 overflow-hidden"
            >
              <nav className="p-4 space-y-2">
                {navItems.map((item) => {
                  const isActive = pathname === item.path;
                  return (
                    <button
                      key={item.label}
                      onClick={() => {
                        router.push(item.path);
                        setIsMobileMenuOpen(false);
                      }}
                      className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all ${
                        isActive ? "bg-primary/10 text-primary font-medium" : "text-gray-400"
                      }`}
                    >
                      <item.icon className="w-5 h-5" />
                      <span>{item.label}</span>
                    </button>
                  );
                })}
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-gray-400 hover:text-red-400"
                >
                  <LogOut className="w-5 h-5" />
                  <span>Sign out</span>
                </button>
              </nav>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Mobile Main Content */}
        <main className="flex-1 overflow-y-auto bg-background/50 relative">
          {children}
        </main>
      </div>

      {/* ─── DESKTOP MAIN CONTENT ─── */}
      <main className="hidden md:block flex-1 overflow-y-auto relative bg-background/50">
        {children}
      </main>
    </div>
  );
}
