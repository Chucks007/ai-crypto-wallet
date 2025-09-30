import { useMemo, useState } from "react";
import type { Suggestion } from "../lib/api";
import { ApprovalModal } from "./ApprovalModal";
import { EmptyState } from "./EmptyState";

type SuggestionListProps = {
  items: Suggestion[];
  onDecisionCreated?: () => void;
};

export function SuggestionList({ items, onDecisionCreated }: SuggestionListProps) {
  const [openId, setOpenId] = useState<number | null>(null);
  const open = useMemo(() => items.find((x) => x.id === openId) || null, [items, openId]);

  return (
    <>
      <header className="card__header">
        <h4 className="card__title">Suggestions</h4>
      </header>
      <div className="card__body">
        {items.length === 0 ? (
          <EmptyState
            title="No suggestions to review"
            subtitle="The agent hasn’t proposed any trades yet."
          />
        ) : (
          <div className="table table--responsive table--tight">
            <table>
              <thead>
                <tr>
                  <th scope="col">Time</th>
                  <th scope="col">Rule</th>
                  <th scope="col">Pair</th>
                  <th scope="col" className="table__cell--numeric">Amount (USD)</th>
                  <th scope="col">Reason</th>
                  <th scope="col" className="table__cell--action">Approve</th>
                </tr>
              </thead>
              <tbody>
                {items.map((s) => (
                  <tr key={s.id}>
                    <td data-label="Time">{new Date(s.created_at).toLocaleString()}</td>
                    <td data-label="Rule">{s.rule}</td>
                    <td data-label="Pair">{s.asset_from} → {s.asset_to}</td>
                    <td data-label="Amount (USD)" className="table__cell--numeric">
                      ${Number(s.amount_usd || 0).toFixed(2)}
                    </td>
                    <td
                      data-label="Reason"
                      className="table__cell--truncate"
                      title={s.reasoning || undefined}
                    >
                      {s.reasoning || "—"}
                    </td>
                    <td data-label="Approve" className="table__cell--action">
                      <button className="button" onClick={() => setOpenId(s.id)}>Approve…</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      {open && (
        <ApprovalModal
          suggestion={open}
          onClose={() => setOpenId(null)}
          onDecisionCreated={onDecisionCreated}
        />
      )}
    </>
  );
}
