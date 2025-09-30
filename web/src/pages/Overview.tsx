import { useEffect, useMemo, useState } from "react";
import { getBalances, getDailyMetrics, type DailyMetrics } from "../lib/api";
import { BalanceCard } from "../components/BalanceCard";
import { RiskBar } from "../components/RiskBar";
import { Spinner } from "../components/Spinner";
import { EmptyState } from "../components/EmptyState";
import { useToast } from "../components/Toast";

export default function Overview() {
  const [balances, setBalances] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<DailyMetrics | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [metricsError, setMetricsError] = useState<string | null>(null);
  const { show } = useToast();
  useEffect(() => {
    let mounted = true;
    setLoading(true);
    Promise.allSettled([getBalances(), getDailyMetrics()])
      .then(([b, m]) => {
        if (!mounted) return;
        if (b.status === "fulfilled") setBalances(b.value || []);
        else {
          const msg = String(b.reason);
          setError(msg);
          show("Failed to load balances", "error");
        }
        if (m.status === "fulfilled") setMetrics(m.value || null);
        else setMetricsError(String(m.reason));
      })
      .finally(() => { if (mounted) setLoading(false); });
    return () => { mounted = false };
  }, []);
  const total = useMemo(() => balances.reduce((s, x) => s + (x.usd_value || 0), 0), [balances]);
  const tradesToday = useMemo(() => {
    if (!metrics) return 0;
    return Object.values(metrics.today?.trades || {}).reduce((s, v) => s + (v || 0), 0);
  }, [metrics]);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <RiskBar portfolioUsd={total} tradesToday={tradesToday} />
      {metrics && (
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: 12,
          padding: 12,
          border: "1px solid #e5e7eb",
          borderRadius: 8,
          background: "#fafafa",
        }}>
          <div>
            <div style={{ fontSize: 12, color: "#6b7280", textTransform: "uppercase" }}>Suggestions Today</div>
            <div style={{ fontSize: 24, fontWeight: 700 }}>{metrics.today.suggestions}</div>
          </div>
          <div>
            <div style={{ fontSize: 12, color: "#6b7280", textTransform: "uppercase" }}>Decisions Today</div>
            <div style={{ fontSize: 14 }}>
              {Object.entries(metrics.today.decisions || {}).length === 0 ? (
                <span>—</span>
              ) : (
                Object.entries(metrics.today.decisions).map(([k, v]) => (
                  <span key={k} style={{ marginRight: 12 }}>
                    <b>{k}</b>: {v}
                  </span>
                ))
              )}
            </div>
          </div>
          <div>
            <div style={{ fontSize: 12, color: "#6b7280", textTransform: "uppercase" }}>Trades Today</div>
            <div style={{ fontSize: 14 }}>
              {Object.entries(metrics.today.trades || {}).length === 0 ? (
                <span>—</span>
              ) : (
                Object.entries(metrics.today.trades).map(([k, v]) => (
                  <span key={k} style={{ marginRight: 12 }}>
                    <b>{k}</b>: {v}
                  </span>
                ))
              )}
            </div>
          </div>
          <div>
            <div style={{ fontSize: 12, color: "#6b7280", textTransform: "uppercase" }}>Auto Worker</div>
            <div style={{ fontSize: 13, color: "#374151" }}>
              <div>Last start: <code>{metrics.last_worker.last_start ? new Date(metrics.last_worker.last_start).toLocaleString() : "—"}</code></div>
              <div>Last finish: <code>{metrics.last_worker.last_finish ? new Date(metrics.last_worker.last_finish).toLocaleString() : "—"}</code></div>
            </div>
          </div>
        </div>
      )}
      {metricsError && (
        <div style={{ color: "#b91c1c", fontSize: 13 }}>Failed to load metrics: {metricsError}</div>
      )}
      {loading && (
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <Spinner /> Loading balances…
        </div>
      )}
      {error && !loading && <pre style={{ color: "#b91c1c", whiteSpace: "pre-wrap" }}>{error}</pre>}
      {!loading && balances.length === 0 ? (
        <EmptyState title="No balances yet" subtitle="Once the backend returns assets, your portfolio appears here." />
      ) : (
        <BalanceCard items={balances} />
      )}
    </div>
  );
}
