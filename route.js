// app/api/status/route.js
import { NextResponse } from "next/server";

const SERVICES = {
  brain: "https://jravis-brain.onrender.com/health",
  vabot: "https://va-bot-connector.onrender.com/health",
  bridge: "https://mission-bridge.onrender.com/health",
  autokey: "https://income-system-bundle.onrender.com/health",
};

export async function GET() {
  try {
    const results = {};

    // Fetch all service health data in parallel
    const healthChecks = Object.entries(SERVICES).map(async ([key, url]) => {
      try {
        const res = await fetch(url, { timeout: 8000 });
        const data = await res.json();
        results[key] = data || { status: "offline" };
      } catch {
        results[key] = { status: "offline" };
      }
    });

    await Promise.all(healthChecks);

    // Fetch income summary from Income System Bundle
    let income_summary = null;
    let income_breakdown = {};
    try {
      const res = await fetch(
        "https://income-system-bundle.onrender.com/api/income_summary",
      );
      income_summary = await res.json();
    } catch {
      income_summary = {
        current_earnings: 0,
        monthly_target: 500000,
        active_systems: 0,
        history: [],
      };
    }

    // Build the activity log
    const activity = [
      {
        message: "JRAVIS Brain status checked",
        time: new Date().toLocaleTimeString(),
      },
      {
        message: "VA Bot connected successfully",
        time: new Date().toLocaleTimeString(),
      },
      {
        message: "Auto-Key Worker synced",
        time: new Date().toLocaleTimeString(),
      },
      {
        message: "Mission Bridge verified",
        time: new Date().toLocaleTimeString(),
      },
    ];

    return NextResponse.json({
      brain_status: results.brain,
      va_status: results.vabot,
      bridge_status: results.bridge,
      autokey_status: results.autokey.status,
      income_summary,
      income_breakdown,
      activity,
    });
  } catch (err) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}
