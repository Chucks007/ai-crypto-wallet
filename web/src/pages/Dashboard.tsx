import { useEffect, useState } from "react";
import { getHealth } from "../lib/api";

type Health = { status: string; version: string };

export default function Dashboard() {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getHealth().then(setHealth).catch((e) => setError(String(e)));
  }, []);

  return (
    <div style={{ padding: 24, fontFamily: "sans-serif" }}>
      <h1>AI Crypto Wallet — Dashboard</h1>
      <p>Milestone 0 scaffold</p>
      {error && <pre>{error}</pre>}
      {health ? (
        <div style={{ marginTop: 12 }}>
          <b>API Health:</b> {health.status} (git {health.version})
        </div>
      ) : (
        <div>Loading API health…</div>
      )}
    </div>
  );
}
