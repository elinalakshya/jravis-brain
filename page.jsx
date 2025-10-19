import React, { useEffect, useState } from "react";
import { motion, useAnimation } from "framer-motion";

// JRAVIS — Mission 2040 AI Dashboard with Dynamic Pulse
export default function MissionControlDashboard() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [locked, setLocked] = useState(false);
  const [lockInput, setLockInput] = useState("");
  const [error, setError] = useState(null);
  const [lastEarnings, setLastEarnings] = useState(0);
  const [pulseColor, setPulseColor] = useState(
    "from-sky-500/10 via-emerald-400/10 to-sky-500/10",
  );

  const controls = useAnimation();

  // =====================
  // 🔄 Fetch live status
  // =====================
  const fetchStatus = async () => {
    try {
      setLoading(true);
      const res = await fetch("/api/status", { cache: "no-store" });
      if (!res.ok) throw new Error(`status ${res.status}`);
      const json = await res.json();

      const newEarnings = json?.income_summary?.current_earnings || 0;

      // 🔵🟢🟠 Dynamic Pulse Reactions
      if (newEarnings > lastEarnings) {
        // Growth → green pulse
        setPulseColor("from-emerald-400/20 via-green-500/20 to-emerald-400/20");
        controls.start({
          opacity: [0.3, 1, 0.3],
          scale: [1, 1.08, 1],
          transition: { duration: 2, ease: "easeInOut" },
        });
      } else if (newEarnings === lastEarnings) {
        // Stable → blue pulse
        setPulseColor("from-sky-500/15 via-blue-400/15 to-sky-500/15");
        controls.start({
          opacity: [0.3, 0.6, 0.3],
          scale: [1, 1.03, 1],
          transition: { duration: 4, ease: "easeInOut" },
        });
      } else {
        // Drop or API lag → amber pulse
        setPulseColor("from-amber-400/20 via-orange-400/20 to-amber-400/20");
        controls.start({
          opacity: [0.4, 0.8, 0.4],
          scale: [1, 1.05, 1],
          transition: { duration: 3, ease: "easeInOut" },
        });
      }

      setLastEarnings(newEarnings);
      setStatus(json);
      setError(null);
    } catch (e) {
      setPulseColor("from-amber-400/20 via-orange-400/20 to-amber-400/20");
      controls.start({
        opacity: [0.4, 0.8, 0.4],
        scale: [1, 1.05, 1],
        transition: { duration: 3, ease: "easeInOut" },
      });
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  // Auto-refresh
  useEffect(() => {
    fetchStatus();
    const t = setInterval(fetchStatus, 10000);
    return () => clearInterval(t);
  }, []);

  // Formatter
  const fmtINR = (n) => {
    if (n == null) return "-";
    try {
      return "₹ " + Number(n).toLocaleString("en-IN");
    } catch (e) {
      return `₹ ${n}`;
    }
  };

  // Lock
  const handleUnlock = () => {
    const lock =
      (typeof window !== "undefined" && window.__JRAVIS_LOCK) || "204040";
    if (lockInput === lock) {
      setLocked(false);
      setLockInput("");
    } else {
      alert("Incorrect lock code");
    }
  };

  const totalEarnings = status?.income_summary?.current_earnings || 0;
  const monthlyTarget = status?.income_summary?.monthly_target || 0;
  const progress = monthlyTarget
    ? Math.min(100, (totalEarnings / monthlyTarget) * 100)
    : 0;

  return (
    <div className="min-h-screen bg-[#06070a] text-[#e6eef3] p-6 font-sans relative overflow-hidden">
      {/* 🧠 JRAVIS Heartbeat Pulse */}
      <motion.div
        className={`absolute inset-0 bg-gradient-to-r ${pulseColor} blur-3xl`}
        animate={controls}
        initial={{ opacity: 0.3, scale: 1 }}
        transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
      />

      <div className="max-w-7xl mx-auto relative z-10">
        <header className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-extrabold tracking-tight">
              JRAVIS — Mission Control
            </h1>
            <p className="text-sm text-gray-400">
              Mission 2040 • Dynamic AI Heartbeat Mode 💚
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-sm text-gray-400">
              UTC {new Date().toLocaleString()}
            </div>
            <div className="px-3 py-1 rounded-full bg-gradient-to-r from-sky-500 to-emerald-400 text-black font-semibold">
              Phase 1 Active
            </div>
          </div>
        </header>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Income */}
          <div className="lg:col-span-2 bg-[#0f1720] border border-[#1f2730] rounded-xl p-6 shadow-lg">
            <div className="flex justify-between items-start">
              <div>
                <div className="text-sm text-gray-400">Mission Progress</div>
                <div className="text-3xl font-bold mt-2">
                  {fmtINR(totalEarnings)}
                </div>
                <div className="text-sm text-gray-400 mt-1">
                  Monthly Target: {fmtINR(monthlyTarget)}
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm text-gray-400">Active Systems</div>
                <div className="text-xl font-medium mt-1">
                  {status?.income_summary?.active_systems ?? "-"}
                </div>
              </div>
            </div>

            {/* Progress */}
            <div className="mt-6">
              <div className="flex items-center justify-between text-sm text-gray-400 mb-2">
                <div>Progress</div>
                <div>{progress.toFixed(1)}%</div>
              </div>
              <motion.div
                className="w-full bg-[#081018] rounded-full h-3 overflow-hidden border border-[#12202a]"
                initial={{ scaleX: 0 }}
                animate={{ scaleX: progress / 100 }}
                transition={{ duration: 1, ease: "easeOut" }}
                style={{ originX: 0 }}
              >
                <div className="h-3 bg-gradient-to-r from-emerald-400 to-sky-500 w-full" />
              </motion.div>
            </div>

            {/* Pulse Graph */}
            <div className="mt-8 relative">
              <div className="text-sm text-gray-300 mb-2 relative z-10">
                AI Sync Pulse — Last 7 Runs
              </div>
              <div className="flex items-end gap-2 h-28 relative z-10">
                {[6, 5, 4, 3, 2, 1, 0].map((i) => {
                  const history = status?.income_summary?.history || [];
                  const v = history[i]?.earnings ?? Math.random() * 10000;
                  const max = Math.max(
                    1,
                    ...history.map((h) => h.earnings || 1),
                  );
                  const h = Math.max(6, (v / max) * 100);
                  return (
                    <motion.div
                      key={i}
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: `${h}%`, opacity: 1 }}
                      transition={{
                        duration: 0.6,
                        delay: i * 0.05,
                        ease: "easeOut",
                      }}
                      whileHover={{
                        scale: 1.1,
                        boxShadow: "0px 0px 10px rgba(56, 224, 169, 0.5)",
                      }}
                      className="w-6 rounded-sm bg-gradient-to-t from-emerald-400 to-sky-500"
                      title={`${fmtINR(v)}`}
                    />
                  );
                })}
              </div>
            </div>
          </div>

          {/* Right: System Status */}
          <aside className="space-y-6">
            <div className="bg-[#0f1720] border border-[#1f2730] rounded-xl p-4 shadow">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-400">System Status</div>
                <div className="text-xs text-gray-400">Auto-refresh 10s</div>
              </div>
              <div className="mt-3 grid grid-cols-1 gap-2">
                {[
                  ["JRAVIS Brain", status?.brain_status?.status ?? "unknown"],
                  ["VA Bot", status?.va_status?.status ?? "unknown"],
                  [
                    "Mission Bridge",
                    status?.bridge_status?.status ?? "unknown",
                  ],
                  ["Auto-Key Worker", status?.autokey_status ?? "unknown"],
                ].map(([name, st]) => (
                  <div
                    key={name}
                    className="flex items-center justify-between text-sm"
                  >
                    <div className="flex items-center gap-2">
                      <div
                        className={`w-3 h-3 rounded-full ${
                          st === "ok" ||
                          st === "online" ||
                          st === "Active" ||
                          st === "accepted"
                            ? "bg-emerald-400"
                            : "bg-orange-400"
                        }`}
                      />
                      <div className="text-gray-300">{name}</div>
                    </div>
                    <div className="text-sm text-gray-400">{st}</div>
                  </div>
                ))}
              </div>
            </div>
          </aside>
        </div>

        <footer className="mt-6 text-center text-sm text-gray-500">
          JRAVIS • Mission 2040 — Dynamic AI Pulse Active 💠
        </footer>
      </div>
    </div>
  );
}
