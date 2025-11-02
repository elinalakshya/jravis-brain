import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";

export default function LiveFeedPanel() {
  const [status, setStatus] = useState("Loading...");

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const base =
          process.env.NEXT_PUBLIC_API_URL ||
          "https://jravis-backend.onrender.com";
        const res = await fetch(`${base}/healthz`);
        const data = await res.json();
        setStatus(data.status || "ok");
      } catch {
        setStatus("offline");
      }
    };
    fetchHealth();
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-4 bg-white/10 border border-white/20 rounded-xl text-white"
    >
      <h2 className="text-lg font-semibold mb-2">Live Feed Panel</h2>
      <p>Backend status: {status}</p>
    </motion.div>
  );
}
