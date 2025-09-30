import { render, screen } from "@testing-library/react";
import { StatusChip } from "../StatusChip";

describe("StatusChip", () => {
  it("renders label and tone", () => {
    render(<StatusChip label="Confirmed" tone="success" icon="check" />);

    const label = screen.getByText("Confirmed") as HTMLElement;
    const chip = label.parentElement as HTMLElement | null;
    expect(chip).toBeInTheDocument();
    expect(chip).toHaveClass("chip");
    expect(chip).toHaveClass("chip--success");
    expect(screen.getByText("✔")).toBeInTheDocument();
  });

  it("falls back gracefully without icon", () => {
    render(<StatusChip label="Submitted" tone="info" />);
    const label = screen.getByText("Submitted") as HTMLElement;
    const chip = label.parentElement as HTMLElement | null;
    const icon = screen.queryByText("✖") as HTMLElement | null;
    expect(icon).not.toBeInTheDocument();
    expect(chip).toHaveClass("chip--info");
  });
});
