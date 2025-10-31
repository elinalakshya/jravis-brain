import React from "react";

export default function LiveFeedPanel() {
  return (
    <div className="p-6 mt-8 rounded-2xl shadow-lg bg-gray-900/70 backdrop-blur-lg border border-gray-700">
      <h2 className="text-2xl font-semibold mb-4 text-cyan-400">
        JRAVIS LIVE FEED
      </h2>
      <ul className="space-y-3 text-gray-300">
        <li>⚙️ Engine: <span className="text-green-400 font-bold">Online</span></li>
        <li>🤖 VA Bot: <span className="text-green-400 font-bold">Active</span></li>
        <li>📊 Current Phase: <span className="text-blue-400 font-semibold">Phase 2 – Scaling</span></li>
        <li>💰 Monthly Range: ₹3.65L – ₹15.05L</li>
      </ul>
      <div className="mt-5 p-4 rounded-lg bg-cyan-950/40 border border-cyan-700 shadow-md">
        <p className="text-sm text-cyan-300 italic">
          JRAVIS: “All systems are operational. Phase 3 activation ready after your approval, Boss.”
        </p>
      </div>
    </div>
  );
}

