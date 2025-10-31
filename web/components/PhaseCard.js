export default function PhaseCard({ phaseKey, payload }) {
  const titleMap = {
    phase1: "Phase 1 — Fast Kickstart",
    phase2: "Phase 2 — Scaling",
    phase3: "Phase 3 — Advanced",
  };
  const targetMap = {
    phase1: "₹3–₹14.5L",
    phase2: "₹3.65–₹15.05L",
    phase3: "₹4.2–₹16.5L",
  };
  const percent =
    (payload.total /
      (phaseKey === "phase1" ? 14.5 : phaseKey === "phase2" ? 15.05 : 16.5)) *
    100;
  return (
    <div className="p-4 bg-gray-800 rounded">
      <h3 className="font-bold">{titleMap[phaseKey]}</h3>
      <div className="text-sm text-gray-300">Target {targetMap[phaseKey]}</div>
      <div className="mt-2">
        <div className="text-3xl font-semibold">₹{payload.total}</div>
        <div className="w-full bg-gray-700 h-3 rounded mt-2">
          <div
            style={{ width: `${Math.min(100, Math.max(0, percent))}%` }}
            className="h-3 bg-green-500 rounded"
          ></div>
        </div>
        <div className="mt-2 text-xs text-gray-400">
          Streams: {payload.count}
        </div>
      </div>
      <div className="mt-3">
        {payload.streams.map((s) => (
          <div key={s.name} className="mt-2 p-2 bg-gray-900 rounded text-sm">
            <div className="flex justify-between">
              <div>{s.name}</div>
              <div>₹{s.amount}</div>
            </div>
            <div className="text-xs text-gray-500">
              updated: {s.last_updated || "-"}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
