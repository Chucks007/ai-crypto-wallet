import React from "react";

export default function SettingsPage() {
  const apiBase = (import.meta as any).env.VITE_API_BASE || "http://localhost:8000";
  return (
    <div>
      <h3>Settings</h3>
      <div style={{ fontSize: 14 }}>
        API Base: <code>{String(apiBase)}</code>
      </div>
      <p style={{ color: "#666" }}>
        Configure Vite env var <code>VITE_API_BASE</code> to point to your API.
      </p>
    </div>
  );
}

