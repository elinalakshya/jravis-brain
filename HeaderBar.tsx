import React, { useEffect, useState } from "react";
import { Brain, Activity, Calendar, Clock } from "lucide-react";

export default function HeaderBar() {
  const [time, setTime] = useState<string>("");

  useEffect(() => {
    const update = () => {
      const now = new Date();
      setTime(
        now.toLocaleTimeString("en-IN", {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        }),
      );
    };
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, []);

  const today = new Date().toLocaleDateString("en-IN", {
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  return (
    <header className="flex justify-between items-center bg-mission-card border border-mission-border p-4 rounded-2xl shadow-neon mb-6">
      <div className="flex items-center gap-2">
        <Brain className="text-mission-accent" size={24} />
        <h1 className="text-xl font-heading tracking-wide">
          JRAVIS Command Console
        </h1>
      </div>
      <div className="flex items-center gap-4 text-mission-subtext text-sm">
        <div className="flex items-center gap-1">
          <Calendar size={16} /> {today}
        </div>
        <div className="flex items-center gap-1">
          <Clock size={16} /> {time}
        </div>
        <div className="flex items-center gap-1 text-mission-accent font-semibold">
          <Activity size={16} /> Phase 1 Active
        </div>
      </div>
    </header>
  );
}

("use client");
import { useState, useEffect } from "react";

export default function HeaderBar() {
  const [status, setStatus] = useState("🟡 Checking...");
  const [phase, setPhase] = useState("Phase 1");
  const [color, setColor] = useState("text-yellow-400");

  async function checkSystemStatus() {
    try {
      const res = await fetch("https://jravis-brain.onrender.com/health");
      if (res.ok) {
        setStatus("🟢 Active");
        setColor("text-green-400");
      } else {
        setStatus("🔴 Offline");
        setColor("text-red-400");
      }
    } catch (err) {
      setStatus("🔴 Offline");
      setColor("text-red-400");
    }
  }

  useEffect(() => {
    checkSystemStatus();
    const interval = setInterval(checkSystemStatus, 10000); // every 10 seconds
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="flex items-center justify-between px-6 py-3 bg-gray-950 text-gray-200 shadow-lg border-b border-gray-800">
      <div className="flex items-center gap-2">
        <span className="text-2xl">🚀</span>
        <h1 className="text-xl font-semibold tracking-wide">
          Mission <span className="text-blue-400">2040</span> Console
        </h1>
      </div>

      <div className="flex items-center gap-6 text-sm">
        <div className="text-gray-400">
          Boss <span className="text-white font-medium">Prakruthi 👑</span>
        </div>
        <div className="text-gray-400">
          System:{" "}
          <span className="flex items-center gap-1">
            <span
              className={`h-2 w-2 rounded-full ${
                status.includes("Active")
                  ? "bg-green-400 animate-pulse"
                  : "bg-red-500"
              }`}
            ></span>
            <span className={`${color} font-semibold`}>{status}</span>
          </span>
        </div>
        <div className="text-gray-400">
          Mode: <span className="text-blue-400 font-semibold">{phase}</span>
        </div>
      </div>
    </header>
  );
}
