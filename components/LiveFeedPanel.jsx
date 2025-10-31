// components/LiveFeedPanel.jsx
import { useState } from "react";
import LiveFeedConnector from "@/components/LiveFeedConnector";
import { motion, AnimatePresence } from "framer-motion";

export default function LiveFeedPanel() {
  const [feed, setFeed] = useState({ income: [], tasks: {}, logs: [] });
  const [lastTs, setLastTs] = useState(null);

  function handleUpdate(data) {
    if (data.type === "jravis_snapshot" && data.payload) {
      setFeed(data.payload);
      setLastTs(data.payload.ts);
    }
  }

  return (
    <div className="p-4 space-y-4">
      <header className="flex justify-between items-center">
        <h2 className="text-xl font-semibold text-gray-800">
          🔴 Live System Feed
        </h2>
        <LiveFeedConnector onUpdate={handleUpdate} />
      </header>

      <section className="grid md:grid-cols-3 gap-4">
        {/* 💰 Income */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl shadow-lg p-4 bg-white"
        >
          <h3 className="font-medium text-gray-700 mb-2">💰 Income (24h)</h3>
          <AnimatePresence>
            {feed.income.length ? (
              feed.income.map((i, idx) => (
                <motion.div
                  key={i.stream}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.3 }}
                  className="text-sm border-b border-gray-100 py-1"
                >
                  <strong>{i.stream}</strong>: ₹{i.amount.toLocaleString()}
                </motion.div>
              ))
            ) : (
              <p className="text-gray-400 text-sm">No income records</p>
            )}
          </AnimatePresence>
        </motion.div>

        {/* 📋 Tasks */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl shadow-lg p-4 bg-white"
        >
          <h3 className="font-medium text-gray-700 mb-2">📋 Tasks Summary</h3>
          <ul className="text-sm space-y-1">
            <li className="text-green-600">
              ✅ Completed: {feed.tasks.completed || 0}
            </li>
            <li className="text-blue-600">
              🕓 Pending: {feed.tasks.pending || 0}
            </li>
            <li className="text-red-600">⚠️ Errors: {feed.tasks.error || 0}</li>
          </ul>
        </motion.div>

        {/* 🪶 Logs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl shadow-lg p-4 bg-white"
        >
          <h3 className="font-medium text-gray-700 mb-2">🪶 Recent Logs</h3>
          <div className="text-xs space-y-1 max-h-40 overflow-y-auto">
            <AnimatePresence>
              {feed.logs.length ? (
                feed.logs.map((l, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ duration: 0.25 }}
                    className="border-b border-gray-100 py-1"
                  >
                    [{l.level}] {l.message}
                  </motion.div>
                ))
              ) : (
                <p className="text-gray-400 text-sm">No logs yet</p>
              )}
            </AnimatePresence>
          </div>
        </motion.div>
      </section>

      {lastTs && (
        <footer className="text-xs text-gray-400 mt-2">
          Last update: {new Date(lastTs).toLocaleString()}
        </footer>
      )}
    </div>
  );
}
