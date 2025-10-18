import React, { useState, useEffect } from "react";
import { TrendingUp, Target, Coins, Layers } from "lucide-react";

export default function IncomeSummaryWidget() {
  const [progress, setProgress] = useState(0);
  const [income, setIncome] = useState(0);

  useEffect(() => {
    // Simulate live updates for demo
    const interval = setInterval(() => {
      setIncome((prev) =>
        prev < 350000 ? prev + Math.floor(Math.random() * 1000) : prev,
      );
      setProgress((prev) => (prev < 70 ? prev + Math.random() * 2 : prev));
    }, 1500);
    return () => clearInterval(interval);
  }, []);

  const monthlyTarget = 500000; // ₹5L target (example)

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Coins className="text-mission-accent" size={22} />
          <h2 className="font-semibold text-lg">Income & Mission Progress</h2>
        </div>
        <Target className="text-mission-accent" size={20} />
      </div>

      <div className="space-y-3 text-sm">
        <div className="flex justify-between">
          <span>Current Earnings:</span>
          <span className="font-semibold text-mission-accent">
            ₹{income.toLocaleString("en-IN")}
          </span>
        </div>

        <div className="flex justify-between">
          <span>Monthly Target:</span>
          <span>₹{monthlyTarget.toLocaleString("en-IN")}</span>
        </div>

        <div className="w-full bg-gray-800 h-2 rounded-full mt-2">
          <div
            className="bg-mission-accent h-2 rounded-full transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>

        <div className="flex justify-between text-xs text-gray-400 mt-1">
          <span>Progress</span>
          <span>{progress.toFixed(1)}%</span>
        </div>

        <div className="flex justify-between mt-4">
          <div className="flex items-center gap-2">
            <Layers size={16} className="text-mission-accent" />
            <span>Active Systems: 10/30</span>
          </div>
          <div className="flex items-center gap-2">
            <TrendingUp size={16} className="text-mission-accent" />
            <span>Phase 1 Growth: +8%</span>
          </div>
        </div>
      </div>
    </div>
  );
}
