import React from "react";

export function RiskBar({
  portfolioUsd,
  tradesToday,
}: {
  portfolioUsd: number;
  tradesToday: number;
}) {
  return (
    <div style={{
      border: "1px solid #eee",
      borderRadius: 8,
      padding: 12,
      background: "#fafafa",
      display: "flex",
      gap: 16,
      alignItems: "center",
      fontSize: 14,
    }}>
      <span>
        Portfolio: <b>${portfolioUsd.toFixed(2)}</b>
      </span>
      <span>
        Trades today: <b>{tradesToday}</b>
      </span>
    </div>
  );
}

