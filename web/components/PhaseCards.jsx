import React from "react";

const titleMap = {
  phase1: "Phase 1 — Fast Kickstart",
  phase2: "Phase 2 — Scaling",
  phase3: "Phase 3 — Advanced Engines",
};
const targetMax = { phase1: 14.5, phase2: 15.05, phase3: 16.5 }; // used for progress %

export default function PhaseCards({ payload, loading }) {
  if (loading)
    return (
      <div className="p-6 rounded-2xl bg-[#07080a] text-gray-400">
        Loading...
      </div>
    );

  return (
    <div className="space-y-6">
      {["phase1", "phase2", "phase3"].map((p) => {
        const data = payload?.[p] || { total: 0, streams: [], count: 0 };
        const total = Number(data.total || 0);
        const pct =
          Math.min(
            100,
            Math.round((total / (targetMax[p] * 100000)) * 10000) / 100,
          ) || Math.min(100, Math.round((total / targetMax[p]) * 100) || 0);
        return (
          <div
            key={p}
            className="p-4 bg-gradient-to-r from-[#071018] to-[#0b0d11] border border-[#111315] rounded-2xl shadow-lg"
          >
            <div className="flex items-start justify-between">
              <div>
                <div className="text-sm text-gray-400">{titleMap[p]}</div>
                <div className="text-2xl font-bold mt-1">
                  ₹{total.toLocaleString()}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  Streams: {data.count || data.streams?.length || 0}
                </div>
              </div>
              <div className="text-right">
                <div className="text-xs text-gray-400">Target range</div>
                <div className="text-sm text-gray-200">
                  {p === "phase1"
                    ? "₹3–14.5L"
                    : p === "phase2"
                      ? "₹3.65–15.05L"
                      : "₹4.2–16.5L+"}
                </div>
              </div>
            </div>

            <div className="mt-3">
              <div className="w-full bg-[#0a0b0d] h-3 rounded overflow-hidden">
                <div
                  style={{ width: `${pct}%` }}
                  className="h-3 bg-gradient-to-r from-[#00bcd4] to-[#00e5ff]"
                ></div>
              </div>
              <div className="mt-2 text-xs text-gray-400">
                {Math.round(pct)}% progress
              </div>
            </div>

            <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2">
              {(data.streams || []).slice(0, 6).map((s, i) => (
                <div
                  key={i}
                  className="p-2 bg-[#06070a] border border-[#111214] rounded"
                >
                  <div className="flex justify-between text-sm">
                    <div className="truncate pr-2">{s.name || s.id}</div>
                    <div className="text-gray-200">
                      ₹{Number(s.amount || 0)}
                    </div>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    updated: {s.last_updated || "-"}
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
