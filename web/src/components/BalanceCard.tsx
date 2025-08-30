import React from "react";

type Balance = {
  id: number;
  asset: string;
  balance: number;
  usd_value?: number | null;
};

export function BalanceCard({ items }: { items: Balance[] }) {
  const total = items.reduce((s, x) => s + (x.usd_value || 0), 0);
  return (
    <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 16 }}>
      <div style={{ fontWeight: 600, marginBottom: 8 }}>Balances</div>
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
        {items.map((b) => (
          <div key={b.id} style={{ minWidth: 140 }}>
            <div style={{ fontSize: 12, color: "#666" }}>{b.asset}</div>
            <div style={{ fontSize: 18 }}>{b.balance}</div>
            <div style={{ fontSize: 12, color: "#666" }}>
              ${(b.usd_value || 0).toFixed(2)}
            </div>
          </div>
        ))}
        <div style={{ marginLeft: "auto", textAlign: "right" }}>
          <div style={{ fontSize: 12, color: "#666" }}>Total (USD)</div>
          <div style={{ fontSize: 18, fontWeight: 600 }}>${total.toFixed(2)}</div>
        </div>
      </div>
    </div>
  );
}

