import React, { useState, useEffect } from "react";
import { Activity, Bot, FileText, Coins } from "lucide-react";

interface LogEntry {
  time: string;
  type: string;
  message: string;
}

export default function SystemActivityWidget() {
  const [logs, setLogs] = useState<LogEntry[]>([]);

  useEffect(() => {
    const interval = setInterval(() => {
      const actions = [
        {
          type: "VA Bot",
          icon: <Bot />,
          message: "VA Bot executed automated task successfully.",
        },
        {
          type: "Report",
          icon: <FileText />,
          message: "Daily income report generated & encrypted.",
        },
        {
          type: "System",
          icon: <Activity />,
          message: "JRAVIS Bridge synchronized phase data.",
        },
        {
          type: "Income",
          icon: <Coins />,
          message: "New ₹1500 passive income added from Phase 1 system.",
        },
      ];
      const random = actions[Math.floor(Math.random() * actions.length)];
      const newLog = {
        time: new Date().toLocaleTimeString("en-IN", { hour12: false }),
        type: random.type,
        message: random.message,
      };
      setLogs((prev) => [newLog, ...prev.slice(0, 19)]); // keep last 20 entries
    }, 4000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="card mt-6 max-h-[400px] overflow-y-auto">
      <div className="flex items-center gap-2 mb-3">
        <Activity className="text-mission-accent" size={22} />
        <h2 className="font-heading text-lg">System Activity Timeline</h2>
      </div>
      <div className="space-y-3 text-sm text-mission-subtext">
        {logs.length === 0 && (
          <p className="text-gray-500">Awaiting first system event...</p>
        )}
        {logs.map((log, index) => (
          <div key={index} className="border-b border-mission-border pb-2">
            <div className="flex justify-between text-xs text-gray-500 mb-1">
              <span>{log.time}</span>
              <span>{log.type}</span>
            </div>
            <p className="text-gray-300">{log.message}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
