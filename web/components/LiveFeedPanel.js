import React from "react";
import { motion } from "framer-motion";

export default function LiveFeedPanel() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="p-5 rounded-2xl shadow-lg bg-gradient-to-b from-[#070a0e] via-[#0b0d11] to-[#0b0c10] border border-[#1a1b1f] text-white"
    >
      <h2 className="text-xl font-semibold mb-3 text-[#00e5ff]">
        JRAVIS Live Feed
      </h2>

      <ul className="space-y-2 text-gray-300 text-sm">
        <li>
          ⚙️ <span className="text-gray-400">JRAVIS Engine:</span>{" "}
          <span className="text-green-400 font-semibold">Online</span>
        </li>
        <li>
          🤖 <span className="text-gray-400">VA Bot Status:</span>{" "}
          <span className="text-green-400 font-semibold">Active</span>
        </li>
        <li>
          📈 <span className="text-gray-400">Current Phase:</span>{" "}
          <span className="font-semibold text-[#00bcd4]">
            Phase 2 – Scaling
          </span>
        </li>
        <li>
          💰 <span className="text-gray-400">Monthly Earning Range:</span>{" "}
          <span className="font-semibold text-[#00e5ff]">₹3.65L – ₹15.05L</span>
        </li>
      </ul>

      <div className="mt-4 p-3 rounded-xl bg-[#0d1115] border border-[#16181b]">
        <p className="text-xs text-gray-400 italic">
          JRAVIS: “All systems are operational. Phase 3 activation ready after
          your approval, Boss.”
        </p>
      </div>
    </motion.div>
  );
}
