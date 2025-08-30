import React, { useEffect, useState } from "react";
import { getEmergencyStop, setEmergencyStop } from "../lib/api";
import { useToast } from "../components/Toast";

export default function SettingsPage() {
  const apiBase = (import.meta as any).env.VITE_API_BASE || "http://localhost:8000";
  const { show } = useToast();
  const [emergencyStop, setEmergencyStopState] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    let mounted = true;
    getEmergencyStop().then((d) => {
      if (mounted) setEmergencyStopState(!!d.enabled);
    }).catch(() => {/* ignore */});
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
    </div>
  );
}
