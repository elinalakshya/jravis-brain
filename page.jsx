import React, { useEffect, useState } from "react";

// JRAVIS Mission Control — single-file React component
// Tailwind-first design. Drop this into a Next.js page (e.g. app/page.jsx or pages/index.jsx)

export default function MissionControlDashboard() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [locked, setLocked] = useState(false);
  const [lockInput, setLockInput] = useState("");
  const [error, setError] = useState(null);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      const res = await fetch("/api/status", { cache: "no-store" });
      if (!res.ok) throw new Error(`status ${res.status}`);
      const json = await res.json();
      setStatus(json);
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const t = setInterval(fetchStatus, 10000);
    return () => clearInterval(t);
  }, []);

  // Helper formatters
  const fmtINR = (n) => {
    if (n == null) return "-";
    try {
      return "₹ " + Number(n).toLocaleString("en-IN");
    } catch (e) {
      return `₹ ${n}`;
    }
  };

  const handleUnlock = () => {
    // simple local-check: compare to env-provided LOCK_CODE via window.__JRAVIS_LOCK (injected server-side)
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
    <div className="min-h-screen bg-[#06070a] text-[#e6eef3] p-6 font-sans">
      <div className="max-w-7xl mx-auto">
        <header className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-extrabold tracking-tight">
              JRAVIS — Mission Control
            </h1>
            <p className="text-sm text-gray-400">
              Mission 2040 • Dark Console • Live Ops
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

        {/* Top grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Big earnings card */}
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

            <div className="mt-6">
              <div className="flex items-center justify-between text-sm text-gray-400 mb-2">
                <div>Progress</div>
                <div>{progress.toFixed(1)}%</div>
              </div>
              <div className="w-full bg-[#081018] rounded-full h-3 overflow-hidden border border-[#12202a]">
                <div
                  className="h-3 bg-gradient-to-r from-emerald-400 to-sky-500"
                  style={{ width: `${progress}%` }}
                />
              </div>

              {/* Simple mini chart: last 7 earnings from memory */}
              <div className="mt-6">
                <div className="text-sm text-gray-300 mb-2">
                  Last 7 runs (sample)
                </div>
                <div className="flex items-end gap-2 h-28">
                  {[6, 5, 4, 3, 2, 1, 0].map((i) => {
                    // mock bars using activity or income history if present
                    const v =
                      status?.income_summary?.history?.[i]?.earnings ||
                      Math.max(0, (totalEarnings / 7) * (Math.random() * 1.5));
                    const max = Math.max(1, totalEarnings || 1);
                    const h = Math.max(6, (v / max) * 100);
                    return (
                      <div
                        key={i}
                        className="w-6 bg-gradient-to-t from-emerald-400 to-sky-500 rounded-sm"
                        style={{ height: `${h}%` }}
                        title={`${fmtINR(v)}`}
                      />
                    );
                  })}
                </div>
              </div>
            </div>
          </div>

          {/* Right column: systems & actions */}
          <aside className="space-y-6">
            <div className="bg-[#0f1720] border border-[#1f2730] rounded-xl p-4 shadow">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-gray-400">Income Snapshot</div>
                  <div className="text-lg font-semibold mt-1">
                    {fmtINR(totalEarnings)}
                  </div>
                </div>
                <div>
                  <button
                    onClick={fetchStatus}
                    className="px-3 py-1 bg-slate-800 rounded-md text-sm text-gray-200"
                  >
                    Refresh
                  </button>
                </div>
              </div>

              <div className="mt-4 space-y-3">
                {status?.income_breakdown ? (
                  Object.entries(status.income_breakdown).map(([k, v]) => (
                    <div
                      key={k}
                      className="flex items-center justify-between text-sm text-gray-300"
                    >
                      <div>{k}</div>
                      <div className="font-medium">{fmtINR(v)}</div>
                    </div>
                  ))
                ) : (
                  <div className="text-sm text-gray-500">
                    No breakdown available
                  </div>
                )}
              </div>
            </div>

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
                        className={`w-3 h-3 rounded-full ${st === "ok" || st === "online" || st === "Active" || st === "accepted" ? "bg-emerald-400" : "bg-orange-400"}`}
                      />
                      <div className="text-gray-300">{name}</div>
                    </div>
                    <div className="text-sm text-gray-400">{st}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-[#0f1720] border border-[#1f2730] rounded-xl p-4 shadow">
              <div className="text-sm text-gray-400">Quick Actions</div>
              <div className="mt-3 flex flex-col gap-2">
                <button
                  onClick={() => window.open("/reports", "_blank")}
                  className="w-full bg-gradient-to-r from-sky-500 to-emerald-400 text-black font-semibold py-2 rounded"
                >
                  Open Reports
                </button>
                <button
                  onClick={() => alert("Triggering manual daily sync...")}
                  className="w-full border border-[#23333a] py-2 rounded text-sm"
                >
                  Trigger Manual Sync
                </button>
              </div>
            </div>
          </aside>
        </div>

        {/* Activity log */}
        <div className="mt-6 bg-[#0f1720] border border-[#1f2730] rounded-xl p-6 shadow">
          <div className="flex items-center justify-between mb-4">
            <div className="font-semibold">Activity Timeline</div>
            <div className="text-sm text-gray-400">Recent events</div>
          </div>

          <div className="space-y-3 max-h-64 overflow-auto">
            {status?.activity?.length ? (
              status.activity.map((a, i) => (
                <div key={i} className="flex items-start gap-3">
                  <div className="w-2 h-8 bg-[#14202a] rounded" />
                  <div>
                    <div className="text-sm text-gray-300">{a.message}</div>
                    <div className="text-xs text-gray-500">{a.time}</div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-sm text-gray-500">No activity yet</div>
            )}
          </div>
        </div>

        <footer className="mt-6 text-center text-sm text-gray-500">
          JRAVIS • Mission 2040 — Built for autonomous growth
        </footer>
      </div>

      {/* Lock modal (simple) */}
      {locked && (
        <div className="fixed inset-0 backdrop-blur-sm flex items-center justify-center">
          <div className="bg-[#071018] border border-[#19303a] rounded-lg p-6 w-full max-w-sm">
            <div className="text-lg font-semibold mb-2">Enter Lock Code</div>
            <input
              value={lockInput}
              onChange={(e) => setLockInput(e.target.value)}
              className="w-full p-3 rounded bg-[#0b1220] border border-[#21303a] text-white"
              placeholder="6-digit lock code"
            />
            <div className="mt-4 flex justify-end gap-2">
              <button
                onClick={() => setLocked(false)}
                className="px-4 py-2 rounded border border-[#23333a]"
              >
                Cancel
              </button>
              <button
                onClick={handleUnlock}
                className="px-4 py-2 rounded bg-emerald-400 text-black font-semibold"
              >
                Unlock
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Error toast */}
      {error && (
        <div className="fixed bottom-6 right-6 bg-[#2a1b1b] border border-red-600 text-white px-4 py-3 rounded">
          Error: {error}
        </div>
      )}
    </div>
  );
}

// Notes for integration:
// - Drop this component into your Next.js `app/page.jsx` or `pages/index.jsx`.
// - Make sure Tailwind is configured. The component uses only Tailwind utility classes.
// - Server can inject lock code to window.__JRAVIS_LOCK if desired.
