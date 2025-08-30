import React, { useEffect, useMemo, useState } from "react";
import { getBalances } from "../lib/api";
import { BalanceCard } from "../components/BalanceCard";
import { RiskBar } from "../components/RiskBar";

export default function Overview() {
  const [balances, setBalances] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    getBalances().then(setBalances).catch((e) => setError(String(e)));
  }, []);
  const total = useMemo(() => balances.reduce((s, x) => s + (x.usd_value || 0), 0), [balances]);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <RiskBar portfolioUsd={total} tradesToday={0} />
      {error && <pre style={{ color: "red" }}>{error}</pre>}
      <BalanceCard items={balances} />
    </div>
  );
}

