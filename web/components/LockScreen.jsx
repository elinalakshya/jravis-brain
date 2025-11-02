import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

export default function LockScreen({ onUnlock }) {
  const [code, setCode] = useState("");
  const [error, setError] = useState(false);
  const correctCode = process.env.NEXT_PUBLIC_LOCK_CODE || "2040";

  const handleUnlock = () => {
    if (code === correctCode) onUnlock?.();
    else {
      setError(true);
      setTimeout(() => setError(false), 1200);
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 1 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 flex flex-col items-center justify-center bg-black text-white z-50"
      >
        <div className="p-8 bg-white/10 rounded-xl border border-white/20 text-center">
          <h2 className="text-xl font-semibold mb-3">JRAVIS Console Locked</h2>
          <input
            type="password"
            placeholder="Enter Lock Code"
            className="w-full p-2 text-center rounded bg-white/20 mb-3"
            value={code}
            onChange={(e) => setCode(e.target.value)}
          />
          <button
            onClick={handleUnlock}
            className="px-4 py-2 bg-cyan-600 rounded-lg hover:bg-cyan-500"
          >
            Unlock
          </button>
          {error && <p className="text-red-400 mt-2">Invalid code</p>}
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
