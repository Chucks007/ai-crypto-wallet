import { useContext } from "react";
import { ToastCtx, type ToastContextValue } from "./ToastContext";

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastCtx);
  if (!ctx) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return ctx;
}
