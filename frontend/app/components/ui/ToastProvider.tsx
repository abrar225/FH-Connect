"use client";

import React, { createContext, useContext, useState, useCallback, useRef } from "react";
import { CheckCircle2, XCircle, AlertCircle, Info, X } from "lucide-react";

type ToastType = "success" | "error" | "warning" | "info";

interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  exiting?: boolean;
}

interface ToastContextValue {
  toast: (type: ToastType, title: string, message?: string) => void;
}

const ToastContext = createContext<ToastContextValue>({
  toast: () => {},
});

export const useToast = () => useContext(ToastContext);

const ICONS: Record<ToastType, React.ReactNode> = {
  success: <CheckCircle2 className="w-5 h-5 text-emerald-400" />,
  error: <XCircle className="w-5 h-5 text-red-400" />,
  warning: <AlertCircle className="w-5 h-5 text-amber-400" />,
  info: <Info className="w-5 h-5 text-blue-400" />,
};

const BORDER_COLORS: Record<ToastType, string> = {
  success: "border-emerald-500/30",
  error: "border-red-500/30",
  warning: "border-amber-500/30",
  info: "border-blue-500/30",
};

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const timerRef = useRef<Map<string, NodeJS.Timeout>>(new Map());

  const dismissToast = useCallback((id: string) => {
    // Start exit animation
    setToasts((prev) => prev.map((t) => (t.id === id ? { ...t, exiting: true } : t)));
    // Remove after animation
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 250);
  }, []);

  const toast = useCallback(
    (type: ToastType, title: string, message?: string) => {
      const id = crypto.randomUUID();
      setToasts((prev) => [...prev, { id, type, title, message }]);

      // Auto-dismiss after 4s
      const timer = setTimeout(() => dismissToast(id), 4000);
      timerRef.current.set(id, timer);
    },
    [dismissToast]
  );

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}

      {/* Toast Container */}
      <div className="fixed top-4 right-4 z-[100] flex flex-col space-y-2 pointer-events-none">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`pointer-events-auto flex items-start space-x-3 bg-surface/90 backdrop-blur-xl border ${
              BORDER_COLORS[t.type]
            } rounded-xl px-4 py-3 shadow-2xl max-w-sm ${
              t.exiting ? "animate-toast-out" : "animate-toast-in"
            }`}
          >
            <div className="mt-0.5">{ICONS[t.type]}</div>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-sm text-white">{t.title}</p>
              {t.message && (
                <p className="text-xs text-gray-400 mt-0.5 line-clamp-2">{t.message}</p>
              )}
            </div>
            <button
              onClick={() => dismissToast(t.id)}
              className="text-gray-500 hover:text-white transition-colors"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
