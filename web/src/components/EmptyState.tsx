import type { ReactNode } from "react";

export function EmptyState({ title, subtitle, action }: { title: string; subtitle?: string; action?: ReactNode; }) {
  return (
    <div style={{
      border: "1px dashed #d1d5db",
      borderRadius: 8,
      padding: 24,
      textAlign: "center",
      color: "#6b7280",
      background: "#fafafa",
    }}>
      <div style={{ fontWeight: 600, color: "#374151", marginBottom: 4 }}>{title}</div>
      {subtitle && <div style={{ fontSize: 13, marginBottom: action ? 12 : 0 }}>{subtitle}</div>}
      {action}
    </div>
  );
}

