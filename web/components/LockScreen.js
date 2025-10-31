import React, { useState } from "react";
import { motion } from "framer-motion";

export default function LockScreen({ onUnlock }) {
  const [code, setCode] = useState("");
  const [error, setError] = useState("");

  const correctCode = "YOUR_LOCK_CODE"; // change this to your actual lock code

  const handleLogin = () => {
    if (code === correctCode) {
      setError("");
      onUnlock();
    } else {
      setError("Access Denied – Incorrect Code");
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 1 }}
      className="h-screen flex items-center justify-center bg-gradient-to-br from-black via-gray-900 to-black text-white"
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.8 }}
        className="p-8 rounded-3xl bg-gray-900/80 backdrop-blur-xl border border-blue-800 shadow-[0_0_30px_rgba(0,150,255,0.2)] w-80 text-center"
      >
        <h2 className="text-2xl font-bold mb-4 text-blue-400 tracking-widest uppercase">
          JRAVIS Secure Access
        </h2>

        <input
          type="password"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          className="w-full p-3 rounded-lg bg-gray-800 text-white border border-gray-700 text-center mb-3 focus:ring-2 focus:ring-blue-600 outline-none"
          placeholder="Enter Lock Code"
        />

        <button
          onClick={handleLogin}
          className="w-full py-3 mt-2 bg-blue-600 hover:bg-blue-500 rounded-lg font-semibold transition-all duration-200"
        >
          Authenticate
        </button>

        {error && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mt-3 text-red-400 text-sm"
          >
            {error}
          </motion.p>
        )}

        <p className="mt-5 text-xs text-gray-500 tracking-widest">
          MILITARY-GRADE ENCRYPTION MODE
        </p>
      </motion.div>
    </motion.div>
  );
}
