import { useEffect, useMemo, useState } from "react";
import { getBalances, getDailyMetrics, type BalanceSnapshot, type DailyMetrics } from "../lib/api";
import { BalanceCard } from "../components/BalanceCard";
import { RiskBar } from "../components/RiskBar";
import { Spinner } from "../components/Spinner";
import { EmptyState } from "../components/EmptyState";
import { useToast } from "../components/useToast";

export default function Overview() {
  const [balances, setBalances] = useState<BalanceSnapshot[]>([]);
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
  }, [show]);
  const total = useMemo(() => balances.reduce((s, x) => s + (x.usd_value || 0), 0), [balances]);
  const tradesToday = useMemo(() => {
    if (!metrics) return 0;
    return Object.values(metrics.today?.trades || {}).reduce((s, v) => s + (v || 0), 0);
  }, [metrics]);
  const tradesByStatus = useMemo(() => Object.entries(metrics?.today.trades ?? {}), [metrics]);
  const tradesTotal = useMemo(
    () => tradesByStatus.reduce((sum, [, value]) => sum + (value || 0), 0),
    [tradesByStatus],
  );

  return (
    <div className="page page--stack">
      <RiskBar portfolioUsd={total} tradesToday={tradesToday} />

      {metrics && (
        <div className="stats-grid">
          <div className="stat-card">
            <span className="stat-card__label">Suggestions Today</span>
            <span className="stat-card__value">{metrics.today.suggestions}</span>
          </div>
          <div className="stat-card">
            <span className="stat-card__label">Decisions Today</span>
            <div className="stat-card__list">
              {Object.entries(metrics.today.decisions || {}).length === 0 ? (
                <span className="stat-card__empty">—</span>
              ) : (
                Object.entries(metrics.today.decisions).map(([k, v]) => (
                  <span key={k}><b>{k}</b>: {v}</span>
                ))
              )}
            </div>
          </div>
          <a className="stat-card stat-card--link" href="#/history#trades">
            <span className="stat-card__label">Trades Today</span>
            <span className="stat-card__value">{tradesTotal}</span>
            <div className="stat-card__list">
              {tradesByStatus.length === 0 ? (
                <span className="stat-card__empty">No trades yet</span>
              ) : (
                tradesByStatus.map(([k, v]) => (
                  <span key={k}><b>{k}</b>: {v}</span>
                ))
              )}
            </div>
            <span className="stat-card__cta">View full history →</span>
          </a>
          <div className="stat-card">
            <span className="stat-card__label">Auto Worker</span>
            <div className="stat-card__list">
              <span>Last start: <code>{metrics.last_worker.last_start ? new Date(metrics.last_worker.last_start).toLocaleString() : "—"}</code></span>
              <span>Last finish: <code>{metrics.last_worker.last_finish ? new Date(metrics.last_worker.last_finish).toLocaleString() : "—"}</code></span>
            </div>
          </div>
        </div>
      )}

      {metricsError && (
        <div className="alert alert--error" role="alert">
          Failed to load metrics: {metricsError}
        </div>
      )}

      {loading && (
        <div className="stack stack--row stack--center">
          <Spinner />
          <span>Loading balances…</span>
        </div>
      )}

      {error && !loading && (
        <div className="alert alert--error" role="alert">
          {error}
        </div>
      )}

      {!loading && balances.length === 0 ? (
        <EmptyState
          title="No balances yet"
          subtitle="Once the backend returns assets, your portfolio appears here."
        />
      ) : (
        <BalanceCard items={balances} />
      )}
    </div>
  );
}
