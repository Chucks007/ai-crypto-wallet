import { useMemo } from "react";
import type { ReactNode } from "react";
import type { Trade } from "../lib/api";
import { normaliseTrades } from "../lib/trades";
import { StatusChip } from "./StatusChip";
import { Spinner } from "./Spinner";
import { EmptyState } from "./EmptyState";

type TradesTableProps = {
  trades: Trade[];
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
  filterControls?: ReactNode;
  emptyTitle?: string;
  emptySubtitle?: string;
};

export function TradesTable({
  trades,
  loading = false,
  error = null,
  onRetry,
  filterControls,
  emptyTitle = "No trades yet",
  emptySubtitle = "When trades execute, they will appear here with their latest status.",
}: TradesTableProps) {
  const items = useMemo(() => normaliseTrades(trades), [trades]);

  if (loading) {
    return (
      <div className="card card--padded">
        <div className="stack stack--row stack--center">
          <Spinner />
          <span>Loading trades…</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card card--padded card--error">
        <div className="stack stack--column" role="alert">
          <strong>Failed to load trades</strong>
          <span>{error}</span>
          {onRetry && (
            <button type="button" className="button button--ghost" onClick={onRetry}>
              Retry
            </button>
          )}
        </div>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="card card--padded">
        <EmptyState
          title={emptyTitle}
          subtitle={emptySubtitle}
          action={onRetry ? <button className="button" onClick={onRetry}>Refresh</button> : undefined}
        />
      </div>
    );
  }

  return (
    <div className="card">
      {filterControls && (
        <div className="card__controls">
          {filterControls}
        </div>
      )}
      <div className="card__body">
        <div className="table table--responsive">
          <table>
            <thead>
              <tr>
                <th scope="col">Time</th>
                <th scope="col">Suggestion</th>
                <th scope="col">Status</th>
                <th scope="col">From</th>
                <th scope="col">To</th>
                <th scope="col">Tx / Notes</th>
              </tr>
            </thead>
            <tbody>
              {items.map((trade) => (
                <tr key={trade.id}>
                  <td data-label="Time">{trade.executedLabel}</td>
                  <td data-label="Suggestion">{trade.suggestionLabel}</td>
                  <td data-label="Status" className="table__cell--status">
                    <StatusChip
                      label={trade.statusMeta.label}
                      tone={trade.statusMeta.tone}
                      icon={trade.statusMeta.icon}
                    />
                  </td>
                  <td data-label="From">{trade.fromAmountLabel}</td>
                  <td data-label="To">{trade.toAmountLabel}</td>
                  <td data-label="Tx / Notes" className="table__cell--truncate">
                    {trade.tx_hash || trade.error || "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
