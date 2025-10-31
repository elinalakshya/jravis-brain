// dashboard_live_feed_secure.js
// Node server that accepts AES-GCM encrypted payloads + daily rotating token
// Run: node dashboard_live_feed_secure.js
// npm i express socket.io sqlite3 cors dotenv

require("dotenv").config({ path: ".env" });
const express = require("express");
const http = require("http");
const { Server } = require("socket.io");
const crypto = require("crypto");
const sqlite3 = require("sqlite3").verbose();
const cors = require("cors");

const PORT = process.env.LIVE_FEED_PORT || 3001;
const DB_PATH = process.env.DB_PATH || "./jravis_core.db";
const WRITE_TO_DB = process.env.WRITE_TO_DB === "true";
const MASTER_KEY = process.env.MASTER_KEY || "";
if (!MASTER_KEY) {
  console.error(
    "ERROR: MASTER_KEY not set in .env. Add MASTER_KEY=<very_random_value>",
  );
  process.exit(1);
}

const app = express();
app.use(cors());
app.use(express.json({ limit: "2mb" })); // used for plaintext mode (if any)

const server = http.createServer(app);
const io = new Server(server, { cors: { origin: "*" } });

// optionally persist feed
let db = null;
if (WRITE_TO_DB) {
  db = new sqlite3.Database(DB_PATH);
  db.run(
    `CREATE TABLE IF NOT EXISTS live_feed (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, type TEXT, payload TEXT)`,
  );
}

// Derive AES key from MASTER_KEY
function aesKeyFromMaster() {
  return crypto.createHash("sha256").update(MASTER_KEY).digest(); // 32 bytes for AES-256
}

// Compute rotating token for a given UTC date string "YYYY-MM-DD"
function rotatingTokenForDate(dateStr) {
  const h = crypto.createHmac("sha256", MASTER_KEY).update(dateStr).digest();
  return h.toString("base64url"); // Node 18+ supports base64url
}

// Accept tokens for today and yesterday (UTC) to provide a grace window
function isValidRotatingToken(token) {
  const now = new Date();
  const utcToday = new Date(
    Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()),
  );
  const yesterday = new Date(utcToday.getTime() - 24 * 60 * 60 * 1000);

  const fmt = (d) => d.toISOString().slice(0, 10);
  const tToday = rotatingTokenForDate(fmt(utcToday));
  const tYesterday = rotatingTokenForDate(fmt(yesterday));
  return token === tToday || token === tYesterday;
}

// AES-GCM decrypt helper: expects base64url inputs (ciphertext, iv, tag)
function decryptPayloadBase64url(cipher_b64url, iv_b64url, tag_b64url) {
  const key = aesKeyFromMaster();
  const cipher = Buffer.from(cipher_b64url, "base64url");
  const iv = Buffer.from(iv_b64url, "base64url");
  const tag = Buffer.from(tag_b64url, "base64url");

  const dec = crypto.createDecipheriv("aes-256-gcm", key, iv);
  dec.setAuthTag(tag);
  const plain = Buffer.concat([dec.update(cipher), dec.final()]);
  return plain.toString("utf8");
}

io.on("connection", (socket) => {
  console.log("Socket connected:", socket.id);
  socket.on("disconnect", () => console.log("Socket disconnected:", socket.id));
});

app.post("/push", (req, res) => {
  const token = req.headers["x-live-token"] || "";
  if (!isValidRotatingToken(token)) {
    return res.status(403).json({ ok: false, message: "invalid token" });
  }

  const encrypted = (req.headers["x-live-encrypted"] || "").toString() === "1";
  let body = req.body;

  try {
    if (encrypted) {
      // expected fields in JSON body: { cipher: "...", iv: "...", tag: "..." }
      const { cipher, iv, tag } = body;
      if (!cipher || !iv || !tag) {
        return res
          .status(400)
          .json({ ok: false, message: "missing encryption fields" });
      }
      const jsonText = decryptPayloadBase64url(cipher, iv, tag);
      body = JSON.parse(jsonText);
    }
  } catch (e) {
    console.error("Decryption error:", e);
    return res.status(400).json({ ok: false, message: "decryption_failed" });
  }

  const type = body.type || "update";
  const payload = body.payload || {};

  // broadcast
  io.emit("live_update", { ts: new Date().toISOString(), type, payload });

  if (WRITE_TO_DB && db) {
    const stmt = db.prepare(
      `INSERT INTO live_feed (ts, type, payload) VALUES (?, ?, ?)`,
    );
    stmt.run(new Date().toISOString(), type, JSON.stringify(payload), (err) => {
      if (err) console.error("DB write error:", err);
      stmt.finalize();
    });
  }

  return res.json({ ok: true });
});

app.get("/health", (req, res) =>
  res.json({ ok: true, ts: new Date().toISOString() }),
);

server.listen(PORT, () =>
  console.log(`Secure Live feed server running on port ${PORT}`),
);
