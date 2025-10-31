// pages/dashboard.jsx
import LiveFeedConnector from "@/components/LiveFeedConnector";
import { useState, useEffect } from "react";

export default function DashboardPage() {
  const [feedItems, setFeedItems] = useState([]);
  const [incomeTotal, setIncomeTotal] = useState(0);
  const [taskSummary, setTaskSummary] = useState({
    done: 0,
    pending: 0,
    issues: 0,
  });

  function handleUpdate(data) {
    setFeedItems((prev) => [data, ...prev].slice(0, 20));

    // Auto-update widgets based on payload type
    if (data.type === "jravis_snapshot" && data.payload) {
      const inc = data.payload.income || [];
      const total = inc.reduce((sum, i) => sum + (i.amount || 0), 0);
      setIncomeTotal(total);

      const t = data.payload.tasks || {};
      setTaskSummary({
        done: t.completed || 0,
        pending: t.pending || 0,
        issues: t.error || 0,
      });
    }
  }

  // optional local timer to refresh visuals every 3 min
  useEffect(() => {
    const interval = setInterval(() => {
      setFeedItems((f) => [...f]); // triggers re-render
    }, 180000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ padding: 20, fontFamily: "sans-serif" }}>
      <header>
        <h1>JRAVIS Dashboard</h1>
        <LiveFeedConnector onUpdate={handleUpdate} />
      </header>

      <section style={{ marginTop: 20 }}>
        <h2>📈 Income Summary</h2>
        <div style={{ fontSize: "1.5rem", fontWeight: "bold" }}>
          ₹ {incomeTotal.toLocaleString("en-IN")}
        </div>
      </section>

      <section style={{ marginTop: 20 }}>
        <h2>🧠 VA Bot Task Summary</h2>
        <ul>
          <li>✅ Completed: {taskSummary.done}</li>
          <li>🕐 Pending: {taskSummary.pending}</li>
          <li>⚠️ Issues: {taskSummary.issues}</li>
        </ul>
      </section>

      <section style={{ marginTop: 20 }}>
        <h2>🔴 Live Feed (latest 20)</h2>
        <ul>
          {feedItems.map((it, idx) => (
            <li key={idx}>
              [{it.type}] {new Date(it.ts).toLocaleTimeString()} —{" "}
              {JSON.stringify(it.payload)}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
