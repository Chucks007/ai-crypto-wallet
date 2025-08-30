import React, { useState } from "react";
import { evaluateApproval, createDecision } from "../lib/api";

type Props = {
  suggestion: {
    id: number;
    asset_from?: string | null;
    asset_to?: string | null;
    amount_usd?: number | null;
  };
  onClose: () => void;
  onDecisionCreated?: () => void;
};

export function ApprovalModal({ suggestion, onClose, onDecisionCreated }: Props) {
  const [slippageBps, setSlippageBps] = useState<number>(50);
  const [gasUsd, setGasUsd] = useState<number>(1);
  const [result, setResult] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleEvaluateAndMaybeApprove() {
    setLoading(true);
    setError(null);
    try {
      const res = await evaluateApproval({
        asset_from: suggestion.asset_from || "USDC",
        asset_to: suggestion.asset_to || "ETH",
        suggested_amount_usd: suggestion.amount_usd || 0,
        slippage_bps: slippageBps,
        gas_estimate_usd: gasUsd,
      });
      setResult(res);
      if (res.status === "approved") {
        await createDecision({
          suggestion_id: suggestion.id,
          decision: "approved",
          reason: (res.cap_notes || []).join(", "),
        });
        onDecisionCreated?.();
      }
    } catch (e: any) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{
      position: "fixed",
      inset: 0,
      background: "rgba(0,0,0,0.4)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      zIndex: 1000,
    }}>
      <div style={{ background: "white", padding: 16, borderRadius: 8, width: 420 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h3>Approve Suggestion</h3>
          <button onClick={onClose}>×</button>
        </div>
        <div style={{ fontSize: 14, color: "#444", marginBottom: 12 }}>
          Asset: <b>{suggestion.asset_from} → {suggestion.asset_to}</b><br/>
          Amount: <b>${suggestion.amount_usd?.toFixed(2)}</b>
        </div>
        <div style={{ display: "flex", gap: 12, marginBottom: 12 }}>
          <label style={{ flex: 1 }}>
            Slippage (bps)
            <input type="number" value={slippageBps}
              onChange={(e) => setSlippageBps(Number(e.target.value))}
              style={{ width: "100%" }} />
          </label>
          <label style={{ flex: 1 }}>
            Gas est. (USD)
            <input type="number" value={gasUsd}
              onChange={(e) => setGasUsd(Number(e.target.value))}
              style={{ width: "100%" }} />
          </label>
        </div>
        <button onClick={handleEvaluateAndMaybeApprove} disabled={loading}>
          {loading ? "Evaluating…" : "Evaluate & Approve if Safe"}
        </button>
        {error && <pre style={{ color: "red", whiteSpace: "pre-wrap" }}>{error}</pre>}
        {result && (
          <div style={{ marginTop: 12, fontSize: 14 }}>
            <div>Status: <b>{result.status}</b></div>
            <div>Cap notes: {(result.cap_notes || []).join(", ") || "-"}</div>
            <div>Violations: {(result.violations || []).join(", ") || "-"}</div>
            <div>Capped amount: ${Number(result.capped_amount_usd).toFixed(2)}</div>
          </div>
        )}
      </div>
    </div>
  );
}

