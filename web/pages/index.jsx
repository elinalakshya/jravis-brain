import { useEffect, useState } from "react";
import LockScreen from "../components/LockScreen";
import PhaseCards from "../components/PhaseCards";
import ChatPanel from "../components/ChatPanel";
import LiveFeedPanel from "../components/LiveFeedPanel";
import axios from "axios";

export default function DashboardPage() {
  const [locked, setLocked] = useState(true);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!locked) fetchData();
    const iv = setInterval(
      () => {
        if (!locked) fetchData();
      },
      30 * 60 * 1000,
    );
    return () => clearInterval(iv);
  }, [locked]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const r = await axios.get("/api/va_dashboard_data");
      setData(r.data);
    } catch (e) {
      console.error("Fetch dashboard data error:", e?.message || e);
    } finally {
      setLoading(false);
    }
  };

  return locked ? (
    <LockScreen onUnlock={() => setLocked(false)} />
  ) : (
    <div className="min-h-screen bg-gradient-to-b from-[#07070b] via-[#0e0f14] to-[#07070b] text-white p-4">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight">
            JRAVIS — Mission 2040
          </h1>
          <div className="text-sm text-gray-400">
            Secure HQ • Live earnings & VA Bot
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className="text-xs text-gray-400">Last sync</div>
            <div className="text-sm">{data?.last_sync || "—"}</div>
          </div>
        </div>
      </header>

      <main className="mt-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        <section className="lg:col-span-2 space-y-6">
          <PhaseCards payload={data?.phases} loading={loading} />
        </section>

        <aside className="space-y-6">
          <LiveFeedPanel />
        </aside>
      </main>

      <ChatPanel />
    </div>
  );
}

import React, { useState } from "react";
import LockScreen from "@/components/LockScreen";
import LiveFeedPanel from "@/components/LiveFeedPanel";

export default function DashboardPage() {
  const [unlocked, setUnlocked] = useState(false);

  if (!unlocked) return <LockScreen onUnlock={() => setUnlocked(true)} />;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-black text-white flex flex-col items-center justify-center p-6">
      <button
        onClick={() => setUnlocked(false)}
        className="absolute top-5 right-5 px-4 py-2 rounded-lg bg-red-600 hover:bg-red-500 font-medium transition-all duration-200"
      >
        Logout
      </button>

      <h1 className="text-4xl font-bold mb-6 text-blue-400 tracking-wide">
        JRAVIS Dark Tech Dashboard
      </h1>
      <div className="w-full max-w-4xl">
        <LiveFeedPanel />
      </div>
    </div>
  );
}
