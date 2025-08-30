import React, { useState } from "react";
import { ApprovalModal } from "./ApprovalModal";

type Suggestion = {
  id: number;
  created_at: string;
  rule: string;
  asset_from?: string | null;
  asset_to?: string | null;
  amount_usd?: number | null;
  reasoning?: string | null;
};

export function SuggestionList({ items, onDecisionCreated }: { items: Suggestion[]; onDecisionCreated?: () => void; }) {
  const [openId, setOpenId] = useState<number | null>(null);
  const open = items.find((x) => x.id === openId) || null;
  return (
    <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 12 }}>
      <div style={{ fontWeight: 600, marginBottom: 8 }}>Suggestions</div>
      <table style={{ width: "100%", fontSize: 14 }}>
        <thead>
          <tr>
            <th align="left">Time</th>
            <th align="left">Rule</th>
            <th align="left">Pair</th>
            <th align="right">Amount (USD)</th>
            <th align="left">Reason</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {items.map((s) => (
            <tr key={s.id}>
              <td>{new Date(s.created_at).toLocaleString()}</td>
              <td>{s.rule}</td>
              <td>{s.asset_from} → {s.asset_to}</td>
              <td align="right">${Number(s.amount_usd || 0).toFixed(2)}</td>
              <td>{s.reasoning}</td>
              <td>
                <button onClick={() => setOpenId(s.id)}>Approve…</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {open && (
        <ApprovalModal
          suggestion={open}
          onClose={() => setOpenId(null)}
          onDecisionCreated={onDecisionCreated}
        />
      )}
    </div>
  );
}

