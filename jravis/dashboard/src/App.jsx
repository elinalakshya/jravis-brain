import React, { useState, useEffect } from "react";
import axios from "axios";

const API_BASE = "http://localhost:5001"; // Jarvis Brain API

export default function App() {
  const [command, setCommand] = useState("");
  const [logs, setLogs] = useState([]);
  const [memory, setMemory] = useState([]);

  const sendCommand = async () => {
    if (!command) return;
    try {
      const res = await axios.post(`${API_BASE}/command`, { command });
      setLogs((prev) => [...prev, res.data]);
      setCommand("");
    } catch (err) {
      alert("Error sending command: " + err.message);
    }
  };

  const fetchMemory = async () => {
    try {
      const res = await axios.get(`${API_BASE}/memory_search?q=latest`);
      setMemory(res.data);
    } catch (err) {
      console.error("Memory fetch failed", err);
    }
  };

  useEffect(() => {
    fetchMemory();
  }, []);

  return (
    <div style={{ fontFamily: "sans-serif", padding: "20px" }}>
      <h1>🧠 Jarvis Dashboard</h1>

      <div style={{ marginTop: "20px" }}>
        <input
          value={command}
          onChange={(e) => setCommand(e.target.value)}
          placeholder="Type a command for Jarvis..."
          style={{ padding: "8px", width: "300px" }}
        />
        <button
          onClick={sendCommand}
          style={{ marginLeft: "10px", padding: "8px 12px" }}
        >
          Send
        </button>
      </div>

      <h2 style={{ marginTop: "30px" }}>📜 Execution Logs</h2>
      <pre
        style={{
          background: "#111",
          color: "#0f0",
          padding: "10px",
          borderRadius: "6px",
        }}
      >
        {JSON.stringify(logs, null, 2)}
      </pre>

      <h2 style={{ marginTop: "30px" }}>🗂 Memory Snapshots</h2>
      <pre style={{ background: "#eee", padding: "10px", borderRadius: "6px" }}>
        {JSON.stringify(memory, null, 2)}
      </pre>
    </div>
  );
}
