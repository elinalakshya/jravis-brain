import LiveFeedConnector from "@/components/LiveFeedConnector";
import { useState } from "react";

export default function DashboardPage() {
  const [feedItems, setFeedItems] = useState([]);

  function handleUpdate(data) {
    setFeedItems((prev) => [data, ...prev].slice(0, 20));
  }

  return (
    <div style={{ padding: 20 }}>
      <h1>JRAVIS Dashboard</h1>
      <LiveFeedConnector onUpdate={handleUpdate} />
      <h2>Live Updates</h2>
      <ul>
        {feedItems.map((it, i) => (
          <li key={i}>
            [{it.type}] {new Date(it.ts).toLocaleTimeString()} —{" "}
            {JSON.stringify(it.payload)}
          </li>
        ))}
      </ul>
    </div>
  );
}
