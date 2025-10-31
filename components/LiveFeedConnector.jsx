// components/LiveFeedConnector.jsx
// Install in front-end: npm i socket.io-client
import { useEffect, useState } from "react";
import io from "socket.io-client";

const SOCKET_URL =
  process.env.NEXT_PUBLIC_LIVE_FEED_URL || "http://localhost:3001";

export default function LiveFeedConnector({ onUpdate }) {
  const [connected, setConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);

  useEffect(() => {
    const socket = io(SOCKET_URL, {
      transports: ["websocket"],
      reconnection: true,
    });
    socket.on("connect", () => setConnected(true));
    socket.on("disconnect", () => setConnected(false));

    socket.on("live_update", (data) => {
      setLastUpdate(data);
      if (typeof onUpdate === "function") onUpdate(data);
    });

    return () => socket.disconnect();
  }, []);

  return (
    <div style={{ display: "inline-block" }}>
      <small>LiveFeed: {connected ? "connected" : "disconnected"}</small>
      {lastUpdate && (
        <div style={{ marginTop: 6 }}>
          <strong>{lastUpdate.type}</strong> ·{" "}
          {new Date(lastUpdate.ts).toLocaleTimeString()}
        </div>
      )}
    </div>
  );
}


import LiveFeedConnector from '@/components/LiveFeedConnector';
import { useState } from 'react';

export default function DashboardPage() {
  const [feedItems, setFeedItems] = useState([]);

  function handleUpdate(data) {
    // push into UI list (keep last 50 for example)
    setFeedItems(prev => [data, ...prev].slice(0, 50));
    // update any widgets: income / tasks / errors...
  }

  return (
    <>
      <header>
        <h1>JRAVIS Dashboard</h1>
        <LiveFeedConnector onUpdate={handleUpdate} />
      </header>

      <section>
        <h2>Live Feed</h2>
        <ul>
          {feedItems.map((it, idx) => (
            <li key={idx}>
              [{it.type}] {new Date(it.ts).toLocaleString()} — {JSON.stringify(it.payload)}
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}

// components/LiveFeedConnector.js
import React, { useEffect, useState } from "react";

export default function LiveFeedConnector() {
  const [status, setStatus] = useState("Connecting...");

  useEffect(() => {
    // Simulate backend connection for now
    const timer = setTimeout(() => {
      setStatus("🟢 Connected to JRAVIS Backend (Secure)");
    }, 1500);

    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="mt-4 p-3 rounded-lg bg-gray-900 border border-cyan-600 text-cyan-300 text-sm font-mono shadow-md">
      <p>{status}</p>
    </div>
  );
}
