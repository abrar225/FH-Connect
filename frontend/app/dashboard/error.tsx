"use client";

import React from "react";

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex h-[60vh] items-center justify-center p-8">
      <div className="bg-surface/50 p-8 rounded-3xl border border-white/5 backdrop-blur-xl max-w-md w-full text-center">
        <div className="w-14 h-14 rounded-2xl bg-red-500/10 flex items-center justify-center mx-auto mb-5">
          <svg
            className="w-7 h-7 text-red-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>
        <h2 className="text-xl font-bold text-white mb-2">
          Something went wrong
        </h2>
        <p className="text-gray-400 text-sm mb-6 leading-relaxed">
          An unexpected error occurred while loading the dashboard. Please try
          again.
        </p>
        <button
          onClick={reset}
          className="px-6 py-2.5 bg-primary/20 text-primary rounded-xl font-medium hover:bg-primary/30 transition-colors"
        >
          Try Again
        </button>
      </div>
    </div>
  );
}
