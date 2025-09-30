import { useEffect, useMemo, useState } from "react";
import {
  getEmergencyStop,
  setEmergencyStop,
  getAutoMode,
  setAutoMode,
  getRuntimeFlag,
  getExecutionStatus,
  getExecutionTokens,
  type ExecutionStatus,
  type ExecutionToken,
} from "../lib/api";
import { useToast } from "../components/Toast";

const CHAIN_LABELS: Record<number, string> = {
  11155111: "Sepolia",
  84532: "Base Sepolia",
};

export default function SettingsPage() {
  const apiBase = (import.meta as any).env.VITE_API_BASE || "http://localhost:8000";
  const { show } = useToast();
  const [emergencyStop, setEmergencyStopState] = useState<boolean>(false);
  const [autoMode, setAutoModeState] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [autoLastStart, setAutoLastStart] = useState<string | null>(null);
  const [autoLastFinish, setAutoLastFinish] = useState<string | null>(null);
  const [executionStatus, setExecutionStatus] = useState<ExecutionStatus | null>(null);
  const [executionStatusError, setExecutionStatusError] = useState<string | null>(null);
  const [executionTokens, setExecutionTokens] = useState<ExecutionToken[]>([]);
  const [executionTokensError, setExecutionTokensError] = useState<string | null>(null);
  const tokensByChain = useMemo(() => {
    const groups: Record<number, ExecutionToken[]> = {};
    executionTokens.forEach((token) => {
      const cid = token.chain_id;
      if (!groups[cid]) groups[cid] = [];
      groups[cid].push(token);
    });
    Object.values(groups).forEach((arr) => arr.sort((a, b) => a.symbol.localeCompare(b.symbol)));
    return groups;
  }, [executionTokens]);

  const formatChain = (id: number | null | undefined) => {
    if (!id) return "—";
    return CHAIN_LABELS[id] ?? `Chain ${id}`;
  };

  const formatUsd = (value: number | null | undefined) => {
    if (value === null || value === undefined) return "—";
    const abs = Math.abs(value);
    const digits = abs >= 1 ? 2 : 6;
    return `$${value.toLocaleString(undefined, { maximumFractionDigits: digits })}`;
  };

  const formatPriceSource = (source: string) => {
    if (!source) return "—";
    if (source === "static") return "Static (env)";
    if (source.startsWith("coingecko:")) {
      const id = source.split(":")[1];
      return `CoinGecko (${id})`;
    }
    return source;
  };

  const chainEntries = Object.entries(tokensByChain);

  useEffect(() => {
    let mounted = true;
    getEmergencyStop().then((d) => {
      if (mounted) setEmergencyStopState(!!d.enabled);
    }).catch(() => {/* ignore */});
    getAutoMode().then((b) => { if (mounted) setAutoModeState(!!b); }).catch(() => {/* ignore */});
    getRuntimeFlag("auto_last_start").then((f) => { if (mounted) setAutoLastStart(f?.value ?? null); }).catch(() => {/* ignore */});
    getRuntimeFlag("auto_last_finish").then((f) => { if (mounted) setAutoLastFinish(f?.value ?? null); }).catch(() => {/* ignore */});
    getExecutionStatus()
      .then((status) => {
        if (!mounted) return;
        setExecutionStatus(status);
        setExecutionStatusError(null);
      })
      .catch((err: any) => {
        if (!mounted) return;
        const detail = err?.response?.data?.detail ?? err?.message ?? String(err);
        setExecutionStatus(null);
        setExecutionStatusError(detail);
      });
    getExecutionTokens()
      .then((tokens) => {
        if (!mounted) return;
        setExecutionTokens(tokens || []);
        setExecutionTokensError(null);
      })
      .catch((err: any) => {
        if (!mounted) return;
        const detail = err?.response?.data?.detail ?? err?.message ?? String(err);
        setExecutionTokens([]);
        setExecutionTokensError(detail);
      });
    return () => { mounted = false };
  }, []);

  async function toggleEmergencyStop() {
    try {
      setLoading(true);
      const next = !emergencyStop;
      await setEmergencyStop(next);
      setEmergencyStopState(next);
      show(next ? "Emergency stop enabled" : "Emergency stop disabled", next ? "error" : "success");
    } catch (e) {
      show("Failed to toggle emergency stop", "error");
    } finally {
      setLoading(false);
    }
  }
  async function toggleAutoMode() {
    try {
      setLoading(true);
      const next = !autoMode;
      await setAutoMode(next);
      setAutoModeState(next);
      show(next ? "Auto mode enabled" : "Auto mode disabled", next ? "success" : "info");
    } catch (e) {
      show("Failed to toggle auto mode", "error");
    } finally {
      setLoading(false);
    }
  }
  return (
    <div>
      <h3>Settings</h3>
      <div style={{ fontSize: 14 }}>
        API Base: <code>{String(apiBase)}</code>
      </div>
      <p style={{ color: "#666" }}>
        Configure Vite env var <code>VITE_API_BASE</code> to point to your API.
      </p>
      <div style={{ marginTop: 16, padding: 12, border: "1px solid #e5e7eb", borderRadius: 8 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <div style={{ fontWeight: 600 }}>Emergency Stop</div>
            <div style={{ fontSize: 13, color: "#666" }}>Blocks approvals/trades when enabled.</div>
          </div>
          <button onClick={toggleEmergencyStop} disabled={loading} style={{
            padding: "8px 12px",
            borderRadius: 6,
            border: "1px solid #d1d5db",
            background: emergencyStop ? "#fee2e2" : "#ecfccb",
            color: emergencyStop ? "#991b1b" : "#14532d",
            cursor: loading ? "not-allowed" : "pointer",
          }}>
            {emergencyStop ? "Disable" : "Enable"}
          </button>
        </div>
      </div>

      <div style={{ marginTop: 12, padding: 12, border: "1px solid #e5e7eb", borderRadius: 8 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <div style={{ fontWeight: 600 }}>Auto Mode</div>
            <div style={{ fontSize: 13, color: "#666" }}>Auto-decider evaluates and commits safe suggestions when enabled.</div>
          </div>
          <button onClick={toggleAutoMode} disabled={loading} style={{
            padding: "8px 12px",
            borderRadius: 6,
            border: "1px solid #d1d5db",
            background: autoMode ? "#dbeafe" : "#f3f4f6",
            color: autoMode ? "#1e3a8a" : "#111827",
            cursor: loading ? "not-allowed" : "pointer",
          }}>
            {autoMode ? "Disable" : "Enable"}
          </button>
        </div>
        <div style={{ marginTop: 8, fontSize: 13, color: "#555" }}>
          <div>Last start: <code>{autoLastStart ? new Date(autoLastStart).toLocaleString() : "—"}</code></div>
          <div>Last finish: <code>{autoLastFinish ? new Date(autoLastFinish).toLocaleString() : "—"}</code></div>
        </div>
      </div>

      <div style={{ marginTop: 12, padding: 12, border: "1px solid #e5e7eb", borderRadius: 8 }}>
        <div style={{ fontWeight: 600 }}>Execution Status</div>
        <div style={{ fontSize: 13, color: "#666" }}>Signer readiness and Permit2 configuration.</div>
        {executionStatusError && (
          <div style={{ marginTop: 8, color: "#b91c1c", fontSize: 12 }}>
            Failed to load execution status: {executionStatusError}
          </div>
        )}
        {!executionStatus && !executionStatusError ? (
          <div style={{ marginTop: 8, fontSize: 13, color: "#6b7280" }}>Loading execution status…</div>
        ) : executionStatus ? (
          <div style={{ marginTop: 8, display: "grid", gap: 6, fontSize: 13, color: "#374151" }}>
            <div>
              Execution enabled: <strong>{executionStatus.execution_enabled ? "Yes" : "No"}</strong>
            </div>
            <div>
              Signer ready: <strong style={{ color: executionStatus.signer_ready ? "#166534" : "#92400e" }}>
                {executionStatus.signer_ready ? "Ready" : "Not ready"}
              </strong>
              {executionStatus.signer_error ? ` (${executionStatus.signer_error})` : null}
            </div>
            <div>
              Signer address: <code>{executionStatus.signer_address ?? "—"}</code>
            </div>
            <div>
              Active chain: <code>{formatChain(executionStatus.configured_chain_id)}</code>
            </div>
            <div>
              Allowed chains: {executionStatus.allowed_chain_ids.length
                ? executionStatus.allowed_chain_ids.map((id) => formatChain(id)).join(", ")
                : "—"}
            </div>
            <div>
              Permit2 status: {executionStatus.permit2.enabled
                ? executionStatus.permit2.ready
                  ? "Ready"
                  : `Not ready (${executionStatus.permit2.status})`
                : "Disabled"}
            </div>
            {executionStatus.permit2.enabled && (
              <>
                <div>Permit2 contract: <code>{executionStatus.permit2.contract ?? "—"}</code></div>
                <div>Permit2 spender: <code>{executionStatus.permit2.default_spender ?? "—"}</code></div>
              </>
            )}
          </div>
        ) : null}
      </div>

      <div style={{ marginTop: 12, padding: 12, border: "1px solid #e5e7eb", borderRadius: 8 }}>
        <div style={{ fontWeight: 600 }}>Token Metadata</div>
        <div style={{ fontSize: 13, color: "#666" }}>Decimals, pricing, and min notionals sourced from the token allowlist.</div>
        {executionTokensError && (
          <div style={{ marginTop: 8, color: "#b91c1c", fontSize: 12 }}>
            Failed to load token metadata: {executionTokensError}
          </div>
        )}
        {!executionTokensError && chainEntries.length === 0 && (
          <div style={{ marginTop: 8, fontSize: 13, color: "#6b7280" }}>
            No token metadata detected. Configure <code>TOKEN_ALLOWLIST_JSON</code> to enable execution.
          </div>
        )}
        {chainEntries.map(([chainId, tokens]) => {
          const numericId = Number(chainId);
          return (
            <div key={chainId} style={{ marginTop: 12 }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: "#374151", textTransform: "uppercase", marginBottom: 6 }}>
                {formatChain(numericId)}
              </div>
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                  <thead>
                    <tr style={{ background: "#f3f4f6", textAlign: "left", fontSize: 12, color: "#4b5563" }}>
                      <th style={{ padding: "6px 8px" }}>Token</th>
                      <th style={{ padding: "6px 8px" }}>Address</th>
                      <th style={{ padding: "6px 8px" }}>Decimals</th>
                      <th style={{ padding: "6px 8px" }}>USD Price</th>
                      <th style={{ padding: "6px 8px" }}>Price Source</th>
                      <th style={{ padding: "6px 8px" }}>Min Trade (USD)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tokens.map((token) => (
                      <tr key={`${chainId}-${token.symbol}`} style={{ borderTop: "1px solid #e5e7eb", fontSize: 12, color: "#111827" }}>
                        <td style={{ padding: "6px 8px", fontWeight: 600 }}>{token.symbol}</td>
                        <td style={{ padding: "6px 8px", fontFamily: "monospace" }}>{token.address ?? "—"}</td>
                        <td style={{ padding: "6px 8px" }}>{token.decimals}</td>
                        <td style={{ padding: "6px 8px" }}>{formatUsd(token.usd_price ?? null)}</td>
                        <td style={{ padding: "6px 8px" }}>{formatPriceSource(token.price_source)}</td>
                        <td style={{ padding: "6px 8px" }}>{formatUsd(token.min_trade_usd ?? null)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
