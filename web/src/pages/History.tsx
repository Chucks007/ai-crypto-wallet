import React, { useEffect, useState } from "react";
import { listDecisions } from "../lib/api";
import { Spinner } from "../components/Spinner";
import { EmptyState } from "../components/EmptyState";
import { useToast } from "../components/Toast";

export default function HistoryPage() {
  const [items, setItems] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const { show } = useToast();

  function refresh() {
    setLoading(true);
    setError(null);
    listDecisions(50)
      .then((d) => setItems(d || []))
      .catch((e) => { setError(String(e)); show("Failed to load history", "error"); })
      .finally(() => setLoading(false));
  }

  useEffect(() => { refresh(); }, []);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h3>History</h3>
        <button onClick={refresh}>Refresh</button>
      </div>
      {loading && (
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <Spinner /> Loading history…
        </div>
      )}
      {error && !loading && <pre style={{ color: "#b91c1c", whiteSpace: "pre-wrap" }}>{error}</pre>}
      {!loading && items.length === 0 ? (
        <EmptyState
          title="No decisions yet"
          subtitle="Approvals and rejections will show here once created."
          action={<button onClick={refresh}>Refresh</button>}
        />
      ) : (
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
      )}
    </div>
  );
}
