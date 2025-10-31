import React, { useState } from "react";
import { motion } from "framer-motion";

export default function LockScreen({ onUnlock }) {
  const [code, setCode] = useState("");
  const [error, setError] = useState(false);
  const LOCK_CODE = "2040"; // your existing lock code

  const handleUnlock = () => {
    if (code === LOCK_CODE) {
      setError(false);
      onUnlock();
    } else {
      setError(true);
      setCode("");
    }
  };

  return (
    <motion.div
      className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-gray-900 via-black to-gray-800 text-white"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 1 }}
    >
      <div className="text-center space-y-4">
        <motion.h1
          className="text-4xl font-bold tracking-widest text-blue-400"
          initial={{ y: -30, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 1 }}
        >
          🔒 JRAVIS SECURE MODE
        </motion.h1>
        <p className="text-gray-400">
          Enter your mission lock code to continue
        </p>
      </div>

      <motion.div
        className="mt-8 bg-gray-900 p-8 rounded-2xl shadow-xl border border-gray-700"
        initial={{ scale: 0.8 }}
        animate={{ scale: 1 }}
        transition={{ duration: 0.6 }}
      >
        <input
          type="password"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleUnlock()}
          placeholder="Enter Lock Code"
          className="w-72 text-center text-lg px-4 py-2 bg-gray-800 border border-gray-600 rounded-xl focus:outline-none focus:border-blue-500 transition"
        />
        <button
          onClick={handleUnlock}
          className="block w-full mt-4 bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-xl font-semibold tracking-wide transition"
        >
          UNLOCK
        </button>
        {error && (
          <p className="text-red-500 mt-3 text-sm font-medium">
            Incorrect code. Try again.
          </p>
        )}
      </motion.div>
      <p className="text-gray-500 text-xs mt-8">
        Mission 2040 | Authorized Access Only
      </p>
    </motion.div>
  );
}
