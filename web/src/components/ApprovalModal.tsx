import { useMemo, useState } from "react";
import { commitApproval, type ApprovalCommitResponse, type ApprovalEvaluateResponse } from "../lib/api";
import { useToast } from "./useToast";

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
  const [result, setResult] = useState<ApprovalEvaluateResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { show } = useToast();
  const modalTitleId = useMemo(() => `approve-modal-${suggestion.id}`, [suggestion.id]);
  const formattedAmount = useMemo(() => Number(suggestion.amount_usd || 0).toFixed(2), [suggestion.amount_usd]);

  async function handleEvaluateAndMaybeApprove() {
    setLoading(true);
    setError(null);
    try {
      const commit: ApprovalCommitResponse = await commitApproval({
        suggestion_id: suggestion.id,
        asset_from: suggestion.asset_from || "USDC",
        asset_to: suggestion.asset_to || "ETH",
        suggested_amount_usd: suggestion.amount_usd || 0,
        slippage_bps: slippageBps,
        gas_estimate_usd: gasUsd,
        reason: "ui_approval",
      });
      // commit.evaluation mirrors evaluate endpoint; reflect it in UI
      setResult(commit.evaluation);
      if (commit.created) {
        show("Decision created", "success");
        onDecisionCreated?.();
      } else {
        const v = (commit.evaluation?.violations || []).join(", ") || "Not approved";
        show(`Approval rejected: ${v}`, "error");
      }
    } catch (error: unknown) {
      setError(error instanceof Error ? error.message : String(error));
      show("Failed to evaluate or commit approval", "error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="modal" role="dialog" aria-modal="true" aria-labelledby={modalTitleId}>
      <div className="modal__panel">
        <header className="modal__header">
          <h3 id={modalTitleId} className="modal__title">Approve Suggestion</h3>
          <button
            type="button"
            className="modal__close"
            onClick={onClose}
            aria-label="Close approval modal"
          >
            ×
          </button>
        </header>
        <div className="modal__body">
          <div className="modal__summary">
            <span><strong>Asset:</strong> {suggestion.asset_from} → {suggestion.asset_to}</span>
            <span><strong>Amount:</strong> ${formattedAmount}</span>
          </div>
          <div className="modal__grid">
            <label className="modal__field">
              <span>Slippage (bps)</span>
              <input
                type="number"
                inputMode="numeric"
                min={0}
                step={5}
                className="input"
                value={slippageBps}
                onChange={(e) => setSlippageBps(Number(e.target.value))}
                disabled={loading}
              />
            </label>
            <label className="modal__field">
              <span>Gas est. (USD)</span>
              <input
                type="number"
                inputMode="decimal"
                min={0}
                step={0.25}
                className="input"
                value={gasUsd}
                onChange={(e) => setGasUsd(Number(e.target.value))}
                disabled={loading}
              />
            </label>
          </div>
          {error && (
            <div className="alert alert--error" role="alert">
              {error}
            </div>
          )}
          {result && (
            <div className="modal__result">
              <div>Status: <strong>{result.status}</strong></div>
              <div>Cap notes: {(result.cap_notes || []).join(", ") || "-"}</div>
              <div>Violations: {(result.violations || []).join(", ") || "-"}</div>
              <div>Capped amount: ${Number(result.capped_amount_usd).toFixed(2)}</div>
            </div>
          )}
        </div>
        <div className="modal__footer">
          <button type="button" className="button button--ghost" onClick={onClose} disabled={loading}>
            Cancel
          </button>
          <button type="button" className="button" onClick={handleEvaluateAndMaybeApprove} disabled={loading}>
            {loading ? "Submitting…" : "Evaluate & Approve"}
          </button>
        </div>
      </div>
    </div>
  );
}
