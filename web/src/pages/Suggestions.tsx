import React, { useEffect, useState } from "react";
import { listSuggestions } from "../lib/api";
import { SuggestionList } from "../components/SuggestionList";
import { Spinner } from "../components/Spinner";
import { EmptyState } from "../components/EmptyState";
import { useToast } from "../components/Toast";

export default function SuggestionsPage() {
  const [items, setItems] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const { show } = useToast();

  function refresh() {
    setLoading(true);
    setError(null);
    listSuggestions(50)
      .then((d) => setItems(d || []))
      .catch((e) => { setError(String(e)); show("Failed to load suggestions", "error"); })
      .finally(() => setLoading(false));
  }

  useEffect(() => { refresh(); }, []);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h3>Suggestions</h3>
        <button onClick={refresh}>Refresh</button>
      </div>
      {loading && (
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <Spinner /> Loading suggestions…
        </div>
      )}
      {error && !loading && <pre style={{ color: "#b91c1c", whiteSpace: "pre-wrap" }}>{error}</pre>}
      {!loading && items.length === 0 ? (
        <EmptyState
          title="No suggestions yet"
          subtitle="When the agent generates ideas, they’ll show up here."
          action={<button onClick={refresh}>Refresh</button>}
        />
      ) : (
        <SuggestionList items={items} onDecisionCreated={refresh} />
      )}
    </div>
  );
}
