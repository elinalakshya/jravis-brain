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
