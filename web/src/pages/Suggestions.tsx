import { useCallback, useEffect, useMemo, useState } from "react";
import { listSuggestions, type Suggestion } from "../lib/api";
import { SuggestionList } from "../components/SuggestionList";
import { Spinner } from "../components/Spinner";
import { EmptyState } from "../components/EmptyState";
import { useToast } from "../components/useToast";
import { DataHeader } from "../components/DataHeader";

export default function SuggestionsPage() {
  const [items, setItems] = useState<Suggestion[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [lastUpdatedIso, setLastUpdatedIso] = useState<string | null>(null);
  const { show } = useToast();

  const refresh = useCallback(() => {
    setLoading(true);
    setError(null);
    listSuggestions(50)
      .then((d) => {
        setItems(d || []);
        setLastUpdatedIso(new Date().toISOString());
      })
      .catch((e) => { setError(String(e)); show("Failed to load suggestions", "error"); })
      .finally(() => setLoading(false));
  }, [show]);

  useEffect(() => { refresh(); }, [refresh]);

  const lastUpdatedLabel = useMemo(() => {
    if (!lastUpdatedIso) return null;
    try {
      return new Date(lastUpdatedIso).toLocaleString();
    } catch {
      return lastUpdatedIso;
    }
  }, [lastUpdatedIso]);

  return (
    <div className="page page--stack">
      <DataHeader
        title="Suggestions"
        subtitle="Review the agent’s latest ideas and approve safe trades"
        onRefresh={refresh}
        refreshing={loading}
        lastUpdated={lastUpdatedLabel}
      />

      {loading && (
        <div className="stack stack--row stack--center">
          <Spinner />
          <span>Loading suggestions…</span>
        </div>
      )}

      {error && !loading && (
        <div className="alert alert--error" role="alert">
          {error}
        </div>
      )}

      {!loading && items.length === 0 ? (
        <EmptyState
          title="No suggestions yet"
          subtitle="When the agent generates ideas, they’ll show up here."
          action={<button className="button" onClick={refresh}>Refresh</button>}
        />
      ) : (
        <div className="card">
          <SuggestionList items={items} onDecisionCreated={refresh} />
        </div>
      )}
    </div>
  );
}
