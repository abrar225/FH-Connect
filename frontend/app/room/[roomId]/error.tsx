"use client";

import React from "react";

export default function RoomError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex h-screen items-center justify-center bg-background p-6">
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
          Unable to load meeting
        </h2>
        <p className="text-gray-400 text-sm mb-6 leading-relaxed">
          There was a problem connecting to the meeting room. Please check your
          connection and try again.
        </p>
        <div className="flex gap-3 justify-center">
          <button
            onClick={reset}
            className="px-6 py-2.5 bg-primary/20 text-primary rounded-xl font-medium hover:bg-primary/30 transition-colors"
          >
            Retry
          </button>
          <a
            href="/dashboard"
            className="px-6 py-2.5 bg-white/5 text-gray-300 rounded-xl font-medium hover:bg-white/10 transition-colors"
          >
            Back to Dashboard
          </a>
        </div>
      </div>
    </div>
  );
}
