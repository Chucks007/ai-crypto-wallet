import React, { useEffect, useState } from "react";
import { listDecisions, listTrades } from "../lib/api";
import { Spinner } from "../components/Spinner";
import { EmptyState } from "../components/EmptyState";
import { useToast } from "../components/Toast";

export default function HistoryPage() {
  const [items, setItems] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [trades, setTrades] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const { show } = useToast();

  function refresh() {
    setLoading(true);
    setError(null);
    Promise.all([listDecisions(50), listTrades(50)])
      .then(([d, t]) => { setItems(d || []); setTrades(t || []); })
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
      {!loading && items.length === 0 && trades.length === 0 ? (
        <EmptyState
          title="No decisions yet"
          subtitle="Approvals and rejections will show here once created."
          action={<button onClick={refresh}>Refresh</button>}
        />
      ) : (
        <div style={{ display: "grid", gap: 16 }}>
          <div>
            <h4 style={{ margin: "8px 0" }}>Decisions</h4>
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
          <div>
            <h4 style={{ margin: "8px 0" }}>Trades</h4>
            <table style={{ width: "100%", fontSize: 14 }}>
              <thead>
                <tr>
                  <th align="left">Time</th>
                  <th align="left">Suggestion</th>
                  <th align="left">Status</th>
                  <th align="left">From</th>
                  <th align="left">To</th>
                  <th align="left">Tx</th>
                </tr>
              </thead>
              <tbody>
                {trades.map((t) => (
                  <tr key={t.id}>
                    <td>{t.executed_at ? new Date(t.executed_at).toLocaleString() : "—"}</td>
                    <td>#{t.suggestion_id}</td>
                    <td>{t.status}</td>
                    <td>{t.amount_from ? `${t.amount_from} ${t.asset_from}` : "—"}</td>
                    <td>{t.amount_to ? `${t.amount_to} ${t.asset_to}` : t.asset_to || "—"}</td>
                    <td style={{ maxWidth: 160, overflow: "hidden", textOverflow: "ellipsis" }}>{t.tx_hash || t.error || ""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
