import { useEffect, useRef, useState } from "react";
import axios from "axios";

export default function ChatPanel() {
  const [msgs, setMsgs] = useState([
    {
      who: "sys",
      text: "JRAVIS online. Ask me about Phase 1/2/3, totals, or top streams.",
    },
  ]);
  const [text, setText] = useState("");
  const boxRef = useRef();

  useEffect(() => {
    if (boxRef.current) boxRef.current.scrollTop = boxRef.current.scrollHeight;
  }, [msgs]);

  const send = async () => {
    if (!text) return;
    setMsgs((m) => [...m, { who: "you", text }]);
    const payload = { text };
    setText("");
    try {
      const r = await axios.post("http://0.0.0.0:8000/api/chat", payload, {
        timeout: 5000,
      });
      setMsgs((m) => [...m, { who: "jravis", text: r.data.reply }]);
    } catch (e) {
      setMsgs((m) => [
        ...m,
        { who: "jravis", text: "Backend unreachable or timeout." },
      ]);
    }
  };

  return (
    <div
      style={{
        position: "fixed",
        right: 12,
        bottom: 12,
        width: 360,
        maxWidth: "95%",
      }}
    >
      <div className="bg-[#07080a] border border-[#111215] rounded-lg shadow-xl overflow-hidden">
        <div
          ref={boxRef}
          style={{ maxHeight: 260, overflowY: "auto", padding: 10 }}
          className="space-y-2"
        >
          {msgs.map((m, i) => (
            <div
              key={i}
              className={m.who === "you" ? "text-right" : "text-left"}
            >
              <div
                className={`inline-block px-3 py-2 rounded-lg ${m.who === "you" ? "bg-gradient-to-r from-[#00bcd4] to-[#00e5ff] text-black" : "bg-[#0b0d11] text-white"}`}
              >
                {m.text}
              </div>
            </div>
          ))}
        </div>

        <div className="p-3 flex gap-2">
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            placeholder="Ask JRAVIS..."
            className="flex-1 p-2 rounded bg-[#06070a] border border-[#111214] text-white"
          />
          <button
            onClick={send}
            className="px-3 rounded bg-gradient-to-r from-[#00bcd4] to-[#00e5ff] text-black font-semibold"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
