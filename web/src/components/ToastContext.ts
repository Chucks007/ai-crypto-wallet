import { createContext } from "react";

export type ToastKind = "info" | "success" | "error";
export type ToastContextValue = {
  show: (message: string, kind?: ToastKind) => void;
};

export const ToastCtx = createContext<ToastContextValue | null>(null);
