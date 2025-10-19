// Import the new widget
import HealthMonitorWidget from "@/components/widgets/HealthMonitorWidget";

export default function Dashboard() {
  return (
    <main className="p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 bg-gray-950 min-h-screen text-gray-100">
      {/* 🧠 Mission Overview */}
      <section className="col-span-2 lg:col-span-3">
        <h1 className="text-3xl font-bold mb-4">JRAVIS Dashboard v5</h1>
      </section>

      {/* 💹 Income System Overview */}
      <div className="col-span-1">
        {/* Your existing IncomeWidget component */}
        {/* <IncomeWidget /> */}
      </div>

      {/* 🔁 Task Progress Overview */}
      <div className="col-span-1">
        {/* Your existing TaskWidget component */}
        {/* <TaskWidget /> */}
      </div>

      {/* 🩺 System Health Monitor */}
      <div className="col-span-1 md:col-span-2">
        <HealthMonitorWidget />
      </div>

      {/* 📊 Add any other widgets below */}
    </main>
  );
}

import React from "react";

export default function Home() {
  return (
    <main
      style={{
        backgroundColor: "#0b0b0b",
        color: "#f0f0f0",
        minHeight: "100vh",
        padding: "2rem",
        fontFamily: "sans-serif",
      }}
    >
      <h1 style={{ fontSize: "2rem", fontWeight: "bold" }}>
        JRAVIS Dashboard v5 — Mission 2040
      </h1>
      <p style={{ color: "#aaa", marginTop: "1rem" }}>
        ✅ Dashboard running successfully. Health Monitor will appear here soon.
      </p>
    </main>
  );
}

import HeaderBar from "@/components/layout/HeaderBar";
import SidebarNav from "@/components/layout/SidebarNav";
import HealthMonitorWidget from "@/components/widgets/HealthMonitorWidget";

export default function DashboardHome() {
  return (
    <main className="bg-mission-bg text-mission-text min-h-screen p-6">
      <HeaderBar />

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="md:col-span-1">
          <SidebarNav />
        </div>

        <div className="md:col-span-3">
          <HealthMonitorWidget />
        </div>
      </div>
    </main>
  );
}

import IncomeSummaryWidget from "@/components/widgets/IncomeSummaryWidget";

{
  /* Income Summary + Progress */
}
<div className="mt-6">
  <IncomeSummaryWidget />
</div>;

import PhaseOverviewWidget from "@/components/widgets/PhaseOverviewWidget";

{
  /* Mission Phases */
}
<div className="mt-6">
  <PhaseOverviewWidget />
</div>;

import SystemActivityWidget from "@/components/widgets/SystemActivityWidget";

{
  /* System Activity Timeline */
}
<div className="mt-6">
  <SystemActivityWidget />
</div>;

import React from "react";
import {
  CheckCircle,
  CircleDot,
  TrendingUp,
  Home,
  Calendar,
} from "lucide-react";

export default function Mission2040Dashboard() {
  return (
    <main className="min-h-screen bg-mission-bg text-mission-text p-8 font-sans">
      <h1 className="text-2xl font-bold mb-6">
        Jarvis Brain – Mission 2040 Dashboard
      </h1>

      {/* Mission Progress + Earnings */}
      <section className="grid md:grid-cols-3 gap-6 mb-8">
        <div className="col-span-2 card">
          <h2 className="text-lg font-semibold mb-2">Mission 2040 Progress</h2>
          <div className="w-full bg-gray-800 h-3 rounded-full mb-3">
            <div className="h-3 bg-mission-accent rounded-full w-[85%]" />
          </div>
          <p className="text-sm text-mission-subtext">
            Current goal – Debt clearance & property purchase by June 2027
          </p>
        </div>

        <div className="card flex flex-col justify-between">
          <h2 className="text-lg font-semibold mb-2">Earnings</h2>
          <div>
            <p className="text-3xl font-bold">₹ 6,24,000</p>
            <p className="text-xl text-mission-subtext">$ 8,250</p>
          </div>
        </div>
      </section>

      {/* Phase Status */}
      <section className="card mb-8 overflow-x-auto">
        <h2 className="text-lg font-semibold mb-3">Phase Status</h2>
        <table className="w-full text-sm border-collapse">
          <thead className="text-mission-subtext border-b border-mission-border">
            <tr>
              <th className="text-left p-2">Phase</th>
              <th className="text-left p-2">Status</th>
              <th className="text-left p-2">Target</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-b border-mission-border">
              <td className="p-2">Phase 1</td>
              <td className="p-2 text-green-400 font-medium">Active</td>
              <td className="p-2">₹ 4 Cr loan clearance</td>
            </tr>
            <tr className="border-b border-mission-border">
              <td className="p-2">Phase 2</td>
              <td className="p-2 text-yellow-400 font-medium">Scale up</td>
              <td className="p-2">Global growth setup</td>
            </tr>
            <tr>
              <td className="p-2">Phase 3</td>
              <td className="p-2 text-purple-400 font-medium">Preparing</td>
              <td className="p-2">Automation – Robo Mode</td>
            </tr>
          </tbody>
        </table>
      </section>

      {/* Task Timeline + Property Tracker */}
      <section className="grid md:grid-cols-2 gap-6 mb-8">
        <div className="card">
          <h2 className="text-lg font-semibold mb-3">Task Timeline</h2>
          <ul className="text-sm space-y-2">
            <li className="flex items-center gap-2">
              <CheckCircle className="text-green-400" size={16} /> Completed
            </li>
            <li className="flex items-center gap-2">
              <CircleDot className="text-blue-400" size={16} /> Today’s Tasks
            </li>
            <li className="flex items-center gap-2">
              <Calendar className="text-gray-400" size={16} /> Tomorrow’s Plan
            </li>
          </ul>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold mb-3">
            Property & Debt Tracker
          </h2>
          <div className="space-y-3 text-sm">
            <div>
              <div className="flex justify-between mb-1">
                <span>Debt Clearance Progress</span>
                <span>₹ 2 Cr</span>
              </div>
              <div className="w-full bg-gray-800 h-2 rounded-full">
                <div className="h-2 bg-blue-500 rounded-full w-[60%]" />
              </div>
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <span>Savings for Property</span>
                <span>₹ 62 L</span>
              </div>
              <div className="w-full bg-gray-800 h-2 rounded-full">
                <div className="h-2 bg-mission-accent rounded-full w-[40%]" />
              </div>
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <span>Timeline to June 2027</span>
              </div>
              <div className="w-full bg-gray-800 h-2 rounded-full">
                <div className="h-2 bg-green-400 rounded-full w-[80%]" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Earnings Tracker */}
      <section className="card">
        <h2 className="text-lg font-semibold mb-3">Earnings Tracker</h2>
        <div className="flex flex-col md:flex-row md:items-center justify-between">
          <div className="text-sm text-mission-subtext">
            <p className="mb-1">Projected Monthly Goal</p>
            <p className="text-mission-accent text-lg font-semibold">
              ₹ 12,00,000
            </p>
          </div>
          <TrendingUp className="text-mission-accent mt-3 md:mt-0" size={32} />
        </div>
      </section>
    </main>
  );
}

import ReportTrackerWidget from "../components/ReportTrackerWidget";

export default function Dashboard() {
  return (
    <div className="flex flex-wrap gap-4 p-6 bg-black min-h-screen text-white">
      {/* Existing widgets */}
      <ReportTrackerWidget />
    </div>
  );
}

import ReportTrackerWidget from "../components/ReportTrackerWidget";
import IncomeInsightsCard from "../components/IncomeInsightsCard";

export default function Dashboard() {
  return (
    <div className="flex flex-wrap gap-4 p-6 bg-black min-h-screen text-white">
      <ReportTrackerWidget />
      <IncomeInsightsCard />
    </div>
  );
}
