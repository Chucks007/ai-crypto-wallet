import React, { useEffect, useState } from "react";
import { getEmergencyStop, setEmergencyStop, getAutoMode, setAutoMode, getRuntimeFlag } from "../lib/api";
import { useToast } from "../components/Toast";

export default function SettingsPage() {
  const apiBase = (import.meta as any).env.VITE_API_BASE || "http://localhost:8000";
  const { show } = useToast();
  const [emergencyStop, setEmergencyStopState] = useState<boolean>(false);
  const [autoMode, setAutoModeState] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [autoLastStart, setAutoLastStart] = useState<string | null>(null);
  const [autoLastFinish, setAutoLastFinish] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    getEmergencyStop().then((d) => {
      if (mounted) setEmergencyStopState(!!d.enabled);
    }).catch(() => {/* ignore */});
    getAutoMode().then((b) => { if (mounted) setAutoModeState(!!b); }).catch(() => {/* ignore */});
    getRuntimeFlag("auto_last_start").then((f) => { if (mounted) setAutoLastStart(f?.value ?? null); }).catch(() => {/* ignore */});
    getRuntimeFlag("auto_last_finish").then((f) => { if (mounted) setAutoLastFinish(f?.value ?? null); }).catch(() => {/* ignore */});
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
    </div>
  );
}
