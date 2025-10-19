// Dashboard.jsx
import React, { useEffect, useState } from "react";

export default function Dashboard() {
  const [stats, setStats] = useState({
    earningsMonth: "Loading...",
    streamsActive: 0,
    systemHealth: "Loading...",
    lastReport: "Loading...",
  });

  const fetchData = async () => {
    try {
      const res = await fetch("http://localhost:3300/api/dashboard");
      const data = await res.json();
      setStats({
        earningsMonth: `₹${data.total_earnings_inr.toLocaleString()}`,
        streamsActive: data.streams_active,
        systemHealth: data.system_health,
        lastReport: data.last_report,
      });
    } catch (err) {
      console.error("Dashboard fetch error:", err);
      setStats((prev) => ({ ...prev, systemHealth: "⚠️ Offline" }));
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000); // refresh every 1 min
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-[#0b0f14] text-slate-200 p-6">
      <div className="max-w-7xl mx-auto">
        <header className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-semibold">
            JRAVIS — Mission 2040 Dashboard
          </h1>
        </header>

        <section className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card title="Monthly Earnings" value={stats.earningsMonth} />
          <Card title="Streams Active" value={stats.streamsActive} />
          <Card title="System Health" value={stats.systemHealth} />
          <Card title="Last Report" value={stats.lastReport} />
        </section>

        <p className="text-sm text-slate-400 text-center mt-4">
          Live feed updates every 60 seconds · Powered by Dhruvayu ⚙️
        </p>
      </div>
    </div>
  );
}

function Card({ title, value }) {
  return (
    <div className="p-4 rounded-2xl bg-gradient-to-br from-slate-800/40 to-slate-900/20 shadow-lg">
      <p className="text-sm text-slate-300">{title}</p>
      <p className="mt-2 text-xl font-bold">{value}</p>
    </div>
  );
}
