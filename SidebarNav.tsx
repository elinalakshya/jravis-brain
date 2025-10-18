import React from "react";
import { Home, Cpu, FileText, Bot, Settings } from "lucide-react";

const navItems = [
  { label: "Overview", icon: Home },
  { label: "Systems", icon: Cpu },
  { label: "Reports", icon: FileText },
  { label: "VA Bot", icon: Bot },
  { label: "Settings", icon: Settings },
];

export default function SidebarNav() {
  return (
    <aside className="bg-mission-card border border-mission-border rounded-2xl p-4 shadow-md flex flex-col gap-4 h-fit">
      {navItems.map((item) => (
        <button
          key={item.label}
          className="flex items-center gap-2 text-mission-subtext hover:text-mission-accent transition-colors"
        >
          <item.icon size={18} />
          <span className="text-sm font-medium">{item.label}</span>
        </button>
      ))}
    </aside>
  );
}
