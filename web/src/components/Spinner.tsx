import React from "react";

export function Spinner({ size = 16 }: { size?: number }) {
  const s = size;
  return (
    <span
      aria-label="loading"
      style={{
        display: "inline-block",
        width: s,
        height: s,
        border: `${Math.max(2, Math.round(s/8))}px solid rgba(0,0,0,0.15)`,
        borderTopColor: "#3b82f6",
        borderRadius: "50%",
        animation: "spin 1s linear infinite",
      }}
    />
  );
}

