import React from "react";
import LiveFeedPanel from "@/components/LiveFeedPanel";
import { motion } from "framer-motion";

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-black text-white font-[Orbitron] p-6">
      <motion.div
        className="max-w-7xl mx-auto"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1 }}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-10">
          <h1 className="text-3xl font-bold text-cyan-400">
            JRAVIS DASHBOARD v6 — PHASE 1 GLOBAL SYSTEM STATUS
          </h1>
          <button className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg shadow-lg font-semibold transition">
            LOG OUT
          </button>
        </div>

        {/* Top Status Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <motion.div
            className="p-6 rounded-2xl border border-gray-700 bg-gray-900/60 backdrop-blur-md shadow-lg"
            whileHover={{ scale: 1.02 }}
          >
            <h2 className="text-xl text-cyan-400 mb-3 font-semibold">
              JRAVIS BRAIN
            </h2>
            <ul className="space-y-2 text-gray-300">
              <li>Status: <span className="text-green-400 font-bold">ACTIVE</span></li>
              <li>Last Loop: 10:24 AM</li>
              <li>API: <span className="text-cyan-400">200 K</span></li>
            </ul>
          </motion.div>

          <motion.div
            className="p-6 rounded-2xl border border-gray-700 bg-gray-900/60 backdrop-blur-md shadow-lg text-center"
            whileHover={{ scale: 1.02 }}
          >
            <div className="flex flex-col items-center">
              <img
                src="/logo.png"
                alt="JRAVIS"
                className="w-16 h-16 mb-3 animate-pulse"
              />
              <h2 className="text-3xl font-bold tracking-wide text-cyan-300">
                LAKSHYA 2040
              </h2>
            </div>
          </motion.div>

          <motion.div
            className="p-6 rounded-2xl border border-gray-700 bg-gray-900/60 backdrop-blur-md shadow-lg"
            whileHover={{ scale: 1.02 }}
          >
            <h2 className="text-xl text-cyan-400 mb-3 font-semibold">
              INCOME ▶ LIVE FEED
            </h2>
            <div className="space-y-2 text-gray-300">
              <p>Target: <span className="text-blue-400 font-semibold">12%</span></p>
              <p>Monthly: <span className="text-green-400 font-semibold">₹1.06 L</span></p>
              <p>Daily: <span className="text-green-400 font-semibold">₹14,280</span></p>
            </div>
          </motion.div>
        </div>

        {/* Tabs Section */}
        <div className="mb-6 border-b border-gray-700 flex gap-4 text-gray-400">
          {["PHASE 1", "PHASE 2", "PHAISE", "THREEE"].map((tab, i) => (
            <button
              key={i}
              className={`pb-2 ${
                i === 0
                  ? "text-cyan-400 border-b-2 border-cyan-400"
                  : "hover:text-white"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Streams Table */}
        <div className="bg-gray-900/60 p-6 rounded-2xl border border-gray-700 backdrop-blur-md shadow-xl">
          <table className="w-full text-left text-gray-300">
            <thead className="text-gray-400 uppercase text-sm border-b border-gray-700">
              <tr>
                <th>#</th>
                <th>Stream Name</th>
                <th>Last Run</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody className="text-sm">
              {[
                ["1", "Elma Reels", "10:30 AM", "OK"],
                ["2", "Printify POD Store", "10:28 AM", "OK"],
                ["3", "Mesity AI Store", "10:25 AM", "RUNNING"],
                ["4", "YouTube Automation", "10:22 AM", "OK"],
                ["5", "Stock Image/Video", "10:18 AM", "600"],
                ["6", "KDP AI Publishing", "10:18 AM", "1300"],
                ["7", "Stationery Export", "10:17 AM", "2600"],
              ].map(([id, name, time, status]) => (
                <tr
                  key={id}
                  className="border-b border-gray-800 hover:bg-gray-800/40 transition"
                >
                  <td>{id}</td>
                  <td className="text-white font-semibold">{name}</td>
                  <td>{time}</td>
                  <td
                    className={
                      status === "OK"
                        ? "text-green-400 font-bold"
                        : status === "RUNNING"
                        ? "text-yellow-400 font-bold"
                        : "text-blue-400"
                    }
                  >
                    {status}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="mt-4 flex justify-between text-gray-400 text-sm">
            <span>
              TOTAL TODAY: <span className="text-green-400 font-semibold">€14,280</span>
            </span>
            <span>00:29:45</span>
          </div>
        </div>

        {/* Live Feed Panel */}
        <div className="mt-10">
          <LiveFeedPanel />
        </div>
      </motion.div>
    </div>
  );
}

