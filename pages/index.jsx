import React, { useState } from "react";
import LockScreen from "@/components/LockScreen";
import LiveFeedPanel from "@/components/LiveFeedPanel";
import { motion, AnimatePresence } from "framer-motion";

export default function DashboardPage() {
  const [unlocked, setUnlocked] = useState(false);

  return (
    <AnimatePresence mode="wait">
      {!unlocked ? (
        <motion.div
          key="lock"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0, transition: { duration: 0.6 } }}
        >
          <LockScreen onUnlock={() => setUnlocked(true)} />
        </motion.div>
      ) : (
        <motion.div
          key="dashboard"
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{
            duration: 0.8,
            ease: [0.25, 0.1, 0.25, 1.0],
          }}
          className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-800 text-white flex flex-col items-center justify-center p-6 relative overflow-hidden"
        >
          {/* Military-grade glowing grid background */}
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(0,150,255,0.1)_0%,transparent_80%)] pointer-events-none"></div>

          {/* Logout button */}
          <button
            onClick={() => setUnlocked(false)}
            className="absolute top-5 right-5 px-4 py-2 rounded-lg bg-red-600 hover:bg-red-500 font-medium transition-all duration-200 z-10"
          >
            Logout
          </button>

          {/* Header */}
          <motion.h1
            className="text-4xl font-extrabold mb-6 text-blue-400 tracking-wide drop-shadow-lg"
            initial={{ y: -20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.7 }}
          >
            JRAVIS Dark-Tech Command Console
          </motion.h1>

          {/* Live Feed */}
          <motion.div
            className="w-full max-w-4xl"
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 1 }}
          >
            <LiveFeedPanel />
          </motion.div>

          {/* Bottom glow */}
          <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-blue-900/20 to-transparent blur-2xl pointer-events-none"></div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
