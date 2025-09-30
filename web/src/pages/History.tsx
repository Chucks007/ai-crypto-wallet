import { useCallback, useEffect, useMemo, useState } from "react";
import type { Decision, DecisionListResponse, Trade } from "../lib/api";
import { listDecisions, listTrades } from "../lib/api";
import { Spinner } from "../components/Spinner";
import { EmptyState } from "../components/EmptyState";
import { useToast } from "../components/useToast";
import { DataHeader } from "../components/DataHeader";
import { TradesTable } from "../components/TradesTable";

export default function HistoryPage() {
  const [decisions, setDecisions] = useState<DecisionListResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [lastUpdatedIso, setLastUpdatedIso] = useState<string | null>(null);
  const [tradeFilter, setTradeFilter] = useState<"all" | "open" | "failed">("all");
  const { show } = useToast();

  const refresh = useCallback(() => {
    setLoading(true);
    setError(null);
    Promise.all([listDecisions(), listTrades(50)])
      .then(([d, t]) => {
        setDecisions(d);
        setTrades(t || []);
        setLastUpdatedIso(new Date().toISOString());
      })
      .catch((e) => { setError(String(e)); show("Failed to load history", "error"); })
      .finally(() => setLoading(false));
  }, [show]);

  useEffect(() => { refresh(); }, [refresh]);

  const decisionItems: Decision[] = decisions?.items ?? [];
  const lastUpdatedLabel = useMemo(() => {
    if (!lastUpdatedIso) return null;
    try {
      return new Date(lastUpdatedIso).toLocaleString();
    } catch {
      return lastUpdatedIso;
    }
  }, [lastUpdatedIso]);

  const tradeCounts = useMemo(() => {
    const all = trades.length;
    let open = 0;
    let failed = 0;
    for (const trade of trades) {
      if (trade.status === "submitted") open += 1;
      if (trade.status === "failed") failed += 1;
    }
    return { all, open, failed };
  }, [trades]);

  const filteredTrades = useMemo(() => {
    switch (tradeFilter) {
      case "open":
        return trades.filter((t) => t.status === "submitted");
      case "failed":
        return trades.filter((t) => t.status === "failed");
      default:
        return trades;
    }
  }, [tradeFilter, trades]);

  const filterControls = (
    <div className="segmented" role="tablist" aria-label="Trade filter">
      {([
        { key: "all" as const, label: `All (${tradeCounts.all})` },
        { key: "open" as const, label: `Open (${tradeCounts.open})` },
        { key: "failed" as const, label: `Failed (${tradeCounts.failed})` },
      ]).map((option) => (
        <button
          type="button"
          key={option.key}
          role="tab"
          aria-selected={tradeFilter === option.key}
          className={`segmented__button${tradeFilter === option.key ? " is-active" : ""}`}
          onClick={() => setTradeFilter(option.key)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );

  return (
    <div className="page page--stack" id="history">
      <DataHeader
        title="History"
        subtitle="Recent decisions and trade execution outcomes"
        onRefresh={refresh}
        refreshing={loading}
        lastUpdated={lastUpdatedLabel}
      />

      {error && !loading && (
        <div className="alert alert--error" role="alert">
          {error}
        </div>
      )}

      <section className="page__section" aria-labelledby="decisions-heading">
        <div className="card">
          <header className="card__header">
            <h4 id="decisions-heading" className="card__title">Decisions</h4>
          </header>
          {loading && decisionItems.length === 0 ? (
            <div className="card__body">
              <div className="stack stack--row stack--center">
                <Spinner />
                <span>Loading decisions…</span>
              </div>
            </div>
          ) : decisionItems.length === 0 ? (
            <div className="card__body">
              <EmptyState
                title="No decisions yet"
                subtitle="Approvals and rejections will show here once created."
                action={<button className="button" onClick={refresh}>Refresh</button>}
              />
            </div>
          ) : (
            <div className="card__body">
              <div className="table table--responsive">
                <table>
                  <thead>
                    <tr>
                      <th scope="col">Time</th>
                      <th scope="col">Suggestion</th>
                      <th scope="col">Decision</th>
                      <th scope="col">Reason</th>
                    </tr>
                  </thead>
                  <tbody>
                    {decisionItems.map((d) => (
                      <tr key={d.id}>
                        <td data-label="Time">{new Date(d.decided_at).toLocaleString()}</td>
                        <td data-label="Suggestion">#{d.suggestion_id}</td>
                        <td data-label="Decision" className="text-capitalize">{d.decision}</td>
                        <td data-label="Reason" className="table__cell--truncate">{d.reason || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </section>

  <section className="page__section" aria-labelledby="trades-heading" id="trades">
        <header className="section__header">
          <h4 id="trades-heading" className="section__title">Trades</h4>
        </header>
        <TradesTable
          trades={filteredTrades}
          loading={loading && trades.length === 0}
          error={!loading && trades.length === 0 ? error : null}
          onRetry={refresh}
          filterControls={filterControls}
        />
      </section>
    </div>
  );
}
