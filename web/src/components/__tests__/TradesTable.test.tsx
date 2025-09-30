import { render, screen } from "@testing-library/react";
import { TradesTable } from "../TradesTable";
import type { Trade } from "../../lib/api";

describe("TradesTable", () => {
  const baseTrade: Trade = {
    id: 1,
    suggestion_id: 10,
    executed_at: "2024-01-01T00:00:00.000Z",
    status: "confirmed",
    tx_hash: "0xtest",
    asset_from: "USDC",
    amount_from: 100,
    asset_to: "ETH",
    amount_to: 0.05,
    slippage_bps: 50,
    gas_est_usd: 2,
    error: null,
  };

  it("renders provided trades with status chips", () => {
    const trades: Trade[] = [
      baseTrade,
      {
        ...baseTrade,
        id: 2,
        suggestion_id: 11,
        status: "failed",
        tx_hash: null,
        error: "execution_error",
      },
    ];

    render(<TradesTable trades={trades} />);

    expect(screen.getByText("#10")).toBeInTheDocument();
    expect(screen.getByText("Confirmed")).toBeInTheDocument();
    expect(screen.getByText("Failed")).toBeInTheDocument();
    expect(screen.getByText("execution_error")).toBeInTheDocument();
  });

  it("shows an empty state when no trades are available", () => {
    render(<TradesTable trades={[]} />);
    expect(screen.getByText("No trades yet")).toBeInTheDocument();
  });
});
