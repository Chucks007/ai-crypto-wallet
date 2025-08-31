import React, { useEffect, useMemo, useState } from "react";
import { getBalances } from "../lib/api";
import { BalanceCard } from "../components/BalanceCard";
import { RiskBar } from "../components/RiskBar";
import { Spinner } from "../components/Spinner";
import { EmptyState } from "../components/EmptyState";
import { useToast } from "../components/Toast";

export default function Overview() {
  const [balances, setBalances] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const { show } = useToast();
  useEffect(() => {
    let mounted = true;
    setLoading(true);
    getBalances()
      .then((d) => { if (mounted) setBalances(d || []); })
      .catch((e) => {
        const msg = String(e);
        if (mounted) setError(msg);
        show("Failed to load balances", "error");
      })
      .finally(() => { if (mounted) setLoading(false); });
    return () => { mounted = false };
  }, []);
  const total = useMemo(() => balances.reduce((s, x) => s + (x.usd_value || 0), 0), [balances]);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <RiskBar portfolioUsd={total} tradesToday={0} />
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
