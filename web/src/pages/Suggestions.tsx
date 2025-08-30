import React, { useEffect, useState } from "react";
import { listSuggestions } from "../lib/api";
import { SuggestionList } from "../components/SuggestionList";

export default function SuggestionsPage() {
  const [items, setItems] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  function refresh() {
    listSuggestions(50).then(setItems).catch((e) => setError(String(e)));
  }

  useEffect(() => { refresh(); }, []);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h3>Suggestions</h3>
        <button onClick={refresh}>Refresh</button>
      </div>
      {error && <pre style={{ color: "red" }}>{error}</pre>}
      <SuggestionList items={items} onDecisionCreated={refresh} />
    </div>
  );
}

