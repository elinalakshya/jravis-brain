"use client";
import { useEffect, useState } from "react";

export default function IncomeInsightsCard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  async function fetchSummary() {
    setLoading(true);
    try {
      const res = await fetch(
        "https://jravis-brain.onrender.com/api/earnings_summary",
      );
      if (res.ok) {
        const result = await res.json();
        setData(result);
      }
    } catch (e) {
      console.error("Failed to fetch summary:", e);
    }
    setLoading(false);
  }

  useEffect(() => {
    fetchSummary();
    const interval = setInterval(fetchSummary, 60000); // refresh every 1 min
    return () => clearInterval(interval);
  }, []);

  if (loading)
    return (
      <div className="bg-gray-900 p-4 rounded-2xl text-white">Loading…</div>
    );
  if (!data)
    return (
      <div className="bg-gray-900 p-4 rounded-2xl text-white">
        No data available.
      </div>
    );

  const { total_income, progress_percent, target, next_report_time } = data;

  return (
    <div className="bg-gray-900 p-4 rounded-2xl text-white shadow-lg w-full md:w-1/2">
      <h2 className="text-lg font-semibold mb-2">💰 Income Insights</h2>
      <p className="text-gray-400 mb-4">Next update: {next_report_time}</p>

      <div className="mb-3">
        <p className="text-xl font-bold">₹ {total_income?.toLocaleString()}</p>
        <p className="text-sm text-gray-400">
          Target: ₹ {target?.toLocaleString()}
        </p>
      </div>

      <div className="w-full bg-gray-700 rounded-full h-3">
        <div
          className="bg-green-500 h-3 rounded-full transition-all"
          style={{ width: `${progress_percent}%` }}
        ></div>
      </div>

      <p className="text-sm text-gray-400 mt-2">
        Progress: {progress_percent?.toFixed(1)}%
      </p>

      <button
        onClick={fetchSummary}
        className="mt-3 bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded-lg text-sm"
      >
        🔄 Refresh
      </button>
    </div>
  );
}
