import type { ReactNode } from "react";

type DataHeaderProps = {
  title: string;
  subtitle?: string;
  lastUpdated?: string | null;
  actions?: ReactNode;
  onRefresh?: () => void;
  refreshing?: boolean;
};

export function DataHeader({
  title,
  subtitle,
  lastUpdated,
  actions,
  onRefresh,
  refreshing = false,
}: DataHeaderProps) {
  return (
    <div className="data-header">
      <div className="data-header__text">
        <h3 className="data-header__title">{title}</h3>
        {subtitle && <p className="data-header__subtitle">{subtitle}</p>}
        {lastUpdated && (
          <span className="data-header__meta">Last updated {lastUpdated}</span>
        )}
      </div>
      <div className="data-header__actions">
        {onRefresh && (
          <button
            type="button"
            onClick={onRefresh}
            className="button button--ghost"
            disabled={refreshing}
          >
            {refreshing ? "Refreshing…" : "Refresh"}
          </button>
        )}
        {actions}
      </div>
    </div>
  );
}
