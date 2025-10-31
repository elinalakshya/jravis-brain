import { useEffect, useState } from "react";
import CryptoJS from "crypto-js";
import { motion, AnimatePresence } from "framer-motion";

/*
  Seed the hashed code in the browser console once:
  localStorage.setItem("jravis_lock_hash", CryptoJS.SHA256("YOUR_CODE").toString());
*/

const LOCK_KEY = "jravis_lock_hash";
const UNLOCKED_FLAG = "jravis_unlocked_flag";

const verifyCode = (code) => {
  const stored = localStorage.getItem(LOCK_KEY);
  if (!stored) return false;
  return CryptoJS.SHA256(code).toString() === stored;
};

export default function LockScreen({ onUnlock }) {
  const [code, setCode] = useState("");
  const [err, setErr] = useState("");
  const [animUnlock, setAnimUnlock] = useState(false);

  useEffect(() => {
    if (localStorage.getItem(UNLOCKED_FLAG) === "1") onUnlock();
  }, []);

  const tryUnlock = () => {
    if (verifyCode(code)) {
      setErr("");
      setAnimUnlock(true);
      localStorage.setItem(UNLOCKED_FLAG, "1");
      setTimeout(() => onUnlock(), 900);
    } else {
      setErr("Incorrect code");
      setCode("");
      // small shake
      const el = document.getElementById("lock-card");
      if (el) {
        el.animate(
          [
            { transform: "translateX(-6px)" },
            { transform: "translateX(6px)" },
            { transform: "translateX(0)" },
          ],
          { duration: 400 },
        );
      }
    }
  };

  return (
    <div className="h-screen flex items-center justify-center bg-black">
      <AnimatePresence>
        {!animUnlock ? (
          <motion.div
            id="lock-card"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="w-full max-w-md p-6 bg-[#0b0d11] border border-[#111215] rounded-2xl shadow-2xl text-center"
          >
            <div className="mb-4">
              <div className="text-3xl font-extrabold text-[#00e5ff]">
                JRAVIS LOCK
              </div>
              <div className="text-xs text-gray-400 mt-1">
                Enter daily report lock code to continue
              </div>
            </div>

            <input
              type="password"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && tryUnlock()}
              placeholder="Enter Lock Code"
              className="w-full p-3 rounded-lg bg-[#07080a] border border-[#151619] text-white mb-3 focus:ring-2 focus:ring-[#00e5ff]/30"
            />

            <button
              onClick={tryUnlock}
              className="w-full py-2 rounded-lg bg-gradient-to-r from-[#00bcd4] to-[#00e5ff] text-black font-semibold"
            >
              UNLOCK
            </button>
            {err && <div className="mt-3 text-red-400 text-sm">{err}</div>}

            <div className="mt-5 text-xs text-gray-500">
              JRAVIS — secure local unlock. No code leaves your browser.
            </div>
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center"
          >
            <h2 className="text-3xl font-bold text-[#00e5ff]">
              Welcome back, Boss
            </h2>
            <p className="mt-2 text-gray-400">
              JRAVIS systems online — loading dashboard…
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
