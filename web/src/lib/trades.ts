import type { Trade, TradeStatus } from "./api";

export type TradeStatusTone = "neutral" | "info" | "success" | "danger";

export type TradeStatusMeta = {
  label: string;
  tone: TradeStatusTone;
  icon: "clock" | "check" | "x" | "minus";
};

export type NormalisedTrade = Trade & {
  executedLabel: string;
  suggestionLabel: string;
  fromAmountLabel: string;
  toAmountLabel: string;
  statusMeta: TradeStatusMeta;
};

const decimalFormatter = new Intl.NumberFormat(undefined, {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const largeNumberFormatter = new Intl.NumberFormat(undefined, {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

function formatAmount(value: number | null, symbol: string | null): string {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return symbol ? `— ${symbol}` : "—";
  }
  const absValue = Math.abs(value);
  const formatter = absValue >= 1000 ? largeNumberFormatter : decimalFormatter;
  const formatted = formatter.format(value);
  return symbol ? `${formatted} ${symbol}` : formatted;
}

function formatTimestamp(value: string | null): string {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

export function getTradeStatusMeta(status: TradeStatus): TradeStatusMeta {
  switch (status) {
    case "submitted":
      return { label: "Submitted", tone: "info", icon: "clock" };
    case "confirmed":
      return { label: "Confirmed", tone: "success", icon: "check" };
    case "failed":
      return { label: "Failed", tone: "danger", icon: "x" };
    case "cancelled":
    default:
      return { label: "Cancelled", tone: "neutral", icon: "minus" };
  }
}

export function normaliseTrade(trade: Trade): NormalisedTrade {
  return {
    ...trade,
    executedLabel: formatTimestamp(trade.executed_at),
    suggestionLabel: `#${trade.suggestion_id}`,
    fromAmountLabel: formatAmount(trade.amount_from, trade.asset_from),
    toAmountLabel: formatAmount(trade.amount_to, trade.asset_to),
    statusMeta: getTradeStatusMeta(trade.status),
  };
}

export function normaliseTrades(trades: Trade[]): NormalisedTrade[] {
  return trades.map(normaliseTrade);
}
