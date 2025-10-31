import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

export default function LockScreen({ onUnlock }) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (password === "2040") {
      setError(false);
      setTimeout(() => onUnlock(), 500);
    } else {
      setError(true);
      setPassword("");
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        className="fixed inset-0 flex flex-col items-center justify-center bg-gradient-to-br from-gray-900 via-black to-gray-800 text-white"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 1 }}
      >
        <motion.div
          className="text-center"
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 1 }}
        >
          <h1 className="text-4xl font-bold tracking-widest mb-6 text-cyan-400">
            JRAVIS SECURE ACCESS
          </h1>
          <form onSubmit={handleSubmit} className="space-y-4">
            <input
              type="password"
              value={password}
              placeholder="Enter Access Code"
              onChange={(e) => setPassword(e.target.value)}
              className="w-72 px-4 py-2 text-center bg-gray-800 border border-cyan-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-400"
            />
            {error && (
              <p className="text-red-400 text-sm animate-pulse">
                Invalid Code — Access Denied
              </p>
            )}
            <button
              type="submit"
              className="w-72 py-2 bg-cyan-500 hover:bg-cyan-400 rounded-lg font-semibold text-gray-900 transition-all duration-300"
            >
              UNLOCK
            </button>
          </form>
        </motion.div>
        <motion.p
          className="absolute bottom-8 text-sm text-gray-400 tracking-widest"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.5, duration: 1 }}
        >
          SYSTEM ENCRYPTION ACTIVE • MIL-GRADE LOCK
        </motion.p>
      </motion.div>
    </AnimatePresence>
  );
}
