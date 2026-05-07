"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";

interface AppUser {
  id: string;
  email: string | null;
  name: string;
  avatarUrl: string | null;
}

interface AuthContextType {
  user: AppUser | null;
  loading: boolean;
  authError: string | null;
  signInWithGoogle: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  authError: null,
  signInWithGoogle: async () => {},
  logout: async () => {},
});

const AUTH_BOOT_TIMEOUT_MS = 8000;
const PROFILE_SYNC_TIMEOUT_MS = 5000;

function withTimeout<T>(promise: PromiseLike<T>, timeoutMs: number, label: string): Promise<T> {
  return new Promise((resolve, reject) => {
    const timer = window.setTimeout(() => reject(new Error(`${label} timed out`)), timeoutMs);
    Promise.resolve(promise)
      .then(resolve)
      .catch(reject)
      .finally(() => window.clearTimeout(timer));
  });
}

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<AppUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState<string | null>(null);

  const mapUser = (authUser: any): AppUser => ({
    id: authUser.id,
    email: authUser.email ?? null,
    name: authUser.user_metadata?.full_name || authUser.user_metadata?.name || authUser.email || "User",
    avatarUrl: authUser.user_metadata?.avatar_url || null,
  });

  const syncUserWithSupabase = async (authUser: AppUser) => {
    try {
      const { error } = await withTimeout(
        supabase
          .from("users")
          .upsert(
            {
              id: authUser.id,
              email: authUser.email,
              name: authUser.name,
            },
            { onConflict: "id" }
          ),
        PROFILE_SYNC_TIMEOUT_MS,
        "Profile sync"
      );

      if (error) {
        setAuthError("Unable to sync user profile.");
      }
    } catch {
      setAuthError("Unable to sync user profile.");
    }
  };

  useEffect(() => {
    let active = true;
    const finishBoot = (currentUser: AppUser | null) => {
      if (!active) return;
      setUser(currentUser);
      setLoading(false);
      if (currentUser) {
        void syncUserWithSupabase(currentUser);
      }
    };

    const bootTimer = window.setTimeout(() => {
      if (!active) return;
      setAuthError("Authentication check is taking longer than expected.");
      setLoading(false);
    }, AUTH_BOOT_TIMEOUT_MS);

    supabase.auth
      .getSession()
      .then(({ data }) => {
        window.clearTimeout(bootTimer);
        finishBoot(data.session?.user ? mapUser(data.session.user) : null);
      })
      .catch(() => {
        window.clearTimeout(bootTimer);
        setAuthError("Unable to check authentication session.");
        finishBoot(null);
      });

    const { data: listener } = supabase.auth.onAuthStateChange(async (_event, session) => {
      const currentUser = session?.user ? mapUser(session.user) : null;
      setUser(currentUser);
      setLoading(false);
      if (currentUser) {
        void syncUserWithSupabase(currentUser);
      }
    });

    return () => {
      active = false;
      window.clearTimeout(bootTimer);
      listener.subscription.unsubscribe();
    };
  }, []);

  const signInWithGoogle = async () => {
    setLoading(true);
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: "google",
        options: {
          redirectTo: `${window.location.origin}/dashboard`,
        },
      });
      if (error) throw error;
    } catch {
      setAuthError("Unable to start Google sign-in.");
      setLoading(false);
    }
  };

  const logout = async () => {
    setLoading(true);
    try {
      await supabase.auth.signOut();
    } catch {
      setAuthError("Unable to sign out.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, authError, signInWithGoogle, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
