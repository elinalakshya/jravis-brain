import React from "react";
import { Zap, Rocket, ShieldCheck } from "lucide-react";

const phases = [
  {
    icon: Zap,
    title: "Phase 1 — Fast Kickstart",
    target: "₹2.5 – ₹5 L/month by Dec 2025",
    desc: "Immediate execution, fastest scaling, early cash inflow.",
    color: "from-green-500/20 to-green-600/10 border-green-500/40",
  },
  {
    icon: Rocket,
    title: "Phase 2 — Scaling & Medium Systems",
    target: "₹6 – ₹10 L/month by Dec 2026",
    desc: "Stronger automation, digital asset growth, global scaling.",
    color: "from-yellow-500/20 to-yellow-600/10 border-yellow-500/40",
  },
  {
    icon: ShieldCheck,
    title: "Phase 3 — Advanced Passive Engines",
    target: "₹12 – ₹15 L+/month by 2027",
    desc: "Long-term heavy-scale global recurring income engines.",
    color: "from-purple-500/20 to-purple-600/10 border-purple-500/40",
  },
];

export default function PhaseOverviewWidget() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
      {phases.map((phase) => (
        <div
          key={phase.title}
          className={`p-5 rounded-2xl border bg-gradient-to-b ${phase.color} shadow-md hover:shadow-neon transition-all duration-300`}
        >
          <div className="flex items-center gap-2 mb-3">
            <phase.icon className="text-mission-accent" size={22} />
            <h3 className="font-heading text-lg">{phase.title}</h3>
          </div>
          <p className="text-sm text-mission-subtext mb-2">{phase.desc}</p>
          <p className="text-xs text-mission-accent font-semibold">
            {phase.target}
          </p>
        </div>
      ))}
    </div>
  );
}
