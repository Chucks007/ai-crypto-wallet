import React, { useEffect, useState } from "react";
import { listDecisions } from "../lib/api";

export default function HistoryPage() {
  const [items, setItems] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  function refresh() {
    listDecisions(50).then(setItems).catch((e) => setError(String(e)));
  }

  useEffect(() => { refresh(); }, []);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h3>History</h3>
        <button onClick={refresh}>Refresh</button>
      </div>
      {error && <pre style={{ color: "red" }}>{error}</pre>}
      <table style={{ width: "100%", fontSize: 14 }}>
        <thead>
          <tr>
            <th align="left">Time</th>
            <th align="left">Suggestion</th>
            <th align="left">Decision</th>
            <th align="left">Reason</th>
          </tr>
        </thead>
        <tbody>
          {items.map((d) => (
            <tr key={d.id}>
              <td>{new Date(d.decided_at).toLocaleString()}</td>
              <td>#{d.suggestion_id}</td>
              <td>{d.decision}</td>
              <td>{d.reason || ""}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

