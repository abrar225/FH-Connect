'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Send, Sparkles } from 'lucide-react';
import { useUIStore } from '@/stores/useUIStore';

export const Sidebar = () => {
  const { isSidebarOpen, activeSidebarTab, closeSidebar } = useUIStore();

  return (
    <AnimatePresence>
      {isSidebarOpen && (
        <motion.div
          initial={{ x: 340, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 340, opacity: 0 }}
          transition={{ type: 'spring', damping: 25, stiffness: 200 }}
          className="fixed top-4 right-4 bottom-4 w-[320px] bg-black/60 backdrop-blur-2xl border border-white/10 rounded-2xl shadow-2xl flex flex-col overflow-hidden z-40"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-white/10 bg-white/5">
            <h2 className="text-white font-semibold flex items-center gap-2">
              {activeSidebarTab === 'intelligence' ? (
                <>
                  <Sparkles size={18} className="text-purple-400" />
                  AI Pulse
                </>
              ) : (
                'Meeting Chat'
              )}
            </h2>
            <button 
              onClick={closeSidebar}
              className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
            >
              <X size={18} />
            </button>
          </div>

          {/* Content Area */}
          <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4 custom-scrollbar">
            {activeSidebarTab === 'chat' && (
              <>
                <MessageBubble sender="System" text="Welcome to the secure meeting." isSystem />
                <MessageBubble sender="Sarah Connor" text="Can everyone hear me clearly?" />
                <MessageBubble sender="You" text="Yes, audio is perfect." isSelf />
              </>
            )}
            
            {activeSidebarTab === 'intelligence' && (
              <div className="flex flex-col gap-4">
                <div className="p-4 rounded-xl bg-purple-500/10 border border-purple-500/20">
                  <h3 className="text-purple-300 text-sm font-medium mb-2">Live Summary</h3>
                  <p className="text-gray-300 text-sm leading-relaxed">
                    The team is currently verifying audio connections before beginning the quarterly review presentation.
                  </p>
                </div>
                
                <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20">
                  <h3 className="text-blue-300 text-sm font-medium mb-2">Action Item Detected</h3>
                  <p className="text-gray-300 text-sm">
                    <span className="font-semibold text-white">@JohnDoe</span> to share the Q3 financial slides.
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Input Area (Only for chat) */}
          {activeSidebarTab === 'chat' && (
            <div className="p-4 border-t border-white/10 bg-white/5">
              <div className="relative">
                <input 
                  type="text" 
                  placeholder="Type a message..." 
                  className="w-full bg-white/5 border border-white/10 rounded-xl py-3 pl-4 pr-12 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500/50 transition-colors"
                />
                <button className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 bg-purple-500 hover:bg-purple-600 rounded-lg text-white transition-colors">
                  <Send size={16} />
                </button>
              </div>
            </div>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );
};

// --- Subcomponents ---

const MessageBubble = ({ sender, text, isSystem, isSelf }: { sender: string, text: string, isSystem?: boolean, isSelf?: boolean }) => {
  if (isSystem) {
    return (
      <div className="w-full text-center my-2">
        <span className="text-xs text-gray-500 bg-white/5 px-2 py-1 rounded-full">{text}</span>
      </div>
    );
  }

  return (
    <div className={`flex flex-col ${isSelf ? 'items-end' : 'items-start'}`}>
      <span className="text-xs text-gray-400 mb-1 ml-1">{sender}</span>
      <div className={`px-4 py-2 rounded-2xl max-w-[85%] text-sm ${
        isSelf 
          ? 'bg-purple-600 text-white rounded-tr-sm' 
          : 'bg-white/10 text-gray-200 rounded-tl-sm'
      }`}>
        {text}
      </div>
    </div>
  );
};
