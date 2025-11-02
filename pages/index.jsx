import React, { useState } from "react";
import FramerMotion from "framer-motion";
const motion = FramerMotion.default?.motion || FramerMotion.motion;
const AnimatePresence =
  FramerMotion.default?.AnimatePresence || FramerMotion.AnimatePresence;

import LockScreen from "../components/LockScreen";
import LiveFeedPanel from "../components/LiveFeedPanel";

export default function DashboardPage() {
  const [unlocked, setUnlocked] = useState(false);

  const pageVariants = {
    hidden: { opacity: 0, y: 20, scale: 0.98 },
    visible: {
      opacity: 1,
      y: 0,
      scale: 1,
      transition: { duration: 0.7, ease: [0.25, 0.1, 0.25, 1.0] },
    },
    exit: { opacity: 0, y: -20, transition: { duration: 0.5 } },
  };

  return (
    <AnimatePresence mode="wait">
      {!unlocked ? (
        <motion.div
          key="lock"
          initial="hidden"
          animate="visible"
          exit="exit"
          variants={pageVariants}
        >
          <LockScreen onUnlock={() => setUnlocked(true)} />
        </motion.div>
      ) : (
        <motion.main
          key="dashboard"
          className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-800 text-white flex flex-col items-center justify-center p-6 relative overflow-hidden"
          initial="hidden"
          animate="visible"
          exit="exit"
          variants={pageVariants}
        >
          {/* Glowing grid background */}
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(0,150,255,0.12)_0%,transparent_80%)] pointer-events-none"></div>

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
            initial={{ y: -25, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.8 }}
          >
            JRAVIS Dark-Tech Command Console
          </motion.h1>

          {/* Live feed area */}
          <motion.section
            className="w-full max-w-4xl"
            initial={{ y: 25, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 1 }}
          >
            <LiveFeedPanel />
          </motion.section>

          {/* Decorative bottom glow */}
          <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-blue-900/20 to-transparent blur-2xl pointer-events-none"></div>
        </motion.main>
      )}
    </AnimatePresence>
  );
}
