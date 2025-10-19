"use client";
import { useEffect, useState } from "react";

export default function ReportTrackerWidget() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);

  async function fetchReports() {
    setLoading(true);
    try {
      const res = await fetch(
        "https://jravis-brain.onrender.com/report_log.json",
      );
      if (res.ok) {
        const data = await res.json();
        setReports(data.slice(-5).reverse());
      }
    } catch (e) {
      console.error("Fetch failed", e);
    }
    setLoading(false);
  }

  useEffect(() => {
    fetchReports();
    const interval = setInterval(fetchReports, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-gray-900 text-white p-4 rounded-2xl shadow-lg w-full md:w-1/2">
      <h2 className="text-lg font-semibold mb-2">
        📊 Mission 2040 Report Tracker
      </h2>
      {loading && <p className="text-gray-400">Loading…</p>}
      {!loading && reports.length === 0 && (
        <p className="text-gray-500">No reports logged yet.</p>
      )}
      <ul className="space-y-2">
        {reports.map((r: any, i: number) => (
          <li
            key={i}
            className="bg-gray-800 p-2 rounded-lg flex justify-between items-center"
          >
            <span>{r.summary}</span>
            <span className="text-sm text-gray-400">
              {new Date(r.timestamp).toLocaleString()}
            </span>
          </li>
        ))}
      </ul>
      <button
        onClick={fetchReports}
        className="mt-3 bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded-lg text-sm"
      >
        🔁 Sync Now
      </button>
    </div>
  );
}
