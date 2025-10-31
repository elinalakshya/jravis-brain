import { useState } from "react";
import axios from "axios";

export default function ChatPanel() {
  const [msgs, setMsgs] = useState([
    { who: "sys", text: "JRAVIS online. Ask about Phase 1/2/3 or totals." },
  ]);
  const [text, setText] = useState("");
  const send = async () => {
    if (!text) return;
    setMsgs((m) => [...m, { who: "you", text }]);
    try {
      const r = await axios.post("/api/chat", { text });
      setMsgs((m) => [...m, { who: "jravis", text: r.data.reply }]);
    } catch (e) {
      setMsgs((m) => [
        ...m,
        { who: "jravis", text: "Error contacting backend." },
      ]);
    } finally {
      setText("");
    }
  };
  return (
    <div
      style={{
        position: "fixed",
        right: 10,
        bottom: 10,
        width: 320,
        maxWidth: "90%",
      }}
      className="bg-gray-800 p-3 rounded shadow-lg"
    >
      <div style={{ maxHeight: 240, overflowY: "auto" }} className="space-y-2">
        {msgs.map((m, i) => (
          <div key={i} className={m.who === "you" ? "text-right" : "text-left"}>
            <div
              className={`inline-block p-2 rounded ${m.who === "you" ? "bg-blue-600" : "bg-gray-700"}`}
            >
              {m.text}
            </div>
          </div>
        ))}
      </div>
      <div className="flex mt-2">
        <input
          className="flex-1 p-2 rounded bg-gray-700"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <button className="ml-2 p-2 bg-green-600 rounded" onClick={send}>
          Send
        </button>
      </div>
    </div>
  );
}
