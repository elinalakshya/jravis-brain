import React, { useEffect, useState } from "react";
import axios from "axios";
import { motion } from "framer-motion";
import { Lock, CheckCircle, RefreshCw } from "lucide-react";

const API = "https://jravis-dashboard-v5-py.onrender.com"; // your backend

export default function App() {
  const [data, setData] = useState(null);
  const [locked, setLocked] = useState(true);
  const [code, setCode] = useState("");
  const [error, setError] = useState("");

  async function unlock() {
    try {
      const res = await axios.post(`${API}/unlock`, { code });
      if (res.status === 200) setLocked(false);
    } catch {
      setError("Invalid Code");
    }
  }

  async function fetchData() {
    const res = await axios.get(`${API}/api/live`);
    setData(res.data);
  }

  useEffect(() => {
    if (!locked) {
      fetchData();
      const i = setInterval(fetchData, 15000);
      return () => clearInterval(i);
    }
  }, [locked]);

  if (locked)
    return (
      <div className="flex items-center justify-center h-screen bg-[#030712]">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="p-10 rounded-2xl bg-[#0b1320]/80 border border-cyan-800 text-center"
        >
          <Lock className="mx-auto text-cyan-400 w-10 h-10 mb-3" />
          <h2 className="text-xl mb-4">JRAVIS Dashboard Locked</h2>
          <input
            type="password"
            placeholder="Enter Lock Code"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            className="p-2 rounded bg-gray-900 text-cyan-200 border border-cyan-700 mb-3 w-full"
          />
          <button
            onClick={unlock}
            className="bg-cyan-600 px-4 py-2 rounded hover:bg-cyan-500 w-full"
          >
            Unlock
          </button>
          {error && <p className="text-red-400 mt-2">{error}</p>}
        </motion.div>
      </div>
    );

  return (
    <div className="min-h-screen bg-[#030712] p-6 text-gray-100">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-cyan-400">
            JRAVIS Command Console — Mission 2040
          </h1>
          <button
            onClick={() => setLocked(true)}
            className="bg-gray-800 px-4 py-2 rounded text-cyan-300 hover:bg-gray-700"
          >
            Lock
          </button>
        </div>

        <div className="grid md:grid-cols-3 gap-4 mb-6">
          <Card title="Total Revenue" value={`₹ ${data?.revenue || "0.00"}`} />
          <Card title="Total Orders" value={data?.orders || "0"} />
          <Card
            title="Progress"
            value={`${data?.progress || 0}%`}
            glow
            progress={data?.progress || 0}
          />
        </div>

        <h2 className="text-xl text-cyan-300 mb-3">Phase 1 Streams</h2>
        <div className="bg-[#0b1320] p-4 rounded-xl border border-cyan-900">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-cyan-900 text-cyan-400">
                <th>#</th>
                <th>System</th>
                <th>Status</th>
                <th>Last Success</th>
              </tr>
            </thead>
            <tbody>
              {data?.systems?.map((s, i) => (
                <tr
                  key={i}
                  className="border-b border-gray-800 hover:bg-gray-900"
                >
                  <td>{i + 1}</td>
                  <td>{s.name}</td>
                  <td>
                    {s.success ? (
                      <CheckCircle className="inline text-green-400 w-4 h-4" />
                    ) : (
                      <RefreshCw className="inline text-yellow-400 w-4 h-4 animate-spin" />
                    )}
                  </td>
                  <td>{s.last_success || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className="text-gray-500 text-sm text-center mt-8">
          JRAVIS Live Feed • Updated {new Date().toUTCString()}
        </p>
      </div>
    </div>
  );
}

function Card({ title, value, glow, progress }) {
  return (
    <motion.div
      whileHover={{ scale: 1.03 }}
      className="bg-[#0b1320] p-4 rounded-xl border border-cyan-900 text-center"
    >
      <h2 className="text-lg text-cyan-300 mb-2">{title}</h2>
      <div
        className={`text-3xl font-bold ${
          glow
            ? "text-cyan-400 drop-shadow-[0_0_10px_#06b6d4]"
            : "text-green-400"
        }`}
      >
        {value}
      </div>
      {glow && (
        <div className="w-full bg-gray-800 rounded-full h-2 mt-3">
          <div
            className="bg-cyan-500 h-2 rounded-full transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}
    </motion.div>
  );
}
