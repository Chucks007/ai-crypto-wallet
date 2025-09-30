import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

type Kind = "info" | "success" | "error";
type Toast = { id: number; message: string; kind: Kind };

type Ctx = {
  show: (message: string, kind?: Kind) => void;
};

const ToastCtx = createContext<Ctx | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<Toast[]>([]);

  const show = useCallback((message: string, kind: Kind = "info") => {
    const id = Date.now() + Math.random();
    const t: Toast = { id, message, kind };
    setItems((xs) => [...xs, t]);
    // auto-dismiss after 3s
    setTimeout(() => setItems((xs) => xs.filter((x) => x.id !== id)), 3000);
  }, []);

  const value = useMemo(() => ({ show }), [show]);

  return (
    <ToastCtx.Provider value={value}>
      {children}
      <div style={{
        position: "fixed",
        right: 16,
        bottom: 16,
        display: "flex",
        flexDirection: "column",
        gap: 8,
        zIndex: 2000,
      }}>
        {items.map((t) => (
          <div key={t.id} style={{
            minWidth: 240,
            maxWidth: 420,
            padding: "10px 12px",
            borderRadius: 6,
            color: "#fff",
            fontSize: 14,
            boxShadow: "0 4px 12px rgba(0,0,0,0.2)",
            background: t.kind === "error" ? "#d14343" : t.kind === "success" ? "#107a3d" : "#3b82f6",
          }}>
            {t.message}
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastCtx);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}

