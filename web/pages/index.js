import { useEffect, useState } from "react";
import axios from "axios";
import LockScreen from "../components/LockScreen";
import PhaseCard from "../components/PhaseCard";
import ChatPanel from "../components/ChatPanel";

export default function Dashboard() {
  const [locked, setLocked] = useState(true);
  const [data, setData] = useState(null);
  const [tab, setTab] = useState("phase1");
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
    try {
      const r = await axios.get("/api/va_dashboard_data");
      setData(r.data);
    } catch (e) {
      console.error(e);
    }
  };
  return locked ? (
    <LockScreen onUnlock={() => setLocked(false)} />
  ) : (
    <div className="min-h-screen bg-dark text-white p-4">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">JRAVIS Mission 2040 — HQ</h1>
        <div className="space-x-2">
          <button
            onClick={() => setTab("phase1")}
            className="px-3 py-1 bg-gray-800 rounded"
          >
            Phase 1
          </button>
          <button
            onClick={() => setTab("phase2")}
            className="px-3 py-1 bg-gray-800 rounded"
          >
            Phase 2
          </button>
          <button
            onClick={() => setTab("phase3")}
            className="px-3 py-1 bg-gray-800 rounded"
          >
            Phase 3
          </button>
        </div>
      </header>

      <section className="mt-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {data &&
            Object.keys(data.phases).map((pkey) =>
              pkey === tab ? (
                <PhaseCard
                  key={pkey}
                  phaseKey={pkey}
                  payload={data.phases[pkey]}
                />
              ) : null,
            )}
        </div>
      </section>

      <ChatPanel />
    </div>
  );
}
