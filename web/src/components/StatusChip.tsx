import type { TradeStatusTone } from "../lib/trades";

const ICONS: Record<string, string> = {
  clock: "🕒",
  check: "✔",
  x: "✖",
  minus: "−",
};

type StatusChipProps = {
  label: string;
  tone?: TradeStatusTone;
  icon?: keyof typeof ICONS;
  title?: string;
};

export function StatusChip({ label, tone = "neutral", icon, title }: StatusChipProps) {
  const symbol = icon ? ICONS[icon] ?? "" : "";
  return (
    <span className={`chip chip--${tone}`} title={title || label}>
      {symbol && <span aria-hidden="true" className="chip__icon">{symbol}</span>}
      <span className="chip__label">{label}</span>
    </span>
  );
}
